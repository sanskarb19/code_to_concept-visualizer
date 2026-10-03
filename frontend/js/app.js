(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const el = {
    concept: $("#concept-select"),
    conceptContext: $("#concept-context"),
    geminiStatus: $("#gemini-status"),
    geminiLabel: $("#gemini-label"),
    run: $("#run-button"),
    previous: $("#previous-button"),
    next: $("#next-button"),
    play: $("#play-button"),
    pause: $("#pause-button"),
    reset: $("#reset-button"),
    explain: $("#explain-button"),
    speed: $("#speed-range"),
    counter: $("#step-counter"),
    traceSummary: $("#trace-summary"),
    traceCount: $("#trace-count"),
    traceList: $("#trace-list"),
    conceptFocus: $("#concept-focus"),
    conceptLensTitle: $("#concept-lens-title"),
    conceptLensMeta: $("#concept-lens-meta"),
    variables: $("#variables-content"),
    variableCount: $("#variable-count"),
    stack: $("#stack-content"),
    stackCount: $("#stack-count"),
    output: $("#output-content"),
    outputCaption: $("#output-caption"),
    explanation: $("#explanation-content"),
    toast: $("#toast"),
    fallback: $("#fallback-editor"),
    host: $("#monaco-host"),
    textarea: $("#code-input"),
    gutter: $("#fallback-gutter"),
    highlight: $("#fallback-highlight"),
    editorPosition: $("#editor-position"),
    editorEngine: $("#editor-engine"),
  };

  const state = {
    concept: "",
    concepts: [],
    events: [],
    execution: null,
    selectedStep: -1,
    playing: false,
    playTimer: null,
    busy: false,
    explaining: false,
    explanationText: "",
    explanationError: "",
    explainRequest: 0,
    currentLine: null,
    errorLine: null,
    toastTimer: null,
    conceptRequest: 0,
    editor: null,
    editorReady: false,
    editorDecorations: [],
    source: "",
  };

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

  async function api(path, options = {}) {
    const response = await fetch(path, {
      credentials: "same-origin",
      ...options,
      headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) },
    });
    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new Error(`The server returned an unreadable response (${response.status}).`);
    }
    if (!response.ok) {
      throw new Error(payload?.detail || payload?.error || `Request failed (${response.status}).`);
    }
    return payload;
  }

  function showToast(message, tone = "error") {
    window.clearTimeout(state.toastTimer);
    el.toast.textContent = message;
    el.toast.dataset.tone = tone;
    el.toast.classList.add("visible");
    state.toastTimer = window.setTimeout(() => el.toast.classList.remove("visible"), 4400);
  }

  function setGeminiStatus(available, status) {
    el.geminiStatus.dataset.state = available ? "online" : "offline";
    el.geminiLabel.textContent = available ? "Connected" : "Unavailable";
    el.geminiStatus.title = status || (available ? "Gemini is available" : "Gemini is not available");
  }

  function getCode() {
    return state.editorReady ? state.editor.getValue() : el.textarea.value;
  }

  function setCode(value) {
    state.source = value;
    if (state.editorReady) {
      state.editor.setValue(value);
    } else {
      el.textarea.value = value;
      syncFallback();
    }
  }

  function matchingBrackets(source, caret) {
    const pairs = { "(": ")", "[": "]", "{": "}" };
    const reverse = { ")": "(", "]": "[", "}": "{" };
    let start = caret < source.length && (pairs[source[caret]] || reverse[source[caret]]) ? caret : caret > 0 ? caret - 1 : -1;
    if (start < 0) return new Set();
    const character = source[start];
    const forward = Boolean(pairs[character]);
    const counterpart = forward ? pairs[character] : reverse[character];
    let depth = 0;
    for (let index = start; forward ? index < source.length : index >= 0; index += forward ? 1 : -1) {
      const current = source[index];
      if (current === character) depth += 1;
      else if (current === counterpart) {
        depth -= 1;
        if (depth === 0) return new Set([start, index]);
      }
    }
    return new Set();
  }

  function syntaxHighlight(source, offset = 0, matched = new Set()) {
    const pattern = /(#[^\n]*|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|\b(?:False|True|None|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b|\b(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?)\b|\b(?:print|range|len|str|int|float|list|dict|set|tuple|sum|min|max|enumerate|zip|type|abs|round|open|input|super)\b|\b[A-Za-z_]\w*(?=\s*\()|(\+|-|\/|\*|%|=|<|>|!|&|\||\^|~|\(|\)|\[|\]|\{|\}))/g;
    let output = "";
    let last = 0;
    let match;
    while ((match = pattern.exec(source))) {
      output += escapeHtml(source.slice(last, match.index));
      let klass = "token-operator";
      if (match[0].startsWith("#")) klass = "token-comment";
      else if (/^['"]/.test(match[0])) klass = "token-string";
      else if (/^\d/.test(match[0])) klass = "token-number";
      else if (/^(print|range|len|str|int|float|list|dict|set|tuple|sum|min|max|enumerate|zip|type|abs|round|open|input|super)$/.test(match[0])) klass = "token-builtin";
      else if (/^(False|True|None|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)$/.test(match[0])) klass = "token-keyword";
      else if (/^[A-Za-z_]/.test(match[0])) klass = "token-function";
      let tokenHtml = "";
      let segmentStart = 0;
      for (let charIndex = 0; charIndex < match[0].length; charIndex += 1) {
        if (matched.has(offset + match.index + charIndex)) {
          tokenHtml += `<span class="${klass}">${escapeHtml(match[0].slice(segmentStart, charIndex))}</span><span class="token-bracket-match">${escapeHtml(match[0][charIndex])}</span>`;
          segmentStart = charIndex + 1;
        }
      }
      tokenHtml += `<span class="${klass}">${escapeHtml(match[0].slice(segmentStart))}</span>`;
      output += tokenHtml;
      last = pattern.lastIndex;
    }
    output += escapeHtml(source.slice(last));
    return output;
  }

  function syncFallback() {
    if (state.editorReady) return;
    const code = el.textarea.value;
    const sourceLines = code.split("\n");
    const lineCount = Math.max(1, sourceLines.length);
    el.gutter.textContent = Array.from({ length: lineCount }, (_, index) => index + 1).join("\n");
    const matched = matchingBrackets(code, el.textarea.selectionStart);
    let offset = 0;
    el.highlight.innerHTML = sourceLines.map((line, index) => {
      const lineStart = offset;
      offset += line.length + 1;
      const classes = ["fallback-line"];
      if (state.currentLine === index + 1) classes.push("is-current");
      if (state.errorLine === index + 1) classes.push("is-error");
      return `<span class="${classes.join(" ")}">${line ? syntaxHighlight(line, lineStart, matched) : "&nbsp;"}</span>`;
    }).join("");
    el.highlight.scrollTop = el.textarea.scrollTop;
    el.highlight.scrollLeft = el.textarea.scrollLeft;
    state.source = code;
    updateCursorPosition();
  }

  function updateCursorPosition() {
    if (state.editorReady) return;
    const before = el.textarea.value.slice(0, el.textarea.selectionStart);
    const lines = before.split("\n");
    el.editorPosition.textContent = `Ln ${lines.length}, Col ${lines[lines.length - 1].length + 1}`;
  }

  function installFallbackEditing() {
    el.textarea.addEventListener("input", syncFallback);
    el.textarea.addEventListener("scroll", syncFallback, { passive: true });
    el.textarea.addEventListener("click", updateCursorPosition);
    el.textarea.addEventListener("keyup", updateCursorPosition);
    el.textarea.addEventListener("select", updateCursorPosition);
    el.textarea.addEventListener("keydown", (event) => {
      if (event.key === "Tab") {
        event.preventDefault();
        const input = el.textarea;
        const start = input.selectionStart;
        const end = input.selectionEnd;
        const value = input.value;
        const selected = value.slice(start, end);
        if (event.shiftKey) {
          const lineStart = value.lastIndexOf("\n", start - 1) + 1;
          const lineEndIndex = value.indexOf("\n", end);
          const lineEnd = lineEndIndex === -1 ? value.length : lineEndIndex;
          const chunk = value.slice(lineStart, lineEnd);
          const updated = chunk.replace(/^ {1,4}/gm, "");
          const removedOnFirst = chunk.split("\n")[0].length - chunk.replace(/^ {1,4}/, "").split("\n")[0].length;
          const replaced = value.slice(0, lineStart) + updated + value.slice(lineEnd);
          input.value = replaced;
          input.setSelectionRange(Math.max(lineStart, start - removedOnFirst), Math.max(lineStart, end - (chunk.length - updated.length)));
        } else if (selected.includes("\n")) {
          const lineStart = value.lastIndexOf("\n", start - 1) + 1;
          const lineEndIndex = value.indexOf("\n", end);
          const lineEnd = lineEndIndex === -1 ? value.length : lineEndIndex;
          const chunk = value.slice(lineStart, lineEnd);
          const updated = chunk.replace(/^/gm, "    ");
          input.value = value.slice(0, lineStart) + updated + value.slice(lineEnd);
          input.setSelectionRange(start + 4, end + (updated.length - chunk.length));
        } else {
          input.setRangeText("    ", start, end, "end");
        }
        syncFallback();
        return;
      }
      if (event.key === "Enter" && !event.shiftKey && !event.ctrlKey && !event.metaKey) {
        const input = el.textarea;
        const start = input.selectionStart;
        const lineStart = input.value.lastIndexOf("\n", start - 1) + 1;
        const beforeCursor = input.value.slice(lineStart, start);
        let indent = (beforeCursor.match(/^\s*/) || [""])[0];
        if (/:(?:\s*|[^#]*\s+#.*)$/.test(beforeCursor.trimEnd())) indent += "    ";
        event.preventDefault();
        input.setRangeText(`\n${indent}`, start, input.selectionEnd, "end");
        syncFallback();
      }
    });
    syncFallback();
  }

  function bootMonaco() {
    const started = Date.now();
    const waitForLoader = () => {
      if (window.require && typeof window.require.config === "function") {
        window.require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs" } });
        window.require(["vs/editor/editor.main"], () => {
          if (state.editorReady) return;
          const currentValue = el.textarea.value;
          state.editor = window.monaco.editor.create(el.host, {
            value: currentValue,
            language: "python",
            theme: "pcv-dark",
            automaticLayout: true,
            fontFamily: '"DM Mono", monospace',
            fontSize: 12,
            lineHeight: 21,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            renderLineHighlight: "all",
            roundedSelection: false,
            cursorBlinking: "smooth",
            padding: { top: 16, bottom: 18 },
            tabSize: 4,
            insertSpaces: true,
            bracketPairColorization: { enabled: true },
            guides: { bracketPairs: true, indentation: true },
            matchBrackets: "always",
            wordWrap: "off",
            accessibilitySupport: "auto",
            ariaLabel: "Python source code editor",
          });
          window.monaco.editor.defineTheme("pcv-dark", {
            base: "vs-dark",
            inherit: true,
            rules: [
              { token: "keyword", foreground: "D8A5D8" },
              { token: "string", foreground: "B7CC91" },
              { token: "number", foreground: "E5B978" },
              { token: "comment", foreground: "83918E", fontStyle: "italic" },
              { token: "identifier", foreground: "E8E4D9" },
              { token: "delimiter", foreground: "D99A80" },
            ],
            colors: {
              "editor.background": "#202733",
              "editor.foreground": "#e8e4d9",
              "editorLineNumber.foreground": "#75818e",
              "editorLineNumber.activeForeground": "#d9c6a4",
              "editor.lineHighlightBackground": "#293442",
              "editor.selectionBackground": "#356b62",
              "editorCursor.foreground": "#e6c88d",
              "editorBracketMatch.background": "#3c504e",
              "editorBracketMatch.border": "#6c9d90",
              "editorIndentGuide.background1": "#333e4b",
              "editorIndentGuide.activeBackground1": "#596b74",
            },
          });
          window.monaco.editor.setTheme("pcv-dark");
          state.editorReady = true;
          state.editor.onDidChangeModelContent(() => { state.source = state.editor.getValue(); });
          state.editor.onDidChangeCursorPosition((event) => {
            el.editorPosition.textContent = `Ln ${event.position.lineNumber}, Col ${event.position.column}`;
          });
          el.host.style.display = "block";
          el.fallback.style.display = "none";
          el.editorEngine.textContent = "Monaco";
          updateEditorMarkers();
          window.addEventListener("resize", () => state.editor?.layout());
        }, () => {
          el.editorEngine.textContent = "Browser editor";
        });
        return;
      }
      if (Date.now() - started < 4200) window.setTimeout(waitForLoader, 100);
      else el.editorEngine.textContent = "Browser editor";
    };
    waitForLoader();
  }

  function updateEditorMarkers() {
    if (!state.editorReady || !state.editor) return;
    const model = state.editor.getModel();
    if (!model) return;
    const decorations = [];
    if (state.currentLine && state.currentLine > 0 && state.currentLine <= model.getLineCount()) {
      decorations.push({
        range: new window.monaco.Range(state.currentLine, 1, state.currentLine, 1),
        options: { isWholeLine: true, className: "pcv-executing-line", glyphMarginClassName: "pcv-executing-glyph" },
      });
    }
    if (state.errorLine && state.errorLine > 0 && state.errorLine <= model.getLineCount()) {
      decorations.push({
        range: new window.monaco.Range(state.errorLine, 1, state.errorLine, model.getLineMaxColumn(state.errorLine)),
        options: { isWholeLine: true, className: "pcv-error-line", glyphMarginClassName: "pcv-error-glyph", overviewRuler: { color: "#c9634a", position: 4 } },
      });
    }
    state.editorDecorations = state.editor.deltaDecorations(state.editorDecorations, decorations);
    if (state.currentLine) state.editor.revealLineInCenterIfOutsideViewport(state.currentLine);
  }

  function updateFallbackMarker() {
    if (!state.editorReady) syncFallback();
  }

  function safeText(value) {
    if (value && typeof value === "object" && Object.prototype.hasOwnProperty.call(value, "__type__")) {
      const type = value.__type__;
      const inner = value.value;
      if (type === "none") return "None";
      if (type === "bool") return inner ? "True" : "False";
      if (type === "str") return JSON.stringify(inner);
      if (type === "dict" && inner && typeof inner === "object") {
        return `{${Object.entries(inner).map(([key, item]) => `${key}: ${safeText(item)}`).join(", ")}}`;
      }
      if (["list", "tuple", "set"].includes(type) && Array.isArray(inner)) {
        const opening = type === "list" ? "[" : type === "tuple" ? "(" : "{";
        const closing = type === "list" ? "]" : type === "tuple" ? ")" : "}";
        return `${opening}${inner.map(safeText).join(", ")}${closing}`;
      }
      return String(inner ?? "");
    }
    if (value === null) return "None";
    if (typeof value === "object") {
      return Array.isArray(value) ? `[${value.map(safeText).join(", ")}]` : JSON.stringify(value);
    }
    return String(value);
  }

  function renderTrace() {
    const events = state.events;
    el.traceCount.textContent = `${events.length} ${events.length === 1 ? "event" : "events"}`;
    el.traceSummary.textContent = events.length ? "CAPTURED TRACE" : "NO TRACE";
    if (!events.length) {
      el.traceList.innerHTML = `<div class="trace-empty"><div class="trace-empty-inner"><strong>${state.busy ? "Capturing execution…" : "Nothing has run yet"}</strong><span>${state.busy ? "The server is tracing your Python program." : "Run your code to inspect its real execution."}</span></div></div>`;
      return;
    }
    el.traceList.innerHTML = events.map((event, index) => {
      const current = index === state.selectedStep;
      return `<button class="trace-row" type="button" role="option" data-step="${index}" aria-selected="${current}" ${current ? 'aria-current="step"' : ""}>
        <span class="trace-step">${String(index + 1).padStart(2, "0")}</span>
        <span class="trace-line">L${escapeHtml(event.line_number ?? "—")}</span>
        <span class="trace-type" data-event="${escapeHtml(event.event)}">${escapeHtml(event.event || "event")}</span>
        <span class="trace-function">${escapeHtml(event.function || "<module>")}</span>
      </button>`;
    }).join("");
    const activeRow = el.traceList.querySelector('[aria-current="step"]');
    activeRow?.scrollIntoView({ block: "nearest" });
  }

  function renderVariables(event) {
    const locals = event?.locals && typeof event.locals === "object" ? event.locals : {};
    const entries = Object.entries(locals);
    el.variableCount.textContent = String(entries.length);
    if (!event) {
      el.variables.innerHTML = '<div class="state-empty">Variable values appear with the trace.</div>';
      return;
    }
    if (!entries.length) {
      el.variables.innerHTML = '<div class="state-empty">No local variables in this frame.</div>';
      return;
    }
    el.variables.innerHTML = entries.map(([name, value]) => `<div class="variable-row"><span class="variable-name">${escapeHtml(name)}</span><span class="variable-value">${escapeHtml(safeText(value))}</span></div>`).join("");
  }

  function stackAt(stepIndex) {
    const frames = [];
    for (let index = 0; index <= stepIndex; index += 1) {
      const event = state.events[index];
      const functionName = event.function || "<module>";
      if (event.event === "call") {
        frames.push({ function: functionName, locals: event.locals || {}, line: event.line_number });
      } else if (event.event === "return") {
        if (!frames.length) frames.push({ function: functionName, locals: event.locals || {}, line: event.line_number });
        else {
          const top = frames[frames.length - 1];
          if (top.function === functionName) {
            top.locals = event.locals || top.locals;
            top.line = event.line_number;
          } else {
            frames.push({ function: functionName, locals: event.locals || {}, line: event.line_number });
          }
        }
        if (index < stepIndex && frames.length) frames.pop();
      } else if (event.event === "line" || event.event === "exception") {
        const frame = [...frames].reverse().find((item) => item.function === functionName);
        if (frame) {
          frame.locals = event.locals || {};
          frame.line = event.line_number;
        } else {
          frames.push({ function: functionName, locals: event.locals || {}, line: event.line_number });
        }
      }
    }
    return frames;
  }

  function renderStack(event) {
    if (!event) {
      el.stackCount.textContent = "—";
      el.stack.innerHTML = '<div class="state-empty">Function frames appear here.</div>';
      return;
    }
    const frames = stackAt(state.selectedStep);
    el.stackCount.textContent = String(frames.length);
    if (!frames.length) {
      el.stack.innerHTML = '<div class="state-empty">No active call frames.</div>';
      return;
    }
    el.stack.innerHTML = `<div class="stack-list">${frames.map((frame, index) => `<div class="stack-frame ${index === frames.length - 1 ? "current" : ""}"><div class="stack-frame-name">${escapeHtml(frame.function)}</div><div class="stack-frame-depth">line ${escapeHtml(frame.line ?? "—")} · depth ${index}</div></div>`).join("")}</div>`;
  }

  function renderConceptFocus(event) {
    el.conceptLensTitle.textContent = state.concept ? `${state.concept} view` : "Concept view";
    if (!event) {
      el.conceptLensMeta.textContent = "Waiting for execution";
      el.conceptFocus.innerHTML = '<div class="focus-empty">Run the program to see the selected concept reflected in actual trace data.</div>';
      return;
    }

    const lineNumber = Number(event.line_number) || 0;
    const lineText = state.source.split(/\r?\n/)[lineNumber - 1] || "";
    const functionName = event.function || "<module>";
    const currentFrames = stackAt(state.selectedStep);
    const previous = state.selectedStep > 0 ? state.events[state.selectedStep - 1] : null;
    const previousLocals = previous?.function === functionName ? (previous.locals || {}) : {};
    const locals = event.locals && typeof event.locals === "object" ? event.locals : {};
    const changed = Object.entries(locals).filter(([name, value]) =>
      JSON.stringify(previousLocals[name]) !== JSON.stringify(value)
    );
    const concept = state.concept || "";
    const loopConcept = /loop/i.test(concept);
    const callConcept = ["Functions", "Recursion"].includes(concept);
    const collectionConcept = ["Lists", "Stack", "Queue", "Dictionary", "Linked List", "Tree", "Graph"].includes(concept);
    let detail = [];

    if (loopConcept) {
      const visits = state.events.slice(0, state.selectedStep + 1)
        .filter((item) => item.line_number === event.line_number && item.function === functionName).length;
      el.conceptLensMeta.textContent = `Trace visit ${visits} · line ${lineNumber}`;
      detail = changed.slice(0, 3).map(([name, value]) =>
        `<span class="focus-chip"><strong>${escapeHtml(name)}</strong><span class="focus-new">${escapeHtml(safeText(value))}</span></span>`
      );
    } else if (callConcept) {
      el.conceptLensMeta.textContent = `${currentFrames.length} active ${currentFrames.length === 1 ? "frame" : "frames"}`;
      detail = currentFrames.slice(-3).map((frame, index) =>
        `<span class="focus-chip"><strong>depth ${Math.max(0, currentFrames.length - Math.min(3, currentFrames.length) + index)}</strong>${escapeHtml(frame.function)}</span>`
      );
    } else if (collectionConcept) {
      const collections = Object.entries(locals).filter(([, value]) =>
        value && typeof value === "object" && ["list", "tuple", "set", "dict"].includes(value.__type__)
      );
      el.conceptLensMeta.textContent = collections.length ? `${collections.length} observed collection${collections.length === 1 ? "" : "s"}` : "Current trace state";
      detail = collections.slice(0, 2).map(([name, value]) => {
        const contents = value.__type__ === "dict" ? Object.entries(value.value || {}) : (value.value || []).map((item, index) => [index, item]);
        const items = contents.slice(0, 5).map(([key, item]) =>
          `<span class="focus-item">${escapeHtml(value.__type__ === "dict" ? `${key}: ${safeText(item)}` : safeText(item))}</span>`
        ).join("");
        return `<span class="focus-chip"><strong>${escapeHtml(name)}</strong><span class="focus-collection">${items || '<span class="focus-item">empty</span>'}</span></span>`;
      });
      if (!detail.length) {
        detail = changed.slice(0, 2).map(([name, value]) =>
          `<span class="focus-chip"><strong>${escapeHtml(name)}</strong><span class="focus-new">${escapeHtml(safeText(value))}</span></span>`
        );
      }
    } else {
      el.conceptLensMeta.textContent = changed.length ? `${changed.length} changed value${changed.length === 1 ? "" : "s"}` : "Captured frame state";
      detail = changed.slice(0, 3).map(([name, value]) => {
        const oldValue = previousLocals[name];
        const before = oldValue === undefined ? "new" : safeText(oldValue);
        return `<span class="focus-chip"><strong>${escapeHtml(name)}</strong><span class="focus-old">${escapeHtml(before)}</span><span>→</span><span class="focus-new">${escapeHtml(safeText(value))}</span></span>`;
      });
    }
    if (!detail.length) {
      detail = [`<span class="focus-chip">${event.event === "return" && event.return_value ? `returns ${escapeHtml(safeText(event.return_value))}` : "No local values changed"}</span>`];
    }

    el.conceptFocus.innerHTML = `<span class="focus-line" aria-label="Line ${lineNumber}">L${lineNumber || "—"}</span>
      <div class="focus-main"><div class="focus-event"><span class="focus-event-type" data-event="${escapeHtml(event.event)}">${escapeHtml(event.event || "event")}</span><span>${escapeHtml(functionName)}</span></div><code class="focus-source">${escapeHtml(lineText || "No source line")}</code></div>
      <div class="focus-detail">${detail.join("")}</div>`;
  }

  function renderOutput(event = null) {
    const execution = state.execution;
    if (!execution) {
      el.output.innerHTML = '<div class="output-empty">Printed output will appear here when your program runs.</div>';
      el.outputCaption.textContent = "stdout";
      return;
    }
    const error = execution.error;
    const output = event?.stdout ?? execution.stdout ?? "";
    const sections = [];
    if (error) {
      const line = error.line ? `Line ${error.line}` : "Line unavailable";
      sections.push(`<div class="output-error"><div class="error-title">Execution error · ${escapeHtml(error.type || "Error")}</div><div class="error-details">${escapeHtml(line)}\n${escapeHtml(error.message || "The program could not be completed.")}</div></div>`);
    } else if (execution.timed_out) {
      sections.push('<div class="output-error"><div class="error-title">Execution timed out</div><div class="error-details">The program exceeded the server execution time limit.</div></div>');
    }
    sections.push(output ? `<pre class="output-pre">${escapeHtml(output)}</pre>` : `<div class="output-empty">${error ? "No stdout was produced before the error." : "No stdout at this step."}</div>`);
    if (execution.stderr) sections.push(`<div class="stderr-output">${escapeHtml(execution.stderr)}</div>`);
    el.output.innerHTML = sections.join("");
    el.outputCaption.textContent = event ? `stdout · step ${state.selectedStep + 1}` : "stdout";
  }

  function renderExplanation() {
    if (state.explaining) {
      el.explanation.innerHTML = '<div class="thinking"><span class="thinking-dots" aria-hidden="true"><i></i><i></i><i></i></span><span>Gemini is reading the selected execution state…</span></div>';
      return;
    }
    if (state.explanationError) {
      el.explanation.innerHTML = `<div class="ai-copy ai-error"><strong>Gemini error</strong><br>${escapeHtml(state.explanationError)}</div>`;
      return;
    }
    if (state.explanationText) {
      el.explanation.innerHTML = `<div class="ai-copy">${escapeHtml(state.explanationText)}</div>`;
      return;
    }
    el.explanation.innerHTML = `<div class="ai-empty"><span class="ai-empty-mark">${state.selectedStep >= 0 ? String(state.selectedStep + 1).padStart(2, "0") : "01"}</span><span>${state.selectedStep >= 0 ? "Ask Gemini to explain this captured step in plain language." : "Select a trace step to ask for a beginner-friendly explanation of what Python just did."}</span></div>`;
  }

  function renderStep() {
    const event = state.selectedStep >= 0 ? state.events[state.selectedStep] : null;
    const total = state.events.length;
    const count = state.selectedStep < 0 ? 0 : state.selectedStep + 1;
    el.counter.innerHTML = `<strong>${count}</strong> / ${total}`;
    el.previous.disabled = state.busy || state.selectedStep <= 0;
    el.next.disabled = state.busy || state.selectedStep < 0 || state.selectedStep >= total - 1;
    el.play.disabled = state.busy || !total || state.playing;
    el.pause.disabled = !state.playing;
    el.reset.disabled = state.busy || !total;
    el.explain.disabled = state.busy || !event || state.explaining;
    state.currentLine = event?.line_number ?? null;
    if (event?.event === "exception") {
      state.errorLine = event.line_number ?? state.execution?.error?.line ?? null;
    } else {
      state.errorLine = state.execution?.error?.line && !total ? state.execution.error.line : null;
    }
    updateEditorMarkers();
    updateFallbackMarker();
    renderTrace();
    renderVariables(event);
    renderStack(event);
    renderConceptFocus(event);
    renderOutput(event);
    renderExplanation();
  }

  function stopPlayback() {
    state.playing = false;
    window.clearTimeout(state.playTimer);
    state.playTimer = null;
    el.play.disabled = state.busy || !state.events.length;
    el.pause.disabled = true;
  }

  function selectStep(index) {
    if (index < 0 || index >= state.events.length) return;
    state.selectedStep = index;
    state.explanationText = "";
    state.explanationError = "";
    state.explaining = false;
    state.explainRequest += 1;
    renderStep();
  }

  function playbackTick() {
    if (!state.playing) return;
    if (state.selectedStep >= state.events.length - 1) {
      stopPlayback();
      return;
    }
    selectStep(Math.max(0, state.selectedStep + 1));
    const speed = Number(el.speed.value);
    const delay = 1150 - speed * 92;
    state.playTimer = window.setTimeout(playbackTick, delay);
  }

  async function loadConcepts() {
    try {
      const payload = await api("/api/concepts");
      if (!payload || !Array.isArray(payload.concepts)) throw new Error("The concepts response was missing its concepts list.");
      state.concepts = payload.concepts;
      el.concept.innerHTML = state.concepts.map((concept) => `<option value="${escapeHtml(concept)}">${escapeHtml(concept)}</option>`).join("");
      if (!state.concepts.length) {
        el.concept.innerHTML = '<option value="">No concepts available</option>';
        showToast("The server returned no Python concepts.", "error");
        return;
      }
      state.concept = state.concepts[0];
      el.concept.value = state.concept;
      el.conceptContext.textContent = state.concept;
      await loadExample(state.concept);
    } catch (error) {
      el.concept.innerHTML = '<option value="">API unavailable</option>';
      el.conceptContext.textContent = "API unavailable";
      showToast(`Could not load concepts: ${error.message}`);
    }
  }

  async function loadExample(concept) {
    const requestId = ++state.conceptRequest;
    el.conceptContext.textContent = concept;
    try {
      const payload = await api(`/api/examples?concept=${encodeURIComponent(concept)}`);
      if (typeof payload.code !== "string") throw new Error("The example response did not include Python code.");
      if (requestId !== state.conceptRequest || concept !== el.concept.value) return;
      setCode(payload.code);
      clearExecution();
    } catch (error) {
      if (requestId !== state.conceptRequest) return;
      showToast(`Could not load the ${concept} example: ${error.message}`);
    }
  }

  function clearExecution() {
    stopPlayback();
    state.execution = null;
    state.events = [];
    state.selectedStep = -1;
    state.currentLine = null;
    state.errorLine = null;
    state.explanationText = "";
    state.explanationError = "";
    state.explaining = false;
    state.explainRequest += 1;
    renderStep();
  }

  async function runCode() {
    if (state.busy) return;
    const code = getCode();
    state.concept = el.concept.value;
    stopPlayback();
    state.busy = true;
    state.execution = null;
    state.events = [];
    state.selectedStep = -1;
    state.currentLine = null;
    state.errorLine = null;
    state.explanationText = "";
    state.explanationError = "";
    el.run.disabled = true;
    el.run.innerHTML = '<span class="thinking-dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="button-word">Running</span>';
    renderStep();
    try {
      const payload = await api("/api/execute", {
        method: "POST",
        body: JSON.stringify({ code, concept: state.concept }),
      });
      if (!payload || !Array.isArray(payload.events)) throw new Error("The execution response did not include trace events.");
      state.execution = payload;
      state.events = payload.events;
      state.selectedStep = payload.events.length ? 0 : -1;
      state.errorLine = payload.error?.line ?? null;
      if (!payload.success && !payload.error && !payload.timed_out) {
        showToast("Execution did not complete successfully. Inspect the program output panel.", "error");
      } else if (payload.timed_out) {
        showToast("Execution stopped after reaching the server time limit.", "error");
      } else if (payload.error) {
        showToast(`${payload.error.type || "Execution error"}${payload.error.line ? ` on line ${payload.error.line}` : ""}: ${payload.error.message || "The program could not be completed."}`, "error");
      }
    } catch (error) {
      state.execution = {
        events: [],
        stdout: "",
        stderr: "",
        timed_out: false,
        error: { type: "API Error", message: error.message, line: null },
      };
      state.events = [];
      state.selectedStep = -1;
      showToast(`Execution request failed: ${error.message}`);
    } finally {
      state.busy = false;
      el.run.disabled = false;
      el.run.innerHTML = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="m5.2 3.5 7.1 4.1-7.1 4.1V3.5Z" fill="currentColor"/></svg><span class="button-word">Run code</span>';
      renderStep();
    }
  }

  async function explainCurrentStep() {
    const event = state.events[state.selectedStep];
    if (!event || state.explaining) return;
    const requestId = ++state.explainRequest;
    const code = getCode();
    const lines = code.split(/\r?\n/);
    const lineNumber = Number(event.line_number) || 1;
    const previous = state.events[state.selectedStep - 1];
    state.explaining = true;
    state.explanationText = "";
    state.explanationError = "";
    renderExplanation();
    renderStep();
    const body = {
      source: code,
      line_number: lineNumber,
      line_text: lines[lineNumber - 1] || "",
      event: event.event,
      function: event.function || "<module>",
      concept: state.concept,
      locals: event.locals || {},
      prev_locals: previous?.locals || {},
    };
    if (event.exception) body.error = event.exception;
    try {
      const payload = await api("/api/explain", { method: "POST", body: JSON.stringify(body) });
      if (requestId !== state.explainRequest) return;
      if (!payload.success) throw new Error(payload.error || "Gemini could not explain this step.");
      if (typeof payload.explanation !== "string" || !payload.explanation.trim()) throw new Error("Gemini returned an empty explanation.");
      state.explanationText = payload.explanation;
    } catch (error) {
      if (requestId !== state.explainRequest) return;
      state.explanationError = error.message;
      showToast(`Gemini explanation failed: ${error.message}`);
      await checkHealth();
    } finally {
      if (requestId === state.explainRequest) {
        state.explaining = false;
        renderExplanation();
        renderStep();
      }
    }
  }

  function bindEvents() {
    el.concept.addEventListener("change", () => {
      state.concept = el.concept.value;
      if (state.concept) {
        el.conceptContext.textContent = state.concept;
        state.explanationText = "";
        state.explanationError = "";
        state.explaining = false;
        state.explainRequest += 1;
        renderStep();
      }
    });
    el.run.addEventListener("click", runCode);
    el.previous.addEventListener("click", () => selectStep(state.selectedStep - 1));
    el.next.addEventListener("click", () => selectStep(state.selectedStep + 1));
    el.play.addEventListener("click", () => {
      if (!state.events.length) return;
      if (state.selectedStep >= state.events.length - 1) selectStep(0);
      state.playing = true;
      el.play.disabled = true;
      el.pause.disabled = false;
      state.playTimer = window.setTimeout(playbackTick, 100);
    });
    el.pause.addEventListener("click", stopPlayback);
    el.reset.addEventListener("click", () => {
      stopPlayback();
      if (state.events.length) selectStep(0);
    });
    el.explain.addEventListener("click", explainCurrentStep);
    el.traceList.addEventListener("click", (event) => {
      const button = event.target.closest("[data-step]");
      if (button) {
        stopPlayback();
        selectStep(Number(button.dataset.step));
      }
    });
    document.addEventListener("keydown", (event) => {
      if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
      if (event.key === "Enter" && document.activeElement !== el.textarea) {
        event.preventDefault();
        runCode();
      }
    });
  }

  async function checkHealth() {
    try {
      const payload = await api("/api/health");
      if (payload.success !== true || !payload.gemini) throw new Error("Health response format is incomplete.");
      setGeminiStatus(Boolean(payload.gemini.available), payload.gemini.status);
    } catch (error) {
      setGeminiStatus(false, "API unavailable");
      showToast(`Could not check Gemini status: ${error.message}`);
    }
  }

  installFallbackEditing();
  bindEvents();
  bootMonaco();
  renderStep();
  checkHealth();
  loadConcepts();
})();