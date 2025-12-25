from __future__ import annotations
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterable
import os
from collections import defaultdict

from ..core.config import get_settings

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "False")
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

@dataclass
class RuleEntry:
    identifier: str
    text: str


@dataclass
class CardEntry:
    name: str
    oracle_id: Optional[str]
    type_line: Optional[str]
    oracle_text: Optional[str]


@dataclass
class RulingEntry:
    oracle_id: Optional[str]
    comment: str
    published_at: str


class IngestService:
    def __init__(self) -> None:
        settings = get_settings()
        self.rules_path = settings.raw_data_dir / "MagicCompRules 20251114.txt"
        self.cards_path = settings.raw_data_dir / "oracle-cards-20251221100301.json"
        self.rulings_path = settings.raw_data_dir / "rulings-20251221100031.json"
        self.reference_dir = settings.reference_data_dir
        self.vectorstore_path = settings.processed_data_dir / "chroma_db"
        self.knowledge_dir = settings.processed_data_dir / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        self.embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self._raw_card_payload: List[Dict[str, Any]] = []

    def ingest(self) -> None:
        rules = self._load_rules(self.rules_path)
        cards = self._load_cards(self.cards_path)
        rulings = self._load_rulings(self.rulings_path)
        reference_docs = self._load_reference_docs()

        rules_texts = [f"{rule.identifier}: {rule.text}" for rule in rules]
        cards_texts = [f"{card.name}: {card.oracle_text}" for card in cards]
        rulings_texts = [f"{ruling.comment}" for ruling in rulings]
        reference_texts = [doc["text"] for doc in reference_docs]
        reference_meta = [doc["metadata"] for doc in reference_docs]
        
        rules_chunks = self.text_splitter.create_documents(rules_texts)
        cards_chunks = self.text_splitter.create_documents(cards_texts)
        rulings_chunks = self.text_splitter.create_documents(rulings_texts)
        reference_chunks = []
        if reference_texts:
            reference_chunks = self.text_splitter.create_documents(reference_texts, metadatas=reference_meta)

        Chroma.from_documents(rules_chunks, self.embedding_function, persist_directory=str(self.vectorstore_path / "rules"))
        Chroma.from_documents(cards_chunks, self.embedding_function, persist_directory=str(self.vectorstore_path / "cards"))
        Chroma.from_documents(rulings_chunks, self.embedding_function, persist_directory=str(self.vectorstore_path / "rulings"))
        if reference_chunks:
            Chroma.from_documents(reference_chunks, self.embedding_function, persist_directory=str(self.vectorstore_path / "reference"))

        card_metadata = self._build_card_metadata(self._raw_card_payload, rulings)
        self._write_card_metadata(card_metadata)

    def _load_rules(self, path: Path) -> List[RuleEntry]:
        entries: List[RuleEntry] = []
        rule_pattern = re.compile(r"^(?P<id>\d{1,3}(?:\.\d+[a-z]?)?)\.\s+(?P<text>.+)$")
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                match = rule_pattern.match(line.strip())
                if match:
                    entries.append(
                        RuleEntry(
                            identifier=match.group("id"),
                            text=match.group("text"),
                        )
                    )
        return entries

    def _load_cards(self, path: Path) -> List[CardEntry]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self._raw_card_payload = payload
        cards: List[CardEntry] = []
        for card in payload:
            cards.append(
                CardEntry(
                    name=card.get("name"),
                    oracle_id=card.get("oracle_id"),
                    type_line=card.get("type_line"),
                    oracle_text=card.get("oracle_text"),
                )
            )
        return cards

    def _load_rulings(self, path: Path) -> List[RulingEntry]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        entries: List[RulingEntry] = []
        for ruling in payload:
            entries.append(
                RulingEntry(
                    oracle_id=ruling.get("oracle_id"),
                    comment=ruling.get("comment", ""),
                    published_at=ruling.get("published_at", ""),
                )
            )
        return entries

    def _load_reference_docs(self) -> List[dict]:
        docs: List[dict] = []
        if not self.reference_dir.exists():
            return docs
        for path in sorted(self.reference_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            docs.append({"text": text, "metadata": {"source": path.name}})
        return docs

    def _build_card_metadata(self, cards_payload: Iterable[Dict[str, Any]], rulings: List[RulingEntry]) -> Dict[str, Dict[str, Any]]:
        rulings_map: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        for ruling in rulings:
            if ruling.oracle_id:
                rulings_map[ruling.oracle_id].append(
                    {"comment": ruling.comment, "published_at": ruling.published_at}
                )
        metadata: Dict[str, Dict[str, Any]] = {}
        rule_pattern = re.compile(r"\d{3}\.\d+[a-z]?")
        for card in cards_payload:
            name = card.get("name")
            if not name:
                continue
            oracle_text = card.get("oracle_text") or ""
            oracle_id = card.get("oracle_id")
            related_rules = sorted(set(rule_pattern.findall(oracle_text)))
            entry = {
                "name": name,
                "oracle_id": oracle_id,
                "type_line": card.get("type_line"),
                "mana_cost": card.get("mana_cost"),
                "color_identity": card.get("color_identity"),
                "keywords": card.get("keywords"),
                "power": card.get("power"),
                "toughness": card.get("toughness"),
                "loyalty": card.get("loyalty"),
                "produced_mana": card.get("produced_mana"),
                "legalities": card.get("legalities"),
                "oracle_text": oracle_text,
                "related_rules": related_rules,
                "rulings": rulings_map.get(oracle_id or "", []),
            }
            metadata[name.lower()] = entry
        return metadata

    def _write_card_metadata(self, metadata: Dict[str, Dict[str, Any]]) -> None:
        target = self.knowledge_dir / "card_metadata.json"
        target.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

ingest_service = IngestService()
