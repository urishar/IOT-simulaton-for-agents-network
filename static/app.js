const state = {
  data: null,
  mode: "sync",
  index: 0,
  timer: null,
};

const el = {
  form: document.querySelector("#controls"),
  agents: document.querySelector("#agents"),
  probability: document.querySelector("#probability"),
  probabilityText: document.querySelector("#probabilityText"),
  seed: document.querySelector("#seed"),
  svg: document.querySelector("#network"),
  play: document.querySelector("#play"),
  step: document.querySelector("#step"),
  label: document.querySelector("#eventLabel"),
  syncTab: document.querySelector("#syncTab"),
  asyncTab: document.querySelector("#asyncTab"),
  metrics: document.querySelector("#metricsGrid"),
  lamport: document.querySelector("#lamportPanel"),
  tables: document.querySelector("#tables"),
  timeline: document.querySelector("#timeline"),
};

el.probability.addEventListener("input", () => {
  el.probabilityText.textContent = Number(el.probability.value).toFixed(2);
});

el.form.addEventListener("submit", (event) => {
  event.preventDefault();
  loadDemo();
});

el.syncTab.addEventListener("click", () => setMode("sync"));
el.asyncTab.addEventListener("click", () => setMode("async"));

el.step.addEventListener("input", () => {
  stop();
  state.index = Number(el.step.value);
  render();
});

el.play.addEventListener("click", () => {
  if (state.timer) {
    stop();
  } else {
    play();
  }
});

async function loadDemo() {
  stop();
  const params = new URLSearchParams({
    agents: el.agents.value,
    probability: el.probability.value,
    seed: el.seed.value,
  });
  const response = await fetch(`/api/demo?${params.toString()}`);
  state.data = await response.json();
  state.index = 0;
  setMode(state.mode);
}

function setMode(mode) {
  state.mode = mode;
  state.index = 0;
  el.syncTab.classList.toggle("active", mode === "sync");
  el.asyncTab.classList.toggle("active", mode === "async");
  const events = currentEvents();
  el.step.max = Math.max(0, events.length - 1);
  el.step.value = 0;
  render();
}

function currentRun() {
  return state.data[state.mode];
}

function currentEvents() {
  return currentRun().events;
}

function currentEvent() {
  return currentEvents()[state.index] || {};
}

function play() {
  el.play.textContent = "Pause";
  state.timer = window.setInterval(() => {
    const events = currentEvents();
    if (state.index >= events.length - 1) {
      stop();
      return;
    }
    state.index += 1;
    el.step.value = state.index;
    render();
  }, state.mode === "sync" ? 420 : 520);
}

function stop() {
  window.clearInterval(state.timer);
  state.timer = null;
  el.play.textContent = "Play";
}

function render() {
  if (!state.data) return;
  renderGraph();
  renderMetrics();
  renderLamport();
  renderTables();
  renderTimeline();
  el.step.value = state.index;
  el.label.textContent = currentEvent().label || "Ready";
}

function renderGraph() {
  const { nodes, edges } = state.data.graph;
  const event = currentEvent();
  const tables = event.tables || currentRun().tables;
  const knownCounts = Object.fromEntries(
    Object.entries(tables).map(([agent, rows]) => [agent, rows.length])
  );

  el.svg.innerHTML = "";

  for (const edge of edges) {
    const a = nodes[edge.source];
    const b = nodes[edge.target];
    el.svg.append(svgEl("line", {
      class: "edge",
      x1: a.x,
      y1: a.y,
      x2: b.x,
      y2: b.y,
    }));
  }

  if (Number.isInteger(event.sender) && Number.isInteger(event.receiver)) {
    const a = nodes[event.sender];
    const b = nodes[event.receiver];
    el.svg.append(svgEl("line", {
      class: "message-line",
      x1: a.x,
      y1: a.y,
      x2: b.x,
      y2: b.y,
    }));
  }

  for (const node of nodes) {
    const group = svgEl("g", {});
    const isHot = node.id === event.sender || node.id === event.receiver;
    const isComplete = knownCounts[node.id] === nodes.length;
    group.append(svgEl("circle", {
      class: `node ${isHot ? "hot" : ""} ${isComplete ? "known" : ""}`,
      cx: node.x,
      cy: node.y,
      r: 28,
    }));
    const label = svgEl("text", { class: "node-label", x: node.x, y: node.y });
    label.textContent = `A${node.id}`;
    group.append(label);
    const known = svgEl("text", { class: "known-label", x: node.x, y: node.y + 45 });
    known.textContent = `${knownCounts[node.id] || 1}/${nodes.length} rows`;
    group.append(known);
    el.svg.append(group);
  }
}

function renderMetrics() {
  const sync = state.data.sync.metrics;
  const async = state.data.async.metrics;
  const comparison = state.data.comparison;
  const cards = [
    ["Agents", comparison.agentCount],
    ["Edges", comparison.edgeCount],
    ["Sync rounds", sync.rounds],
    ["Sync messages", sync.messages],
    ["Async deliveries", async.deliveries],
    ["Max Lamport", async.maxLamport],
  ];
  el.metrics.innerHTML = cards.map(([label, value]) => (
    `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`
  )).join("");
}

function renderLamport() {
  const agentCount = state.data.comparison.agentCount;
  const event = currentEvent();
  const clocks = state.mode === "async"
    ? event.lamport || state.data.async.lamport
    : Object.fromEntries(Array.from({ length: agentCount }, (_, i) => [i, 0]));
  const max = Math.max(1, ...Object.values(clocks));

  el.lamport.innerHTML = Object.entries(clocks).map(([agent, value]) => `
    <div class="clock-row">
      <strong>A${agent}</strong>
      <div class="clock-track"><div class="clock-fill" style="width:${(value / max) * 100}%"></div></div>
      <span>${value}</span>
    </div>
  `).join("");
}

function renderTables() {
  const event = currentEvent();
  const tables = event.tables || currentRun().tables;
  el.tables.innerHTML = Object.entries(tables).map(([agent, rows]) => `
    <div class="table-block">
      <h3>Agent A${agent}</h3>
      <table>
        <thead><tr><th>target</th><th>dist</th><th>via</th></tr></thead>
        <tbody>
          ${rows.map(row => `<tr><td>A${row.target}</td><td>${row.distance}</td><td>A${row.via}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>
  `).join("");
}

function renderTimeline() {
  const events = currentEvents();
  const visible = events.slice(0, Math.min(events.length, 80));
  el.timeline.innerHTML = visible.map((event, index) => {
    const changed = event.changed && event.changed.length;
    const text = event.sender === null
      ? event.label
      : `A${event.sender} -> A${event.receiver}${changed ? `, +${changed} row${changed > 1 ? "s" : ""}` : ""}`;
    return `<div class="event ${index === state.index ? "active" : ""} ${changed ? "changed" : ""}">${text}</div>`;
  }).join("");
}

function svgEl(name, attributes) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attributes)) {
    node.setAttribute(key, value);
  }
  return node;
}

loadDemo();
