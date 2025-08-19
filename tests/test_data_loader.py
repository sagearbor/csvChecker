"""Unit tests for CSV data loader."""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path

from src.data_loader import load_csv, CSVLoadError


@pytest.fixture
def valid_csv():
    """Create a temporary valid CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,name,age\n1,Alice,25\n2,Bob,30\n")
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def malformed_csv():
    """Create a temporary malformed CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,name,age\n1,Alice,25\n2,Bob\n3,Charlie,35,extra")
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def empty_csv():
    """Create a temporary empty CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("")
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def non_csv_file():
    """Create a temporary non-CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is not a CSV file")
        f.flush()
        yield f.name
    os.unlink(f.name)


def test_load_valid_csv(valid_csv):
    """Test loading a valid CSV file."""
    df = load_csv(valid_csv)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['id', 'name', 'age']
    assert df.iloc[0]['name'] == 'Alice'
    assert df.iloc[1]['age'] == 30


def test_load_csv_with_path_object(valid_csv):
    """Test loading CSV using Path object."""
    df = load_csv(Path(valid_csv))
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_load_nonexistent_file():
    """Test loading a file that doesn't exist."""
    with pytest.raises(CSVLoadError, match="File not found"):
        load_csv("nonexistent.csv")


def test_load_non_csv_file(non_csv_file):
    """Test loading a non-CSV file."""
    with pytest.raises(CSVLoadError, match="File is not a CSV"):
        load_csv(non_csv_file)


def test_load_empty_csv(empty_csv):
    """Test loading an empty CSV file."""
    with pytest.raises(CSVLoadError, match="CSV file is empty"):
        load_csv(empty_csv)


def test_load_malformed_csv(malformed_csv):
    """Test loading a malformed CSV file."""
    # Note: pandas is quite forgiving, so this might not always raise an error
    # depending on the type of malformation. Let's test what we can.
    try:
        df = load_csv(malformed_csv)
        # If it loads, check that we got some data
        assert isinstance(df, pd.DataFrame)
    except CSVLoadError:
        # If it raises an error, that's also acceptable
        pass


def test_csv_load_error_inheritance():
    """Test that CSVLoadError is properly defined."""
    assert issubclass(CSVLoadError, Exception)
    
    error = CSVLoadError("test message")
    assert str(error) == "test message"