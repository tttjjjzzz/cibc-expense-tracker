import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".qfx", ".ofx", ".csv"}


class _TransactionFileHandler(FileSystemEventHandler):
    def __init__(self, account_id: str = ""):
        self.account_id = account_id

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        # Brief pause so the file finishes writing before we read it
        time.sleep(0.5)
        if not path.exists():
            return

        logger.info(f"New file detected: {path.name}")
        print(f"  -> Importing {path.name}...")
        try:
            from cli import run_pipeline
            inserted, skipped = run_pipeline(str(path), account_id=self.account_id)
            print(f"  -> Done: {inserted} new, {skipped} skipped.")
            logger.info(f"{path.name}: {inserted} new, {skipped} skipped")
        except Exception as e:
            print(f"  -> Error importing {path.name}: {e}")
            logger.error(f"Failed to import {path.name}: {e}")


def start_watcher(folder: str = "./imports", account_id: str = "") -> None:
    """Start watching *folder* and auto-import any QFX/CSV files dropped into it.

    Blocks until the user presses Ctrl-C.
    """
    watch_path = Path(folder).resolve()
    watch_path.mkdir(parents=True, exist_ok=True)

    # Initialise DB before any files arrive
    from storage import database
    database.init_db()

    handler = _TransactionFileHandler(account_id=account_id)
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=False)
    observer.start()

    print(f"Watching {watch_path}")
    print("Drop QFX or CSV files into that folder to import automatically.")
    print("Press Ctrl-C to stop.\n")

    try:
        while observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        print("\nWatcher stopped.")
