from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from .data_loader import datastore
from ..core.config import get_settings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from ..services.scryfall import scryfall_service
from ..services.state_manager import state_manager_cls

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

        self.rules_retriever = self.rules_db.as_retriever()
        self.cards_retriever = self.cards_db.as_retriever()
        self.rulings_retriever = self.rulings_db.as_retriever()

        self.llm = Ollama(model="llama3", base_url="http://ollama:11434")
        self.prompt = ChatPromptTemplate.from_template(
            """Answer the question based only on the following context:
Rules: {rules_context}
Cards: {cards_context}
Rulings: {rulings_context}
{player_guidance}

Question: {question}
"""
        )
        self.chain = (
            RunnableParallel({
                "rules_context": self.rules_retriever, 
                "cards_context": self.cards_retriever,
                "rulings_context": self.rulings_retriever,
                "question": RunnablePassthrough()
            })
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _ensure_loaded(self) -> None:
        if not datastore.rules or not datastore.cards or not datastore.rulings:
            datastore.load()

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
        # Try to detect a card name via Scryfall autocomplete on the whole question.
        # If we get a suggestion, fetch the named card and include a short summary
        # in the `cards_context` to help the model.
        cards_context = None
        state_context = None
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
                cards_context = "\n".join(parts)
        except Exception:
            # on any failure, continue without external card context
            cards_context = None

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
        if cards_context:
            payload["cards_context"] = cards_context
        if state_context:
            payload["state_context"] = state_context

            # Derive deterministic rule outputs for top suspected card and include as tools_context
            try:
                tools_context_parts = []
                top_card_name = None
                if isinstance(cards_context, str) and cards_context.startswith("Name:"):
                    top_card_name = cards_context.splitlines()[0].split(":", 1)[1].strip()

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
            except Exception:
                pass
        
        # Add player guidance based on profile
        player_guidance = self._build_player_guidance(user)
        payload["player_guidance"] = player_guidance

        return self.chain.invoke(payload)


melvin_service = MelvinService()



