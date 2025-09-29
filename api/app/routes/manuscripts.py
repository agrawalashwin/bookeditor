from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4

router = APIRouter()

class ManuscriptCreate(BaseModel):
    title: str
    author: str | None = None
    content: str

@router.post("/")
async def create_manuscript(payload: ManuscriptCreate):
    # TODO: persist to DB
    manuscript_id = str(uuid4())
    return {"id": manuscript_id, "title": payload.title}

@router.get("/{manuscript_id}")
async def get_manuscript(manuscript_id: str):
    # TODO: fetch from DB
    raise HTTPException(status_code=404, detail="Not implemented")
