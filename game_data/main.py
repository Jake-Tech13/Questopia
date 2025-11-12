# path: game_data/main.py
from __future__ import annotations

from time import sleep

from utils.logger import init_logging, get_logger, shutdown_logging
import core.weapons as wp

def main(show_console: bool = True) -> int:
    # initialize logging console
    init_logging(
        "logs/log.txt",
        level="DEBUG",
        rotation="size",
        max_bytes=5 * 1024 * 1024, #5MB
        backup_count=5,
        show_console=show_console,
        auto_close=True,
        console_title="Game Logger"
    )
    # get access to the logger
    log = get_logger(__name__)
    log.log_info("Starting game...")
    
    
    
    # close console + logging at game exit
    shutdown_logging()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(show_console=True))