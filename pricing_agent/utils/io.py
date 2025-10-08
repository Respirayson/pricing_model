"""I/O utilities for saving and loading data."""

import json
from pathlib import Path
from typing import Any, Dict, List
from ..schemas import PriceEvidence, PriceBenchRow


def save_json(data: Any, file_path: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save file
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)


def load_json(file_path: str) -> Any:
    """
    Load data from JSON file.
    
    Args:
        file_path: Path to load file from
        
    Returns:
        Loaded data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_evidence(evidence: List[PriceEvidence], file_path: str) -> None:
    """
    Save price evidence to JSON file.
    
    Args:
        evidence: List of price evidence
        file_path: Path to save file
    """
    data = [ev.model_dump() for ev in evidence]
    save_json(data, file_path)


def load_evidence(file_path: str) -> List[PriceEvidence]:
    """
    Load price evidence from JSON file.
    
    Args:
        file_path: Path to load file from
        
    Returns:
        List of price evidence
    """
    data = load_json(file_path)
    return [PriceEvidence.model_validate(item) for item in data]


def save_benchmark(bench: List[PriceBenchRow], file_path: str) -> None:
    """
    Save price benchmark to JSON file.
    
    Args:
        bench: List of benchmark rows
        file_path: Path to save file
    """
    data = [row.model_dump() for row in bench]
    save_json(data, file_path)


def load_benchmark(file_path: str) -> List[PriceBenchRow]:
    """
    Load price benchmark from JSON file.
    
    Args:
        file_path: Path to load file from
        
    Returns:
        List of benchmark rows
    """
    data = load_json(file_path)
    return [PriceBenchRow.model_validate(item) for item in data]
