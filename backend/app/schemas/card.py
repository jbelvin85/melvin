from pydantic import BaseModel


class CardSummary(BaseModel):
    name: str
    type_line: str | None = None
    oracle_text: str | None = None


class CardSearchResponse(BaseModel):
    results: list[CardSummary]
