/*
 * Pyxis Effector - Plugin for Aegisub
 * Copyright (C) 2026 @mandholine, @effector2, @pholguinc
 *
 * Integrated Documentation & Manual Viewer Service
 */

(function (window, document) {
    "use strict";

    const STORAGE_KEY = "pyxis_help_window_state";

    /**
     * Interactive documentation and technical manual viewer service for Pyxis Effector.
     * Manages a non-blocking floating window with live Markdown parsing, KaTeX formula
     * rendering, bi-directional scrollspy navigation, and LocalStorage bounds persistence.
     */
    class PyxisHelpViewer {
        /**
         * Initialises internal state, bounds tracking, and DOM lifecycle hooks.
         */
        constructor() {
            this.container = null;
            this.header = null;
            this.sidebar = null;
            this.contentPane = null;
            this.tocContainer = null;
            this.searchInput = null;
            this.breadcrumbEl = null;

            this.tocData = [];
            this.chapterCache = {};
            this.currentChapter = null;
            this.currentNode = null;
            this.isMaximized = false;
            this.isMinimized = false;
            this.savedBounds = null;

            this.isDragging = false;
            this.dragOffset = { x: 0, y: 0 };
            this.isResizing = false;
            this.currentResizer = null;
            this.resizeStart = { x: 0, y: 0, w: 0, h: 0, l: 0, t: 0 };

            this.isSplitterDragging = false;
            this.splitterStartX = 0;
            this.splitterStartWidth = 260;

            this.init();
        }

        /**
         * Binds DOM readiness listener to construct the viewer shell.
         */
        init() {
            if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", () => this.buildDOM());
            } else {
                this.buildDOM();
            }
        }

        /**
         * Resolves internationalised UI string via the Pyxis i18n subsystem.
         * @param {string} key - Translation key.
         * @param {object} [params] - Replacement tokens.
         * @param {string} [fallback] - Fallback string if key is unmapped.
         * @returns {string} Translated string.
         */
        t(key, params, fallback) {
            if (window.PyxisI18n && typeof window.PyxisI18n.t === "function") {
                return window.PyxisI18n.t(key, params, fallback);
            }
            if (window.t && typeof window.t === "function") {
                return window.t(key, params, fallback);
            }
            return fallback !== undefined ? fallback : key;
        }

        /**
         * Constructs the floating window DOM structure, header actions, and resizer handles.
         */
        buildDOM() {
            if (document.getElementById("pyxis-help-window")) {
                return;
            }

            const win = document.createElement("div");
            win.id = "pyxis-help-window";
            win.className = "pyxis-help-window";
            win.style.display = "none";

            win.innerHTML = `
                <div class="pyxis-floating-header pyxis-help-header" id="pyxis-help-header">
                    <div class="pyxis-floating-header-title">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:16px;height:16px;stroke:var(--doc-accent-bright, var(--accent-primary, #22858c));fill:none;stroke-width:2.2;">
                            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                        </svg>
                        <span id="pyxis-help-win-title" data-i18n="help.window_title">Pyxis Effector — Manual</span>
                    </div>
                    <div class="pyxis-floating-header-actions">
                        <button class="pyxis-header-icon-btn" id="pyxis-help-btn-minimize" data-i18n-tooltip="help.minimize_tooltip" data-tooltip="Minimize">
                            <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                        </button>
                        <button class="pyxis-header-icon-btn" id="pyxis-help-btn-maximize" data-i18n-tooltip="help.maximize_tooltip" data-tooltip="Maximize">
                            <svg class="svg-icon" id="pyxis-help-max-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
                        </button>
                        <button class="pyxis-header-icon-btn pyxis-btn-close" id="pyxis-help-btn-close" data-i18n-tooltip="help.close_tooltip" data-tooltip="Close">
                            <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        </button>
                    </div>
                </div>

                <div class="pyxis-help-body" id="pyxis-help-body">
                    <aside class="pyxis-help-sidebar" id="pyxis-help-sidebar">
                        <div class="pyxis-help-search-box">
                            <svg class="svg-icon pyxis-help-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8"></circle>
                                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                            </svg>
                            <input type="text" class="pyxis-help-search-input" id="pyxis-help-search-input" 
                                   placeholder="Search nodes or topics..." data-i18n-placeholder="help.search_placeholder" spellcheck="false">
                            <button class="pyxis-help-search-clear" id="pyxis-help-search-clear" style="display:none;">&times;</button>
                        </div>
                        <div class="pyxis-help-toc" id="pyxis-help-toc">
                            <div class="pyxis-help-loading-toc" data-i18n="common.loading">Loading documentation index...</div>
                        </div>
                    </aside>

                    <div class="pyxis-help-splitter" id="pyxis-help-splitter"></div>

                    <main class="pyxis-help-main" id="pyxis-help-main">
                        <div class="pyxis-help-topbar">
                            <div class="pyxis-help-breadcrumbs" id="pyxis-help-breadcrumbs">
                                <span class="crumb-root" id="crumb-root" data-i18n="help.manual_root">Manual</span>
                            </div>
                            <div class="pyxis-help-topbar-actions">
                                <button class="pyxis-help-btn-scroll-top" id="pyxis-help-scroll-top" data-i18n-tooltip="help.scroll_top_tooltip" data-tooltip="Scroll to top">
                                    <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
                                </button>
                            </div>
                        </div>
                        <div class="pyxis-help-content pyxis-markdown-body" id="pyxis-help-content">
                            <div class="pyxis-help-empty" data-i18n="help.select_chapter">Select a chapter or node to view documentation.</div>
                        </div>
                    </main>
                </div>

                <!-- Resizers -->
                <div class="pyxis-floating-resizer nw" data-dir="nw"></div>
                <div class="pyxis-floating-resizer ne" data-dir="ne"></div>
                <div class="pyxis-floating-resizer sw" data-dir="sw"></div>
                <div class="pyxis-floating-resizer se" data-dir="se"></div>
                <div class="pyxis-floating-resizer n" data-dir="n"></div>
                <div class="pyxis-floating-resizer s" data-dir="s"></div>
                <div class="pyxis-floating-resizer w" data-dir="w"></div>
                <div class="pyxis-floating-resizer e" data-dir="e"></div>
            `;

            document.body.appendChild(win);

            this.container = win;
            this.header = win.querySelector("#pyxis-help-header");
            this.sidebar = win.querySelector("#pyxis-help-sidebar");
            this.contentPane = win.querySelector("#pyxis-help-content");
            this.tocContainer = win.querySelector("#pyxis-help-toc");
            this.searchInput = win.querySelector("#pyxis-help-search-input");
            this.breadcrumbEl = win.querySelector("#pyxis-help-breadcrumbs");

            this.bindEvents();
            this.restoreBounds();
            this.configureMarked();
        }

        /**
         * Configures marked.js options and injects custom image renderer for local assets.
         */
        configureMarked() {
            if (window.marked && typeof window.marked.setOptions === "function") {
                const renderer = new (window.marked.Renderer || Object)();
                const transparentSvg = "data:image/svg+xml;utf8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%221%22%20height%3D%221%22%3E%3Crect%20fill%3D%22transparent%22%20width%3D%221%22%20height%3D%221%22%2F%3E%3C%2Fsvg%3E";

                renderer.image = function(href, title, text) {
                    const cleanHref = (href || "").trim();
                    if (cleanHref.startsWith("data:") || cleanHref.startsWith("http://") || cleanHref.startsWith("https://")) {
                        return `<img src="${cleanHref}" alt="${text || ''}" title="${title || ''}">`;
                    }
                    const imgName = cleanHref.split("/").pop();
                    return `<img class="pyxis-doc-img" data-doc-img="${imgName}" src="${transparentSvg}" alt="${text || ''}" title="${title || ''}">`;
                };

                window.marked.setOptions({
                    gfm: true,
                    breaks: true,
                    headerIds: true,
                    mangle: false,
                    renderer: renderer
                });
            }
        }

        bindEvents() {
            // Dragging
            this.header.addEventListener("mousedown", (e) => this.onDragStart(e));

            // Resizing Window
            const resizers = this.container.querySelectorAll(".pyxis-floating-resizer");
            resizers.forEach((r) => {
                r.addEventListener("mousedown", (e) => this.onResizeStart(e, r.getAttribute("data-dir")));
            });

            // Resizing Splitter
            const splitter = this.container.querySelector("#pyxis-help-splitter");
            splitter.addEventListener("mousedown", (e) => this.onSplitterStart(e));

            window.addEventListener("mousemove", (e) => {
                if (this.isDragging) this.onDragMove(e);
                if (this.isResizing) this.onResizeMove(e);
                if (this.isSplitterDragging) this.onSplitterMove(e);
            });

            window.addEventListener("mouseup", () => {
                if (this.isDragging) this.onDragEnd();
                if (this.isResizing) this.onResizeEnd();
                if (this.isSplitterDragging) this.onSplitterEnd();
            });

            // Header Buttons (Solo Iconos con Tooltip)
            const btnClose = this.container.querySelector("#pyxis-help-btn-close");
            btnClose.addEventListener("click", () => this.close());

            const btnMax = this.container.querySelector("#pyxis-help-btn-maximize");
            btnMax.addEventListener("click", () => this.toggleMaximize());

            const btnMin = this.container.querySelector("#pyxis-help-btn-minimize");
            btnMin.addEventListener("click", () => this.toggleMinimize());

            // Doble clic en cabecera para maximizar/restaurar
            this.header.addEventListener("dblclick", (e) => {
                if (e.target.closest(".pyxis-floating-header-actions")) return;
                this.toggleMaximize();
            });

            // Buscador
            this.searchInput.addEventListener("input", () => this.onSearch());
            const clearBtn = this.container.querySelector("#pyxis-help-search-clear");
            clearBtn.addEventListener("click", () => {
                this.searchInput.value = "";
                clearBtn.style.display = "none";
                this.renderTOC(this.tocData);
            });

            // Scroll to Top
            const btnScrollTop = this.container.querySelector("#pyxis-help-scroll-top");
            btnScrollTop.addEventListener("click", () => {
                this.contentPane.scrollTo({ top: 0, behavior: "smooth" });
            });

            // Atajo de teclado Esc (cerrar o salir de maximizado)
            window.addEventListener("keydown", (e) => {
                if (e.key === "Escape" && this.isOpen()) {
                    if (this.isMaximized) {
                        this.toggleMaximize();
                    } else {
                        this.close();
                    }
                }
            });

            // Sincronización dinámica de idioma
            window.addEventListener("pyxis:languageChanged", () => {
                this.chapterCache = {};
                this.loadTOC();
                if (this.currentChapter) {
                    this.loadChapter(this.currentChapter);
                }
            });

            // Scrollspy para seguimiento de lectura en tiempo real
            this.setupScrollSpy();
        }

        // =========================================================================
        // WINDOW POSITIONING & PERSISTENCE
        // =========================================================================

        /**
         * Restores window geometry and sidebar split dimensions from LocalStorage.
         */
        restoreBounds() {
            try {
                const raw = localStorage.getItem(STORAGE_KEY);
                if (raw) {
                    const data = JSON.parse(raw);
                    if (data.w && data.h) {
                        const winW = window.innerWidth;
                        const winH = window.innerHeight;
                        const w = Math.min(Math.max(480, data.w), winW - 20);
                        const h = Math.min(Math.max(360, data.h), winH - 20);
                        const l = Math.min(Math.max(10, data.l), winW - w - 10);
                        const t = Math.min(Math.max(10, data.t), winH - h - 10);

                        this.container.style.width = `${w}px`;
                        this.container.style.height = `${h}px`;
                        this.container.style.left = `${l}px`;
                        this.container.style.top = `${t}px`;
                        if (data.sidebarWidth) {
                            this.sidebar.style.width = `${data.sidebarWidth}px`;
                        }
                        return;
                    }
                }
            } catch (e) {}

            // Por defecto centrado
            const defW = Math.min(1020, window.innerWidth - 80);
            const defH = Math.min(720, window.innerHeight - 80);
            const defL = Math.max(20, Math.floor((window.innerWidth - defW) / 2));
            const defT = Math.max(20, Math.floor((window.innerHeight - defH) / 2));

            this.container.style.width = `${defW}px`;
            this.container.style.height = `${defH}px`;
            this.container.style.left = `${defL}px`;
            this.container.style.top = `${defT}px`;
        }

        /**
         * Persists window size, location, and sidebar split width into LocalStorage.
         */
        saveBounds() {
            if (this.isMaximized) return;
            try {
                const rect = this.container.getBoundingClientRect();
                const state = {
                    w: rect.width,
                    h: rect.height,
                    l: rect.left,
                    t: rect.top,
                    sidebarWidth: this.sidebar.offsetWidth
                };
                localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
            } catch (e) {}
        }

        // =========================================================================
        // DRAG & RESIZE ENGINE
        // =========================================================================

        /**
         * Initiates floating window drag interaction from the titlebar header.
         * @param {MouseEvent} e - Mouse event initiating the drag gesture.
         */
        onDragStart(e) {
            if (e.target.closest(".pyxis-floating-header-actions")) return;
            if (this.isMaximized) return;

            this.isDragging = true;
            const rect = this.container.getBoundingClientRect();
            this.dragOffset.x = e.clientX - rect.left;
            this.dragOffset.y = e.clientY - rect.top;

            this.container.classList.add("is-dragging");
            document.body.style.userSelect = "none";
        }

        /**
         * Updates floating window coordinates during an active drag interaction.
         * Clamps the window position within visible browser viewport boundaries.
         * @param {MouseEvent} e - Mouse event reporting current pointer coordinates.
         */
        onDragMove(e) {
            if (!this.isDragging) return;
            let x = e.clientX - this.dragOffset.x;
            let y = e.clientY - this.dragOffset.y;

            // Restringir a la pantalla
            const maxW = window.innerWidth;
            const maxH = window.innerHeight;
            const w = this.container.offsetWidth;

            x = Math.max(10 - w + 100, Math.min(x, maxW - 100));
            y = Math.max(0, Math.min(y, maxH - 40));

            this.container.style.left = `${x}px`;
            this.container.style.top = `${y}px`;
        }

        /**
         * Finalises floating window dragging and saves the resulting position into LocalStorage.
         */
        onDragEnd() {
            if (!this.isDragging) return;
            this.isDragging = false;
            this.container.classList.remove("is-dragging");
            document.body.style.userSelect = "";
            this.saveBounds();
        }

        /**
         * Initiates an 8-direction resize operation on the floating window.
         * @param {MouseEvent} e - Mouse event initiating the resize action.
         * @param {string} dir - Compass direction of the active resizer handle ('n', 's', 'e', 'w', 'nw', 'ne', 'sw', 'se').
         */
        onResizeStart(e, dir) {
            if (this.isMaximized) return;
            e.stopPropagation();
            this.isResizing = true;
            this.currentResizer = dir;

            const rect = this.container.getBoundingClientRect();
            this.resizeStart = {
                x: e.clientX,
                y: e.clientY,
                w: rect.width,
                h: rect.height,
                l: rect.left,
                t: rect.top
            };

            this.container.classList.add("is-resizing");
            document.body.style.userSelect = "none";
            const cursorMap = {
                n: "ns-resize",
                s: "ns-resize",
                e: "ew-resize",
                w: "ew-resize",
                nw: "nwse-resize",
                se: "nwse-resize",
                ne: "nesw-resize",
                sw: "nesw-resize"
            };
            if (cursorMap[dir]) {
                document.body.style.cursor = cursorMap[dir];
            }
        }

        /**
         * Recalculates and applies window dimensions during an active edge or corner resize gesture.
         * Enforces minimum dimensions to prevent window collapse.
         * @param {MouseEvent} e - Mouse event reporting pointer movement.
         */
        onResizeMove(e) {
            if (!this.isResizing) return;
            const dx = e.clientX - this.resizeStart.x;
            const dy = e.clientY - this.resizeStart.y;
            const dir = this.currentResizer;

            let newW = this.resizeStart.w;
            let newH = this.resizeStart.h;
            let newL = this.resizeStart.l;
            let newT = this.resizeStart.t;

            const minW = 480;
            const minH = 340;

            if (dir.includes("e")) {
                newW = Math.max(minW, this.resizeStart.w + dx);
            }
            if (dir.includes("s")) {
                newH = Math.max(minH, this.resizeStart.h + dy);
            }

            if (dir.includes("w")) {
                const maxDx = this.resizeStart.w - minW;
                const clampedDx = Math.min(dx, maxDx);
                newW = this.resizeStart.w - clampedDx;
                newL = this.resizeStart.l + clampedDx;
            }

            if (dir.includes("n")) {
                const maxDy = this.resizeStart.h - minH;
                const clampedDy = Math.min(dy, maxDy);
                newH = this.resizeStart.h - clampedDy;
                newT = this.resizeStart.t + clampedDy;
            }

            this.container.style.width = `${newW}px`;
            this.container.style.height = `${newH}px`;
            this.container.style.left = `${newL}px`;
            this.container.style.top = `${newT}px`;
        }

        /**
         * Finalises window resizing, restores document cursor and persists geometry.
         */
        onResizeEnd() {
            if (!this.isResizing) return;
            this.isResizing = false;
            this.currentResizer = null;
            this.container.classList.remove("is-resizing");
            document.body.style.userSelect = "";
            document.body.style.cursor = "";
            this.saveBounds();
        }

        /**
         * Initiates horizontal sidebar splitter drag interaction.
         * @param {MouseEvent} e - Mouse event on the splitter bar.
         */
        onSplitterStart(e) {
            e.stopPropagation();
            this.isSplitterDragging = true;
            this.splitterStartX = e.clientX;
            this.splitterStartWidth = this.sidebar.offsetWidth;
            this.container.classList.add("is-resizing-splitter");
            document.body.style.userSelect = "none";
        }

        /**
         * Adjusts sidebar width according to splitter drag displacement, clamped between 180px and 480px.
         * @param {MouseEvent} e - Mouse event with current pointer coordinates.
         */
        onSplitterMove(e) {
            if (!this.isSplitterDragging) return;
            const dx = e.clientX - this.splitterStartX;
            const newW = Math.max(180, Math.min(480, this.splitterStartWidth + dx));
            this.sidebar.style.width = `${newW}px`;
        }

        /**
         * Finalises splitter dragging and persists new sidebar width to LocalStorage.
         */
        onSplitterEnd() {
            if (!this.isSplitterDragging) return;
            this.isSplitterDragging = false;
            this.container.classList.remove("is-resizing-splitter");
            document.body.style.userSelect = "";
            this.saveBounds();
        }

        // =========================================================================
        // WINDOW VISIBILITY & CONTROLS
        // =========================================================================

        /**
         * Checks whether the help viewer window is currently displayed.
         * @returns {boolean} True if window container exists and is visible.
         */
        isOpen() {
            return this.container && this.container.style.display !== "none";
        }

        /**
         * Displays the help viewer window, resets scroll offsets, and loads Table of Contents if empty.
         */
        open() {
            if (!this.container) this.buildDOM();
            if (this.isMinimized) {
                this.toggleMinimize();
            }
            this.container.style.display = "flex";
            this.container.style.zIndex = "150000";

            this.container.scrollTop = 0;
            this.container.scrollLeft = 0;
            if (this.sidebar) { this.sidebar.scrollTop = 0; this.sidebar.scrollLeft = 0; }
            const mainEl = this.container.querySelector("#pyxis-help-main");
            if (mainEl) { mainEl.scrollTop = 0; mainEl.scrollLeft = 0; }
            const bodyEl = this.container.querySelector("#pyxis-help-body");
            if (bodyEl) { bodyEl.scrollTop = 0; bodyEl.scrollLeft = 0; }

            if (this.tocData.length === 0) {
                this.loadTOC();
            }
        }

        /**
         * Hides the help viewer window.
         */
        close() {
            if (!this.container) return;
            this.container.style.display = "none";
        }

        /**
         * Toggles the visibility state of the help viewer window.
         */
        toggle() {
            if (this.isOpen()) {
                this.close();
            } else {
                this.open();
            }
        }

        /**
         * Minimises the window to only show the header bar, or restores full window body.
         */
        toggleMinimize() {
            if (this.isMaximized) {
                this.toggleMaximize();
            }

            this.isMinimized = !this.isMinimized;
            this.container.classList.toggle("is-minimized", this.isMinimized);
            const btn = this.container.querySelector("#pyxis-help-btn-minimize");
            if (this.isMinimized) {
                btn.setAttribute("data-tooltip", this.t("help.restore_tooltip", null, "Restore"));
            } else {
                btn.setAttribute("data-tooltip", this.t("help.minimize_tooltip", null, "Minimize"));
                // Al restaurar, garantizar que no quede desbordado fuera de la pantalla
                const rect = this.container.getBoundingClientRect();
                const winW = window.innerWidth;
                const winH = window.innerHeight;
                if (rect.right > winW) {
                    const newL = Math.max(10, winW - rect.width - 10);
                    this.container.style.left = `${newL}px`;
                }
                if (rect.bottom > winH) {
                    const newT = Math.max(10, winH - rect.height - 10);
                    this.container.style.top = `${newT}px`;
                }
            }
        }

        /**
         * Maximises the help viewer to occupy the full viewport or restores previously saved bounds.
         */
        toggleMaximize() {
            if (this.isMinimized) {
                this.toggleMinimize();
            }

            this.isMaximized = !this.isMaximized;
            this.container.classList.toggle("is-maximized", this.isMaximized);

            const maxIcon = this.container.querySelector("#pyxis-help-max-icon");
            const maxBtn = this.container.querySelector("#pyxis-help-btn-maximize");

            if (this.isMaximized) {
                this.savedBounds = {
                    w: this.container.style.width,
                    h: this.container.style.height,
                    l: this.container.style.left,
                    t: this.container.style.top
                };
                maxIcon.innerHTML = `<rect x="5" y="7" width="14" height="14" rx="2" ry="2"></rect><polyline points="9 7 9 3 19 3 19 13 15 13"></polyline>`;
                maxBtn.setAttribute("data-tooltip", this.t("help.restore_tooltip", null, "Restore"));
            } else {
                if (this.savedBounds) {
                    this.container.style.width = this.savedBounds.w;
                    this.container.style.height = this.savedBounds.h;
                    this.container.style.left = this.savedBounds.l;
                    this.container.style.top = this.savedBounds.t;
                }
                maxIcon.innerHTML = `<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>`;
                maxBtn.setAttribute("data-tooltip", this.t("help.maximize_tooltip", null, "Maximize"));
            }
        }

        // =========================================================================
        // DATA LOADING & TOC RENDERING
        // =========================================================================

        /**
         * Fetches documentation Table of Contents from backend API and renders sidebar navigation.
         */
        async loadTOC() {
            if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.get_docs_toc !== "function") {
                this.tocContainer.innerHTML = `<div class="pyxis-help-error">${this.t("help.ipc_error", null, "Backend documentation service not available.")}</div>`;
                return;
            }

            try {
                const lang = (window.PyxisI18n && window.PyxisI18n.currentLang) || "es";
                const res = await window.pywebview.api.get_docs_toc(lang);
                if (res && res.success && Array.isArray(res.toc)) {
                    this.tocData = res.toc;
                    this.renderTOC(this.tocData);

                    // Si no hay capítulo seleccionado, cargar el primero
                    if (!this.currentChapter && this.tocData.length > 0) {
                        this.loadChapter(this.tocData[0].file);
                    }
                } else {
                    this.tocContainer.innerHTML = `<div class="pyxis-help-error">${res.error || "Failed to load index."}</div>`;
                }
            } catch (err) {
                this.tocContainer.innerHTML = `<div class="pyxis-help-error">Error: ${err.message || err}</div>`;
            }
        }

        /**
         * Renders the hierarchical Table of Contents with expandable chapter groups and node items.
         * @param {Array<object>} chapters - List of chapter descriptor objects.
         * @param {string} [filterText=""] - Optional search query to filter chapters and nodes.
         */
        renderTOC(chapters, filterText = "") {
            this.tocContainer.innerHTML = "";
            const lowerFilter = (filterText || "").trim().toLowerCase();

            chapters.forEach((ch) => {
                let matchedNodes = ch.nodes;
                let chMatch = false;

                if (lowerFilter) {
                    chMatch = ch.title.toLowerCase().includes(lowerFilter) || ch.file.toLowerCase().includes(lowerFilter);
                    matchedNodes = ch.nodes.filter(n => 
                        n.type.toLowerCase().includes(lowerFilter) || 
                        n.label.toLowerCase().includes(lowerFilter) ||
                        n.title.toLowerCase().includes(lowerFilter)
                    );
                    if (!chMatch && matchedNodes.length === 0) {
                        return; // Ocultar capítulo si nada coincide
                    }
                }

                const chGroup = document.createElement("div");
                chGroup.className = "pyxis-toc-chapter-group";
                if (lowerFilter || this.currentChapter === ch.file) {
                    chGroup.classList.add("is-expanded");
                }

                const hasNodes = ch.nodes && ch.nodes.length > 0;
                const chHeader = document.createElement("div");
                chHeader.className = `pyxis-toc-chapter-header ${this.currentChapter === ch.file ? "is-active" : ""}`;
                chHeader.innerHTML = `
                    <span class="pyxis-toc-chevron ${hasNodes ? "" : "is-empty"}">
                        <svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </span>
                    <span class="pyxis-toc-chapter-title" title="${ch.title}">${ch.title}</span>
                    ${hasNodes ? `<span class="pyxis-toc-badge">${ch.nodes.length}</span>` : ""}
                `;

                // Clic en el chevron: solo pliega / despliega la sección sin recargar ni navegar
                const chevronEl = chHeader.querySelector(".pyxis-toc-chevron");
                if (chevronEl && hasNodes) {
                    chevronEl.addEventListener("click", (e) => {
                        e.stopPropagation();
                        chGroup.classList.toggle("is-expanded");
                    });
                }

                // Clic en la cabecera:
                chHeader.addEventListener("click", () => {
                    if (this.currentChapter === ch.file) {
                        // Si ya es el capítulo actual, alternar plegado sin recargar ni reiniciar scroll
                        chGroup.classList.toggle("is-expanded");
                    } else {
                        // Si es un capítulo diferente, expandirlo y cargarlo
                        chGroup.classList.add("is-expanded");
                        this.loadChapter(ch.file);
                    }
                });

                chGroup.appendChild(chHeader);

                if (hasNodes) {
                    const nodeList = document.createElement("div");
                    nodeList.className = "pyxis-toc-node-list";

                    const nodesToRender = lowerFilter && !chMatch ? matchedNodes : ch.nodes;
                    nodesToRender.forEach((n) => {
                        const nodeItem = document.createElement("div");
                        nodeItem.className = `pyxis-toc-node-item ${this.currentNode === n.type ? "is-active" : ""}`;
                        nodeItem.setAttribute("data-node-type", n.type);
                        const nodeDisplayName = n.name || (n.type.includes("/") ? n.type.split("/")[1] : n.type);
                        const nodeTooltip = n.type + (n.label ? ` (${n.label})` : "");
                        nodeItem.innerHTML = `
                            <span class="pyxis-toc-node-bullet"></span>
                            <span class="pyxis-toc-node-name" title="${nodeTooltip}">${nodeDisplayName}</span>
                        `;

                        nodeItem.addEventListener("click", (e) => {
                            e.stopPropagation();
                            this.jumpToNode(n.type, ch.file, n.anchor);
                        });

                        nodeList.appendChild(nodeItem);
                    });

                    chGroup.appendChild(nodeList);
                }

                this.tocContainer.appendChild(chGroup);
            });

            if (this.tocContainer.children.length === 0) {
                this.tocContainer.innerHTML = `<div class="pyxis-help-empty">${this.t("help.no_results", null, "No matching topics found.")}</div>`;
            }
        }

        /**
         * Filters the Table of Contents interactively based on user query input.
         * Toggles the visibility of the search clear button.
         */
        onSearch() {
            const val = this.searchInput.value;
            const clearBtn = this.container.querySelector("#pyxis-help-search-clear");
            clearBtn.style.display = val ? "block" : "none";
            this.renderTOC(this.tocData, val);
        }

        // =========================================================================
        // CHAPTER & NODE CONTENT RENDERING
        // =========================================================================

        /**
         * Loads and displays a documentation chapter markdown document.
         * @param {string} chapterFile - Filename of the target chapter (e.g. '03 Basics.md').
         * @param {string|null} [targetAnchor=null] - Optional section/node anchor to scroll to.
         */
        async loadChapter(chapterFile, targetAnchor = null) {
            this.isProgrammaticScroll = true;
            clearTimeout(this._programmaticScrollTimer);
            this._programmaticScrollTimer = setTimeout(() => {
                this.isProgrammaticScroll = false;
            }, 800);

            this.currentChapter = chapterFile;
            if (!targetAnchor) {
                this.currentNode = null;
            }
            this.updateActiveTOC(true, true);
            this.updateBreadcrumbs();

            let content = this.chapterCache[chapterFile];
            if (!content) {
                this.contentPane.innerHTML = `<div class="pyxis-help-loading-content"><div class="pyxis-spin"></div><span>${this.t("common.loading", null, "Loading...")}</span></div>`;

                if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.get_doc_chapter !== "function") {
                    this.contentPane.innerHTML = `<div class="pyxis-help-error">${this.t("help.ipc_error", null, "Backend documentation service not available.")}</div>`;
                    return;
                }

            try {
                const lang = (window.PyxisI18n && window.PyxisI18n.currentLang) || "es";
                const res = await window.pywebview.api.get_doc_chapter(chapterFile, lang);
                if (res && res.success) {
                    content = res.content;
                    if (res.filename) {
                        this.currentChapter = res.filename;
                    }
                    this.chapterCache[this.currentChapter] = content;
                } else {
                    this.contentPane.innerHTML = `<div class="pyxis-help-error">${res.error || "Chapter not found."}</div>`;
                    return;
                }
            } catch (e) {
                this.contentPane.innerHTML = `<div class="pyxis-help-error">Error: ${e.message || e}</div>`;
                return;
            }
        }

            this.renderMarkdown(content);

            if (targetAnchor) {
                requestAnimationFrame(() => {
                    this.scrollToAnchor(targetAnchor);
                    setTimeout(() => this.scrollToAnchor(targetAnchor), 80);
                });
            } else {
                this.contentPane.scrollTo({ top: 0, behavior: "auto" });
            }
        }

        /**
         * Sanitises plain text into safe HTML entities.
         * @param {string} str - Unsanitised string.
         * @returns {string} HTML-escaped string.
         */
        escapeHtml(str) {
            return (str || "")
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        /**
         * Converts raw Markdown text into styled HTML with KaTeX math and code protection.
         * @param {string} markdownText - Raw markdown source text.
         */
        renderMarkdown(markdownText) {
            let html = "";
            if (window.marked && typeof window.marked.parse === "function") {
                // 1. Proteger bloques de código y código inline antes de procesar matemáticas
                const codeTokens = [];
                let textWithoutCode = markdownText.replace(/(```[\s\S]*?```|`[^`\n]+`)/g, (match) => {
                    const id = `@@PYXIS_CODE_${codeTokens.length}@@`;
                    codeTokens.push({ id, code: match });
                    return id;
                });

                // 2. Extraer fórmulas en bloque (display math): $$...$$
                const mathTokens = [];
                let textWithMathPlaceholders = textWithoutCode.replace(/\$\$([\s\S]+?)\$\$/g, (match, tex) => {
                    const id = `@@PYXIS_MATH_DISP_${mathTokens.length}@@`;
                    mathTokens.push({ id, tex: tex.trim(), display: true });
                    return `\n\n${id}\n\n`;
                });

                // 3. Extraer fórmulas en línea (inline math): $...$
                // Coincide con $tex$ sin espacio blanco en los extremos
                textWithMathPlaceholders = textWithMathPlaceholders.replace(/(^|[^\\])\$([^\s\$](?:\\\$|[^\$\n])*?[^\s\$]|[^\s\$])\$/g, (match, prefix, tex) => {
                    const id = `@@PYXIS_MATH_INLN_${mathTokens.length}@@`;
                    mathTokens.push({ id, tex: tex.trim(), display: false });
                    return `${prefix}${id}`;
                });

                // 4. Restaurar bloques de código originales
                codeTokens.forEach((item) => {
                    textWithMathPlaceholders = textWithMathPlaceholders.replace(item.id, () => item.code);
                });

                // 5. Parsear Markdown a HTML con Marked
                html = window.marked.parse(textWithMathPlaceholders);

                // 6. Renderizar fórmulas con KaTeX
                const katexObj = window.katex || (typeof katex !== "undefined" ? katex : null);

                mathTokens.forEach((item) => {
                    let rendered = "";
                    if (katexObj && typeof katexObj.renderToString === "function") {
                        try {
                            rendered = katexObj.renderToString(item.tex, {
                                displayMode: item.display,
                                throwOnError: false,
                                strict: false
                            });
                        } catch (e) {
                            console.warn("KaTeX render error:", e, item.tex);
                            rendered = `<code class="katex-error">${this.escapeHtml(item.tex)}</code>`;
                        }
                    } else {
                        // Fallback si KaTeX no está presente
                        rendered = item.display ? `$$${item.tex}$$` : `$${item.tex}$`;
                    }

                    if (item.display) {
                        const pRegex = new RegExp(`<p>\\s*${item.id}\\s*<\\/p>`, "g");
                        if (pRegex.test(html)) {
                            html = html.replace(pRegex, rendered);
                        } else {
                            html = html.split(item.id).join(rendered);
                        }
                    } else {
                        html = html.split(item.id).join(rendered);
                    }
                });
            } else {
                html = `<pre style="white-space:pre-wrap;font-family:monospace;">${this.escapeHtml(markdownText)}</pre>`;
            }

            this.contentPane.innerHTML = html;
            this.enhanceMarkdownElements();
        }

        /**
         * Enhances parsed HTML elements with node anchor identifiers, code copy buttons,
         * async local image loading, and GitHub-style callout alert containers.
         */
        enhanceMarkdownElements() {
            // 1. Inyectar IDs y data attributes en encabezados de nodos para navegación directa y scrollspy
            const headers = this.contentPane.querySelectorAll("h2");
            headers.forEach((h) => {
                const text = h.textContent || "";
                const m = text.match(/(?:Nodo|Node)\s+[`"']?([^`"'\(\)\n]+)[`"']?/i);
                if (m) {
                    const canonical = m[1].trim();
                    const anchor = `node-${canonical.toLowerCase().replace(/\//g, '-').replace(/\s+/g, '-')}`;
                    h.id = anchor;
                    h.classList.add("pyxis-help-node-heading");
                    h.setAttribute("data-node-type", canonical);
                }
            });

            // 2. Estilizar diagramas ASCII de nodos y añadir botones de copiado a bloques de código
            const preElements = this.contentPane.querySelectorAll("pre");
            preElements.forEach((pre) => {
                const code = pre.querySelector("code");
                const text = (code ? code.textContent : pre.textContent) || "";

                if (text.includes("+---") || text.includes("| ") || text.includes("+===") || text.includes("├───")) {
                    pre.classList.add("pyxis-ascii-diagram");
                } else {
                    // Botón para copiar código
                    const copyBtn = document.createElement("button");
                    copyBtn.className = "pyxis-code-copy-btn";
                    copyBtn.innerHTML = `<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
                    copyBtn.title = "Copy snippet";
                    copyBtn.addEventListener("click", () => {
                        navigator.clipboard.writeText(text);
                        copyBtn.classList.add("copied");
                        setTimeout(() => copyBtn.classList.remove("copied"), 1500);
                    });
                    pre.appendChild(copyBtn);
                }
            });

            // 3. Cargar imágenes locales de documentación de forma asíncrona segura
            const imgElements = this.contentPane.querySelectorAll("img");
            imgElements.forEach(async (img) => {
                let imgName = img.getAttribute("data-doc-img");
                if (!imgName) {
                    const src = img.getAttribute("src") || "";
                    if (src && !src.startsWith("data:") && !src.startsWith("http://") && !src.startsWith("https://")) {
                        imgName = src.split("/").pop();
                    }
                }
                if (imgName && window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_doc_image === "function") {
                    try {
                        const res = await window.pywebview.api.get_doc_image(imgName);
                        if (res && res.success && res.data_url) {
                            img.src = res.data_url;
                        }
                    } catch (e) {
                        console.warn("Could not load doc image:", imgName, e);
                    }
                }
            });

            // 4. Transformar alertas estilo GitHub (> [!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION])
            const lang = ((window.PyxisI18n && window.PyxisI18n.currentLang) || "es").toLowerCase();
            const isEs = lang.startsWith("es");
            const alertMeta = {
                note: {
                    label: isEs ? "Nota" : "Note",
                    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
                },
                tip: {
                    label: isEs ? "Consejo" : "Tip",
                    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M12 2a7 7 0 0 0-4 12.7c.6.6 1 1.4 1 2.3h6c0-.9.4-1.7 1-2.3A7 7 0 0 0 12 2z"></path></svg>`
                },
                important: {
                    label: isEs ? "Importante" : "Important",
                    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`
                },
                warning: {
                    label: isEs ? "Advertencia" : "Warning",
                    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`
                },
                caution: {
                    label: isEs ? "Precaución" : "Caution",
                    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`
                }
            };

            const blockquotes = this.contentPane.querySelectorAll("blockquote");
            blockquotes.forEach((bq) => {
                const firstP = bq.querySelector("p");
                if (!firstP) return;
                const rawHtml = firstP.innerHTML.trim();
                const alertMatch = rawHtml.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](?:\s*<br\s*\/?>\s*|\s*)/i);
                if (!alertMatch) return;

                const type = alertMatch[1].toLowerCase();
                const meta = alertMeta[type] || alertMeta.note;
                const remainingHtml = rawHtml.slice(alertMatch[0].length).trim();

                if (remainingHtml) {
                    firstP.innerHTML = remainingHtml;
                } else {
                    firstP.remove();
                }

                bq.classList.add("pyxis-md-alert", `pyxis-md-alert-${type}`);
                const headerDiv = document.createElement("div");
                headerDiv.className = "pyxis-md-alert-header";
                headerDiv.innerHTML = `<span class="pyxis-md-alert-icon">${meta.icon}</span><span class="pyxis-md-alert-title">${meta.label}</span>`;
                bq.insertBefore(headerDiv, bq.firstChild);
            });
        }

        /**
         * Smoothly scrolls the content container to a specified anchor or node heading.
         * @param {string} anchor - Element identifier, anchor name, or node-type token.
         */
        scrollToAnchor(anchor) {
            if (!anchor) return;
            let el = null;
            try {
                if (window.CSS && typeof CSS.escape === "function") {
                    el = this.contentPane.querySelector(`#${CSS.escape(anchor)}`) || this.contentPane.querySelector(`[name="${CSS.escape(anchor)}"]`);
                }
            } catch (e) {}

            if (!el) {
                const candidate = document.getElementById(anchor);
                if (candidate && this.contentPane.contains(candidate)) {
                    el = candidate;
                }
            }

            if (!el) {
                const allHeads = this.contentPane.querySelectorAll("h2.pyxis-help-node-heading, h2, h3, a[name]");
                for (const h of allHeads) {
                    if (h.id === anchor || h.getAttribute("name") === anchor) {
                        el = h;
                        break;
                    }
                }
            }

            if (!el && this.currentNode) {
                const curLower = String(this.currentNode).toLowerCase().trim();
                const curLeaf = curLower.includes("/") ? curLower.split("/")[1].trim() : curLower;
                const allHeads = this.contentPane.querySelectorAll("h2.pyxis-help-node-heading, [data-node-type]");
                for (const h of allHeads) {
                    const hType = (h.getAttribute("data-node-type") || "").toLowerCase().trim();
                    const hLeaf = hType.includes("/") ? hType.split("/")[1].trim() : hType;
                    if (hType === curLower || hLeaf === curLeaf) {
                        el = h;
                        break;
                    }
                }
            }

            if (el && this.contentPane) {
                this.isProgrammaticScroll = true;
                clearTimeout(this._programmaticScrollTimer);
                this._programmaticScrollTimer = setTimeout(() => {
                    this.isProgrammaticScroll = false;
                }, 800);

                const paneRect = this.contentPane.getBoundingClientRect();
                const elRect = el.getBoundingClientRect();
                const targetScroll = this.contentPane.scrollTop + (elRect.top - paneRect.top) - 16;

                this.contentPane.scrollTo({
                    top: Math.max(0, targetScroll),
                    behavior: "smooth"
                });

                // Prevent any ancestor containers from retaining unwanted scroll
                if (this.container) { this.container.scrollTop = 0; this.container.scrollLeft = 0; }
                const mainEl = this.container ? this.container.querySelector("#pyxis-help-main") : null;
                if (mainEl) { mainEl.scrollTop = 0; mainEl.scrollLeft = 0; }

                el.classList.add("pyxis-section-highlight");
                setTimeout(() => el.classList.remove("pyxis-section-highlight"), 2400);
            }
        }

        /**
         * Navigates directly to the manual entry for a canonical node type.
         * Opens the viewer window, loads the relevant chapter if needed, and scrolls to anchor.
         * @param {string} nodeType - Canonical node type (e.g. 'Basic/Coordinate System').
         * @param {string|null} [chapterFile=null] - Optional chapter filename hint.
         * @param {string|null} [nodeAnchor=null] - Optional anchor string override.
         */
        async jumpToNode(nodeType, chapterFile = null, nodeAnchor = null) {
            this.open();
            this.currentNode = nodeType;

            this.isProgrammaticScroll = true;
            clearTimeout(this._programmaticScrollTimer);
            this._programmaticScrollTimer = setTimeout(() => {
                this.isProgrammaticScroll = false;
            }, 800);

            let targetChapter = chapterFile;
            let targetAnchor = nodeAnchor || `node-${String(nodeType).toLowerCase().trim().replace(/\//g, '-').replace(/\s+/g, '-')}`;

            // Si no se proporcionó el capítulo o el anchor, consultarlo a través de la API
            if (!targetChapter || !nodeAnchor) {
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_node_doc === "function") {
                    try {
                        const lang = (window.PyxisI18n && window.PyxisI18n.currentLang) || "es";
                        const res = await window.pywebview.api.get_node_doc(nodeType, lang);
                        if (res && res.success && res.found) {
                            if (!targetChapter) targetChapter = res.chapter_file;
                            if (res.anchor) targetAnchor = res.anchor;
                        }
                    } catch (e) {}
                }
            }

            // Fallback: buscar en tocData local
            if (!targetChapter && this.tocData.length > 0) {
                for (const ch of this.tocData) {
                    if (ch.nodes) {
                        const found = ch.nodes.find(n => n.type.toLowerCase() === nodeType.toLowerCase() || (n.name && n.name.toLowerCase() === nodeType.toLowerCase()));
                        if (found) {
                            targetChapter = ch.file;
                            if (found.anchor && !nodeAnchor) targetAnchor = found.anchor;
                            break;
                        }
                    }
                }
            }

            if (targetChapter) {
                if (this.currentChapter !== targetChapter) {
                    await this.loadChapter(targetChapter, targetAnchor);
                } else {
                    this.scrollToAnchor(targetAnchor);
                }
            }

            this.updateActiveTOC(true, true);
            this.updateBreadcrumbs();
        }

        /**
         * Initialises passive requestAnimationFrame scroll listening on the markdown viewport.
         */
        setupScrollSpy() {
            if (this._scrollListenerAttached) return;
            this._scrollListenerAttached = true;

            let ticking = false;
            this.contentPane.addEventListener("scroll", () => {
                if (this.isProgrammaticScroll) return;
                if (!ticking) {
                    window.requestAnimationFrame(() => {
                        this.onContentScroll();
                        ticking = false;
                    });
                    ticking = true;
                }
            }, { passive: true });
        }

        /**
         * Evaluates viewport scroll position against rendered node headings and synchronises active node.
         * Uses a 130px visual reading threshold from the top of the container.
         */
        onContentScroll() {
            if (!this.contentPane || this.isProgrammaticScroll) return;

            const headings = Array.from(this.contentPane.querySelectorAll(".pyxis-help-node-heading"));
            if (headings.length === 0) return;

            const containerRect = this.contentPane.getBoundingClientRect();
            const containerTop = this.contentPane.scrollTop;
            const containerHeight = this.contentPane.clientHeight;
            const scrollHeight = this.contentPane.scrollHeight;

            // Si llegamos casi al final del documento, activar el último nodo del capítulo
            if (containerTop + containerHeight >= scrollHeight - 35) {
                const lastHeading = headings[headings.length - 1];
                const nodeType = lastHeading.getAttribute("data-node-type");
                if (nodeType && nodeType !== this.currentNode) {
                    this.setCurrentNodeFromScroll(nodeType);
                }
                return;
            }

            // Umbral visual de lectura: 130px desde el borde superior visible
            const activationOffset = 130;
            let activeHeading = null;

            for (let i = 0; i < headings.length; i++) {
                const h = headings[i];
                const rect = h.getBoundingClientRect();
                const relativeTop = rect.top - containerRect.top;

                if (relativeTop <= activationOffset) {
                    activeHeading = h;
                } else {
                    break;
                }
            }

            if (activeHeading) {
                const nodeType = activeHeading.getAttribute("data-node-type");
                if (nodeType && nodeType !== this.currentNode) {
                    this.setCurrentNodeFromScroll(nodeType);
                }
            } else {
                // Posición antes del primer nodo (encabezado o introducción del capítulo)
                const firstHeading = headings[0];
                const firstRect = firstHeading.getBoundingClientRect();
                if (firstRect.top - containerRect.top > activationOffset) {
                    if (this.currentNode !== null) {
                        this.setCurrentNodeFromScroll(null);
                    }
                }
            }
        }

        /**
         * Updates the active node state triggered by scrollspy and propagates changes to TOC and breadcrumbs.
         * @param {string|null} nodeType - Detected canonical node type or null if scrolled to chapter header.
         */
        setCurrentNodeFromScroll(nodeType) {
            this.currentNode = nodeType;
            this.updateActiveTOC(true, false);
            this.updateBreadcrumbs();
        }

        /**
         * Synchronises the breadcrumb navigation bar with current chapter and node titles.
         */
        updateBreadcrumbs() {
            if (!this.breadcrumbEl) return;
            const chInfo = this.tocData.find(c => c.file === this.currentChapter);
            const chTitle = chInfo ? chInfo.title : (this.currentChapter ? this.currentChapter.replace(".md", "") : "");

            let nodeDisplay = "";
            if (this.currentNode && chInfo && chInfo.nodes) {
                const curTypeLower = (this.currentNode || "").toLowerCase();
                const curLeaf = curTypeLower.includes("/") ? curTypeLower.split("/")[1].trim() : curTypeLower.trim();

                const n = chInfo.nodes.find(item => {
                    const itTypeLower = (item.type || "").toLowerCase();
                    const itLeaf = itTypeLower.includes("/") ? itTypeLower.split("/")[1].trim() : itTypeLower.trim();
                    return itTypeLower === curTypeLower || itLeaf === curLeaf;
                });

                if (n) {
                    nodeDisplay = n.name || (n.type.includes("/") ? n.type.split("/")[1] : n.type);
                } else {
                    nodeDisplay = this.currentNode.includes("/") ? this.currentNode.split("/")[1] : this.currentNode;
                }
            }

            this.breadcrumbEl.innerHTML = `
                <span class="crumb-root" data-i18n="help.manual_root">${this.t("help.manual_root", null, "Manual")}</span>
                <span class="crumb-sep">/</span>
                <span class="crumb-chapter">${chTitle}</span>
                ${nodeDisplay ? `<span class="crumb-sep">/</span><span class="crumb-node">${nodeDisplay}</span>` : ""}
            `;
        }

        /**
         * Highlights the currently active chapter and node item in the Table of Contents tree.
         * Optionally auto-scrolls the sidebar container to keep the active item within visible view.
         * @param {boolean} [scrollSidebar=true] - Whether to scroll the sidebar to reveal the active node.
         * @param {boolean} [forceExpand=false] - Whether to force accordion expansion of the active chapter group.
         */
        updateActiveTOC(scrollSidebar = true, forceExpand = false) {
            if (!this.tocContainer) return;
            const chHeaders = this.tocContainer.querySelectorAll(".pyxis-toc-chapter-header");
            chHeaders.forEach(h => h.classList.remove("is-active"));

            const nodeItems = this.tocContainer.querySelectorAll(".pyxis-toc-node-item");
            nodeItems.forEach(n => n.classList.remove("is-active"));

            let currentGroup = null;
            if (this.currentChapter) {
                const chNumMatch = String(this.currentChapter).match(/^(\d+)/);
                const chNum = chNumMatch ? parseInt(chNumMatch[1], 10) : null;

                const activeCh = Array.from(this.tocContainer.querySelectorAll(".pyxis-toc-chapter-group")).find((g, idx) => {
                    const h = g.querySelector(".pyxis-toc-chapter-title");
                    const tocItem = this.tocData && this.tocData[idx];
                    if (tocItem && tocItem.file === this.currentChapter) return true;
                    if (chNum !== null && tocItem && tocItem.chapter_num === chNum) return true;
                    return h && h.title && h.title.includes(this.currentChapter.replace(".md", ""));
                });
                if (activeCh) {
                    currentGroup = activeCh;
                    const hdr = activeCh.querySelector(".pyxis-toc-chapter-header");
                    if (hdr) hdr.classList.add("is-active");
                    if (forceExpand) {
                        activeCh.classList.add("is-expanded");
                    }
                }
            }

            if (this.currentNode && currentGroup) {
                const curTypeLower = (this.currentNode || "").toLowerCase();
                const curLeaf = curTypeLower.includes("/") ? curTypeLower.split("/")[1].trim() : curTypeLower.trim();

                const activeNode = Array.from(currentGroup.querySelectorAll(".pyxis-toc-node-item")).find(item => {
                    const itemType = (item.getAttribute("data-node-type") || "").toLowerCase();
                    const itemLeaf = itemType.includes("/") ? itemType.split("/")[1].trim() : itemType.trim();
                    return itemType === curTypeLower || itemLeaf === curLeaf;
                });

                if (activeNode) {
                    activeNode.classList.add("is-active");
                    if (forceExpand) {
                        currentGroup.classList.add("is-expanded");
                    }
                    if (scrollSidebar && currentGroup.classList.contains("is-expanded") && this.tocContainer) {
                        const tocRect = this.tocContainer.getBoundingClientRect();
                        const nodeRect = activeNode.getBoundingClientRect();
                        if (nodeRect.top < tocRect.top || nodeRect.bottom > tocRect.bottom) {
                            const targetScroll = this.tocContainer.scrollTop + (nodeRect.top - tocRect.top) - (tocRect.height / 2) + (nodeRect.height / 2);
                            this.tocContainer.scrollTo({
                                top: Math.max(0, targetScroll),
                                behavior: "smooth"
                            });
                        }
                        if (this.sidebar) { this.sidebar.scrollTop = 0; this.sidebar.scrollLeft = 0; }
                    }
                }
            }
        }
    }

    window.PyxisHelpViewer = new PyxisHelpViewer();

})(window, document);
