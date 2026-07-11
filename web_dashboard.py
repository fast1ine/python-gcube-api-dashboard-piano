import argparse
import json
import mimetypes
import os
import signal
import threading
import time
import traceback
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
STATIC_ROOT = ROOT / "web_static"


class DashboardService:
    def __init__(self):
        self._lock = threading.RLock()
        self._stop_requested = threading.Event()
        self._worker = None
        self._client = None
        self._log_sequence = 0
        self._logs = deque(maxlen=160)
        self._state = {
            "state": "Idle",
            "bluetooth": "-",
            "transport": "-",
            "device": "-",
            "group_id": "00",
            "connection": {"connected": 0, "total": 0},
            "mac": "-",
            "last_update": None,
            "cubes": [],
            "error": None,
        }
        self._log("Web dashboard ready.")

    def snapshot(self):
        with self._lock:
            data = dict(self._state)
            data["connection"] = dict(self._state["connection"])
            data["cubes"] = [dict(cube) for cube in self._state["cubes"]]
            data["logs"] = list(self._logs)
            data["running"] = bool(self._worker and self._worker.is_alive())
            return data

    def scan_devices(self, group_id="00", timeout=5):
        group_value = self.parse_group_id(group_id)
        group_label = "{:02X}".format(group_value)
        timeout = max(1, min(float(timeout), 10))
        devices = []
        errors = []

        try:
            import serial.tools.list_ports
            from connection.connectionutils import ConnectionUtils

            for port in serial.tools.list_ports.comports():
                if ConnectionUtils.DONGLE_PNP_ID in str(port.hwid).upper():
                    devices.append(
                        {
                            "type": "serial",
                            "identifier": str(port.device),
                            "name": str(port.description or "PingPong USB Dongle"),
                            "details": str(port.hwid),
                        }
                    )
        except Exception as exc:
            errors.append("USB scan: {}".format(exc))

        try:
            from connection.bletransport import BleSerialTransport

            for device in BleSerialTransport.scan(timeout=timeout, group_label=group_label):
                devices.append(
                    {
                        "type": "ble",
                        "identifier": device["address"],
                        "name": device["name"],
                        "details": "Bluetooth LE / Nordic UART",
                    }
                )
        except Exception as exc:
            errors.append("BLE scan: {}".format(exc))

        self._log(
            "{} connection device(s) found for group {}.".format(len(devices), group_label)
        )
        return {"devices": devices, "errors": errors, "group_id": group_label}

    def connect(self, payload):
        with self._lock:
            if self._worker and self._worker.is_alive():
                raise RuntimeError("A robot connection is already active.")

        robot_count = int(payload.get("robots", 1))
        if not 1 <= robot_count <= 8:
            raise ValueError("Robot count must be between 1 and 8.")
        period = float(payload.get("period", 0.1))
        if not 0.01 <= period <= 1:
            raise ValueError("Sensor period must be between 0.01 and 1.0 seconds.")
        connect_timeout = float(payload.get("timeout", 30))
        if connect_timeout < 0:
            raise ValueError("Connection timeout must be zero or positive.")
        group_id = self.parse_group_id(payload.get("group_id", "00"))
        device_type = str(payload.get("device_type", "auto")).lower()
        if device_type not in ("auto", "ble", "serial"):
            raise ValueError("Unsupported connection type.")

        config = {
            "robots": robot_count,
            "period": period,
            "timeout": connect_timeout,
            "group_id": group_id,
            "device_type": device_type,
            "identifier": str(payload.get("identifier") or ""),
            "name": str(payload.get("name") or ""),
            "auto_sensor": bool(payload.get("auto_sensor", True)),
        }
        self._stop_requested.clear()
        group_label = "{:02X}".format(group_id)
        with self._lock:
            self._state.update(
                {
                    "state": "Connecting",
                    "bluetooth": "Scanning",
                    "transport": "-",
                    "device": "-",
                    "group_id": group_label,
                    "connection": {"connected": 0, "total": robot_count},
                    "mac": "-",
                    "last_update": None,
                    "cubes": [],
                    "error": None,
                }
            )
        self._log("Connecting to PingPong group {}.".format(group_label))
        self._worker = threading.Thread(
            target=self._connection_worker,
            args=(config,),
            daemon=True,
        )
        self._worker.start()

    def stop(self):
        with self._lock:
            if not self._worker or not self._worker.is_alive():
                self._state["state"] = "Stopped"
                return
            self._state["state"] = "Stopping"
        self._stop_requested.set()
        self._log("Stopping robot connection.")

    def play_music(self, payload):
        notes = payload.get("notes")
        if not isinstance(notes, list) or not 1 <= len(notes) <= 80:
            raise ValueError("Notes must be a list containing 1 to 80 values.")
        try:
            notes = [int(note) for note in notes]
        except (TypeError, ValueError):
            raise ValueError("Every note must be an integer.")
        if any(note < 0 or note > 127 for note in notes):
            raise ValueError("Note values must be between 0 and 127.")

        cube = int(payload.get("cube", 1))
        with self._lock:
            client = self._client
            connected = self._state["state"] == "Connected"
            total = self._state["connection"]["total"]
        if not connected or client is None:
            raise RuntimeError("Connect a PingPong robot before playing the piano.")
        if not 1 <= cube <= total:
            raise ValueError("Cube must be between 1 and {}.".format(total))

        durations = self._music_values(payload.get("durations", 250), len(notes), 10, 2550)
        rests = self._music_values(payload.get("rests", 0), len(notes), 0, 2550)
        duration_units = [max(1, min(255, int(round(value / 10.0)))) for value in durations]
        rest_units = [max(0, min(255, int(round(value / 10.0)))) for value in rests]
        packet = client._GenerateProtocolInstance.SetMusicNotesInAction_SetMusicNotes_bytes(
            cube,
            notes,
            duration_units,
            rest_units,
        )
        client.write(packet)
        return {"ok": True, "cube": cube, "notes": notes}

    def stop_music(self, payload):
        cube = int(payload.get("cube", 1))
        with self._lock:
            client = self._client
            connected = self._state["state"] == "Connected"
            total = self._state["connection"]["total"]
        if not connected or client is None:
            return {"ok": True}
        if not 1 <= cube <= total:
            raise ValueError("Cube must be between 1 and {}.".format(total))
        packet = client._GenerateProtocolInstance.SetMusicNotesInAction_PlayMusicNotes_bytes(
            cube,
            False,
        )
        client.write(packet)
        return {"ok": True}

    def close(self):
        self.stop()
        worker = self._worker
        if worker and worker.is_alive():
            worker.join(timeout=12)

    def _connection_worker(self, config):
        client = None
        transport = None
        try:
            from connection.bletransport import BleSerialTransport
            from pingpongthread import PingPongThread

            transport_kind = config["device_type"]
            if transport_kind in ("auto", "ble"):
                try:
                    address = config["identifier"] if transport_kind == "ble" else ""
                    name = config["name"]
                    group_label = "{:02X}".format(config["group_id"])
                    if not address:
                        self._set_state(bluetooth="BLE scanning")
                        scan_timeout = (
                            5
                            if config["timeout"] == 0
                            else min(max(config["timeout"], 1), 10)
                        )
                        devices = BleSerialTransport.scan(
                            timeout=scan_timeout,
                            group_label=group_label,
                        )
                        if not devices:
                            raise RuntimeError(
                                "No matching PingPong BLE device is advertising."
                            )
                        address = devices[0]["address"]
                        name = devices[0]["name"]
                    self._log("Opening Bluetooth LE device {}.".format(name or address))
                    transport = BleSerialTransport(
                        address,
                        name=name,
                        connect_timeout=config["timeout"] or 15,
                    )
                    transport_kind = "ble"
                    self._set_state(
                        bluetooth="BLE ready",
                        transport="Bluetooth LE",
                        device="{} ({})".format(name or "PingPong", address),
                    )
                except Exception as exc:
                    if config["device_type"] == "ble":
                        raise
                    self._log("Bluetooth LE unavailable: {}".format(exc), "warning")
                    self._log("Falling back to the PingPong USB dongle.")
                    transport = None
                    transport_kind = "serial"

            if transport is None:
                port = config["identifier"] if config["device_type"] == "serial" else ""
                transport, port = self._open_usb_dongle(
                    port,
                    config["timeout"],
                )
                transport_kind = "serial"
                self._set_state(
                    bluetooth="USB ready",
                    transport="USB dongle",
                    device=port,
                )

            client = PingPongThread(
                number=config["robots"],
                group_id=config["group_id"],
                transport=transport,
                transport_kind=transport_kind,
            )
            self._client = client
            self._log("Starting {} reader.".format(transport_kind.upper()))
            client.start()
            self._wait_for_connection(client, config["timeout"])
            self._set_state(state="Connected", error=None)
            self._log("Robots are fully connected.")

            if config["auto_sensor"] and transport_kind == "ble":
                time.sleep(1)

            while not self._stop_requested.is_set():
                if config["auto_sensor"] and client.play_once_full_connect():
                    client.receive_sensor_data(
                        "all",
                        method="periodic",
                        period=config["period"],
                    )
                    self._log("Periodic sensor stream enabled.")
                self._update_robot_status(client.get_robot_status())
                time.sleep(0.15)
        except Exception as exc:
            self._set_state(
                state="Error",
                bluetooth="Error",
                error=str(exc),
            )
            self._log(self._last_traceback_line(), "error")
        finally:
            if client is not None:
                try:
                    client.end()
                except Exception:
                    self._log("Connection cleanup completed with an error.", "warning")
            if transport is not None and getattr(transport, "is_open", False):
                try:
                    transport.close()
                except Exception:
                    pass
            self._client = None
            self._reset_pingpong_flags()
            with self._lock:
                if self._state["state"] not in ("Error",):
                    self._state["state"] = "Stopped"
                if "scanning" in self._state["bluetooth"].lower():
                    self._state["bluetooth"] = "Stopped"
            self._log("Connection stopped.")

    def _open_usb_dongle(self, preferred_port, timeout):
        import serial
        import serial.tools.list_ports
        from connection.connectionutils import ConnectionUtils
        from protocols.generateprotocol import GenerateProtocol

        started_at = time.monotonic()
        check_packet = GenerateProtocol(1).DongleInAction_bytes()
        while not self._stop_requested.is_set():
            if timeout and time.monotonic() - started_at > timeout:
                raise RuntimeError("PingPong USB dongle scan timed out.")
            ports = [
                port
                for port in serial.tools.list_ports.comports()
                if ConnectionUtils.DONGLE_PNP_ID in str(port.hwid).upper()
            ]
            if preferred_port:
                ports = [
                    port for port in ports if str(port.device) == preferred_port
                ]
            self._set_state(bluetooth="USB scanning")
            for port in ports:
                probe = None
                try:
                    probe = serial.serial_for_url(
                        str(port.device),
                        baudrate=115200,
                        timeout=1,
                        write_timeout=1,
                        rtscts=True,
                    )
                    probe.write(check_packet)
                    response = probe.read(11)
                    if (
                        len(response) >= 11
                        and response[6] == 0xDA
                        and response[10] == 0x0D
                    ):
                        probe.close()
                        transport = ConnectionUtils().connect_serial_URL(
                            str(port.device)
                        )
                        if transport is None:
                            raise RuntimeError("Could not open the PingPong USB dongle.")
                        return transport, str(port.device)
                except Exception:
                    pass
                finally:
                    try:
                        if probe is not None and probe.is_open:
                            probe.close()
                    except Exception:
                        pass
            time.sleep(0.5)
        raise RuntimeError("USB dongle scan stopped.")

    def _wait_for_connection(self, client, timeout):
        started_at = time.monotonic()
        while not self._stop_requested.is_set():
            if timeout and time.monotonic() - started_at > timeout:
                raise RuntimeError("Robot connection timed out.")
            status = client.get_robot_status()
            self._update_robot_status(status)
            controller = status.get("controller_status", {})
            processed = status.get("processed_status", {})
            total = controller.get("connection_number", 0) or 0
            connected = processed.get("connected_number", 0) or 0
            if total > 0 and connected == total:
                time.sleep(1)
                return
            time.sleep(0.15)
        raise RuntimeError("Robot connection stopped.")

    def _update_robot_status(self, status):
        controller = status.get("controller_status", {})
        processed = status.get("processed_status", {})
        total = controller.get("connection_number", 0) or 0
        connected = processed.get("connected_number", 0) or 0
        cubes = []
        for index in range(total):
            cubes.append(
                {
                    "cube": index + 1,
                    "sensor_mode": self._at(
                        controller.get("get_sensor_mode"), index
                    ),
                    "button": self._at(processed.get("button"), index),
                    "gyro": self._triplet(
                        self._at(processed.get("sensor_gyro_xyz"), index)
                    ),
                    "acc": self._triplet(
                        self._at(processed.get("sensor_acc_xyz"), index)
                    ),
                    "prox": self._at(processed.get("sensor_prox"), index),
                    "previous_prox": self._at(
                        processed.get("sensor_prox_old"), index
                    ),
                    "ain": self._at(processed.get("AIN"), index),
                    "stepper_mode": self._at(
                        controller.get("stepper_mode"), index
                    ),
                    "stepper_speed": self._at(
                        controller.get("stepper_speed"), index
                    ),
                    "stepper_step": self._at(
                        controller.get("stepper_step"), index
                    ),
                    "stepper_paused": self._at(
                        controller.get("stepper_pause"), index
                    ),
                    "servo_mode": self._at(
                        controller.get("servo_mode"), index
                    ),
                    "servo_angle": self._at(
                        controller.get("servo_angle"), index
                    ),
                }
            )
        mac = self._triplet(processed.get("MAC_address", []))
        with self._lock:
            self._state["connection"] = {
                "connected": connected,
                "total": total,
            }
            self._state["mac"] = mac
            self._state["last_update"] = time.strftime("%H:%M:%S")
            self._state["cubes"] = cubes

    def _set_state(self, **values):
        with self._lock:
            self._state.update(values)

    @staticmethod
    def _music_values(value, count, minimum, maximum):
        values = value if isinstance(value, list) else [value] * count
        if len(values) != count:
            raise ValueError("Music value lists must match the note count.")
        try:
            values = [int(item) for item in values]
        except (TypeError, ValueError):
            raise ValueError("Music timing values must be integers.")
        if any(item < minimum or item > maximum for item in values):
            raise ValueError(
                "Music timing values must be between {} and {} ms.".format(
                    minimum, maximum
                )
            )
        return values

    def _log(self, message, level="info"):
        with self._lock:
            self._log_sequence += 1
            self._logs.append(
                {
                    "id": self._log_sequence,
                    "time": time.strftime("%H:%M:%S"),
                    "level": level,
                    "message": str(message),
                }
            )

    @staticmethod
    def parse_group_id(value):
        text = str(value).strip().upper()
        if text.startswith("0X"):
            text = text[2:]
        if not 1 <= len(text) <= 2 or any(
            char not in "01234567" for char in text
        ):
            raise ValueError(
                "Group ID must be hexadecimal 00-77 using digits 0 to 7."
            )
        return int(text, 16)

    @staticmethod
    def _at(values, index):
        if isinstance(values, (list, tuple)) and index < len(values):
            return DashboardService._json_value(values[index])
        return None

    @staticmethod
    def _triplet(value):
        if isinstance(value, (list, tuple)):
            return ", ".join(
                "-" if item is None else str(item) for item in value
            )
        return "-" if value is None else str(value)

    @staticmethod
    def _json_value(value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple)):
            return [DashboardService._json_value(item) for item in value]
        return str(value)

    @staticmethod
    def _last_traceback_line():
        lines = [
            line.strip()
            for line in traceback.format_exc().splitlines()
            if line.strip()
        ]
        return lines[-1] if lines else "Unknown connection error."

    @staticmethod
    def _reset_pingpong_flags():
        try:
            from pingpongthread import PingPongThread

            PingPongThread._is_start = False
            PingPongThread._is_instance = False
        except Exception:
            pass


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "PingPongDashboard/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            return self._json(HTTPStatus.OK, self.server.service.snapshot())
        if parsed.path == "/api/devices":
            query = parse_qs(parsed.query)
            group_id = query.get("group_id", ["00"])[0]
            timeout = query.get("timeout", ["5"])[0]
            try:
                result = self.server.service.scan_devices(group_id, timeout)
                return self._json(HTTPStatus.OK, result)
            except (ValueError, RuntimeError) as exc:
                return self._json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(exc)},
                )
        return self._static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
            if parsed.path == "/api/connect":
                self.server.service.connect(payload)
                return self._json(
                    HTTPStatus.ACCEPTED,
                    {"ok": True},
                )
            if parsed.path == "/api/disconnect":
                self.server.service.stop()
                return self._json(HTTPStatus.ACCEPTED, {"ok": True})
            if parsed.path == "/api/piano/play":
                result = self.server.service.play_music(payload)
                return self._json(HTTPStatus.OK, result)
            if parsed.path == "/api/piano/stop":
                result = self.server.service.stop_music(payload)
                return self._json(HTTPStatus.OK, result)
            return self._json(
                HTTPStatus.NOT_FOUND,
                {"error": "Not found."},
            )
        except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
            return self._json(
                HTTPStatus.BAD_REQUEST,
                {"error": str(exc)},
            )

    def _static(self, path):
        files = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/piano": ("piano.html", "text/html; charset=utf-8"),
            "/piano/": ("piano.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/piano.js": ("piano.js", "text/javascript; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
            "/pingpong-mark.svg": ("pingpong-mark.svg", "image/svg+xml"),
        }
        item = files.get(path)
        if item is None:
            return self.send_error(HTTPStatus.NOT_FOUND)
        filename, content_type = item
        target = STATIC_ROOT / filename
        try:
            data = target.read_bytes()
        except FileNotFoundError:
            return self.send_error(HTTPStatus.NOT_FOUND)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 64 * 1024:
            raise ValueError("Request is too large.")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, _format, *_args):
        return


class DashboardHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, service):
        super().__init__(address, DashboardHandler)
        self.service = service


def parse_args():
    parser = argparse.ArgumentParser(
        description="PingPong robot web status dashboard"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main():
    args = parse_args()
    service = DashboardService()
    server = DashboardHTTPServer((args.host, args.port), service)
    url = "http://{}:{}/".format(args.host, args.port)
    print("PingPong web dashboard: {}".format(url))

    def shutdown(_signum, _frame):
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        service.close()
        server.server_close()


if __name__ == "__main__":
    main()
