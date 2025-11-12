# path: game_data/utils/logger.py
from __future__ import annotations

import atexit
import importlib
import logging
import logging.config
import os
import platform
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, IO, Literal, Optional, Tuple

MESSAGE_LEVEL = 25
if logging.getLevelName(MESSAGE_LEVEL) != "MESSAGE":
    logging.addLevelName(MESSAGE_LEVEL, "MESSAGE")

RotationKind = Literal["size", "time"]

_WRAPPERS: Dict[Tuple[str, str], "Logger"] = {}
_CONSOLE: Optional["_ConsoleProc"] = None
_AUTO_CLOSE: bool = True
_DEFAULT_CONTEXT = "Game Log"
_SHOW_SOURCE = True
_PAD_WIDTH = 7
_SESSION_START: Optional[datetime] = None
_NEXT_DAY_MARK: Optional[datetime] = None

@dataclass
class _ConsoleProc:
    popen: subprocess.Popen
    host: str
    port: int


# ---------- utils
def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent  # .../game_data

def _coerce_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    level = level.upper()
    return MESSAGE_LEVEL if level == "MESSAGE" else getattr(logging, level)

def _find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]

def _python_exe() -> str:
    exe = Path(sys.executable)
    if platform.system() == "Windows":
        pe = exe.with_name("python.exe")
        if pe.exists():
            return str(pe)
    return str(exe)

def _level_label(levelno: int) -> str:
    mapping = {
        logging.DEBUG: "Debug",
        logging.INFO: "Info",
        MESSAGE_LEVEL: "Message",
        logging.WARNING: "Warning",
        logging.ERROR: "Error",
        logging.CRITICAL: "Fatal",
    }
    return mapping.get(levelno, logging.getLevelName(levelno).title())


# ---------- formatters
class AlignedFormatter(logging.Formatter):
    """
    Rend: '[HH:MM:SS | LevelPad: Context | module:lineno] message'
    - LevelPad est aligné à pad_width.
    - Context (= record.ctx ou default_context).
    - Source optionnelle (module:lineno).
    """
    def __init__(self, *, show_source: bool, pad_width: int, default_context: str) -> None:
        super().__init__(datefmt="%H:%M:%S")
        self.show_source = show_source
        self.pad_width = pad_width
        self.default_context = default_context

    def format(self, record: logging.LogRecord) -> str:
        # header
        t = self.formatTime(record, self.datefmt)
        lvl = _level_label(record.levelno).ljust(self.pad_width)
        ctx = getattr(record, "ctx", None) or self.default_context
        parts = [f"[{t} | {lvl}: {ctx}"]
        if self.show_source:
            parts.append(f"{record.module}:{record.lineno}")
        head = " | ".join(parts)

        # message
        msg = record.getMessage()  # toujours dispo, remplace formatMessage()
        line = f"{head}] {msg}"

        # exceptions / stack
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        if record.stack_info:
            line = f"{line}\n{self.formatStack(record.stack_info)}"
        return line


# ---------- file session helpers
def _file_handlers() -> list[logging.FileHandler]:
    hs: list[logging.FileHandler] = []
    for h in logging.getLogger().handlers:
        if isinstance(h, logging.FileHandler):
            hs.append(h)
    return hs

def _emit_file_line(line: str) -> None:
    for h in _file_handlers():
        stream: Optional[IO[str]] = getattr(h, "stream", None)
        if stream is None:
            continue
        try:
            h.acquire()
            stream.write(line)
            if not line.endswith("\n"):
                stream.write("\n")
            stream.flush()
        finally:
            h.release()

def _emit_session_header(now: datetime) -> None:
    stamp = now.strftime("%d-%m-%Y | %H:%M:%S")
    _emit_file_line(f"---[ {stamp} ]---")

def _emit_session_separator_and_header(now: datetime) -> None:
    _emit_file_line("|")
    _emit_session_header(now)

def _emit_session_footer(start: datetime, end: datetime) -> None:
    secs = int((end - start).total_seconds())
    hours = secs // 3600
    mins = (secs % 3600) // 60
    secs = secs % 60
    _emit_file_line(f"Logging Time - {hours:02d}:{mins:02d}:{secs:02d}\r")

def _maybe_emit_daily_header(now: datetime) -> None:
    global _NEXT_DAY_MARK
    if _NEXT_DAY_MARK and now >= _NEXT_DAY_MARK:
        _emit_session_separator_and_header(now)
        _NEXT_DAY_MARK = _NEXT_DAY_MARK + timedelta(days=1)


# ---------- public API
def init_logging(
    log_path: str | Path,
    *,
    level: str | int = "INFO",
    rotation: RotationKind = "size",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
    when: str = "midnight",
    interval: int = 1,
    show_console: bool = False,
    console_title: str = "Logger",
    context_label: str = "Game Log",
    auto_close: bool = True,
    show_source: bool = True,
    pad_width: int = 7,
) -> None:
    """
    Fichier (rotation) + console séparée optionnelle, console principale muette.
    Format aligné, contexte libre, source optionnelle.
    Fichier: en-tête de session + footer "Logging Time".
    """
    global _DEFAULT_CONTEXT, _SHOW_SOURCE, _PAD_WIDTH, _SESSION_START, _NEXT_DAY_MARK, _AUTO_CLOSE
    _DEFAULT_CONTEXT = context_label
    _SHOW_SOURCE = show_source
    _PAD_WIDTH = pad_width
    _AUTO_CLOSE = auto_close

    lvl = _coerce_level(level)
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler: Dict[str, object] = {"level": lvl, "formatter": "file_fmt"}
    if rotation == "size":
        file_handler.update(
            {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_path),
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8",
            }
        )
    elif rotation == "time":
        file_handler.update(
            {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": str(log_path),
                "when": when,
                "interval": interval,
                "backupCount": backup_count,
                "encoding": "utf-8",
                "utc": False,
            }
        )
    else:
        raise ValueError(f"Unknown rotation: {rotation}")

    handlers_cfg: Dict[str, Dict[str, object]] = {"file": file_handler}

    if show_console:
        host, port = "127.0.0.1", _find_free_port()
        ok = _start_console_server(
            host=host,
            port=port,
            level=lvl,
            title=console_title,
            show_source=show_source,
            pad_width=pad_width,
            default_context=context_label,
        )
        if ok:
            handlers_cfg["console_socket"] = {
                "class": "logging.handlers.SocketHandler",
                "level": lvl,
                "host": host,
                "port": port,
            }

    cfg = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "file_fmt": {
                "()": f"{__name__}.AlignedFormatter",
                "show_source": show_source,
                "pad_width": pad_width,
                "default_context": context_label,
            },
        },
        "handlers": handlers_cfg,
        "root": {"level": lvl, "handlers": list(handlers_cfg.keys())},
    }
    logging.config.dictConfig(cfg)

    # méthode .message
    def _log_message(self: logging.Logger, msg, *args, **kwargs):
        if self.isEnabledFor(MESSAGE_LEVEL):
            self._log(MESSAGE_LEVEL, msg, args, **kwargs)
    if not hasattr(logging.Logger, "message"):
        logging.Logger.message = _log_message  # type: ignore[attr-defined]

    # début de session
    now = datetime.now()
    _SESSION_START = now
    _NEXT_DAY_MARK = now + timedelta(days=1)
    _emit_session_header(now)
    atexit.register(_write_session_footer)


def _write_session_footer() -> None:
    if _SESSION_START:
        _emit_session_footer(_SESSION_START, datetime.now())


def _resolve_server_module() -> Tuple[str, Optional[Path]]:
    server_module = "utils.log_console_server"
    try:
        importlib.import_module(server_module)
        return server_module, None
    except Exception:
        fallback = Path(__file__).with_name("log_console_server.py")
        return server_module, fallback if fallback.exists() else (server_module, None)  # type: ignore[return-value]


def _start_console_server(
    *,
    host: str,
    port: int,
    level: int,
    title: str,
    show_source: bool,
    pad_width: int,
    default_context: str,
    ) -> bool:
    """_summary_

    Args:
        host (str): _description_
        port (int): _description_
        level (int): _description_
        title (str): _description_
        show_source (bool): _description_
        pad_width (int): _description_
        default_context (str): _description_

    Returns:
        bool: _description_
    """
    global _CONSOLE
    mod, fallback = _resolve_server_module()
    root = _project_root()
    env = {**os.environ, "PYTHONPATH": str(root)}
    py = _python_exe()

    argv = [py, "-u"]
    if fallback is None:
        argv += ["-m", mod]
    else:
        argv += [str(fallback)]
    argv += [
        "--host",
        host,
        "--port",
        str(port),
        "--level",
        str(level),
        "--title",
        title,
        "--pad-width",
        str(pad_width),
        "--show-source",
        "1" if show_source else "0",
        "--default-context",
        default_context,
    ]

    creationflags = 0
    if platform.system() == "Windows":
        creationflags = 0x00000010  # CREATE_NEW_CONSOLE

    try:
        pop = subprocess.Popen(
            argv,
            cwd=str(root),
            env=env,
            creationflags=creationflags,
            stdin=None,
            stdout=None,
            stderr=None,
            close_fds=(platform.system() != "Windows"),
        )
    except Exception:
        logging.getLogger(__name__).exception("Logger console failed to start")
        return False

    _CONSOLE = _ConsoleProc(pop, host, port)

    deadline = time.time() + 8.0
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.1)
    logging.getLogger(__name__).error("Logger console cannot be joined on %s:%d (timeout).", host, port)
    return False


def shutdown_logging() -> None:
    """Close the console and stop logging events into the log file."""
    global _CONSOLE
    try:
        logging.shutdown()
    finally:
        if _CONSOLE and _CONSOLE.popen.poll() is None and _AUTO_CLOSE:
            try:
                _CONSOLE.popen.terminate()
                _CONSOLE.popen.wait(timeout=1.5)
            except Exception:
                get_logger(__name__).log_exception("ERROR: Logger console could not be terminated properly, initiating secondary closure procedure...")
            if _CONSOLE.popen.poll() is None:
                try:
                    _CONSOLE.popen.kill()
                except Exception:
                    get_logger(__name__).log_fatal("FATAL_ERROR: Logger console could not be terminated. Please close the window manually.")
        _CONSOLE = None


# ---------- wrapper
class Logger:
    """
    **BepInEx-like logger API**
    
    """
    __slots__ = ("_logger", "_context")

    def __init__(
        self,
        name: str,
        context: Optional[str]
        ) -> None:
        self._logger = logging.getLogger(name)
        self._context = context or _DEFAULT_CONTEXT

    def _emit(self, level: int, msg: str, *args, **kwargs) -> None:
        """
        Output a custom message with a chosen `level` into the console.\n
        Output is logged into the log file specified at `init_logging(log_path: str | Path, ...)`.\n
        
        Args:
            level (int): Can be equal to the following constants (or their direct value) from the `logging module`: `DEBUG` (`20`), `INFO` (`30`), `ERROR` (`40`), `CRITICAL` (`50`). You can also parse in `logger.MESSAGE_LEVEL` which is equal to `25`.
            msg (str): The string you want to output.
        """
        _maybe_emit_daily_header(datetime.now())
        extra = kwargs.pop("extra", {})
        if "ctx" not in extra:
            extra["ctx"] = self._context
        self._logger.log(level, msg, *args, extra=extra, **kwargs)

    def log_debug(self, msg: str, *args, **kwargs) -> None:
        """Log custom messages in DEBUG mode. Text will appear in *Grey* in the console."""
        self._emit(logging.DEBUG, msg, *args, **kwargs)
    def log_message(self, msg: str, *args, **kwargs) -> None:
        """Log custom messages in MESSAGE mode. Text will appear in *Green* in the console."""
        self._emit(MESSAGE_LEVEL, msg, *args, **kwargs)
    def log_info(self, msg: str, *args, **kwargs) -> None:
        """Log custom messages in INFO mode. Text will appear in *White* in the console."""
        self._emit(logging.INFO, msg, *args, **kwargs)
    def log_warning(self, msg: str, *args, **kwargs) -> None:
        """Log custom messages in WARNING mode. Text will appear in *Yellow* in the console."""
        self._emit(logging.WARNING, msg, *args, **kwargs)
    def log_error(self, msg: str, *args, **kwargs) -> None:
        """Log custom messages in ERROR mode. Text will appear in *Red* in the console."""
        self._emit(logging.ERROR, msg, *args, **kwargs)
    def log_fatal(self, msg: str, *args, **kwargs) -> None:
        """Log custom messages in FATAL mode. Text will appear in *Dark Red* in the console."""
        self._emit(logging.CRITICAL, msg, *args, **kwargs)
    def log_exception(self, msg: str, *args, **kwargs) -> None:
        """Log custom exception messages. Text will appear in *Red* in the console."""
        kwargs["exc_info"] = True
        self._emit(logging.ERROR, msg, *args, **kwargs)

def get_logger(name: str, *, context: Optional[str] = None) -> Logger:
    key = (name, context or _DEFAULT_CONTEXT)
    if key not in _WRAPPERS:
        _WRAPPERS[key] = Logger(name, context)
    return _WRAPPERS[key]
