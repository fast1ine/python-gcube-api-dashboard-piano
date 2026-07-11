import argparse
import queue
import threading
import time
import traceback
import tkinter as tk
from tkinter import ttk


class StatusDashboard:
    POLL_INTERVAL_MS = 150

    def __init__(
        self,
        root,
        default_robots=1,
        default_period=0.1,
        default_bluetooth_timeout=30,
        default_group_id="00",
        auto_sensor=True,
    ):
        self.root = root
        self.root.title("PingPong Status Dashboard")
        self.root.geometry("1180x620")
        self.root.minsize(980, 520)

        self.events = queue.Queue()
        self.stop_requested = threading.Event()
        self.worker = None
        self.device_scan_worker = None
        self.client = None
        self.bluetooth_window = None
        self.bluetooth_tree = None
        self.group_id_entry = None
        self.bluetooth_scan_var = tk.StringVar(value="")

        self.robot_count_var = tk.IntVar(value=default_robots)
        self.period_var = tk.StringVar(value=str(default_period))
        self.bluetooth_timeout_var = tk.StringVar(value=str(default_bluetooth_timeout))
        self.group_id_var = tk.StringVar(value=str(default_group_id).upper())
        self.auto_sensor_var = tk.BooleanVar(value=auto_sensor)
        self.state_var = tk.StringVar(value="Idle")
        self.bluetooth_var = tk.StringVar(value="-")
        self.port_var = tk.StringVar(value="-")
        self.active_group_var = tk.StringVar(value="-")
        self.connection_var = tk.StringVar(value="-")
        self.mac_var = tk.StringVar(value="-")
        self.last_update_var = tk.StringVar(value="-")

        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(self.POLL_INTERVAL_MS, self._drain_events)

    def _build_layout(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill=tk.X)

        ttk.Label(toolbar, text="Robots").pack(side=tk.LEFT)
        self.robot_spin = tk.Spinbox(
            toolbar,
            from_=1,
            to=8,
            width=4,
            textvariable=self.robot_count_var,
            justify=tk.CENTER,
        )
        self.robot_spin.pack(side=tk.LEFT, padx=(6, 14))

        ttk.Label(toolbar, text="Sensor period").pack(side=tk.LEFT)
        self.period_entry = ttk.Entry(toolbar, width=7, textvariable=self.period_var)
        self.period_entry.pack(side=tk.LEFT, padx=(6, 4))
        ttk.Label(toolbar, text="sec").pack(side=tk.LEFT, padx=(0, 14))

        ttk.Label(toolbar, text="BT timeout").pack(side=tk.LEFT)
        self.bluetooth_timeout_entry = ttk.Entry(toolbar, width=7, textvariable=self.bluetooth_timeout_var)
        self.bluetooth_timeout_entry.pack(side=tk.LEFT, padx=(6, 4))
        ttk.Label(toolbar, text="sec").pack(side=tk.LEFT, padx=(0, 14))

        self.auto_sensor_check = ttk.Checkbutton(
            toolbar,
            text="Auto sensor",
            variable=self.auto_sensor_var,
        )
        self.auto_sensor_check.pack(side=tk.LEFT, padx=(0, 14))

        self.bluetooth_button = ttk.Button(
            toolbar,
            text="Bluetooth...",
            command=self.open_bluetooth_window,
        )
        self.bluetooth_button.pack(side=tk.LEFT)

        self.connect_button = ttk.Button(toolbar, text="Auto connect", command=self.connect)
        self.connect_button.pack(side=tk.LEFT, padx=(8, 0))

        self.stop_button = ttk.Button(toolbar, text="Stop", command=self.stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(8, 0))

        summary = ttk.Frame(outer, padding=(0, 12, 0, 8))
        summary.pack(fill=tk.X)
        self._summary_item(summary, "State", self.state_var).pack(side=tk.LEFT, padx=(0, 28))
        self._summary_item(summary, "Bluetooth", self.bluetooth_var).pack(side=tk.LEFT, padx=(0, 28))
        self._summary_item(summary, "Port", self.port_var).pack(side=tk.LEFT, padx=(0, 28))
        self._summary_item(summary, "Group ID", self.active_group_var).pack(side=tk.LEFT, padx=(0, 28))
        self._summary_item(summary, "Connection", self.connection_var).pack(side=tk.LEFT, padx=(0, 28))
        self._summary_item(summary, "MAC", self.mac_var).pack(side=tk.LEFT, padx=(0, 28))
        self._summary_item(summary, "Last update", self.last_update_var).pack(side=tk.LEFT)

        table_frame = ttk.Frame(outer)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = (
            "cube",
            "sensor_mode",
            "button",
            "gyro",
            "acc",
            "prox",
            "prox_old",
            "ain",
            "stepper_mode",
            "stepper_speed",
            "stepper_step",
            "stepper_pause",
            "servo_mode",
            "servo_angle",
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        headings = {
            "cube": "Cube",
            "sensor_mode": "Sensor",
            "button": "Button",
            "gyro": "Gyro XYZ",
            "acc": "Acc XYZ",
            "prox": "Prox",
            "prox_old": "Prev Prox",
            "ain": "AIN",
            "stepper_mode": "Stepper",
            "stepper_speed": "Speed",
            "stepper_step": "Step",
            "stepper_pause": "Paused",
            "servo_mode": "Servo",
            "servo_angle": "Angle",
        }
        widths = {
            "cube": 56,
            "sensor_mode": 92,
            "button": 70,
            "gyro": 112,
            "acc": 112,
            "prox": 64,
            "prox_old": 82,
            "ain": 64,
            "stepper_mode": 92,
            "stepper_speed": 72,
            "stepper_step": 72,
            "stepper_pause": 72,
            "servo_mode": 82,
            "servo_angle": 72,
        }
        for name in columns:
            self.tree.heading(name, text=headings[name])
            self.tree.column(name, width=widths[name], minwidth=widths[name], anchor=tk.CENTER)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        log_frame = ttk.Frame(outer, padding=(0, 10, 0, 0))
        log_frame.pack(fill=tk.X)
        ttk.Label(log_frame, text="Log").pack(anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.X)

    def _summary_item(self, parent, title, variable):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text=title).pack(anchor=tk.W)
        ttk.Label(frame, textvariable=variable, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        return frame

    def open_bluetooth_window(self):
        if self.bluetooth_window and self.bluetooth_window.winfo_exists():
            self.bluetooth_window.lift()
            self.bluetooth_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        self.bluetooth_window = window
        window.title("Bluetooth Connection")
        window.geometry("720x420")
        window.minsize(580, 360)
        window.transient(self.root)
        window.protocol("WM_DELETE_WINDOW", self._close_bluetooth_window)

        outer = ttk.Frame(window, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(outer)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header, text="Available PingPong connections", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        ttk.Button(header, text="Refresh", command=self._refresh_bluetooth_ports).pack(side=tk.RIGHT)

        table_frame = ttk.Frame(outer)
        table_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("kind", "identifier", "name", "details")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("kind", text="Type")
        tree.heading("identifier", text="Address / Port")
        tree.heading("name", text="Device")
        tree.heading("details", text="Details")
        tree.column("kind", width=100, minwidth=85, anchor=tk.CENTER, stretch=False)
        tree.column("identifier", width=145, minwidth=100, anchor=tk.CENTER, stretch=False)
        tree.column("name", width=230, minwidth=150)
        tree.column("details", width=230, minwidth=150)
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        tree.bind("<Double-1>", lambda _event: self._connect_selected_bluetooth_port())
        self.bluetooth_tree = tree

        ttk.Label(outer, textvariable=self.bluetooth_scan_var).pack(fill=tk.X, pady=(8, 0))

        group_frame = ttk.Frame(outer, padding=(0, 10, 0, 0))
        group_frame.pack(fill=tk.X)
        ttk.Label(group_frame, text="Group ID").pack(side=tk.LEFT)
        self.group_id_entry = ttk.Entry(
            group_frame,
            width=6,
            justify=tk.CENTER,
            textvariable=self.group_id_var,
        )
        self.group_id_entry.pack(side=tk.LEFT, padx=(8, 6))
        ttk.Label(group_frame, text="Hexadecimal 00-77").pack(side=tk.LEFT)

        actions = ttk.Frame(outer, padding=(0, 12, 0, 0))
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Cancel", command=self._close_bluetooth_window).pack(side=tk.RIGHT)
        ttk.Button(
            actions,
            text="Connect selected",
            command=self._connect_selected_bluetooth_port,
        ).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(
            actions,
            text="Auto search",
            command=self._connect_from_bluetooth_window,
        ).pack(side=tk.LEFT)

        self._refresh_bluetooth_ports()
        window.after(50, window.focus_force)

    def _refresh_bluetooth_ports(self):
        if not self.bluetooth_tree:
            return
        if self.device_scan_worker and self.device_scan_worker.is_alive():
            return
        self.bluetooth_scan_var.set("Scanning Bluetooth LE devices and USB dongles...")
        for item in self.bluetooth_tree.get_children():
            self.bluetooth_tree.delete(item)
        try:
            group_label = "{:02X}".format(self._parse_group_id(self.group_id_var.get()))
        except ValueError as exc:
            self.bluetooth_scan_var.set(str(exc))
            return
        self.device_scan_worker = threading.Thread(
            target=self._scan_connection_devices,
            args=(group_label,),
            daemon=True,
        )
        self.device_scan_worker.start()

    def _scan_connection_devices(self, group_label):
        devices = []
        errors = []
        try:
            import serial.tools.list_ports
            from connection.connectionutils import ConnectionUtils

            for port in serial.tools.list_ports.comports():
                if ConnectionUtils.DONGLE_PNP_ID in str(port.hwid).upper():
                    devices.append(("USB dongle", str(port.device), str(port.description or "PingPong Dongle"), str(port.hwid)))
        except Exception as exc:
            errors.append("USB scan: {}".format(exc))

        try:
            from connection.bletransport import BleSerialTransport

            for device in BleSerialTransport.scan(timeout=5, group_label=group_label):
                devices.append(("Bluetooth LE", device["address"], device["name"], "Nordic UART"))
        except Exception as exc:
            errors.append("BLE scan: {}".format(exc))
        self.events.put(("device_scan", (devices, errors)))

    def _render_connection_devices(self, payload):
        if not self.bluetooth_tree or not self.bluetooth_window or not self.bluetooth_window.winfo_exists():
            return
        devices, errors = payload
        for item in self.bluetooth_tree.get_children():
            self.bluetooth_tree.delete(item)
        for values in devices:
            self.bluetooth_tree.insert("", tk.END, values=values)
        children = self.bluetooth_tree.get_children()
        if children:
            self.bluetooth_scan_var.set("{} PingPong connection(s) found.".format(len(children)))
            self.bluetooth_tree.selection_set(children[0])
            self.bluetooth_tree.focus(children[0])
        elif errors:
            self.bluetooth_scan_var.set(errors[-1])
        else:
            self.bluetooth_scan_var.set("No PingPong BLE device or USB dongle found.")
            self._log("No PingPong device is advertising. Close PingPong Scratch before retrying.")

    def _connect_selected_bluetooth_port(self):
        if not self.bluetooth_tree:
            return
        selection = self.bluetooth_tree.selection()
        if not selection:
            self._log("Select a PingPong connection in the Bluetooth window.")
            return
        values = self.bluetooth_tree.item(selection[0], "values")
        if not values:
            return
        group_id = self._group_id_from_window()
        if group_id is None:
            return
        kind, identifier, name = str(values[0]), str(values[1]), str(values[2])
        if kind == "Bluetooth LE":
            group_label = "{:02X}".format(group_id)
            if group_id > 0 and "PINGPONG.{}".format(group_label) not in name.upper():
                self.bluetooth_scan_var.set(
                    "Selected device does not belong to group {}.".format(group_label)
                )
                return
            self._close_bluetooth_window()
            self.connect(
                group_id=group_id,
                preferred_ble_address=identifier,
                preferred_ble_name=name,
            )
        else:
            self._close_bluetooth_window()
            self.connect(preferred_port=identifier, group_id=group_id)

    def _connect_from_bluetooth_window(self):
        group_id = self._group_id_from_window()
        if group_id is None:
            return
        self._close_bluetooth_window()
        self.connect(group_id=group_id)

    def _group_id_from_window(self):
        try:
            group_id = self._parse_group_id(self.group_id_var.get())
        except ValueError as exc:
            self.bluetooth_scan_var.set(str(exc))
            self._log(str(exc))
            if self.group_id_entry:
                self.group_id_entry.focus_set()
                self.group_id_entry.selection_range(0, tk.END)
            return None
        self.group_id_var.set("{:02X}".format(group_id))
        return group_id

    def _close_bluetooth_window(self):
        if self.bluetooth_window and self.bluetooth_window.winfo_exists():
            self.bluetooth_window.destroy()
        self.bluetooth_window = None
        self.bluetooth_tree = None
        self.group_id_entry = None
        self.bluetooth_scan_var.set("")

    def connect(
        self,
        preferred_port=None,
        group_id=None,
        preferred_ble_address=None,
        preferred_ble_name=None,
    ):
        if self.worker and self.worker.is_alive():
            return

        try:
            robot_count = int(self.robot_count_var.get())
            if not 1 <= robot_count <= 8:
                raise ValueError
        except Exception:
            self._log("Robot count must be between 1 and 8.")
            return

        try:
            period = float(self.period_var.get())
            if not 0.01 <= period <= 1:
                raise ValueError
        except Exception:
            self._log("Sensor period must be between 0.01 and 1.0 seconds.")
            return

        try:
            bluetooth_timeout = float(self.bluetooth_timeout_var.get())
            if bluetooth_timeout < 0:
                raise ValueError
        except Exception:
            self._log("Bluetooth timeout must be 0 or a positive number.")
            return

        try:
            if group_id is None:
                group_id = self._parse_group_id(self.group_id_var.get())
            else:
                group_id = self._validate_group_id_value(group_id)
        except ValueError as exc:
            self._log(str(exc))
            return
        group_label = "{:02X}".format(group_id)
        self.group_id_var.set(group_label)

        self.stop_requested.clear()
        self._set_running_controls(True)
        self.state_var.set("Connecting")
        self.bluetooth_var.set("Scanning")
        self.port_var.set("-")
        self.active_group_var.set(group_label)
        self.connection_var.set("-")
        self.mac_var.set("-")
        self.last_update_var.set("-")
        self._clear_table()
        if preferred_ble_address:
            self._log(
                "Connecting to group {} through Bluetooth LE device {}...".format(
                    group_label,
                    preferred_ble_name or preferred_ble_address,
                )
            )
        elif preferred_port:
            self._log(
                "Connecting to group {} through selected Bluetooth port {}...".format(
                    group_label,
                    preferred_port,
                )
            )
        else:
            self._log("Searching for PingPong Bluetooth LE or USB dongle for group {}...".format(group_label))

        self.worker = threading.Thread(
            target=self._worker_main,
            args=(
                robot_count,
                period,
                bluetooth_timeout,
                self.auto_sensor_var.get(),
                preferred_port,
                group_id,
                preferred_ble_address,
                preferred_ble_name,
            ),
            daemon=True,
        )
        self.worker.start()

    def stop(self):
        if self.worker and self.worker.is_alive():
            self.state_var.set("Stopping")
            self.stop_requested.set()
            self.stop_button.configure(state=tk.DISABLED)
            self._log("Stopping dashboard connection...")

    def close(self):
        if self.worker and self.worker.is_alive():
            self.stop()
            self.root.after(300, self._destroy_when_stopped)
        else:
            self.root.destroy()

    def _destroy_when_stopped(self):
        if self.worker and self.worker.is_alive():
            self.root.after(300, self._destroy_when_stopped)
        else:
            self.root.destroy()

    def _worker_main(
        self,
        robot_count,
        period,
        bluetooth_timeout,
        auto_sensor,
        preferred_port,
        group_id,
        preferred_ble_address,
        preferred_ble_name,
    ):
        client = None
        transport = None
        original_find_bluetooth_dongle = None
        try:
            from pingpongthread import PingPongThread
            from connection.connectionutils import ConnectionUtils

            transport_kind = "serial"
            group_label = "{:02X}".format(group_id)
            if preferred_ble_address or not preferred_port:
                try:
                    from connection.bletransport import BleSerialTransport

                    address = preferred_ble_address
                    name = preferred_ble_name
                    if not address:
                        self.events.put(("bluetooth", "BLE scanning"))
                        scan_timeout = 5 if bluetooth_timeout == 0 else min(max(bluetooth_timeout, 1), 10)
                        devices = BleSerialTransport.scan(timeout=scan_timeout, group_label=group_label)
                        if not devices:
                            raise RuntimeError("No matching PingPong BLE device is advertising.")
                        address = devices[0]["address"]
                        name = devices[0]["name"]
                    self.events.put(("log", "Connecting directly with Bluetooth LE: {}.".format(name or address)))
                    transport = BleSerialTransport(
                        address,
                        name=name,
                        connect_timeout=bluetooth_timeout or 15,
                    )
                    transport_kind = "ble"
                    self.events.put(("bluetooth", "BLE ready"))
                    self.events.put(("port", "{} ({})".format(name or "PingPong", address)))
                except Exception as exc:
                    if preferred_ble_address:
                        raise
                    self.events.put(("log", "Bluetooth LE unavailable: {}".format(exc)))
                    self.events.put(("log", "Falling back to the PingPong USB dongle."))

            if transport is None:
                original_find_bluetooth_dongle = ConnectionUtils.find_bluetooth_dongle

                def find_bluetooth_dongle_with_dashboard(instance, connect_bytes):
                    return self._find_bluetooth_dongle(
                        connect_bytes,
                        bluetooth_timeout,
                        preferred_port,
                    )

                ConnectionUtils.find_bluetooth_dongle = find_bluetooth_dongle_with_dashboard

            client = PingPongThread(
                number=robot_count,
                group_id=group_id,
                transport=transport,
                transport_kind=transport_kind,
            )
            self.events.put(("client", client))
            self.events.put(("log", "Starting {} reader thread.".format(transport_kind.upper())))
            client.start()
            self.events.put(("log", "Waiting for full robot connection."))
            if not self._wait_until_full_connect(client, bluetooth_timeout):
                return
            self.events.put(("connected", None))

            if auto_sensor and transport_kind == "ble":
                time.sleep(1)

            while not self.stop_requested.is_set():
                try:
                    if auto_sensor and client.play_once_full_connect():
                        self._start_sensor_stream(client, period)
                    status = client.get_robot_status()
                    self.events.put(("status", status))
                except Exception:
                    self.events.put(("error", traceback.format_exc()))
                time.sleep(0.15)
        except Exception:
            self.events.put(("error", traceback.format_exc()))
        finally:
            if client is not None:
                try:
                    client.end()
                except Exception:
                    self.events.put(("log", "Connection cleanup finished with a non-fatal error."))
            elif transport is not None:
                transport.close()
            if transport is not None and transport.is_open:
                transport.close()
            if original_find_bluetooth_dongle is not None:
                try:
                    from connection.connectionutils import ConnectionUtils
                    ConnectionUtils.find_bluetooth_dongle = original_find_bluetooth_dongle
                except Exception:
                    pass
            self._reset_pingpong_thread_flags()
            self.events.put(("stopped", None))

    def _reset_pingpong_thread_flags(self):
        try:
            from pingpongthread import PingPongThread
            PingPongThread._is_start = False
            PingPongThread._is_instance = False
        except Exception:
            pass

    def _find_bluetooth_dongle(self, connect_bytes, bluetooth_timeout, preferred_port=None):
        import serial
        import serial.tools.list_ports
        from connection.connectionutils import ConnectionUtils

        started_at = time.time()
        last_scan_log_at = 0
        while not self.stop_requested.is_set():
            if bluetooth_timeout and time.time() - started_at > bluetooth_timeout:
                raise RuntimeError("Bluetooth dongle scan timed out.")

            ports = [
                port for port in serial.tools.list_ports.comports()
                if ConnectionUtils.DONGLE_PNP_ID in str(port.hwid).upper()
            ]
            if preferred_port:
                ports = [port for port in ports if str(port.device) == preferred_port]
            now = time.time()
            if now - last_scan_log_at > 5:
                port_names = ", ".join(str(port.device) for port in ports) or "none"
                self.events.put(("bluetooth", "Scanning"))
                if preferred_port:
                    message = "Checking selected Bluetooth port: {}".format(preferred_port)
                else:
                    message = "Bluetooth scan ports: {}".format(port_names)
                self.events.put(("log", message))
                last_scan_log_at = now

            for port in ports:
                if self.stop_requested.is_set():
                    raise RuntimeError("Bluetooth scan stopped.")
                if self._probe_bluetooth_port(serial, port, connect_bytes):
                    self.events.put(("bluetooth", "Ready"))
                    self.events.put(("port", str(port.device)))
                    self.events.put(("log", "Bluetooth dongle found on {}.".format(port.device)))
                    return str(port.device)

            time.sleep(0.5)

        raise RuntimeError("Bluetooth scan stopped.")

    def _probe_bluetooth_port(self, serial_module, port, connect_bytes):
        ser = None
        try:
            ser = serial_module.serial_for_url(
                str(port.device),
                baudrate=115200,
                timeout=1,
                write_timeout=1,
                rtscts=True,
            )
            ser.write(connect_bytes)
            data = ser.read(11)
            return len(data) >= 11 and data[6] == 0xDA and data[10] == 0x0D
        except Exception:
            return False
        finally:
            try:
                if ser is not None:
                    ser.close()
            except Exception:
                pass

    def _wait_until_full_connect(self, client, bluetooth_timeout=0):
        started_at = time.time()
        while not self.stop_requested.is_set():
            if bluetooth_timeout and time.time() - started_at > bluetooth_timeout:
                raise RuntimeError("Robot connection timed out.")
            status = client.get_robot_status()
            self.events.put(("status", status))
            controller = status.get("controller_status", {})
            processed = status.get("processed_status", {})
            connection_number = controller.get("connection_number", 0)
            connected_number = processed.get("connected_number", 0)
            if connection_number == connected_number and connection_number > 0:
                time.sleep(1)
                return True
            time.sleep(0.15)
        return False

    def _start_sensor_stream(self, client, period):
        try:
            client.receive_sensor_data("all", method="periodic", period=period)
            self.events.put(("log", "Periodic sensor stream enabled."))
        except Exception:
            self.events.put(("error", traceback.format_exc()))

    def _drain_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "client":
                    self.client = payload
                elif kind == "connected":
                    self.state_var.set("Connected")
                    self._log("Robots are fully connected.")
                elif kind == "bluetooth":
                    self.bluetooth_var.set(payload)
                elif kind == "port":
                    self.port_var.set(payload)
                elif kind == "device_scan":
                    self._render_connection_devices(payload)
                elif kind == "status":
                    self._render_status(payload)
                elif kind == "error":
                    self.state_var.set("Error")
                    if "scanning" in self.bluetooth_var.get().lower():
                        self.bluetooth_var.set("Error")
                    self._log(self._last_line(payload))
                elif kind == "log":
                    self._log(payload)
                elif kind == "stopped":
                    self.client = None
                    if self.state_var.get() != "Error":
                        self.state_var.set("Stopped")
                    if "scanning" in self.bluetooth_var.get().lower():
                        self.bluetooth_var.set("Stopped")
                    self._set_running_controls(False)
                    self._log("Stopped.")
        except queue.Empty:
            pass
        self.root.after(self.POLL_INTERVAL_MS, self._drain_events)

    def _render_status(self, status):
        controller = status.get("controller_status", {})
        processed = status.get("processed_status", {})
        connection_number = controller.get("connection_number", 0) or 0
        connected_number = processed.get("connected_number", 0)

        self.connection_var.set("{}/{}".format(connected_number, connection_number))
        self.mac_var.set(self._format_triplet(processed.get("MAC_address", [])))
        self.last_update_var.set(time.strftime("%H:%M:%S"))

        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx in range(connection_number):
            row = (
                idx + 1,
                self._list_value(controller.get("get_sensor_mode"), idx),
                self._list_value(processed.get("button"), idx),
                self._format_triplet(self._list_value(processed.get("sensor_gyro_xyz"), idx)),
                self._format_triplet(self._list_value(processed.get("sensor_acc_xyz"), idx)),
                self._list_value(processed.get("sensor_prox"), idx),
                self._list_value(processed.get("sensor_prox_old"), idx),
                self._list_value(processed.get("AIN"), idx),
                self._list_value(controller.get("stepper_mode"), idx),
                self._list_value(controller.get("stepper_speed"), idx),
                self._list_value(controller.get("stepper_step"), idx),
                self._list_value(controller.get("stepper_pause"), idx),
                self._list_value(controller.get("servo_mode"), idx),
                self._list_value(controller.get("servo_angle"), idx),
            )
            self.tree.insert("", tk.END, values=tuple(self._clean_value(value) for value in row))

    def _clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _set_running_controls(self, running):
        self.bluetooth_button.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.connect_button.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.stop_button.configure(state=tk.NORMAL if running else tk.DISABLED)
        self.robot_spin.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.period_entry.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.bluetooth_timeout_entry.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.auto_sensor_check.configure(state=tk.DISABLED if running else tk.NORMAL)

    def _log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, "[{}] {}\n".format(time.strftime("%H:%M:%S"), message))
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _list_value(self, values, index):
        if isinstance(values, (list, tuple)) and 0 <= index < len(values):
            return values[index]
        return None

    def _format_triplet(self, value):
        if isinstance(value, (list, tuple)):
            return ", ".join(str(self._clean_value(item)) for item in value)
        return self._clean_value(value)

    def _clean_value(self, value):
        if value is None:
            return "-"
        if value is True:
            return "Yes"
        if value is False:
            return "No"
        return value

    @staticmethod
    def _parse_group_id(value):
        text = str(value).strip().upper()
        if text.startswith("0X"):
            text = text[2:]
        if not 1 <= len(text) <= 2 or any(char not in "01234567" for char in text):
            raise ValueError("Group ID must be hexadecimal 00-77 using digits 0 to 7.")
        return int(text, 16)

    @staticmethod
    def _validate_group_id_value(group_id):
        if isinstance(group_id, bool) or not isinstance(group_id, int):
            raise ValueError("Group ID must be hexadecimal 00-77 using digits 0 to 7.")
        high_nibble = group_id >> 4
        low_nibble = group_id & 0x0F
        if group_id < 0 or high_nibble > 7 or low_nibble > 7:
            raise ValueError("Group ID must be hexadecimal 00-77 using digits 0 to 7.")
        return group_id

    def _last_line(self, text):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines[-1] if lines else text


def parse_args():
    parser = argparse.ArgumentParser(description="PingPong robot status dashboard")
    parser.add_argument("--robots", type=int, default=1, help="number of robots, 1 to 8")
    parser.add_argument("--period", type=float, default=0.1, help="sensor period in seconds")
    parser.add_argument("--bluetooth-timeout", type=float, default=30, help="Bluetooth scan timeout in seconds, 0 retries forever")
    parser.add_argument("--group-id", default="00", help="robot group ID in hexadecimal, 00 to 77")
    parser.add_argument("--no-auto-sensor", action="store_true", help="do not start periodic sensor polling")
    return parser.parse_args()


def main():
    args = parse_args()
    root = tk.Tk()
    StatusDashboard(
        root,
        default_robots=args.robots,
        default_period=args.period,
        default_bluetooth_timeout=args.bluetooth_timeout,
        default_group_id=args.group_id,
        auto_sensor=not args.no_auto_sensor,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
