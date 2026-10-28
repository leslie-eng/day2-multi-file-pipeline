"""
Day 2 - Multi-File Data Processing Pipeline
Squad Python Specialization - Data Engineering

Usage:
    python pipeline.py --input data/ --output output/
"""

import argparse
import csv
import logging
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS: set[str] = {
    "transaction_id",
    "date",
    "branch",
    "customer_id",
    "product",
    "quantity",
    "unit_price",
    "payment_method",
}

# to find differences between sets use 
set1 = {1, 2, 3}
set2 = {2, 3, 4}
diff = set2 - set1

# Renamed columns are not automatically mapped.
COLUMN_ALIASES: dict[str, str] = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)

data_files = Path("C:/Users/ADMIN/Desktop/Lux Dev Data Enginering/coding session/soko_fresh_supermarket/day2-multi-file-pipeline/data")

def discover_files(folder: Path, pattern: str = "transactions_*.csv") -> list[Path]:
    """Return matching CSV files in stable filename order."""
    if not folder.is_dir():
        raise FileNotFoundError(f"Input directory not found: {folder}")

    return sorted(folder.glob(pattern), key=lambda path: path.name)

#print(discover_files(data_files))
data_func = discover_files(data_files)
#print(data_func)

def read_transactions(path: Path) -> tuple[list[str], list[dict]]:
    """Read a CSV file and attach its source filename to every row."""
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path.name}")

        header = [ column.strip() if column else "" for column in reader.fieldnames ]
        #list_demo = [item for item in items if condition]
        

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


#print(data_func[0])
#print(read_transactions(data_func[0]))
prod_tuple = read_transactions(data_func[0])[0]
#print(read_transactions(data_func[0])[1][0].get("transaction_id"))

#seen_ids = {rows[item].get("transaction_id") for item in range(len(rows))}
#print(seen_ids)

def validate_columns(header: list[str], required: set[str] = REQUIRED_COLUMNS,) -> set[str]:
    """Return required columns missing from a file header."""
    return required - set(header)

# print(validate_columns(header=prod_tuple))
# print("Required columns")
# print(REQUIRED_COLUMNS)
# print("header from read_transaction")
# print(prod_tuple)


