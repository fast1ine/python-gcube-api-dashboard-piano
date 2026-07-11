const $ = (selector) => document.querySelector(selector);

const elements = {
  groupId: $("#group-id"),
  robotCount: $("#robot-count"),
  period: $("#sensor-period"),
  timeout: $("#connection-timeout"),
  device: $("#device-select"),
  autoSensor: $("#auto-sensor"),
  scan: $("#scan-button"),
  connect: $("#connect-button"),
  disconnect: $("#disconnect-button"),
  badge: $("#status-badge"),
  stateText: $("#status-text"),
  rows: $("#robot-rows"),
  rowCount: $("#row-count"),
  live: $("#live-indicator"),
  logs: $("#log-list"),
  toast: $("#toast"),
};

let hiddenLogIds = new Set();
let latestLogs = [];
let toastTimer;
let polling = false;

function normalizeGroupId(value) {
  const clean = String(value).trim().replace(/^0x/i, "").toUpperCase();
  if (!/^[0-7]{1,2}$/.test(clean)) {
    throw new Error("그룹 ID는 0~7 숫자만 사용해 00~77 범위로 입력하세요.");
  }
  return clean.padStart(2, "0");
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `요청 실패 (${response.status})`);
  return data;
}

function showToast(message, error = false) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.className = `toast visible${error ? " error" : ""}`;
  toastTimer = setTimeout(() => { elements.toast.className = "toast"; }, 3200);
}

async function scanDevices() {
  try {
    const group = normalizeGroupId(elements.groupId.value);
    elements.groupId.value = group;
    elements.scan.disabled = true;
    const timeout = Math.min(Math.max(Number(elements.timeout.value) || 5, 1), 10);
    const data = await request(`/api/devices?group_id=${encodeURIComponent(group)}&timeout=${timeout}`);
    elements.device.replaceChildren(new Option("자동 선택", ""));
    for (const device of data.devices) {
      const option = new Option(`${device.name} · ${device.type.toUpperCase()} · ${device.identifier}`, JSON.stringify(device));
      elements.device.add(option);
    }
    const details = data.errors.length ? ` (${data.errors.join(" / ")})` : "";
    showToast(`${data.devices.length}개 연결 장치를 찾았습니다.${details}`, data.errors.length > 0);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    elements.scan.disabled = false;
  }
}

async function connect() {
  try {
    const selected = elements.device.value ? JSON.parse(elements.device.value) : {};
    const payload = {
      group_id: normalizeGroupId(elements.groupId.value),
      robots: Number(elements.robotCount.value),
      period: Number(elements.period.value),
      timeout: Number(elements.timeout.value),
      auto_sensor: elements.autoSensor.checked,
      device_type: selected.type || "auto",
      identifier: selected.identifier || "",
      name: selected.name || "",
    };
    elements.groupId.value = payload.group_id;
    await request("/api/connect", { method: "POST", body: JSON.stringify(payload) });
    showToast(`그룹 ${payload.group_id} 연결을 시작했습니다.`);
    await refreshStatus();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function disconnect() {
  try {
    await request("/api/disconnect", { method: "POST", body: "{}" });
    showToast("연결 종료를 요청했습니다.");
    await refreshStatus();
  } catch (error) {
    showToast(error.message, true);
  }
}

function display(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (value === true) return "Yes";
  if (value === false) return "No";
  return String(value);
}

function setMetric(id, value) { $(`#metric-${id}`).textContent = display(value); }

function renderState(data) {
  const state = data.state || "Idle";
  elements.stateText.textContent = state;
  elements.badge.className = `status-badge ${state.toLowerCase()}`;
  const active = data.running || ["Connecting", "Connected", "Stopping"].includes(state);
  elements.connect.disabled = active;
  elements.disconnect.disabled = !active;
  elements.scan.disabled = active;
  elements.live.classList.toggle("active", state === "Connected");

  setMetric("bluetooth", data.bluetooth);
  setMetric("transport", data.transport);
  setMetric("device", data.device);
  setMetric("group", data.group_id);
  setMetric("connection", `${data.connection.connected}/${data.connection.total}`);
  setMetric("mac", data.mac);
  setMetric("updated", data.last_update);
}

function renderRows(cubes) {
  elements.rowCount.textContent = `${cubes.length} cube${cubes.length === 1 ? "" : "s"}`;
  if (!cubes.length) {
    elements.rows.innerHTML = '<tr class="empty-row"><td colspan="14">연결된 로봇이 없습니다.</td></tr>';
    return;
  }
  elements.rows.innerHTML = cubes.map((cube) => `
    <tr>
      <td class="cube-cell">#${display(cube.cube)}</td>
      <td>${display(cube.sensor_mode)}</td>
      <td>${display(cube.button)}</td>
      <td>${display(cube.gyro)}</td>
      <td>${display(cube.acc)}</td>
      <td>${display(cube.prox)}</td>
      <td>${display(cube.previous_prox)}</td>
      <td>${display(cube.ain)}</td>
      <td>${display(cube.stepper_mode)}</td>
      <td>${display(cube.stepper_speed)}</td>
      <td>${display(cube.stepper_step)}</td>
      <td>${display(cube.stepper_paused)}</td>
      <td>${display(cube.servo_mode)}</td>
      <td>${display(cube.servo_angle)}</td>
    </tr>`).join("");
}

function renderLogs(logs) {
  latestLogs = logs;
  const visible = logs.filter((entry) => !hiddenLogIds.has(entry.id));
  elements.logs.innerHTML = visible.map((entry) => `
    <div class="log-entry ${entry.level}">
      <time>${entry.time}</time>
      <p>${escapeHtml(entry.message)}</p>
    </div>`).join("");
  elements.logs.scrollTop = elements.logs.scrollHeight;
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

async function refreshStatus() {
  if (polling) return;
  polling = true;
  try {
    const data = await request("/api/status");
    renderState(data);
    renderRows(data.cubes || []);
    renderLogs(data.logs || []);
    if (data.error && data.state === "Error") showToast(data.error, true);
  } catch (error) {
    elements.stateText.textContent = "Server offline";
    elements.badge.className = "status-badge error";
  } finally {
    polling = false;
  }
}

elements.scan.addEventListener("click", scanDevices);
elements.connect.addEventListener("click", connect);
elements.disconnect.addEventListener("click", disconnect);
elements.groupId.addEventListener("blur", () => {
  try { elements.groupId.value = normalizeGroupId(elements.groupId.value); }
  catch (error) { showToast(error.message, true); }
});
$("#clear-log-button").addEventListener("click", () => {
  hiddenLogIds = new Set(latestLogs.map((entry) => entry.id));
  elements.logs.replaceChildren();
});

refreshStatus();
setInterval(refreshStatus, 500);
setTimeout(scanDevices, 700);
