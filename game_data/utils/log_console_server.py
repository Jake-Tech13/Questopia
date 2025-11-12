# path: game_data/utils/log_console_server.py
from __future__ import annotations

import argparse
import logging
import pickle
import socketserver
import struct
import sys
from typing import Optional

MESSAGE_LEVEL = 25
if logging.getLevelName(MESSAGE_LEVEL) != "MESSAGE":
    logging.addLevelName(MESSAGE_LEVEL, "MESSAGE")

# --- Colors (console only)
ANSI_RESET = "\033[0m"
LEVEL_COLOR = {
    logging.DEBUG: "\033[90m",     # grey
    MESSAGE_LEVEL: "\033[38;2;0;170m",     # dark-green
    logging.INFO: "\033[37m",      # white
    logging.WARNING: "\033[38;2;255;255m",   # yellow
    logging.ERROR: "\033[38;2;255m",  # red
    logging.FATAL: "\033[38;2;128m",  # dark-red
}

def _level_label(levelno: int) -> str:
    mapping = {
        logging.DEBUG: "Debug",
        logging.INFO: "Info",
        MESSAGE_LEVEL: "Message",
        logging.WARNING: "Warning",
        logging.ERROR: "Error",
        logging.FATAL: "Fatal",
    }
    return mapping.get(levelno, logging.getLevelName(levelno).title())

class AlignedFormatter(logging.Formatter):
    def __init__(
        self, *, 
        show_source: bool,
        pad_width: int,
        default_context: str,
        use_color: bool = True
    ) -> None:
        super().__init__(datefmt="%H:%M:%S")
        self.show_source = show_source
        self.pad_width = pad_width
        self.default_context = default_context
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        t = self.formatTime(record, self.datefmt)
        lvl = _level_label(record.levelno).ljust(self.pad_width)
        ctx = getattr(record, "ctx", None) or self.default_context
        parts = [f"[{t} | {lvl}: {ctx}"]
        if self.show_source:
            parts.append(f"{record.module}:{record.lineno}")
        head = " | ".join(parts)
        msg = record.getMessage()
        line = f"{head}] {msg}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        if record.stack_info:
            line = f"{line}\n{self.formatStack(record.stack_info)}"
        if self.use_color:
            color = LEVEL_COLOR.get(record.levelno)
            if color:
                line = f"{color}{line}{ANSI_RESET}"
        return line


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            data = b""
            while len(data) < slen:
                more = self.connection.recv(slen - len(data))
                if not more:
                    break
                data += more
            if not data:
                break
            obj = pickle.loads(data)
            record = logging.makeLogRecord(obj)
            logging.getLogger(record.name).handle(record)

class LogRecordSocketServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def _set_title(title: str) -> None:
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception:
            try:
                import os
                os.system(f"title {title}")
            except Exception:
                pass

def _run_server(
        host: str, 
        port: int, 
        level: int, 
        title: str, 
        show_source: bool, 
        pad_width: int, 
        default_context: str
    ) -> None:
    _set_title(title)
    root = logging.getLogger()
    root.setLevel(level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(
        AlignedFormatter(
            show_source=show_source, 
            pad_width=pad_width, 
            default_context=default_context, 
            use_color=True
        )
    )
    root.addHandler(ch)
    server = LogRecordSocketServer((host, port), LogRecordStreamHandler)
    root.info("Logger console ready on %s:%d", host, port)
    server.serve_forever()

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--level", type=int, default=logging.INFO)
    ap.add_argument("--title", default="Logger")
    ap.add_argument("--show-source", default="1")
    ap.add_argument("--pad-width", type=int, default=7)
    ap.add_argument("--default-context", default="Game Log")
    args = ap.parse_args(argv)
    try:
        show_source = str(args.show_source).strip() not in {"0", "false", "False"}
        _run_server(args.host, args.port, args.level, args.title, show_source, args.pad_width, args.default_context)
    except Exception as e:
        print(f"[console-server] crash: {e}", file=sys.stderr)
        try:
            input("Press Enter to close this console...")
        except Exception:
            pass
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
