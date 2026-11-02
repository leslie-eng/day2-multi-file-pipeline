"""
Day 2 - Multi-File Data Processing Pipeline
Squad Python Specialization - Data Engineering

Usage (suggested):  python pipeline.py --input data/ --output output/
"""
import csv
import logging
from pathlib import Path
import argparse

REQUIRED_COLUMNS: set[str] = {
    "transaction_id", "date", "branch", "customer_id",
    "product", "quantity", "unit_price", "payment_method",
}

VALID_COLUMNS = [
    "transaction_id", "date", "branch", "customer_id", "product",
    "quantity", "unit_price", "line_total", "payment_method",
    "payment_ref", "source_file",
]
REJECTED_COLUMNS = [
    "payment_ref", "source_file", "row_number", "transaction_id", "reasons",
]

# "qty" is accepted as a documented alias for the canonical "quantity" column.
COLUMN_ALIASES: dict[str, str] = {"qty": "quantity"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def discover_files(folder: Path, pattern: str = "transactions_*.csv") -> list[Path]:
    """Return matching CSV files in stable filename order."""
    if not folder.is_dir():
        logging.error("The input directory %s does not exist", folder)
        return []
    return sorted(folder.glob(pattern))


def canonical_column(column: str) -> str:
    column = column.strip()
    return COLUMN_ALIASES.get(column, column)


def read_transactions(path: Path) -> tuple[list[str], list[dict]]:
    """Read a CSV file and attach source metadata and physical row numbers."""
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path.name}")

        header = [canonical_column(column) for column in reader.fieldnames]
        rows = []
        for row_number, raw_row in enumerate(reader, start=2):
            row = {
                canonical_column(key.strip() if key else ""): value
                for key, value in raw_row.items()
                if key is not None
            }
            row["source_file"] = path.name
            row["row_number"] = row_number
            rows.append(row)

    return header, rows


def validate_columns(header: list[str], required: set[str] = REQUIRED_COLUMNS) -> set[str]:
    """Return required columns missing from the normalized header."""
    return required - set(header)


def find_problems(row: dict, seen_ids: set[str]) -> list[str]:
    """Return validation problems for a transaction row."""
    problems = []

    for column in REQUIRED_COLUMNS:
        value = row.get(column)
        if value is None or str(value).strip() == "":
            problems.append("Missing required value: " + column)

    qty_text = str(row.get("quantity", "")).strip()
    try:
        qty = int(qty_text)
        if qty <= 0:
            problems.append("Quantity must be greater than zero")
    except ValueError:
        if qty_text != "":
            problems.append("Quantity must be numeric")

    price_text = str(row.get("unit_price", "")).strip()
    try:
        price = float(price_text)
        if price <= 0:
            problems.append("Unit price must be greater than zero")
    except ValueError:
        if price_text != "":
            problems.append("Unit price must be numeric")

    tid = str(row.get("transaction_id", "")).strip()
    if tid != "" and tid in seen_ids:
        problems.append("Duplicate transaction ID")

    return problems


def clean_row(row: dict) -> dict:
    """Strip text and convert numeric fields to their output types."""
    cleaned = {
        key: (value.strip() if isinstance(value, str) else value)
        for key, value in row.items()
    }
    cleaned["quantity"] = int(cleaned["quantity"])
    cleaned["unit_price"] = float(cleaned["unit_price"])
    cleaned["line_total"] = cleaned["quantity"] * cleaned["unit_price"]
    return cleaned


def write_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_summary(stats: dict) -> str:
    """Format processing counts, rejection reasons, and total revenue."""
    lines = [
        "MULTI-FILE TRANSACTION PIPELINE SUMMARY",
        "=======================================",
        f"Files discovered: {stats['files_discovered']}",
        f"Files processed: {stats['files_processed']}",
        f"Files rejected: {stats['files_rejected']}",
        f"Rows read: {stats['rows_read']}",
        f"Valid transactions: {stats['valid_transactions']}",
        f"Rejected transactions: {stats['rejected_transactions']}",
        f"Total revenue: {stats['total_revenue']:.2f}",
        "",
        "REJECTION REASONS",
        "=================",
    ]
    for reason, count in sorted(stats["reason_counts"].items()):
        lines.append(f"{reason}: {count}")
    return "\n".join(lines) + "\n"


def run_pipeline(input_dir: Path, output_dir: Path) -> dict:
    files = discover_files(input_dir)
    stats = {
        "files_discovered": len(files), "files_processed": 0,
        "files_rejected": 0, "rows_read": 0,
        "valid_transactions": 0, "rejected_transactions": 0,
        "total_revenue": 0.0, "reason_counts": {},
    }
    valid_rows, rejected_rows = [], []
    seen_ids = set()

    if not files:
        logger.warning("No transaction CSV files found in %s", input_dir)

    for path in files:
        try:
            header, rows = read_transactions(path)
        except (OSError, csv.Error, UnicodeError, ValueError) as error:
            logger.error("Could not read %s: %s", path.name, error)
            stats["files_rejected"] += 1
            continue

        stats["rows_read"] += len(rows)
        missing_columns = validate_columns(header)
        if missing_columns:
            missing_text = ", ".join(sorted(missing_columns))
            logger.error("Skipping %s: missing columns: %s", path.name, missing_text)
            stats["files_rejected"] += 1
            reason = "Missing required columns: " + missing_text
            for row in rows:
                rejected_rows.append({
                    "payment_ref": row.get("payment_ref", ""), "source_file": path.name,
                    "row_number": row["row_number"], "transaction_id": row.get("transaction_id", ""),
                    "reasons": reason,
                })
                stats["reason_counts"][reason] = stats["reason_counts"].get(reason, 0) + 1
            continue

        stats["files_processed"] += 1
        for row in rows:
            problems = find_problems(row, seen_ids)
            if problems:
                rejected_rows.append({
                    "payment_ref": row.get("payment_ref", ""), "source_file": path.name,
                    "row_number": row["row_number"], "transaction_id": row.get("transaction_id", ""),
                    "reasons": "; ".join(problems),
                })
                for reason in problems:
                    stats["reason_counts"][reason] = stats["reason_counts"].get(reason, 0) + 1
                continue

            transaction_id = row["transaction_id"].strip()
            seen_ids.add(transaction_id)
            cleaned = clean_row(row)
            valid_rows.append({column: cleaned.get(column, "") for column in VALID_COLUMNS})
            stats["total_revenue"] += cleaned["line_total"]

    stats["valid_transactions"] = len(valid_rows)
    stats["rejected_transactions"] = len(rejected_rows)

    write_csv(valid_rows, output_dir / "consolidated_transactions.csv", VALID_COLUMNS)
    write_csv(rejected_rows, output_dir / "rejected_transactions.csv", REJECTED_COLUMNS)
    summary_path = output_dir / "summary.txt"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = build_summary(stats)
    summary_path.write_text(summary, encoding="utf-8")
    logger.info("\n%s", summary)
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-file transaction processing pipeline")
    parser.add_argument("--input", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()

    try:
        run_pipeline(args.input, args.output)
    except (OSError, ValueError) as error:
        logger.error("Pipeline failed: %s", error)
        raise SystemExit(1)

