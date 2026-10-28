"""
Day 2 - Multi-File Data Processing Pipeline
Squad Python Specialization - Data Engineering

Usage (suggested):  python pipeline.py --input data/ --output output/
"""
import csv
import logging
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS: set[str] = {
    "transaction_id", "date", "branch", "customer_id",
    "product", "quantity", "unit_price", "payment_method",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)

RAW = Path("C:/Users/ADMIN/Desktop/Lux Dev Data Enginering/coding session/soko_fresh_supermarket/day2-multi-file-pipeline/data")

# TODO: decide whether a known alias (e.g. a renamed column) should be mapped or rejected,
# and record the decision in your README.
COLUMN_ALIASES: dict[str, str] = {}


def discover_files( folder: Path, pattern: str = "transactions_*.csv") -> list[Path]:
    """Return matching CSV files in stable filename order."""
    
    if not folder.is_dir():
        logging.error(msg=f"The input directory {folder} does not exist")
        return []

    return sorted(folder.glob(pattern))
data_files = discover_files(RAW, pattern="transactions_*.csv")


def read_transactions(path: Path) -> tuple[list[str], list[dict]]:
    """Read a CSV file and attach its source filename to every row."""
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path.name}")

        header = [
            column.strip() if column else ""
            for column in reader.fieldnames
        ]

        rows = []

        for raw_row in reader:
            row = {
                (key.strip() if key else ""): value
                for key, value in raw_row.items()
                if key is not None
            }
            row["_source_file"] = path.name
            rows.append(row)

    return header, rows
header = read_transactions(path=data_files[0])[0]


def validate_columns(header: list[str], required: set[str] = REQUIRED_COLUMNS) -> set[str]:
    """Return the set of required columns missing from the header (empty set means valid)."""
    return required - set(header)

print(validate_columns(header=header))


def find_problems(row: dict, seen_ids: set[str]) -> list[str]:
    """Return a list of human-readable reasons this row is invalid (empty list means valid).

    Must cover: blank required values, non-numeric or non-positive quantity/price,
    and transaction IDs already seen in this run.
    """
    raise NotImplementedError


def clean_row(row: dict) -> dict:
    """Return a normalised copy of a valid row (types converted, whitespace stripped)."""
    raise NotImplementedError


def write_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    """Write rows to CSV, creating parent folders as needed."""
    raise NotImplementedError


def build_summary(stats: dict) -> str:
    """Format the processing summary shown in the expected-output resource."""
    raise NotImplementedError


def run_pipeline(input_dir: Path, output_dir: Path) -> dict:
    """Run every step and return the statistics used by build_summary()."""
    # TODO
    pass


if __name__ == "__main__":
    # TODO: parse arguments, call run_pipeline, print the summary
    pass
