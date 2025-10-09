"""Configuration settings for the pricing agent."""

import os
from typing import Optional
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration for the pricing agent."""
    
    # LLM settings
    llm_api_key: Optional[str] = Field(default=None, description="API key for LLM provider")
    llm_model: str = Field(default="gpt-4.1-nano", description="LLM model to use")
    llm_temperature: float = Field(default=0.1, description="LLM temperature for deterministic output")
    llm_max_tokens: int = Field(default=2000, description="Maximum tokens for LLM response")
    
    # Processing settings
    chunk_size: int = Field(default=3000, description="Maximum characters per text chunk")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    min_confidence: float = Field(default=0.5, description="Minimum confidence for price evidence")
    
    # File paths
    repo_docs_dir: str = Field(default="repo_docs", description="Directory containing source documents")
    sources_file: str = Field(default="sources.yml", description="Sources manifest file")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls(
            llm_api_key=os.getenv("LLM_API_KEY"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4.1-nano"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "3000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            min_confidence=float(os.getenv("MIN_CONFIDENCE", "0.5")),
            repo_docs_dir=os.getenv("REPO_DOCS_DIR", "repo_docs"),
            sources_file=os.getenv("SOURCES_FILE", "sources.yml"),
        )
