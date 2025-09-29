from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import asyncio
import io

from ..database import get_db
from ..models import Manuscript, ManuscriptVersion, StylePref
from ..services.embeddings import EmbeddingService
from ..services.export import ExportService

router = APIRouter()

class ManuscriptCreate(BaseModel):
    title: str
    author: Optional[str] = None
    content: str

class ManuscriptResponse(BaseModel):
    id: str
    title: str
    author: Optional[str]
    created_at: datetime
    current_version_id: Optional[str]

class StylePrefUpdate(BaseModel):
    key: str
    value: str

@router.post("/", response_model=ManuscriptResponse)
async def create_manuscript(payload: ManuscriptCreate, db: Session = Depends(get_db)):
    """Create a new manuscript with initial version."""
    # Create manuscript
    manuscript = Manuscript(
        title=payload.title,
        author=payload.author
    )
    db.add(manuscript)
    db.commit()

    # Create initial version
    version_tag = datetime.now().isoformat()
    initial_version = ManuscriptVersion(
        manuscript_id=manuscript.id,
        version_tag=version_tag,
        content=payload.content
    )
    db.add(initial_version)
    db.commit()

    # Update manuscript to point to current version
    manuscript.current_version_id = initial_version.id
    db.commit()

    # Process embeddings in background
    embedding_service = EmbeddingService()
    asyncio.create_task(
        embedding_service.process_manuscript_version(db, str(initial_version.id))
    )

    return ManuscriptResponse(
        id=str(manuscript.id),
        title=manuscript.title,
        author=manuscript.author,
        created_at=manuscript.created_at,
        current_version_id=str(manuscript.current_version_id)
    )

@router.get("/{manuscript_id}", response_model=ManuscriptResponse)
async def get_manuscript(manuscript_id: str, db: Session = Depends(get_db)):
    """Get manuscript metadata."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    return ManuscriptResponse(
        id=str(manuscript.id),
        title=manuscript.title,
        author=manuscript.author,
        created_at=manuscript.created_at,
        current_version_id=str(manuscript.current_version_id) if manuscript.current_version_id else None
    )

@router.get("/{manuscript_id}/content")
async def get_manuscript_content(manuscript_id: str, db: Session = Depends(get_db)):
    """Get current manuscript content."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript or not manuscript.current_version:
        raise HTTPException(status_code=404, detail="Manuscript or current version not found")

    return {"content": manuscript.current_version.content}

@router.post("/{manuscript_id}/ingest")
async def ingest_manuscript(manuscript_id: str, db: Session = Depends(get_db)):
    """Re-process manuscript for embeddings."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript or not manuscript.current_version_id:
        raise HTTPException(status_code=404, detail="Manuscript or current version not found")

    embedding_service = EmbeddingService()
    await embedding_service.process_manuscript_version(db, str(manuscript.current_version_id))

    return {"status": "success", "message": "Manuscript processed for embeddings"}

@router.put("/{manuscript_id}/style")
async def update_style_prefs(
    manuscript_id: str,
    style_prefs: dict,
    db: Session = Depends(get_db)
):
    """Update style preferences for manuscript."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Delete existing preferences
    db.query(StylePref).filter(StylePref.manuscript_id == manuscript_id).delete()

    # Add new preferences
    for key, value in style_prefs.items():
        style_pref = StylePref(
            manuscript_id=manuscript_id,
            key=key,
            value=str(value)
        )
        db.add(style_pref)

    db.commit()
    return {"status": "success", "updated_prefs": style_prefs}

@router.get("/{manuscript_id}/history")
async def get_manuscript_history(manuscript_id: str, db: Session = Depends(get_db)):
    """Get manuscript version history."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    versions = db.query(ManuscriptVersion).filter(
        ManuscriptVersion.manuscript_id == manuscript_id
    ).order_by(ManuscriptVersion.created_at.desc()).all()

    return {
        "versions": [
            {
                "id": str(version.id),
                "version_tag": version.version_tag,
                "created_at": version.created_at,
                "is_current": version.id == manuscript.current_version_id
            }
            for version in versions
        ]
    }

@router.post("/{manuscript_id}/export")
async def export_manuscript(
    manuscript_id: str,
    format: str = "markdown",  # "markdown" or "docx"
    db: Session = Depends(get_db)
):
    """Export manuscript to specified format."""
    export_service = ExportService()

    try:
        if format.lower() == "markdown":
            content = export_service.export_to_markdown(db, manuscript_id)
            filename = export_service.get_export_filename(db, manuscript_id, "markdown")

            return StreamingResponse(
                io.StringIO(content),
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        elif format.lower() == "docx":
            buffer = export_service.export_to_docx(db, manuscript_id)
            filename = export_service.get_export_filename(db, manuscript_id, "docx")

            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'markdown' or 'docx'")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/{manuscript_id}/revert")
async def revert_manuscript(
    manuscript_id: str,
    to_version_id: str,
    db: Session = Depends(get_db)
):
    """Revert manuscript to a previous version."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    target_version = db.query(ManuscriptVersion).filter(
        ManuscriptVersion.id == to_version_id,
        ManuscriptVersion.manuscript_id == manuscript_id
    ).first()
    if not target_version:
        raise HTTPException(status_code=404, detail="Target version not found")

    # Update current version
    old_version_id = manuscript.current_version_id
    manuscript.current_version_id = target_version.id
    db.commit()

    return {
        "status": "success",
        "from_version_id": str(old_version_id),
        "to_version_id": str(target_version.id),
        "reverted_to": target_version.version_tag
    }
