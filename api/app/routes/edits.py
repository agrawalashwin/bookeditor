from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any

from ..database import get_db
from ..models import Manuscript, ManuscriptVersion, EditSession, EditOption, AppliedEdit
from ..services.llm import LLMService
from ..services.diff import DiffService

router = APIRouter()

class EditSuggestRequest(BaseModel):
    manuscript_id: str
    instruction: str
    target_range: Dict[str, int]  # {"start": int, "end": int}
    k: int = 6
    num_options: int = 3
    style_prefs: Optional[Dict[str, str]] = None

class EditOptionResponse(BaseModel):
    option_id: str
    label: str
    before: str
    after: str
    diff: list
    severity: str

class EditSuggestResponse(BaseModel):
    edit_session_id: str
    options: list[EditOptionResponse]

@router.post("/suggest", response_model=EditSuggestResponse)
async def suggest_edit(payload: EditSuggestRequest, db: Session = Depends(get_db)):
    """Generate edit suggestions for a text range."""
    try:
        llm_service = LLMService()

        # Create edit session and generate options
        session_id = await llm_service.create_edit_session(
            db=db,
            manuscript_id=payload.manuscript_id,
            instruction=payload.instruction,
            start_char=payload.target_range["start"],
            end_char=payload.target_range["end"],
            k=payload.k,
            num_options=payload.num_options,
            style_prefs=payload.style_prefs
        )

        # Fetch the created options
        edit_session = db.query(EditSession).filter(EditSession.id == session_id).first()
        if not edit_session:
            raise HTTPException(status_code=500, detail="Failed to create edit session")

        options = []
        for option in edit_session.options:
            options.append(EditOptionResponse(
                option_id=str(option.id),
                label=option.option_label,
                before=option.before_text,
                after=option.after_text,
                diff=option.diff_json,
                severity="light"  # TODO: extract from diff_json or store separately
            ))

        return EditSuggestResponse(
            edit_session_id=session_id,
            options=options
        )

    except Exception as e:
        print(f"Error in suggest_edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ApplyRequest(BaseModel):
    edit_session_id: str
    option_id: str

@router.post("/apply")
async def apply_edit(payload: ApplyRequest, db: Session = Depends(get_db)):
    """Apply a chosen edit option to the manuscript."""
    try:
        # Get edit session and option
        edit_session = db.query(EditSession).filter(
            EditSession.id == payload.edit_session_id
        ).first()
        if not edit_session:
            raise HTTPException(status_code=404, detail="Edit session not found")

        edit_option = db.query(EditOption).filter(
            EditOption.id == payload.option_id,
            EditOption.edit_session_id == payload.edit_session_id
        ).first()
        if not edit_option:
            raise HTTPException(status_code=404, detail="Edit option not found")

        # Get current manuscript version
        manuscript = db.query(Manuscript).filter(
            Manuscript.id == edit_session.manuscript_id
        ).first()
        if not manuscript or not manuscript.current_version:
            raise HTTPException(status_code=404, detail="Manuscript or current version not found")

        current_version = manuscript.current_version

        # Apply the diff
        diff_service = DiffService()
        new_content = diff_service.apply_diff(current_version.content, edit_option.diff_json)

        # Create new version
        new_version_tag = datetime.now().isoformat()
        new_version = ManuscriptVersion(
            manuscript_id=manuscript.id,
            version_tag=new_version_tag,
            content=new_content
        )
        db.add(new_version)
        db.commit()

        # Update manuscript current version
        old_version_id = manuscript.current_version_id
        manuscript.current_version_id = new_version.id
        db.commit()

        # Record the applied edit
        applied_edit = AppliedEdit(
            edit_session_id=edit_session.id,
            chosen_option_id=edit_option.id,
            applied_by="user",  # TODO: get from auth
            from_version_id=old_version_id,
            to_version_id=new_version.id
        )
        db.add(applied_edit)
        db.commit()

        return {
            "from_version": current_version.version_tag,
            "to_version": new_version.version_tag,
            "from_version_id": str(old_version_id),
            "to_version_id": str(new_version.id)
        }

    except Exception as e:
        print(f"Error in apply_edit: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
