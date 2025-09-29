import os
import asyncio
from typing import List, Optional
import openai
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models import Chunk, ChunkEmbedding, ManuscriptVersion
from .chunking import TextChunker, TextChunk


class EmbeddingService:
    def __init__(self, model: str = None):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("EMBED_MODEL", "text-embedding-3-large")
        self.chunker = TextChunker()
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch."""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise
    
    async def process_manuscript_version(self, db: Session, version_id: str) -> None:
        """
        Process a manuscript version: chunk the text and generate embeddings.
        """
        # Get the manuscript version
        version = db.query(ManuscriptVersion).filter(ManuscriptVersion.id == version_id).first()
        if not version:
            raise ValueError(f"Manuscript version {version_id} not found")
        
        # Delete existing chunks and embeddings for this version
        existing_chunks = db.query(Chunk).filter(Chunk.manuscript_version_id == version_id).all()
        for chunk in existing_chunks:
            db.query(ChunkEmbedding).filter(ChunkEmbedding.chunk_id == chunk.id).delete()
            db.delete(chunk)
        db.commit()
        
        # Chunk the text
        text_chunks = self.chunker.chunk_text(version.content)
        
        if not text_chunks:
            return
        
        # Create chunk records
        chunk_records = []
        for text_chunk in text_chunks:
            chunk_record = Chunk(
                manuscript_version_id=version_id,
                chapter=text_chunk.chapter,
                start_char=text_chunk.start_char,
                end_char=text_chunk.end_char,
                text=text_chunk.text
            )
            db.add(chunk_record)
            chunk_records.append(chunk_record)
        
        db.commit()
        
        # Generate embeddings in batches
        batch_size = 64
        chunk_texts = [chunk.text for chunk in text_chunks]
        
        for i in range(0, len(chunk_texts), batch_size):
            batch_texts = chunk_texts[i:i + batch_size]
            batch_chunks = chunk_records[i:i + batch_size]
            
            try:
                embeddings = await self.embed_texts(batch_texts)
                
                # Store embeddings
                for chunk_record, embedding in zip(batch_chunks, embeddings):
                    chunk_embedding = ChunkEmbedding(
                        chunk_id=chunk_record.id,
                        embedding=embedding
                    )
                    db.add(chunk_embedding)
                
                db.commit()
                
            except Exception as e:
                print(f"Error processing batch {i//batch_size + 1}: {e}")
                db.rollback()
                raise
    
    async def retrieve_relevant_chunks(
        self, 
        db: Session, 
        manuscript_id: str, 
        query_text: str, 
        k: int = 6
    ) -> List[Chunk]:
        """
        Retrieve the most relevant chunks for a query using vector similarity.
        """
        # Generate embedding for the query
        query_embedding = await self.embed_text(query_text)
        
        # Query for similar chunks using cosine similarity
        query = text("""
            SELECT c.*, ce.embedding <=> :query_embedding as distance
            FROM chunks c
            JOIN chunk_embeddings ce ON c.id = ce.chunk_id
            JOIN manuscript_versions mv ON c.manuscript_version_id = mv.id
            JOIN manuscripts m ON mv.manuscript_id = m.id
            WHERE m.id = :manuscript_id
            ORDER BY ce.embedding <=> :query_embedding
            LIMIT :k
        """)
        
        result = db.execute(query, {
            "query_embedding": str(query_embedding),
            "manuscript_id": manuscript_id,
            "k": k
        })
        
        chunk_ids = [row[0] for row in result.fetchall()]
        
        # Fetch full chunk objects
        chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        
        # Sort by the original similarity order
        chunk_dict = {str(chunk.id): chunk for chunk in chunks}
        ordered_chunks = [chunk_dict[chunk_id] for chunk_id in chunk_ids if chunk_id in chunk_dict]
        
        return ordered_chunks
    
    async def get_context_for_range(
        self, 
        db: Session, 
        manuscript_id: str, 
        start_char: int, 
        end_char: int, 
        context_chars: int = 1000
    ) -> str:
        """
        Get surrounding context for a character range in the manuscript.
        """
        # Get the current version
        manuscript = db.query(ManuscriptVersion).join(
            ManuscriptVersion.manuscript
        ).filter_by(id=manuscript_id).first()
        
        if not manuscript:
            return ""
        
        content = manuscript.content
        
        # Expand the range to include context
        context_start = max(0, start_char - context_chars)
        context_end = min(len(content), end_char + context_chars)
        
        return content[context_start:context_end]
