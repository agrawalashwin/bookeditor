import json
from typing import List, Dict, Any
from diff_match_patch import diff_match_patch
from dataclasses import dataclass


@dataclass
class DiffOperation:
    op: str  # 'replace', 'insert', 'delete'
    start: int
    end: int
    text: str = ""


class DiffService:
    def __init__(self):
        self.dmp = diff_match_patch()
        # Configure for better performance and readability
        self.dmp.Diff_Timeout = 1.0
        self.dmp.Diff_EditCost = 4
    
    def compute_diff(self, before: str, after: str) -> List[Dict[str, Any]]:
        """
        Compute diff between before and after text.
        Returns a list of operations that can be applied to transform before -> after.
        """
        # Normalize line endings
        before = before.replace('\r\n', '\n').replace('\r', '\n')
        after = after.replace('\r\n', '\n').replace('\r', '\n')
        
        # Compute the diff
        diffs = self.dmp.diff_main(before, after)
        self.dmp.diff_cleanupSemantic(diffs)
        
        # Convert to our operation format
        operations = []
        current_pos = 0
        
        for op, text in diffs:
            if op == diff_match_patch.DIFF_EQUAL:
                current_pos += len(text)
            elif op == diff_match_patch.DIFF_DELETE:
                operations.append({
                    "op": "delete",
                    "start": current_pos,
                    "end": current_pos + len(text),
                    "text": ""
                })
                current_pos += len(text)
            elif op == diff_match_patch.DIFF_INSERT:
                operations.append({
                    "op": "insert",
                    "start": current_pos,
                    "end": current_pos,
                    "text": text
                })
                # Don't advance position for inserts
        
        # Merge adjacent operations for cleaner diffs
        return self._merge_operations(operations)
    
    def _merge_operations(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge adjacent delete/insert operations into replace operations."""
        if not operations:
            return operations
        
        merged = []
        i = 0
        
        while i < len(operations):
            current = operations[i]
            
            # Check if we can merge with next operation
            if (i + 1 < len(operations) and 
                current["op"] == "delete" and 
                operations[i + 1]["op"] == "insert" and
                current["end"] == operations[i + 1]["start"]):
                
                # Merge delete + insert into replace
                next_op = operations[i + 1]
                merged.append({
                    "op": "replace",
                    "start": current["start"],
                    "end": current["end"],
                    "text": next_op["text"]
                })
                i += 2
            else:
                merged.append(current)
                i += 1
        
        return merged
    
    def apply_diff(self, original: str, operations: List[Dict[str, Any]]) -> str:
        """
        Apply a list of diff operations to the original text.
        Operations should be sorted by start position in descending order.
        """
        # Sort operations by start position (descending) to avoid position shifts
        sorted_ops = sorted(operations, key=lambda x: x["start"], reverse=True)
        
        result = original
        
        for op in sorted_ops:
            op_type = op["op"]
            start = op["start"]
            end = op.get("end", start)
            text = op.get("text", "")
            
            if op_type == "replace":
                result = result[:start] + text + result[end:]
            elif op_type == "insert":
                result = result[:start] + text + result[start:]
            elif op_type == "delete":
                result = result[:start] + result[end:]
        
        return result
    
    def get_diff_preview(self, before: str, after: str, context_chars: int = 150) -> Dict[str, Any]:
        """
        Generate a preview of the diff with limited context for UI display.
        """
        operations = self.compute_diff(before, after)
        
        if not operations:
            return {
                "has_changes": False,
                "preview": before[:context_chars * 2] + ("..." if len(before) > context_chars * 2 else ""),
                "operations": []
            }
        
        # Find the range of changes
        min_start = min(op["start"] for op in operations)
        max_end = max(op.get("end", op["start"]) for op in operations)
        
        # Expand to include context
        context_start = max(0, min_start - context_chars)
        context_end = min(len(after), max_end + context_chars)
        
        # Get the preview text (after changes)
        preview_text = after[context_start:context_end]
        
        # Adjust operation positions relative to preview
        adjusted_operations = []
        for op in operations:
            if op["start"] >= context_start and op["start"] <= context_end:
                adjusted_op = op.copy()
                adjusted_op["start"] -= context_start
                adjusted_op["end"] = adjusted_op.get("end", adjusted_op["start"]) - context_start
                adjusted_operations.append(adjusted_op)
        
        return {
            "has_changes": True,
            "preview": preview_text,
            "operations": adjusted_operations,
            "context_start": context_start,
            "context_end": context_end
        }
    
    def validate_operations(self, original: str, operations: List[Dict[str, Any]]) -> bool:
        """
        Validate that operations can be safely applied to the original text.
        """
        try:
            # Try to apply the operations
            result = self.apply_diff(original, operations)
            return True
        except Exception:
            return False
