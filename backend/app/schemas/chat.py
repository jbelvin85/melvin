from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, description="User question to Melvin")


class RuleSnippet(BaseModel):
    identifier: str
    text: str


class CardSnippet(BaseModel):
    name: str
    oracle_id: str | None = None
    type_line: str | None = None
    oracle_text: str | None = None


class RulingSnippet(BaseModel):
    oracle_id: str | None = None
    comment: str
    published_at: str | None = None


class ChatResponse(BaseModel):
    rules: list[RuleSnippet] = []
    cards: list[CardSnippet] = []
    rulings: list[RulingSnippet] = []
