import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / ".web_dashboard.pid"
LOG_FILE = ROOT / "web_dashboard.log"
SERVER_FILE = ROOT / "web_dashboard.py"


def parse_args():
    parser = argparse.ArgumentParser(description="Start the PingPong web dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--wait", type=float, default=10.0)
    return parser.parse_args()


def process_is_running(pid):
    if os.name == "nt":
        try:
            process_id = int(pid)
        except (TypeError, ValueError):
            return False
        access = 0x00100000 | 0x1000  # SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION
        handle = ctypes.windll.kernel32.OpenProcess(access, False, process_id)
        if not handle:
            return False
        try:
            return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == 0x102
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (OSError, TypeError, ValueError):
        return False


def status_is_ready(url, timeout=0.5):
    try:
        with urlopen(url + "api/status", timeout=timeout) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


def read_pid_file():
    try:
        return json.loads(PID_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def main():
    args = parse_args()
    if not 1 <= args.port <= 65535:
        raise SystemExit("Port must be between 1 and 65535.")
    if args.wait <= 0:
        raise SystemExit("Wait time must be positive.")

    url = "http://{}:{}/".format(args.host, args.port)
    existing = read_pid_file()
    if existing:
        pid = existing.get("pid")
        existing_url = existing.get("url", url)
        if process_is_running(pid) and status_is_ready(existing_url):
            print("PingPong web dashboard is already running.")
            print(existing_url)
            return 0
        try:
            PID_FILE.unlink()
        except FileNotFoundError:
            pass

    if status_is_ready(url):
        raise SystemExit(
            "Port {} already has a dashboard server not managed by server_start.py.".format(
                args.port
            )
        )

    command = [
        sys.executable,
        "-B",
        str(SERVER_FILE),
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    environment = os.environ.copy()
    environment["PYTHONUNBUFFERED"] = "1"
    popen_options = {
        "cwd": str(ROOT),
        "env": environment,
        "stdin": subprocess.DEVNULL,
    }
    if os.name == "nt":
        popen_options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    else:
        popen_options["start_new_session"] = True

    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write("\n[{}] Starting {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), url))
        log.flush()
        process = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            **popen_options
        )

    PID_FILE.write_text(
        json.dumps(
            {
                "pid": process.pid,
                "host": args.host,
                "port": args.port,
                "url": url,
                "started_at": time.time(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    deadline = time.monotonic() + args.wait
    while time.monotonic() < deadline:
        if process.poll() is not None:
            try:
                PID_FILE.unlink()
            except FileNotFoundError:
                pass
            raise SystemExit(
                "Dashboard server exited with code {}. See {}.".format(
                    process.returncode, LOG_FILE
                )
            )
        if status_is_ready(url):
            print("PingPong web dashboard started (PID {}).".format(process.pid))
            print(url)
            return 0
        time.sleep(0.2)

    process.terminate()
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass
    raise SystemExit("Dashboard did not become ready. See {}.".format(LOG_FILE))


if __name__ == "__main__":
    raise SystemExit(main())
