from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4

router = APIRouter()

class EditSuggestRequest(BaseModel):
    manuscript_id: str
    instruction: str
    target_range: dict
    k: int = 6
    num_options: int = 3
    style_prefs: dict | None = None

@router.post("/suggest")
async def suggest_edit(payload: EditSuggestRequest):
    # TODO: call embeddings + LLM
    session_id = str(uuid4())
    options = []
    for label in ["A", "B", "C"][: payload.num_options]:
        options.append(
            {
                "option_id": str(uuid4()),
                "label": label,
                "before": "...",
                "after": "...",
                "diff": [{"op": "replace", "start": payload.target_range.get("start"), "end": payload.target_range.get("end"), "text": "..."}],
                "severity": "light",
            }
        )
    return {"edit_session_id": session_id, "options": options}

class ApplyRequest(BaseModel):
    edit_session_id: str
    option_id: str

@router.post("/apply")
async def apply_edit(payload: ApplyRequest):
    # TODO: check version, apply patch, create new version
    return {"from_version": "v0", "to_version": "v1"}
