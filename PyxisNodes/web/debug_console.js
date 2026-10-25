/*
 * Pyxis Effector - Plugin for Aegisub
 * Copyright (C) 2026 @mandholine, @effector2, @pholguinc
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 * For any question you can visit: https://discord.gg/fsxRESeQZN
 */

/**
 * @file debug_console.js
 * @description Integrated developer diagnostic console overlay (F1 / Escape) for Pyxis Effector.
 * Captures browser events, IPC messages, and runtime logging with search and export capabilities.
 * @module PyxisDebugConsole
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        /* =============================================================================
           PYXIS INTEGRATED DEBUG CONSOLE (F1 / ESCAPE)
           ============================================================================= */
        window.PyxisDebugConsole = (function () {
            let isOpen = false;
            let searchQuery = "";
            let logs = [];
            let initialFetched = false;

            function getOverlay() {
                return document.getElementById("pyxis-debug-console-overlay");
            }

            function getBody() {
                return document.getElementById("pyxis-debug-console-body");
            }

            function getScrollBtn() {
                return document.getElementById("pyxis-debug-btn-autoscroll");
            }

            function getCountBadge() {
                return document.getElementById("pyxis-debug-log-count");
            }

            function isNearBottom(threshold = 50) {
                const body = getBody();
                if (!body) return true;
                const distanceToBottom = body.scrollHeight - body.scrollTop - body.clientHeight;
                return distanceToBottom <= threshold;
            }

            function updateScrollBtnVisibility() {
                const btn = getScrollBtn();
                if (!btn) return;
                const nearBottom = isNearBottom(50);
                btn.classList.toggle("is-visible", !nearBottom);
            }

            function scrollToBottom(smooth = true) {
                const body = getBody();
                if (!body) return;
                if (smooth && typeof body.scrollTo === "function") {
                    body.scrollTo({ top: body.scrollHeight, behavior: "smooth" });
                } else {
                    body.scrollTop = body.scrollHeight;
                }
                setTimeout(updateScrollBtnVisibility, 150);
            }

            function formatLine(line) {
                let cls = "log-dim";
                const l = String(line).toLowerCase();
                if (l.includes("error") || l.includes("exception") || l.includes("traceback") || l.includes("failed")) {
                    cls = "log-error";
                } else if (l.includes("warning") || l.includes("warn")) {
                    cls = "log-warn";
                } else if (l.includes("[pyxis scan]") || l.includes("loaded:") || l.includes("res=")) {
                    cls = "log-scan";
                } else if (l.includes("[pyxis") || l.includes("info") || l.includes("success") || l.includes("completed")) {
                    cls = "log-info";
                }
                return `<div class="pyxis-log-row ${cls}">${escapeHtml(line)}</div>`;
            }

            function escapeHtml(str) {
                return String(str)
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }

            function renderLogs(forceScrollToBottom = false) {
                const body = getBody();
                if (!body) return;

                const shouldScroll = forceScrollToBottom || isNearBottom(50);

                const filtered = searchQuery
                    ? logs.filter(line => String(line).toLowerCase().includes(searchQuery.toLowerCase()))
                    : logs;

                const countBadge = getCountBadge();
                if (countBadge) {
                    const lineWord = window.PyxisI18n ? PyxisI18n.t("ui.console.lines") : "lines";
                    countBadge.textContent = `${filtered.length} ${lineWord}`;
                }

                if (filtered.length === 0) {
                    const emptyText = window.PyxisI18n ? PyxisI18n.t("ui.console.empty") : "No console logs.";
                    body.innerHTML = `<div class="pyxis-debug-console-empty">${escapeHtml(emptyText)}</div>`;
                    updateScrollBtnVisibility();
                    return;
                }

                body.innerHTML = filtered.map(formatLine).join("");

                if (shouldScroll) {
                    body.scrollTop = body.scrollHeight;
                }
                updateScrollBtnVisibility();
            }

            function appendLog(line) {
                if (!line) return;
                logs.push(line);
                if (logs.length > 3000) {
                    logs.shift();
                }
                if (isOpen) {
                    const body = getBody();
                    if (!body) return;

                    if (searchQuery && !String(line).toLowerCase().includes(searchQuery.toLowerCase())) {
                        return;
                    }

                    const shouldScroll = isNearBottom(50);

                    const emptyEl = body.querySelector(".pyxis-debug-console-empty");
                    if (emptyEl) {
                        emptyEl.remove();
                    }

                    const temp = document.createElement("div");
                    temp.innerHTML = formatLine(line);
                    const row = temp.firstElementChild;
                    if (row) {
                        body.appendChild(row);
                        if (shouldScroll) {
                            body.scrollTop = body.scrollHeight;
                        }
                    }

                    const countBadge = getCountBadge();
                    if (countBadge) {
                        const lineWord = window.PyxisI18n ? PyxisI18n.t("ui.console.lines") : "lines";
                        const total = searchQuery ? body.querySelectorAll(".pyxis-log-row").length : logs.length;
                        countBadge.textContent = `${total} ${lineWord}`;
                    }

                    updateScrollBtnVisibility();
                }
            }

            let pollTimer = null;

            function fetchLogsFromBackend() {
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_console_logs === "function") {
                    window.pywebview.api.get_console_logs().then(res => {
                        if (res && res.success && Array.isArray(res.logs)) {
                            const isFirst = !initialFetched;
                            logs = res.logs.slice();
                            initialFetched = true;
                            if (isOpen) {
                                renderLogs(isFirst);
                            }
                        }
                    }).catch(() => {});
                }
            }

            function open() {
                isOpen = true;
                const overlay = getOverlay();
                if (overlay) {
                    overlay.classList.add("is-open");
                }
                fetchLogsFromBackend();
                if (pollTimer) clearInterval(pollTimer);
                pollTimer = setInterval(fetchLogsFromBackend, 800);

                const searchInput = document.getElementById("pyxis-debug-search-input");
                if (searchInput) {
                    setTimeout(() => searchInput.focus(), 50);
                }
                setTimeout(() => {
                    scrollToBottom(false);
                    updateScrollBtnVisibility();
                }, 80);
            }

            function close() {
                isOpen = false;
                if (pollTimer) {
                    clearInterval(pollTimer);
                    pollTimer = null;
                }
                const overlay = getOverlay();
                if (overlay) {
                    overlay.classList.remove("is-open");
                }
            }

            function toggle() {
                if (isOpen) close();
                else open();
            }

            function clear() {
                logs = [];
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.clear_console_logs === "function") {
                    window.pywebview.api.clear_console_logs();
                }
                renderLogs(true);
            }

            function copy() {
                const text = logs.join("");
                if (!navigator.clipboard) {
                    const ta = document.createElement("textarea");
                    ta.id = "pyxis-clipboard-helper";
                    ta.name = "pyxis-clipboard-helper";
                    ta.value = text;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand("copy");
                    document.body.removeChild(ta);
                } else {
                    navigator.clipboard.writeText(text);
                }
                const btn = document.getElementById("pyxis-debug-copy-label");
                if (btn) {
                    const originalText = btn.textContent;
                    btn.textContent = window.PyxisI18n ? PyxisI18n.t("ui.console.copied") : "Copied!";
                    setTimeout(() => {
                        btn.textContent = window.PyxisI18n ? PyxisI18n.t("ui.console.copy") : originalText;
                    }, 1800);
                }
            }

            function init() {
                const closeBtn = document.getElementById("pyxis-debug-btn-close");
                if (closeBtn) closeBtn.addEventListener("click", close);

                const clearBtn = document.getElementById("pyxis-debug-btn-clear");
                if (clearBtn) clearBtn.addEventListener("click", clear);

                const copyBtn = document.getElementById("pyxis-debug-btn-copy");
                if (copyBtn) copyBtn.addEventListener("click", copy);

                const autoScrollBtn = document.getElementById("pyxis-debug-btn-autoscroll");
                if (autoScrollBtn) {
                    autoScrollBtn.addEventListener("click", () => {
                        scrollToBottom(true);
                    });
                }

                const body = getBody();
                if (body) {
                    body.addEventListener("scroll", updateScrollBtnVisibility, { passive: true });
                }

                const searchInput = document.getElementById("pyxis-debug-search-input");
                if (searchInput) {
                    searchInput.addEventListener("input", (e) => {
                        searchQuery = e.target.value.trim();
                        renderLogs();
                    });
                }

                const overlay = getOverlay();
                if (overlay) {
                    overlay.addEventListener("click", (e) => {
                        if (e.target === overlay) {
                            close();
                        }
                    });
                }
            }

            window.__pyxis_push_log = function (text) {
                appendLog(text);
            };

            window.addEventListener("pywebviewready", () => {
                fetchLogsFromBackend();
            });

            if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", init);
            } else {
                init();
            }

            return {
                open,
                close,
                toggle,
                clear,
                copy,
                appendLog,
                fetchLogs: fetchLogsFromBackend,
                isOpen: () => isOpen,
                scrollToBottom
            };
        })();

        window.addEventListener("keydown", function(e) {
            if (e.key === "F1") {
                e.preventDefault();
                if (window.PyxisDebugConsole) {
                    window.PyxisDebugConsole.toggle();
                }
            } else if (e.key === "Escape") {
                if (window.PyxisDebugConsole && window.PyxisDebugConsole.isOpen()) {
                    e.preventDefault();
                    window.PyxisDebugConsole.close();
                }
            }
        });
