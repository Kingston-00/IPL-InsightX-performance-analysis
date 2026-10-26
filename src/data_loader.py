"""Loading the two IPL CSV files from disk.

The deliveries file in some public IPL datasets is padded with spaces (every
value is padded to a fixed width), which makes it very large in memory. We
therefore read it in chunks and strip the spaces.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger("ipl_insightx")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MATCHES_FILE = "matches.csv"
DELIVERIES_FILE = "deliveries.csv"

# Text values that mean "no value" in the source files.
NA_TOKENS = {"", "NA", "N/A", "NaN", "nan", "None", "null"}


MEMORY_MESSAGE = ("Not enough free memory (RAM) to read {name}. The file itself is fine. Close other programs "
                  "(browser tabs, other editors), then restart the app. See 'Common errors' in the README.")


class DataFileError(Exception):
    """Raised when a data file is missing, empty or unreadable."""


def _strip_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Strip spaces from headers and text values and turn NA tokens into NaN."""
    chunk.columns = [str(c).strip() for c in chunk.columns]
    for col in chunk.columns:
        values = chunk[col].str.strip()
        chunk[col] = values.mask(values.isin(NA_TOKENS))
    return chunk


def read_csv_clean(path: Path, chunksize: int = 20_000) -> pd.DataFrame:
    """Read a CSV as text, strip padding and return one DataFrame.

    Everything stays as text here; numeric conversion happens in data_cleaning
    where invalid values can be counted and reported.
    """
    path = Path(path)
    if not path.is_file():
        raise DataFileError(f"File not found: {path.name}")
    if path.stat().st_size == 0:
        raise DataFileError(f"File is empty: {path.name}")
    try:
        parts = [
            _strip_chunk(chunk)
            for chunk in pd.read_csv(path, dtype=str, chunksize=chunksize, keep_default_na=False)
        ]
    except pd.errors.EmptyDataError as exc:
        raise DataFileError(f"File has no data: {path.name}") from exc
    except MemoryError as exc:
        logger.exception("Out of memory while reading %s", path)
        raise DataFileError(MEMORY_MESSAGE.format(name=path.name)) from exc
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        logger.exception("Could not parse %s", path)
        if "out of memory" in str(exc).lower():      # the C parser reports memory shortage as a ParserError
            raise DataFileError(MEMORY_MESSAGE.format(name=path.name)) from exc
        raise DataFileError(f"Could not read {path.name}: it does not look like a valid CSV file.") from exc
    if not parts:
        raise DataFileError(f"File has no rows: {path.name}")
    frame = pd.concat(parts, ignore_index=True)
    if frame.empty:
        raise DataFileError(f"File has no rows: {path.name}")
    return frame


def missing_files(data_dir: Path = DATA_DIR) -> list[str]:
    """Return the names of required CSV files that are not in data_dir."""
    data_dir = Path(data_dir)
    return [name for name in (MATCHES_FILE, DELIVERIES_FILE) if not (data_dir / name).is_file()]


def load_raw_matches(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load matches.csv as text."""
    return read_csv_clean(Path(data_dir) / MATCHES_FILE)


def load_raw_deliveries(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load deliveries.csv as text."""
    return read_csv_clean(Path(data_dir) / DELIVERIES_FILE)
