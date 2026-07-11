import json
import ctypes
import os
import signal
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / ".web_dashboard.pid"


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


def request_disconnect(url):
    request = Request(
        url + "api/disconnect",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=2):
            return
    except (OSError, URLError):
        return


def remove_pid_file():
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass


def main():
    try:
        details = json.loads(PID_FILE.read_text(encoding="utf-8"))
        pid = int(details["pid"])
    except FileNotFoundError:
        print("PingPong web dashboard is not managed or already stopped.")
        return 0
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        remove_pid_file()
        raise SystemExit("Invalid dashboard PID file was removed.")

    if not process_is_running(pid):
        remove_pid_file()
        print("PingPong web dashboard was already stopped.")
        return 0

    url = details.get(
        "url",
        "http://{}:{}/".format(details.get("host", "127.0.0.1"), details.get("port", 8765)),
    )
    request_disconnect(url)
    time.sleep(0.4)

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

    deadline = time.monotonic() + 6
    while time.monotonic() < deadline and process_is_running(pid):
        time.sleep(0.2)

    if process_is_running(pid) and os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        time.sleep(0.5)

    if process_is_running(pid):
        raise SystemExit("Could not stop dashboard process {}.".format(pid))

    remove_pid_file()
    print("PingPong web dashboard stopped (PID {}).".format(pid))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
