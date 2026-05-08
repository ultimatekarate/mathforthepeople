/* popovers.js — Math for the People
 *
 * Hover (desktop) or tap (mobile) on a .glossary-ref or .equation-ref and a
 * small panel appears with the term's definition or the rendered equation.
 * Pure vanilla JS, no framework. Uses KaTeX (loaded by base.html) to render
 * equation previews when KaTeX is available; falls back to raw TeX if not.
 *
 * Data sources:
 *   .glossary-ref[data-term]  -> looked up in window.GLOSSARY
 *   .equation-ref[data-equation, data-source-title]
 *                             -> rendered inline by KaTeX
 */
(function () {
  "use strict";

  // Single popover element shared across all triggers. Cheaper to reuse
  // than to create one per link, and lets us animate transitions cleanly.
  var popover = document.createElement("div");
  popover.className = "popover";
  popover.setAttribute("role", "tooltip");
  popover.setAttribute("aria-hidden", "true");
  document.body.appendChild(popover);

  var currentTrigger = null;
  var hideTimer = null;
  var renderCache = new Map(); // trigger element -> rendered HTML

  // --- Content builders ----------------------------------------------------

  function buildGlossaryContent(termId) {
    var entry = (window.GLOSSARY || {})[termId];
    if (!entry) {
      return "<p><em>Unknown term: " + escapeHtml(termId) + "</em></p>";
    }
    var html =
      '<div class="popover-kind">term</div>' +
      '<div class="popover-title">' + escapeHtml(entry.name) + '</div>' +
      '<div class="popover-body">' + entry.definition_html + '</div>';
    if (entry.defined_in_url) {
      html +=
        '<div class="popover-source">' +
        'See <a href="' + entry.defined_in_url + '">the post</a> ' +
        'for the full treatment.' +
        '</div>';
    }
    return html;
  }

  function buildEquationContent(trigger) {
    // data-equation already contains MathML rendered server-side by
    // build.py (latex2mathml). The browser unescapes the attribute on
    // read, so we get a real MathML string we can drop into innerHTML.
    var mathml = trigger.dataset.equation || "";
    var sourceTitle = trigger.dataset.sourceTitle || "";
    var html =
      '<div class="popover-kind">equation</div>' +
      '<div class="popover-equation">' + mathml + '</div>';
    if (sourceTitle) {
      html +=
        '<div class="popover-source">From “' +
        escapeHtml(sourceTitle) + '”.</div>';
    }
    return html;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // --- Show / hide ---------------------------------------------------------

  function showFor(trigger) {
    if (currentTrigger === trigger && popover.classList.contains("visible")) {
      return; // already showing for this trigger
    }
    clearTimeout(hideTimer);

    var html = renderCache.get(trigger);
    if (!html) {
      if (trigger.classList.contains("glossary-ref")) {
        html = buildGlossaryContent(trigger.dataset.term);
      } else if (trigger.classList.contains("equation-ref")) {
        html = buildEquationContent(trigger);
      } else {
        return;
      }
      renderCache.set(trigger, html);
    }
    popover.innerHTML = html;
    position(trigger);
    popover.classList.add("visible");
    popover.setAttribute("aria-hidden", "false");
    currentTrigger = trigger;
  }

  function scheduleHide() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function () {
      popover.classList.remove("visible");
      popover.setAttribute("aria-hidden", "true");
      currentTrigger = null;
    }, 100);
  }

  function hideNow() {
    clearTimeout(hideTimer);
    popover.classList.remove("visible");
    popover.setAttribute("aria-hidden", "true");
    currentTrigger = null;
  }

  // --- Positioning ---------------------------------------------------------
  // Place the popover above the trigger if there's room, otherwise below.
  // Clamp horizontally so it never spills off the viewport.

  function position(trigger) {
    var rect = trigger.getBoundingClientRect();
    var pop = popover;
    // Reset so we can measure the popover's natural size.
    pop.style.left = "0px";
    pop.style.top = "0px";
    pop.style.maxWidth = Math.min(380, window.innerWidth - 24) + "px";

    var popRect = pop.getBoundingClientRect();
    var margin = 8;
    var pageY = window.scrollY || window.pageYOffset;
    var pageX = window.scrollX || window.pageXOffset;

    // Vertical: prefer above. If not enough space, go below.
    var topAbove = rect.top + pageY - popRect.height - margin;
    var topBelow = rect.bottom + pageY + margin;
    var top = (rect.top > popRect.height + margin) ? topAbove : topBelow;

    // Horizontal: center on the trigger, then clamp.
    var triggerCenter = rect.left + pageX + rect.width / 2;
    var left = triggerCenter - popRect.width / 2;
    var minLeft = pageX + 8;
    var maxLeft = pageX + window.innerWidth - popRect.width - 8;
    if (left < minLeft) left = minLeft;
    if (left > maxLeft) left = maxLeft;

    pop.style.left = left + "px";
    pop.style.top = top + "px";
  }

  // --- Wiring --------------------------------------------------------------

  function bindAll() {
    var triggers = document.querySelectorAll(".glossary-ref, .equation-ref");
    Array.prototype.forEach.call(triggers, function (el) {
      el.addEventListener("mouseenter", function () { showFor(el); });
      el.addEventListener("mouseleave", scheduleHide);
      el.addEventListener("focus", function () { showFor(el); });
      el.addEventListener("blur", scheduleHide);
      // On touch devices, prevent navigation on the first tap; show the
      // popover instead. A second tap follows the link.
      var tappedOnce = false;
      el.addEventListener("click", function (e) {
        // Heuristic: if the popover is already showing for this trigger,
        // let the click through (the user is following the link).
        if (currentTrigger === el && popover.classList.contains("visible")) {
          return;
        }
        // On hover-capable devices (desktop), let clicks pass through
        // immediately — the popover's already shown via mouseenter.
        if (matchMedia("(hover: hover)").matches) return;
        e.preventDefault();
        showFor(el);
      });
    });
  }

  // Keep popover open while the cursor is on it (so users can click the
  // 'see post' link inside).
  popover.addEventListener("mouseenter", function () {
    clearTimeout(hideTimer);
  });
  popover.addEventListener("mouseleave", scheduleHide);

  // Dismiss on outside click (mobile mostly) and on Escape.
  document.addEventListener("click", function (e) {
    if (!popover.contains(e.target) &&
        !(e.target.closest && e.target.closest(".glossary-ref, .equation-ref"))) {
      hideNow();
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hideNow();
  });

  // Wait for KaTeX to load before binding equation popovers, so the
  // first hover on an equation ref renders cleanly. Binding glossary
  // popovers can happen immediately, but it's simpler to do everything
  // once after `load`.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindAll);
  } else {
    bindAll();
  }
})();
