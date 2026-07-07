"use strict";
// Interactive label editor: upload -> adjust (crop/rotate/threshold/profile) -> print.
// Vanilla JS, no build step. Crop coordinates are stored as 0..1 fractions so they
// are independent of the displayed image scale.

const $ = (id) => document.getElementById(id);
const state = {
  id: null,
  page: 0,
  pages: 1,
  profile: "generic_4x6",
  cropMode: "profile",   // profile | auto | manual | none
  rotate: 0,
  threshold: 128,
  crop: [0.1, 0.1, 0.9, 0.9], // manual box fractions [l,t,r,b]
};
let renderTimer = null;
let lastObjectUrl = null;

// ---------- toast ----------
function toast(msg, kind = "") {
  const el = $("toast");
  el.textContent = msg;
  el.className = "toast show " + kind;
  clearTimeout(el._t);
  el._t = setTimeout(() => (el.className = "toast " + kind), 3200);
}

// ---------- upload ----------
async function upload(file) {
  const body = new FormData();
  body.append("file", file);
  toast("Uploading " + file.name + "…");
  let res;
  try {
    res = await fetch("/api/upload", { method: "POST", body });
  } catch (e) { toast("Upload failed: " + e, "err"); return; }
  if (!res.ok) { toast("Upload failed: " + (await res.text()), "err"); return; }
  const data = await res.json();
  state.id = data.id;
  state.page = 0;
  state.pages = data.pages || 1;
  state.profile = data.suggested_profile;
  state.cropMode = "profile";
  state.rotate = 0;
  state.threshold = 128;
  $("srcName").textContent = data.name + `  (${data.width}×${data.height})`;
  $("profile").value = state.profile;
  syncControls();
  syncPageNav();
  loadSourcePage();
  $("editor").classList.remove("hidden");
  $("srcImg").onload = () => { positionCropBox(); render(); };
}

function loadSourcePage() {
  $("srcImg").src = `/api/source/${state.id}?page=${state.page}&t=` + Date.now();
}

function syncPageNav() {
  const nav = $("pageNav");
  nav.classList.toggle("hidden", state.pages <= 1);
  $("pageLabel").textContent = `Page ${state.page + 1} of ${state.pages}`;
  $("pagePrev").disabled = state.page <= 0;
  $("pageNext").disabled = state.page >= state.pages - 1;
}

function gotoPage(delta) {
  const next = Math.min(state.pages - 1, Math.max(0, state.page + delta));
  if (next === state.page) return;
  state.page = next;
  syncPageNav();
  loadSourcePage(); // onload triggers render()
}

// ---------- render (debounced) ----------
function scheduleRender() { clearTimeout(renderTimer); renderTimer = setTimeout(render, 180); }

async function render() {
  if (!state.id) return;
  $("renderSpin").classList.remove("hidden");
  const payload = {
    id: state.id,
    page: state.page,
    profile: state.profile,
    rotate: state.rotate,
    threshold: state.threshold,
    crop_mode: state.cropMode,
    crop: state.cropMode === "manual" ? state.crop : null,
  };
  let res;
  try {
    res = await fetch("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (e) { $("renderSpin").classList.add("hidden"); toast("Render failed: " + e, "err"); return; }
  if (!res.ok) { $("renderSpin").classList.add("hidden"); toast("Render error: " + (await res.text()), "err"); return; }
  const bytes = res.headers.get("X-Zpl-Bytes");
  const blob = await res.blob();
  if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);
  lastObjectUrl = URL.createObjectURL(blob);
  $("outImg").src = lastObjectUrl;
  $("zplInfo").textContent = bytes ? `ZPL: ${(+bytes / 1024).toFixed(1)} KB` : "";
  $("renderSpin").classList.add("hidden");
}

// ---------- print ----------
async function doPrint() {
  if (!state.id) return;
  const btn = $("printBtn");
  btn.disabled = true; btn.textContent = "Printing…";
  try {
    const res = await fetch("/api/print", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: state.id, page: state.page, profile: state.profile, rotate: state.rotate,
        threshold: state.threshold, crop_mode: state.cropMode,
        crop: state.cropMode === "manual" ? state.crop : null,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok) { toast("✓ " + data.detail, "ok"); loadHistory(); }
    else toast("Print failed: " + (data.detail || res.status), "err");
  } catch (e) { toast("Print failed: " + e, "err"); }
  finally { btn.disabled = false; btn.textContent = "Print"; }
}

// ---------- controls ----------
function syncControls() {
  document.querySelectorAll("#cropMode button").forEach((b) =>
    b.classList.toggle("on", b.dataset.crop === state.cropMode));
  document.querySelectorAll("#rotate button").forEach((b) =>
    b.classList.toggle("on", +b.dataset.rot === state.rotate));
  $("threshold").value = state.threshold;
  $("threshVal").textContent = state.threshold;
  $("cropbox").classList.toggle("hidden", state.cropMode !== "manual");
  $("cropHint").textContent = state.cropMode === "manual"
    ? "Drag the box to frame the label; drag corners to resize."
    : state.cropMode === "auto" ? "Auto-cropping to the largest content block."
    : state.cropMode === "none" ? "Using the whole page." : "Using the profile's crop setting.";
  if (state.cropMode === "manual") positionCropBox();
}

function wireControls() {
  $("profile").addEventListener("change", (e) => { state.profile = e.target.value; scheduleRender(); });
  $("cropMode").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    state.cropMode = b.dataset.crop; syncControls(); scheduleRender();
  });
  $("rotate").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    state.rotate = +b.dataset.rot; syncControls(); scheduleRender();
  });
  $("threshold").addEventListener("input", (e) => {
    state.threshold = +e.target.value; $("threshVal").textContent = state.threshold; scheduleRender();
  });
  $("printBtn").addEventListener("click", doPrint);
  $("resetBtn").addEventListener("click", () => {
    state.rotate = 0; state.threshold = 128; state.cropMode = "profile";
    $("profile").value = state.profile; syncControls(); scheduleRender();
  });
}

// ---------- crop box (manual) ----------
function positionCropBox() {
  const img = $("srcImg"), box = $("cropbox");
  if (!img.clientWidth) return;
  const [l, t, r, b] = state.crop;
  box.style.left = l * img.clientWidth + "px";
  box.style.top = t * img.clientHeight + "px";
  box.style.width = (r - l) * img.clientWidth + "px";
  box.style.height = (b - t) * img.clientHeight + "px";
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function wireCropBox() {
  const stage = $("stage"), img = $("srcImg"), box = $("cropbox");
  let mode = null, corner = null, startX = 0, startY = 0, startCrop = null;

  const toFrac = (e) => {
    const rect = img.getBoundingClientRect();
    return [clamp((e.clientX - rect.left) / rect.width, 0, 1),
            clamp((e.clientY - rect.top) / rect.height, 0, 1)];
  };

  stage.addEventListener("pointerdown", (e) => {
    if (state.cropMode !== "manual") return;
    e.preventDefault();
    const handle = e.target.closest(".handle");
    startCrop = state.crop.slice();
    [startX, startY] = toFrac(e);
    if (handle) { mode = "resize"; corner = handle.className.split(" ")[1]; }
    else if (e.target === box) { mode = "move"; }
    else { mode = "draw"; state.crop = [startX, startY, startX, startY]; }
    stage.setPointerCapture(e.pointerId);
  });

  stage.addEventListener("pointermove", (e) => {
    if (!mode) return;
    const [fx, fy] = toFrac(e);
    let [l, t, r, b] = state.crop;
    if (mode === "draw") { l = Math.min(startX, fx); r = Math.max(startX, fx); t = Math.min(startY, fy); b = Math.max(startY, fy); }
    else if (mode === "move") {
      const dw = startCrop[2] - startCrop[0], dh = startCrop[3] - startCrop[1];
      l = clamp(startCrop[0] + (fx - startX), 0, 1 - dw); t = clamp(startCrop[1] + (fy - startY), 0, 1 - dh);
      r = l + dw; b = t + dh;
    } else if (mode === "resize") {
      if (corner.includes("w")) l = Math.min(fx, r - 0.02);
      if (corner.includes("e")) r = Math.max(fx, l + 0.02);
      if (corner.includes("n")) t = Math.min(fy, b - 0.02);
      if (corner.includes("s")) b = Math.max(fy, t + 0.02);
    }
    state.crop = [l, t, r, b];
    positionCropBox();
  });

  const finish = (e) => {
    if (!mode) return;
    mode = null;
    try { stage.releasePointerCapture(e.pointerId); } catch (_) {}
    scheduleRender();
  };
  stage.addEventListener("pointerup", finish);
  stage.addEventListener("pointercancel", finish);
  window.addEventListener("resize", positionCropBox);
}

// ---------- saved label history ----------
function esc(s) { return (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

async function loadHistory() {
  let list;
  try { list = await (await fetch("/api/history")).json(); } catch (_) { return; }
  const wrap = $("history"), el = $("historyList");
  if (!list.length) { wrap.classList.add("hidden"); return; }
  wrap.classList.remove("hidden");
  el.innerHTML = list.map((h) => {
    const when = h.created ? new Date(h.created).toLocaleString() : "";
    const pg = h.page ? " · p" + (h.page + 1) : "";
    return `<div class="hcard">
      <img src="${h.preview_url}" alt="label" loading="lazy">
      <div class="hmeta">
        <div class="hname" title="${esc(h.name)}">${esc(h.name)}</div>
        <div class="muted">${esc(h.profile)}${pg} · ${esc(when)}</div>
        <div class="hactions">
          <button class="reprint" data-id="${h.id}">Reprint</button>
          <button class="del" data-id="${h.id}">Delete</button>
        </div>
      </div></div>`;
  }).join("");
}

function wireHistory() {
  $("historyList").addEventListener("click", async (e) => {
    const btn = e.target.closest("button"); if (!btn) return;
    const id = btn.dataset.id;
    if (btn.classList.contains("reprint")) {
      btn.disabled = true;
      try {
        const res = await fetch(`/api/history/${id}/reprint`, { method: "POST" });
        const d = await res.json().catch(() => ({}));
        toast(res.ok ? "✓ " + d.detail : "Reprint failed: " + (d.detail || res.status), res.ok ? "ok" : "err");
      } finally { btn.disabled = false; }
    } else if (btn.classList.contains("del")) {
      await fetch(`/api/history/${id}`, { method: "DELETE" });
      loadHistory();
    }
  });
}

// ---------- printer status ----------
async function refreshStatus() {
  const dot = $("statusDot"), text = $("statusText");
  text.textContent = "checking…"; dot.className = "dot";
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    if (!data.ok) { dot.className = "dot err"; text.textContent = "offline · " + data.printer; return; }
    const f = data.flags || {};
    const problems = ["paper_out", "head_open", "paused", "ribbon_out"].filter((k) => f[k]);
    if (problems.length) { dot.className = "dot"; text.textContent = problems.join(", "); }
    else { dot.className = "dot ok"; text.textContent = "ready · " + data.printer; }
  } catch (e) { dot.className = "dot err"; text.textContent = "status error"; }
}

// ---------- init ----------
async function loadProfiles() {
  try {
    const profiles = await (await fetch("/api/profiles")).json();
    $("profile").innerHTML = profiles
      .map((p) => `<option value="${p.name}">${p.name} — ${p.description || p.page_type}</option>`)
      .join("");
  } catch (_) {}
}

function wireDrop() {
  const drop = $("drop"), file = $("file");
  file.addEventListener("change", () => file.files[0] && upload(file.files[0]));
  ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("hot"); }));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("hot"); }));
  drop.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) upload(f); });
}

// Click the 4x6 preview to toggle actual-size (100%, true pixels) inspection.
$("outImg").addEventListener("click", () => $("outImg").parentElement.classList.toggle("zoom"));
$("pagePrev").addEventListener("click", () => gotoPage(-1));
$("pageNext").addEventListener("click", () => gotoPage(1));

wireDrop(); wireControls(); wireCropBox(); wireHistory(); loadProfiles();
loadHistory();
refreshStatus();
$("statusPill").addEventListener("click", refreshStatus);
setInterval(refreshStatus, 30000);
