(function () {
  "use strict";

  const OVERLAY_ID = "fd-transfer-tab-overlay";
  const IFRAME_ID = "fd-transfer-tab-iframe";
  const TAB_COUNT = 5;
  const DEFAULT_TOP = 96;
  const TOP_GAP = 10;

  // Flutter (CanvasKit) mode: tab text usually isn't in DOM, so use tab-bar hit testing.
  let desiredVisible = true; // First tab is default in current app.
  let overlayEl = null;
  let lastApplyToken = 0;
  let lastTabBottom = 0;

  function normalizeText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function hasAnyLabel(text, labels) {
    return labels.some((label) => text.includes(label));
  }

  // DOM fallback (works when accessibility/DOM tabs are present).
  function detectSelectionFromDom() {
    const fileLabels = ["文件传输", "文件上传", "File Transfer", "File Upload"];
    const otherLabels = [
      "文本传输",
      "Text Transfer",
      "文件管理",
      "File Manager",
      "媒体管理",
      "Media",
      "终端控制",
      "Terminal Control",
    ];
    const nodes = document.querySelectorAll("button,[role='tab'],[aria-selected],div,span");
    for (const node of nodes) {
      if (!(node instanceof HTMLElement)) continue;
      const selected = node.getAttribute("aria-selected");
      if (selected !== "true") continue;
      const text = normalizeText(node.innerText || node.textContent);
      if (!text) continue;
      if (hasAnyLabel(text, fileLabels)) return true;
      if (hasAnyLabel(text, otherLabels)) return false;
    }
    return null;
  }

  function computeTabBarRect() {
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    // Tuned for current Flutter desktop layout; still scales with viewport size.
    const width = Math.max(320, Math.min(vw - 24, Math.round(vw * 0.82)));
    const left = Math.max(12, Math.round((vw - width) / 2));
    const top = Math.max(40, Math.min(126, Math.round(vh * 0.085)));
    const height = Math.max(40, Math.min(70, Math.round(vh * 0.065)));

    return {
      left,
      right: left + width,
      top,
      bottom: top + height,
      width,
    };
  }

  function tabIndexFromPoint(clientX, clientY) {
    const rect = computeTabBarRect();
    if (clientY < rect.top || clientY > rect.bottom) return -1;
    if (clientX < rect.left || clientX > rect.right) return -1;
    const slotWidth = rect.width / TAB_COUNT;
    const index = Math.floor((clientX - rect.left) / slotWidth);
    if (index < 0 || index >= TAB_COUNT) return -1;
    lastTabBottom = rect.bottom;
    return index;
  }

  function estimateOverlayTop() {
    if (lastTabBottom > 0) {
      return Math.min(window.innerHeight - 120, Math.max(DEFAULT_TOP, Math.round(lastTabBottom + TOP_GAP)));
    }
    return DEFAULT_TOP;
  }

  function ensureOverlay() {
    if (overlayEl && overlayEl.isConnected) return overlayEl;
    const existing = document.getElementById(OVERLAY_ID);
    if (existing instanceof HTMLElement) {
      overlayEl = existing;
      return overlayEl;
    }

    const overlay = document.createElement("div");
    overlay.id = OVERLAY_ID;
    overlay.style.position = "fixed";
    overlay.style.left = "0";
    overlay.style.right = "0";
    overlay.style.bottom = "0";
    overlay.style.top = DEFAULT_TOP + "px";
    overlay.style.display = "none";
    overlay.style.pointerEvents = "none";
    overlay.style.zIndex = "2147483000";
    overlay.style.background = "transparent";

    const frame = document.createElement("iframe");
    frame.id = IFRAME_ID;
    frame.src = "/transfer";
    frame.title = "Friendeck Transfer Tab";
    frame.style.display = "block";
    frame.style.width = "100%";
    frame.style.height = "100%";
    frame.style.border = "0";
    frame.style.background = "transparent";

    overlay.appendChild(frame);
    document.body.appendChild(overlay);
    overlayEl = overlay;
    return overlayEl;
  }

  function applyOverlayVisibility() {
    const token = ++lastApplyToken;
    window.requestAnimationFrame(() => {
      if (token !== lastApplyToken) return;
      const overlay = ensureOverlay();
      overlay.style.top = estimateOverlayTop() + "px";
      overlay.style.display = desiredVisible ? "block" : "none";
      overlay.style.pointerEvents = desiredVisible ? "auto" : "none";
    });
  }

  function onPointerDown(event) {
    if (!(event instanceof PointerEvent || event instanceof MouseEvent)) return;
    const target = event.target;
    if (target instanceof HTMLElement && target.closest("#" + OVERLAY_ID)) return;

    const idx = tabIndexFromPoint(event.clientX, event.clientY);
    if (idx === 0) {
      desiredVisible = true;
      applyOverlayVisibility();
      return;
    }
    if (idx > 0) {
      desiredVisible = false;
      applyOverlayVisibility();
    }
  }

  function onDomClickFallback(event) {
    const fileLabels = ["文件传输", "文件上传", "File Transfer", "File Upload"];
    const otherLabels = [
      "文本传输",
      "Text Transfer",
      "文件管理",
      "File Manager",
      "媒体管理",
      "Media",
      "终端控制",
      "Terminal Control",
    ];
    const path = typeof event.composedPath === "function" ? event.composedPath() : [event.target];
    for (const item of path) {
      if (!(item instanceof HTMLElement)) continue;
      const text = normalizeText(item.innerText || item.textContent);
      if (!text) continue;
      if (hasAnyLabel(text, fileLabels)) {
        desiredVisible = true;
        applyOverlayVisibility();
        return;
      }
      if (hasAnyLabel(text, otherLabels)) {
        desiredVisible = false;
        applyOverlayVisibility();
        return;
      }
    }
  }

  function onHashChangeFallback() {
    const hash = String(window.location.hash || "").toLowerCase();
    if (hash.includes("transfer")) {
      desiredVisible = true;
      applyOverlayVisibility();
      return;
    }
    if (hash.includes("file-manager") || hash.includes("media") || hash.includes("text") || hash.includes("terminal")) {
      desiredVisible = false;
      applyOverlayVisibility();
    }
  }

  function installMutationSync() {
    const observer = new MutationObserver(() => {
      const selected = detectSelectionFromDom();
      if (selected === null) return;
      desiredVisible = selected;
      applyOverlayVisibility();
    });
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["aria-selected", "class", "style"],
    });
  }

  function init() {
    ensureOverlay();

    document.addEventListener("pointerdown", onPointerDown, true);
    document.addEventListener("click", onDomClickFallback, true);
    window.addEventListener("hashchange", onHashChangeFallback);
    window.addEventListener("resize", () => {
      applyOverlayVisibility();
    });

    installMutationSync();

    // Wait for Flutter mount, then show transfer replacement by default.
    window.setTimeout(() => {
      const selected = detectSelectionFromDom();
      if (selected !== null) desiredVisible = selected;
      applyOverlayVisibility();
    }, 1200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
