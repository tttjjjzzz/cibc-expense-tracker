import logging
import sys
from pathlib import Path

import click

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline(filepath: str, account_id: str = "") -> tuple:
    """Full ingestion pipeline. Returns (inserted, skipped)."""
    from ingestion.detector import detect_and_parse
    from processing.categoriser import categorise_all
    from processing.deduplicator import deduplicate
    from processing.enricher import enrich_all
    from storage import database

    database.init_db()

    transactions = detect_and_parse(filepath, account_id=account_id)
    if not transactions:
        return 0, 0

    transactions = enrich_all(transactions)
    transactions = categorise_all(transactions)
    new = deduplicate(transactions)
    skipped = len(transactions) - len(new)

    if new:
        database.insert_transactions(new)
        database.log_import(Path(filepath).name, len(new))

    return len(new), skipped


@click.group()
def cli():
    """CIBC Expense Tracker CLI."""


@cli.command("import")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--account-id", default="", help="Account ID (last 4 digits) for CSV imports")
def import_file(filepath, account_id):
    """Import a single QFX or CSV file."""
    try:
        inserted, skipped = run_pipeline(filepath, account_id=account_id)
        click.echo(f"Imported {inserted} new transaction(s), skipped {skipped} duplicate(s).")
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)


@cli.command("import-dir")
@click.argument("dirpath", type=click.Path(exists=True, file_okay=False))
@click.option("--account-id", default="", help="Account ID for CSV imports")
def import_dir(dirpath, account_id):
    """Import all QFX and CSV files from a directory."""
    from storage import database
    database.init_db()

    total_inserted = total_skipped = 0
    for path in sorted(Path(dirpath).iterdir()):
        if path.suffix.lower() in (".qfx", ".ofx", ".csv"):
            click.echo(f"Importing {path.name}...")
            try:
                inserted, skipped = run_pipeline(str(path), account_id=account_id)
                click.echo(f"  -> {inserted} new, {skipped} skipped")
                total_inserted += inserted
                total_skipped += skipped
            except Exception as e:
                logger.warning(f"  -> Failed: {e}")

    click.echo(f"\nTotal: {total_inserted} imported, {total_skipped} skipped.")


@cli.command()
@click.option("--year", default=None, type=int, help="Year (default: current)")
@click.option("--month", default=None, type=int, help="Month (default: current)")
def summary(year, month):
    """Show spending summary for a month."""
    from datetime import date
    from storage import database

    database.init_db()
    today = date.today()
    year = year or today.year
    month = month or today.month

    rows = database.get_monthly_summary(year, month)
    if not rows:
        click.echo(f"No spending data for {year}-{month:02d}.")
        return

    click.echo(f"\nSpending summary for {year}-{month:02d}:")
    click.echo(f"{'Category':<25} {'Total':>10} {'Txns':>6}")
    click.echo("-" * 45)
    total = 0.0
    for row in rows:
        click.echo(f"{row['category']:<25} {row['total']:>10.2f} {row['count']:>6}")
        total += row["total"]
    click.echo("-" * 45)
    click.echo(f"{'TOTAL':<25} {total:>10.2f}")


@cli.command()
def dashboard():
    """Launch the Streamlit dashboard."""
    import subprocess
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    subprocess.run(["streamlit", "run", str(dashboard_path)], check=True)


@cli.command()
@click.option("--folder", default="./imports", show_default=True,
              help="Folder to watch for new QFX/CSV files.")
@click.option("--account-id", default="", help="Account ID for CSV imports.")
def watch(folder, account_id):
    """Watch a folder and auto-import new QFX/CSV files dropped into it."""
    from watcher import start_watcher
    start_watcher(folder=folder, account_id=account_id)


if __name__ == "__main__":
    cli()
