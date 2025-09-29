from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, INT4RANGE
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from .database import Base


class Manuscript(Base):
    __tablename__ = "manuscripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    author = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    current_version_id = Column(UUID(as_uuid=True), ForeignKey("manuscript_versions.id"))
    
    # Relationships
    versions = relationship("ManuscriptVersion", back_populates="manuscript", cascade="all, delete-orphan", foreign_keys="ManuscriptVersion.manuscript_id")
    current_version = relationship("ManuscriptVersion", foreign_keys=[current_version_id], post_update=True)
    edit_sessions = relationship("EditSession", back_populates="manuscript", cascade="all, delete-orphan")
    style_prefs = relationship("StylePref", back_populates="manuscript", cascade="all, delete-orphan")


class ManuscriptVersion(Base):
    __tablename__ = "manuscript_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manuscript_id = Column(UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False)
    version_tag = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    manuscript = relationship("Manuscript", back_populates="versions", foreign_keys=[manuscript_id])
    chunks = relationship("Chunk", back_populates="manuscript_version", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manuscript_version_id = Column(UUID(as_uuid=True), ForeignKey("manuscript_versions.id", ondelete="CASCADE"), nullable=False)
    chapter = Column(Integer)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    
    # Relationships
    manuscript_version = relationship("ManuscriptVersion", back_populates="chunks")
    embedding = relationship("ChunkEmbedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"
    
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(Vector(3072))  # OpenAI text-embedding-3-large dimension
    
    # Relationships
    chunk = relationship("Chunk", back_populates="embedding")


class EditSession(Base):
    __tablename__ = "edit_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manuscript_id = Column(UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False)
    instruction = Column(Text, nullable=False)
    target_range = Column(INT4RANGE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    manuscript = relationship("Manuscript", back_populates="edit_sessions")
    options = relationship("EditOption", back_populates="edit_session", cascade="all, delete-orphan")
    applied_edit = relationship("AppliedEdit", back_populates="edit_session", uselist=False)


class EditOption(Base):
    __tablename__ = "edit_options"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    edit_session_id = Column(UUID(as_uuid=True), ForeignKey("edit_sessions.id", ondelete="CASCADE"), nullable=False)
    option_label = Column(String, nullable=False)
    before_text = Column(Text, nullable=False)
    after_text = Column(Text, nullable=False)
    diff_json = Column(JSON, nullable=False)
    
    # Relationships
    edit_session = relationship("EditSession", back_populates="options")


class AppliedEdit(Base):
    __tablename__ = "applied_edits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    edit_session_id = Column(UUID(as_uuid=True), ForeignKey("edit_sessions.id", ondelete="CASCADE"), nullable=False)
    chosen_option_id = Column(UUID(as_uuid=True), ForeignKey("edit_options.id"))
    applied_by = Column(String)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    from_version_id = Column(UUID(as_uuid=True), ForeignKey("manuscript_versions.id"))
    to_version_id = Column(UUID(as_uuid=True), ForeignKey("manuscript_versions.id"))
    
    # Relationships
    edit_session = relationship("EditSession", back_populates="applied_edit")
    chosen_option = relationship("EditOption")
    from_version = relationship("ManuscriptVersion", foreign_keys=[from_version_id])
    to_version = relationship("ManuscriptVersion", foreign_keys=[to_version_id])


class StylePref(Base):
    __tablename__ = "style_prefs"
    
    manuscript_id = Column(UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE"), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(Text)
    
    # Relationships
    manuscript = relationship("Manuscript", back_populates="style_prefs")
