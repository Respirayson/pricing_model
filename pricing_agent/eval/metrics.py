"""Evaluation metrics for pricing models."""

from typing import List, Tuple
import statistics


def calculate_percentiles(data: List[float]) -> Tuple[float, float, float]:
    """
    Calculate p10, p50, p90 percentiles.
    
    Args:
        data: List of values
        
    Returns:
        Tuple of (p10, p50, p90)
    """
    if not data:
        return 0.0, 0.0, 0.0
    
    sorted_data = sorted(data)
    n = len(sorted_data)
    
    def percentile(p: int) -> float:
        k = (n - 1) * p / 100
        f = int(k)
        c = k - f
        
        if f + 1 < n:
            return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
        else:
            return sorted_data[f]
    
    return percentile(10), percentile(50), percentile(90)


def calculate_mape(actual: List[float], predicted: List[float]) -> float:
    """
    Calculate Mean Absolute Percentage Error.
    
    Args:
        actual: Actual values
        predicted: Predicted values
        
    Returns:
        MAPE value
    """
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lists must have same length")
    
    if not actual:
        return 0.0
    
    errors = []
    for a, p in zip(actual, predicted):
        if a != 0:  # Avoid division by zero
            error = abs(a - p) / abs(a)
            errors.append(error)
    
    if not errors:
        return 0.0
    
    return statistics.mean(errors) * 100  # Return as percentage


def calculate_rmse(actual: List[float], predicted: List[float]) -> float:
    """
    Calculate Root Mean Square Error.
    
    Args:
        actual: Actual values
        predicted: Predicted values
        
    Returns:
        RMSE value
    """
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lists must have same length")
    
    if not actual:
        return 0.0
    
    squared_errors = [(a - p) ** 2 for a, p in zip(actual, predicted)]
    mse = statistics.mean(squared_errors)
    return mse ** 0.5
