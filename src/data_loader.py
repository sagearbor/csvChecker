"""CSV data loader utility with error handling."""

import pandas as pd
from typing import Union
from pathlib import Path


class CSVLoadError(Exception):
    """Custom exception for CSV loading failures."""
    pass


def load_csv(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Safely load CSV file with pandas, catching parsing errors.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded CSV data
        
    Raises:
        CSVLoadError: If file cannot be loaded or parsed
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise CSVLoadError(f"File not found: {filepath}")
        
        if not filepath.suffix.lower() == '.csv':
            raise CSVLoadError(f"File is not a CSV: {filepath}")
            
        df = pd.read_csv(filepath)
        
        if df.empty:
            raise CSVLoadError(f"CSV file is empty: {filepath}")
            
        return df
        
    except pd.errors.EmptyDataError:
        raise CSVLoadError(f"CSV file is empty or has no data: {filepath}")
    except pd.errors.ParserError as e:
        raise CSVLoadError(f"Failed to parse CSV file: {filepath}. Error: {str(e)}")
    except UnicodeDecodeError as e:
        raise CSVLoadError(f"Encoding error in CSV file: {filepath}. Error: {str(e)}")
    except Exception as e:
        raise CSVLoadError(f"Unexpected error loading CSV file: {filepath}. Error: {str(e)}")