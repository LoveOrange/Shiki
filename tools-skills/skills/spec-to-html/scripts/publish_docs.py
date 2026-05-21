#!/usr/bin/env python3
"""Publish Markdown files as an offline static HTML documentation site."""

import argparse
import html
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "out",
    "target",
    "tmp",
    "web_spec",
}

ASSET_FILES = [
    "highlight.min.js",
    "highlight-theme.css",
    "mermaid.min.js",
]

SITE_CSS = """
:root {
  --bg: #eef2f6;
  --panel: #ffffff;
  --panel-muted: #f8fafc;
  --text: #172033;
  --muted: #647085;
  --subtle: #94a3b8;
  --line: #d8dee8;
  --line-soft: #edf0f5;
  --accent: #0f766e;
  --accent-strong: #0b4f49;
  --accent-soft: #e7f4f2;
  --accent-line: #9fd6ce;
  --mark: #8a4b16;
  --code: #111827;
  --code-line: #263244;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 15px/1.68 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.layout {
  display: grid;
  grid-template-columns: minmax(280px, 330px) minmax(0, 1fr) minmax(210px, 260px);
  min-height: 100vh;
}
.view-controls {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 40;
  display: flex;
  gap: 6px;
  align-items: center;
  border: 1px solid rgb(15 23 42 / 12%);
  border-radius: 7px;
  background: rgb(255 255 255 / 90%);
  box-shadow: 0 8px 22px rgb(15 23 42 / 12%);
  padding: 5px;
  backdrop-filter: blur(10px);
}
.view-controls button {
  border: 1px solid transparent;
  border-radius: 5px;
  background: transparent;
  color: #344054;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  padding: 7px 9px;
}
.view-controls button:hover {
  background: #eef3f6;
}
.view-controls button.active {
  border-color: var(--accent-line);
  background: var(--accent-soft);
  color: var(--accent-strong);
}
.view-controls button:focus-visible {
  outline: 2px solid var(--accent-line);
  outline-offset: 2px;
}
body.nav-collapsed:not(.toc-collapsed):not(.focus-mode) .layout {
  grid-template-columns: minmax(0, 1fr) minmax(210px, 260px);
}
body.toc-collapsed:not(.nav-collapsed):not(.focus-mode) .layout {
  grid-template-columns: minmax(280px, 330px) minmax(0, 1fr);
}
body.nav-collapsed.toc-collapsed .layout,
body.focus-mode .layout {
  grid-template-columns: minmax(0, 1fr);
}
body.nav-collapsed .sidebar,
body.focus-mode .sidebar {
  display: none;
}
body.toc-collapsed .toc-panel,
body.focus-mode .toc-panel {
  display: none;
}
body.focus-mode article {
  width: min(100%, 1080px);
}
body.focus-mode .source {
  width: min(100%, 1080px);
}
.sidebar {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  overflow: auto;
  border-right: 1px solid var(--line);
  background: linear-gradient(180deg, #ffffff 0%, #f7fafc 100%);
  padding: 24px 14px 28px;
}
.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  margin: 0 8px 8px;
  font-size: 18px;
  line-height: 1.25;
  font-weight: 700;
}
.brand::before {
  content: "";
  width: 10px;
  height: 28px;
  border-radius: 4px;
  background: linear-gradient(180deg, var(--accent), var(--mark));
  flex: 0 0 auto;
}
.generated {
  margin: 0 8px 18px;
  color: var(--muted);
  font-size: 12px;
}
.nav-tree {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-group {
  margin-top: 2px;
}
.nav-group summary {
  display: flex;
  gap: 8px;
  align-items: baseline;
  justify-content: space-between;
  cursor: pointer;
  list-style: none;
  border-radius: 6px;
  color: #263445;
  font-size: 13px;
  font-weight: 720;
  padding: 8px 9px;
  overflow-wrap: anywhere;
}
.nav-group summary::-webkit-details-marker {
  display: none;
}
.nav-group summary:hover {
  background: #eef3f6;
}
.nav-group summary::before {
  content: "+";
  color: var(--subtle);
  flex: 0 0 auto;
  font-weight: 700;
}
.nav-group[open] > summary::before {
  content: "-";
}
.nav-folder-name {
  flex: 1 1 auto;
  min-width: 0;
}
.nav-count {
  color: var(--subtle);
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 600;
}
.nav-group-pages {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-left: 14px;
  padding: 2px 0 7px 9px;
  border-left: 1px solid var(--line-soft);
}
.nav-root-pages {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: block;
  padding: 7px 9px;
  border-radius: 6px;
  color: var(--text);
}
.nav-item:hover {
  background: #eef3f6;
  text-decoration: none;
}
.nav-item.active {
  background: var(--accent-soft);
  box-shadow: inset 3px 0 0 var(--accent);
  color: var(--accent-strong);
}
.nav-item span {
  display: block;
  overflow-wrap: anywhere;
  font-size: 13px;
  font-weight: 650;
  line-height: 1.25;
}
.nav-item small {
  display: block;
  color: var(--subtle);
  overflow-wrap: anywhere;
  font-size: 11px;
  line-height: 1.25;
  margin-top: 2px;
}
.content {
  min-width: 0;
  padding: 34px 44px 72px;
}
.landing-main {
  width: min(100%, 1120px);
  margin: 0 auto;
  padding: 46px 34px 72px;
}
.source {
  width: min(100%, 940px);
  margin: 0 auto 14px;
  color: var(--muted);
  font-size: 12px;
}
.source code {
  background: #fff;
  border: 1px solid var(--line-soft);
}
article {
  width: min(100%, 940px);
  margin: 0 auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 40px 46px;
  box-shadow: 0 16px 38px rgb(15 23 42 / 7%);
}
h1, h2, h3, h4, h5, h6 {
  margin: 1.35em 0 .55em;
  line-height: 1.25;
}
h1 {
  margin-top: 0;
  margin-bottom: .75em;
  padding-bottom: .45em;
  border-bottom: 1px solid var(--line-soft);
  font-size: 34px;
  letter-spacing: 0;
}
h2 { border-top: 1px solid var(--line-soft); padding-top: 24px; font-size: 23px; letter-spacing: 0; }
h3 { font-size: 19px; letter-spacing: 0; }
h4 { font-size: 16px; letter-spacing: 0; }
p { margin: 0 0 1em; }
ul, ol { padding-left: 1.45rem; }
li + li { margin-top: .25em; }
.anchor {
  float: left;
  margin-left: -22px;
  opacity: 0;
  color: var(--muted);
}
h1:hover .anchor, h2:hover .anchor, h3:hover .anchor, h4:hover .anchor {
  opacity: 1;
}
table {
  display: block;
  width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
  margin: 18px 0;
  font-size: 14px;
}
th, td {
  border: 1px solid var(--line);
  padding: 8px 10px;
  vertical-align: top;
}
th { background: #f1f4f8; text-align: left; }
pre {
  position: relative;
  overflow-x: auto;
  background: var(--code);
  color: #f5f7fb;
  border-radius: 6px;
  padding: 14px 16px;
  border: 1px solid var(--code-line);
}
code {
  background: #edf0f3;
  border-radius: 4px;
  padding: 1px 5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .92em;
}
pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}
.code-copy {
  position: absolute;
  top: 8px;
  right: 8px;
  border: 1px solid rgb(255 255 255 / 18%);
  border-radius: 5px;
  background: rgb(255 255 255 / 10%);
  color: #e5e7eb;
  cursor: pointer;
  font-size: 12px;
  opacity: 0;
  padding: 3px 8px;
}
pre:hover .code-copy,
.code-copy:focus {
  opacity: 1;
}
blockquote {
  margin: 18px 0;
  padding: 10px 16px;
  border-left: 4px solid var(--accent);
  background: #f4f7f7;
  color: #384046;
}
img { max-width: 100%; }
.diagram {
  position: relative;
  margin: 22px 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #ffffff;
  overflow: hidden;
}
.diagram-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  padding: 8px;
  border-bottom: 1px solid var(--line);
  background: var(--panel-muted);
}
.diagram-toolbar button {
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff;
  color: var(--text);
  padding: 4px 8px;
  cursor: pointer;
}
.diagram-toolbar button:hover {
  background: var(--accent-soft);
}
.diagram-canvas {
  overflow: auto;
  padding: 16px;
  transform-origin: top left;
  cursor: zoom-in;
}
.diagram-canvas svg {
  display: block;
  height: auto;
  margin: 0 auto;
  max-width: 100%;
}
.diagram-source {
  border-top: 1px solid var(--line);
  padding: 8px 12px;
}
.diagram-source summary {
  cursor: pointer;
  color: var(--muted);
}
.diagram-source pre {
  margin: 10px 0 0;
}
.landing-list {
  display: grid;
  gap: 4px;
  margin-top: 12px;
}
.landing-section {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: 0 10px 26px rgb(15 23 42 / 5%);
  margin: 12px 0;
  padding: 18px;
}
.landing-section h2 {
  border-top: 0;
  padding-top: 0;
  margin: 0 0 10px;
  font-size: 18px;
}
.landing-section small {
  color: var(--subtle);
  font-size: 12px;
  font-weight: 500;
  margin-left: 8px;
}
.toc-panel {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  overflow: auto;
  border-left: 1px solid var(--line);
  background: #fbfcfd;
  padding: 28px 18px;
}
.toc-title {
  color: #344054;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .04em;
  margin-bottom: 10px;
  text-transform: uppercase;
}
.toc-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.toc-item {
  border-left: 2px solid transparent;
  color: var(--muted);
  display: block;
  font-size: 12px;
  line-height: 1.3;
  padding: 5px 0 5px 9px;
  overflow-wrap: anywhere;
}
.toc-item:hover {
  border-left-color: var(--accent);
  color: var(--accent-strong);
  text-decoration: none;
}
.toc-item.active {
  border-left-color: var(--accent);
  color: var(--accent-strong);
  font-weight: 700;
}
.toc-level-1 { font-weight: 700; }
.toc-level-2 { margin-left: 8px; }
.toc-level-3 { margin-left: 10px; }
.toc-level-4 { margin-left: 18px; }
.toc-empty {
  color: var(--subtle);
  font-size: 12px;
}
body.diagram-viewer-open {
  overflow: hidden;
}
.diagram-viewer {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: grid;
  grid-template-rows: auto 1fr;
  background: rgb(15 23 42 / 92%);
  color: #f8fafc;
}
.diagram-viewer[hidden] {
  display: none;
}
.diagram-viewer-toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  border-bottom: 1px solid rgb(255 255 255 / 14%);
  background: rgb(15 23 42 / 94%);
  padding: 10px 12px;
}
.diagram-viewer-title {
  color: #e2e8f0;
  font-size: 13px;
  font-weight: 700;
  margin-right: auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.diagram-viewer-toolbar button {
  border: 1px solid rgb(255 255 255 / 20%);
  border-radius: 5px;
  background: rgb(255 255 255 / 8%);
  color: #f8fafc;
  cursor: pointer;
  padding: 5px 9px;
}
.diagram-viewer-toolbar button:hover {
  background: rgb(255 255 255 / 16%);
}
.diagram-viewer-stage {
  position: relative;
  overflow: hidden;
  cursor: grab;
  outline: none;
  touch-action: none;
}
.diagram-viewer-stage.dragging {
  cursor: grabbing;
}
.diagram-viewer-content {
  position: absolute;
  left: 0;
  top: 0;
  transform-origin: 0 0;
  will-change: transform;
}
.diagram-viewer-content svg {
  display: block;
  max-width: none;
  width: auto;
  height: auto;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 18px 48px rgb(0 0 0 / 35%);
}
.diagram-viewer-status {
  position: absolute;
  left: 14px;
  bottom: 12px;
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 999px;
  background: rgb(15 23 42 / 72%);
  color: #cbd5e1;
  font-size: 12px;
  padding: 5px 10px;
  pointer-events: none;
}
.diagram-viewer-message {
  min-width: 280px;
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 8px;
  background: rgb(15 23 42 / 82%);
  color: #e2e8f0;
  padding: 18px;
}
@media (max-width: 1100px) {
  .layout {
    grid-template-columns: minmax(260px, 310px) minmax(0, 1fr);
  }
  .toc-panel {
    display: none;
  }
}
@media (max-width: 820px) {
  .layout { display: block; }
  .view-controls {
    left: 12px;
    right: 12px;
    justify-content: flex-end;
  }
  .sidebar {
    position: static;
    height: auto;
    max-height: 42vh;
  }
  .content { padding: 58px 16px 48px; }
  article { padding: 24px 18px; }
  h1 { font-size: 28px; }
  .anchor { display: none; }
}
"""

SITE_JS = """
(function () {
  if (window.hljs) {
    window.hljs.highlightAll();
  }
  if (window.mermaid) {
    window.mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function copyText(value, callback) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(value).then(function () {
        if (callback) callback();
      });
      return;
    }

    var textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    if (callback) callback();
  }

  function readLayoutState() {
    try {
      var raw = window.localStorage.getItem("specToHtmlLayout");
      if (raw) return JSON.parse(raw);
    } catch (error) {}
    return { nav: false, toc: false, focus: false };
  }

  function writeLayoutState(state) {
    try {
      window.localStorage.setItem("specToHtmlLayout", JSON.stringify(state));
    } catch (error) {}
  }

  function setupLayoutControls() {
    var controls = document.querySelector(".view-controls");
    if (!controls) return;
    var state = readLayoutState();

    function applyState(persist) {
      var hideNav = Boolean(state.focus || state.nav);
      var hideToc = Boolean(state.focus || state.toc);
      document.body.classList.toggle("nav-collapsed", hideNav);
      document.body.classList.toggle("toc-collapsed", hideToc);
      document.body.classList.toggle("focus-mode", Boolean(state.focus));

      controls.querySelectorAll("[data-layout-action]").forEach(function (button) {
        var action = button.getAttribute("data-layout-action");
        var active = (action === "nav" && hideNav) || (action === "toc" && hideToc) || (action === "focus" && state.focus);
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
      });

      if (persist) writeLayoutState(state);
    }

    controls.querySelectorAll("[data-layout-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.getAttribute("data-layout-action");
        if (action === "nav") {
          if (state.focus) {
            state.focus = false;
            state.nav = false;
          } else {
            state.nav = !state.nav;
          }
        }
        if (action === "toc") {
          if (state.focus) {
            state.focus = false;
            state.toc = false;
          } else {
            state.toc = !state.toc;
          }
        }
        if (action === "focus") {
          state.focus = !state.focus;
        }
        applyState(true);
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.target && /input|textarea|select/i.test(event.target.tagName || "")) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (event.key === "[") {
        state.nav = !state.nav;
        state.focus = false;
        applyState(true);
      }
      if (event.key === "]") {
        state.toc = !state.toc;
        state.focus = false;
        applyState(true);
      }
      if (event.key && event.key.toLowerCase() === "f") {
        state.focus = !state.focus;
        applyState(true);
      }
    });

    applyState(false);
  }

  setupLayoutControls();

  function parseSvgLength(value) {
    var match = String(value || "").match(/^[0-9.]+/);
    return match ? parseFloat(match[0]) : 0;
  }

  function normalizeMermaidSvg(container, mode) {
    var svg = container.querySelector("svg");
    if (!svg) return null;
    mode = mode || "actual";

    var width = 0;
    var height = 0;
    var viewBox = svg.getAttribute("viewBox");
    if (viewBox) {
      var parts = viewBox.trim().split(/[,\s]+/).map(Number);
      if (parts.length >= 4 && parts[2] > 0 && parts[3] > 0) {
        width = parts[2];
        height = parts[3];
      }
    }

    if (!width || !height) {
      width = parseSvgLength(svg.getAttribute("width"));
      height = parseSvgLength(svg.getAttribute("height"));
    }

    if ((!width || !height) && typeof svg.getBBox === "function") {
      try {
        var box = svg.getBBox();
        width = box.width;
        height = box.height;
        if (!viewBox && width > 0 && height > 0) {
          svg.setAttribute("viewBox", [box.x, box.y, width, height].join(" "));
        }
      } catch (error) {}
    }

    width = Math.max(1, Math.ceil(width || 960));
    height = Math.max(1, Math.ceil(height || 540));
    svg.setAttribute("width", String(width));
    svg.setAttribute("height", String(height));
    if (mode === "inline") {
      svg.style.width = "100%";
      svg.style.height = "auto";
      svg.style.maxWidth = width + "px";
    } else {
      svg.style.width = width + "px";
      svg.style.height = height + "px";
      svg.style.maxWidth = "none";
    }
    container.dataset.diagramWidth = String(width);
    container.dataset.diagramHeight = String(height);
    return { width: width, height: height };
  }

  function renderMermaid(container, renderId, source, mode) {
    if (!window.mermaid || !source.trim()) {
      container.innerHTML = "<pre><code></code></pre>";
      container.querySelector("code").textContent = source;
      return Promise.resolve();
    }
    return window.mermaid.render(renderId, source).then(function (result) {
      container.innerHTML = result.svg;
      normalizeMermaidSvg(container, mode);
    }).catch(function (error) {
      container.innerHTML = "<pre><code></code></pre>";
      container.querySelector("code").textContent = String(error);
    });
  }

  function createDiagramViewer() {
    var viewer = document.createElement("div");
    viewer.className = "diagram-viewer";
    viewer.hidden = true;
    viewer.setAttribute("role", "dialog");
    viewer.setAttribute("aria-modal", "true");
    viewer.innerHTML =
      '<div class="diagram-viewer-toolbar">' +
        '<div class="diagram-viewer-title">Mermaid preview</div>' +
        '<button type="button" data-viewer-action="zoom-out">Zoom out</button>' +
        '<button type="button" data-viewer-action="zoom-in">Zoom in</button>' +
        '<button type="button" data-viewer-action="fit">Fit</button>' +
        '<button type="button" data-viewer-action="actual-size">100%</button>' +
        '<button type="button" data-viewer-action="copy">Copy source</button>' +
        '<button type="button" data-viewer-action="close">Close</button>' +
      '</div>' +
      '<div class="diagram-viewer-stage" tabindex="0">' +
        '<div class="diagram-viewer-content"></div>' +
        '<div class="diagram-viewer-status">Scroll or pinch to zoom · drag to pan · double-click to fit</div>' +
      '</div>';
    document.body.appendChild(viewer);

    var title = viewer.querySelector(".diagram-viewer-title");
    var stage = viewer.querySelector(".diagram-viewer-stage");
    var content = viewer.querySelector(".diagram-viewer-content");
    var status = viewer.querySelector(".diagram-viewer-status");
    var state = {
      source: "",
      scale: 1,
      x: 0,
      y: 0,
      dragging: false,
      pointerId: null,
      dragX: 0,
      dragY: 0,
      baseX: 0,
      baseY: 0
    };

    function applyTransform() {
      content.style.transform = "translate(" + state.x + "px, " + state.y + "px) scale(" + state.scale + ")";
      status.textContent = Math.round(state.scale * 100) + "% · scroll or pinch to zoom · drag to pan · double-click to fit";
    }

    function contentSize() {
      var savedWidth = parseFloat(content.dataset.diagramWidth);
      var savedHeight = parseFloat(content.dataset.diagramHeight);
      if (savedWidth > 0 && savedHeight > 0) {
        return { width: savedWidth, height: savedHeight };
      }
      var normalized = normalizeMermaidSvg(content, "actual");
      if (normalized) {
        return normalized;
      }
      var rect = content.getBoundingClientRect();
      return {
        width: Math.max(1, rect.width / state.scale),
        height: Math.max(1, rect.height / state.scale)
      };
    }

    function fit() {
      var rect = stage.getBoundingClientRect();
      var size = contentSize();
      var availableWidth = Math.max(120, rect.width - 80);
      var availableHeight = Math.max(120, rect.height - 80);
      var nextScale = Math.min(availableWidth / size.width, availableHeight / size.height);
      if (!Number.isFinite(nextScale) || nextScale <= 0) {
        nextScale = 1;
      }
      state.scale = clamp(nextScale, 0.12, 2.5);
      state.x = (rect.width - size.width * state.scale) / 2;
      state.y = (rect.height - size.height * state.scale) / 2;
      applyTransform();
    }

    function zoomAt(clientX, clientY, factor) {
      var rect = stage.getBoundingClientRect();
      var pointerX = clientX - rect.left;
      var pointerY = clientY - rect.top;
      var contentX = (pointerX - state.x) / state.scale;
      var contentY = (pointerY - state.y) / state.scale;
      state.scale = clamp(state.scale * factor, 0.12, 8);
      state.x = pointerX - contentX * state.scale;
      state.y = pointerY - contentY * state.scale;
      applyTransform();
    }

    function close() {
      viewer.hidden = true;
      document.body.classList.remove("diagram-viewer-open");
      content.innerHTML = "";
      state.dragging = false;
    }

    function open(source, label) {
      state.source = source;
      title.textContent = label || "Mermaid preview";
      viewer.hidden = false;
      document.body.classList.add("diagram-viewer-open");
      content.innerHTML = '<div class="diagram-viewer-message">Rendering diagram...</div>';
      try {
        stage.focus({ preventScroll: true });
      } catch (error) {
        stage.focus();
      }
      renderMermaid(content, "diagram-viewer-" + Date.now(), source, "actual").then(function () {
        window.requestAnimationFrame(function () {
          normalizeMermaidSvg(content, "actual");
          fit();
        });
      });
    }

    stage.addEventListener("wheel", function (event) {
      event.preventDefault();
      var factor = Math.exp(-event.deltaY * 0.0015);
      zoomAt(event.clientX, event.clientY, factor);
    }, { passive: false });

    stage.addEventListener("pointerdown", function (event) {
      if (event.button !== 0 && event.pointerType !== "touch") return;
      state.dragging = true;
      state.pointerId = event.pointerId;
      state.dragX = event.clientX;
      state.dragY = event.clientY;
      state.baseX = state.x;
      state.baseY = state.y;
      stage.classList.add("dragging");
      stage.setPointerCapture(event.pointerId);
    });

    stage.addEventListener("pointermove", function (event) {
      if (!state.dragging || event.pointerId !== state.pointerId) return;
      state.x = state.baseX + event.clientX - state.dragX;
      state.y = state.baseY + event.clientY - state.dragY;
      applyTransform();
    });

    function stopDrag(event) {
      if (state.pointerId === event.pointerId) {
        state.dragging = false;
        state.pointerId = null;
        stage.classList.remove("dragging");
      }
    }
    stage.addEventListener("pointerup", stopDrag);
    stage.addEventListener("pointercancel", stopDrag);
    stage.addEventListener("dblclick", fit);

    viewer.querySelectorAll("[data-viewer-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.getAttribute("data-viewer-action");
        var rect = stage.getBoundingClientRect();
        var centerX = rect.left + rect.width / 2;
        var centerY = rect.top + rect.height / 2;
        if (action === "zoom-in") zoomAt(centerX, centerY, 1.25);
        if (action === "zoom-out") zoomAt(centerX, centerY, 0.8);
        if (action === "fit") fit();
        if (action === "actual-size") {
          state.scale = 1;
          state.x = 40;
          state.y = 40;
          applyTransform();
        }
        if (action === "copy") copyText(state.source);
        if (action === "close") close();
      });
    });

    document.addEventListener("keydown", function (event) {
      if (viewer.hidden) return;
      if (event.key === "Escape") close();
      if (event.key === "0") fit();
    });

    return { open: open, close: close };
  }

  var diagramViewer = createDiagramViewer();

  document.querySelectorAll("article pre").forEach(function (pre) {
    if (pre.closest(".diagram")) return;
    var code = pre.querySelector("code");
    if (!code) return;
    var button = document.createElement("button");
    button.type = "button";
    button.className = "code-copy";
    button.textContent = "Copy";
    button.addEventListener("click", function () {
      copyText(code.textContent || "", function () {
        button.textContent = "Copied";
        window.setTimeout(function () {
          button.textContent = "Copy";
        }, 1200);
      });
    });
    pre.appendChild(button);
  });

  document.querySelectorAll(".diagram").forEach(function (diagram, index) {
    var source = diagram.getAttribute("data-diagram-source") || "";
    var canvas = diagram.querySelector(".diagram-canvas");
    var scale = 1;

    function applyScale() {
      canvas.style.transform = "scale(" + scale + ")";
      canvas.style.width = (100 / scale) + "%";
    }

    function openViewer() {
      diagramViewer.open(source, "Mermaid diagram");
    }

    canvas.setAttribute("role", "button");
    canvas.setAttribute("tabindex", "0");
    canvas.setAttribute("title", "Open full screen Mermaid preview");
    canvas.addEventListener("click", function (event) {
      if (event.target.closest("a, button, summary, details")) return;
      openViewer();
    });
    canvas.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openViewer();
      }
    });

    diagram.querySelectorAll("[data-diagram-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.getAttribute("data-diagram-action");
        if (action === "zoom-in") scale = Math.min(3, scale + 0.15);
        if (action === "zoom-out") scale = Math.max(0.4, scale - 0.15);
        if (action === "reset") scale = 1;
        if (action === "copy") copyText(source);
        if (action === "open") openViewer();
        applyScale();
      });
    });

    renderMermaid(canvas, "diagram-" + index, source, "inline");
  });

  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".toc-item"));
  var tocTargets = tocLinks.map(function (link) {
    var href = link.getAttribute("href") || "";
    var id = href.charAt(0) === "#" ? href.slice(1) : "";
    try {
      id = decodeURIComponent(id);
    } catch (error) {}
    return { link: link, target: document.getElementById(id) };
  }).filter(function (item) {
    return item.target;
  });

  function activateToc(id) {
    tocTargets.forEach(function (item) {
      item.link.classList.toggle("active", item.target.id === id);
    });
  }

  if (tocTargets.length && "IntersectionObserver" in window) {
    activateToc(tocTargets[0].target.id);
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) activateToc(entry.target.id);
      });
    }, { rootMargin: "-12% 0px -72% 0px", threshold: 0 });
    tocTargets.forEach(function (item) {
      observer.observe(item.target);
    });
  }
})();
"""


@dataclass
class RenderContext:
    title: str
    base_dir: Path
    output_dir: Path
    generated_at: str
    source_to_html: dict[Path, Path]
    source_root: Path
    broken_links: list[tuple[Path, str]] = field(default_factory=list)
    anchors: dict[Path, set[str]] = field(default_factory=dict)
    toc: dict[Path, list[tuple[int, str, str]]] = field(default_factory=dict)


def find_project_root() -> Path:
    """Use the current working directory as the generic publishing root."""
    return Path.cwd().resolve()


def resolve_input(raw: str, project_root: Path) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    project_path = project_root / path
    if project_path.exists():
        return project_path.resolve()
    return (Path.cwd() / path).resolve()


def collect_markdown(inputs: list[Path], output_dir: Path) -> list[Path]:
    files: list[Path] = []
    output_dir = output_dir.resolve()
    for input_path in inputs:
        if input_path.is_file():
            if input_path.suffix.lower() == ".md":
                files.append(input_path.resolve())
            continue
        if not input_path.is_dir():
            raise FileNotFoundError(f"Input path does not exist: {input_path}")
        input_root = input_path.resolve()
        for path in sorted(input_root.rglob("*.md")):
            resolved = path.resolve()
            if output_dir in resolved.parents or resolved == output_dir:
                continue
            relative_parts = resolved.relative_to(input_root).parts
            if any(part in SKIP_DIRS for part in relative_parts):
                continue
            files.append(resolved)
    return sorted(set(files))


def common_base(inputs: list[Path]) -> Path:
    bases = [path if path.is_dir() else path.parent for path in inputs]
    return Path(os.path.commonpath([str(path.resolve()) for path in bases]))


def web_spec_dir(root: Path) -> Path:
    if root.name == "web_spec":
        return root
    return root / "web_spec"


def target_path(source: Path, base_dir: Path, output_dir: Path) -> Path:
    relative = source.relative_to(base_dir).with_suffix(".html")
    if relative == Path("index.html"):
        relative = Path("index.page.html")
    return output_dir / relative


def is_external_link(target: str) -> bool:
    parsed = urlsplit(target)
    return bool(parsed.scheme or parsed.netloc) or target.startswith(("mailto:", "tel:"))


def split_link_target(target: str) -> tuple[str, str]:
    if "#" not in target:
        return target, ""
    path_part, anchor = target.split("#", 1)
    return path_part, "#" + anchor


def rewrite_link(target: str, source: Path, ctx: RenderContext) -> str:
    target = target.strip()
    if not target or target.startswith("#") or is_external_link(target):
        return target

    path_part, anchor = split_link_target(target)
    if not path_part:
        return target

    if path_part.lower().endswith(".md"):
        linked_source = (source.parent / path_part).resolve()
        linked_html = ctx.source_to_html.get(linked_source)
        if linked_html is None:
            ctx.broken_links.append((source, target))
            return target
        current_html_dir = ctx.source_to_html[source].parent
        relative = os.path.relpath(linked_html, current_html_dir)
        return relative.replace(os.sep, "/") + anchor

    return target


def slugify(text: str, used: set[str]) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.lower()).strip("-")
    if not slug:
        slug = "section"
    base = slug
    index = 2
    while slug in used:
        slug = f"{base}-{index}"
        index += 1
    used.add(slug)
    return slug


def render_inline_text(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def render_inline(text: str, source: Path, ctx: RenderContext) -> str:
    tokens: list[str] = []

    def token(value: str) -> str:
        tokens.append(value)
        return f"@@SPEC_TO_HTML_TOKEN_{len(tokens) - 1}@@"

    def code_repl(match: re.Match[str]) -> str:
        return token(f"<code>{html.escape(match.group(1))}</code>")

    def image_repl(match: re.Match[str]) -> str:
        alt = html.escape(match.group(1), quote=True)
        src = html.escape(rewrite_link(match.group(2), source, ctx), quote=True)
        return token(f'<img src="{src}" alt="{alt}">')

    def link_repl(match: re.Match[str]) -> str:
        label = render_inline_text(match.group(1))
        href = html.escape(rewrite_link(match.group(2), source, ctx), quote=True)
        return token(f'<a href="{href}">{label}</a>')

    text = re.sub(r"`([^`]+)`", code_repl, text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", image_repl, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    rendered = render_inline_text(text)
    for index, value in enumerate(tokens):
        rendered = rendered.replace(f"@@SPEC_TO_HTML_TOKEN_{index}@@", value)
    return rendered


def is_table_separator(line: str) -> bool:
    if not line.strip().startswith("|"):
        return False
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_table(lines: list[str], source: Path, ctx: RenderContext) -> str:
    headers = split_table_row(lines[0])
    rows = [split_table_row(line) for line in lines[2:]]
    output = ["<table>", "<thead><tr>"]
    for header in headers:
        output.append(f"<th>{render_inline(header, source, ctx)}</th>")
    output.append("</tr></thead>")
    output.append("<tbody>")
    for row in rows:
        output.append("<tr>")
        padded = row + [""] * max(0, len(headers) - len(row))
        for cell in padded[: len(headers)]:
            output.append(f"<td>{render_inline(cell, source, ctx)}</td>")
        output.append("</tr>")
    output.append("</tbody></table>")
    return "".join(output)


def consume_paragraph(lines: list[str], start: int) -> tuple[str, int]:
    paragraph: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            break
        if re.match(r"^#{1,6}\s+", stripped):
            break
        if stripped.startswith("```"):
            break
        if stripped.startswith(">"):
            break
        if re.match(r"^([-*])\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            break
        if stripped.startswith("|") and index + 1 < len(lines) and is_table_separator(lines[index + 1]):
            break
        if re.fullmatch(r"[-*_]{3,}", stripped):
            break
        paragraph.append(stripped)
        index += 1
    return " ".join(paragraph), index


def render_markdown(text: str, source: Path, ctx: RenderContext) -> str:
    lines = text.splitlines()
    used_anchors: set[str] = set()
    toc_entries: list[tuple[int, str, str]] = []
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        fence = re.match(r"^```([\w.+-]*)\s*$", stripped)
        if fence:
            language = fence.group(1).lower()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            index += 1
            code_text = "\n".join(code_lines)
            if language == "mermaid":
                escaped_source = html.escape(code_text)
                escaped_attr = html.escape(code_text, quote=True)
                output.append(
                    '<figure class="diagram" data-diagram-source="'
                    + escaped_attr
                    + '">'
                    + '<figcaption class="diagram-toolbar">'
                    + '<button type="button" data-diagram-action="zoom-in">Zoom in</button>'
                    + '<button type="button" data-diagram-action="zoom-out">Zoom out</button>'
                    + '<button type="button" data-diagram-action="reset">Reset</button>'
                    + '<button type="button" data-diagram-action="open">Full screen</button>'
                    + '<button type="button" data-diagram-action="copy">Copy source</button>'
                    + '</figcaption>'
                    + f'<div class="diagram-canvas"><pre><code>{escaped_source}</code></pre></div>'
                    + '<details class="diagram-source"><summary>Mermaid source</summary>'
                    + f'<pre><code class="language-mermaid">{escaped_source}</code></pre>'
                    + '</details></figure>'
                )
            else:
                class_name = f' class="language-{html.escape(language, quote=True)}"' if language else ""
                output.append(f"<pre><code{class_name}>{html.escape(code_text)}</code></pre>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            raw_label = heading.group(2).strip()
            label = render_inline(raw_label, source, ctx)
            anchor = slugify(raw_label, used_anchors)
            toc_label = re.sub(r"`", "", re.sub(r"<[^>]+>", "", raw_label)).strip()
            toc_entries.append((level, toc_label, anchor))
            output.append(f'<h{level} id="{anchor}"><a class="anchor" href="#{anchor}">#</a>{label}</h{level}>')
            index += 1
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and is_table_separator(lines[index + 1]):
            table_lines = [lines[index], lines[index + 1]]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            output.append(render_table(table_lines, source, ctx))
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip().lstrip(">").strip())
                index += 1
            output.append(f"<blockquote>{render_inline(' '.join(quote_lines), source, ctx)}</blockquote>")
            continue

        if re.match(r"^([-*])\s+", stripped):
            items: list[str] = []
            while index < len(lines) and re.match(r"^([-*])\s+", lines[index].strip()):
                items.append(re.sub(r"^([-*])\s+", "", lines[index].strip()))
                index += 1
            output.append("<ul>" + "".join(f"<li>{render_inline(item, source, ctx)}</li>" for item in items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while index < len(lines) and re.match(r"^\d+\.\s+", lines[index].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[index].strip()))
                index += 1
            output.append("<ol>" + "".join(f"<li>{render_inline(item, source, ctx)}</li>" for item in items) + "</ol>")
            continue

        if re.fullmatch(r"[-*_]{3,}", stripped):
            output.append("<hr>")
            index += 1
            continue

        paragraph, index = consume_paragraph(lines, index)
        if paragraph:
            output.append(f"<p>{render_inline(paragraph, source, ctx)}</p>")
        else:
            index += 1

    ctx.anchors[source] = used_anchors
    ctx.toc[source] = toc_entries
    return "\n".join(output)


def page_title(source: Path, markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return re.sub(r"`", "", match.group(1)).strip()
    return source.stem.replace("_", " ").replace("-", " ").title()


def directory_label(path: str) -> str:
    if path == ".":
        return "Overview"
    return path.replace("/", " / ")


@dataclass
class DirectoryNode:
    name: str
    path: str
    files: list[tuple[Path, Path, str]] = field(default_factory=list)
    children: dict[str, "DirectoryNode"] = field(default_factory=dict)


def directory_path(relative_parent: Path) -> str:
    value = relative_parent.as_posix()
    return "." if value in ("", ".") else value


def page_sort_key(page: tuple[Path, Path, str], ctx: RenderContext) -> tuple[int, str]:
    relative = page[0].relative_to(ctx.base_dir)
    name = relative.name.lower()
    rank = 0 if name in ("readme.md", "index.md") else 1
    return rank, relative.as_posix()


def build_directory_tree(pages: list[tuple[Path, Path, str]], ctx: RenderContext) -> DirectoryNode:
    root = DirectoryNode("Overview", ".")
    for source, html_path, title in pages:
        relative = source.relative_to(ctx.base_dir)
        node = root
        parts: list[str] = []
        for part in relative.parent.parts:
            if part == ".":
                continue
            parts.append(part)
            path = "/".join(parts)
            node = node.children.setdefault(part, DirectoryNode(part, path))
        node.files.append((source, html_path, title))
    return root


def page_count(node: DirectoryNode) -> int:
    return len(node.files) + sum(page_count(child) for child in node.children.values())


def current_directory(current: Path | None, ctx: RenderContext) -> str:
    if current is None:
        return "."
    return directory_path(current.relative_to(ctx.base_dir).parent)


def node_contains_path(node: DirectoryNode, directory: str) -> bool:
    if node.path == ".":
        return True
    return directory == node.path or directory.startswith(node.path + "/")


def render_nav_item(source: Path, html_path: Path, title: str, current: Path | None, from_path: Path, ctx: RenderContext) -> str:
    href = os.path.relpath(html_path, from_path.parent).replace(os.sep, "/")
    source_rel = source.relative_to(ctx.base_dir).as_posix()
    active = " active" if current == source else ""
    return (
        f'<a class="nav-item{active}" href="{html.escape(href, quote=True)}">'
        f"<span>{html.escape(title)}</span><small>{html.escape(source_rel)}</small></a>"
    )


def render_nav_node(node: DirectoryNode, current: Path | None, from_path: Path, ctx: RenderContext, depth: int = 0) -> str:
    current_dir = current_directory(current, ctx)
    open_attr = " open" if current is None or node_contains_path(node, current_dir) else ""
    label = "Overview" if node.path == "." else node.name
    output = [f'<details class="nav-group nav-depth-{depth}"{open_attr}>']
    output.append(
        "<summary>"
        f'<span class="nav-folder-name">{html.escape(label)}</span>'
        f'<span class="nav-count">{page_count(node)}</span>'
        "</summary>"
    )
    output.append('<div class="nav-group-pages">')
    for source, html_path, title in sorted(node.files, key=lambda item: page_sort_key(item, ctx)):
        output.append(render_nav_item(source, html_path, title, current, from_path, ctx))
    for child in sorted(node.children.values(), key=lambda item: item.name):
        output.append(render_nav_node(child, current, from_path, ctx, depth + 1))
    output.append("</div></details>")
    return "\n".join(output)


def render_nav(current: Path | None, from_path: Path, pages: list[tuple[Path, Path, str]], ctx: RenderContext) -> str:
    tree = build_directory_tree(pages, ctx)
    output = ['<nav class="nav-tree">']
    if tree.files:
        output.append('<div class="nav-root-pages">')
        for source, html_path, title in sorted(tree.files, key=lambda item: page_sort_key(item, ctx)):
            output.append(render_nav_item(source, html_path, title, current, from_path, ctx))
        output.append("</div>")
    for child in sorted(tree.children.values(), key=lambda item: item.name):
        output.append(render_nav_node(child, current, from_path, ctx))
    output.append("</nav>")
    return "\n".join(output)


def flatten_directory_nodes(node: DirectoryNode) -> list[DirectoryNode]:
    nodes = [node]
    for child in sorted(node.children.values(), key=lambda item: item.path):
        nodes.extend(flatten_directory_nodes(child))
    return nodes


def render_toc(source: Path, ctx: RenderContext) -> str:
    entries = [entry for entry in ctx.toc.get(source, []) if 1 <= entry[0] <= 4]
    if not entries:
        return '<div class="toc-empty">No sections</div>'

    links = ['<nav class="toc-list">']
    for level, label, anchor in entries:
        links.append(
            f'<a class="toc-item toc-level-{level}" href="#{html.escape(anchor, quote=True)}">'
            f"{html.escape(label)}</a>"
        )
    links.append("</nav>")
    return "\n".join(links)


def asset_href(from_path: Path, ctx: RenderContext, filename: str) -> str:
    asset_path = ctx.output_dir / "assets" / filename
    return os.path.relpath(asset_path, from_path.parent).replace(os.sep, "/")


def html_shell(page_title_text: str, source: Path, body: str, nav: str, toc: str, ctx: RenderContext) -> str:
    source_rel = source.relative_to(ctx.source_root).as_posix() if ctx.source_root in source.parents else str(source)
    html_path = ctx.source_to_html[source]
    site_css = asset_href(html_path, ctx, "site.css")
    highlight_css = asset_href(html_path, ctx, "highlight-theme.css")
    highlight_js = asset_href(html_path, ctx, "highlight.min.js")
    mermaid_js = asset_href(html_path, ctx, "mermaid.min.js")
    site_js = asset_href(html_path, ctx, "site.js")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(page_title_text)} - {html.escape(ctx.title)}</title>
  <link rel="stylesheet" href="{html.escape(highlight_css, quote=True)}">
  <link rel="stylesheet" href="{html.escape(site_css, quote=True)}">
</head>
<body>
  <div class="view-controls" aria-label="Reader layout controls">
    <button type="button" data-layout-action="nav" aria-pressed="false" title="Toggle navigation">Nav</button>
    <button type="button" data-layout-action="toc" aria-pressed="false" title="Toggle table of contents">TOC</button>
    <button type="button" data-layout-action="focus" aria-pressed="false" title="Focus reading mode">Focus</button>
  </div>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">{html.escape(ctx.title)}</div>
      <div class="generated">Generated {html.escape(ctx.generated_at)}</div>
      {nav}
    </aside>
    <main class="content">
      <div class="source">Source: <code>{html.escape(source_rel)}</code></div>
      <article>
{body}
      </article>
    </main>
    <aside class="toc-panel">
      <div class="toc-title">On This Page</div>
      {toc}
    </aside>
  </div>
  <script src="{html.escape(highlight_js, quote=True)}"></script>
  <script src="{html.escape(mermaid_js, quote=True)}"></script>
  <script src="{html.escape(site_js, quote=True)}"></script>
</body>
</html>
"""


def render_landing(pages: list[tuple[Path, Path, str]], ctx: RenderContext, landing_name: str) -> str:
    landing_dir = (ctx.output_dir / landing_name).parent
    sections: list[str] = []
    tree = build_directory_tree(pages, ctx)
    for node in flatten_directory_nodes(tree):
        if not node.files:
            continue
        sections.append('<section class="landing-section">')
        sections.append(
            f"<h2>{html.escape(directory_label(node.path))}"
            f"<small>{len(node.files)} page(s)</small></h2>"
        )
        sections.append('<div class="landing-list">')
        for source, html_path, title in sorted(node.files, key=lambda item: page_sort_key(item, ctx)):
            href = os.path.relpath(html_path, landing_dir).replace(os.sep, "/")
            rel = source.relative_to(ctx.base_dir).as_posix()
            sections.append(
                f'<a class="nav-item" href="{html.escape(href, quote=True)}">'
                f"<span>{html.escape(title)}</span><small>{html.escape(rel)}</small></a>"
            )
        sections.append("</div></section>")
    directory_sections = "\n".join(sections)
    body = (
        f"<h1>{html.escape(ctx.title)}</h1>\n"
        f"<p>This is a generated offline HTML view of the source Markdown. Edit the Markdown and publish again to update this site.</p>\n"
        f"{directory_sections}"
    )
    site_css = "assets/site.css"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(ctx.title)}</title>
  <link rel="stylesheet" href="{html.escape(site_css, quote=True)}">
</head>
<body><main class="landing-main">{body}</main></body>
</html>
"""


def write_report(ctx: RenderContext, page_count: int, landing_name: str) -> None:
    lines = [
        "# Publish Report",
        "",
        f"- **Generated At**: {ctx.generated_at}",
        f"- **Input Base**: `{ctx.base_dir}`",
        f"- **Output Dir**: `{ctx.output_dir}`",
        f"- **Pages**: {page_count}",
        f"- **Landing Page**: `{landing_name}`",
        "",
        "## Broken Markdown Links",
        "",
    ]
    if ctx.broken_links:
        for source, target in ctx.broken_links:
            lines.append(f"- `{source.relative_to(ctx.base_dir)}` -> `{target}`")
    else:
        lines.append("- None")
    lines.append("")
    (ctx.output_dir / "publish_report.md").write_text("\n".join(lines), encoding="utf-8")


def bundled_asset_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "assets"


def write_assets(ctx: RenderContext) -> None:
    output_assets = ctx.output_dir / "assets"
    output_assets.mkdir(parents=True, exist_ok=True)
    (output_assets / "site.css").write_text(SITE_CSS.strip() + "\n", encoding="utf-8")
    (output_assets / "site.js").write_text(SITE_JS.strip() + "\n", encoding="utf-8")

    source_assets = bundled_asset_dir()
    missing = []
    for filename in ASSET_FILES:
        source = source_assets / filename
        if not source.exists():
            missing.append(str(source))
            continue
        shutil.copy2(source, output_assets / filename)

    if missing:
        raise FileNotFoundError("Missing bundled offline assets:\n" + "\n".join(missing))


def prepare_output_dir(output_dir: Path) -> None:
    if output_dir.exists() and (output_dir / "publish_report.md").exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def publish(inputs: list[Path], output_dir: Path, title: str, fail_on_broken_links: bool) -> int:
    prepare_output_dir(output_dir)
    sources = collect_markdown(inputs, output_dir)
    if not sources:
        raise FileNotFoundError("No Markdown files found in input paths.")

    base_dir = common_base(inputs)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    source_to_html = {source: target_path(source, base_dir, output_dir) for source in sources}
    ctx = RenderContext(
        title=title,
        base_dir=base_dir,
        output_dir=output_dir,
        generated_at=generated_at,
        source_to_html=source_to_html,
        source_root=base_dir,
    )
    write_assets(ctx)

    rendered_pages: list[tuple[Path, Path, str, str]] = []
    for source in sources:
        text = source.read_text(encoding="utf-8")
        title_text = page_title(source, text)
        body = render_markdown(text, source, ctx)
        rendered_pages.append((source, source_to_html[source], title_text, body))

    page_index = [(source, html_path, title_text) for source, html_path, title_text, _ in rendered_pages]
    for source, html_path, title_text, body in rendered_pages:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        nav = render_nav(source, html_path, page_index, ctx)
        toc = render_toc(source, ctx)
        html_path.write_text(html_shell(title_text, source, body, nav, toc, ctx), encoding="utf-8")

    landing_name = "index.html"
    (output_dir / landing_name).write_text(render_landing(page_index, ctx, landing_name), encoding="utf-8")
    write_report(ctx, len(rendered_pages), landing_name)

    print(f"Published {len(rendered_pages)} page(s) to {output_dir}")
    print(f"Landing page: {output_dir / landing_name}")
    if ctx.broken_links:
        print(f"Broken Markdown links: {len(ctx.broken_links)}")
        if fail_on_broken_links:
            return 2
    else:
        print("Broken Markdown links: 0")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    project_root = find_project_root()
    parser = argparse.ArgumentParser(
        description="Publish Markdown files as an offline static HTML documentation site."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Markdown file or directory inputs. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output root directory. The site is written to <output>/web_spec unless output is already named web_spec.",
    )
    parser.add_argument(
        "--title",
        default="Web Spec",
        help="Documentation site title.",
    )
    parser.add_argument(
        "--fail-on-broken-links",
        action="store_true",
        help="Exit non-zero if local Markdown links point to missing files.",
    )
    args = parser.parse_args(argv)
    args.project_root = project_root
    args.resolved_inputs = [
        resolve_input(raw, project_root)
        for raw in (args.inputs or ["."])
    ]
    if args.output:
        output_root = Path(args.output).expanduser()
        output_root = output_root.resolve() if output_root.is_absolute() else (project_root / output_root).resolve()
    else:
        output_root = common_base(args.resolved_inputs)
    args.resolved_output = web_spec_dir(output_root)
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    return publish(
        inputs=args.resolved_inputs,
        output_dir=args.resolved_output,
        title=args.title,
        fail_on_broken_links=args.fail_on_broken_links,
    )


if __name__ == "__main__":
    raise SystemExit(main())
