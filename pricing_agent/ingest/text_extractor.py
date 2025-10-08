"""Text extraction from various document formats."""

import os
from pathlib import Path
from typing import Optional


def extract_text(doc_info: dict) -> Optional[str]:
    """
    Extract text from a document based on its file type.
    
    Args:
        doc_info: Document information dictionary from loader
        
    Returns:
        Extracted text or None if extraction fails
    """
    # Handle web content
    if doc_info.get('source_type') == 'web':
        return doc_info.get('content', '')
    
    # Handle local files
    file_path = doc_info['file_path']
    file_extension = doc_info['file_extension']
    
    try:
        if file_extension == '.txt':
            return _extract_txt(file_path)
        elif file_extension == '.md':
            return _extract_md(file_path)
        elif file_extension in ['.html', '.htm']:
            return _extract_html(file_path)
        elif file_extension == '.pdf':
            return _extract_pdf(file_path)
        else:
            print(f"Warning: Unsupported file type {file_extension} for {file_path}")
            return None
            
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return None


def _extract_txt(file_path: str) -> str:
    """Extract text from plain text file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def _extract_md(file_path: str) -> str:
    """Extract text from Markdown file."""
    # For now, treat as plain text
    # TODO: Use markdown parser to extract only text content
    return _extract_txt(file_path)


def _extract_html(file_path: str) -> str:
    """Extract text from HTML file."""
    # TODO: Implement HTML text extraction using BeautifulSoup or trafilatura
    # For now, return a placeholder
    return f"[HTML content from {file_path} - TODO: implement HTML parsing]"


def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    # TODO: Implement PDF text extraction using pdfplumber or PyMuPDF
    # For now, return a placeholder
    return f"[PDF content from {file_path} - TODO: implement PDF parsing]"
