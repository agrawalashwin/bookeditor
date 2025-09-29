import re
import tiktoken
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    start_char: int
    end_char: int
    chapter: int = None


class TextChunker:
    def __init__(self, model_name: str = "gpt-4.1", chunk_size: int = 800, overlap: int = 150):
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base encoding for newer models
            self.encoding = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = chunk_size  # in tokens
        self.overlap = overlap  # in tokens
    
    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Chunk text into overlapping segments based on token count.
        Tries to break at sentence boundaries when possible.
        """
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into sentences for better chunking boundaries
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk_sentences = []
        current_tokens = 0
        current_start_char = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))
            
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk_sentences:
                chunk_text = ''.join(current_chunk_sentences)
                chunk_end_char = current_start_char + len(chunk_text)
                
                chunks.append(TextChunk(
                    text=chunk_text.strip(),
                    start_char=current_start_char,
                    end_char=chunk_end_char,
                    chapter=self._detect_chapter(chunk_text)
                ))
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk_sentences, self.overlap)
                current_chunk_sentences = [overlap_text] if overlap_text else []
                current_tokens = len(self.encoding.encode(overlap_text)) if overlap_text else 0
                current_start_char = chunk_end_char - len(overlap_text) if overlap_text else chunk_end_char
            
            current_chunk_sentences.append(sentence)
            current_tokens += sentence_tokens
        
        # Add final chunk if there's remaining content
        if current_chunk_sentences:
            chunk_text = ''.join(current_chunk_sentences)
            chunks.append(TextChunk(
                text=chunk_text.strip(),
                start_char=current_start_char,
                end_char=current_start_char + len(chunk_text),
                chapter=self._detect_chapter(chunk_text)
            ))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences, preserving whitespace and structure."""
        # Handle markdown headings specially - don't split them
        lines = text.split('\n')
        sentences = []
        current_paragraph = []

        for line in lines:
            # If it's a heading, treat it as a separate sentence
            if line.strip().startswith('#'):
                # Finish current paragraph first
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    sentences.extend(self._split_paragraph_into_sentences(paragraph_text))
                    current_paragraph = []

                # Add heading as single sentence
                sentences.append(line + '\n')

            elif line.strip() == '':
                # Empty line - finish current paragraph
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    sentences.extend(self._split_paragraph_into_sentences(paragraph_text))
                    current_paragraph = []
                sentences.append('\n')

            else:
                # Regular line - add to current paragraph
                current_paragraph.append(line)

        # Handle remaining paragraph
        if current_paragraph:
            paragraph_text = '\n'.join(current_paragraph)
            sentences.extend(self._split_paragraph_into_sentences(paragraph_text))

        return [s for s in sentences if s.strip()]

    def _split_paragraph_into_sentences(self, paragraph: str) -> List[str]:
        """Split a paragraph into sentences."""
        sentence_pattern = r'([.!?]+\s*)'
        parts = re.split(sentence_pattern, paragraph)

        sentences = []
        for i in range(0, len(parts) - 1, 2):
            sentence = parts[i]
            if i + 1 < len(parts):
                sentence += parts[i + 1]  # Add the punctuation and whitespace
            if sentence.strip():
                sentences.append(sentence)

        # Handle case where text doesn't end with sentence punctuation
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1])

        return sentences
    
    def _get_overlap_text(self, sentences: List[str], overlap_tokens: int) -> str:
        """Get the last part of current chunk for overlap with next chunk."""
        if not sentences:
            return ""
        
        # Work backwards from the end to get approximately overlap_tokens worth
        overlap_text = ""
        current_tokens = 0
        
        for sentence in reversed(sentences):
            sentence_tokens = len(self.encoding.encode(sentence))
            if current_tokens + sentence_tokens > overlap_tokens:
                break
            overlap_text = sentence + overlap_text
            current_tokens += sentence_tokens
        
        return overlap_text
    
    def _detect_chapter(self, text: str) -> int:
        """Detect chapter number from text content."""
        # Look for chapter markers in markdown and plain text
        chapter_patterns = [
            r'#\s*chapter\s+(\d+)',  # # Chapter 1
            r'##\s*chapter\s+(\d+)', # ## Chapter 1
            r'chapter\s+(\d+)',      # Chapter 1
            r'ch\.\s*(\d+)',         # Ch. 1
            r'^#\s*(\d+)\.?\s',      # # 1. or # 1
            r'^##\s*(\d+)\.?\s',     # ## 1. or ## 1
            r'part\s+(\d+)',         # Part 1
            r'section\s+(\d+)',      # Section 1
        ]

        text_lower = text.lower()
        lines = text_lower.split('\n')

        # Check first few lines for chapter markers
        for line in lines[:5]:
            line = line.strip()
            for pattern in chapter_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        return int(match.group(1))
                    except (ValueError, IndexError):
                        continue

        return None
