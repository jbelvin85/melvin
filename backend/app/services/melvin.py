from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Tuple, Dict
import re

import threading

from .data_loader import datastore, CardEntry
from ..core.config import get_settings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from ..services.scryfall import scryfall_service
from ..services.state_manager import state_manager_cls
from .cards import card_search_service
from .knowledge import knowledge_store

if TYPE_CHECKING:
    from ..models.user import User


class MelvinService:
    def __init__(self) -> None:
        self._ensure_loaded()
        settings = get_settings()
        self.vectorstore_path = settings.processed_data_dir / "chroma_db"
        self.embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        
        self.rules_db = Chroma(persist_directory=str(self.vectorstore_path / "rules"), embedding_function=self.embedding_function)
        self.cards_db = Chroma(persist_directory=str(self.vectorstore_path / "cards"), embedding_function=self.embedding_function)
        self.rulings_db = Chroma(persist_directory=str(self.vectorstore_path / "rulings"), embedding_function=self.embedding_function)
        self.reference_db = self._load_vector_store("reference")

        self.rules_retriever = self.rules_db.as_retriever()
        self.cards_retriever = self.cards_db.as_retriever()
        self.rulings_retriever = self.rulings_db.as_retriever()
        self.reference_retriever = self.reference_db.as_retriever() if self.reference_db else None
        self.rule_identifiers = {rule.identifier for rule in datastore.rules}

        self.model_name = self._load_model_choice(default_model=settings.ollama_model)
        self.llm = Ollama(model=self.model_name, base_url=self._ollama_base_url(settings))
        self.prompt = ChatPromptTemplate.from_template(
            """Answer the question based only on the following context:
Rules: {rules_context}
Cards: {cards_context}
Rulings: {rulings_context}
Commander & Intro Guides: {reference_context}
Knowledge Graph: {knowledge_context}
{player_guidance}

Question: {question}
"""
        )
    def _ensure_loaded(self) -> None:
        if not datastore.rules or not datastore.cards or not datastore.rulings:
            datastore.load()

    def _load_vector_store(self, name: str) -> Optional[Chroma]:
        target = self.vectorstore_path / name
        if not target.exists():
            return None
        return Chroma(persist_directory=str(target), embedding_function=self.embedding_function)

    def _build_player_guidance(self, user: Optional[User] = None) -> str:
        """
        Build conversation guidance based on player psychographic profile.
        Returns empty string if no profile exists.
        """
        if not user or not hasattr(user, 'profile') or not user.profile:
            return ""
        
        profile = user.profile
        from .assessment import ARCHETYPE_INFO
        
        archetype_info = ARCHETYPE_INFO.get(profile.primary_type)
        if not archetype_info:
            return ""
        
        guidance = archetype_info.get("conversation_guidance", "")
        return f"Player Profile Guidance: {guidance}" if guidance else ""

    def answer_question(self, question: str, user: Optional[User] = None) -> str:
        response_text, _, _ = self.answer_question_with_details(question, user=user)
        return response_text

    def _summarize_doc(self, label: str, docs: List) -> Optional[Dict[str, str]]:
        if not docs:
            return None
        snippet = docs[0].page_content.strip().replace("\n", " ")
        if len(snippet) > 200:
            snippet = f"{snippet[:197]}..."
        return {"label": label, "detail": f"Top excerpt: {snippet}"}

    def _format_card_entry(self, entry: CardEntry) -> str:
        parts = [f"Name: {entry.name}"]
        if entry.type_line:
            parts.append(f"Type: {entry.type_line}")
        if entry.oracle_text:
            parts.append(f"Oracle: {entry.oracle_text}")
        return "\n".join(parts)

    def _ollama_base_url(self, settings):
        return f"http://{settings.ollama_host}:{settings.ollama_port}"

    def _model_choice_path(self):
        settings = get_settings()
        return settings.processed_data_dir / "model_selection.json"

    def _load_model_choice(self, default_model: str) -> str:
        path = self._model_choice_path()
        if path.exists():
            try:
                import json

                with path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if isinstance(data, dict) and isinstance(data.get("model"), str):
                    return data["model"]
            except Exception:
                pass
        return default_model

    def _save_model_choice(self, model_name: str) -> None:
        path = self._model_choice_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            import json

            with path.open("w", encoding="utf-8") as handle:
                json.dump({"model": model_name}, handle)
        except Exception:
            # Persisting the choice is best-effort; ignore failures to avoid breaking runtime flow.
            pass

    def set_model(self, model_name: str) -> None:
        settings = get_settings()
        self.model_name = model_name
        self.llm = Ollama(model=model_name, base_url=self._ollama_base_url(settings))
        self._save_model_choice(model_name)

    def _extract_tagged_cards(self, text: str) -> List[str]:
        pattern = re.compile(r"\[([^\[\]]{2,120})\]")
        results = []
        for match in pattern.findall(text or ""):
            candidate = match.strip()
            if candidate:
                results.append(candidate)
        return results

    def _extract_rule_ids(self, text: str) -> List[str]:
        if not text:
            return []
        pattern = re.compile(r"\b(\d{3}\.\d+[a-z]?)\b")
        return pattern.findall(text)

    def answer_question_with_details(
        self,
        question: str,
        user: Optional[User] = None,
        tone: Optional[str] = None,
        detail_level: Optional[str] = None,
        selected_cards: Optional[List[str]] = None,
    ) -> Tuple[str, List[Dict[str, str]], Dict[str, str]]:
        explicit_cards = selected_cards or []
        thinking: List[Dict[str, str]] = []
        thinking.append({"label": "Question received", "detail": question.strip()})
        style_notes: List[str] = []
        if tone:
            style_notes.append(f"Preferred tone: {tone}")
        if detail_level:
            style_notes.append(f"Detail level: {detail_level}")
        if style_notes:
            thinking.append({"label": "User preference", "detail": " | ".join(style_notes)})

        # Try to detect a card name via Scryfall autocomplete on the whole question.
        # If we get a suggestion, fetch the named card and include a short summary
        # in the `cards_context` to help the model.
        scryfall_cards_context = None
        scryfall_card_name = None
        state_context = None
        external_card_sections: List[str] = []
        try:
            ac = scryfall_service.autocomplete(question)
            if ac and ac.get("data"):
                # take top suggestion
                top = ac["data"][0]
                # fetch full card by named fuzzy
                card = scryfall_service.get_card(f"named?fuzzy={top}")
                # Build a short summary
                parts = [f"Name: {card.get('name')}"]
                if card.get("mana_cost"):
                    parts.append(f"Mana: {card.get('mana_cost')}")
                if card.get("type_line"):
                    parts.append(f"Type: {card.get('type_line')}")
                if card.get("oracle_text"):
                    parts.append(f"Oracle: {card.get('oracle_text')}")
                scryfall_cards_context = "\n".join(parts)
                scryfall_card_name = card.get("name")
        except Exception:
            # on any failure, continue without external card context
            scryfall_cards_context = None

        # Try to attach the most recent saved board state as `state_context` if available
        try:
            # attempt to get latest state from DB if available
            # lightweight: fetch the most recent saved state
            db = None
            from ..dependencies import get_db as _get_db

            # dependencies.get_db is a generator; can't call here reliably — skip if not in request
            # Instead, attempt to read a fallback latest entry via direct session import if available
            from ..core.database import SessionLocal
            with SessionLocal() as session:
                manager = state_manager_cls(session)
                states = manager.list_states()
                if states:
                    state_context = states[0].state
        except Exception:
            state_context = None

        payload = {"question": question}
        resolved_cards: Dict[str, CardEntry] = {}
        warnings: List[str] = []
        if explicit_cards:
            resolved = card_search_service.resolve_cards(explicit_cards)
            if resolved:
                for entry in resolved:
                    if entry.name:
                        resolved_cards.setdefault(entry.name.lower(), entry)
                manual_sections = [self._format_card_entry(entry) for entry in resolved]
                external_card_sections.append("User-selected cards:\n" + "\n\n".join(manual_sections))
                names = ", ".join(card.name for card in resolved if card.name)
                thinking.append({"label": "Card context", "detail": f"Added user card references: {names}"})

        tagged_names = self._extract_tagged_cards(question)
        if tagged_names:
            tagged_entries = card_search_service.resolve_cards(tagged_names)
            if tagged_entries:
                for entry in tagged_entries:
                    if entry.name:
                        resolved_cards.setdefault(entry.name.lower(), entry)
                tag_sections = [self._format_card_entry(entry) for entry in tagged_entries]
                external_card_sections.append("Tagged cards:\n" + "\n\n".join(tag_sections))
                names = ", ".join(card.name for card in tagged_entries if card.name)
                thinking.append({"label": "Card context", "detail": f"Parsed tagged cards: {names}"})
            unmatched = {tag.lower() for tag in tagged_names}
            for entry in tagged_entries or []:
                if entry.name:
                    unmatched.discard(entry.name.lower())
            if unmatched:
                warnings.append(
                    "The following tagged cards were not found in the local Oracle database: "
                    + ", ".join(sorted(unmatched))
                )
        mentioned_rules = set(self._extract_rule_ids(question))
        missing_rules = sorted(mentioned_rules - self.rule_identifiers)
        if missing_rules:
            warnings.append(
                "These referenced rule IDs were not found in the loaded Comprehensive Rules snapshot: "
                + ", ".join(missing_rules)
            )

        resolved_list = list(resolved_cards.values())
        knowledge_sections: List[str] = []
        knowledge_names: List[str] = []
        if scryfall_cards_context:
            external_card_sections.append(f"Scryfall autocomplete:\n{scryfall_cards_context}")
            first_line = scryfall_cards_context.splitlines()[0] if scryfall_cards_context.splitlines() else scryfall_cards_context
            if first_line.lower().startswith("name:"):
                card_name = first_line.split(":", 1)[1].strip()
            else:
                card_name = first_line.strip()
            thinking.append({"label": "Card context", "detail": f"Added Scryfall summary for {card_name}"})
        if scryfall_card_name:
            citations.append(f"Scryfall autocomplete: {scryfall_card_name}")

        if resolved_list:
            names = ", ".join(entry.name for entry in resolved_list if entry.name)
            if names:
                citations.append(f"Oracle database entries: {names}")

        for entry in resolved_list:
            meta = knowledge_store.get_card(entry.name or "")
            if not meta:
                continue
            lines = [f"{meta.get('name')} — {meta.get('type_line') or ''}".strip()]
            if meta.get("color_identity"):
                lines.append(f"Color Identity: {', '.join(meta['color_identity'])}")
            if meta.get("mana_cost"):
                lines.append(f"Mana Cost: {meta['mana_cost']}")
            if meta.get("keywords"):
                lines.append(f"Keywords: {', '.join(meta['keywords'])}")
            legalities = meta.get("legalities") or {}
            commander_legality = legalities.get("commander")
            if commander_legality:
                lines.append(f"Commander legality: {commander_legality}")
            produced = meta.get("produced_mana")
            if produced:
                lines.append(f"Produces mana: {', '.join(produced)}")
            if meta.get("related_rules"):
                lines.append(f"Related rules: {', '.join(meta['related_rules'])}")
            rulings = meta.get("rulings") or []
            if rulings:
                latest = rulings[-1]
                lines.append(f"Latest ruling ({latest.get('published_at')}): {latest.get('comment')}")
            knowledge_sections.append("\n".join(lines))
            if meta.get("name"):
                knowledge_names.append(meta["name"])
        if knowledge_sections:
            payload["knowledge_context"] = "\n\n".join(knowledge_sections)
            thinking.append({"label": "Knowledge graph", "detail": "Injected structured metadata for tagged/user-selected cards."})
        else:
            payload["knowledge_context"] = ""
        if knowledge_names:
            citations.append("Knowledge graph data: " + ", ".join(knowledge_names))

        if external_card_sections:
            payload["external_cards_context"] = "\n\n".join(external_card_sections)
        if state_context:
            payload["state_context"] = state_context
            # Derive deterministic rule outputs for top suspected card and include as tools_context
            try:
                tools_context_parts = []
                top_card_name = None
                if resolved_list and resolved_list[0].name:
                    top_card_name = resolved_list[0].name
                elif isinstance(scryfall_cards_context, str) and scryfall_cards_context.startswith("Name:"):
                    top_card_name = scryfall_cards_context.splitlines()[0].split(":", 1)[1].strip()

                if top_card_name:
                    player_id = None
                    players = state_context.get("players") if isinstance(state_context, dict) else None
                    if players and len(players) > 0:
                        player_id = players[0].get("id") or players[0].get("name")
                    if player_id:
                        try:
                            from ..services.rule_engine import rule_engine
                            castable = rule_engine.is_castable(state_context or {}, player_id, top_card_name)
                            tools_context_parts.append(f"Rule:is_castable {top_card_name} => {castable}")
                        except Exception:
                            pass
                    try:
                        from ..services.rule_engine import rule_engine
                        validate = rule_engine.validate_targets(state_context or {}, {"card_name": top_card_name, "targets": []})
                        tools_context_parts.append(f"Rule:validate_targets {top_card_name} => {validate}")
                    except Exception:
                        pass

                if tools_context_parts:
                    payload["tools_context"] = "\n".join(tools_context_parts)
                    thinking.append({"label": "Rule engine", "detail": "Added deterministic rule engine checks to context"})
            except Exception:
                pass
        
        # Add player guidance based on profile
        player_guidance = self._build_player_guidance(user)
        if style_notes:
            preference_line = " ".join(style_notes)
            player_guidance = f"{player_guidance}\nConversation preferences: {preference_line}".strip()
        payload["player_guidance"] = player_guidance
        if player_guidance:
            thinking.append({"label": "Player profile", "detail": player_guidance})

        rules_docs = self.rules_retriever.get_relevant_documents(question)
        cards_docs = self.cards_retriever.get_relevant_documents(question)
        rulings_docs = self.rulings_retriever.get_relevant_documents(question)
        reference_docs: List = []
        if self.reference_retriever:
            reference_docs = self.reference_retriever.get_relevant_documents(question)

        payload["rules_context"] = rules_docs
        payload["cards_context"] = cards_docs
        payload["rulings_context"] = rulings_docs
        payload["reference_context"] = reference_docs

        reference_sources: List[str] = []
        for doc in reference_docs[:3]:
            metadata = getattr(doc, "metadata", {}) or {}
            source = metadata.get("source")
            if source and source not in reference_sources:
                reference_sources.append(source)
        if reference_sources:
            citations.append("Reference guides: " + ", ".join(reference_sources))

        summary = self._summarize_doc("Rules context", rules_docs)
        if summary:
            thinking.append(summary)
        summary = self._summarize_doc("Card knowledge", cards_docs)
        if summary:
            thinking.append(summary)
        summary = self._summarize_doc("Rulings reference", rulings_docs)
        if summary:
            thinking.append(summary)
        summary = self._summarize_doc("Commander reference", reference_docs)
        if summary:
            thinking.append(summary)

        rule_doc_ids = self._rule_ids_from_docs(rules_docs)
        if rule_doc_ids:
            citations.append("Comprehensive Rules: " + ", ".join(rule_doc_ids))
        if cards_docs:
            citations.append("Oracle text embeddings (retrieved)")
        if rulings_docs:
            citations.append("Historic rulings corpus")

        has_context = any(
            [
                rules_docs,
                cards_docs,
                rulings_docs,
                reference_docs,
                external_card_sections,
                knowledge_sections,
                state_context,
            ]
        )

        if not has_context:
            fallback = "I could not find any supporting card, rule, or ruling data for that request. Please double-check the names or provide more detail."
            answer_text = self._apply_postamble(fallback, citations, warnings)
            context_snapshot = {
                "rules": "",
                "cards": "",
                "rulings": "",
                "references": "",
                "knowledge": "",
                "player_guidance": "",
                "state": state_context or "",
                "tools": payload.get("tools_context") or "",
                "external_cards": payload.get("external_cards_context") or "",
            }
            thinking.append({"label": "Insufficient context", "detail": "No relevant documents were retrieved; returned fallback guidance."})
            return answer_text, thinking, context_snapshot

        prompt_input = self._prepare_prompt_input(payload)
        context_snapshot = {
            "rules": prompt_input.get("rules_context", ""),
            "cards": prompt_input.get("cards_context", ""),
            "rulings": prompt_input.get("rulings_context", ""),
            "references": prompt_input.get("reference_context", ""),
            "knowledge": prompt_input.get("knowledge_context", ""),
            "player_guidance": prompt_input.get("player_guidance", ""),
            "state": payload.get("state_context") or "",
            "tools": payload.get("tools_context") or "",
            "external_cards": payload.get("external_cards_context") or "",
        }
        prompt_value = self.prompt.format_prompt(**prompt_input)
        llm_response = self.llm.invoke(prompt_value.to_string())
        answer_text = llm_response if isinstance(llm_response, str) else StrOutputParser().invoke(llm_response)
        answer_text = self._apply_postamble(answer_text, citations, warnings)
        thinking.append({"label": "Final synthesis", "detail": "Generated response with llama3 via Ollama."})
        return answer_text, thinking, context_snapshot

    def _prepare_prompt_input(self, payload: dict) -> dict:
        def format_docs(value):
            if value is None:
                return ""
            if isinstance(value, str):
                return value
            if isinstance(value, list):
                parts = []
                for item in value:
                    content = getattr(item, "page_content", None)
                    parts.append(content if content is not None else str(item))
                return "\n\n".join(parts)
            return str(value)

        merged = dict(payload)
        merged["rules_context"] = format_docs(payload.get("rules_context"))
        cards_text = format_docs(payload.get("cards_context"))
        extra_cards = payload.get("external_cards_context")
        if extra_cards:
            cards_text = f"{cards_text}\n\nExternal Card Info:\n{extra_cards}".strip()
        merged["cards_context"] = cards_text
        merged["rulings_context"] = format_docs(payload.get("rulings_context"))
        merged["reference_context"] = format_docs(payload.get("reference_context"))
        merged["knowledge_context"] = payload.get("knowledge_context", "")
        merged["player_guidance"] = payload.get("player_guidance", "")
        return merged

    def _rule_ids_from_docs(self, docs: List) -> List[str]:
        if not docs:
            return []
        rule_ids: List[str] = []
        pattern = re.compile(r"(\d{3}\.\d+[a-z]?)")
        for doc in docs[:5]:
            content = getattr(doc, "page_content", "") or ""
            match = pattern.search(content)
            if match:
                candidate = match.group(1)
                if candidate not in rule_ids:
                    rule_ids.append(candidate)
        return rule_ids

    def _apply_postamble(self, text: str, citations: List[str], warnings: List[str]) -> str:
        blocks: List[str] = [text.strip()]
        if warnings:
            warning_lines = "\n".join(f"- {message}" for message in warnings)
            blocks.append(f"Warnings:\n{warning_lines}")
        if citations:
            citation_lines = "\n".join(f"- {item}" for item in citations)
            blocks.append(f"Sources:\n{citation_lines}")
        return "\n\n".join(block for block in blocks if block)


_melvin_service: MelvinService | None = None
_melvin_lock = threading.Lock()


def get_melvin_service() -> MelvinService:
    global _melvin_service
    if _melvin_service is None:
        with _melvin_lock:
            if _melvin_service is None:
                _melvin_service = MelvinService()
    return _melvin_service
