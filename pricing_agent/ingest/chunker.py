"""Text chunking for processing large documents."""

from typing import List


def chunk_text(text: str, max_chars: int = 3000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for processing.
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text or len(text) <= max_chars:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        
        # Try to break at word boundary
        if end < len(text):
            # Look for last space, newline, or sentence boundary
            for i in range(end, max(start + max_chars // 2, end - 100), -1):
                if text[i] in [' ', '\n', '.', '!', '?']:
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks
