from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from ..core.config import get_settings


settings = get_settings()
mongo_client = AsyncIOMotorClient(settings.mongo_uri)
mongo_db = mongo_client[settings.mongo_db]
messages_collection = mongo_db["messages"]


async def append_message(
    conversation_id: int,
    sender: str,
    content: str,
    thinking: Optional[List[dict]] = None,
    context: Optional[dict] = None,
) -> None:
    document = {
        "conversation_id": conversation_id,
        "sender": sender,
        "content": content,
        "created_at": datetime.utcnow(),
    }
    if thinking:
        document["thinking"] = thinking
    if context:
        document["context"] = context
    await messages_collection.insert_one(document)


async def fetch_messages(conversation_id: int) -> List[dict]:
    cursor = messages_collection.find({"conversation_id": conversation_id}).sort("created_at", 1)
    results: List[dict] = []
    async for doc in cursor:
        results.append(
            {
                "sender": doc.get("sender", ""),
                "content": doc.get("content", ""),
                "created_at": doc.get("created_at"),
                "thinking": doc.get("thinking"),
                "context": doc.get("context"),
            }
        )
    return results
