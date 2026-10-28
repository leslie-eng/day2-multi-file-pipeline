"""
Day 2 - Multi-File Data Processing Pipeline
Squad Python Specialization - Data Engineering

Usage (suggested):  python pipeline.py --input data/ --output output/
"""
import csv
import logging
from pathlib import Path
import argparse
import math

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
#data_files = discover_files(RAW, pattern="transactions_*.csv")


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
#header = read_transactions(path=data_files[0])[0]


def validate_columns(header: list[str], required: set[str] = REQUIRED_COLUMNS) -> set[str]:
    """Return the set of required columns missing from the header (empty set means valid)."""
    return required - set(header)

#print(validate_columns(header=header))


def find_problems(row: dict, seen_ids: set[str]) -> list[str]:
    """Return a list of human-readable reasons this row is invalid (empty list means valid).

    Must cover: blank required values, non-numeric or non-positive quantity/price,
    and transaction IDs already seen in this run.
    """
    problems = []

    # step 1: check every required column has a value
    for column in REQUIRED_COLUMNS:
        value = row.get(column)

        if value is None:
            problems.append("Missing required value: " + column)
        elif str(value).strip() == "":
            problems.append("Missing required value: " + column)

    # step 2: check quantity is a number and greater than 0
    qty_text = str(row.get("quantity", "")).strip()

    try:
        qty = int(qty_text)
        if qty <= 0:
            problems.append("Quantity must be greater than zero")
    except ValueError:
        problems.append("Quantity must be numeric")

    # step 3: check unit price is a number and greater than 0
    price_text = str(row.get("unit_price", "")).strip()

    try:
        price = int(price_text)
        if price <= 0:
            problems.append("Unit price must be greater than zero")
    except ValueError:
        problems.append("Unit price must be numeric")

    # step 4: check for duplicate transaction id
    tid = str(row.get("transaction_id", "")).strip()

    if tid != "":
        if tid in seen_ids:
            problems.append("Duplicate transaction ID")
            

    return problems


def clean_row(row: dict) -> dict:
    """Strip whitespace and convert numeric fields."""
    cleaned = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in row.items()
    }

    cleaned["quantity"] = float(cleaned["quantity"])
    cleaned["unit_price"] = float(cleaned["unit_price"])

    return cleaned


def write_csv(rows: list[dict], path: Path, fieldnames: list[str],) -> None:
    """Write CSV rows, creating parent folders as necessary."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def build_summary(stats: dict) -> str:
    """Format a readable processing summary."""
    return (
        "MULTI-FILE TRANSACTION PIPELINE SUMMARY\n"
        "=======================================\n"
        f"Files discovered: {stats['files_discovered']}\n"
        f"Files processed: {stats['files_processed']}\n"
        f"Files rejected: {stats['files_rejected']}\n"
        f"Rows read: {stats['rows_read']}\n"
        f"Valid transactions: {stats['valid_transactions']}\n"
        f"Rejected transactions: {stats['rejected_transactions']}\n"
    )


def run_pipeline(input_dir: Path, output_dir: Path) -> dict:
    """Discover, validate, clean, consolidate, and report."""

    # step 1: find all the csv files
    files = discover_files(input_dir)

    # counters that go into the summary at the end
    stats = {
        "files_discovered": len(files),
        "files_processed": 0,
        "files_rejected": 0,
        "rows_read": 0,
        "valid_transactions": 0,
        "rejected_transactions": 0,
    }

    valid_rows = []
    rejected_rows = []

    # one set for the whole run so duplicate ids across files are caught
    seen_ids = set()

    output_columns = sorted(REQUIRED_COLUMNS)

    if len(files) == 0:
        logger.warning("No transaction CSV files found in %s", input_dir)

    # step 2: go through each file
    for path in files:

        # try to read the file, skip it if something goes wrong
        try:
            header, rows = read_transactions(path)
        except (OSError, csv.Error, UnicodeError, ValueError) as error:
            logger.error("Could not read %s: %s", path.name, error)
            stats["files_rejected"] += 1
            continue

        stats["rows_read"] += len(rows)

        # check the file has all the columns we need
        missing_columns = validate_columns(header)

        if len(missing_columns) > 0:
            missing_text = ", ".join(sorted(missing_columns))
            logger.error("Skipping %s: missing columns: %s", path.name, missing_text)
            stats["files_rejected"] += 1

            # every row in this file goes to the rejected list
            for row in rows:
                rejected_row = dict(row)
                rejected_row["_rejection_reason"] = "Missing required columns: " + missing_text
                rejected_rows.append(rejected_row)

            continue

        stats["files_processed"] += 1

        # step 3: check each row in the file
        for row in rows:
            problems = find_problems(row, seen_ids)

            # if there are any problems, reject the row
            if len(problems) > 0:
                rejected_row = dict(row)
                rejected_row["_rejection_reason"] = "; ".join(problems)
                rejected_rows.append(rejected_row)
                continue

            # only add the id to seen_ids after the row passes validation
            transaction_id = row["transaction_id"].strip()
            seen_ids.add(transaction_id)

            cleaned = clean_row(row)

            # build the final row with only the columns we want
            valid_row = {}
            for column in output_columns:
                valid_row[column] = cleaned[column]
            valid_row["_source_file"] = cleaned["_source_file"]

            valid_rows.append(valid_row)

    # step 4: update the counts
    stats["valid_transactions"] = len(valid_rows)
    stats["rejected_transactions"] = len(rejected_rows)

    # step 5: write the output files
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_columns = output_columns + ["_source_file"]
    rejected_columns = output_columns + ["_source_file", "_rejection_reason"]

    write_csv(valid_rows, output_dir / "consolidated_transactions.csv", valid_columns)
    write_csv(rejected_rows, output_dir / "rejected_transactions.csv", rejected_columns)

    summary = build_summary(stats)

    summary_path = output_dir / "summary.txt"
    summary_path.write_text(summary, encoding="utf-8")

    logger.info("\n%s", summary)

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Multi-file transaction processing pipeline"
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data"),
        help="Directory containing transaction CSV files",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for pipeline output files",
    )

    args = parser.parse_args()

    try:
        run_pipeline(args.input, args.output)
    except (OSError, ValueError) as error:
        logger.error("Pipeline failed: %s", error)
        raise SystemExit(1)
