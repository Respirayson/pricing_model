"""Document loader for iterating through source files and web content."""

import os
from pathlib import Path
from typing import Iterator, Dict, Any, List
from .web_scraper import WebScraper, get_pricing_sources


def iter_docs(repo_dir: str, include_web: bool = False) -> Iterator[Dict[str, Any]]:
    """
    Iterate through documents in the repository directory and optionally web sources.
    
    Args:
        repo_dir: Path to directory containing source documents
        include_web: Whether to include web-scraped content
        
    Yields:
        Dictionary with document metadata and path
    """
    # First, yield local files
    for doc in iter_local_docs(repo_dir):
        yield doc
    
    # Then, optionally yield web-scraped content
    if include_web:
        for doc in iter_web_docs():
            yield doc


def iter_local_docs(repo_dir: str) -> Iterator[Dict[str, Any]]:
    """
    Iterate through local documents in the repository directory.
    
    Args:
        repo_dir: Path to directory containing source documents
        
    Yields:
        Dictionary with document metadata and path
    """
    repo_path = Path(repo_dir)
    
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository directory not found: {repo_dir}")
    
    # Supported file extensions
    supported_extensions = {'.pdf', '.html', '.htm', '.md', '.txt'}
    
    for file_path in repo_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            # Extract relative path for source_id
            relative_path = file_path.relative_to(repo_path)
            source_id = str(relative_path).replace(os.sep, '_').replace('.', '_')
            
            yield {
                'source_id': source_id,
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_extension': file_path.suffix.lower(),
                'file_size': file_path.stat().st_size,
                'relative_path': str(relative_path),
                'source_type': 'local'
            }


def iter_web_docs() -> Iterator[Dict[str, Any]]:
    """
    Iterate through web-scraped documents.
    
    Yields:
        Dictionary with web document metadata
    """
    try:
        scraper = WebScraper(delay=1.0)
        sources = get_pricing_sources()
        
        for source in sources:
            # For now, skip placeholder URLs
            if 'example.com' in source.get('url', ''):
                continue
            
            # Create a document entry for web content
            yield {
                'source_id': source['id'],
                'source_url': source['url'],
                'source_title': source['title'],
                'published_date': source.get('date'),
                'source_type': 'web',
                'file_extension': '.html'
            }
    except Exception as e:
        print(f"Error setting up web scraping: {e}")


def scrape_and_save_web_content(output_dir: str = "repo_docs") -> List[str]:
    """
    Scrape web content and save to local files.
    
    Args:
        output_dir: Directory to save scraped content
        
    Returns:
        List of saved file paths
    """
    try:
        scraper = WebScraper(delay=2.0)
        sources = get_pricing_sources()
        
        # Filter out placeholder URLs
        real_sources = [s for s in sources if 'example.com' not in s.get('url', '')]
        
        if not real_sources:
            print("No real URLs to scrape (all are placeholders)")
            return []
        
        documents = scraper.scrape_pricing_sources(real_sources)
        saved_files = []
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for doc in documents:
            # Save as markdown file
            filename = f"{doc['source_id']}.md"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {doc['source_title']}\n\n")
                f.write(f"**Source:** {doc['source_url']}\n")
                f.write(f"**Date:** {doc.get('published_date', 'Unknown')}\n\n")
                f.write(doc['content'])
            
            saved_files.append(str(filepath))
            print(f"Saved web content to: {filepath}")
        
        return saved_files
        
    except Exception as e:
        print(f"Error scraping web content: {e}")
        return []
