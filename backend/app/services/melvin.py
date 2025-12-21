from __future__ import annotations
from .data_loader import datastore
from ..core.config import get_settings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough


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

    def answer_question(self, question: str) -> str:
        return self.chain.invoke(question)


melvin_service = MelvinService()


