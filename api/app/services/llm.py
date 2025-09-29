import os
import json
from typing import List, Dict, Any, Optional
import openai
from sqlalchemy.orm import Session

from ..models import Manuscript, ManuscriptVersion, EditSession, EditOption, StylePref
from .embeddings import EmbeddingService
from .diff import DiffService


class LLMService:
    def __init__(self, model: str = None):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("GEN_MODEL", "gpt-4.1")
        self.embedding_service = EmbeddingService()
        self.diff_service = DiffService()
    
    def _get_system_prompt(self, num_options: int = 3) -> str:
        return f"""You are a developmental editor. You will produce multiple edited variations of the selected passage while preserving author voice and global style constraints.

Rules:
- Output JSON only, matching the provided schema.
- Generate exactly {num_options} options with severities: light, medium, bold.
- Maintain coherence with the provided CONTEXT.
- Do not change named entities, facts, or chronology.
- Improve clarity, flow, and concision as instructed.
- Keep the same POV and tense unless explicitly asked to change.
- Keep edits self-contained to the target range.
- Light edits: minor word choice, sentence structure improvements
- Medium edits: paragraph restructuring, moderate content changes
- Bold edits: significant rewriting while preserving core meaning"""
    
    def _get_user_prompt(
        self, 
        instruction: str, 
        target_text: str, 
        context_snippets: str, 
        style_prefs: Dict[str, str],
        start_pos: int,
        end_pos: int
    ) -> str:
        return f"""INSTRUCTION: {instruction}
TARGET_RANGE: {start_pos}-{end_pos}
TARGET_TEXT:
\"\"\"
{target_text}
\"\"\"
CONTEXT (neighboring paragraphs & retrieved chunks):
\"\"\"
{context_snippets}
\"\"\"
STYLE_PREFS:
{json.dumps(style_prefs, indent=2)}
SCHEMA:
{{
  "type": "object",
  "properties": {{
    "options": {{
      "type": "array",
      "items": {{
        "type": "object",
        "properties": {{
          "label": {{"type": "string"}},
          "severity": {{"type": "string", "enum": ["light", "medium", "bold"]}},
          "before": {{"type": "string"}},
          "after": {{"type": "string"}}
        }},
        "required": ["label", "severity", "before", "after"]
      }}
    }}
  }},
  "required": ["options"]
}}"""
    
    async def generate_edit_suggestions(
        self,
        db: Session,
        manuscript_id: str,
        instruction: str,
        start_char: int,
        end_char: int,
        k: int = 6,
        num_options: int = 3,
        style_prefs: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate edit suggestions for a text range.
        """
        # Get manuscript and current version
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        if not manuscript or not manuscript.current_version:
            raise ValueError("Manuscript or current version not found")
        
        current_version = manuscript.current_version
        content = current_version.content
        
        # Extract target text
        target_text = content[start_char:end_char]
        if not target_text.strip():
            raise ValueError("Target text is empty")
        
        # Get style preferences
        if style_prefs is None:
            style_prefs = {}
            db_style_prefs = db.query(StylePref).filter(
                StylePref.manuscript_id == manuscript_id
            ).all()
            for pref in db_style_prefs:
                style_prefs[pref.key] = pref.value
        
        # Get relevant context chunks
        context_query = f"{instruction} {target_text}"
        relevant_chunks = await self.embedding_service.retrieve_relevant_chunks(
            db, manuscript_id, context_query, k
        )
        
        # Get surrounding context
        surrounding_context = await self.embedding_service.get_context_for_range(
            db, manuscript_id, start_char, end_char, context_chars=500
        )
        
        # Combine context
        context_snippets = surrounding_context
        if relevant_chunks:
            chunk_texts = [chunk.text for chunk in relevant_chunks]
            context_snippets += "\n\n--- Retrieved Context ---\n" + "\n\n".join(chunk_texts)
        
        # Generate suggestions
        system_prompt = self._get_system_prompt(num_options)
        user_prompt = self._get_user_prompt(
            instruction, target_text, context_snippets, style_prefs, start_char, end_char
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            options = result.get("options", [])
            
            # Process options and compute diffs
            processed_options = []
            severities = ["light", "medium", "bold"]
            
            for i, option in enumerate(options[:num_options]):
                label = option.get("label", chr(65 + i))  # A, B, C
                severity = option.get("severity", severities[i % len(severities)])
                before = option.get("before", target_text)
                after = option.get("after", "")
                
                if not after:
                    continue
                
                # Compute diff
                diff_ops = self.diff_service.compute_diff(before, after)
                
                # Adjust diff positions to global coordinates
                adjusted_diff_ops = []
                for op in diff_ops:
                    adjusted_op = op.copy()
                    adjusted_op["start"] += start_char
                    adjusted_op["end"] = adjusted_op.get("end", adjusted_op["start"]) + start_char
                    adjusted_diff_ops.append(adjusted_op)
                
                processed_options.append({
                    "label": label,
                    "severity": severity,
                    "before": before,
                    "after": after,
                    "diff": adjusted_diff_ops
                })
            
            return {
                "options": processed_options,
                "target_range": {"start": start_char, "end": end_char},
                "context_used": len(context_snippets)
            }
            
        except Exception as e:
            print(f"Error generating edit suggestions: {e}")
            raise
    
    async def create_edit_session(
        self,
        db: Session,
        manuscript_id: str,
        instruction: str,
        start_char: int,
        end_char: int,
        k: int = 6,
        num_options: int = 3,
        style_prefs: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create an edit session with generated options.
        Returns the edit session ID.
        """
        # Generate suggestions
        suggestions = await self.generate_edit_suggestions(
            db, manuscript_id, instruction, start_char, end_char, k, num_options, style_prefs
        )
        
        # Create edit session
        edit_session = EditSession(
            manuscript_id=manuscript_id,
            instruction=instruction,
            target_range=f"[{start_char},{end_char})"
        )
        db.add(edit_session)
        db.commit()
        
        # Create edit options
        for option_data in suggestions["options"]:
            edit_option = EditOption(
                edit_session_id=edit_session.id,
                option_label=option_data["label"],
                before_text=option_data["before"],
                after_text=option_data["after"],
                diff_json=option_data["diff"]
            )
            db.add(edit_option)
        
        db.commit()
        
        return str(edit_session.id)
