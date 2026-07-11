const $ = (selector) => document.querySelector(selector);

const WHITE_OFFSETS = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24];
const BLACK_KEYS = [
  [1, 1], [3, 2], [6, 4], [8, 5], [10, 6],
  [13, 8], [15, 9], [18, 11], [20, 12], [22, 13],
];
const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const KEY_BINDINGS = ["a", "w", "s", "e", "d", "f", "t", "g", "y", "h", "u", "j", "k"];
const KEY_OFFSETS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

const elements = {
  keyboard: $("#piano-keyboard"),
  cube: $("#piano-cube"),
  duration: $("#note-duration"),
  octave: $("#octave-value"),
  currentNote: $("#current-note"),
  device: $("#instrument-device"),
  light: $("#instrument-light"),
  badge: $("#piano-status-badge"),
  statusText: $("#piano-status-text"),
  stop: $("#stop-note"),
  toast: $("#piano-toast"),
};

let octave = 4;
let connected = false;
let toastTimer;
let lastTotal = 0;

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
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
  toastTimer = setTimeout(() => { elements.toast.className = "toast"; }, 3000);
}

function protocolNote(offset) {
  return 12 * (octave + 1) - 8 + offset;
}

function noteLabel(offset) {
  const midi = 12 * (octave + 1) + offset;
  return `${NOTE_NAMES[midi % 12]}${Math.floor(midi / 12) - 1}`;
}

function buildKeyboard() {
  elements.keyboard.replaceChildren();
  for (const offset of WHITE_OFFSETS) {
    const key = document.createElement("button");
    key.type = "button";
    key.className = "piano-key white-key";
    key.dataset.offset = offset;
    key.innerHTML = `<span>${noteLabel(offset)}</span>`;
    elements.keyboard.appendChild(key);
  }
  for (const [offset, afterWhite] of BLACK_KEYS) {
    const key = document.createElement("button");
    key.type = "button";
    key.className = "piano-key black-key";
    key.dataset.offset = offset;
    key.style.left = `calc(${afterWhite / WHITE_OFFSETS.length * 100}% - 17px)`;
    key.innerHTML = `<span>${noteLabel(offset)}</span>`;
    elements.keyboard.appendChild(key);
  }
  elements.keyboard.querySelectorAll(".piano-key").forEach((key) => {
    key.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      playOffset(Number(key.dataset.offset), key);
    });
  });
}

async function playNotes(notes, durations, rests = 0) {
  if (!connected) {
    showToast("대시보드에서 PingPong 로봇을 먼저 연결하세요.", true);
    return;
  }
  try {
    await request("/api/piano/play", {
      method: "POST",
      body: JSON.stringify({
        cube: Number(elements.cube.value),
        notes,
        durations,
        rests,
      }),
    });
  } catch (error) {
    showToast(error.message, true);
  }
}

function playOffset(offset, keyElement) {
  const label = noteLabel(offset);
  elements.currentNote.textContent = label;
  if (keyElement) {
    keyElement.classList.add("pressed");
    setTimeout(() => keyElement.classList.remove("pressed"), 140);
  }
  playNotes([protocolNote(offset)], Number(elements.duration.value));
}

async function stopMusic() {
  try {
    await request("/api/piano/stop", {
      method: "POST",
      body: JSON.stringify({ cube: Number(elements.cube.value) }),
    });
    elements.currentNote.textContent = "-";
  } catch (error) {
    showToast(error.message, true);
  }
}

function updateCubeOptions(total) {
  if (total === lastTotal) return;
  const selected = Number(elements.cube.value) || 1;
  elements.cube.replaceChildren();
  for (let cube = 1; cube <= Math.max(total, 1); cube += 1) {
    elements.cube.add(new Option(`Cube ${cube}`, String(cube)));
  }
  elements.cube.value = String(Math.min(selected, Math.max(total, 1)));
  lastTotal = total;
}

async function refreshStatus() {
  try {
    const data = await request("/api/status");
    connected = data.state === "Connected" && data.connection.connected > 0;
    elements.statusText.textContent = data.state;
    elements.badge.className = `status-badge ${data.state.toLowerCase()}`;
    elements.light.classList.toggle("active", connected);
    elements.device.textContent = connected
      ? `${data.device} · ${data.connection.connected}/${data.connection.total}`
      : "로봇 연결 필요";
    elements.cube.disabled = !connected;
    elements.stop.disabled = !connected;
    updateCubeOptions(data.connection.total || 0);
  } catch (_error) {
    connected = false;
    elements.statusText.textContent = "Server offline";
    elements.badge.className = "status-badge error";
    elements.device.textContent = "서버 연결 끊김";
  }
}

function changeOctave(delta) {
  octave = Math.min(6, Math.max(2, octave + delta));
  elements.octave.textContent = octave;
  buildKeyboard();
}

const presets = {
  scale: { offsets: [0, 2, 4, 5, 7, 9, 11, 12], durations: 180, rests: 20 },
  school: { offsets: [4, 2, 0, 2, 4, 4, 4, 2, 2, 2, 4, 7, 7], durations: 250, rests: 25 },
  signal: { offsets: [0, 7, 12], durations: [140, 140, 380], rests: [30, 30, 0] },
};

document.querySelectorAll("[data-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    const preset = presets[button.dataset.preset];
    elements.currentNote.textContent = button.querySelector("strong").textContent;
    playNotes(preset.offsets.map(protocolNote), preset.durations, preset.rests);
  });
});

document.addEventListener("keydown", (event) => {
  if (event.repeat || event.ctrlKey || event.altKey || event.metaKey) return;
  const index = KEY_BINDINGS.indexOf(event.key.toLowerCase());
  if (index < 0) return;
  event.preventDefault();
  const offset = KEY_OFFSETS[index];
  playOffset(offset, elements.keyboard.querySelector(`[data-offset="${offset}"]`));
});

$("#octave-down").addEventListener("click", () => changeOctave(-1));
$("#octave-up").addEventListener("click", () => changeOctave(1));
elements.stop.addEventListener("click", stopMusic);

buildKeyboard();
refreshStatus();
setInterval(refreshStatus, 800);
