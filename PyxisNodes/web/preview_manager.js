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
 * @file preview_manager.js
 * @description High-performance video previewing and WebAssembly subtitle renderer manager.
 * Orchestrates ArtPlayer instances, JASSUB WASM bindings, frame-accurate timeline synchronisation,
 * floating detached players, telemetric overlays, and real-time audio playback.
 * @module PyxisPreviewManager
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        (function() {
            "use strict";
            const activePlayers = {};
            const creatingPlayers = {};

            function disarmMediaSession() {
                try {
                    if ('mediaSession' in navigator) {
                        const noop = (e) => {
                            if (e && typeof e.preventDefault === 'function') e.preventDefault();
                            if (e && typeof e.stopImmediatePropagation === 'function') e.stopImmediatePropagation();
                            return false;
                        };
                        const mediaActions = [
                            'play', 'pause', 'stop', 'playpause',
                            'seekbackward', 'seekforward', 'seekto',
                            'previoustrack', 'nexttrack', 'skipad'
                        ];
                        mediaActions.forEach(action => {
                            try {
                                navigator.mediaSession.setActionHandler(action, noop);
                            } catch (_) {}
                        });
                        try {
                            navigator.mediaSession.playbackState = 'none';
                            if (navigator.mediaSession.metadata) {
                                navigator.mediaSession.metadata = null;
                            }
                        } catch (_) {}
                    }
                } catch (e) {}
            }
            window.__pyxis_disarm_media_session = disarmMediaSession;

            function blockMediaKey(e) {
                const k = e.key || '';
                const c = e.code || '';
                const codeNum = e.keyCode || e.which || 0;
                if (
                    k === 'MediaPlayPause' || c === 'MediaPlayPause' || codeNum === 179 ||
                    k === 'MediaPlay' || c === 'MediaPlay' ||
                    k === 'MediaPause' || c === 'MediaPause' ||
                    k === 'MediaStop' || c === 'MediaStop' || codeNum === 178 ||
                    k === 'MediaTrackNext' || c === 'MediaTrackNext' || codeNum === 176 ||
                    k === 'MediaTrackPrevious' || c === 'MediaTrackPrevious' || codeNum === 177 ||
                    k === 'MediaSelect' || c === 'MediaSelect' || codeNum === 181
                ) {
                    if (typeof e.preventDefault === 'function') e.preventDefault();
                    if (typeof e.stopPropagation === 'function') e.stopPropagation();
                    if (typeof e.stopImmediatePropagation === 'function') e.stopImmediatePropagation();
                    disarmMediaSession();
                    return false;
                }
            }

            (function setupMediaKeyShield() {
                disarmMediaSession();

                ['keydown', 'keyup', 'keypress'].forEach(evtType => {
                    window.addEventListener(evtType, blockMediaKey, { capture: true, passive: false });
                    document.addEventListener(evtType, blockMediaKey, { capture: true, passive: false });
                });
            })();

            (function setupCanvasForegroundOverlay() {
                if (typeof LGraphCanvas === "undefined") return;
                const origDrawFrontCanvas = LGraphCanvas.prototype.drawFrontCanvas;

                const fgCanvasPool = [];

                function getFgCanvas(idx, zIndex) {
                    let c = fgCanvasPool[idx];
                    if (!c) {
                        if (idx === 0) {
                            c = document.getElementById("node_canvas_fg");
                        }
                        if (!c) {
                            c = document.createElement("canvas");
                            c.id = "node_canvas_fg_" + idx;
                            c.className = "pyxis-node-canvas-fg";
                            const workspace = document.querySelector(".workspace");
                            if (workspace) workspace.appendChild(c);
                        }
                        fgCanvasPool[idx] = c;
                    }
                    c.style.display = "block";
                    c.style.position = "absolute";
                    c.style.top = "0";
                    c.style.left = "0";
                    c.style.width = "100%";
                    c.style.height = "100%";
                    c.style.pointerEvents = "none";
                    c.style.overflow = "hidden";
                    c.style.zIndex = String(zIndex);
                    return c;
                }

                LGraphCanvas.prototype.drawFrontCanvas = function() {
                    origDrawFrontCanvas.apply(this, arguments);

                    if (!this.graph || !this.canvas) return;

                    const allNodes = this.graph._nodes || [];
                    if (allNodes.length === 0) {
                        fgCanvasPool.forEach(c => {
                            if (c) {
                                const ctx = c.getContext("2d");
                                if (ctx) ctx.clearRect(0, 0, c.width, c.height);
                                c.style.display = "none";
                            }
                        });
                        return;
                    }

                    const previewIndices = [];
                    for (let i = 0; i < allNodes.length; i++) {
                        const n = allNodes[i];
                        if (!n) continue;
                        const nIdStr = String(n.id);
                        const nType = (n.type || '').toLowerCase();
                        const nTitle = (n.title || '').toLowerCase();
                        const isPrev = nType.includes('preview') || nType.includes('previsualizador') || nTitle.includes('preview') || nTitle.includes('previsualizador');
                        if (isPrev) {
                            const p = activePlayers[nIdStr];
                            if (p && !p.isPinned && !p.isFullscreen) {
                                previewIndices.push(i);
                            }
                        }
                    }

                    if (previewIndices.length === 0) {
                        fgCanvasPool.forEach(c => {
                            if (c) {
                                const ctx = c.getContext("2d");
                                if (ctx) ctx.clearRect(0, 0, c.width, c.height);
                                c.style.display = "none";
                            }
                        });
                        return;
                    }

                    let activeSegmentCount = 0;
                    for (let k = 0; k < previewIndices.length; k++) {
                        const startIdx = previewIndices[k] + 1;
                        const endIdx = (k + 1 < previewIndices.length) ? previewIndices[k + 1] : (allNodes.length - 1);
                        if (startIdx > endIdx) continue;

                        const maxNodes = Math.max(1, allNodes.length);
                        const normalizedRatio = previewIndices[k] / maxNodes;
                        const segmentZ = 1000 + Math.floor(normalizedRatio * 40000) + 500;
                        const fgCanvas = getFgCanvas(activeSegmentCount, segmentZ);
                        activeSegmentCount++;

                        if (fgCanvas.width !== this.canvas.width || fgCanvas.height !== this.canvas.height) {
                            fgCanvas.width = this.canvas.width;
                            fgCanvas.height = this.canvas.height;
                        }

                        const fgCtx = fgCanvas.getContext("2d");
                        if (!fgCtx) continue;
                        fgCtx.clearRect(0, 0, fgCanvas.width, fgCanvas.height);

                        fgCtx.save();
                        this.ds.toCanvasContext(fgCtx);

                        for (let i = startIdx; i <= endIdx; i++) {
                            const node = allNodes[i];
                            if (!node) continue;

                            fgCtx.save();
                            fgCtx.translate(node.pos[0], node.pos[1]);
                            this.drawNode(node, fgCtx);
                            fgCtx.restore();
                        }

                        if (k === previewIndices.length - 1 && this.connecting_pos != null && typeof this.drawConnectingLink === "function") {
                            this.drawConnectingLink(fgCtx);
                        }

                        fgCtx.restore();
                    }

                    for (let cIdx = activeSegmentCount; cIdx < fgCanvasPool.length; cIdx++) {
                        const c = fgCanvasPool[cIdx];
                        if (c) {
                            const ctx = c.getContext("2d");
                            if (ctx) ctx.clearRect(0, 0, c.width, c.height);
                            c.style.display = "none";
                        }
                    }
                };
            })();

            (function setupPlayerLayerPointerCapture() {
                const layer = document.getElementById('pyxis-canvas-players-layer');
                if (!layer) return;

                window.addEventListener('pointerup', () => {
                    if (window.canvas) {
                        window.canvas.pointer_is_down = false;
                        window.canvas.pointer_is_double = false;
                    }
                }, true);
                window.addEventListener('mouseup', () => {
                    if (window.canvas) {
                        window.canvas.pointer_is_down = false;
                        window.canvas.pointer_is_double = false;
                    }
                }, true);

                function updatePointerEventsUnderCursor(e) {
                    if (window.__pyxisDraggingFloating) return;
                    if (!window.canvas || !window.canvas.graph) return;
                    const canvas = window.canvas;
                    const ds = canvas.ds;
                    if (!ds) return;

                    const isCanvasInteracting = Boolean(
                        canvas.node_dragged ||
                        canvas.connecting_node ||
                        canvas.dragging_canvas ||
                        canvas.resizing_node ||
                        canvas.dragging_rectangle ||
                        canvas.selected_group
                    );

                    if (isCanvasInteracting) {
                        Object.keys(activePlayers).forEach(nodeIdStr => {
                            const p = activePlayers[nodeIdStr];
                            if (!p || p.isPinned || p.isFullscreen) return;
                            if (p.wrapper && p.wrapper.style.pointerEvents !== 'none') {
                                p.wrapper.style.pointerEvents = 'none';
                            }
                            if (p.headerActions && p.headerActions.style.pointerEvents !== 'none') {
                                p.headerActions.style.pointerEvents = 'none';
                            }
                        });
                        return;
                    }

                    const b = canvas.canvas.getBoundingClientRect();
                    const canvasX = (e.clientX - b.left) / ds.scale - ds.offset[0];
                    const canvasY = (e.clientY - b.top) / ds.scale - ds.offset[1];

                    const topNode = canvas.graph.getNodeOnPos(canvasX, canvasY, canvas.visible_nodes, 15);
                    const allNodes = canvas.graph._nodes || [];
                    const topIdx = topNode ? allNodes.indexOf(topNode) : -1;

                    Object.keys(activePlayers).forEach(nodeIdStr => {
                        const p = activePlayers[nodeIdStr];
                        if (!p || p.isPinned || p.isFullscreen || !p.node) return;
                        const myIdx = allNodes.indexOf(p.node);

                        const isCoveredByTop = Boolean(topNode && topNode !== p.node && topIdx > myIdx);
                        const targetPE = isCoveredByTop ? 'none' : 'auto';

                        if (p.wrapper && p.wrapper.style.pointerEvents !== targetPE) {
                            p.wrapper.style.pointerEvents = targetPE;
                        }
                        if (p.headerActions && p.headerActions.style.pointerEvents !== targetPE) {
                            p.headerActions.style.pointerEvents = targetPE;
                        }
                    });
                }

                window.addEventListener('pointermove', updatePointerEventsUnderCursor, { passive: true });
                window.addEventListener('mousemove', updatePointerEventsUnderCursor, { passive: true });
                window.addEventListener('pointerup', updatePointerEventsUnderCursor, { passive: true });
                window.addEventListener('mouseup', updatePointerEventsUnderCursor, { passive: true });

                // Retime Mode Floating Tooltip (600ms hover delay)
                let pyxisRetimeTooltipEl = null;
                let pyxisRetimeTooltipTimer = null;
                let pyxisRetimeCurrentHover = null;

                function getOrCreateRetimeTooltipEl() {
                    if (!pyxisRetimeTooltipEl) {
                        pyxisRetimeTooltipEl = document.createElement("div");
                        pyxisRetimeTooltipEl.id = "pyxis-retime-mode-tooltip";
                        pyxisRetimeTooltipEl.className = "pyxis-retime-tooltip-card";
                        document.body.appendChild(pyxisRetimeTooltipEl);
                    }
                    return pyxisRetimeTooltipEl;
                }

                function showPyxisRetimeModeTooltip(node, modeKey, clientX, clientY) {
                    if (!node || !modeKey) return;
                    const el = getOrCreateRetimeTooltipEl();
                    const cleanKey = String(modeKey).toLowerCase().trim();
                    const tr = window.t || (window.PyxisI18n ? (k, p, d) => window.PyxisI18n.t(k, p, d) : null);

                    const title = tr ? tr(`nodes.retime_modes.${cleanKey}.title`, null, modeKey) : modeKey;
                    const formula = tr ? tr(`nodes.retime_modes.${cleanKey}.formula`, null, "") : "";
                    const desc = tr ? tr(`nodes.retime_modes.${cleanKey}.desc`, null, "") : "";

                    const escapeFunc = typeof escapeHtml === "function" ? escapeHtml : (str => String(str || "").replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m])));

                    el.innerHTML = `
                        <div class="rt-header">
                            <span class="rt-title">${escapeFunc(title)}</span>
                            <span class="rt-badge">${escapeFunc(cleanKey)}</span>
                        </div>
                        ${formula ? `<div class="rt-formula">${escapeFunc(formula)}</div>` : ''}
                        <div class="rt-desc">${escapeFunc(desc)}</div>
                    `;

                    el.style.left = '0px';
                    el.style.top = '0px';
                    el.style.display = 'block';
                    el.classList.add('visible');

                    const tipRect = el.getBoundingClientRect();
                    const margin = 12;
                    let left = clientX + margin;
                    let top = clientY + margin;

                    if (left + tipRect.width > window.innerWidth - 10) {
                        left = clientX - tipRect.width - margin;
                    }
                    if (top + tipRect.height > window.innerHeight - 10) {
                        top = clientY - tipRect.height - margin;
                    }
                    if (left < 10) left = 10;
                    if (top < 10) top = 10;

                    el.style.left = `${Math.round(left)}px`;
                    el.style.top = `${Math.round(top)}px`;
                }

                function hidePyxisRetimeModeTooltip() {
                    if (pyxisRetimeTooltipTimer) {
                        clearTimeout(pyxisRetimeTooltipTimer);
                        pyxisRetimeTooltipTimer = null;
                    }
                    pyxisRetimeCurrentHover = null;
                    if (pyxisRetimeTooltipEl) {
                        pyxisRetimeTooltipEl.classList.remove('visible');
                        pyxisRetimeTooltipEl.style.display = 'none';
                    }
                }
                window.hidePyxisRetimeModeTooltip = hidePyxisRetimeModeTooltip;

                function checkRetimePillHover(e) {
                    if (window.__pyxisDraggingFloating) {
                        hidePyxisRetimeModeTooltip();
                        return;
                    }
                    if (!window.canvas || !window.canvas.graph || !window.canvas.ds) {
                        hidePyxisRetimeModeTooltip();
                        return;
                    }
                    const canvas = window.canvas;
                    const ds = canvas.ds;
                    const b = canvas.canvas.getBoundingClientRect();

                    if (e.clientX < b.left || e.clientX > b.right || e.clientY < b.top || e.clientY > b.bottom) {
                        hidePyxisRetimeModeTooltip();
                        return;
                    }

                    const canvasX = (e.clientX - b.left) / ds.scale - ds.offset[0];
                    const canvasY = (e.clientY - b.top) / ds.scale - ds.offset[1];

                    const node = canvas.graph.getNodeOnPos(canvasX, canvasY, canvas.visible_nodes, 15);
                    if (!node) {
                        hidePyxisRetimeModeTooltip();
                        return;
                    }

                    const title = String(node.title || node.type || "");
                    const typeStr = String(node.type || "");
                    const isRetime = (title === "Retime" || title === "Time/Retime" || typeStr === "Retime" || typeStr === "Time/Retime" || typeStr.endsWith("/Retime"));
                    if (!isRetime) {
                        hidePyxisRetimeModeTooltip();
                        return;
                    }

                    const modeInfo = typeof getTitleModeInfo === "function" ? getTitleModeInfo(node) : null;
                    if (!modeInfo) {
                        hidePyxisRetimeModeTooltip();
                        return;
                    }

                    const local_pos = [canvasX - node.pos[0], canvasY - node.pos[1]];
                    if (local_pos[1] < -32 || local_pos[1] > 2) {
                        hidePyxisRetimeModeTooltip();
                        return;
                    }

                    const btnText = modeInfo.currentShort;
                    let textW = 50;
                    if (canvas && canvas.ctx) {
                        textW = canvas.ctx.measureText(btnText).width;
                    }
                    const btnW = Math.max(55, textW + 14);
                    const btnX = node.size[0] - btnW - 8;

                    if (local_pos[0] >= btnX - 4 && local_pos[0] <= btnX + btnW + 6) {
                        const hoverKey = `${node.id}_${modeInfo.currentFull}`;
                        if (pyxisRetimeCurrentHover && pyxisRetimeCurrentHover.key === hoverKey) {
                            pyxisRetimeCurrentHover.clientX = e.clientX;
                            pyxisRetimeCurrentHover.clientY = e.clientY;
                            return;
                        }

                        if (pyxisRetimeTooltipTimer) {
                            clearTimeout(pyxisRetimeTooltipTimer);
                        }
                        if (pyxisRetimeTooltipEl) {
                            pyxisRetimeTooltipEl.classList.remove('visible');
                            pyxisRetimeTooltipEl.style.display = 'none';
                        }

                        const currentFull = modeInfo.currentFull;
                        pyxisRetimeCurrentHover = {
                            key: hoverKey,
                            nodeId: node.id,
                            mode: currentFull,
                            clientX: e.clientX,
                            clientY: e.clientY
                        };

                        pyxisRetimeTooltipTimer = setTimeout(() => {
                            if (pyxisRetimeCurrentHover && pyxisRetimeCurrentHover.key === hoverKey) {
                                showPyxisRetimeModeTooltip(node, currentFull, pyxisRetimeCurrentHover.clientX, pyxisRetimeCurrentHover.clientY);
                            }
                        }, 600);
                    } else {
                        hidePyxisRetimeModeTooltip();
                    }
                }

                window.addEventListener('pointermove', checkRetimePillHover, { passive: true });
                window.addEventListener('mousemove', checkRetimePillHover, { passive: true });
                window.addEventListener('pointerdown', hidePyxisRetimeModeTooltip, { passive: true });
                window.addEventListener('mousedown', hidePyxisRetimeModeTooltip, { passive: true });
                window.addEventListener('wheel', hidePyxisRetimeModeTooltip, { passive: true });
                window.addEventListener('scroll', hidePyxisRetimeModeTooltip, { passive: true });
                window.addEventListener('blur', hidePyxisRetimeModeTooltip, { passive: true });
                window.addEventListener('contextmenu', hidePyxisRetimeModeTooltip, { passive: true });

                let isInterceptedAction = false;

                function getTargetInfo(e) {
                    if (!window.canvas || !window.canvas.graph) return null;
                    const canvas = window.canvas;
                    const ds = canvas.ds;
                    if (!ds) return null;

                    const b = canvas.canvas.getBoundingClientRect();
                    const canvasX = (e.clientX - b.left) / ds.scale - ds.offset[0];
                    const canvasY = (e.clientY - b.top) / ds.scale - ds.offset[1];

                    const topNode = canvas.graph.getNodeOnPos(canvasX, canvasY, canvas.visible_nodes, 15);
                    if (!topNode) return null;

                    const targetWrapper = e.target.closest('.pyxis-node-player-wrapper');
                    const targetHeader = e.target.closest('.pyxis-node-header-actions');
                    let targetNodeId = null;
                    if (targetWrapper) {
                        targetNodeId = targetWrapper.id.replace('pyxis-player-wrapper-', '');
                    } else if (targetHeader) {
                        targetNodeId = targetHeader.id.replace('pyxis-player-header-', '');
                    }

                    const allNodes = canvas.graph._nodes || [];
                    const topIdx = allNodes.indexOf(topNode);

                    let targetNode = null;
                    let targetIdx = -1;
                    if (targetNodeId) {
                        targetNode = canvas.graph.getNodeById(Number(targetNodeId));
                        if (targetNode) {
                            targetIdx = allNodes.indexOf(targetNode);
                        }
                    }

                    return {
                        canvas,
                        topNode,
                        topIdx,
                        targetNode,
                        targetIdx,
                        targetWrapper,
                        targetHeader,
                        isForeignTop: Boolean(targetNode && topNode !== targetNode && topIdx > targetIdx)
                    };
                }

                function handleLayerEvent(e) {
                    const info = getTargetInfo(e);

                    if (isInterceptedAction) {
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        e.preventDefault();

                        if (e.type === 'click' || e.type === 'dblclick' || e.type === 'pointerup' || e.type === 'mouseup') {
                            if (window.canvas) {
                                window.canvas.pointer_is_down = false;
                                window.canvas.pointer_is_double = false;
                                window.canvas.node_dragged = null;
                                window.canvas.resizing_node = false;
                            }
                            setTimeout(() => { isInterceptedAction = false; }, 60);
                        }
                        return;
                    }

                    if (!info) return;

                    if (info.isForeignTop) {
                        isInterceptedAction = true;
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        e.preventDefault();

                        if (info.targetWrapper) info.targetWrapper.style.pointerEvents = 'none';
                        if (info.targetHeader) info.targetHeader.style.pointerEvents = 'none';

                        if (e.type === 'pointerdown') {
                            info.canvas.pointer_is_down = false;
                            info.canvas.pointer_is_double = false;
                            info.canvas.node_dragged = null;
                            info.canvas.resizing_node = false;
                            info.canvas.processMouseDown(e);
                        }
                        return;
                    }

                    if (info.targetWrapper && e.type === 'pointerdown') {
                        const isInteractive = Boolean(
                            e.target.closest('.pyxis-custom-player-controls') || 
                            e.target.closest('.pyxis-header-buttons') || 
                            e.target.closest('.pyxis-floating-header') || 
                            e.target.closest('button') || 
                            e.target.closest('input') || 
                            e.target.closest('.art-settings') ||
                            info.targetWrapper.classList.contains('pyxis-player-fullscreen')
                        );
                        if (!isInteractive) {
                            const rect = info.targetWrapper.getBoundingClientRect();
                            const clickX = e.clientX - rect.left;
                            const clickY = e.clientY - rect.top;
                            if (clickX > rect.width - 32 && clickY > rect.height - 32) {
                                isInterceptedAction = true;
                                e.stopPropagation();
                                e.stopImmediatePropagation();
                                e.preventDefault();
                                info.canvas.pointer_is_down = false;
                                info.canvas.pointer_is_double = false;
                                info.canvas.node_dragged = null;
                                info.canvas.resizing_node = false;
                                info.canvas.processMouseDown(e);
                                return;
                            }
                        }
                    }

                    if (e.type === 'pointerdown' && info.targetNode) {
                        if (info.canvas.current_node !== info.targetNode) {
                            info.canvas.selectNode(info.targetNode);
                            info.canvas.bringToFront(info.targetNode);
                            if (info.canvas.setDirty) info.canvas.setDirty(true, true);
                            if (typeof updateInNodePlayersPosition === 'function') {
                                updateInNodePlayersPosition();
                            }
                        }
                    }
                }

                ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click', 'dblclick', 'contextmenu'].forEach(evtName => {
                    layer.addEventListener(evtName, handleLayerEvent, true);
                });
            })();

            function updatePreviewMetadataBadges(nodeIdStr, info) {
                if (info && typeof info.scaled_border_and_shadow === 'boolean' && activePlayers[nodeIdStr]) {
                    activePlayers[nodeIdStr].scaledBorderAndShadow = info.scaled_border_and_shadow;
                }
                const metaContainer = document.getElementById('pyxis-player-meta-' + nodeIdStr);
                if (!metaContainer) return;
                const mediaMeta = (info && info.media_meta) ? info.media_meta : null;
                if (!mediaMeta) {
                    metaContainer.innerHTML = '';
                    return;
                }

                const videoCodec = mediaMeta.video_codec || '';
                const resolution = mediaMeta.resolution || (info.res_x && info.res_y ? `${info.res_x}x${info.res_y}` : '');
                const fpsStr = mediaMeta.fps_str || (info.fps ? `${Number(info.fps).toFixed(2)} fps` : '');
                const audioHzStr = mediaMeta.audio_hz_str || '';
                const bitrateStr = mediaMeta.bitrate_str || '';
                const audioChannels = mediaMeta.audio_channels || '';

                const items = [];
                if (videoCodec && videoCodec !== 'NO VIDEO' && videoCodec !== 'SIN VÍDEO') {
                    items.push({ text: videoCodec, key: 'preview.meta_codec_tooltip', fallback: 'Video codec' });
                }
                if (resolution && resolution !== 'N/A') {
                    items.push({ text: resolution, key: 'preview.meta_res_tooltip', fallback: 'Native resolution' });
                }
                if (fpsStr && fpsStr !== 'N/A') {
                    items.push({ text: fpsStr, key: 'preview.meta_fps_tooltip', fallback: 'Frames per second (FPS)' });
                }
                if (audioHzStr && audioHzStr !== 'N/A' && audioHzStr !== 'NO AUDIO' && audioHzStr !== 'No audio' && audioHzStr !== 'SIN AUDIO' && audioHzStr !== 'Sin audio') {
                    items.push({ text: audioHzStr, key: 'preview.meta_hz_tooltip', fallback: 'Audio sample rate' });
                }
                if (bitrateStr && bitrateStr !== 'N/A') {
                    items.push({ text: bitrateStr, key: 'preview.meta_bitrate_tooltip', fallback: 'Total bitrate' });
                }
                if (audioChannels && audioChannels !== 'N/A') {
                    items.push({ text: audioChannels, key: 'preview.meta_channels_tooltip', fallback: 'Audio channels' });
                }

                metaContainer.innerHTML = items.map(item => {
                    const tip = window.t ? window.t(item.key) : item.fallback;
                    return `<span class="pyxis-meta-item" aria-label="${escapeHtml(tip)}" data-i18n-aria-label="${item.key}">${escapeHtml(item.text)}</span>`;
                }).join('<span class="pyxis-meta-sep">, </span>');

                if (typeof attachPyxisDelayTooltip === 'function') {
                    metaContainer.querySelectorAll('.pyxis-meta-item').forEach(span => {
                        const tipKey = span.getAttribute('data-i18n-aria-label');
                        const fallback = span.getAttribute('aria-label');
                        attachPyxisDelayTooltip(span, () => {
                            return window.t && tipKey ? window.t(tipKey) : (span.getAttribute('aria-label') || fallback || '');
                        }, 800);
                    });
                }
            }

            function updateInNodePlayersPosition() {
                if (!window.graph || !window.canvas) return;
                const scale = window.canvas.ds.scale || 1;
                const tx = window.canvas.ds.offset[0] || 0;
                const ty = window.canvas.ds.offset[1] || 0;

                const nodes = window.graph._nodes || [];
                const currentPreviewNodes = {};

                nodes.forEach((node, nodeIdx) => {
                    if (!node || node.id === undefined) return;
                    const nodeIdStr = String(node.id);
                    const nType = (node.type || '').toLowerCase();
                    const nTitle = (node.title || '').toLowerCase();
                    if (nType.includes('preview') || nType.includes('previsualizador') || nTitle.includes('previsualizador') || nTitle.includes('preview')) {
                        currentPreviewNodes[nodeIdStr] = node;

                        const isCollapsed = Boolean(node.flags && node.flags.collapsed);
                        const p = activePlayers[nodeIdStr];
                        if (p) {
                            p.node = node;
                        }

                        if (isCollapsed) {
                            if (p) {
                                p.wasCollapsed = true;
                                if (p.headerActions) {
                                    p.headerActions.style.display = 'none';
                                }
                                if (p.wrapper && !p.isPinned) {
                                    p.wrapper.style.display = 'none';
                                }
                            }
                            return;
                        }

                        if (p && p.wasCollapsed) {
                            p.wasCollapsed = false;
                            p.lastW = null;
                            p.lastH = null;
                            if (p.wrapper && !p.isPinned) {
                                p.wrapper.style.display = '';
                            }
                            if (p.art && typeof p.art.resize === 'function') {
                                try { p.art.resize(); } catch(e) {}
                            }
                            if (p.jassub && typeof p.jassub.resize === 'function') {
                                try { p.jassub.resize(); } catch(e) {}
                            }
                        }

                        if (!p || !p.isPinned) {
                            const isCustomZoom = Boolean(
                                (p && p.transformState && p.transformState.isCustom) ||
                                (node.properties && node.properties.viewport_custom)
                            );
                            const curAspect = getNodePreviewAspectRatio(node);
                            const minW = getDynamicMinPreviewWidth(curAspect);
                            const curW = (node.size && node.size[0] && node.size[0] >= minW) ? node.size[0] : 520;
                            const calcH = calculatePrevisualizadorNodeHeight(curW, curAspect);
                            const targetH = (isCustomZoom && node.size && node.size[1] >= 140)
                                ? node.size[1]
                                : ((isCustomZoom && node.properties && node.properties.previewer_height && Number(node.properties.previewer_height) >= 140)
                                    ? Number(node.properties.previewer_height)
                                    : calcH);
                            const isResizingNode = Boolean(window.canvas && window.canvas.resizing_node === node);
                            if (!isResizingNode) {
                                if (!node.size || node.size[0] < minW || node.size[1] < 140 || (!isCustomZoom && Math.abs(node.size[1] - targetH) > 1.5)) {
                                    node.size = [curW, targetH];
                                    if (node.properties) {
                                        node.properties.previewer_width = curW;
                                        node.properties.previewer_height = targetH;
                                    }
                                    if (typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                                }
                            }
                        } else {
                            const isResizingNode = Boolean(window.canvas && window.canvas.resizing_node === node);
                            if (!isResizingNode) {
                                const minSz = (typeof node.computeSize === 'function') ? node.computeSize() : [284, 54];
                                const minW = Math.max(270, minSz ? minSz[0] : 284);
                                const curW = (node.size && node.size[0]) ? node.size[0] : minW;
                                const targetW = Math.max(curW, minW);
                                if (!node.size || node.size[0] < minW || node.size[1] !== 54) {
                                    node.size = [targetW, 54];
                                    if (typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                                }
                            }
                        }

                        if (!activePlayers[nodeIdStr] && !creatingPlayers[nodeIdStr]) {
                            createInNodePlayer(node);
                        }

                        const pUpdated = activePlayers[nodeIdStr];
                        if (pUpdated) {
                            pUpdated.node = node;
                            const isNodeSelected = Boolean(node.is_selected);
                            if (pUpdated.wasSelected && !isNodeSelected && pUpdated.wrapper) {
                                const expC = pUpdated.wrapper.querySelector('.pyxis-pbar-container.is-heatmap-expanded');
                                if (expC && typeof expC._collapseHeatmap === 'function') {
                                    expC._collapseHeatmap();
                                } else if (expC) {
                                    expC.classList.remove('is-heatmap-expanded');
                                }
                            }
                            pUpdated.wasSelected = isNodeSelected;
                            if (pUpdated.isFullscreen || pUpdated.inTelemetryCockpit) {
                                return;
                            }

                            const maxNodes = Math.max(1, nodes.length);
                            const normalizedRatio = nodeIdx / maxNodes;
                            const baseZ = 1000 + Math.floor(normalizedRatio * 40000);

                            if (pUpdated.headerActions) {
                                pUpdated.headerActions.style.display = '';
                                pUpdated.headerActions.classList.toggle('is-pinned', Boolean(pUpdated.isPinned));
                                pUpdated.headerActions.style.zIndex = String(baseZ + 2);

                                let leftStart = 138;
                                if (node.widgets && node.widgets.length > 0) {
                                    const wOutput = node.widgets.find(w => w && (w.name === "Output IDs" || w.property === "output_ids"));
                                    if (wOutput && typeof getInlineBoxWidth === 'function') {
                                        const wBox = getInlineBoxWidth(node, wOutput, "Output IDs", "output_ids", node.size[0]);
                                        leftStart = pUpdated.isPinned ? (22 + wBox + 8) : Math.max(135, 22 + wBox + 10);
                                    }
                                }
                                const headX = (node.pos[0] + leftStart + tx) * scale;
                                const headY = (node.pos[1] + 8 + ty) * scale;
                                const headW = pUpdated.isPinned ? 164 : Math.max(168, node.size[0] - leftStart - 10);
                                pUpdated.headerActions.style.left = headX + 'px';
                                pUpdated.headerActions.style.top = headY + 'px';
                                pUpdated.headerActions.style.width = headW + 'px';
                                pUpdated.headerActions.style.transform = `scale(${scale})`;
                                pUpdated.headerActions.style.transformOrigin = 'top left';
                                pUpdated.headerActions.style.visibility = 'visible';
                                pUpdated.headerActions.style.opacity = '1';
                                pUpdated.headerActions.style.pointerEvents = 'auto';
                            }
                            if (pUpdated.wrapper && !pUpdated.isPinned) {
                                pUpdated.wrapper.style.display = '';
                                pUpdated.wrapper.style.zIndex = pUpdated.hasFFmpegMissing ? String(baseZ + 30) : String(baseZ);

                                const topOffset = 46;
                                const sideMargin = 10;
                                const bottomMargin = 10;
                                const screenX = (node.pos[0] + sideMargin + tx) * scale;
                                const screenY = (node.pos[1] + topOffset + ty) * scale;
                                const unscaledW = Math.max(100, node.size[0] - (sideMargin * 2));
                                const unscaledH = Math.max(100, node.size[1] - topOffset - bottomMargin);

                                pUpdated.wrapper.style.left = screenX + 'px';
                                pUpdated.wrapper.style.top = screenY + 'px';
                                pUpdated.wrapper.style.width = unscaledW + 'px';
                                pUpdated.wrapper.style.height = unscaledH + 'px';
                                pUpdated.wrapper.style.transform = 'scale(' + scale + ')';
                                pUpdated.wrapper.style.transformOrigin = 'top left';
                                pUpdated.wrapper.style.visibility = 'visible';
                                pUpdated.wrapper.style.opacity = '1';
                                pUpdated.wrapper.style.pointerEvents = '';

                                if (pUpdated.lastW !== node.size[0] || pUpdated.lastH !== node.size[1]) {
                                    pUpdated.lastW = node.size[0];
                                    pUpdated.lastH = node.size[1];
                                    const isResizing = Boolean(
                                        (window.canvas && window.canvas.resizing_node === node) ||
                                        pUpdated.isResizing ||
                                        window.__pyxisDraggingFloating
                                    );
                                    if (!isResizing) {
                                        if (pUpdated.art && typeof pUpdated.art.resize === 'function') {
                                            try { pUpdated.art.resize(); } catch(e) {}
                                        }
                                        if (pUpdated.jassub && typeof pUpdated.jassub.resize === 'function') {
                                            try { pUpdated.jassub.resize(); } catch(e) {}
                                        }
                                    } else if (getNodeRenderMode(node) === "mpv") {
                                        scheduleMpvSharpResize(nodeIdStr, 60);
                                    }
                                    if (typeof pUpdated.applyTransform === 'function') {
                                        pUpdated.applyTransform();
                                    }
                                }
                                if (pUpdated.lastCanvasScale !== scale) {
                                    const prevScale = pUpdated.lastCanvasScale;
                                    pUpdated.lastCanvasScale = scale;
                                    if (prevScale !== undefined && getNodeRenderMode(node) === "mpv") {
                                        scheduleMpvSharpResize(nodeIdStr, 90);
                                    }
                                }
                            }
                        }
                    }
                });

                Object.keys(activePlayers).forEach(nodeIdStr => {
                    if (!currentPreviewNodes[nodeIdStr]) {
                        destroyInNodePlayer(nodeIdStr);
                    }
                });

                const allWrappers = document.querySelectorAll('.pyxis-node-player-wrapper');
                allWrappers.forEach(wrap => {
                    const wId = wrap.id.replace('pyxis-player-wrapper-', '');
                    if (!currentPreviewNodes[wId]) {
                        if (wrap.parentNode) wrap.parentNode.removeChild(wrap);
                    }
                });
                const allHeaders = document.querySelectorAll('.pyxis-node-header-actions');
                allHeaders.forEach(head => {
                    const hId = head.id.replace('pyxis-player-header-', '');
                    if (!currentPreviewNodes[hId]) {
                        if (head.parentNode) head.parentNode.removeChild(head);
                    }
                });
            }

            function logPlayer(msg) {
                console.log("[PYXIS PLAYER]", msg);
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.log_player_event === "function") {
                    window.pywebview.api.log_player_event(msg);
                }
            }

            function getPreviewBounds(nodeIdStr) {
                const p = activePlayers[nodeIdStr];
                const curSource = (p && p.node && p.node.properties && p.node.properties.preview_source) || "base";
                const pInfo = (curSource === "aegisub" && window.PyxisPreviewConfigAegi) 
                    ? window.PyxisPreviewConfigAegi 
                    : ((curSource === "base" && window.PyxisPreviewConfigBase) ? window.PyxisPreviewConfigBase : window.PyxisPreviewConfig) || {};

                const winStart = Math.max(0, Number(pInfo.clip_start_sec) || 0);
                let winEnd = Number(pInfo.clip_end_sec);
                if (!winEnd || winEnd <= winStart) {
                    const dur = Number(pInfo.clip_duration_sec) || 15.0;
                    winEnd = winStart + dur;
                }
                if (p && p.art && p.art.duration && p.art.duration > winStart) {
                    winEnd = Math.min(winEnd, p.art.duration);
                }
                const winDur = Math.max(0.1, winEnd - winStart);
                return { winStart, winEnd, winDur };
            }

            function getRenderModeSvgHtml(mode) {
                if (mode === "mpv") {
                    return `<svg class="pyxis-icon-rendermode-mpv" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">` +
                        `<circle cx="12" cy="12" r="10" stroke-width="2.0"/>` +
                        `<polygon points="10.2 8.4 16.2 12 10.2 15.6 10.2 8.4" stroke-width="2.0"/>` +
                        `</svg>`;
                }
                return `<svg class="pyxis-icon-rendermode-ts" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">` +
                    `<circle cx="12" cy="12" r="10" stroke-width="2.0"/>` +
                    `<path d="M7.0 8.8h4.2M9.1 8.8v6.4" stroke-width="1.85"/>` +
                    `<path d="M16.8 9.8c0-.7-.7-1.0-1.8-1.0-1.1 0-1.9.5-1.9 1.5 0 .9.7 1.3 1.9 1.7 1.2.4 1.9.8 1.9 1.8 0 1.0-.8 1.5-2.0 1.5-1.1 0-1.9-.4-1.9-1.1" stroke-width="1.85"/>` +
                    `</svg>`;
            }

            function getNodeRenderMode(nodeOrId) {
                let targetNode = null;
                if (nodeOrId && typeof nodeOrId === "object") {
                    targetNode = nodeOrId;
                } else if (nodeOrId !== undefined && nodeOrId !== null) {
                    const idStr = String(nodeOrId);
                    const p = activePlayers[idStr];
                    targetNode = (p && p.node) ? p.node : null;
                    if (!targetNode && window.graph && typeof window.graph.getNodeById === "function") {
                        targetNode = window.graph.getNodeById(Number(idStr)) || window.graph.getNodeById(idStr);
                    }
                }
                const rawMode = (targetNode && targetNode.properties && targetNode.properties.render_mode) || "typesetting";
                return rawMode === "mpv" ? "mpv" : "typesetting";
            }

            function getRenderModeTooltipKey(mode) {
                return mode === "mpv" ? "preview.render_mode_mpv_tooltip" : "preview.render_mode_ts_tooltip";
            }

            function getRenderModeTooltipText(mode) {
                const key = getRenderModeTooltipKey(mode);
                if (window.t) {
                    const tr = window.t(key);
                    if (tr && tr !== key) return tr;
                }
                return mode === "mpv"
                    ? "Render Mode: mpv Sharpness & Aspect - Click to switch to Typesetting (TS)"
                    : "Render Mode: 1:1 Typesetting (TS) - Click to switch to mpv view";
            }

            function formatAssForRenderMode(rawAss, mode, optScaledBas) {
                if (!rawAss || typeof rawAss !== "string") {
                    return rawAss || "";
                }
                const lines = rawAss.split(/\r?\n/);
                const out = [];
                let inScriptInfo = false;
                let hasScaledBas = false;
                const effectiveBas = (optScaledBas !== undefined && optScaledBas !== null)
                    ? Boolean(optScaledBas)
                    : true;

                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];
                    const trimmed = line.trim();
                    if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
                        if (inScriptInfo && !hasScaledBas) {
                            out.push(`ScaledBorderAndShadow: ${effectiveBas ? "yes" : "no"}`);
                            hasScaledBas = true;
                        }
                        inScriptInfo = (trimmed.toLowerCase() === "[script info]");
                        out.push(line);
                        continue;
                    }
                    if (inScriptInfo) {
                        if (mode === "mpv" && /^layoutres[xy]\s*:/i.test(trimmed)) {
                            continue;
                        }
                        if (/^scaledborderandshadow\s*:/i.test(trimmed)) {
                            hasScaledBas = true;
                            out.push(`ScaledBorderAndShadow: ${effectiveBas ? "yes" : "no"}`);
                            continue;
                        }
                    }
                    out.push(line);
                }
                if (inScriptInfo && !hasScaledBas) {
                    out.push(`ScaledBorderAndShadow: ${effectiveBas ? "yes" : "no"}`);
                }
                return out.join("\n");
            }

            function syncJassubDomPlacement(p, mode, optJassub, optRoot) {
                const root = optRoot || (p && p.art && p.art.template && p.art.template.$player) || (p && p.box) || null;
                const jassubObj = optJassub || (p && p.jassub) || null;
                const jassubParent = (jassubObj && jassubObj._canvasParent) || (root ? root.querySelector("div.JASSUB") : null);
                if (!root || !jassubParent) return;

                if (mode === "mpv") {
                    const frame = root.querySelector(".pyxis-video-frame");
                    if (frame && jassubParent.parentNode !== frame) {
                        frame.appendChild(jassubParent);
                    }
                    jassubParent.classList.add("is-mpv-screen-space");
                } else {
                    jassubParent.classList.remove("is-mpv-screen-space");
                    jassubParent.style.removeProperty("--mpv-jassub-w");
                    jassubParent.style.removeProperty("--mpv-jassub-h");
                    jassubParent.style.removeProperty("--mpv-jassub-ml");
                    jassubParent.style.removeProperty("--mpv-jassub-mt");
                    jassubParent.style.transform = "";
                    const viewport = root.querySelector(".pyxis-video-viewport");
                    if (viewport && jassubParent.parentNode !== viewport) {
                        viewport.appendChild(jassubParent);
                    }
                }
            }

            function syncMpvJassubOverlay(boxEl, nodeIdStr, safeNW, safeNH, scaleVal, panX, panY) {
                if (!boxEl) return;
                const p = activePlayers[String(nodeIdStr)];
                const mode = getNodeRenderMode((p && p.node) || nodeIdStr);
                const jassubParent = (p && p.jassub && p.jassub._canvasParent) || boxEl.querySelector("div.JASSUB");
                if (!jassubParent) return;

                if (mode !== "mpv") {
                    syncJassubDomPlacement(p, "typesetting", p && p.jassub, boxEl);
                    return;
                }

                const frame = boxEl.querySelector(".pyxis-video-frame");
                if (frame && jassubParent.parentNode !== frame) {
                    frame.appendChild(jassubParent);
                }
                jassubParent.classList.add("is-mpv-screen-space");

                const effScale = (isFinite(scaleVal) && scaleVal > 0) ? scaleVal : 1.0;
                const displayW = Math.max(1, safeNW * effScale);
                const displayH = Math.max(1, safeNH * effScale);
                jassubParent.style.setProperty("--mpv-jassub-w", displayW + "px");
                jassubParent.style.setProperty("--mpv-jassub-h", displayH + "px");
                jassubParent.style.setProperty("--mpv-jassub-ml", (-displayW / 2) + "px");
                jassubParent.style.setProperty("--mpv-jassub-mt", (-displayH / 2) + "px");
                jassubParent.style.transform = `translate3d(${panX || 0}px, ${panY || 0}px, 0px)`;
            }

            function forceJassubPausedRefresh(jassub) {
                if (!jassub) return;
                try {
                    if (jassub._video && jassub._video.paused && typeof jassub.setCurrentTime === "function") {
                        const curT = (jassub._video.currentTime || 0) + (jassub.timeOffset || 0);
                        jassub.setCurrentTime(true, curT);
                    }
                } catch (e) {}
            }

            function scheduleMpvSharpResize(nodeId, delayMs = 60) {
                const idStr = String(nodeId);
                const p = activePlayers[idStr];
                if (!p) return;
                if (p.mpvResizeTimer) {
                    clearTimeout(p.mpvResizeTimer);
                    p.mpvResizeTimer = null;
                }
                if (delayMs <= 0) {
                    if (p.jassub && typeof p.jassub.resize === "function") {
                        try { p.jassub.resize(0, 0, 0, 0, true); } catch (e) {}
                        forceJassubPausedRefresh(p.jassub);
                    }
                    return;
                }
                p.mpvResizeTimer = setTimeout(() => {
                    p.mpvResizeTimer = null;
                    const pLatest = activePlayers[idStr];
                    if (!pLatest || !pLatest.jassub) return;
                    if (getNodeRenderMode(pLatest.node || idStr) !== "mpv") return;
                    if (typeof pLatest.jassub.resize === "function") {
                        try { pLatest.jassub.resize(0, 0, 0, 0, true); } catch (e) {}
                        forceJassubPausedRefresh(pLatest.jassub);
                    }
                }, delayMs);
            }

            async function updateJassubTrack(jassub, assText, optNodeId, skipRawSave = false) {
                if (!jassub || !assText) return;
                try {
                    logPlayer("updateJassubTrack start, assText len: " + assText.length);
                    let resolvedPlayer = (optNodeId !== undefined && optNodeId !== null) ? activePlayers[String(optNodeId)] : null;
                    if (!resolvedPlayer) {
                        const keys = Object.keys(activePlayers);
                        for (let i = 0; i < keys.length; i++) {
                            if (activePlayers[keys[i]] && activePlayers[keys[i]].jassub === jassub) {
                                resolvedPlayer = activePlayers[keys[i]];
                                break;
                            }
                        }
                    }
                    if (resolvedPlayer && !skipRawSave) {
                        resolvedPlayer.rawAssContent = assText;
                    }
                    const activeMode = getNodeRenderMode(resolvedPlayer ? resolvedPlayer.node : optNodeId);
                    if (resolvedPlayer) {
                        syncJassubDomPlacement(resolvedPlayer, activeMode, jassub);
                        if (typeof resolvedPlayer.applyTransform === "function") {
                            try { resolvedPlayer.applyTransform(); } catch (e) {}
                        }
                    }
                    const scaledBas = (resolvedPlayer && typeof resolvedPlayer.scaledBorderAndShadow === 'boolean')
                        ? resolvedPlayer.scaledBorderAndShadow
                        : (window.PyxisPreviewConfig && typeof window.PyxisPreviewConfig.scaled_border_and_shadow === 'boolean'
                            ? window.PyxisPreviewConfig.scaled_border_and_shadow
                            : true);
                    const effectiveAss = formatAssForRenderMode(assText, activeMode, scaledBas);
                    if (jassub._loaded) {
                        try { await jassub._loaded; } catch (e) {}
                    }
                    if (typeof jassub.setTrack === 'function') {
                        jassub.setTrack(effectiveAss);
                        logPlayer("setTrack executed successfully (" + activeMode + ").");
                    } else if (typeof jassub.setTrackByUrl === 'function') {
                        const blob = new Blob([effectiveAss], { type: 'text/plain;charset=utf-8' });
                        const blobUrl = URL.createObjectURL(blob);
                        jassub.setTrackByUrl(blobUrl);
                        logPlayer("setTrackByUrl executed successfully (" + activeMode + ").");
                    }
                    if (typeof jassub.resize === 'function') {
                        try { jassub.resize(0, 0, 0, 0, true); } catch (e) {}
                    }
                    forceJassubPausedRefresh(jassub);
                } catch (e) {
                    console.warn("[Pyxis JASSUB track update warning]", e);
                    logPlayer("updateJassubTrack exception: " + String(e));
                }
            }

            function convertFontEntryToUint8Array(fontEntry) {
                if (!fontEntry) return null;
                let dataUrl = "";
                if (typeof fontEntry === "string") {
                    dataUrl = fontEntry;
                } else if (typeof fontEntry === "object") {
                    dataUrl = fontEntry.data || fontEntry.data_url || "";
                }
                if (!dataUrl || typeof dataUrl !== "string") return null;
                const commaIdx = dataUrl.indexOf(",");
                if (commaIdx === -1) return null;
                try {
                    const base64Str = dataUrl.substring(commaIdx + 1);
                    const binStr = window.atob(base64Str);
                    const len = binStr.length;
                    const bytes = new Uint8Array(len);
                    for (let i = 0; i < len; i++) {
                        bytes[i] = binStr.charCodeAt(i);
                    }
                    return bytes;
                } catch (e) {
                    console.error("[Pyxis Font Decode Error]", e);
                    return null;
                }
            }

            function injectFontsIntoJassub(jassub, fontsMap) {
                if (!jassub) {
                    console.error("[Pyxis Font Chivato] ERROR: injectFontsIntoJassub llamado sin instancia de JASSUB!");
                    return;
                }
                if (!fontsMap || typeof fontsMap !== "object") {
                    console.warn("[Pyxis Font Chivato] AVISO: injectFontsIntoJassub llamado con fontsMap vacío/inválido:", fontsMap);
                    return;
                }
                window.__pyxis_last_fonts_map = fontsMap;
                const fontKeys = Object.keys(fontsMap);
                console.log("[Pyxis Font Loader] Injecting fonts into JASSUB. Total keys:", fontKeys.length, fontKeys);
                if (!window.__pyxis_injected_fonts) {
                    window.__pyxis_injected_fonts = new Set();
                }
                const processed = new Set();
                let successCount = 0;
                for (const [fName, fEntry] of Object.entries(fontsMap)) {
                    const cacheKey = (typeof fEntry === 'object' && fEntry.path) ? fEntry.path : fName.toLowerCase();
                    if (processed.has(cacheKey) || window.__pyxis_injected_fonts.has(cacheKey)) continue;
                    processed.add(cacheKey);

                    const u8 = convertFontEntryToUint8Array(fEntry);
                    if (!u8) {
                        console.error("[Pyxis Font Loader] ERROR decoding binary for font '" + fName + "'. Entry:", fEntry);
                        continue;
                    }
                    try {
                        if (typeof jassub.addFont === "function") {
                            jassub.addFont(u8);
                            window.__pyxis_injected_fonts.add(cacheKey);
                            successCount++;
                            logPlayer("Font Loader -> Success addFont in JASSUB: " + fName + " (" + u8.length + " bytes)");
                        } else {
                            console.error("[Pyxis Font Loader] ERROR: jassub.addFont is NOT a function!");
                        }
                    } catch (e) {
                        console.error("[Pyxis Font Loader] EXCEPTION invoking jassub.addFont for " + fName + ":", e);
                    }
                }
                console.log("[Pyxis Font Loader] Injection summary: " + successCount + " binary fonts loaded into libass.");
            }

            function attachPyxisDelayTooltip(el, tooltipText, delayMs = 1000) {
                if (!el) return;
                let hoverTimer = null;
                let tooltipEl = null;

                function showTooltip() {
                    if (tooltipEl) return;
                    tooltipEl = document.createElement("div");
                    tooltipEl.className = "pyxis-btn-tooltip";
                    tooltipEl.innerText = typeof tooltipText === "function" ? tooltipText() : tooltipText;

                    const rect = el.getBoundingClientRect();
                    tooltipEl.style.position = "fixed";
                    tooltipEl.style.left = (rect.left + rect.width / 2) + "px";
                    tooltipEl.style.top = (rect.top - 28) + "px";
                    document.body.appendChild(tooltipEl);

                    requestAnimationFrame(() => {
                        if (tooltipEl) tooltipEl.classList.add("visible");
                    });
                }

                function hideTooltip() {
                    if (hoverTimer) {
                        clearTimeout(hoverTimer);
                        hoverTimer = null;
                    }
                    if (tooltipEl) {
                        if (tooltipEl.parentNode) tooltipEl.parentNode.removeChild(tooltipEl);
                        tooltipEl = null;
                    }
                }

                el.addEventListener("mouseenter", () => {
                    hideTooltip();
                    hoverTimer = setTimeout(showTooltip, delayMs);
                });

                el.addEventListener("mouseleave", hideTooltip);
                el.addEventListener("mousedown", hideTooltip);
                el.addEventListener("click", hideTooltip);
            }

            async function createInNodePlayer(node) {
                if (!node || node.id === undefined) return;
                const nodeIdStr = String(node.id);
                if (activePlayers[nodeIdStr] || creatingPlayers[nodeIdStr] || document.getElementById('pyxis-player-wrapper-' + nodeIdStr)) {
                    return;
                }
                creatingPlayers[nodeIdStr] = true;
                logPlayer("createInNodePlayer initiated for node: " + nodeIdStr);

                try {
                    const layer = document.getElementById('pyxis-canvas-players-layer');
                    if (!layer) return;

                    if (node.inputs && node.inputs[0]) {
                        node.inputs[0].multiple = true;
                    }

                    const curSource = (node.properties && node.properties.preview_source) || "base";
                    const isBase = curSource === "base";
                    const initialHasAegisub = Boolean(window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub);
                    const sourceTip = isBase 
                        ? (window.t ? window.t("preview.source_base_tooltip") : "Source: Base Template (preview_base.ass) - Click to switch to Aegisub") 
                        : (window.t ? window.t("preview.source_aegisub_tooltip") : "Source: Open File in Aegisub - Click to switch to Base");
                    const curRenderMode = getNodeRenderMode(node);
                    const isMpvInit = curRenderMode === "mpv";
                    const renderModeTipKey = getRenderModeTooltipKey(curRenderMode);
                    const renderModeTip = getRenderModeTooltipText(curRenderMode);

                    const wrapper = document.createElement('div');
                    wrapper.id = 'pyxis-player-wrapper-' + nodeIdStr;
                    wrapper.className = 'pyxis-node-player-wrapper';
                    wrapper.style.visibility = 'hidden';
                    wrapper.style.opacity = '0';
                    wrapper.style.pointerEvents = 'none';

                    const headerActions = document.createElement('div');
                    headerActions.id = 'pyxis-player-header-' + nodeIdStr;
                    headerActions.className = 'pyxis-node-header-actions';
                    headerActions.style.visibility = 'hidden';
                    headerActions.style.opacity = '0';
                    headerActions.style.pointerEvents = 'none';
                    headerActions.innerHTML = `
                        <div class="pyxis-node-header-meta" id="pyxis-player-meta-${nodeIdStr}"></div>
                        <div class="pyxis-header-buttons">
                            <button id="btn-source-${nodeIdStr}" class="pyxis-header-icon-btn pyxis-btn-source ${!initialHasAegisub ? 'disabled' : ''}" aria-label="${sourceTip}" data-i18n-aria-label="${isBase ? 'preview.source_base_tooltip' : 'preview.source_aegisub_tooltip'}" ${!initialHasAegisub ? 'disabled' : ''}>
                                <img src="${isBase ? 'CD.png' : 'Aegisub_logo.png'}" alt="${curSource}" />
                            </button>
                            <button id="btn-rendermode-${nodeIdStr}" class="pyxis-header-icon-btn pyxis-btn-rendermode ${isMpvInit ? 'is-mpv-mode' : ''}" aria-label="${renderModeTip}" data-i18n-aria-label="${renderModeTipKey}">
                                ${getRenderModeSvgHtml(curRenderMode)}
                            </button>
                            <button id="btn-pin-${nodeIdStr}" class="pyxis-header-icon-btn" aria-label="${window.t ? window.t('preview.pin') : 'Pin player to screen'}" data-i18n-aria-label="preview.pin">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 17v5"/>
                                    <path d="M9 2v3l-2 5v3h10v-3l-2-5V2z"/>
                                </svg>
                            </button>
                            <button id="btn-refresh-${nodeIdStr}" class="pyxis-header-icon-btn pyxis-btn-refresh-preview" aria-label="${window.t ? window.t('preview.refresh') : 'Refresh Previewer'}" data-i18n-aria-label="preview.refresh">
                                <svg class="pyxis-icon-refresh" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
                                </svg>
                                <svg class="pyxis-icon-cancel" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                            <button id="btn-hardsub-${nodeIdStr}" class="pyxis-header-icon-btn" aria-label="${window.t ? window.t('preview.hardsub') : 'Render Hardsub with FFmpeg'}" data-i18n-aria-label="preview.hardsub">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M4 11v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8H4z"/>
                                    <path d="M4 11V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v6H4z"/>
                                    <path d="M9 3l-2 8"/>
                                    <path d="M15 3l-2 8"/>
                                </svg>
                            </button>
                        </div>
                    `;

                    const btnSource = headerActions.querySelector('#btn-source-' + nodeIdStr);
                    const btnRenderMode = headerActions.querySelector('#btn-rendermode-' + nodeIdStr);
                    const btnPin = headerActions.querySelector('#btn-pin-' + nodeIdStr);
                    const btnRefresh = headerActions.querySelector('#btn-refresh-' + nodeIdStr);
                    const btnHardsub = headerActions.querySelector('#btn-hardsub-' + nodeIdStr);

                    if (btnSource) {
                        btnSource.onclick = () => window.PyxisNodePlayerManager.togglePreviewSource(nodeIdStr);
                        attachPyxisDelayTooltip(btnSource, () => {
                            const p = activePlayers[nodeIdStr];
                            const curSrc = (p && p.node && p.node.properties && p.node.properties.preview_source) || "base";
                            const k = curSrc === "base" ? "preview.source_base_tooltip" : "preview.source_aegisub_tooltip";
                            return window.t ? window.t(k) : (curSrc === "base" ? "Source: Base Template (preview_base.ass) - Click to switch to Aegisub" : "Source: Open File in Aegisub - Click to switch to Base");
                        }, 1000);
                    }
                    if (btnRenderMode) {
                        btnRenderMode.onclick = () => window.PyxisNodePlayerManager.togglePreviewRenderMode(nodeIdStr);
                        attachPyxisDelayTooltip(btnRenderMode, () => getRenderModeTooltipText(getNodeRenderMode(nodeIdStr)), 1000);
                    }
                    if (btnPin) {
                        btnPin.onclick = () => window.PyxisNodePlayerManager.togglePinPreview(nodeIdStr);
                        attachPyxisDelayTooltip(btnPin, () => (window.t ? window.t("preview.pin") : "Pin player to screen"), 1000);
                    }
                    if (btnRefresh) {
                        btnRefresh.onclick = () => window.PyxisNodePlayerManager.refreshPreview(nodeIdStr);
                        attachPyxisDelayTooltip(btnRefresh, () => {
                            if (btnRefresh.classList.contains("is-refreshing")) {
                                return window.t ? window.t("preview.cancel_refresh") : "Cancel preview generation";
                            }
                            return window.t ? window.t("preview.refresh") : "Refresh Previewer";
                        }, 600);
                    }
                    if (btnHardsub) {
                        btnHardsub.onclick = () => window.PyxisNodePlayerManager.renderHardsub(nodeIdStr);
                        attachPyxisDelayTooltip(btnHardsub, () => (window.t ? window.t("preview.hardsub") : "Render Hardsub with FFmpeg"), 1000);
                    }

                    const box = document.createElement('div');
                    box.id = 'pyxis-artplayer-container-' + nodeIdStr;
                    box.className = 'pyxis-artplayer-box';
                    box.style.backgroundColor = '#000000';

                    const topProgress = document.createElement('div');
                    topProgress.id = 'pyxis-top-progress-' + nodeIdStr;
                    topProgress.className = 'pyxis-player-top-progress-track';
                    topProgress.innerHTML = `<div class="pyxis-player-top-progress-bar"></div>`;
                    box.appendChild(topProgress);

                    const loadingBackdrop = document.createElement('div');
                    loadingBackdrop.id = 'pyxis-player-loading-' + nodeIdStr;
                    loadingBackdrop.className = 'pyxis-player-loading-backdrop is-loading';
                    loadingBackdrop.innerHTML = `
                        <img src="loadingB.gif" class="pyxis-player-loading-gif" alt="${window.t ? window.t('common.loading') : 'Loading...'}" data-i18n-alt="common.loading">
                        <div class="pyxis-player-loading-text" data-i18n="preview.loading">${window.t ? window.t('preview.loading') : 'Loading preview...'}</div>
                        <div class="pyxis-player-loading-progress-box">
                            <div class="pyxis-player-loading-progress-track is-indeterminate">
                                <div class="pyxis-player-loading-progress-bar"></div>
                            </div>
                            <div class="pyxis-player-loading-progress-meta">
                                <span class="pyxis-player-loading-progress-pct">0%</span>
                                <span class="pyxis-player-loading-progress-info"></span>
                            </div>
                        </div>
                        <button type="button" class="pyxis-player-loading-cancel-btn" aria-label="${window.t ? window.t('preview.cancel') : 'Cancel'}">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                            <span data-i18n="preview.cancel">${window.t ? window.t('preview.cancel') : 'Cancel'}</span>
                        </button>
                    `;

                    const cancelBtn = loadingBackdrop.querySelector('.pyxis-player-loading-cancel-btn');
                    if (cancelBtn) {
                        cancelBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.cancelPreview === 'function') {
                                window.PyxisNodePlayerManager.cancelPreview(nodeIdStr);
                            }
                        });
                    }

                    const scale = (window.graphcanvas && window.graphcanvas.ds && window.graphcanvas.ds.scale) || 1.0;
                    const tx = (window.graphcanvas && window.graphcanvas.ds && window.graphcanvas.ds.offset) ? window.graphcanvas.ds.offset[0] : 0;
                    const ty = (window.graphcanvas && window.graphcanvas.ds && window.graphcanvas.ds.offset) ? window.graphcanvas.ds.offset[1] : 0;
                    const nodePos = (node && node.pos && Array.isArray(node.pos)) ? node.pos : [0, 0];
                    const nodeSize = (node && node.size && Array.isArray(node.size)) ? node.size : [520, 330];

                    let leftStart = 138;
                    if (node.widgets && node.widgets.length > 0) {
                        const wOutput = node.widgets.find(w => w && (w.name === "Output IDs" || w.property === "output_ids"));
                        if (wOutput && typeof getInlineBoxWidth === 'function') {
                            const wBox = getInlineBoxWidth(node, wOutput, "Output IDs", "output_ids", nodeSize[0]);
                            leftStart = Math.max(135, 22 + wBox + 10);
                        }
                    }
                    const headX = (nodePos[0] + leftStart + tx) * scale;
                    const headY = (nodePos[1] + 8 + ty) * scale;
                    const headW = Math.max(168, nodeSize[0] - leftStart - 10);

                    headerActions.style.left = headX + 'px';
                    headerActions.style.top = headY + 'px';
                    headerActions.style.width = headW + 'px';
                    headerActions.style.transform = `scale(${scale})`;
                    headerActions.style.transformOrigin = 'top left';

                    const topOffset = 46;
                    const sideMargin = 10;
                    const bottomMargin = 10;
                    const screenX = (nodePos[0] + sideMargin + tx) * scale;
                    const screenY = (nodePos[1] + topOffset + ty) * scale;
                    const unscaledW = Math.max(100, nodeSize[0] - (sideMargin * 2));
                    const unscaledH = Math.max(100, nodeSize[1] - topOffset - bottomMargin);

                    wrapper.style.left = screenX + 'px';
                    wrapper.style.top = screenY + 'px';
                    wrapper.style.width = unscaledW + 'px';
                    wrapper.style.height = unscaledH + 'px';
                    wrapper.style.transform = 'scale(' + scale + ')';
                    wrapper.style.transformOrigin = 'top left';

                    wrapper.appendChild(box);
                    wrapper.appendChild(loadingBackdrop);
                    layer.appendChild(wrapper);
                    layer.appendChild(headerActions);

                    const topProgressBar = topProgress.querySelector('.pyxis-player-top-progress-bar');

                    activePlayers[nodeIdStr] = {
                        wrapper: wrapper,
                        box: box,
                        headerActions: headerActions,
                        node: node,
                        loadingBackdrop: loadingBackdrop,
                        topProgressTrack: topProgress,
                        topProgressBar: topProgressBar,
                        isInitializing: true,
                        hasRefreshed: false
                    };
                    if (typeof updateInNodePlayersPosition === 'function') {
                        updateInNodePlayersPosition();
                    }

                    function handleCornerClick(e) {
                        const rect = wrapper.getBoundingClientRect();
                        const clickX = e.clientX - rect.left;
                        const clickY = e.clientY - rect.top;
                        if (clickX > rect.width - 32 && clickY > rect.height - 32) {
                            return;
                        }
                        e.stopPropagation();
                    }
                    wrapper.addEventListener('mousedown', handleCornerClick);
                    wrapper.addEventListener('pointerdown', handleCornerClick);
                    headerActions.addEventListener('mousedown', function(e) { e.stopPropagation(); });
                    headerActions.addEventListener('pointerdown', function(e) { e.stopPropagation(); });

                    let artInstance = null;
                    let jassubInstance = null;

                    let videoUrl = '';
                    let audioUrl = '';
                    let initialAss = '';
                    let fontUrl = '';
                    let fontsMap = {};
                    let previewInfo = null;

                    function getNativeResolution() {
                        const vid = (artInstance && artInstance.template) ? artInstance.template.$video : (box ? box.querySelector('video') : null);
                        const pActive = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                            ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                            : null;
                        const curSource = (pActive && pActive.node && pActive.node.properties && pActive.node.properties.preview_source) || (node.properties && node.properties.preview_source) || "base";
                        const pInfo = (curSource === "aegisub" && window.PyxisPreviewConfigAegi) 
                            ? window.PyxisPreviewConfigAegi 
                            : ((curSource === "base" && window.PyxisPreviewConfigBase) ? window.PyxisPreviewConfigBase : window.PyxisPreviewConfig) || previewInfo || {};

                        const hasRealVideo = Boolean(pInfo && pInfo.real_video_file && vid && vid.videoWidth > 0 && vid.videoHeight > 0);
                        let nW = hasRealVideo ? vid.videoWidth : (pInfo.res_x || 1920);
                        const nH = hasRealVideo ? vid.videoHeight : (pInfo.res_y || 1080);
                        const storageW = (pInfo && pInfo.storage_x) ? pInfo.storage_x : (hasRealVideo ? vid.videoWidth : (pInfo.res_x || 1920));
                        const storageH = (pInfo && pInfo.storage_y) ? pInfo.storage_y : (hasRealVideo ? vid.videoHeight : (pInfo.res_y || 1080));
                        if (hasRealVideo && pInfo && pInfo.media_meta && pInfo.media_meta.sar && pInfo.media_meta.sar !== "1:1") {
                            let darNum = 0.0;
                            const rawDar = pInfo.media_meta.display_aspect_ratio;
                            if (typeof rawDar === 'number') {
                                darNum = rawDar;
                            } else if (typeof rawDar === 'string' && rawDar.trim()) {
                                if (rawDar.includes(':') || rawDar.includes('/')) {
                                    const parts = rawDar.split(/[:\/]/);
                                    if (parts.length === 2) {
                                        const n = parseFloat(parts[0]);
                                        const d = parseFloat(parts[1]);
                                        if (n > 0 && d > 0) darNum = n / d;
                                    }
                                } else {
                                    darNum = parseFloat(rawDar);
                                }
                            }
                            if (!darNum || !isFinite(darNum) || darNum <= 0) {
                                const sarParts = String(pInfo.media_meta.sar).split(/[:\/]/);
                                if (sarParts.length === 2) {
                                    const sNum = parseFloat(sarParts[0]);
                                    const sDen = parseFloat(sarParts[1]);
                                    if (sNum > 0 && sDen > 0) {
                                        darNum = (storageW / storageH) * (sNum / sDen);
                                    }
                                }
                            }
                            if (darNum > 0 && isFinite(darNum)) {
                                nW = Math.max(1, Math.round(nH * darNum));
                            }
                        }
                        return { w: nW, h: nH, storageW: storageW, storageH: storageH, hasRealVideo: hasRealVideo };
                    }

                    if (window.pywebview && window.pywebview.api) {
                        const curSource = (node.properties && node.properties.preview_source) || "base";
                        const initTargets = (window.graph) ? resolveConnectedOutputsForPreview(node) : [];
                        const serialized = (window.graph) ? window.graph.serialize() : null;

                        if (typeof window.pywebview.api.check_ffmpeg_status === 'function') {
                            try {
                                const ffStatus = await window.pywebview.api.check_ffmpeg_status();
                                if (ffStatus && !ffStatus.available) {
                                    showPlayerFFmpegMissingBanner(nodeIdStr);
                                    if (typeof window.showFFmpegDownloadModal === 'function') {
                                        window.showFFmpegDownloadModal(async (downloaded) => {
                                            if (!downloaded) return;
                                            await loadPreviewMediaAfterFFmpeg(nodeIdStr);
                                        });
                                    }
                                }
                            } catch (e) {
                                console.warn("[Pyxis check_ffmpeg_status warning]", e);
                            }
                        }

                        if (typeof window.pywebview.api.get_preview_info === 'function') {
                            previewInfo = await window.pywebview.api.get_preview_info(curSource, initTargets, serialized);
                        }
                        if (typeof window.pywebview.api.get_preview_video_data_url === 'function') {
                            videoUrl = await window.pywebview.api.get_preview_video_data_url(curSource, initTargets, serialized);
                        }

                        // If user cancelled while fetching Aegisub media, or if Aegisub video URL returned empty, fall back to base source
                        if (curSource === "aegisub" && (window.__pyxis_is_preview_cancelled || !videoUrl)) {
                            window.__pyxis_is_preview_cancelled = false;
                            curSource = "base";
                            if (node.properties) {
                                node.properties.preview_source = "base";
                            }
                            const hasAegi = (initialHasAegisub !== undefined)
                                ? initialHasAegisub
                                : Boolean(window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub);
                            updateSourceButtonUI(nodeIdStr, "base", hasAegi);
                            if (typeof window.pywebview.api.get_preview_info === 'function') {
                                previewInfo = await window.pywebview.api.get_preview_info("base", initTargets, serialized);
                            }
                            if (typeof window.pywebview.api.get_preview_video_data_url === 'function') {
                                videoUrl = await window.pywebview.api.get_preview_video_data_url("base", initTargets, serialized);
                            }
                        }

                        if (typeof window.pywebview.api.get_preview_audio_data_url === 'function') {
                            audioUrl = await window.pywebview.api.get_preview_audio_data_url(curSource, initTargets, serialized);
                        }

                        if (typeof window.pywebview.api.get_initial_base_ass === 'function') {
                            initialAss = await window.pywebview.api.get_initial_base_ass(curSource, initTargets, serialized);
                        }
                        if (typeof window.pywebview.api.get_preview_fonts_map === 'function') {
                            fontsMap = await window.pywebview.api.get_preview_fonts_map(curSource);
                        } else if (typeof window.pywebview.api.get_preview_font_data_url === 'function') {
                            fontUrl = await window.pywebview.api.get_preview_font_data_url(curSource);
                        }
                    }
                    logPlayer("Data loaded - videoUrl len: " + videoUrl.length + ", initialAss len: " + initialAss.length + ", fonts count: " + Object.keys(fontsMap || {}).length);

                    if (!videoUrl) {
                        videoUrl = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';
                    }

                    if (previewInfo) {
                        window.PyxisPreviewConfig = previewInfo;
                        const cSrc = (node.properties && node.properties.preview_source) || "base";
                        if (cSrc === "base") window.PyxisPreviewConfigBase = previewInfo;
                        if (cSrc === "aegisub") window.PyxisPreviewConfigAegi = previewInfo;
                        if (previewInfo.aspect_ratio) {
                            node.preview_aspect_ratio = previewInfo.aspect_ratio;
                            if (node.properties) node.properties.preview_aspect_ratio = previewInfo.aspect_ratio;
                        }
                        updatePreviewMetadataBadges(nodeIdStr, previewInfo);
                        const pExisting = activePlayers[nodeIdStr];
                        if (!pExisting || !pExisting.isPinned) {
                            const isCustomZoom = Boolean(
                                (pExisting && pExisting.transformState && pExisting.transformState.isCustom) ||
                                (node.properties && node.properties.viewport_custom)
                            );
                            const dynMinW = getDynamicMinPreviewWidth(previewInfo.aspect_ratio);
                            let targetW = (node.size && node.size[0] && node.size[0] >= dynMinW) ? node.size[0] : 520;
                            if (node.properties && node.properties.previewer_width) {
                                targetW = Math.max(dynMinW, Number(node.properties.previewer_width));
                            } else if (previewInfo.res_x && (!node.size || node.size[0] < dynMinW)) {
                                const scaled = Math.round(previewInfo.res_x * 0.50);
                                targetW = Math.max(dynMinW, Math.min(1280, scaled));
                            }
                            let targetH;
                            if (isCustomZoom && node.properties && node.properties.previewer_height && Number(node.properties.previewer_height) >= 140) {
                                targetH = Number(node.properties.previewer_height);
                            } else if (isCustomZoom && node.size && node.size[1] >= 140) {
                                targetH = node.size[1];
                            } else {
                                targetH = calculatePrevisualizadorNodeHeight(targetW, previewInfo.aspect_ratio);
                            }
                            if (!node.size || node.size[0] !== targetW || node.size[1] < 140 || (!isCustomZoom && Math.abs(node.size[1] - targetH) > 1.5)) {
                                node.size = [targetW, targetH];
                                if (node.properties) {
                                    node.properties.previewer_width = targetW;
                                    node.properties.previewer_height = targetH;
                                }
                                if (typeof node.setDirtyCanvas === 'function') {
                                    node.setDirtyCanvas(true, true);
                                }
                                if (window.canvas) {
                                    window.canvas.setDirty(true, true);
                                    window.canvas.draw(true, true);
                                }
                            }
                        } else {
                            const minSz = (typeof node.computeSize === 'function') ? node.computeSize() : [284, 54];
                            const minW = Math.max(270, minSz ? minSz[0] : 284);
                            const curW = (node.size && node.size[0]) ? node.size[0] : minW;
                            node.size = [Math.max(curW, minW), 54];
                            if (typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                            if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                        }
                    }

                    if (window.Artplayer) {
                        try {
                            window.Artplayer.DBCLICK_FULLSCREEN = false;
                            window.Artplayer.CONTEXTMENU = false;
                        } catch(e) {}
                        box.addEventListener('contextmenu', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation();
                        }, true);
                        artInstance = new Artplayer({
                            container: box,
                            url: videoUrl,
                            loop: true,
                            hotkey: false,
                            setting: true,
                            playbackRate: true,
                            contextmenu: [],
                            fullscreen: false,
                            fullscreenWeb: false,
                            pip: false,
                            autoSize: false,
                            volume: 0.5,
                            isLive: false,
                            moreVideoAttr: {
                                crossOrigin: 'anonymous',
                                playsInline: true,
                                loop: true
                            }
                        });
                        logPlayer("Artplayer instance created for node: " + nodeIdStr);

                        artInstance.on('ready', async function() {
                            logPlayer("Artplayer onReady event fired for node: " + nodeIdStr);
                            if (loadingBackdrop) {
                                loadingBackdrop.classList.remove('is-loading');
                            }
                            if (artInstance.template && artInstance.template.$video) {
                                try {
                                    artInstance.template.$video.crossOrigin = 'anonymous';
                                    artInstance.template.$video.loop = true;
                                    const vidEl = artInstance.template.$video;
                                    vidEl.loop = true;

                                    const playerEl = artInstance.template.$player;
                                    if (playerEl && vidEl && vidEl.parentNode) {
                                        let frame = playerEl.querySelector('.pyxis-video-frame');
                                        if (!frame) {
                                            frame = document.createElement('div');
                                            frame.className = 'pyxis-video-frame';
                                            vidEl.parentNode.insertBefore(frame, vidEl);
                                        }
                                        let viewport = frame.querySelector('.pyxis-video-viewport');
                                        if (!viewport) {
                                            viewport = document.createElement('div');
                                            viewport.className = 'pyxis-video-viewport';
                                            frame.appendChild(viewport);
                                        }
                                        if (vidEl.parentNode !== viewport) {
                                            viewport.appendChild(vidEl);
                                        }
                                        const existingJassub = playerEl.querySelector('div.JASSUB');
                                        if (existingJassub) {
                                            syncJassubDomPlacement(activePlayers[nodeIdStr], getNodeRenderMode(node), null, playerEl);
                                        }
                                    }

                                    const onVideoMeta = () => {
                                        const b = getPreviewBounds(nodeIdStr);
                                        if (b.winStart > 0 && artInstance.currentTime < b.winStart - 0.05) {
                                            try { artInstance.currentTime = b.winStart; } catch(e) {}
                                        }
                                        const { w: effectiveW, h: effectiveH, hasRealVideo } = getNativeResolution();
                                        const detectedAspect = (effectiveH > 0) ? (effectiveW / effectiveH) : (16 / 9);

                                        node.preview_aspect_ratio = detectedAspect;
                                        if (node.properties) node.properties.preview_aspect_ratio = detectedAspect;
                                        const curSource = (node.properties && node.properties.preview_source) || "base";
                                        if (curSource === "base" && window.PyxisPreviewConfigBase) {
                                            window.PyxisPreviewConfigBase.aspect_ratio = detectedAspect;
                                            window.PyxisPreviewConfigBase.res_x = effectiveW;
                                            window.PyxisPreviewConfigBase.res_y = effectiveH;
                                        } else if (curSource === "aegisub" && window.PyxisPreviewConfigAegi) {
                                            window.PyxisPreviewConfigAegi.aspect_ratio = detectedAspect;
                                            window.PyxisPreviewConfigAegi.res_x = effectiveW;
                                            window.PyxisPreviewConfigAegi.res_y = effectiveH;
                                        }
                                        if (window.PyxisPreviewConfig) {
                                            window.PyxisPreviewConfig.aspect_ratio = detectedAspect;
                                            window.PyxisPreviewConfig.res_x = effectiveW;
                                            window.PyxisPreviewConfig.res_y = effectiveH;
                                        }
                                        const pActive = activePlayers[nodeIdStr];
                                        if (!pActive || !pActive.isPinned) {
                                            const isCustomZoom = Boolean(
                                                (pActive && pActive.transformState && pActive.transformState.isCustom) ||
                                                (node.properties && node.properties.viewport_custom)
                                            );
                                            const dynMinW = getDynamicMinPreviewWidth(detectedAspect);
                                            let curW = (node.size && node.size[0] && node.size[0] >= dynMinW) ? node.size[0] : 520;
                                            if (node.properties && node.properties.previewer_width) {
                                                curW = Math.max(dynMinW, Number(node.properties.previewer_width));
                                            }
                                            let curH;
                                            if (isCustomZoom && node.properties && node.properties.previewer_height) {
                                                curH = Number(node.properties.previewer_height);
                                            } else if (isCustomZoom && node.size && node.size[1]) {
                                                curH = node.size[1];
                                            } else {
                                                curH = calculatePrevisualizadorNodeHeight(curW, detectedAspect);
                                            }
                                            node.size = [curW, curH];
                                            if (node.properties) {
                                                node.properties.previewer_width = curW;
                                                node.properties.previewer_height = curH;
                                            }
                                            if (pActive) {
                                                pActive.lastW = curW;
                                                pActive.lastH = curH;
                                                if (pActive.wrapper && !pActive.isPinned) {
                                                    pActive.wrapper.style.width = Math.max(100, curW - 20) + 'px';
                                                    pActive.wrapper.style.height = Math.max(100, curH - 56) + 'px';
                                                }
                                                if (typeof pActive.applyTransform === 'function') {
                                                    pActive.applyTransform();
                                                }
                                            }
                                            if (typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                                            if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                        } else if (pActive && pActive.isPinned) {
                                            if (pActive.wrapper) {
                                                const rect = pActive.wrapper.getBoundingClientRect();
                                                const curFloatingW = Math.max(340, rect.width || parseFloat(pActive.wrapper.style.width) || (pActive.savedFloatingWidth ? parseFloat(pActive.savedFloatingWidth) : 560));
                                                const curFloatingH = Math.max(200, rect.height || parseFloat(pActive.wrapper.style.height) || (pActive.savedFloatingHeight ? parseFloat(pActive.savedFloatingHeight) : 380));
                                                pActive.wrapper.style.setProperty('width', curFloatingW + 'px', 'important');
                                                pActive.wrapper.style.setProperty('height', curFloatingH + 'px', 'important');
                                                pActive.savedFloatingWidth = curFloatingW + 'px';
                                                pActive.savedFloatingHeight = curFloatingH + 'px';
                                            }
                                            if (typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                                            if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                        }
                                        if (typeof updateInNodePlayersPosition === 'function') {
                                            updateInNodePlayersPosition();
                                        }
                                        if (pActive) {
                                            if (pActive.art && typeof pActive.art.resize === 'function') {
                                                try { pActive.art.resize(); } catch(e) {}
                                            }
                                            if (typeof pActive.applyTransform === 'function') {
                                                pActive.applyTransform();
                                            }
                                            if (pActive.jassub && typeof pActive.jassub.resize === 'function') {
                                                try { pActive.jassub.resize(); } catch(e) {}
                                            }
                                        }
                                    };
                                    if (vidEl.readyState >= 1) {
                                        onVideoMeta();
                                    }
                                    vidEl.addEventListener('loadedmetadata', onVideoMeta);
                                    artInstance.on('video:loadedmetadata', onVideoMeta);
                                    artInstance.on('restart', onVideoMeta);

                                    const enforceNoMediaSession = () => {
                                        disarmMediaSession();
                                    };
                                    ['play', 'playing', 'pause', 'timeupdate', 'loadeddata', 'loadedmetadata', 'canplay', 'volumechange'].forEach(evt => {
                                        vidEl.addEventListener(evt, enforceNoMediaSession);
                                    });
                                    ['keydown', 'keyup', 'keypress'].forEach(evt => {
                                        vidEl.addEventListener(evt, blockMediaKey, { capture: true, passive: false });
                                        if (box) box.addEventListener(evt, blockMediaKey, { capture: true, passive: false });
                                    });

                                    artInstance.template.$video.addEventListener('play', function(e) {
                                        disarmMediaSession();
                                        if (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.isDaemonSuspended) {
                                            try { artInstance.pause(); } catch(err) {}
                                            try { artInstance.template.$video.pause(); } catch(err) {}
                                            e.preventDefault();
                                            e.stopPropagation();
                                        }
                                    });
                                } catch(e) {}
                            }
                            setupCustomPlayerControls(artInstance, nodeIdStr, node, wrapper);
                            setupPlayerViewportZoomPan(artInstance, nodeIdStr, box);

                            if (artInstance.template && artInstance.template.$progress) {
                                const releaseProgressDrag = () => {
                                    try { artInstance.emit('document:mouseup'); } catch(e) {}
                                };
                                artInstance.template.$progress.addEventListener('pointerup', releaseProgressDrag);
                                window.addEventListener('mouseup', releaseProgressDrag);
                                window.addEventListener('pointerup', releaseProgressDrag);
                                window.addEventListener('blur', releaseProgressDrag);
                            }
                            if (window.JASSUB) {
                                try {
                                    const jassOpts = {
                                        video: artInstance.template.$video,
                                        workerUrl: 'libs/jassub/jassub-worker.js',
                                        wasmUrl: location.origin + '/libs/jassub/jassub-worker.wasm',
                                        offscreenRender: false,
                                        onDemandRender: false,
                                        debug: false,
                                        prescaleFactor: 1.0,
                                        prescaleHeightLimit: 4320,
                                        maxRenderHeight: 0
                                    };
                                    if (activePlayers[nodeIdStr]) {
                                        activePlayers[nodeIdStr].rawAssContent = initialAss || "";
                                    }
                                    const initRenderMode = getNodeRenderMode(node);
                                    if (initialAss) {
                                        const initBas = (previewInfo && typeof previewInfo.scaled_border_and_shadow === 'boolean')
                                            ? previewInfo.scaled_border_and_shadow
                                            : (window.PyxisPreviewConfig && typeof window.PyxisPreviewConfig.scaled_border_and_shadow === 'boolean'
                                                ? window.PyxisPreviewConfig.scaled_border_and_shadow
                                                : true);
                                        jassOpts.subContent = formatAssForRenderMode(initialAss, initRenderMode, initBas);
                                    }
                                    const fontByteArrays = [];
                                    const fontUrlsMap = {};
                                    const processedSizes = new Set();
                                    if (fontsMap && typeof fontsMap === 'object') {
                                        for (const [fName, fEntry] of Object.entries(fontsMap)) {
                                            const u8 = convertFontEntryToUint8Array(fEntry);
                                            if (u8 && !processedSizes.has(u8.length)) {
                                                processedSizes.add(u8.length);
                                                fontByteArrays.push(u8);
                                            }
                                            if (typeof fEntry === 'object' && fEntry.http_url) {
                                                fontUrlsMap[fName.toLowerCase()] = fEntry.http_url;
                                            }
                                        }
                                    }
                                    if (fontByteArrays.length > 0) {
                                        jassOpts.fonts = fontByteArrays;
                                    }
                                    if (Object.keys(fontUrlsMap).length > 0) {
                                        jassOpts.availableFonts = Object.assign({}, fontUrlsMap);
                                    }
                                    const primaryFontClean = (previewInfo && previewInfo.font_name) ? String(previewInfo.font_name).toLowerCase() : 'arial';
                                    if (jassOpts.availableFonts && jassOpts.availableFonts[primaryFontClean]) {
                                        jassOpts.fallbackFont = primaryFontClean;
                                    }
                                    jassubInstance = new JASSUB(jassOpts);
                                    if (activePlayers[nodeIdStr]) {
                                        activePlayers[nodeIdStr].jassub = jassubInstance;
                                    }

                                    // Intercept _demandRender to prevent RVFC storage dimension flutter on anamorphic videos
                                    if (typeof jassubInstance._demandRender === 'function') {
                                        const origDemandRender = jassubInstance._demandRender.bind(jassubInstance);
                                        jassubInstance._demandRender = function(opts) {
                                            if (!opts) return;
                                            try {
                                                const { w: nW, h: nH } = getNativeResolution();
                                                const safeNW = Math.max(1, nW || 1920);
                                                const safeNH = Math.max(1, nH || 1080);
                                                // Ensure RVFC decoded storage dimensions (e.g. 720x480) match effective
                                                // display aspect ratio so libass worker doesn't oscillate on each video frame
                                                opts.width = safeNW;
                                                opts.height = safeNH;
                                            } catch (_) {}
                                            return origDemandRender(opts);
                                        };
                                    }

                                    // Intercept resize to support both 1:1 Typesetting canvas fidelity and Screen-Space mpv rasterization
                                    jassubInstance.resize = function(w, h, top, left, paused) {
                                        try {
                                            const { w: nW, h: nH } = getNativeResolution();
                                            const safeNW = Math.max(1, nW || 1920);
                                            const safeNH = Math.max(1, nH || 1080);
                                            const renderMode = getNodeRenderMode(nodeIdStr);

                                            if (renderMode === "mpv") {
                                                const dpr = Math.min(3.0, Math.max(1.0, window.devicePixelRatio || 1.0));
                                                const rect = this._canvasParent ? this._canvasParent.getBoundingClientRect() : null;
                                                let cssW = (rect && rect.width > 2) ? rect.width : 0;
                                                let cssH = (rect && rect.height > 2) ? rect.height : 0;
                                                if (cssW <= 0 || cssH <= 0) {
                                                    const pCur = activePlayers[nodeIdStr];
                                                    const actScale = (pCur && pCur.transformState && pCur.transformState.actualScale > 0)
                                                        ? pCur.transformState.actualScale
                                                        : 1.0;
                                                    const cScale = (pCur && !pCur.isPinned && !pCur.isFullscreen && !pCur.inTelemetryCockpit && window.graphcanvas && window.graphcanvas.ds)
                                                        ? (window.graphcanvas.ds.scale || 1.0)
                                                        : 1.0;
                                                    cssW = safeNW * actScale * cScale;
                                                    cssH = safeNH * actScale * cScale;
                                                }
                                                let targetW = Math.max(2, Math.round(cssW * dpr));
                                                let targetH = Math.max(2, Math.round(cssH * dpr));
                                                const MAX_MPV_DIM = 3840;
                                                if (targetW > MAX_MPV_DIM || targetH > MAX_MPV_DIM) {
                                                    const clampRatio = MAX_MPV_DIM / Math.max(targetW, targetH);
                                                    targetW = Math.max(2, Math.round(targetW * clampRatio));
                                                    targetH = Math.max(2, Math.round(targetH * clampRatio));
                                                }

                                                // In mpv mode, ensure videoWidth and videoHeight reflect the display aspect ratio
                                                // (safeNW, safeNH) to match MPV's sub-ass-vsfilter-aspect-compat=yes behavior.
                                                // Passing non-square storage dimensions (e.g. 720x480 for anamorphic DVD) causes
                                                // libass to apply an unintended double-PAR horizontal distortion on scripts authored
                                                // in display aspect ratio coordinates (PlayRes).
                                                this._videoWidth = safeNW;
                                                this._videoHeight = safeNH;

                                                if (this._canvas) {
                                                    this._canvas.style.width = '100%';
                                                    this._canvas.style.height = '100%';
                                                    this._canvas.style.top = '0px';
                                                    this._canvas.style.left = '0px';
                                                }
                                                if (this._canvasParent) {
                                                    this._canvasParent.style.removeProperty('width');
                                                    this._canvasParent.style.removeProperty('height');
                                                    this._canvasParent.style.removeProperty('top');
                                                    this._canvasParent.style.removeProperty('left');
                                                }
                                                if (this._canvasctrl && (this._canvasctrl.width === 0 || this._canvasctrl.height === 0)) {
                                                    this._canvasctrl.width = targetW;
                                                    this._canvasctrl.height = targetH;
                                                }
                                                const force = Boolean(paused ?? this._video?.paused ?? true);
                                                this.sendMessage("canvas", {
                                                    width: targetW,
                                                    height: targetH,
                                                    videoWidth: safeNW,
                                                    videoHeight: safeNH,
                                                    force: force
                                                });
                                            } else {
                                                const dpr = Math.min(2.0, Math.max(1.0, window.devicePixelRatio || 1.0));
                                                const targetW = Math.max(1, Math.round(safeNW * dpr));
                                                const targetH = Math.max(1, Math.round(safeNH * dpr));

                                                this._videoWidth = safeNW;
                                                this._videoHeight = safeNH;

                                                if (this._canvas) {
                                                    this._canvas.style.width = '100%';
                                                    this._canvas.style.height = '100%';
                                                    this._canvas.style.top = '0px';
                                                    this._canvas.style.left = '0px';
                                                }
                                                if (this._canvasParent) {
                                                    this._canvasParent.style.width = '100%';
                                                    this._canvasParent.style.height = '100%';
                                                    this._canvasParent.style.top = '0px';
                                                    this._canvasParent.style.left = '0px';
                                                }
                                                if (this._canvasctrl) {
                                                    if (this._canvasctrl.width !== targetW || this._canvasctrl.height !== targetH) {
                                                        this._canvasctrl.width = targetW;
                                                        this._canvasctrl.height = targetH;
                                                    }
                                                }
                                                const force = paused ?? this._video?.paused ?? false;
                                                this.sendMessage("canvas", {
                                                    width: targetW,
                                                    height: targetH,
                                                    videoWidth: safeNW,
                                                    videoHeight: safeNH,
                                                    force: force
                                                });
                                            }
                                        } catch (err) {
                                            console.error("[Pyxis JASSUB Resize Error]", err);
                                        }
                                    };

                                    const playerContainer = (artInstance.template && artInstance.template.$player) || box;
                                    syncJassubDomPlacement(activePlayers[nodeIdStr], initRenderMode, jassubInstance, playerContainer);
                                    if (activePlayers[nodeIdStr] && typeof activePlayers[nodeIdStr].applyTransform === 'function') {
                                        activePlayers[nodeIdStr].applyTransform();
                                    }
                                    try { jassubInstance.resize(0, 0, 0, 0, true); } catch(e) {}

                                    if (initialAss && typeof updateJassubTrack === "function") {
                                        await updateJassubTrack(jassubInstance, initialAss, nodeIdStr);
                                    }
                                    logPlayer("JASSUB instance created for node: " + nodeIdStr + " with unapplied base subtitle (" + initialAss.length + " bytes)");
                                    if (window.PyxisTelemetry && typeof window.PyxisTelemetry.renderAllPreviewerHeatmaps === 'function') {
                                        window.PyxisTelemetry.renderAllPreviewerHeatmaps();
                                    }
                                } catch (err) {
                                    console.error("[Pyxis JASSUB Error]", err);
                                    logPlayer("JASSUB creation exception: " + String(err));
                                }
                            }
                        });
                    }

                    function setupPlayerViewportZoomPan(artInstance, nodeIdStr, box) {
                        if (!artInstance || !box) return;

                        const pActiveObjInit = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                            ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                            : null;
                        let targetNodeInit = pActiveObjInit ? pActiveObjInit.node : null;
                        if (!targetNodeInit && window.graph) {
                            targetNodeInit = window.graph.getNodeById(Number(nodeIdStr)) || window.graph.getNodeById(nodeIdStr);
                        }
                        const nodeProps = (targetNodeInit && targetNodeInit.properties) || {};
                        const savedZoom = parseFloat(nodeProps.viewport_zoom);
                        const savedPanX = parseFloat(nodeProps.viewport_pan_x);
                        const savedPanY = parseFloat(nodeProps.viewport_pan_y);
                        const savedCustom = Boolean(nodeProps.viewport_custom);
                        const isCustomInit = savedCustom || ((!isNaN(savedZoom) && savedZoom > 0 && Math.abs(savedZoom - 1.0) > 0.001) || (!isNaN(savedPanX) && savedPanX !== 0) || (!isNaN(savedPanY) && savedPanY !== 0));

                        const transformState = {
                            zoom: (!isNaN(savedZoom) && savedZoom > 0) ? savedZoom : 1.0,
                            userZoom: (!isNaN(savedZoom) && savedZoom > 0) ? savedZoom : 1.0,
                            panX: !isNaN(savedPanX) ? savedPanX : 0,
                            panY: !isNaN(savedPanY) ? savedPanY : 0,
                            isPanning: false,
                            startX: 0,
                            startY: 0,
                            startPanX: 0,
                            startPanY: 0,
                            isCustom: isCustomInit,
                            actualScale: null,
                            lastPW: null,
                            lastPH: null
                        };

                        function syncTransformToNode() {
                            let tn = targetNodeInit;
                            if (!tn) {
                                const pObj = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                                    ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                                    : null;
                                tn = pObj ? pObj.node : null;
                            }
                            if (!tn && window.graph) {
                                tn = window.graph.getNodeById(Number(nodeIdStr)) || window.graph.getNodeById(nodeIdStr);
                            }
                            if (!tn) return;
                            if (!tn.properties) tn.properties = {};
                            const isCust = Boolean(transformState.isCustom);
                            tn.properties.viewport_zoom = isCust ? (transformState.userZoom || 1.0) : 1.0;
                            tn.properties.viewport_pan_x = isCust ? Math.round(transformState.panX * 100) / 100 : 0;
                            tn.properties.viewport_pan_y = isCust ? Math.round(transformState.panY * 100) / 100 : 0;
                            tn.properties.viewport_custom = isCust;

                            if (typeof window.updateTemplateUIState === "function") {
                                window.updateTemplateUIState();
                            }
                            if (typeof window.__pyxis_schedule_save === "function") {
                                window.__pyxis_schedule_save(150);
                            }
                        }

                        function getVideoContainer() {
                            const vp = box.querySelector('.pyxis-video-viewport');
                            if (vp) return vp;
                            const vid = artInstance.template ? artInstance.template.$video : box.querySelector('video');
                            if (vid && vid.parentElement && !vid.parentElement.classList.contains('art-video-player')) {
                                return vid.parentElement;
                            }
                            return vid;
                        }

                        function applyTransform() {
                            const videoContainer = getVideoContainer();
                            if (!videoContainer) return;
                            const vid = artInstance.template ? artInstance.template.$video : box.querySelector('video');
                            if (vid && videoContainer && vid.parentNode !== videoContainer) {
                                videoContainer.appendChild(vid);
                            }
                            const jassubParent = box.querySelector('div.JASSUB');
                            if (jassubParent && getNodeRenderMode(nodeIdStr) !== "mpv" && jassubParent.parentNode !== videoContainer) {
                                videoContainer.appendChild(jassubParent);
                            }
                            const { w: nW, h: nH } = getNativeResolution();
                            const safeNW = Math.max(1, nW || 1920);
                            const safeNH = Math.max(1, nH || 1080);
                            videoContainer.style.width = safeNW + 'px';
                            videoContainer.style.height = safeNH + 'px';
                            videoContainer.style.marginLeft = (-safeNW / 2) + 'px';
                            videoContainer.style.marginTop = (-safeNH / 2) + 'px';
                            const p = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                                ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                                : null;
                            const node = p ? p.node : null;

                            const curSource = (p && p.node && p.node.properties && p.node.properties.preview_source) || (node && node.properties && node.properties.preview_source) || "base";
                            const pInfo = (curSource === "aegisub" && window.PyxisPreviewConfigAegi) 
                                ? window.PyxisPreviewConfigAegi 
                                : ((curSource === "base" && window.PyxisPreviewConfigBase) ? window.PyxisPreviewConfigBase : window.PyxisPreviewConfig) || previewInfo || {};
                            let dummyColor = '#2a2a2a';
                            if (pInfo && pInfo.dummy_info && pInfo.dummy_info.color_hex) {
                                const hex = String(pInfo.dummy_info.color_hex).replace(/^#/, '');
                                dummyColor = '#' + hex;
                            }
                            videoContainer.style.backgroundColor = dummyColor;

                            let pW = 520;
                            let pH = 292;

                            if (p && p.isFullscreen) {
                                pW = window.innerWidth;
                                pH = Math.max(50, window.innerHeight - 68);
                            } else if (p && p.inTelemetryCockpit) {
                                pW = Math.max(100, box.clientWidth || box.offsetWidth || 520);
                                pH = Math.max(50, (box.clientHeight || box.offsetHeight || 360) - 68);
                            } else if (p && p.isPinned) {
                                const targetWrapper = p.wrapper || box;
                                pW = Math.max(100, targetWrapper.clientWidth || targetWrapper.offsetWidth || parseFloat(targetWrapper.style.width) || (p.savedFloatingWidth ? parseFloat(p.savedFloatingWidth) : 560));
                                const totalH = targetWrapper.clientHeight || targetWrapper.offsetHeight || parseFloat(targetWrapper.style.height) || (p.savedFloatingHeight ? parseFloat(p.savedFloatingHeight) : 380);
                                pH = Math.max(50, totalH - 98);
                            } else if (node && node.size) {
                                pW = Math.max(100, Math.round(node.size[0] - 20));
                                pH = Math.max(50, Math.round(node.size[1] - 124));
                            } else {
                                const frameEl = box.querySelector('.pyxis-video-frame');
                                if (frameEl && frameEl.clientWidth > 0 && frameEl.clientHeight > 0) {
                                    pW = frameEl.clientWidth;
                                    pH = frameEl.clientHeight;
                                } else {
                                    const viewportParent = videoContainer.parentElement || box.querySelector('.pyxis-video-frame') || box;
                                    pW = viewportParent.clientWidth || viewportParent.offsetWidth || 520;
                                    pH = viewportParent.clientHeight || viewportParent.offsetHeight || 292;
                                    if (viewportParent.classList.contains('art-video-player') || viewportParent === box) {
                                        pH = Math.max(50, pH - 68);
                                    }
                                }
                            }

                            const baseScale = Math.min(pW / safeNW, pH / safeNH);
                            const pActiveObj = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                                ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                                : null;

                            let actualScale;
                            if (transformState.isCustom) {
                                const isResizingNow = Boolean(
                                    !(pActiveObj && pActiveObj.isResettingAnim) && (
                                        (window.canvas && window.canvas.resizing_node === node) ||
                                        (pActiveObj && pActiveObj.isResizing) ||
                                        window.__pyxisDraggingFloating
                                    )
                                );

                                // Compensate panX and panY for viewport size changes using an Anchor Baseline
                                // so that the content (landscape) remains completely stationary on screen
                                // down to subpixel precision without accumulation drift while window borders move.
                                if (!(pActiveObj && pActiveObj.isResettingAnim)) {
                                    if (isResizingNow) {
                                        let curLeft = 0;
                                        let curTop = 0;
                                        if (pActiveObj && pActiveObj.isPinned && pActiveObj.wrapper) {
                                            curLeft = parseFloat(pActiveObj.wrapper.style.left) || 0;
                                            curTop = parseFloat(pActiveObj.wrapper.style.top) || 0;
                                        }

                                        if (!transformState.resizeAnchor) {
                                            transformState.resizeAnchor = {
                                                pW: (transformState.lastPW !== null && transformState.lastPW > 0) ? transformState.lastPW : pW,
                                                pH: (transformState.lastPH !== null && transformState.lastPH > 0) ? transformState.lastPH : pH,
                                                panX: (typeof transformState.panX === 'number') ? transformState.panX : 0,
                                                panY: (typeof transformState.panY === 'number') ? transformState.panY : 0,
                                                left: curLeft,
                                                top: curTop
                                            };
                                        }
                                        const anchor = transformState.resizeAnchor;
                                        const dLeft = curLeft - anchor.left;
                                        const dTop = curTop - anchor.top;
                                        transformState.panX = anchor.panX - (pW - anchor.pW) / 2 - dLeft;
                                        transformState.panY = anchor.panY - (pH - anchor.pH) / 2 - dTop;
                                    } else {
                                        if (transformState.resizeAnchor) {
                                            delete transformState.resizeAnchor;
                                        }
                                    }
                                }
                                transformState.lastPW = pW;
                                transformState.lastPH = pH;

                                // The scale of the video must stay FIXED during window resizing.
                                // Resizing the window must NOT alter the magnification of the landscape.
                                if (isResizingNow && transformState.actualScale && transformState.actualScale > 0) {
                                    actualScale = transformState.actualScale;
                                } else {
                                    actualScale = baseScale * (transformState.userZoom || 1.0);
                                    transformState.actualScale = actualScale;
                                }
                                transformState.zoom = Math.round((actualScale / baseScale) * 1000) / 1000;
                                transformState.userZoom = transformState.zoom;
                            } else {
                                transformState.isCustom = false;
                                transformState.zoom = 1.0;
                                transformState.userZoom = 1.0;
                                transformState.panX = 0;
                                transformState.panY = 0;
                                transformState.lastPW = pW;
                                transformState.lastPH = pH;
                                if (transformState.resizeAnchor) {
                                    delete transformState.resizeAnchor;
                                }
                                actualScale = Math.round(baseScale * 100000) / 100000;
                                transformState.actualScale = actualScale;
                            }

                            if (!isFinite(actualScale) || isNaN(actualScale) || actualScale <= 0) {
                                actualScale = 1.0;
                            }

                            videoContainer.style.transform = `translate3d(${transformState.panX}px, ${transformState.panY}px, 0px) scale(${actualScale})`;
                            syncMpvJassubOverlay(box, nodeIdStr, safeNW, safeNH, actualScale, transformState.panX, transformState.panY);
                        }

                        let resetAnimId = null;

                        function cancelResetAnimation() {
                            if (resetAnimId) {
                                cancelAnimationFrame(resetAnimId);
                                resetAnimId = null;
                            }
                            const p = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                                ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                                : null;
                            if (p) {
                                p.isResettingAnim = false;
                            }
                        }

                        function animateResetTransform(onComplete) {
                            cancelResetAnimation();

                            const p = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                                ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                                : null;
                            const isTelemetryMode = Boolean(p && p.inTelemetryCockpit);
                            const node = p ? p.node : null;
                            const { w: nW, h: nH } = getNativeResolution();
                            const safeNW = Math.max(1, nW || 1920);
                            const safeNH = Math.max(1, nH || 1080);
                            const curAspect = isTelemetryMode
                                ? ((window.PyxisTelemetry && typeof window.PyxisTelemetry.getCockpitAspectRatio === 'function')
                                    ? window.PyxisTelemetry.getCockpitAspectRatio()
                                    : (safeNW / safeNH))
                                : ((typeof getNodePreviewAspectRatio === 'function')
                                    ? (getNodePreviewAspectRatio(node) || (safeNW / safeNH))
                                    : (safeNW / safeNH));

                            const startPanX = transformState.panX || 0;
                            const startPanY = transformState.panY || 0;
                            const startScale = (transformState.isCustom && transformState.actualScale) ? transformState.actualScale : null;

                            let isNodeMode = false;
                            let isFloatingMode = false;
                            let startH = 0;
                            let targetH = 0;

                            let videoPane = null;
                            let bodyEl = null;
                            let startPaneW = 0;
                            let startPaneH = 0;
                            let targetPaneW = 0;
                            let targetPaneH = 0;
                            const bottomBarH = 68;

                            if (isTelemetryMode) {
                                const stage = document.getElementById('pyxis-tel-video-stage');
                                videoPane = stage ? stage.closest('.pyxis-tel-video-pane') : document.querySelector('.pyxis-tel-video-pane');
                                bodyEl = videoPane ? videoPane.closest('.pyxis-tel-body') : null;

                                startPaneW = (videoPane && videoPane.clientWidth) ? videoPane.clientWidth : 534;
                                startPaneH = (videoPane && videoPane.clientHeight) ? videoPane.clientHeight : 360;
                                const curFrameH = Math.max(1, startPaneH - bottomBarH);
                                const currentAspect = startPaneW / curFrameH;

                                const customSize = (window.PyxisTelemetry && typeof window.PyxisTelemetry.getCustomCockpitSize === 'function')
                                    ? window.PyxisTelemetry.getCustomCockpitSize()
                                    : null;

                                const hasCustomFreeAspect = Boolean(customSize && customSize.free);
                                const isAspectOriginal = !hasCustomFreeAspect && (Math.abs(currentAspect - curAspect) < 0.03);

                                if (isAspectOriginal) {
                                    resetTransform(false);
                                    if (typeof onComplete === 'function') onComplete();
                                    return;
                                }

                                const bodyW = (bodyEl && bodyEl.clientWidth) ? bodyEl.clientWidth : window.innerWidth;
                                const bodyH = (bodyEl && bodyEl.clientHeight) ? bodyEl.clientHeight : (window.innerHeight - 54);
                                const minW = 260;
                                const maxW = Math.max(320, Math.min(Math.round(window.innerWidth * 0.72), bodyW - 420));
                                const minH = 185;
                                const maxH = Math.max(230, bodyH - 190);

                                const effMinW = Math.max(minW, Math.round((minH - bottomBarH) * curAspect));
                                const effMaxW = Math.max(effMinW, Math.min(maxW, Math.round((maxH - bottomBarH) * curAspect)));

                                let baseW = (customSize && customSize.w > 0) ? customSize.w : startPaneW;
                                targetPaneW = Math.max(effMinW, Math.min(effMaxW, Math.round(baseW)));
                                targetPaneH = Math.round(targetPaneW / curAspect) + bottomBarH;
                                if (targetPaneH > maxH) {
                                    targetPaneH = maxH;
                                    targetPaneW = Math.max(effMinW, Math.min(effMaxW, Math.round((targetPaneH - bottomBarH) * curAspect)));
                                }
                            } else if (p && !p.isFullscreen) {
                                if (!p.isPinned && node && node.size) {
                                    isNodeMode = true;
                                    const w = node.size[0] || 520;
                                    startH = node.size[1];
                                    targetH = calculatePrevisualizadorNodeHeight(w, curAspect);
                                } else if (p.isPinned && p.wrapper) {
                                    isFloatingMode = true;
                                    const rect = p.wrapper.getBoundingClientRect();
                                    const w = Math.max(340, rect.width || parseFloat(p.wrapper.style.width) || 560);
                                    startH = rect.height || parseFloat(p.wrapper.style.height) || 380;
                                    const chromeH = 98;
                                    targetH = Math.round(w / curAspect) + chromeH;
                                }
                            }

                            const noPan = (startPanX === 0 && startPanY === 0);
                            const noScale = (startScale === null);
                            const noDimDiff = isTelemetryMode
                                ? (startPaneW === targetPaneW && startPaneH === targetPaneH)
                                : ((!isNodeMode && !isFloatingMode) || (startH === targetH));

                            if (noPan && noScale && noDimDiff) {
                                if (p) p.isResettingAnim = false;
                                transformState.isCustom = false;
                                transformState.zoom = 1.0;
                                transformState.userZoom = 1.0;
                                transformState.panX = 0;
                                transformState.panY = 0;
                                transformState.isPanning = false;
                                transformState.actualScale = null;
                                box.classList.remove('is-panning');
                                if (isTelemetryMode && window.PyxisTelemetry && typeof window.PyxisTelemetry.onCockpitResetComplete === 'function') {
                                    window.PyxisTelemetry.onCockpitResetComplete(targetPaneW, targetPaneH);
                                }
                                applyTransform();
                                syncTransformToNode();
                                if (typeof onComplete === 'function') onComplete();
                                return;
                            }

                            if (p) {
                                p.isResettingAnim = true;
                            }

                            const duration = 280; // ms
                            const startTime = performance.now();

                            function easeOutCubic(t) {
                                return 1 - Math.pow(1 - t, 3);
                            }

                            function step(now) {
                                const elapsed = now - startTime;
                                const progress = Math.min(1.0, elapsed / duration);
                                const ease = easeOutCubic(progress);

                                if (isTelemetryMode) {
                                    const curPaneW = Math.round(startPaneW + (targetPaneW - startPaneW) * ease);
                                    const curPaneH = Math.round(startPaneH + (targetPaneH - startPaneH) * ease);
                                    if (videoPane) {
                                        videoPane.style.width = `${curPaneW}px`;
                                    }
                                    if (bodyEl) {
                                        bodyEl.style.gridTemplateRows = `${curPaneH}px 1fr`;
                                    }
                                } else if (isNodeMode) {
                                    const curH = Math.round(startH + (targetH - startH) * ease);
                                    node.size[1] = curH;
                                    if (p) p.lastH = curH;
                                    if (p && p.wrapper && !p.isPinned) {
                                        p.wrapper.style.height = Math.max(100, curH - 56) + 'px';
                                    }
                                    if (typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                                    if (window.canvas) {
                                        window.canvas.setDirty(true, true);
                                        window.canvas.draw(true, true);
                                    }
                                } else if (isFloatingMode) {
                                    const curH = Math.round(startH + (targetH - startH) * ease);
                                    p.wrapper.style.setProperty('height', curH + 'px', 'important');
                                    p.savedFloatingHeight = curH + 'px';
                                }

                                transformState.panX = Math.round((startPanX + (0 - startPanX) * ease) * 100) / 100;
                                transformState.panY = Math.round((startPanY + (0 - startPanY) * ease) * 100) / 100;

                                let pW = 520, pH = 292;
                                if (isTelemetryMode) {
                                    const curPaneW = Math.round(startPaneW + (targetPaneW - startPaneW) * ease);
                                    const curPaneH = Math.round(startPaneH + (targetPaneH - startPaneH) * ease);
                                    pW = Math.max(100, curPaneW);
                                    pH = Math.max(50, curPaneH - bottomBarH);
                                } else if (p && p.isFullscreen) {
                                    pW = window.innerWidth;
                                    pH = Math.max(50, window.innerHeight - 68);
                                } else if (isFloatingMode) {
                                    const curFloatingH = startH + (targetH - startH) * ease;
                                    const rect = p.wrapper.getBoundingClientRect();
                                    pW = Math.max(100, rect.width || parseFloat(p.wrapper.style.width) || 560);
                                    pH = Math.max(50, curFloatingH - 98);
                                } else if (isNodeMode) {
                                    pW = Math.max(100, node.size[0] - 20);
                                    const curH = startH + (targetH - startH) * ease;
                                    pH = Math.max(50, curH - 124);
                                }

                                const frameBaseScale = Math.min(pW / safeNW, pH / safeNH);
                                let curScale = frameBaseScale;
                                if (startScale !== null) {
                                    curScale = startScale + (frameBaseScale - startScale) * ease;
                                    transformState.actualScale = curScale;
                                    transformState.zoom = Math.round((curScale / frameBaseScale) * 1000) / 1000;
                                }

                                transformState.lastPW = pW;
                                transformState.lastPH = pH;

                                const videoContainer = getVideoContainer();
                                if (videoContainer) {
                                    videoContainer.style.transform = `translate3d(${transformState.panX}px, ${transformState.panY}px, 0px) scale(${curScale})`;
                                }
                                syncMpvJassubOverlay(box, nodeIdStr, safeNW, safeNH, curScale, transformState.panX, transformState.panY);

                                if (progress < 1.0) {
                                    resetAnimId = requestAnimationFrame(step);
                                } else {
                                    resetAnimId = null;
                                    if (p) {
                                        p.isResettingAnim = false;
                                    }
                                    transformState.isCustom = false;
                                    transformState.zoom = 1.0;
                                    transformState.userZoom = 1.0;
                                    transformState.panX = 0;
                                    transformState.panY = 0;
                                    transformState.isPanning = false;
                                    transformState.actualScale = null;
                                    box.classList.remove('is-panning');

                                    if (isTelemetryMode) {
                                        if (window.PyxisTelemetry && typeof window.PyxisTelemetry.onCockpitResetComplete === 'function') {
                                            window.PyxisTelemetry.onCockpitResetComplete(targetPaneW, targetPaneH);
                                        }
                                    } else if (isNodeMode) {
                                        node.size[1] = targetH;
                                        if (p) p.lastH = targetH;
                                        if (p && p.wrapper && !p.isPinned) {
                                            p.wrapper.style.height = Math.max(100, targetH - 56) + 'px';
                                        }
                                        if (typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                                        if (window.canvas) {
                                            window.canvas.setDirty(true, true);
                                            window.canvas.draw(true, true);
                                        }
                                    } else if (isFloatingMode) {
                                        p.wrapper.style.setProperty('height', targetH + 'px', 'important');
                                        p.savedFloatingHeight = targetH + 'px';
                                    }

                                    applyTransform();
                                    syncTransformToNode();

                                    if (p && p.art && typeof p.art.resize === 'function') {
                                        try { p.art.resize(); } catch(e) {}
                                    }
                                    if (p && p.jassub && typeof p.jassub.resize === 'function') {
                                        try { p.jassub.resize(); } catch(e) {}
                                    }
                                    if (typeof onComplete === 'function') {
                                        onComplete();
                                    }
                                }
                            }

                            resetAnimId = requestAnimationFrame(step);
                        }

                        function resetTransform(animated = false) {
                            const pCheck = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                                ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                                : null;
                            if (animated) {
                                animateResetTransform();
                            } else {
                                cancelResetAnimation();
                                transformState.isCustom = false;
                                transformState.zoom = 1.0;
                                transformState.userZoom = 1.0;
                                transformState.panX = 0;
                                transformState.panY = 0;
                                transformState.isPanning = false;
                                transformState.actualScale = null;
                                box.classList.remove('is-panning');

                                const p = pCheck;
                                const node = p ? p.node : null;
                                if (p && !p.isFullscreen && !p.isPinned && !p.inTelemetryCockpit && node && node.size) {
                                    const curAspect = getNodePreviewAspectRatio(node);
                                    const targetH = calculatePrevisualizadorNodeHeight(node.size[0], curAspect);
                                    node.size[1] = targetH;
                                    p.lastH = targetH;
                                    if (p.wrapper) {
                                        p.wrapper.style.height = Math.max(100, targetH - 56) + 'px';
                                    }
                                    if (typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                                    if (window.canvas) {
                                        window.canvas.setDirty(true, true);
                                        window.canvas.draw(true, true);
                                    }
                                } else if (p && p.inTelemetryCockpit && window.PyxisTelemetry && typeof window.PyxisTelemetry.syncCockpitVideoLayout === 'function') {
                                    if (typeof window.PyxisTelemetry.resetCockpitSizeToAspect === 'function') {
                                        window.PyxisTelemetry.resetCockpitSizeToAspect();
                                    }
                                    window.PyxisTelemetry.syncCockpitVideoLayout();
                                }

                                applyTransform();
                                syncTransformToNode();
                                if (p && p.art && typeof p.art.resize === 'function') {
                                    try { p.art.resize(); } catch(e) {}
                                }
                                if (p && p.jassub && typeof p.jassub.resize === 'function') {
                                    try { p.jassub.resize(); } catch(e) {}
                                }
                            }
                        }

                        // 1. Zoom con la rueda del ratón focalizado en el puntero
                        const onWheel = (e) => {
                            const target = e.target;
                            if (target && target.closest && target.closest('.pyxis-custom-player-controls')) {
                                return;
                            }
                            e.preventDefault();
                            e.stopPropagation();

                            if (e.deltaY > 0 && resetAnimId) {
                                return;
                            }
                            if (e.deltaY < 0 && resetAnimId) {
                                cancelResetAnimation();
                            }

                            const videoContainer = getVideoContainer();
                            if (!videoContainer) return;

                            const viewportParent = videoContainer.parentElement || box.querySelector('.pyxis-video-frame') || box;
                            const parentRect = viewportParent.getBoundingClientRect();
                            const { w: nW, h: nH } = getNativeResolution();
                            const safeNW = Math.max(1, nW || 1920);
                            const safeNH = Math.max(1, nH || 1080);
                            const pW = viewportParent.clientWidth || 520;
                            const pH = viewportParent.clientHeight || 292;
                            const baseScale = Math.min(pW / safeNW, pH / safeNH);

                            const mouseX = e.clientX - parentRect.left;
                            const mouseY = e.clientY - parentRect.top;

                            const midX = parentRect.width / 2;
                            const midY = parentRect.height / 2;

                            const dx = mouseX - midX;
                            const dy = mouseY - midY;

                            const curScale = (transformState.isCustom && transformState.actualScale) 
                                ? transformState.actualScale 
                                : baseScale;
                            const zoomFactor = e.deltaY < 0 ? 1.15 : (1 / 1.15);
                            let newScale = curScale * zoomFactor;

                            const pCur = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                                ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                                : null;
                            const inTel = Boolean(pCur && pCur.inTelemetryCockpit);

                            if (newScale <= baseScale * 1.02) {
                                animateResetTransform();
                                return;
                            } else if (newScale > baseScale * 15.0) {
                                newScale = baseScale * 15.0;
                            }

                            const scaleRatio = newScale / curScale;
                            if (inTel && e.deltaY > 0 && curScale > baseScale) {
                                const t = Math.max(0, Math.min(1, (newScale - baseScale) / (curScale - baseScale)));
                                transformState.panX = Math.round(transformState.panX * t * 100) / 100;
                                transformState.panY = Math.round(transformState.panY * t * 100) / 100;
                            } else {
                                transformState.panX = Math.round((dx - (dx - transformState.panX) * scaleRatio) * 100) / 100;
                                transformState.panY = Math.round((dy - (dy - transformState.panY) * scaleRatio) * 100) / 100;
                            }
                            transformState.actualScale = newScale;
                            transformState.zoom = Math.round((newScale / baseScale) * 1000) / 1000;
                            transformState.userZoom = transformState.zoom;
                            transformState.isCustom = true;
                            transformState.lastPW = pW;
                            transformState.lastPH = pH;
                            if (transformState.resizeAnchor) {
                                delete transformState.resizeAnchor;
                            }

                            applyTransform();
                            syncTransformToNode();
                            if (getNodeRenderMode(nodeIdStr) === "mpv") {
                                scheduleMpvSharpResize(nodeIdStr, 60);
                            }
                        };

                        // 2. Pan con botón medio del ratón (button === 1)
                        const onPointerDown = (e) => {
                            cancelResetAnimation();
                            if (e.button === 1) {
                                const target = e.target;
                                if (target && target.closest && target.closest('.pyxis-custom-player-controls')) {
                                    return;
                                }
                                e.preventDefault();
                                e.stopPropagation();

                                transformState.isPanning = true;
                                transformState.startX = e.clientX;
                                transformState.startY = e.clientY;
                                transformState.startPanX = transformState.panX;
                                transformState.startPanY = transformState.panY;

                                box.classList.add('is-panning');
                                try { box.setPointerCapture(e.pointerId); } catch(err) {}
                            }
                        };

                        const onPointerMove = (e) => {
                            if (!transformState.isPanning) return;
                            e.preventDefault();
                            e.stopPropagation();

                            const dx = e.clientX - transformState.startX;
                            const dy = e.clientY - transformState.startY;

                            transformState.panX = transformState.startPanX + dx;
                            transformState.panY = transformState.startPanY + dy;
                            transformState.isCustom = true;

                            applyTransform();
                        };

                        const onPointerUp = (e) => {
                            if (transformState.isPanning) {
                                transformState.isPanning = false;
                                if (transformState.resizeAnchor) {
                                    delete transformState.resizeAnchor;
                                }
                                box.classList.remove('is-panning');
                                try { box.releasePointerCapture(e.pointerId); } catch(err) {}
                                e.preventDefault();
                                e.stopPropagation();
                                syncTransformToNode();
                            }
                        };

                        // 3. Prevenir menú auxiliar o scroll por defecto con botón medio
                        const onAuxClick = (e) => {
                            if (e.button === 1) {
                                e.preventDefault();
                                e.stopPropagation();
                            }
                        };

                        // 4. Restablecer con la tecla R cuando el ratón está sobre el reproductor
                        let isMouseOver = false;
                        const onMouseEnter = () => { isMouseOver = true; };
                        const onMouseLeave = () => { isMouseOver = false; };
                        box.addEventListener('mouseenter', onMouseEnter);
                        box.addEventListener('mouseleave', onMouseLeave);

                        const onKeyDown = (e) => {
                            if (!isMouseOver) return;
                            const activeEl = document.activeElement;
                            if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable)) {
                                return;
                            }
                            if (e.key === 'r' || e.key === 'R') {
                                e.preventDefault();
                                e.stopPropagation();
                                resetTransform(true);
                            }
                        };
                        window.addEventListener('keydown', onKeyDown);

                        box.addEventListener('wheel', onWheel, { passive: false });
                        box.addEventListener('pointerdown', onPointerDown);
                        box.addEventListener('pointermove', onPointerMove);
                        box.addEventListener('pointerup', onPointerUp);
                        box.addEventListener('pointercancel', onPointerUp);
                        box.addEventListener('auxclick', onAuxClick);

                        applyTransform();
                        artInstance.on('resize', () => {
                            applyTransform();
                        });
                        artInstance.on('ready', () => {
                            applyTransform();
                        });
                        artInstance.on('video:loadedmetadata', () => {
                            applyTransform();
                            if (window.PyxisTelemetry && window.PyxisTelemetry.isOpen && typeof window.PyxisTelemetry.syncCockpitVideoLayout === 'function') {
                                window.PyxisTelemetry.syncCockpitVideoLayout();
                            }
                        });
                        setTimeout(applyTransform, 100);

                        if (activePlayers[nodeIdStr]) {
                            activePlayers[nodeIdStr].transformState = transformState;
                            activePlayers[nodeIdStr].resetTransform = resetTransform;
                            activePlayers[nodeIdStr].animateResetTransform = animateResetTransform;
                            activePlayers[nodeIdStr].cancelResetAnimation = cancelResetAnimation;
                            activePlayers[nodeIdStr].applyTransform = applyTransform;
                            activePlayers[nodeIdStr].getNativeResolution = getNativeResolution;
                            activePlayers[nodeIdStr].isInitialized = true;
                            activePlayers[nodeIdStr].destroyZoomPan = () => {
                                cancelResetAnimation();
                                window.removeEventListener('keydown', onKeyDown);
                                box.removeEventListener('mouseenter', onMouseEnter);
                                box.removeEventListener('mouseleave', onMouseLeave);
                            };
                        }
                    }

                    function setupCustomPlayerControls(artInstance, nodeIdStr, node, wrapper) {
                        if (!artInstance || !artInstance.template || !artInstance.template.$player) return;
                        const playerEl = artInstance.template.$player;

                        const oldControls = playerEl.querySelector('.pyxis-custom-player-controls');
                        if (oldControls) oldControls.remove();

                        const curSrcVal = (node.properties && node.properties.preview_source) || "base";
                        const isBaseSrc = curSrcVal === "base";
                        const initialHasAegisub = Boolean(window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub);
                        const tipFsKey = isBaseSrc ? "preview.source_base_tooltip" : "preview.source_aegisub_tooltip";
                        const tipFs = window.t ? window.t(tipFsKey) : (isBaseSrc
                            ? "Source: Base Template (preview_base.ass) - Click to switch to Aegisub"
                            : "Source: Open File in Aegisub - Click to switch to Base");
                        const curRenderModeFs = getNodeRenderMode(node);
                        const isMpvFs = curRenderModeFs === "mpv";
                        const tipRenderFsKey = getRenderModeTooltipKey(curRenderModeFs);
                        const tipRenderFs = getRenderModeTooltipText(curRenderModeFs);

                        const controls = document.createElement('div');
                        controls.className = 'pyxis-custom-player-controls';
                        controls.id = 'pyxis-player-controls-' + nodeIdStr;
                        controls.innerHTML = `
                            <div class="pyxis-pbar-container">
                                <canvas class="pyxis-pbar-heatmap" id="pyxis-pbar-heatmap-${nodeIdStr}" width="640" height="32"></canvas>
                                <div class="pyxis-pbar-track">
                                    <div class="pyxis-pbar-loaded" style="width: 0%;"></div>
                                    <div class="pyxis-pbar-played" style="width: 0%;"></div>
                                    <div class="pyxis-pbar-thumb" style="left: 0%;"></div>
                                </div>
                                <div class="pyxis-pbar-tip">00:00</div>
                            </div>
                            <div class="pyxis-ptime-header-row">
                                <span class="pyxis-ptime-current">00:00</span>
                                <span class="pyxis-ptime-duration">00:00</span>
                            </div>
                            <div class="pyxis-pcontrols-row">
                                <div class="pyxis-pcontrols-left">
                                    <button class="pyxis-pbtn pyxis-pbtn-volume" aria-label="${window.t ? window.t('preview.mute') : 'Mute / Unmute'}">
                                        <svg class="icon-vol-high" viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
                                        <svg class="icon-vol-low" viewBox="0 0 24 24" style="display:none;"><path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/></svg>
                                        <svg class="icon-vol-mute" viewBox="0 0 24 24" style="display:none;"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>
                                    </button>
                                    <div class="pyxis-pvolume-container">
                                        <input type="range" class="pyxis-pvolume-slider" id="pyxis-pvolume-slider-${nodeIdStr}" name="pyxis-pvolume-slider" min="0" max="1" step="0.01" value="0.5" aria-label="Volume">
                                    </div>
                                </div>
                                <div class="pyxis-pcontrols-center">
                                    <button class="pyxis-pbtn pyxis-pbtn-step-prev" aria-label="${window.t ? window.t('preview.prev_frame') : 'Previous frame (-1 frame)'}">
                                        <svg viewBox="0 0 24 24"><path d="M6 5h2v14H6V5zm12 0l-9 7 9 7V5z"/></svg>
                                    </button>
                                    <button class="pyxis-pbtn pyxis-pbtn-seek-back" aria-label="${window.t ? window.t('preview.seek_back_10') : 'Seek backward 10s'}">
                                        <svg viewBox="0 0 24 24"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>
                                    </button>
                                    <button class="pyxis-pbtn pyxis-pbtn-hero pyxis-pbtn-playpause" aria-label="${window.t ? window.t('preview.play') : 'Play / Pause'}">
                                        <svg class="icon-play" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                                        <svg class="icon-pause" viewBox="0 0 24 24" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                                    </button>
                                    <button class="pyxis-pbtn pyxis-pbtn-seek-fwd" aria-label="${window.t ? window.t('preview.seek_fwd_10') : 'Seek forward 10s'}">
                                        <svg viewBox="0 0 24 24"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/></svg>
                                    </button>
                                    <button class="pyxis-pbtn pyxis-pbtn-step-next" aria-label="${window.t ? window.t('preview.next_frame') : 'Next frame (+1 frame)'}">
                                        <svg viewBox="0 0 24 24"><path d="M6 19l9-7-9-7v14zm10-14v14h2V5h-2z"/></svg>
                                    </button>
                                </div>
                                <div class="pyxis-pcontrols-right">
                                    <button id="btn-ctrl-source-${nodeIdStr}" class="pyxis-pbtn pyxis-pbtn-fs-only pyxis-pbtn-source ${!initialHasAegisub ? 'disabled' : ''}" aria-label="${tipFs}" data-i18n-aria-label="${tipFsKey}" ${!initialHasAegisub ? 'disabled' : ''}>
                                        <img src="${isBaseSrc ? 'CD.png' : 'Aegisub_logo.png'}" alt="${curSrcVal}" />
                                    </button>
                                    <button id="btn-ctrl-rendermode-${nodeIdStr}" class="pyxis-pbtn pyxis-pbtn-fs-only pyxis-pbtn-rendermode ${isMpvFs ? 'is-mpv-mode' : ''}" aria-label="${tipRenderFs}" data-i18n-aria-label="${tipRenderFsKey}">
                                        ${getRenderModeSvgHtml(curRenderModeFs)}
                                    </button>
                                    <button id="btn-ctrl-refresh-${nodeIdStr}" class="pyxis-pbtn pyxis-pbtn-fs-only pyxis-pbtn-refresh" aria-label="${window.t ? window.t('preview.refresh') : 'Refresh Previewer'}" data-i18n-aria-label="preview.refresh">
                                        <svg class="pyxis-icon-refresh" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
                                        </svg>
                                        <svg class="pyxis-icon-cancel" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                                            <line x1="18" y1="6" x2="6" y2="18"></line>
                                            <line x1="6" y1="6" x2="18" y2="18"></line>
                                        </svg>
                                    </button>
                                    <button id="btn-ctrl-hardsub-${nodeIdStr}" class="pyxis-pbtn pyxis-pbtn-fs-only pyxis-pbtn-hardsub" aria-label="${window.t ? window.t('preview.hardsub') : 'Render Hardsub with FFmpeg'}" data-i18n-aria-label="preview.hardsub">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M4 11v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8H4z"/>
                                            <path d="M4 11V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v6H4z"/>
                                            <path d="M9 3l-2 8"/>
                                            <path d="M15 3l-2 8"/>
                                        </svg>
                                    </button>
                                    <button class="pyxis-pbtn pyxis-pbtn-settings" aria-label="${window.t ? window.t('preview.settings') : 'Settings'}">
                                        <svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
                                    </button>
                                    <button class="pyxis-pbtn pyxis-pbtn-fullscreen" aria-label="${window.t ? window.t('preview.fullscreen') : 'Fullscreen'}">
                                        <svg class="icon-fs-enter" viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
                                        <svg class="icon-fs-exit" viewBox="0 0 24 24" style="display:none;"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>
                                    </button>
                                </div>
                            </div>
                        `;

                        controls.addEventListener('mousedown', (e) => e.stopPropagation());
                        controls.addEventListener('pointerdown', (e) => e.stopPropagation());
                        controls.addEventListener('click', (e) => e.stopPropagation());

                        playerEl.appendChild(controls);

                        const pbarContainer = controls.querySelector('.pyxis-pbar-container');
                        const pbarLoaded = controls.querySelector('.pyxis-pbar-loaded');
                        const pbarPlayed = controls.querySelector('.pyxis-pbar-played');
                        const pbarThumb = controls.querySelector('.pyxis-pbar-thumb');
                        const pbarTip = controls.querySelector('.pyxis-pbar-tip');

                        const btnVolume = controls.querySelector('.pyxis-pbtn-volume');
                        const iconVolHigh = btnVolume.querySelector('.icon-vol-high');
                        const iconVolLow = btnVolume.querySelector('.icon-vol-low');
                        const iconVolMute = btnVolume.querySelector('.icon-vol-mute');
                        const sliderVolume = controls.querySelector('.pyxis-pvolume-slider');

                        const timeCurrent = controls.querySelector('.pyxis-ptime-current');
                        const timeDuration = controls.querySelector('.pyxis-ptime-duration');

                        const btnStepPrev = controls.querySelector('.pyxis-pbtn-step-prev');
                        const btnSeekBack = controls.querySelector('.pyxis-pbtn-seek-back');
                        const btnPlayPause = controls.querySelector('.pyxis-pbtn-playpause');
                        const iconPlay = btnPlayPause.querySelector('.icon-play');
                        const iconPause = btnPlayPause.querySelector('.icon-pause');
                        const btnSeekFwd = controls.querySelector('.pyxis-pbtn-seek-fwd');
                        const btnStepNext = controls.querySelector('.pyxis-pbtn-step-next');

                        const btnCtrlSource = controls.querySelector('#btn-ctrl-source-' + nodeIdStr);
                        const btnCtrlRenderMode = controls.querySelector('#btn-ctrl-rendermode-' + nodeIdStr);
                        const btnCtrlRefresh = controls.querySelector('#btn-ctrl-refresh-' + nodeIdStr);
                        const btnCtrlHardsub = controls.querySelector('#btn-ctrl-hardsub-' + nodeIdStr);

                        if (btnCtrlSource) {
                            btnCtrlSource.onclick = (e) => {
                                e.stopPropagation();
                                window.PyxisNodePlayerManager.togglePreviewSource(nodeIdStr);
                            };
                            if (typeof attachPyxisDelayTooltip === 'function') {
                                attachPyxisDelayTooltip(btnCtrlSource, () => {
                                    const p = activePlayers[nodeIdStr];
                                    const curSrc = (p && p.node && p.node.properties && p.node.properties.preview_source) || "base";
                                    const k = curSrc === "base" ? "preview.source_base_tooltip" : "preview.source_aegisub_tooltip";
                                    return window.t ? window.t(k) : (curSrc === "base" ? "Source: Base Template (preview_base.ass) - Click to switch to Aegisub" : "Source: Open File in Aegisub - Click to switch to Base");
                                }, 800);
                            }
                        }
                        if (btnCtrlRenderMode) {
                            btnCtrlRenderMode.onclick = (e) => {
                                e.stopPropagation();
                                window.PyxisNodePlayerManager.togglePreviewRenderMode(nodeIdStr);
                            };
                            if (typeof attachPyxisDelayTooltip === 'function') {
                                attachPyxisDelayTooltip(btnCtrlRenderMode, () => getRenderModeTooltipText(getNodeRenderMode(nodeIdStr)), 800);
                            }
                        }
                        if (btnCtrlRefresh) {
                            btnCtrlRefresh.onclick = (e) => {
                                e.stopPropagation();
                                window.PyxisNodePlayerManager.refreshPreview(nodeIdStr);
                            };
                            if (typeof attachPyxisDelayTooltip === 'function') {
                                attachPyxisDelayTooltip(btnCtrlRefresh, () => {
                                    if (btnCtrlRefresh.classList.contains("is-refreshing")) {
                                        return window.t ? window.t("preview.cancel_refresh") : "Cancel preview generation";
                                    }
                                    return window.t ? window.t('preview.refresh') : "Refresh Previewer";
                                }, 600);
                            }
                        }
                        if (btnCtrlHardsub) {
                            btnCtrlHardsub.onclick = (e) => {
                                e.stopPropagation();
                                window.PyxisNodePlayerManager.renderHardsub(nodeIdStr);
                            };
                            if (typeof attachPyxisDelayTooltip === 'function') {
                                attachPyxisDelayTooltip(btnCtrlHardsub, () => (window.t ? window.t('preview.hardsub') : "Render Hardsub with FFmpeg"), 800);
                            }
                        }

                        const btnSettings = controls.querySelector('.pyxis-pbtn-settings');
                        const btnFullscreen = controls.querySelector('.pyxis-pbtn-fullscreen');
                        const iconFsEnter = btnFullscreen.querySelector('.icon-fs-enter');
                        const iconFsExit = btnFullscreen.querySelector('.icon-fs-exit');

                        if (artInstance && artInstance.controls) {
                            artInstance.controls.setting = btnSettings;
                        }

                        function formatTime(seconds) {
                            if (isNaN(seconds) || seconds < 0) seconds = 0;
                            const m = Math.floor(seconds / 60);
                            const s = Math.floor(seconds % 60);
                            return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
                        }

                        function formatTimeWithMs(seconds) {
                            if (isNaN(seconds) || seconds < 0) seconds = 0;
                            const m = Math.floor(seconds / 60);
                            const s = Math.floor(seconds % 60);
                            const ms = Math.floor((seconds % 1) * 1000);
                            return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0') + '.' + String(ms).padStart(3, '0');
                        }

                        function updateVolumeUI() {
                            const p = activePlayers[nodeIdStr];
                            const isDecoupled = Boolean(p && p.isDecoupled);
                            const isMuted = isDecoupled 
                                ? Boolean(p.userMuted) 
                                : Boolean(artInstance.muted);
                            const vol = isMuted 
                                ? 0 
                                : (isDecoupled 
                                    ? ((p.userVolume !== undefined) ? p.userVolume : 0.5)
                                    : ((artInstance.volume !== undefined) ? artInstance.volume : 0.5));
                            sliderVolume.value = vol;
                            sliderVolume.style.background = `linear-gradient(to right, var(--accent-primary) ${vol * 100}%, rgba(255,255,255,0.2) ${vol * 100}%)`;

                            if (vol === 0 || isMuted) {
                                iconVolHigh.style.display = 'none';
                                iconVolLow.style.display = 'none';
                                iconVolMute.style.display = 'block';
                            } else if (vol < 0.5) {
                                iconVolHigh.style.display = 'none';
                                iconVolLow.style.display = 'block';
                                iconVolMute.style.display = 'none';
                            } else {
                                iconVolHigh.style.display = 'block';
                                iconVolLow.style.display = 'none';
                                iconVolMute.style.display = 'none';
                            }
                        }

                        let lastVolume = 0.5;
                        btnVolume.onclick = (e) => {
                            e.stopPropagation();
                            const p = activePlayers[nodeIdStr];
                            if (p && p.isDecoupled) {
                                if (p.userMuted || (p.userVolume === 0)) {
                                    p.userMuted = false;
                                    p.userVolume = (lastVolume > 0) ? lastVolume : 0.5;
                                } else {
                                    lastVolume = (p.userVolume !== undefined && p.userVolume > 0) ? p.userVolume : 0.5;
                                    p.userMuted = true;
                                }
                                if (p.auxAudio) {
                                    p.auxAudio.muted = Boolean(p.userMuted);
                                    p.auxAudio.volume = p.userMuted ? 0 : p.userVolume;
                                }
                                if (p.art && p.art.video) {
                                    p.art.video.muted = true;
                                    p.art.video.defaultMuted = true;
                                }
                            } else {
                                if (artInstance.muted || artInstance.volume === 0) {
                                    artInstance.muted = false;
                                    artInstance.volume = (lastVolume > 0) ? lastVolume : 0.5;
                                } else {
                                    lastVolume = artInstance.volume;
                                    artInstance.muted = true;
                                    artInstance.volume = 0;
                                }
                            }
                            updateVolumeUI();
                        };

                        sliderVolume.oninput = (e) => {
                            e.stopPropagation();
                            const val = parseFloat(sliderVolume.value);
                            const p = activePlayers[nodeIdStr];
                            if (p && p.isDecoupled) {
                                if (val === 0) {
                                    p.userMuted = true;
                                    p.userVolume = 0;
                                } else {
                                    p.userMuted = false;
                                    p.userVolume = val;
                                    lastVolume = val;
                                }
                                if (p.auxAudio) {
                                    p.auxAudio.muted = Boolean(p.userMuted);
                                    p.auxAudio.volume = p.userMuted ? 0 : p.userVolume;
                                }
                                if (p.art && p.art.video) {
                                    p.art.video.muted = true;
                                    p.art.video.defaultMuted = true;
                                }
                            } else {
                                if (val === 0) {
                                    artInstance.muted = true;
                                    artInstance.volume = 0;
                                } else {
                                    artInstance.muted = false;
                                    artInstance.volume = val;
                                    lastVolume = val;
                                }
                            }
                            updateVolumeUI();
                        };

                        function updatePlayPauseUI() {
                            const isPlaying = artInstance.playing;
                            if (isPlaying) {
                                iconPlay.style.display = 'none';
                                iconPause.style.display = 'block';
                            } else {
                                iconPlay.style.display = 'block';
                                iconPause.style.display = 'none';
                            }
                        }

                        btnPlayPause.onclick = (e) => {
                            e.stopPropagation();
                            artInstance.toggle();
                        };

                        function stepFrame(deltaFrames) {
                            if (!artInstance) return;
                            try { artInstance.pause(); } catch(e) {}
                            const fps = (window.PyxisPreviewConfig && window.PyxisPreviewConfig.fps && window.PyxisPreviewConfig.fps > 0) 
                                ? window.PyxisPreviewConfig.fps 
                                : 24.0;
                            const frameDuration = 1.0 / fps;
                            const { winStart, winEnd } = getPreviewBounds(nodeIdStr);
                            const target = Math.max(winStart, Math.min(winEnd, artInstance.currentTime + deltaFrames * frameDuration));
                            artInstance.currentTime = target;
                        }

                        function seekRelative(deltaSec) {
                            if (!artInstance) return;
                            const { winStart, winEnd } = getPreviewBounds(nodeIdStr);
                            const target = Math.max(winStart, Math.min(winEnd, artInstance.currentTime + deltaSec));
                            artInstance.currentTime = target;
                        }

                        btnStepPrev.onclick = (e) => { e.stopPropagation(); stepFrame(-1); };
                        btnSeekBack.onclick = (e) => { e.stopPropagation(); seekRelative(-10); };
                        btnSeekFwd.onclick = (e) => { e.stopPropagation(); seekRelative(10); };
                        btnStepNext.onclick = (e) => { e.stopPropagation(); stepFrame(1); };

                        btnSettings.onclick = (e) => {
                            e.stopPropagation();
                            if (artInstance && artInstance.setting) {
                                artInstance.setting.toggle();
                            }
                        };

                        const targetWrapper = wrapper || (activePlayers[nodeIdStr] ? activePlayers[nodeIdStr].wrapper : null);

                        if (artInstance) {
                            artInstance.on('video:play', updatePlayPauseUI);
                            artInstance.on('video:pause', updatePlayPauseUI);
                        }

                        function syncAndRepaintFullscreenTransition() {
                            const pCurr = activePlayers[nodeIdStr];
                            if (pCurr) {
                                pCurr.lastW = null;
                                pCurr.lastH = null;
                                pCurr.lastCanvasScale = null;
                            }
                            if (typeof updateInNodePlayersPosition === 'function') {
                                try { updateInNodePlayersPosition(); } catch(e) {}
                            }
                            if (artInstance && typeof artInstance.resize === 'function') {
                                try { artInstance.resize(); } catch(e) {}
                            }
                            if (pCurr && typeof pCurr.applyTransform === 'function') {
                                try { pCurr.applyTransform(); } catch(e) {}
                            }
                            if (pCurr && pCurr.jassub && typeof pCurr.jassub.resize === 'function') {
                                try { pCurr.jassub.resize(0, 0, 0, 0, true); } catch(e) {}
                                if (typeof forceJassubPausedRefresh === 'function') {
                                    forceJassubPausedRefresh(pCurr.jassub);
                                }
                            }
                            // Force Chromium/WebView2 hardware video decoder to present frame when paused
                            const v = (artInstance && artInstance.template && artInstance.template.$video) || (box && box.querySelector('video'));
                            if (v && v.paused) {
                                try {
                                    const cur = v.currentTime;
                                    if (cur > 0.001) {
                                        v.currentTime = cur - 0.0001;
                                        v.currentTime = cur;
                                    } else {
                                        v.currentTime = cur + 0.0001;
                                        v.currentTime = cur;
                                    }
                                } catch(e) {}
                            }
                        }

                        function toggleFullscreen(forceState) {
                            if (!targetWrapper) return;
                            const p = activePlayers[nodeIdStr];
                            const isNowFs = (forceState !== undefined) 
                                ? Boolean(forceState) 
                                : !targetWrapper.classList.contains('pyxis-player-fullscreen');

                            // Fullscreen is strictly disabled while inside the Telemetry cockpit
                            if (isNowFs && ((p && p.inTelemetryCockpit) || (window.PyxisTelemetry && window.PyxisTelemetry.isOpen))) {
                                return;
                            }

                            if (window.canvas) {
                                window.canvas.pointer_is_down = false;
                                window.canvas.pointer_is_double = false;
                                window.canvas.node_dragged = null;
                                window.canvas.resizing_node = false;
                                window.canvas.dragging_canvas = false;
                            }
                            if (p) {
                                p.isFullscreen = isNowFs;
                                p.lastW = null;
                                p.lastH = null;
                                p.lastCanvasScale = null;
                                if (p.transformState) {
                                    p.transformState.lastPW = null;
                                    p.transformState.lastPH = null;
                                    if (!isNowFs && !p.transformState.isCustom) {
                                        p.transformState.panX = 0;
                                        p.transformState.panY = 0;
                                        p.transformState.actualScale = null;
                                    }
                                }
                            }

                            if (isNowFs) {
                                if (pbarContainer && typeof pbarContainer._collapseHeatmap === 'function') {
                                    pbarContainer._collapseHeatmap();
                                }
                                targetWrapper.classList.add('pyxis-player-fullscreen');
                                document.body.classList.add('pyxis-player-fullscreen-active');
                                iconFsEnter.style.display = 'none';
                                iconFsExit.style.display = 'block';
                                const canRequestNativeFs = document.fullscreenEnabled && 
                                                           !window.pywebview && 
                                                           (navigator.userActivation ? navigator.userActivation.isActive : true);
                                if (canRequestNativeFs) {
                                    try {
                                        if (targetWrapper.requestFullscreen) {
                                            targetWrapper.requestFullscreen().catch(() => {});
                                        } else if (document.documentElement.requestFullscreen) {
                                            document.documentElement.requestFullscreen().catch(() => {});
                                        }
                                    } catch(e) {}
                                }
                            } else {
                                targetWrapper.classList.remove('pyxis-player-fullscreen');
                                document.body.classList.remove('pyxis-player-fullscreen-active');
                                iconFsEnter.style.display = 'block';
                                iconFsExit.style.display = 'none';
                                try {
                                    if (document.fullscreenElement) {
                                        document.exitFullscreen().catch(() => {});
                                    }
                                } catch(e) {}
                            }

                            requestAnimationFrame(syncAndRepaintFullscreenTransition);
                            setTimeout(syncAndRepaintFullscreenTransition, 60);
                            setTimeout(syncAndRepaintFullscreenTransition, 180);
                            setTimeout(syncAndRepaintFullscreenTransition, 350);
                        }

                        btnFullscreen.onclick = (e) => {
                            e.stopPropagation();
                            const p = activePlayers[nodeIdStr];
                            if ((p && p.inTelemetryCockpit) || (window.PyxisTelemetry && window.PyxisTelemetry.isOpen)) {
                                return;
                            }
                            if (window.canvas) {
                                window.canvas.pointer_is_down = false;
                                window.canvas.pointer_is_double = false;
                                window.canvas.node_dragged = null;
                                window.canvas.resizing_node = false;
                                window.canvas.dragging_canvas = false;
                            }
                            toggleFullscreen();
                        };

                        let clickDebounceTimer = null;
                        const DOUBLE_CLICK_DELAY = 240;

                        const onKeydown = (e) => {
                            if (!targetWrapper) return;
                            const isFs = targetWrapper.classList.contains('pyxis-player-fullscreen');
                            if (e.key === 'Escape' && isFs) {
                                toggleFullscreen(false);
                            }
                        };
                        window.addEventListener('keydown', onKeydown);
                        document.addEventListener('keydown', onKeydown);

                        const onFullscreenChange = () => {
                            if (!targetWrapper) return;
                            const isFs = targetWrapper.classList.contains('pyxis-player-fullscreen');
                            if (!document.fullscreenElement) {
                                if (isFs) {
                                    toggleFullscreen(false);
                                } else {
                                    syncAndRepaintFullscreenTransition();
                                    setTimeout(syncAndRepaintFullscreenTransition, 60);
                                    setTimeout(syncAndRepaintFullscreenTransition, 180);
                                    setTimeout(syncAndRepaintFullscreenTransition, 350);
                                }
                            } else if (document.fullscreenElement) {
                                syncAndRepaintFullscreenTransition();
                                setTimeout(syncAndRepaintFullscreenTransition, 60);
                                setTimeout(syncAndRepaintFullscreenTransition, 180);
                            }
                        };
                        document.addEventListener('fullscreenchange', onFullscreenChange);

                        if (activePlayers[nodeIdStr]) {
                            activePlayers[nodeIdStr].toggleFullscreen = toggleFullscreen;
                            activePlayers[nodeIdStr].syncAndRepaintFullscreenTransition = syncAndRepaintFullscreenTransition;
                            activePlayers[nodeIdStr].clearClickDebounce = () => {
                                if (clickDebounceTimer) {
                                    clearTimeout(clickDebounceTimer);
                                    clickDebounceTimer = null;
                                }
                            };
                            activePlayers[nodeIdStr].destroyFullscreenListeners = () => {
                                window.removeEventListener('keydown', onKeydown);
                                document.removeEventListener('keydown', onKeydown);
                                document.removeEventListener('fullscreenchange', onFullscreenChange);
                            };
                        }

                        if (playerEl) {
                            // Decouple single click (play/pause) from double click (fullscreen) in capture phase
                            playerEl.addEventListener('click', (e) => {
                                if (e.target.closest('.pyxis-custom-player-controls') || e.target.closest('.art-settings') || e.target.closest('.art-contextmenus')) {
                                    return;
                                }
                                e.stopImmediatePropagation();
                                e.stopPropagation();

                                if (clickDebounceTimer) {
                                    // Second click received within window: double click -> cancel play/pause toggle
                                    clearTimeout(clickDebounceTimer);
                                    clickDebounceTimer = null;
                                    return;
                                }

                                clickDebounceTimer = setTimeout(() => {
                                    clickDebounceTimer = null;
                                    if (artInstance) {
                                        artInstance.toggle();
                                    }
                                }, DOUBLE_CLICK_DELAY);
                            }, true);

                            playerEl.addEventListener('dblclick', (e) => {
                                if (e.target.closest('.pyxis-custom-player-controls') || e.target.closest('.art-settings') || e.target.closest('.art-contextmenus')) {
                                    return;
                                }
                                e.stopImmediatePropagation();
                                e.stopPropagation();
                                e.preventDefault();
                                if (clickDebounceTimer) {
                                    clearTimeout(clickDebounceTimer);
                                    clickDebounceTimer = null;
                                }
                                const p = activePlayers[nodeIdStr];
                                if ((p && p.inTelemetryCockpit) || (window.PyxisTelemetry && window.PyxisTelemetry.isOpen)) {
                                    return;
                                }
                                toggleFullscreen();
                            }, true);

                            playerEl.addEventListener('contextmenu', (e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                e.stopImmediatePropagation();
                            }, true);
                        }

                        let isDraggingSeek = false;
                        let seekDownClientX = 0;
                        let seekDownOnHeatmap = false;
                        let seekMovedDuringDrag = false;
                        let heatmapAnimRaf = null;
                        const pbarHeatmap = controls.querySelector('.pyxis-pbar-heatmap');
                        const pbarTrack = controls.querySelector('.pyxis-pbar-track');

                        function triggerHeatmapSmoothRedraw(durationMs) {
                            if (!pbarHeatmap || !window.PyxisTelemetry || typeof window.PyxisTelemetry.renderPreviewerHeatmap !== 'function') return;
                            if (heatmapAnimRaf) cancelAnimationFrame(heatmapAnimRaf);
                            const startTs = performance.now();
                            const step = (now) => {
                                window.PyxisTelemetry.renderPreviewerHeatmap(pbarHeatmap);
                                if (now - startTs < (durationMs || 240)) {
                                    heatmapAnimRaf = requestAnimationFrame(step);
                                } else {
                                    heatmapAnimRaf = null;
                                }
                            };
                            heatmapAnimRaf = requestAnimationFrame(step);
                        }

                        if (pbarHeatmap && window.PyxisTelemetry && typeof window.PyxisTelemetry.renderPreviewerHeatmap === 'function') {
                            requestAnimationFrame(() => window.PyxisTelemetry.renderPreviewerHeatmap(pbarHeatmap));
                            if (typeof ResizeObserver !== 'undefined') {
                                const ro = new ResizeObserver(() => {
                                    if (window.PyxisTelemetry && typeof window.PyxisTelemetry.renderPreviewerHeatmap === 'function') {
                                        window.PyxisTelemetry.renderPreviewerHeatmap(pbarHeatmap);
                                    }
                                });
                                ro.observe(pbarHeatmap);
                            }
                        }

                        function collapseHeatmap() {
                            if (pbarContainer.classList.contains('is-heatmap-expanded')) {
                                pbarContainer.classList.remove('is-heatmap-expanded');
                                if (pbarHeatmap) {
                                    delete pbarHeatmap.dataset.hoverRatio;
                                    pbarHeatmap.dataset.isOverGraph = '0';
                                }
                                triggerHeatmapSmoothRedraw(250);
                            }
                        }
                        pbarContainer._collapseHeatmap = collapseHeatmap;

                        const onOutsidePointerDown = (e) => {
                            if (!document.body.contains(pbarContainer)) {
                                window.removeEventListener('pointerdown', onOutsidePointerDown, true);
                                return;
                            }
                            if (!pbarContainer.classList.contains('is-heatmap-expanded')) return;
                            const target = e.target;
                            if (wrapper && target && wrapper.contains(target)) return;
                            collapseHeatmap();
                        };
                        window.addEventListener('pointerdown', onOutsidePointerDown, true);

                        function isEventInHeatmapZone(e) {
                            if (!pbarHeatmap || !pbarTrack) return false;
                            if (!window.PyxisTelemetry || !window.PyxisTelemetry.lastData || !Array.isArray(window.PyxisTelemetry.lastData.frames) || window.PyxisTelemetry.lastData.frames.length < 2) {
                                return false;
                            }
                            if (window.PyxisTelemetry.isOpen) {
                                return false;
                            }
                            if ((targetWrapper && targetWrapper.classList.contains('pyxis-player-fullscreen')) || Boolean(document.fullscreenElement)) {
                                return false;
                            }
                            const trackRect = pbarTrack.getBoundingClientRect();
                            return (e.target === pbarHeatmap) || (e.clientY < (trackRect.top - 3));
                        }

                        let seekRafId = null;
                        let pendingSeekTargetTime = null;
                        function scheduleVideoSeek(targetSec, immediate = false) {
                            pendingSeekTargetTime = targetSec;
                            if (immediate) {
                                if (seekRafId) {
                                    cancelAnimationFrame(seekRafId);
                                    seekRafId = null;
                                }
                                if (pendingSeekTargetTime !== null) {
                                    const t = pendingSeekTargetTime;
                                    pendingSeekTargetTime = null;
                                    try { artInstance.currentTime = t; } catch (err) {}
                                }
                                return;
                            }
                            if (!seekRafId) {
                                seekRafId = requestAnimationFrame(() => {
                                    seekRafId = null;
                                    if (pendingSeekTargetTime !== null) {
                                        const t = pendingSeekTargetTime;
                                        pendingSeekTargetTime = null;
                                        try { artInstance.currentTime = t; } catch (err) {}
                                    }
                                });
                            }
                        }

                        function updateHoverTip(e) {
                            const rect = pbarContainer.getBoundingClientRect();
                            if (rect.width <= 0) return 0;
                            const rawX = e.clientX - rect.left;
                            const clampedX = Math.max(0, Math.min(rect.width, rawX));
                            const pct = clampedX / rect.width;
                            const { winDur } = getPreviewBounds(nodeIdStr);
                            const hoverTime = pct * winDur;
                            const overHeatmap = !isDraggingSeek && isEventInHeatmapZone(e);
                            const isExpandedNow = pbarContainer.classList.contains('is-heatmap-expanded');

                            if (pbarHeatmap) {
                                pbarHeatmap.dataset.hoverRatio = String(pct);
                                pbarHeatmap.dataset.isOverGraph = overHeatmap ? '1' : '0';
                                if (isExpandedNow && window.PyxisTelemetry && typeof window.PyxisTelemetry.renderPreviewerHeatmap === 'function') {
                                    window.PyxisTelemetry.renderPreviewerHeatmap(pbarHeatmap);
                                }
                            }

                            let tipText = formatTimeWithMs(hoverTime);
                            pbarTip.style.borderColor = 'var(--border-highlight)';
                            if (window.PyxisTelemetry && typeof window.PyxisTelemetry.getFrameAtRatio === 'function') {
                                const fInfo = window.PyxisTelemetry.getFrameAtRatio(pct);
                                if (fInfo && typeof fInfo.render_ms === 'number') {
                                    tipText += `  |  ${fInfo.render_ms.toFixed(2)} ms`;
                                    const summary = (window.PyxisTelemetry.lastData && window.PyxisTelemetry.lastData.summary) ? window.PyxisTelemetry.lastData.summary : {};
                                    const bMs = Number(summary.frame_budget_ms) || 41.71;
                                    if (fInfo.render_ms > bMs) {
                                        pbarTip.style.borderColor = 'rgba(244, 63, 94, 0.9)';
                                    } else if (fInfo.render_ms > bMs * 0.65) {
                                        pbarTip.style.borderColor = 'rgba(251, 191, 36, 0.85)';
                                    } else {
                                        pbarTip.style.borderColor = overHeatmap ? 'var(--doc-accent-bright)' : 'var(--border-highlight)';
                                    }
                                }
                            }
                            if (overHeatmap) {
                                const clickHint = isExpandedNow
                                    ? (window.t ? window.t('telemetry.click_to_open') : 'Click: Open Telemetry')
                                    : (window.t ? window.t('telemetry.click_to_expand') : 'Click: Expand graph');
                                tipText += `  |  ${clickHint}`;
                            }
                            pbarTip.textContent = tipText;

                            const tipWidth = pbarTip.offsetWidth || 56;
                            const halfTip = tipWidth / 2;
                            const tipLeftPx = Math.max(halfTip + 4, Math.min(rect.width - halfTip - 4, clampedX));
                            pbarTip.style.left = `${(tipLeftPx / rect.width) * 100}%`;
                            return pct;
                        }

                        pbarContainer.addEventListener('pointerenter', (e) => {
                            updateHoverTip(e);
                        });
                        pbarContainer.addEventListener('pointerleave', () => {
                            if (pbarHeatmap) {
                                delete pbarHeatmap.dataset.hoverRatio;
                                pbarHeatmap.dataset.isOverGraph = '0';
                                if (pbarContainer.classList.contains('is-heatmap-expanded') && window.PyxisTelemetry && typeof window.PyxisTelemetry.renderPreviewerHeatmap === 'function') {
                                    window.PyxisTelemetry.renderPreviewerHeatmap(pbarHeatmap);
                                }
                            }
                        });
                        pbarContainer.addEventListener('pointermove', (e) => {
                            const pct = updateHoverTip(e);
                            if (isDraggingSeek) {
                                pbarPlayed.style.width = (pct * 100) + '%';
                                pbarThumb.style.left = (pct * 100) + '%';
                                const { winStart, winDur } = getPreviewBounds(nodeIdStr);
                                const relTime = pct * winDur;
                                timeCurrent.textContent = formatTime(relTime);
                                scheduleVideoSeek(winStart + relTime, false);
                            } else if (seekDownOnHeatmap) {
                                const movedPx = Math.abs((e.clientX || 0) - seekDownClientX);
                                if (movedPx >= 6) {
                                    seekMovedDuringDrag = true;
                                }
                            }
                        });

                        pbarContainer.addEventListener('pointerdown', (e) => {
                            e.stopPropagation();
                            if (window.canvas) {
                                window.canvas.pointer_is_down = false;
                                window.canvas.dragging_canvas = false;
                                if (node && !node.is_selected && typeof window.canvas.selectNode === 'function') {
                                    try { window.canvas.selectNode(node); } catch(err) {}
                                }
                            }
                            seekDownClientX = e.clientX;
                            seekMovedDuringDrag = false;
                            seekDownOnHeatmap = isEventInHeatmapZone(e);
                            try { pbarContainer.setPointerCapture(e.pointerId); } catch(err) {}
                            if (seekDownOnHeatmap) {
                                isDraggingSeek = false;
                                updateHoverTip(e);
                            } else {
                                isDraggingSeek = true;
                                pbarContainer.classList.add('is-dragging');
                                const pct = updateHoverTip(e);
                                pbarPlayed.style.width = (pct * 100) + '%';
                                pbarThumb.style.left = (pct * 100) + '%';
                                const { winStart, winDur } = getPreviewBounds(nodeIdStr);
                                const relTime = pct * winDur;
                                timeCurrent.textContent = formatTime(relTime);
                                scheduleVideoSeek(winStart + relTime, true);
                            }
                        });

                        const releaseSeek = (e) => {
                            try { pbarContainer.releasePointerCapture(e.pointerId); } catch(err) {}
                            if (isDraggingSeek) {
                                isDraggingSeek = false;
                                pbarContainer.classList.remove('is-dragging');
                                if (pendingSeekTargetTime !== null) {
                                    scheduleVideoSeek(pendingSeekTargetTime, true);
                                }
                            }
                            if (seekDownOnHeatmap) {
                                const movedPx = Math.abs((e.clientX || 0) - seekDownClientX);
                                const isClick = (e.type === 'pointerup') && !seekMovedDuringDrag && movedPx < 8;
                                seekDownOnHeatmap = false;
                                seekMovedDuringDrag = false;
                                if (isClick) {
                                    if (!pbarContainer.classList.contains('is-heatmap-expanded')) {
                                        pbarContainer.classList.add('is-heatmap-expanded');
                                        updateHoverTip(e);
                                        triggerHeatmapSmoothRedraw(260);
                                    } else {
                                        collapseHeatmap();
                                        if (window.PyxisTelemetry && typeof window.PyxisTelemetry.open === 'function') {
                                            window.PyxisTelemetry.open(nodeIdStr);
                                        }
                                    }
                                }
                            }
                        };
                        pbarContainer.addEventListener('pointerup', releaseSeek);
                        pbarContainer.addEventListener('pointercancel', releaseSeek);

                        function updateTimeUI() {
                            const { winStart, winEnd, winDur } = getPreviewBounds(nodeIdStr);
                            const current = artInstance.currentTime || 0;
                            timeDuration.textContent = formatTime(winDur);

                            // Clamp playback to the effect window: when reaching winEnd, loop back to winStart
                            if (!artInstance.paused && current >= (winEnd - 0.03)) {
                                artInstance.currentTime = winStart;
                                return;
                            } else if (!artInstance.paused && current < (winStart - 0.1)) {
                                artInstance.currentTime = winStart;
                                return;
                            }

                            const relCurrent = Math.max(0, Math.min(winDur, current - winStart));

                            if (!isDraggingSeek) {
                                timeCurrent.textContent = formatTime(relCurrent);
                                const pct = (winDur > 0) ? (relCurrent / winDur) * 100 : 0;
                                pbarPlayed.style.width = pct + '%';
                                pbarThumb.style.left = pct + '%';
                            }

                            const video = artInstance.template ? artInstance.template.$video : null;
                            if (video && video.buffered && video.buffered.length > 0 && winDur > 0) {
                                let bufEnd = 0;
                                for (let i = 0; i < video.buffered.length; i++) {
                                    if (video.buffered.start(i) <= current && current <= video.buffered.end(i)) {
                                        bufEnd = video.buffered.end(i);
                                        break;
                                    }
                                }
                                if (!bufEnd && video.buffered.length > 0) {
                                    bufEnd = video.buffered.end(video.buffered.length - 1);
                                }
                                const relBufEnd = Math.max(0, Math.min(winDur, bufEnd - winStart));
                                pbarLoaded.style.width = Math.min(100, (relBufEnd / winDur) * 100) + '%';
                            }
                        }

                        artInstance.on('video:timeupdate', updateTimeUI);
                        artInstance.on('video:progress', updateTimeUI);
                        artInstance.on('video:loadedmetadata', updateTimeUI);
                        artInstance.on('video:durationchange', updateTimeUI);

                        artInstance.on('video:play', updatePlayPauseUI);
                        artInstance.on('video:pause', updatePlayPauseUI);
                        artInstance.on('play', updatePlayPauseUI);
                        artInstance.on('pause', updatePlayPauseUI);

                        artInstance.on('video:volumechange', updateVolumeUI);

                        const handleLoopEnd = () => {
                            if (artInstance && artInstance.template && artInstance.template.$video) {
                                const { winStart } = getPreviewBounds(nodeIdStr);
                                try {
                                    artInstance.currentTime = winStart;
                                    artInstance.play();
                                } catch(e) {}
                            }
                        };
                        artInstance.on('video:ended', handleLoopEnd);
                        artInstance.on('ended', handleLoopEnd);

                        updateTimeUI();
                        updatePlayPauseUI();
                        updateVolumeUI();
                        if (activePlayers[nodeIdStr]) {
                            activePlayers[nodeIdStr].updateTimeUI = updateTimeUI;
                            activePlayers[nodeIdStr].updateVolumeUI = updateVolumeUI;
                        }
                        if (box) {
                            box._pyxisUpdateTimeUI = updateTimeUI;
                            box._pyxisUpdateVolumeUI = updateVolumeUI;
                        }
                    }

                    const hasAegi = Boolean(previewInfo && previewInfo.has_aegisub);
                    const existingP = activePlayers[nodeIdStr] || {};
                    activePlayers[nodeIdStr] = Object.assign(existingP, {
                        wrapper: wrapper,
                        box: box,
                        headerActions: headerActions,
                        art: artInstance,
                        jassub: jassubInstance,
                        loadingBackdrop: loadingBackdrop,
                        node: node,
                        hasRefreshed: false,
                        hasAegisub: hasAegi,
                        videoUrl: videoUrl,
                        scaledBorderAndShadow: (previewInfo && typeof previewInfo.scaled_border_and_shadow === 'boolean') ? previewInfo.scaled_border_and_shadow : true,
                        isInitializing: false,
                        isInitialized: true,
                        updateTimeUI: existingP.updateTimeUI || (box ? box._pyxisUpdateTimeUI : undefined),
                        updateVolumeUI: existingP.updateVolumeUI || (box ? box._pyxisUpdateVolumeUI : undefined)
                    });
                    updateSourceButtonUI(nodeIdStr, curSource, hasAegi);
                    updateRenderModeButtonUI(nodeIdStr, getNodeRenderMode(node));
                    updatePreviewMetadataBadges(nodeIdStr, previewInfo);
                    if (audioUrl) {
                        setupDecoupledAudio(activePlayers[nodeIdStr], audioUrl);
                    } else {
                        teardownDecoupledAudio(activePlayers[nodeIdStr]);
                    }

                    if (node && node.properties && node.properties.is_pinned && !activePlayers[nodeIdStr].isPinned) {
                        togglePinPreview(nodeIdStr);
                    }
                } finally {
                    delete creatingPlayers[nodeIdStr];
                }
            }

            function destroyInNodePlayer(nodeId) {
                const p = activePlayers[nodeId];
                if (!p) return;

                if (p.mpvResizeTimer) {
                    clearTimeout(p.mpvResizeTimer);
                    p.mpvResizeTimer = null;
                }
                teardownDecoupledAudio(p);

                if (p.headerActions && p.headerActions.parentNode) {
                    p.headerActions.parentNode.removeChild(p.headerActions);
                }
                if (p.jassub && typeof p.jassub.destroy === 'function') {
                    try {
                        if (p.jassub._video && p.jassub._video.parentNode && p.jassub._canvasParent && p.jassub._canvasParent.parentNode !== p.jassub._video.parentNode) {
                            p.jassub._video.parentNode.appendChild(p.jassub._canvasParent);
                        }
                    } catch (e) {}
                    try { p.jassub.destroy(); } catch (e) {}
                    if (window.__pyxis_injected_fonts) window.__pyxis_injected_fonts.clear();
                }
                if (p.art && typeof p.art.destroy === 'function') {
                    try { p.art.destroy(true); } catch (e) {}
                }
                if (typeof p.destroyZoomPan === 'function') {
                    try { p.destroyZoomPan(); } catch (e) {}
                }
                if (typeof p.destroyFullscreenListeners === 'function') {
                    try { p.destroyFullscreenListeners(); } catch (e) {}
                }
                if (typeof p.clearClickDebounce === 'function') {
                    try { p.clearClickDebounce(); } catch (e) {}
                }
                if (p.wrapper && p.wrapper.parentNode) {
                    p.wrapper.parentNode.removeChild(p.wrapper);
                }
                delete activePlayers[nodeId];
                if (Object.keys(activePlayers).length === 0 && window.PyxisTelemetry && typeof window.PyxisTelemetry.clearData === 'function') {
                    window.PyxisTelemetry.clearData(true);
                }
            }

            function destroyAllPlayers() {
                Object.keys(activePlayers).forEach(nodeId => {
                    destroyInNodePlayer(nodeId);
                });
                if (window.PyxisTelemetry && typeof window.PyxisTelemetry.clearData === 'function') {
                    window.PyxisTelemetry.clearData(true);
                }
                const allWrappers = document.querySelectorAll('.pyxis-node-player-wrapper');
                allWrappers.forEach(wrap => {
                    if (wrap.parentNode) wrap.parentNode.removeChild(wrap);
                });
                const allHeaders = document.querySelectorAll('.pyxis-node-header-actions');
                allHeaders.forEach(head => {
                    if (head.parentNode) head.parentNode.removeChild(head);
                });
            }

            function setupDecoupledAudio(p, audioUrl) {
                if (!p || !p.art || !p.art.video) return;
                teardownDecoupledAudio(p);
                if (!audioUrl) return;

                p.isDecoupled = true;

                // Cache user's intended volume before muting the underlying container video
                if (p.userVolume === undefined) {
                    p.userVolume = (typeof p.art.volume === 'number' && p.art.volume > 0) ? p.art.volume : 0.5;
                }
                if (p.userMuted === undefined) {
                    p.userMuted = Boolean(p.art.muted);
                }

                const v = p.art.video;
                // Pre-mute the underlying container video so Chromium/Media Foundation NEVER attempts
                // to decode the incompatible audio track in the container (preventing pipeline stall/freeze).
                v.muted = true;
                v.defaultMuted = true;

                const audio = new Audio();
                audio.crossOrigin = 'anonymous';
                audio.preload = 'auto';
                audio.src = audioUrl;

                audio.currentTime = v.currentTime || 0;
                audio.playbackRate = v.playbackRate || 1;
                audio.volume = p.userMuted ? 0 : (typeof p.userVolume === 'number' ? p.userVolume : 0.5);
                audio.muted = Boolean(p.userMuted);

                const onPlay = () => {
                    audio.currentTime = v.currentTime;
                    audio.play().catch(() => {});
                };
                const onPause = () => {
                    audio.pause();
                };
                const onSeeking = () => {
                    audio.currentTime = v.currentTime;
                };
                const onSeeked = () => {
                    audio.currentTime = v.currentTime;
                };
                const onRateChange = () => {
                    audio.playbackRate = v.playbackRate;
                };
                const onVolumeChange = () => {
                    if (!p.isDecoupled) {
                        audio.volume = p.art.muted ? 0 : (typeof p.art.volume === 'number' ? p.art.volume : 1);
                        audio.muted = Boolean(p.art.muted);
                    }
                };
                const onWaiting = () => {
                    audio.pause();
                };
                const onPlaying = () => {
                    audio.currentTime = v.currentTime;
                    if (audio.paused && !v.paused) {
                        audio.play().catch(() => {});
                    }
                };

                v.addEventListener('play', onPlay);
                v.addEventListener('pause', onPause);
                v.addEventListener('seeking', onSeeking);
                v.addEventListener('seeked', onSeeked);
                v.addEventListener('ratechange', onRateChange);
                v.addEventListener('volumechange', onVolumeChange);
                v.addEventListener('waiting', onWaiting);
                v.addEventListener('playing', onPlaying);

                p.auxAudio = audio;
                p._auxAudioCleanups = [
                    () => v.removeEventListener('play', onPlay),
                    () => v.removeEventListener('pause', onPause),
                    () => v.removeEventListener('seeking', onSeeking),
                    () => v.removeEventListener('seeked', onSeeked),
                    () => v.removeEventListener('ratechange', onRateChange),
                    () => v.removeEventListener('volumechange', onVolumeChange),
                    () => v.removeEventListener('waiting', onWaiting),
                    () => v.removeEventListener('playing', onPlaying)
                ];

                if (typeof p.updateVolumeUI === 'function') {
                    p.updateVolumeUI();
                }
            }

            function teardownDecoupledAudio(p) {
                if (!p) return;
                p.isDecoupled = false;
                if (p._auxAudioCleanups && Array.isArray(p._auxAudioCleanups)) {
                    p._auxAudioCleanups.forEach(fn => {
                        try { fn(); } catch(e) {}
                    });
                    p._auxAudioCleanups = null;
                }
                if (p.auxAudio) {
                    try {
                        p.auxAudio.pause();
                        p.auxAudio.removeAttribute('src');
                        p.auxAudio.load();
                    } catch(e) {}
                    p.auxAudio = null;
                }
                if (p.art && p.art.video) {
                    const restoredMuted = (p.userMuted !== undefined) ? Boolean(p.userMuted) : Boolean(p.art.muted);
                    const restoredVol = (p.userVolume !== undefined) ? p.userVolume : ((typeof p.art.volume === 'number') ? p.art.volume : 0.5);
                    p.art.video.muted = restoredMuted;
                    p.art.video.defaultMuted = restoredMuted;
                    p.art.video.volume = restoredVol;
                }
                if (typeof p.updateVolumeUI === 'function') {
                    p.updateVolumeUI();
                }
            }

            function updateSourceButtonUI(nodeIdStr, source, hasAegisub) {
                const isBase = source === "base";
                const iconFile = isBase ? "CD.png" : "Aegisub_logo.png";
                const tipKey = isBase ? "preview.source_base_tooltip" : "preview.source_aegisub_tooltip";
                const tip = window.t ? window.t(tipKey) : (isBase
                    ? "Source: Base Template (preview_base.ass) - Click to switch to Aegisub"
                    : "Source: Open File in Aegisub - Click to switch to Base");

                const btnSelectors = ['#btn-source-' + nodeIdStr, '#btn-float-source-' + nodeIdStr, '#btn-ctrl-source-' + nodeIdStr];
                btnSelectors.forEach(sel => {
                    const btn = document.querySelector(sel);
                    if (btn) {
                        const img = btn.querySelector('img');
                        if (img) {
                            img.src = iconFile;
                            img.alt = source;
                        }
                        btn.setAttribute('data-i18n-aria-label', tipKey);
                        btn.setAttribute('aria-label', tip);
                        btn.removeAttribute('data-i18n-title');
                        btn.removeAttribute('title');
                        if (!hasAegisub) {
                            const noAegi = window.t ? window.t("preview.no_aegisub_session") : "No active Aegisub session with subtitles";
                            btn.classList.add('disabled');
                            btn.setAttribute('disabled', 'true');
                            btn.setAttribute('data-i18n-aria-label', 'preview.no_aegisub_session');
                            btn.setAttribute('aria-label', noAegi);
                        } else {
                            btn.classList.remove('disabled');
                            btn.removeAttribute('disabled');
                        }
                    }
                });
            }

            function updateRenderModeButtonUI(nodeIdStr, mode) {
                const cleanId = String(nodeIdStr);
                const cleanMode = (mode === "mpv") ? "mpv" : "typesetting";
                const isMpv = cleanMode === "mpv";
                const tipKey = getRenderModeTooltipKey(cleanMode);
                const tip = getRenderModeTooltipText(cleanMode);
                const svgHtml = getRenderModeSvgHtml(cleanMode);

                const btnSelectors = [
                    '#btn-rendermode-' + cleanId,
                    '#btn-float-rendermode-' + cleanId,
                    '#btn-ctrl-rendermode-' + cleanId
                ];
                btnSelectors.forEach(sel => {
                    const btn = document.querySelector(sel);
                    if (btn) {
                        btn.innerHTML = svgHtml;
                        btn.classList.toggle('is-mpv-mode', isMpv);
                        btn.setAttribute('data-i18n-aria-label', tipKey);
                        btn.setAttribute('aria-label', tip);
                        btn.removeAttribute('data-i18n-title');
                        btn.removeAttribute('title');
                    }
                });
            }

            async function togglePreviewRenderMode(nodeId) {
                const nodeIdStr = String(nodeId);
                const p = activePlayers[nodeIdStr];
                let targetNode = (p && p.node) ? p.node : null;
                if (!targetNode && window.graph) {
                    targetNode = window.graph.getNodeById(Number(nodeIdStr)) || window.graph.getNodeById(nodeIdStr);
                }
                if (!targetNode) return;
                if (!targetNode.properties) targetNode.properties = {};

                const curMode = getNodeRenderMode(targetNode);
                const nextMode = (curMode === "mpv") ? "typesetting" : "mpv";
                targetNode.properties.render_mode = nextMode;

                if (typeof window.updateTemplateUIState === "function") {
                    window.updateTemplateUIState();
                }
                if (typeof window.__pyxis_schedule_save === "function") {
                    window.__pyxis_schedule_save(150);
                }

                updateRenderModeButtonUI(nodeIdStr, nextMode);

                if (p) {
                    if (p.mpvResizeTimer) {
                        clearTimeout(p.mpvResizeTimer);
                        p.mpvResizeTimer = null;
                    }
                    syncJassubDomPlacement(p, nextMode);
                    if (typeof p.applyTransform === 'function') {
                        try { p.applyTransform(); } catch (e) {}
                    }
                    if (p.jassub) {
                        try { p.jassub.resize(0, 0, 0, 0, true); } catch (e) {}
                        if (p.rawAssContent) {
                            await updateJassubTrack(p.jassub, p.rawAssContent, nodeIdStr, true);
                        } else {
                            forceJassubPausedRefresh(p.jassub);
                        }
                    }
                }

                if (typeof window.showPyxisToast === 'function') {
                    const modeLabel = (nextMode === "mpv")
                        ? (window.t ? window.t("preview.render_mode_mpv_label") : "mpv (Screen Space)")
                        : (window.t ? window.t("preview.render_mode_ts_label") : "Typesetting (1:1)");
                    const msg = window.t
                        ? window.t("toast.preview_render_mode", { mode: modeLabel })
                        : ("Render Mode: " + modeLabel);
                    window.showPyxisToast(msg, "source");
                }
            }

            async function safeArtSwitchUrl(artInstance, newUrl, timeoutMs = 2000) {
                if (!artInstance || !newUrl) return;
                if (artInstance.url === newUrl) return;
                try {
                    let timeoutId = null;
                    const switchPromise = (typeof artInstance.switchUrl === 'function')
                        ? artInstance.switchUrl(newUrl)
                        : Promise.resolve();
                    const timeoutPromise = new Promise(resolve => {
                        timeoutId = setTimeout(() => {
                            // Fallback: forcefully update video.src if Artplayer's canplay promise timed out
                            try {
                                const v = (artInstance.template && artInstance.template.$video) || artInstance.video;
                                if (v && v.src !== newUrl) {
                                    v.src = newUrl;
                                    v.load();
                                }
                            } catch (e) {}
                            resolve();
                        }, timeoutMs);
                    });
                    await Promise.race([switchPromise, timeoutPromise]);
                    if (timeoutId) clearTimeout(timeoutId);
                } catch (err) {
                    console.warn("[Pyxis] safeArtSwitchUrl exception:", err);
                    try {
                        const v = (artInstance.template && artInstance.template.$video) || artInstance.video;
                        if (v && v.src !== newUrl) {
                            v.src = newUrl;
                            v.load();
                        }
                    } catch (e) {}
                }
            }

            async function revertToPreviewBase(nodeId) {
                const nodeIdStr = String(nodeId);
                const p = activePlayers[nodeIdStr];
                if (!p || !p.node) return;
                if (!p.node.properties) p.node.properties = {};

                p.node.properties.preview_source = "base";
                teardownDecoupledAudio(p);
                const hasAegi = (p.hasAegisub !== undefined)
                    ? p.hasAegisub
                    : (window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub);
                updateSourceButtonUI(nodeIdStr, "base", hasAegi);

                if (window.pywebview && window.pywebview.api) {
                    try {
                        const serialized = (window.graph) ? window.graph.serialize() : null;
                        const connectedOutputs = resolveConnectedOutputsForPreview(p.node);
                        if (typeof window.pywebview.api.get_preview_video_data_url === 'function') {
                            const baseVideoUrl = await window.pywebview.api.get_preview_video_data_url("base", connectedOutputs, serialized);
                            if (baseVideoUrl && p.art && p.videoUrl !== baseVideoUrl) {
                                p.videoUrl = baseVideoUrl;
                                await safeArtSwitchUrl(p.art, baseVideoUrl);
                            }
                        }
                        if (typeof window.pywebview.api.get_preview_info === 'function') {
                            const baseInfo = await window.pywebview.api.get_preview_info("base", connectedOutputs, serialized);
                            if (baseInfo) {
                                window.PyxisPreviewConfig = baseInfo;
                                window.PyxisPreviewConfigBase = baseInfo;
                                updatePreviewMetadataBadges(nodeIdStr, baseInfo);
                            }
                        }
                        if (typeof window.pywebview.api.get_preview_fonts_map === 'function' && p.jassub) {
                            try {
                                const fontsMap = await window.pywebview.api.get_preview_fonts_map("base");
                                if (fontsMap && typeof fontsMap === 'object') {
                                    injectFontsIntoJassub(p.jassub, fontsMap);
                                }
                            } catch (e) {}
                        }
                        if (typeof window.pywebview.api.get_initial_base_ass === 'function' && p.jassub) {
                            const baseAss = await window.pywebview.api.get_initial_base_ass("base", connectedOutputs, serialized);
                            if (baseAss && typeof updateJassubTrack === "function") {
                                await updateJassubTrack(p.jassub, baseAss, nodeIdStr);
                            }
                        }
                        if (p.art) {
                            const b = getPreviewBounds(nodeIdStr);
                            try { p.art.seek = b.winStart; } catch (e) {}
                            try { p.art.currentTime = b.winStart; } catch (e) {}
                        }
                        if (typeof p.updateTimeUI === 'function') {
                            try { p.updateTimeUI(); } catch (e) {}
                        }
                    } catch (err) {
                        console.warn("[Pyxis] Error reverting to base preview:", err);
                    }
                }
            }

            async function togglePreviewSource(nodeId) {
                const nodeIdStr = String(nodeId);
                const p = activePlayers[nodeIdStr];
                if (!p || !p.node) return;
                if (!p.node.properties) p.node.properties = {};

                // If conversion or preview switch is currently running, treat clicking the source button as an immediate cancellation and return to base
                if (window.__pyxis_is_preview_running || window.__pyxis_is_preview_or_hardsub_running) {
                    console.log("[Pyxis] Source toggle clicked while active; cancelling conversion and reverting to base");
                    await cancelPreview(nodeIdStr, "preview.source_switch_cancelled");
                    return;
                }

                const curSource = p.node.properties.preview_source || "base";
                const hasAegi = (p.hasAegisub !== undefined) ? p.hasAegisub : (window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub);

                if (curSource === "base" && !hasAegi) {
                    if (typeof window.showPyxisToast === 'function') {
                        window.showPyxisToast("toast.no_active_aegisub", "warning");
                    }
                    return;
                }

                const nextSource = (curSource === "base") ? "aegisub" : "base";

                // Record playback state and pause immediately so media is not playing behind the loading screen
                const wasPlaying = Boolean(p.art && p.art.playing);
                if (p.art) {
                    try { p.art.pause(); } catch (e) {}
                }
                teardownDecoupledAudio(p);

                // Initialize cancellation and loading tracker
                window.__pyxis_active_preview_node_id = nodeIdStr;
                window.__pyxis_is_preview_running = true;
                window.__pyxis_is_preview_cancelled = false;

                setPlayerLoading(nodeId, true, "preview.switching_source");

                if (window.pywebview && window.pywebview.api) {
                    try {
                        const serialized = (window.graph) ? window.graph.serialize() : null;
                        const connectedOutputs = resolveConnectedOutputsForPreview(p.node);

                        // Pre-query target media parameters and resize node immediately so that loading
                        // overlays and audio conversion progress are rendered within correct aspect ratio
                        let targetInfo = null;
                        if (typeof window.pywebview.api.get_preview_info === 'function') {
                            try {
                                targetInfo = await window.pywebview.api.get_preview_info(nextSource, connectedOutputs, serialized);
                                if (targetInfo && !window.__pyxis_is_preview_cancelled) {
                                    updatePreviewMetadataBadges(nodeIdStr, targetInfo);
                                    if (targetInfo.is_audio_decoupled) {
                                        p.isDecoupled = true;
                                        if (p.userVolume === undefined && p.art) {
                                            p.userVolume = (typeof p.art.volume === 'number' && p.art.volume > 0) ? p.art.volume : 0.5;
                                        }
                                        if (p.userMuted === undefined && p.art) {
                                            p.userMuted = Boolean(p.art.muted);
                                        }
                                        if (p.art && p.art.video) {
                                            p.art.video.muted = true;
                                            p.art.video.defaultMuted = true;
                                        }
                                    } else {
                                        p.isDecoupled = false;
                                    }
                                    if (targetInfo.aspect_ratio && p.node) {
                                        p.node.preview_aspect_ratio = targetInfo.aspect_ratio;
                                        if (p.node.properties) p.node.properties.preview_aspect_ratio = targetInfo.aspect_ratio;
                                        const nodeAspect = getNodePreviewAspectRatio(p.node);
                                        if (!p.isPinned) {
                                            const dynMinW = getDynamicMinPreviewWidth(nodeAspect);
                                            let targetW = (p.node.size && p.node.size[0] && p.node.size[0] >= dynMinW) ? p.node.size[0] : 520;
                                            if (p.node.properties && p.node.properties.previewer_width && p.node.properties.previewer_height) {
                                                targetW = Math.max(dynMinW, Number(p.node.properties.previewer_width));
                                            } else if (targetInfo.res_x && targetInfo.res_x > 0) {
                                                const scaled = Math.round(targetInfo.res_x * 0.50);
                                                targetW = Math.max(dynMinW, Math.min(1280, scaled));
                                            }
                                            const newH = (p.node.properties && p.node.properties.previewer_height)
                                                ? Number(p.node.properties.previewer_height)
                                                : calculatePrevisualizadorNodeHeight(targetW, nodeAspect);
                                            p.node.size = [targetW, newH];
                                            p.lastW = targetW;
                                            p.lastH = newH;
                                            if (p.wrapper && !p.isPinned) {
                                                p.wrapper.style.width = Math.max(100, targetW - 20) + 'px';
                                                p.wrapper.style.height = Math.max(100, newH - 56) + 'px';
                                            }
                                            if (typeof p.node.setDirtyCanvas === 'function') p.node.setDirtyCanvas(true, true);
                                            if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                            if (typeof updateInNodePlayersPosition === 'function') {
                                                updateInNodePlayersPosition();
                                            }
                                        } else {
                                            const minSz = (typeof p.node.computeSize === 'function') ? p.node.computeSize() : [284, 54];
                                            const minW = Math.max(270, minSz ? minSz[0] : 284);
                                            const curW = (p.node.size && p.node.size[0]) ? p.node.size[0] : minW;
                                            p.node.size = [Math.max(curW, minW), 54];
                                            if (p.originalSize) {
                                                let pinTargetW = p.originalSize[0];
                                                if (targetInfo.res_x && targetInfo.res_x > 0) {
                                                    pinTargetW = Math.max(getDynamicMinPreviewWidth(nodeAspect), Math.min(1280, Math.round(targetInfo.res_x * 0.50)));
                                                    p.originalSize[0] = pinTargetW;
                                                }
                                                p.originalSize[1] = calculatePrevisualizadorNodeHeight(pinTargetW, nodeAspect);
                                            }
                                            if (p.wrapper) {
                                                const rect = p.wrapper.getBoundingClientRect();
                                                const curFloatingW = Math.max(340, rect.width || parseFloat(p.wrapper.style.width) || (p.savedFloatingWidth ? parseFloat(p.savedFloatingWidth) : 560));
                                                const chromeH = 98;
                                                const newFloatingH = Math.round(curFloatingW / nodeAspect) + chromeH;
                                                p.wrapper.style.setProperty('width', curFloatingW + 'px', 'important');
                                                p.wrapper.style.setProperty('height', newFloatingH + 'px', 'important');
                                                p.savedFloatingWidth = curFloatingW + 'px';
                                                p.savedFloatingHeight = newFloatingH + 'px';
                                                if (p.art && typeof p.art.resize === 'function') {
                                                    try { p.art.resize(); } catch(e) {}
                                                }
                                                if (typeof p.resetTransform === 'function') {
                                                    try { p.resetTransform(); } catch(e) {}
                                                } else if (typeof p.applyTransform === 'function') {
                                                    try { p.applyTransform(); } catch(e) {}
                                                }
                                                if (p.jassub && typeof p.jassub.resize === 'function') {
                                                    try { p.jassub.resize(); } catch(e) {}
                                                }
                                            }
                                            if (typeof p.node.setDirtyCanvas === 'function') p.node.setDirtyCanvas(true, true);
                                            if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                        }
                                    }
                                }
                            } catch (infoErr) {
                                console.warn("[Pyxis] Pre-querying preview info failed:", infoErr);
                            }
                        }

                        // Parallelise retrieval of video URL, decoupled audio URL, font map, and subtitle ASS
                        const [newVideoUrl, nextAudioUrl, newFontsMap, baseAss] = await Promise.all([
                            (typeof window.pywebview.api.get_preview_video_data_url === 'function')
                                ? window.pywebview.api.get_preview_video_data_url(nextSource, connectedOutputs, serialized).catch(err => {
                                    console.warn("[Pyxis] Failed to get preview video url:", err);
                                    return null;
                                })
                                : Promise.resolve(null),
                            (typeof window.pywebview.api.get_preview_audio_data_url === 'function')
                                ? window.pywebview.api.get_preview_audio_data_url(nextSource, connectedOutputs, serialized).catch(err => {
                                    console.warn("[Pyxis] Failed to get preview audio url:", err);
                                    return null;
                                })
                                : Promise.resolve(null),
                            (typeof window.pywebview.api.get_preview_fonts_map === 'function' && p.jassub)
                                ? window.pywebview.api.get_preview_fonts_map(nextSource).catch(err => {
                                    console.warn("[Pyxis] Failed to get preview fonts map:", err);
                                    return null;
                                })
                                : Promise.resolve(null),
                            (typeof window.pywebview.api.get_initial_base_ass === 'function' && p.jassub)
                                ? window.pywebview.api.get_initial_base_ass(nextSource, connectedOutputs, serialized).catch(err => {
                                    console.warn("[Pyxis] Failed to get initial ASS:", err);
                                    return null;
                                })
                                : Promise.resolve(null)
                        ]);

                        if (window.__pyxis_is_preview_cancelled || !newVideoUrl) {
                            console.log("[Pyxis] Source switch aborted or cancelled; reverting to base");
                            await revertToPreviewBase(nodeIdStr);
                            setPlayerLoading(nodeIdStr, false);
                            window.__pyxis_is_preview_running = false;
                            window.__pyxis_active_preview_node_id = null;
                            return;
                        }

                        // Commit source change
                        p.node.properties.preview_source = nextSource;

                        if (typeof p.resetTransform === 'function') {
                            p.resetTransform();
                        }

                        updateSourceButtonUI(nodeIdStr, nextSource, hasAegi);

                        if (typeof window.showPyxisToast === 'function') {
                            const srcLabel = (nextSource === "base") 
                                ? (window.t ? window.t("preview.source_base_label") : "Base Template") 
                                : (window.t ? window.t("preview.source_aegisub_label") : "Aegisub");
                            window.showPyxisToast(window.t ? window.t("toast.preview_source", { source: srcLabel }) : ("Preview Source: " + srcLabel), "source");
                        }

                        if (targetInfo) {
                            window.PyxisPreviewConfig = targetInfo;
                            if (nextSource === "base") window.PyxisPreviewConfigBase = targetInfo;
                            if (nextSource === "aegisub") window.PyxisPreviewConfigAegi = targetInfo;
                        }

                        // Update decoupled audio track immediately
                        if (nextAudioUrl) {
                            setupDecoupledAudio(p, nextAudioUrl);
                        } else {
                            teardownDecoupledAudio(p);
                        }

                        // Inject binary font assets into libass / JASSUB
                        if (newFontsMap && typeof newFontsMap === 'object' && p.jassub) {
                            try {
                                injectFontsIntoJassub(p.jassub, newFontsMap);
                            } catch (e) {
                                console.warn("[Pyxis togglePreviewSource font update warning]", e);
                            }
                        }

                        // Synchronise JASSUB subtitle track
                        if (baseAss && p.jassub && typeof updateJassubTrack === "function") {
                            await updateJassubTrack(p.jassub, baseAss, nodeIdStr);
                        }

                        // Switch video track in ArtPlayer
                        if (newVideoUrl && p.art && p.videoUrl !== newVideoUrl) {
                            p.videoUrl = newVideoUrl;
                            await safeArtSwitchUrl(p.art, newVideoUrl);
                        }
                        if (p.art) {
                            const b = getPreviewBounds(nodeIdStr);
                            try { p.art.seek = b.winStart; } catch (e) {}
                            try { p.art.currentTime = b.winStart; } catch (e) {}
                        }
                        if (typeof p.updateTimeUI === 'function') {
                            try { p.updateTimeUI(); } catch (e) {}
                        }
                        p.hasRefreshed = false;
                        if (window.PyxisTelemetry && typeof window.PyxisTelemetry.clearData === 'function') {
                            window.PyxisTelemetry.clearData(true);
                        }
                        if (typeof updateInNodePlayersPosition === 'function') {
                            updateInNodePlayersPosition();
                        }
                        if (p.art && typeof p.art.resize === 'function') {
                            try { p.art.resize(); } catch(e) {}
                        }
                        if (typeof p.resetTransform === 'function') {
                            try { p.resetTransform(); } catch(e) {}
                        } else if (typeof p.applyTransform === 'function') {
                            p.applyTransform();
                        }
                        if (p.jassub && typeof p.jassub.resize === 'function') {
                            try { p.jassub.resize(); } catch (e) {}
                        }
                    } catch (e) {
                        console.error("[Pyxis togglePreviewSource switch media error]", e);
                        await revertToPreviewBase(nodeIdStr);
                    } finally {
                        if (window.__pyxis_is_preview_cancelled) {
                            await revertToPreviewBase(nodeIdStr);
                        }
                        setPlayerLoading(nodeIdStr, false);
                        window.__pyxis_is_preview_running = false;
                        window.__pyxis_active_preview_node_id = null;
                        if (wasPlaying && p.art && !window.__pyxis_is_preview_cancelled) {
                            try {
                                p.art.play().catch(() => {});
                            } catch (e) {}
                        }
                    }
                }
            }

            function resolveConnectedOutputsForPreview(previewNode) {
                const connectedOutputIds = [];
                if (!previewNode || !window.graph) return connectedOutputIds;

                const visitedNodes = new Set();

                function parseAndPushString(strVal) {
                    if (!strVal) return;
                    const items = String(strVal).split(/[,;]+/).map(s => s.trim()).filter(Boolean);
                    items.forEach(item => {
                        if (!connectedOutputIds.includes(item)) {
                            connectedOutputIds.push(item);
                        }
                    });
                }

                function traceUpstreamNode(nodeId) {
                    if (!nodeId || visitedNodes.has(nodeId)) return;
                    visitedNodes.add(nodeId);

                    const targetNode = window.graph.getNodeById(nodeId);
                    if (!targetNode) return;

                    const nType = (targetNode.type || '').toLowerCase();
                    const nTitle = (targetNode.title || '').toLowerCase();

                    // If it is an Output node:
                    if (nType.includes('output') || nTitle === 'output' || targetNode.kind === 'output') {
                        // 1. Identify precisely by node id (unique integer string)
                        const numId = String(targetNode.id);
                        if (!connectedOutputIds.includes(numId)) {
                            connectedOutputIds.push(numId);
                        }

                        // 2. Identify by custom user output_id / queue_id if specified
                        const customId = (targetNode.properties && (targetNode.properties.output_id || targetNode.properties.queue_id)) 
                            ? String(targetNode.properties.output_id || targetNode.properties.queue_id).trim() 
                            : "";
                        if (customId && !connectedOutputIds.includes(customId)) {
                            connectedOutputIds.push(customId);
                        }

                        // 3. If targetNode has a custom non-generic title (renamed by user), include it
                        const rawTitle = (targetNode.title || '').trim();
                        const isGenericTitle = (rawTitle.toLowerCase() === 'output');
                        if (rawTitle && !isGenericTitle && !connectedOutputIds.includes(rawTitle)) {
                            connectedOutputIds.push(rawTitle);
                        }

                        // Do NOT push generic "default" or "Output"
                        return;
                    }

                    // If it is a String / Text / Variable node connected to preview:
                    if (nType.includes('string') || nType.includes('text') || nType.includes('texto') || nType.includes('var') || nTitle.includes('string') || nTitle.includes('text')) {
                        let textVal = (targetNode.properties && (targetNode.properties.value !== undefined ? targetNode.properties.value : targetNode.properties.text)) 
                            ? String(targetNode.properties.value !== undefined ? targetNode.properties.value : targetNode.properties.text)
                            : "";
                        if (!textVal && targetNode.widgets && targetNode.widgets[0]) {
                            textVal = String(targetNode.widgets[0].value || "");
                        }
                        if (textVal && textVal.trim()) {
                            parseAndPushString(textVal);
                        }
                    }

                    // Trace upstream links (e.g. if connected via a pass-through or router node)
                    if (targetNode.inputs && targetNode.inputs.length > 0) {
                        targetNode.inputs.forEach(inp => {
                            const linkIds = [];
                            if (Array.isArray(inp.links) && inp.links.length > 0) {
                                linkIds.push(...inp.links);
                            } else if (inp.link !== null && inp.link !== undefined) {
                                linkIds.push(inp.link);
                            }

                            linkIds.forEach(lId => {
                                const link = window.graph.links[lId];
                                if (link && link.origin_id) {
                                    traceUpstreamNode(link.origin_id);
                                }
                            });
                        });
                    }
                }

                // Check links directly connected to previewNode's inputs (all input slots)
                if (previewNode.inputs && previewNode.inputs.length > 0) {
                    previewNode.inputs.forEach(inp => {
                        const linkIds = [];
                        if (Array.isArray(inp.links) && inp.links.length > 0) {
                            linkIds.push(...inp.links);
                        } else if (inp.link !== null && inp.link !== undefined) {
                            linkIds.push(inp.link);
                        }

                        linkIds.forEach(lId => {
                            const link = window.graph.links[lId];
                            if (link && link.origin_id) {
                                traceUpstreamNode(link.origin_id);
                            }
                        });
                    });
                }

                // Check text properties configured directly on the preview node
                let textIdsStr = (previewNode.properties && previewNode.properties.output_ids !== undefined) ? String(previewNode.properties.output_ids) : "";
                if (!textIdsStr && previewNode.widgets) {
                    const w = previewNode.widgets.find(w => w && (w.property === "output_ids" || w.name === "Output IDs"));
                    if (w && w.value) textIdsStr = String(w.value);
                }

                if (textIdsStr && textIdsStr.trim()) {
                    parseAndPushString(textIdsStr);
                }

                // STRICT: Do NOT fall back to allSalidas or "default".
                // If nothing is connected or typed, connectedOutputIds remains []!
                return connectedOutputIds;
            }

            async function cancelPreview(nodeId, customToastKey = null) {
                const targetId = nodeId !== undefined ? String(nodeId) : window.__pyxis_active_preview_node_id;
                window.__pyxis_is_preview_cancelled = true;
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.cancel_preview_ass === 'function') {
                    try {
                        await window.pywebview.api.cancel_preview_ass();
                    } catch (e) {
                        console.warn("[Pyxis Preview] Error invoking cancel_preview_ass:", e);
                    }
                }
                setAllPlayersLoading(false);
                if (targetId) {
                    setPlayerLoading(targetId, false);
                    const btns = [
                        document.querySelector('#btn-refresh-' + targetId),
                        document.querySelector('#btn-float-refresh-' + targetId),
                        document.querySelector('#btn-ctrl-refresh-' + targetId)
                    ].filter(Boolean);
                    btns.forEach(b => {
                        b.classList.remove('is-refreshing');
                        const tipKey = b.getAttribute('data-i18n-title') || 'preview.refresh_tooltip';
                        b.setAttribute('title', window.t ? window.t(tipKey) : 'Refresh subtitle preview');
                    });
                    const p = activePlayers[targetId];
                    const isSourceSwitchCancel = (customToastKey === "preview.source_switch_cancelled");
                    if (p && p.node && p.node.properties) {
                        if (isSourceSwitchCancel) {
                            await revertToPreviewBase(targetId);
                        } else {
                            const curSource = p.node.properties.preview_source || "base";
                            const hasAegi = Boolean(window.PyxisPreviewConfigAegi && window.PyxisPreviewConfigAegi.dialogues && window.PyxisPreviewConfigAegi.dialogues.length > 0) || Boolean(p.hasAegisub);
                            updateSourceButtonUI(targetId, curSource, hasAegi);
                        }
                    } else {
                        updateSourceButtonUI(targetId, "base", Boolean(window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub));
                    }
                }
                window.__pyxis_is_preview_running = false;
                window.__pyxis_is_preview_or_hardsub_running = false;
                window.__pyxis_active_preview_node_id = null;
                if (typeof window.showPyxisToast === 'function') {
                    const toastKey = customToastKey || "preview.cancelled";
                    const fallbackToast = (toastKey === "preview.source_switch_cancelled")
                        ? "Source switch cancelled; reverting to Base preview"
                        : "Preview generation cancelled";
                    window.showPyxisToast(window.t ? window.t(toastKey) : fallbackToast, "info");
                }
            }

            function updatePlayerProgress(nodeId, data) {
                const targetId = nodeId !== undefined ? String(nodeId) : window.__pyxis_active_preview_node_id;
                if (!targetId) return;
                const p = activePlayers[String(targetId)];
                const backdrop = (p && p.loadingBackdrop) || document.querySelector('#pyxis-player-loading-' + targetId);
                const topBar = (p && p.topProgressBar) || document.querySelector('#pyxis-top-progress-bar-' + targetId);

                let pctVal = 0;
                let infoStr = "";

                if (typeof data === "number") {
                    pctVal = Math.min(100, Math.max(0, Math.floor(data)));
                } else if (typeof data === "object" && data !== null) {
                    const rawPct = (data.percent !== undefined) ? data.percent : (data.pct || 0);
                    pctVal = Math.min(100, Math.max(0, Math.floor(rawPct)));
                    const parts = [];
                    if (data.lines_generated !== undefined && data.lines_generated > 0) {
                        const linesWord = window.t ? (window.t('preview.lines') || window.t('ui.console.lines') || 'lines') : 'lines';
                        parts.push(`${data.lines_generated} ${linesWord}`);
                    }
                    if (data.speed) {
                        parts.push(data.speed);
                    } else if (data.phase) {
                        parts.push(data.phase);
                    }
                    infoStr = parts.join(" • ");
                }

                if (topBar) {
                    const topTrack = (p && p.topProgressTrack) || document.querySelector('#pyxis-top-progress-' + targetId);
                    if (topTrack) {
                        topTrack.classList.add('is-active');
                        if (pctVal > 0) topTrack.classList.remove('is-indeterminate');
                    }
                    topBar.style.width = pctVal + '%';
                }

                if (backdrop) {
                    const track = backdrop.querySelector('.pyxis-player-loading-progress-track');
                    const bar = backdrop.querySelector('.pyxis-player-loading-progress-bar');
                    const pctEl = backdrop.querySelector('.pyxis-player-loading-progress-pct');
                    const infoEl = backdrop.querySelector('.pyxis-player-loading-progress-info');

                    if (track && pctVal > 0) {
                        track.classList.remove('is-indeterminate');
                    }
                    if (bar) {
                        bar.style.width = pctVal + '%';
                    }
                    if (pctEl) {
                        pctEl.textContent = pctVal + '%';
                    }
                    if (infoEl && infoStr) {
                        infoEl.textContent = infoStr;
                    }
                }
            }

            window.__pyxis_on_preview_progress = function(data) {
                if (window.__pyxis_active_preview_node_id) {
                    updatePlayerProgress(window.__pyxis_active_preview_node_id, data);
                } else if (typeof activePlayers === 'object' && activePlayers) {
                    const pKeys = Object.keys(activePlayers);
                    if (pKeys.length > 0) {
                        for (let i = 0; i < pKeys.length; i++) {
                            updatePlayerProgress(pKeys[i], data);
                        }
                    } else {
                        const allBackdrops = document.querySelectorAll('.pyxis-player-loading-backdrop');
                        allBackdrops.forEach(backdrop => {
                            const idMatch = backdrop.id && backdrop.id.match(/^pyxis-player-loading-(.+)$/);
                            if (idMatch) {
                                updatePlayerProgress(idMatch[1], data);
                            }
                        });
                    }
                }
            };

            function setAllPlayersLoading(isLoading, messageKey = "preview.loading") {
                let updated = false;
                if (typeof activePlayers === 'object' && activePlayers) {
                    const pKeys = Object.keys(activePlayers);
                    for (let i = 0; i < pKeys.length; i++) {
                        setPlayerLoading(pKeys[i], isLoading, messageKey);
                        updated = true;
                    }
                }
                if (!updated && window.__pyxis_active_preview_node_id) {
                    setPlayerLoading(window.__pyxis_active_preview_node_id, isLoading, messageKey);
                    updated = true;
                }
                if (!updated) {
                    const allBackdrops = document.querySelectorAll('.pyxis-player-loading-backdrop');
                    allBackdrops.forEach(backdrop => {
                        const idMatch = backdrop.id && backdrop.id.match(/^pyxis-player-loading-(.+)$/);
                        if (idMatch) {
                            setPlayerLoading(idMatch[1], isLoading, messageKey);
                        }
                    });
                }
            }

            window.__pyxis_set_preview_loading = function(isLoading, messageKey) {
                setAllPlayersLoading(isLoading, messageKey);
            };

            async function refreshPreview(nodeId, forceVideoReload = false) {
                if (!window.pywebview || !window.pywebview.api || !window.graph) return;

                const nodeIdStr = String(nodeId);

                // Re-clicking while preview generation is active triggers cancellation
                if (window.__pyxis_is_preview_running && window.__pyxis_active_preview_node_id === nodeIdStr) {
                    await cancelPreview(nodeIdStr);
                    return;
                }

                window.__pyxis_is_preview_running = true;
                window.__pyxis_is_preview_cancelled = false;
                window.__pyxis_active_preview_node_id = nodeIdStr;
                window.__pyxis_is_preview_or_hardsub_running = true;

                if (window.PyxisUndoManager && typeof window.PyxisUndoManager.flushPendingState === "function") {
                    window.PyxisUndoManager.flushPendingState();
                }
                const refBtns = [
                    document.querySelector('#btn-refresh-' + nodeIdStr),
                    document.querySelector('#btn-float-refresh-' + nodeIdStr),
                    document.querySelector('#btn-ctrl-refresh-' + nodeIdStr)
                ].filter(Boolean);
                refBtns.forEach(b => {
                    b.classList.add('is-refreshing');
                    b.setAttribute('title', window.t ? window.t('preview.cancel_refresh') : 'Click to cancel generation');
                });
                setPlayerLoading(nodeIdStr, true, "preview.generating");
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.check_ffmpeg_status === 'function') {
                    try {
                        const ffStatus = await window.pywebview.api.check_ffmpeg_status();
                        if (ffStatus && !ffStatus.available) {
                            showPlayerFFmpegMissingBanner(nodeIdStr);
                            if (typeof window.showFFmpegDownloadModal === 'function') {
                                window.showFFmpegDownloadModal(async (downloaded) => {
                                    if (!downloaded) return;
                                    await loadPreviewMediaAfterFFmpeg(nodeIdStr);
                                });
                            }
                            setPlayerLoading(nodeIdStr, false);
                            refBtns.forEach(b => {
                                b.classList.remove('is-refreshing');
                                b.setAttribute('title', window.t ? window.t('preview.refresh') : 'Refresh Previewer');
                            });
                            window.__pyxis_is_preview_running = false;
                            window.__pyxis_is_preview_or_hardsub_running = false;
                            return;
                        }
                    } catch (e) {
                        console.warn("[Pyxis refreshPreview check_ffmpeg_status warning]", e);
                    }
                }

                try {
                    if (typeof window.syncWidgetsToProperties === "function") {
                        window.syncWidgetsToProperties();
                    }
                    const serialized = window.graph.serialize();

                    const p = activePlayers[nodeIdStr];
                    if (p) p.hasRefreshed = true;
                    const curSource = (p && p.node && p.node.properties && p.node.properties.preview_source) || "base";
                    const connectedOutputIds = (p && p.node) ? resolveConnectedOutputsForPreview(p.node) : [];

                    logPlayer("refreshPreview source=" + curSource + " resolved output IDs: " + JSON.stringify(connectedOutputIds));

                    let updatedInfo = null;
                    if (typeof window.pywebview.api.get_preview_info === 'function') {
                        updatedInfo = await window.pywebview.api.get_preview_info(curSource, connectedOutputIds, serialized);
                        if (window.__pyxis_is_preview_cancelled) return;
                        if (updatedInfo) {
                            window.PyxisPreviewConfig = updatedInfo;
                            if (curSource === "base") window.PyxisPreviewConfigBase = updatedInfo;
                            if (curSource === "aegisub") window.PyxisPreviewConfigAegi = updatedInfo;
                            if (p) {
                                p.hasAegisub = Boolean(updatedInfo.has_aegisub);
                                if (p.node && updatedInfo.aspect_ratio) {
                                    p.node.preview_aspect_ratio = updatedInfo.aspect_ratio;
                                    if (p.node.properties) p.node.properties.preview_aspect_ratio = updatedInfo.aspect_ratio;
                                    const nodeAspect = getNodePreviewAspectRatio(p.node);
                                    if (!p.isPinned) {
                                        const isCustomZoom = Boolean(
                                            (p && p.transformState && p.transformState.isCustom) ||
                                            (p.node && p.node.properties && p.node.properties.viewport_custom)
                                        );
                                        const dynMinW = getDynamicMinPreviewWidth(nodeAspect);
                                        const curW = (p.node.size && p.node.size[0] && p.node.size[0] >= dynMinW) ? p.node.size[0] : Math.max(dynMinW, 520);
                                        const curH = (isCustomZoom && p.node.size && p.node.size[1]) 
                                            ? p.node.size[1] 
                                            : calculatePrevisualizadorNodeHeight(curW, nodeAspect);
                                        p.node.size = [curW, curH];
                                        p.lastW = curW;
                                        p.lastH = curH;
                                        if (p.node.properties) {
                                            p.node.properties.previewer_width = curW;
                                            p.node.properties.previewer_height = curH;
                                        }
                                        if (p.wrapper && !p.isPinned) {
                                            p.wrapper.style.width = Math.max(100, curW - 20) + 'px';
                                            p.wrapper.style.height = Math.max(100, curH - 56) + 'px';
                                        }
                                        if (p.art && typeof p.art.resize === 'function') {
                                            try { p.art.resize(); } catch(e) {}
                                        }
                                        if (typeof p.applyTransform === 'function') {
                                            try { p.applyTransform(); } catch(e) {}
                                        }
                                        if (p.jassub && typeof p.jassub.resize === 'function') {
                                            try { p.jassub.resize(); } catch(e) {}
                                        }
                                        if (typeof p.node.setDirtyCanvas === 'function') p.node.setDirtyCanvas(true, true);
                                        if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                    } else {
                                        const minSz = (typeof p.node.computeSize === 'function') ? p.node.computeSize() : [284, 54];
                                        const minW = Math.max(270, minSz ? minSz[0] : 284);
                                        const curW = (p.node.size && p.node.size[0]) ? p.node.size[0] : minW;
                                        p.node.size = [Math.max(curW, minW), 54];
                                        if (p.wrapper) {
                                            const rect = p.wrapper.getBoundingClientRect();
                                            const curFloatingW = Math.max(340, rect.width || parseFloat(p.wrapper.style.width) || (p.savedFloatingWidth ? parseFloat(p.savedFloatingWidth) : 560));
                                            const curFloatingH = Math.max(200, rect.height || parseFloat(p.wrapper.style.height) || (p.savedFloatingHeight ? parseFloat(p.savedFloatingHeight) : 380));
                                            p.wrapper.style.setProperty('width', curFloatingW + 'px', 'important');
                                            p.wrapper.style.setProperty('height', curFloatingH + 'px', 'important');
                                            p.savedFloatingWidth = curFloatingW + 'px';
                                            p.savedFloatingHeight = curFloatingH + 'px';
                                            if (p.art && typeof p.art.resize === 'function') {
                                                try { p.art.resize(); } catch(e) {}
                                            }
                                            if (typeof p.applyTransform === 'function') {
                                                try { p.applyTransform(); } catch(e) {}
                                            }
                                            if (p.jassub && typeof p.jassub.resize === 'function') {
                                                try { p.jassub.resize(); } catch(e) {}
                                            }
                                        }
                                        if (typeof p.node.setDirtyCanvas === 'function') p.node.setDirtyCanvas(true, true);
                                        if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                    }
                                }
                                updateSourceButtonUI(nodeIdStr, curSource, p.hasAegisub);
                                updateRenderModeButtonUI(nodeIdStr, getNodeRenderMode(p.node));
                                updatePreviewMetadataBadges(nodeIdStr, updatedInfo);
                                if (updatedInfo && updatedInfo.is_audio_decoupled) {
                                    p.isDecoupled = true;
                                    if (p.userVolume === undefined && p.art) {
                                        p.userVolume = (typeof p.art.volume === 'number' && p.art.volume > 0) ? p.art.volume : 0.5;
                                    }
                                    if (p.userMuted === undefined && p.art) {
                                        p.userMuted = Boolean(p.art.muted);
                                    }
                                    if (p.art && p.art.video) {
                                        p.art.video.muted = true;
                                        p.art.video.defaultMuted = true;
                                    }
                                } else {
                                    p.isDecoupled = false;
                                }
                            }
                        }
                    }

                    if (window.__pyxis_is_preview_cancelled) return;

                    let videoChanged = false;
                    if (typeof window.pywebview.api.get_preview_video_data_url === 'function') {
                        const newVideoUrl = await window.pywebview.api.get_preview_video_data_url(curSource, connectedOutputIds, serialized);
                        if (window.__pyxis_is_preview_cancelled) return;
                        if (newVideoUrl && p && p.art) {
                            if (forceVideoReload || p.videoUrl !== newVideoUrl) {
                                videoChanged = true;
                                p.videoUrl = newVideoUrl;
                                try {
                                    await safeArtSwitchUrl(p.art, newVideoUrl);
                                } catch (e) {
                                    console.warn("[Pyxis Artplayer switchUrl warning]", e);
                                }
                            }
                        }
                    }

                    if (videoChanged && typeof window.pywebview.api.get_preview_audio_data_url === 'function') {
                        try {
                            const refAudioUrl = await window.pywebview.api.get_preview_audio_data_url(curSource, connectedOutputIds, serialized);
                            if (refAudioUrl) {
                                setupDecoupledAudio(p, refAudioUrl);
                            } else {
                                teardownDecoupledAudio(p);
                            }
                        } catch (e) {
                            console.warn("[Pyxis refreshPreview audio update warning]", e);
                        }
                    }

                    if (window.__pyxis_is_preview_cancelled) return;

                    if (!p.fontsInjected && typeof window.pywebview.api.get_preview_fonts_map === 'function' && p && p.jassub) {
                        try {
                            const refFontsMap = await window.pywebview.api.get_preview_fonts_map(curSource);
                            if (window.__pyxis_is_preview_cancelled) return;
                            if (refFontsMap && typeof refFontsMap === 'object') {
                                injectFontsIntoJassub(p.jassub, refFontsMap);
                                p.fontsInjected = true;
                            }
                        } catch (e) {
                            console.warn("[Pyxis refreshPreview font update warning]", e);
                        }
                    }

                    if (window.__pyxis_is_preview_cancelled) return;

                    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.cancel_ass_telemetry === 'function') {
                        try { window.pywebview.api.cancel_ass_telemetry(); } catch (e) {}
                    }

                    const assFilename = 'preview_dummy_' + nodeIdStr + '.ass';
                    const res = await window.pywebview.api.generate_preview_ass(serialized, connectedOutputIds, assFilename, undefined, undefined, curSource);
                    if (window.__pyxis_is_preview_cancelled || (res && res.cancelled)) {
                        return;
                    }

                    let trackUpdated = false;
                    if (res && (res === true || res.success) && res.content !== undefined) {
                        const targetCfg = (curSource === "aegisub" && window.PyxisPreviewConfigAegi)
                            ? window.PyxisPreviewConfigAegi
                            : ((curSource === "base" && window.PyxisPreviewConfigBase) ? window.PyxisPreviewConfigBase : window.PyxisPreviewConfig);
                        if (targetCfg && typeof res.clip_start_sec === 'number' && typeof res.clip_end_sec === 'number') {
                            targetCfg.clip_start_sec = res.clip_start_sec;
                            targetCfg.clip_end_sec = res.clip_end_sec;
                            targetCfg.clip_duration_sec = res.clip_duration_sec;
                            targetCfg.clip_start_ms = res.clip_start_ms;
                            if (window.PyxisPreviewConfig && window.PyxisPreviewConfig !== targetCfg) {
                                window.PyxisPreviewConfig.clip_start_sec = res.clip_start_sec;
                                window.PyxisPreviewConfig.clip_end_sec = res.clip_end_sec;
                                window.PyxisPreviewConfig.clip_duration_sec = res.clip_duration_sec;
                                window.PyxisPreviewConfig.clip_start_ms = res.clip_start_ms;
                            }
                        }
                        if (p && p.jassub) {
                            await updateJassubTrack(p.jassub, res.content, nodeIdStr);
                            trackUpdated = true;
                        }
                    }
                    if (!trackUpdated && connectedOutputIds.length === 0 && typeof window.pywebview.api.get_initial_base_ass === 'function' && p && p.jassub) {
                        const baseAss = await window.pywebview.api.get_initial_base_ass(curSource, connectedOutputIds, serialized);
                        if (window.__pyxis_is_preview_cancelled) return;
                        if (baseAss) {
                            await updateJassubTrack(p.jassub, baseAss, nodeIdStr);
                            trackUpdated = true;
                        }
                    }
                    if (p && p.art) {
                        const b = getPreviewBounds(nodeIdStr);
                        const curT = p.art.currentTime || 0;
                        if (videoChanged || curT < b.winStart - 0.05 || curT > b.winEnd + 0.05) {
                            try { p.art.seek = b.winStart; } catch (e) {}
                            try { p.art.currentTime = b.winStart; } catch (e) {}
                        }
                        if (typeof p.updateTimeUI === 'function') {
                            try { p.updateTimeUI(); } catch (e) {}
                        }
                        if (videoChanged && typeof p.applyTransform === 'function') {
                            try { p.applyTransform(); } catch(e) {}
                        }
                    }
                    if (typeof window.showPyxisToast === 'function') {
                        if (connectedOutputIds.length === 0) {
                            window.showPyxisToast(window.t ? window.t("preview.restored_base") : "Previsualización restablecida al subtítulo base original (sin salidas conectadas)", "info");
                        } else if (trackUpdated) {
                            window.showPyxisToast("toast.effect_generated_preview", "success");
                        }
                    }
                    if (connectedOutputIds.length > 0) {
                        if (window.PyxisTelemetry && typeof window.PyxisTelemetry.triggerFromPreviewer === 'function') {
                            setTimeout(() => {
                                window.PyxisTelemetry.triggerFromPreviewer(nodeIdStr, serialized, connectedOutputIds, curSource, false);
                            }, 30);
                        }
                    } else {
                        if (p) p.hasRefreshed = false;
                        if (window.PyxisTelemetry && typeof window.PyxisTelemetry.clearData === 'function') {
                            window.PyxisTelemetry.clearData(true);
                        }
                    }
                    if (typeof updateInNodePlayersPosition === 'function') {
                        updateInNodePlayersPosition();
                    }
                    if (p && p.art && typeof p.art.resize === 'function') {
                        try { p.art.resize(); } catch(e) {}
                    }
                    if (p && typeof p.applyTransform === 'function') {
                        p.applyTransform();
                    }
                    if (p && p.jassub && typeof p.jassub.resize === 'function') {
                        try { p.jassub.resize(); } catch(e) {}
                    }
                } catch (err) {
                    console.error("[Pyxis Preview Refresh Error]", err);
                } finally {
                    refBtns.forEach(b => {
                        b.classList.remove('is-refreshing');
                        const tipKey = b.getAttribute('data-i18n-title') || 'preview.refresh_tooltip';
                        b.setAttribute('title', window.t ? window.t(tipKey) : 'Refresh subtitle preview');
                    });
                    setPlayerLoading(nodeIdStr, false);
                    window.__pyxis_is_preview_running = false;
                    window.__pyxis_active_preview_node_id = null;
                    setTimeout(() => {
                        window.__pyxis_is_preview_or_hardsub_running = false;
                    }, 400);
                }
            }

            async function renderHardsub(nodeId) {
                if (!window.pywebview || !window.pywebview.api || !window.graph) return;
                window.__pyxis_is_preview_or_hardsub_running = true;
                const watchdogTimer = setTimeout(() => {
                    if (window.__pyxis_is_preview_or_hardsub_running) {
                        console.warn("[Pyxis Hardsub] Hardsub watchdog timeout triggered");
                        window.__pyxis_is_preview_or_hardsub_running = false;
                        const btns = [
                            document.querySelector('#btn-hardsub-' + nodeId),
                            document.querySelector('#btn-float-hardsub-' + nodeId),
                            document.querySelector('#btn-ctrl-hardsub-' + nodeId)
                        ].filter(Boolean);
                        btns.forEach(b => b.classList.remove('is-rendering-hardsub'));
                    }
                }, 60000);
                if (window.PyxisUndoManager && typeof window.PyxisUndoManager.flushPendingState === "function") {
                    window.PyxisUndoManager.flushPendingState();
                }
                const hardBtns = [
                    document.querySelector('#btn-hardsub-' + nodeId),
                    document.querySelector('#btn-float-hardsub-' + nodeId),
                    document.querySelector('#btn-ctrl-hardsub-' + nodeId)
                ].filter(Boolean);
                hardBtns.forEach(b => b.classList.add('is-rendering-hardsub'));

                try {
                    if (typeof window.syncWidgetsToProperties === "function") {
                        window.syncWidgetsToProperties();
                    }
                    const serialized = window.graph.serialize();

                    const p = activePlayers[nodeId];
                    const curSource = (p && p.node && p.node.properties && p.node.properties.preview_source) || "base";
                    const connectedOutputIds = (p && p.node) ? resolveConnectedOutputsForPreview(p.node) : [];
                    if (connectedOutputIds.length === 0) {
                        if (typeof window.showPyxisToast === 'function') {
                            window.showPyxisToast(window.t ? window.t("preview.no_outputs_hardsub_warning") : "No outputs connected or specified for rendering", "warning");
                        }
                        return;
                    }

                    const targetArg = connectedOutputIds;
                    const clockNum = String(Math.floor(Date.now()) % 1000000).padStart(6, '0');
                    const mp4Filename = 'Effect_' + clockNum + '.mp4';

                    // Verify if FFmpeg is available before starting hardsub encoding
                    if (window.pywebview && window.pywebview.api && window.pywebview.api.check_ffmpeg_status) {
                        const ffStatus = await window.pywebview.api.check_ffmpeg_status();
                        if (ffStatus && !ffStatus.available) {
                            hardBtns.forEach(b => b.classList.remove('is-rendering-hardsub'));
                            window.__pyxis_is_preview_or_hardsub_running = false;
                            clearTimeout(watchdogTimer);
                            if (window.showFFmpegDownloadModal) {
                                window.showFFmpegDownloadModal(async (downloaded) => {
                                    if (downloaded) {
                                        await renderHardsub(nodeId);
                                    }
                                });
                            } else if (typeof window.showPyxisToast === 'function') {
                                window.showPyxisToast(window.t ? window.t("preview.hardsub_need_ffmpeg") : "FFmpeg is required to render hardsub videos.", "warning");
                            }
                            return;
                        }
                    }

                    const res = await window.pywebview.api.render_preview_hardsub(serialized, targetArg, mp4Filename, curSource);
                    if (res && res.cancelled) {
                        if (typeof window.showPyxisToast === 'function') {
                            window.showPyxisToast(window.t ? window.t("preview.hardsub_cancelled") : "Hardsub rendering cancelled", "warning");
                        }
                        return;
                    }
                    if (res && (res === true || res.success)) {
                        if (typeof window.showPyxisToast === 'function') {
                            const pathText = res.saved_path ? (" at " + res.saved_path) : "";
                            const successMsg = window.t ? window.t("preview.hardsub_success") : "Hardsub rendered successfully";
                            window.showPyxisToast(successMsg + pathText, "success");
                        }
                    } else if (res && res.error) {
                        if (typeof window.showPyxisToast === 'function') {
                            const errorMsg = window.t ? window.t("preview.hardsub_error", { error: res.error }) : ("Hardsub error: " + res.error);
                            window.showPyxisToast(errorMsg, "error");
                        }
                    }
                } catch (err) {
                    console.error("[Pyxis Hardsub Render Error]", err);
                } finally {
                    clearTimeout(watchdogTimer);
                    hardBtns.forEach(b => b.classList.remove('is-rendering-hardsub'));
                    setTimeout(() => {
                        window.__pyxis_is_preview_or_hardsub_running = false;
                    }, 400);
                }
            }

            function togglePinPreview(nodeId) {
                const p = activePlayers[nodeId];
                if (!p || !p.wrapper) return;

                let floatingContainer = document.getElementById('pyxis-floating-players-container');
                if (!floatingContainer) {
                    floatingContainer = document.createElement('div');
                    floatingContainer.id = 'pyxis-floating-players-container';
                    document.body.appendChild(floatingContainer);
                }

                const nodeIdStr = String(nodeId);
                p.isPinned = !p.isPinned;
                if (p.transformState) {
                    p.transformState.lastPW = null;
                    p.transformState.lastPH = null;
                }

                const btnPin = p.headerActions ? p.headerActions.querySelector('#btn-pin-' + nodeIdStr) : null;

                if (p.isPinned) {
                    if (!p.originalSize && p.node) {
                        if (p.node.properties && p.node.properties.previewer_width && p.node.properties.previewer_height && Number(p.node.properties.previewer_height) >= 100) {
                            p.originalSize = [Number(p.node.properties.previewer_width), Number(p.node.properties.previewer_height)];
                        } else if (p.node.size) {
                            p.originalSize = [p.node.size[0], p.node.size[1]];
                        }
                    }
                    if (!p.originalComputeSize && p.node) {
                        p.originalComputeSize = p.node.computeSize;
                    }
                    if (!p.originalOnResize && p.node) {
                        p.originalOnResize = p.node.onResize;
                    }
                    if (p.node) {
                        const minW = (typeof p.node.computeSize === 'function')
                            ? p.node.computeSize()[0]
                            : ((typeof p.originalComputeSize === 'function') ? p.originalComputeSize.call(p.node)[0] : 284);
                        const savedPinnedW = (p.node.properties && p.node.properties.pinned_width) ? Number(p.node.properties.pinned_width) : 0;
                        const targetW = (savedPinnedW >= minW) ? savedPinnedW : minW;
                        p.node.size[0] = targetW;
                        p.node.size[1] = 54;
                        p.node.lastW = targetW;
                        p.node.lastH = 54;
                        if (!p.node.properties) p.node.properties = {};
                        p.node.properties.is_pinned = true;
                        p.node.properties.pinned_width = targetW;

                        p.node.computeSize = function() {
                            if (typeof p.originalComputeSize === 'function') {
                                const sz = p.originalComputeSize.call(this);
                                return [sz ? sz[0] : 284, 54];
                            }
                            return [284, 54];
                        };
                        p.node.onResize = function(size) {
                            const sz = (typeof this.computeSize === 'function') ? this.computeSize() : [270, 54];
                            const reqW = sz ? sz[0] : 270;
                            size[0] = Math.max(reqW, Math.round(size[0]));
                            size[1] = 54;
                            this.size[0] = size[0];
                            this.size[1] = 54;
                            this.lastW = size[0];
                            this.lastH = 54;
                            if (!this.properties) this.properties = {};
                            this.properties.pinned_width = size[0];
                            if (window.__pyxis_schedule_save) {
                                window.__pyxis_schedule_save(50);
                            }
                        };
                        if (typeof p.node.setDirtyCanvas === 'function') {
                            p.node.setDirtyCanvas(true, true);
                        }
                        if (window.canvas) {
                            window.canvas.setDirty(true, true);
                            window.canvas.draw(true, true);
                        }
                    }

                    if (btnPin) {
                        btnPin.classList.add('active');
                        btnPin.setAttribute('aria-label', window.t ? window.t('preview.unpin') : 'Unpin player');
                        btnPin.setAttribute('data-i18n-aria-label', 'preview.unpin');
                    }
                    if (p.headerActions) {
                        p.headerActions.classList.add('is-pinned');
                    }

                    const curSource = (p.node && p.node.properties && p.node.properties.preview_source) || "base";
                    const isBase = curSource === "base";
                    const hasAegi = (p.hasAegisub !== undefined) ? p.hasAegisub : (window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub);
                    const sourceTip = isBase 
                        ? (window.t ? window.t("preview.source_base_tooltip") : "Source: Base Template (preview_base.ass) - Click to switch to Aegisub") 
                        : (window.t ? window.t("preview.source_aegisub_tooltip") : "Source: Open File in Aegisub - Click to switch to Base");
                    const curRenderFloat = getNodeRenderMode(p.node || nodeIdStr);
                    const isMpvFloat = curRenderFloat === "mpv";
                    const renderFloatTipKey = getRenderModeTooltipKey(curRenderFloat);
                    const renderFloatTip = getRenderModeTooltipText(curRenderFloat);

                    let floatHeader = p.wrapper.querySelector('.pyxis-floating-header');
                    if (!floatHeader) {
                        floatHeader = document.createElement('div');
                        floatHeader.className = 'pyxis-floating-header';
                        floatHeader.innerHTML = `
                            <div class="pyxis-floating-header-title">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 17v5"/><path d="M9 2v3l-2 5v3h10v-3l-2-5V2z"/>
                                </svg>
                                <span data-i18n="preview.pinned_title">${window.t ? window.t('preview.pinned_title') : 'Previewer (Pinned)'}</span>
                            </div>
                            <div class="pyxis-floating-header-actions">
                                <button id="btn-float-source-${nodeIdStr}" class="pyxis-header-icon-btn pyxis-btn-source ${!hasAegi ? 'disabled' : ''}" aria-label="${sourceTip}" data-i18n-aria-label="${isBase ? 'preview.source_base_tooltip' : 'preview.source_aegisub_tooltip'}" ${!hasAegi ? 'disabled' : ''}>
                                    <img src="${isBase ? 'CD.png' : 'Aegisub_logo.png'}" alt="${curSource}" />
                                </button>
                                <button id="btn-float-rendermode-${nodeIdStr}" class="pyxis-header-icon-btn pyxis-btn-rendermode ${isMpvFloat ? 'is-mpv-mode' : ''}" aria-label="${renderFloatTip}" data-i18n-aria-label="${renderFloatTipKey}">
                                    ${getRenderModeSvgHtml(curRenderFloat)}
                                </button>
                                <button id="btn-float-unpin-${nodeIdStr}" class="pyxis-header-icon-btn active" aria-label="${window.t ? window.t('preview.unpin') : 'Unpin player'}" data-i18n-aria-label="preview.unpin">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 17v5"/><path d="M9 2v3l-2 5v3h10v-3l-2-5V2z"/>
                                    </svg>
                                </button>
                                <button id="btn-float-refresh-${nodeIdStr}" class="pyxis-header-icon-btn pyxis-btn-refresh-preview" aria-label="${window.t ? window.t('preview.refresh') : 'Refresh Previewer'}" data-i18n-aria-label="preview.refresh">
                                    <svg class="pyxis-icon-refresh" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
                                    </svg>
                                    <svg class="pyxis-icon-cancel" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                </button>
                                <button id="btn-float-hardsub-${nodeIdStr}" class="pyxis-header-icon-btn" aria-label="${window.t ? window.t('preview.hardsub') : 'Render Hardsub with FFmpeg'}" data-i18n-aria-label="preview.hardsub">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M4 11v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8H4z"/>
                                        <path d="M4 11V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v6H4z"/>
                                        <path d="M9 3l-2 8"/><path d="M15 3l-2 8"/>
                                    </svg>
                                </button>
                            </div>
                        `;
                        p.wrapper.insertBefore(floatHeader, p.wrapper.firstChild);

                        const bSource = floatHeader.querySelector('#btn-float-source-' + nodeIdStr);
                        const bRenderMode = floatHeader.querySelector('#btn-float-rendermode-' + nodeIdStr);
                        const bUnpin = floatHeader.querySelector('#btn-float-unpin-' + nodeIdStr);
                        const bRef = floatHeader.querySelector('#btn-float-refresh-' + nodeIdStr);
                        const bHard = floatHeader.querySelector('#btn-float-hardsub-' + nodeIdStr);

                        const stopHeaderPointerEvents = (btn) => {
                            if (!btn) return;
                            btn.addEventListener('pointerdown', (e) => e.stopPropagation());
                            btn.addEventListener('mousedown', (e) => e.stopPropagation());
                        };

                        if (bSource) {
                            stopHeaderPointerEvents(bSource);
                            bSource.onclick = (e) => { e.stopPropagation(); togglePreviewSource(nodeIdStr); };
                            attachPyxisDelayTooltip(bSource, () => {
                                const curSrc = (p && p.node && p.node.properties && p.node.properties.preview_source) || "base";
                                const k = curSrc === "base" ? "preview.source_base_tooltip" : "preview.source_aegisub_tooltip";
                                return window.t ? window.t(k) : (curSrc === "base" ? "Source: Base Template (preview_base.ass) - Click to switch to Aegisub" : "Source: Open File in Aegisub - Click to switch to Base");
                            }, 1000);
                        }
                        if (bRenderMode) {
                            stopHeaderPointerEvents(bRenderMode);
                            bRenderMode.onclick = (e) => { e.stopPropagation(); togglePreviewRenderMode(nodeIdStr); };
                            attachPyxisDelayTooltip(bRenderMode, () => getRenderModeTooltipText(getNodeRenderMode(nodeIdStr)), 1000);
                        }
                        if (bUnpin) {
                            stopHeaderPointerEvents(bUnpin);
                            bUnpin.onclick = (e) => { e.stopPropagation(); togglePinPreview(nodeIdStr); };
                            attachPyxisDelayTooltip(bUnpin, () => (window.t ? window.t("preview.unpin") : "Unpin player"), 1000);
                        }
                        if (bRef) {
                            stopHeaderPointerEvents(bRef);
                            bRef.onclick = (e) => { e.stopPropagation(); refreshPreview(nodeIdStr); };
                            attachPyxisDelayTooltip(bRef, () => {
                                if (bRef.classList.contains("is-refreshing")) {
                                    return window.t ? window.t("preview.cancel_refresh") : "Cancel preview generation";
                                }
                                return window.t ? window.t("preview.refresh") : "Refresh Previewer";
                            }, 600);
                        }
                        if (bHard) {
                            stopHeaderPointerEvents(bHard);
                            bHard.onclick = (e) => { e.stopPropagation(); renderHardsub(nodeIdStr); };
                            attachPyxisDelayTooltip(bHard, () => (window.t ? window.t("preview.hardsub") : "Render Hardsub with FFmpeg"), 1000);
                        }

                        let isDragging = false;
                        let startX = 0, startY = 0;
                        let initialTop = 20, initialLeft = 20;
                        let cachedTopBarH = 52;
                        let cachedMinTop = 60;
                        let cachedMaxLeft = 0;
                        let cachedMaxTop = 0;
                        let dragRafId = null;
                        let pendingLeft = 0;
                        let pendingTop = 0;

                        floatHeader.addEventListener('pointerdown', (e) => {
                            if (e.target.closest('.pyxis-header-icon-btn')) {
                                return;
                            }
                            isDragging = true;
                            window.__pyxisDraggingFloating = true;
                            startX = e.clientX;
                            startY = e.clientY;
                            const rect = p.wrapper.getBoundingClientRect();
                            initialTop = rect.top;
                            initialLeft = rect.left;
                            pendingLeft = initialLeft;
                            pendingTop = initialTop;

                            const topBar = document.querySelector('.top-bar');
                            cachedTopBarH = (topBar && topBar.offsetHeight) ? topBar.offsetHeight : 52;
                            cachedMinTop = cachedTopBarH + 8;
                            cachedMaxLeft = window.innerWidth - rect.width;
                            cachedMaxTop = window.innerHeight - rect.height;

                            p.wrapper.style.transition = 'none';
                            floatHeader.setPointerCapture(e.pointerId);
                            e.stopPropagation();
                        });

                        floatHeader.addEventListener('pointermove', (e) => {
                            if (!isDragging) return;
                            const dx = e.clientX - startX;
                            const dy = e.clientY - startY;
                            let newLeft = initialLeft + dx;
                            let newTop = initialTop + dy;

                            newLeft = Math.max(0, Math.min(newLeft, cachedMaxLeft));
                            newTop = Math.max(cachedMinTop, Math.min(newTop, cachedMaxTop));

                            pendingLeft = newLeft;
                            pendingTop = newTop;

                            if (!dragRafId) {
                                dragRafId = requestAnimationFrame(() => {
                                    dragRafId = null;
                                    if (!isDragging) return;
                                    p.wrapper.style.left = pendingLeft + 'px';
                                    p.wrapper.style.top = pendingTop + 'px';
                                });
                            }
                            e.stopPropagation();
                        });

                        const stopDrag = (e) => {
                            if (!isDragging) return;
                            isDragging = false;
                            window.__pyxisDraggingFloating = false;
                            if (dragRafId) {
                                cancelAnimationFrame(dragRafId);
                                dragRafId = null;
                            }
                            try { floatHeader.releasePointerCapture(e.pointerId); } catch (err) {}

                            p.wrapper.style.left = pendingLeft + 'px';
                            p.wrapper.style.top = pendingTop + 'px';
                            p.wrapper.style.transition = 'transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), top 0.35s cubic-bezier(0.16, 1, 0.3, 1), left 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s ease';

                            const rect = p.wrapper.getBoundingClientRect();
                            const snapThreshold = 35;
                            const wWidth = window.innerWidth;
                            const wHeight = window.innerHeight;
                            const snapTop = cachedTopBarH + 16;
                            const snapMargin = 20;

                            let finalTop = rect.top;
                            let finalLeft = rect.left;
                            let snapped = false;

                            const isNearTop = Math.abs(rect.top - snapTop) < snapThreshold || rect.top < (cachedTopBarH + snapThreshold);
                            const isNearBottom = (wHeight - rect.bottom) < snapThreshold;
                            const isNearLeft = rect.left < snapThreshold;
                            const isNearRight = (wWidth - rect.right) < snapThreshold;

                            if (isNearLeft && isNearTop) {
                                finalLeft = snapMargin;
                                finalTop = snapTop;
                                snapped = true;
                            } else if (isNearRight && isNearTop) {
                                finalLeft = wWidth - rect.width - snapMargin;
                                finalTop = snapTop;
                                snapped = true;
                            } else if (isNearLeft && isNearBottom) {
                                finalLeft = snapMargin;
                                finalTop = wHeight - rect.height - snapMargin;
                                snapped = true;
                            } else if (isNearRight && isNearBottom) {
                                finalLeft = wWidth - rect.width - snapMargin;
                                finalTop = wHeight - rect.height - snapMargin;
                                snapped = true;
                            }

                            if (snapped) {
                                p.wrapper.style.left = finalLeft + 'px';
                                p.wrapper.style.top = finalTop + 'px';
                                p.wrapper.classList.remove('pyxis-magnetic-pulse');
                                void p.wrapper.offsetWidth;
                                p.wrapper.classList.add('pyxis-magnetic-pulse');
                            }
                            e.stopPropagation();
                        };

                        floatHeader.addEventListener('pointerup', stopDrag);
                        floatHeader.addEventListener('pointercancel', stopDrag);
                    } else {
                        floatHeader.style.display = 'flex';
                    }

                    floatingContainer.appendChild(p.wrapper);
                    p.wrapper.classList.add('pyxis-floating-player-wrapper');

                    const topBar = document.querySelector('.top-bar');
                    const topBarH = (topBar && topBar.offsetHeight) ? topBar.offsetHeight : 52;
                    const defaultTop = (topBarH + 16) + 'px';
                    const defaultLeft = '20px';

                    const currentAspect = getNodePreviewAspectRatio(p.node) || (16 / 9);
                    const initFloatingW = 560;
                    const initFloatingH = Math.round(initFloatingW / currentAspect) + 98;

                    const savedPropLeft = (p.node && p.node.properties && p.node.properties.floating_x !== undefined) ? (p.node.properties.floating_x + 'px') : null;
                    const savedPropTop = (p.node && p.node.properties && p.node.properties.floating_y !== undefined) ? (p.node.properties.floating_y + 'px') : null;
                    const savedPropWidth = (p.node && p.node.properties && p.node.properties.floating_width !== undefined) ? (p.node.properties.floating_width + 'px') : null;
                    const savedPropHeight = (p.node && p.node.properties && p.node.properties.floating_height !== undefined) ? (p.node.properties.floating_height + 'px') : null;

                    const userSavedRatio = (savedPropWidth && savedPropHeight && parseFloat(savedPropHeight) > 0)
                        ? (parseFloat(savedPropWidth) / parseFloat(savedPropHeight))
                        : (p.savedFloatingWidth && p.savedFloatingHeight && parseFloat(p.savedFloatingHeight) > 0
                            ? (parseFloat(p.savedFloatingWidth) / parseFloat(p.savedFloatingHeight))
                            : null);

                    let curFloatingW = p.savedFloatingWidth 
                        ? Math.max(340, parseFloat(p.savedFloatingWidth)) 
                        : (savedPropWidth ? Math.max(340, parseFloat(savedPropWidth)) : initFloatingW);
                    let expectedFloatingH = Math.round(curFloatingW / currentAspect) + 98;
                    let targetWVal = curFloatingW;
                    let targetHVal = p.savedFloatingHeight ? parseFloat(p.savedFloatingHeight) : (savedPropHeight ? parseFloat(savedPropHeight) : expectedFloatingH);
                    if (!targetHVal || (!savedPropHeight && !p.savedFloatingHeight && Math.abs(targetHVal - expectedFloatingH) > 8)) {
                        targetHVal = expectedFloatingH;
                    }

                    // Viewport-aware sizing limits: ensure the floating player box fits into the viewport
                    // If scaling is needed, strictly preserve the user's custom saved aspect ratio (userSavedRatio)
                    const maxAllowedW = Math.max(340, window.innerWidth - 20);
                    const maxAllowedH = Math.max(200, window.innerHeight - topBarH - 20);
                    if (targetWVal > maxAllowedW) {
                        targetWVal = maxAllowedW;
                        targetHVal = userSavedRatio ? Math.round(targetWVal / userSavedRatio) : (Math.round(targetWVal / currentAspect) + 98);
                    }
                    if (targetHVal > maxAllowedH) {
                        targetHVal = maxAllowedH;
                        targetWVal = Math.max(340, userSavedRatio ? Math.round(targetHVal * userSavedRatio) : Math.round((targetHVal - 98) * currentAspect));
                    }

                    const rawTargetLeft = p.savedFloatingLeft || savedPropLeft || defaultLeft;
                    const rawTargetTop = p.savedFloatingTop || savedPropTop || defaultTop;
                    let parsedLeft = parseFloat(rawTargetLeft);
                    let parsedTop = parseFloat(rawTargetTop);
                    if (isNaN(parsedLeft)) parsedLeft = 20;
                    if (isNaN(parsedTop)) parsedTop = topBarH + 16;

                    // Clamping: ensure the entire player box (including bottom controls) remains completely visible within viewport
                    const minLeft = 10;
                    const maxLeft = Math.max(minLeft, window.innerWidth - targetWVal - 10);
                    const minTop = topBarH + 8;
                    const maxTop = Math.max(minTop, window.innerHeight - targetHVal - 10);

                    const clampedLeft = Math.max(minLeft, Math.min(parsedLeft, maxLeft));
                    const clampedTop = Math.max(minTop, Math.min(parsedTop, maxTop));

                    const targetW = targetWVal + 'px';
                    const targetH = targetHVal + 'px';
                    const targetLeft = clampedLeft + 'px';
                    const targetTop = clampedTop + 'px';

                    p.savedFloatingLeft = targetLeft;
                    p.savedFloatingTop = targetTop;
                    p.savedFloatingWidth = targetW;
                    p.savedFloatingHeight = targetH;

                    p.wrapper.style.width = targetW;
                    p.wrapper.style.height = targetH;
                    p.wrapper.style.left = targetLeft;
                    p.wrapper.style.top = targetTop;
                    p.wrapper.style.transform = 'none';

                    function attachPyxisFloatingResizers(pObj) {
                        if (!pObj || !pObj.wrapper) return;
                        if (pObj.wrapper.querySelector('.pyxis-floating-resizer')) return;

                        const handlesList = ['nw', 'ne', 'sw', 'se'];
                        handlesList.forEach(handleType => {
                            const handle = document.createElement('div');
                            handle.className = `pyxis-floating-resizer ${handleType}`;
                            pObj.wrapper.appendChild(handle);

                            let isResizing = false;
                            let startX = 0, startY = 0;
                            let startW = 0, startH = 0;
                            let startTop = 0, startLeft = 0;
                            let startRight = 0, startBottom = 0;
                            let currentW = 0, currentH = 0, currentLeft = 0, currentTop = 0;
                            let cachedTopBarH = 52;
                            let cachedMinTop = 60;
                            let cachedMaxW = 1200;
                            let cachedAspect = 16 / 9;

                            handle.addEventListener('pointerdown', (e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                if (pObj && typeof pObj.cancelResetAnimation === 'function') {
                                    pObj.cancelResetAnimation();
                                }
                                isResizing = true;
                                pObj.isResizing = true;
                                window.__pyxisDraggingFloating = true;
                                startX = e.clientX;
                                startY = e.clientY;
                                const rect = pObj.wrapper.getBoundingClientRect();
                                startW = rect.width;
                                startH = rect.height;
                                startTop = rect.top;
                                startLeft = rect.left;
                                startRight = rect.left + rect.width;
                                startBottom = rect.top + rect.height;
                                currentW = startW;
                                currentH = startH;
                                currentLeft = startLeft;
                                currentTop = startTop;

                                const topBar = document.querySelector('.top-bar');
                                cachedTopBarH = (topBar && topBar.offsetHeight) ? topBar.offsetHeight : 52;
                                cachedMinTop = cachedTopBarH + 8;
                                cachedMaxW = window.innerWidth - 20;
                                cachedAspect = (typeof getNodePreviewAspectRatio === 'function')
                                    ? (getNodePreviewAspectRatio(pObj.node) || (16 / 9))
                                    : (16 / 9);

                                document.body.classList.add('pyxis-resizing-active');
                                pObj.wrapper.classList.add('is-resizing');
                                pObj.wrapper.style.transition = 'none';
                                pObj.activeResizeHandle = handleType;
                                handle.setPointerCapture(e.pointerId);
                            });

                            let resizeRafId = null;
                            let pendingW = startW, pendingH = startH, pendingLeft = startLeft, pendingTop = startTop;

                            const onResizeMove = (e) => {
                                if (!isResizing) return;
                                e.preventDefault();
                                e.stopPropagation();

                                const dx = e.clientX - startX;
                                const dy = e.clientY - startY;

                                const minW = 340;
                                const minH = 200;
                                const chromeH = 98;
                                const curAspect = cachedAspect;
                                const margin = 8;
                                const minLeft = margin;
                                const maxRight = window.innerWidth - margin;
                                const minTop = cachedMinTop;
                                const maxBottom = window.innerHeight - margin;

                                const isZoomed = Boolean(pObj && pObj.transformState && pObj.transformState.isCustom);

                                let newW = startW;
                                let newH = startH;
                                let newLeft = startLeft;
                                let newTop = startTop;

                                if (isZoomed) {
                                    if (handleType === 'se') {
                                        newW = Math.max(minW, Math.min(cachedMaxW, startW + dx));
                                        if (startLeft + newW > maxRight) newW = maxRight - startLeft;
                                        newH = Math.max(minH, startH + dy);
                                        if (startTop + newH > maxBottom) newH = maxBottom - startTop;
                                        newLeft = startLeft;
                                        newTop = startTop;
                                    } else if (handleType === 'sw') {
                                        newW = Math.max(minW, Math.min(cachedMaxW, startW - dx));
                                        newLeft = startRight - newW;
                                        if (newLeft < minLeft) {
                                            newLeft = minLeft;
                                            newW = startRight - newLeft;
                                        }
                                        newH = Math.max(minH, startH + dy);
                                        if (startTop + newH > maxBottom) newH = maxBottom - startTop;
                                        newTop = startTop;
                                    } else if (handleType === 'ne') {
                                        newW = Math.max(minW, Math.min(cachedMaxW, startW + dx));
                                        if (startLeft + newW > maxRight) newW = maxRight - startLeft;
                                        newLeft = startLeft;
                                        newH = Math.max(minH, startH - dy);
                                        newTop = startBottom - newH;
                                        if (newTop < minTop) {
                                            newTop = minTop;
                                            newH = startBottom - newTop;
                                        }
                                    } else if (handleType === 'nw') {
                                        newW = Math.max(minW, Math.min(cachedMaxW, startW - dx));
                                        newLeft = startRight - newW;
                                        if (newLeft < minLeft) {
                                            newLeft = minLeft;
                                            newW = startRight - newLeft;
                                        }
                                        newH = Math.max(minH, startH - dy);
                                        newTop = startBottom - newH;
                                        if (newTop < minTop) {
                                            newTop = minTop;
                                            newH = startBottom - newTop;
                                        }
                                    }
                                } else {
                                    const eff_dx = (handleType === 'se' || handleType === 'ne') ? dx : -dx;
                                    const eff_dy = (handleType === 'se' || handleType === 'sw') ? dy : -dy;
                                    const deltaW = Math.round((eff_dx * curAspect + eff_dy) * curAspect / (curAspect * curAspect + 1));
                                    const targetW = startW + deltaW;

                                    if (handleType === 'nw') {
                                        const limitW_x = Math.max(minW, startRight - minLeft);
                                        const limitH_y = Math.max(minW / curAspect + chromeH, startBottom - minTop);
                                        const limitW_y = Math.max(minW, Math.round((limitH_y - chromeH) * curAspect));
                                        const maxAllowedW = Math.min(cachedMaxW, limitW_x, limitW_y);

                                        newW = Math.max(minW, Math.min(maxAllowedW, targetW));
                                        newH = Math.round(newW / curAspect) + chromeH;
                                        newLeft = startRight - newW;
                                        newTop = startBottom - newH;

                                        if (newLeft < minLeft) {
                                            newLeft = minLeft;
                                            newW = startRight - newLeft;
                                            newH = Math.round(newW / curAspect) + chromeH;
                                            newTop = startBottom - newH;
                                        }
                                        if (newTop < minTop) {
                                            newTop = minTop;
                                            newH = startBottom - newTop;
                                            newW = Math.round((newH - chromeH) * curAspect);
                                            newLeft = startRight - newW;
                                        }
                                    } else if (handleType === 'ne') {
                                        const limitW_x = Math.max(minW, maxRight - startLeft);
                                        const limitH_y = Math.max(minW / curAspect + chromeH, startBottom - minTop);
                                        const limitW_y = Math.max(minW, Math.round((limitH_y - chromeH) * curAspect));
                                        const maxAllowedW = Math.min(cachedMaxW, limitW_x, limitW_y);

                                        newW = Math.max(minW, Math.min(maxAllowedW, targetW));
                                        newH = Math.round(newW / curAspect) + chromeH;
                                        newLeft = startLeft;
                                        newTop = startBottom - newH;

                                        if (newLeft + newW > maxRight) {
                                            newW = maxRight - newLeft;
                                            newH = Math.round(newW / curAspect) + chromeH;
                                            newTop = startBottom - newH;
                                        }
                                        if (newTop < minTop) {
                                            newTop = minTop;
                                            newH = startBottom - newTop;
                                            newW = Math.round((newH - chromeH) * curAspect);
                                        }
                                    } else if (handleType === 'sw') {
                                        const limitW_x = Math.max(minW, startRight - minLeft);
                                        const limitH_y = Math.max(minW / curAspect + chromeH, maxBottom - startTop);
                                        const limitW_y = Math.max(minW, Math.round((limitH_y - chromeH) * curAspect));
                                        const maxAllowedW = Math.min(cachedMaxW, limitW_x, limitW_y);

                                        newW = Math.max(minW, Math.min(maxAllowedW, targetW));
                                        newH = Math.round(newW / curAspect) + chromeH;
                                        newLeft = startRight - newW;
                                        newTop = startTop;

                                        if (newLeft < minLeft) {
                                            newLeft = minLeft;
                                            newW = startRight - newLeft;
                                            newH = Math.round(newW / curAspect) + chromeH;
                                        }
                                        if (newTop + newH > maxBottom) {
                                            newH = maxBottom - newTop;
                                            newW = Math.round((newH - chromeH) * curAspect);
                                            newLeft = startRight - newW;
                                        }
                                    } else if (handleType === 'se') {
                                        const limitW_x = Math.max(minW, maxRight - startLeft);
                                        const limitH_y = Math.max(minW / curAspect + chromeH, maxBottom - startTop);
                                        const limitW_y = Math.max(minW, Math.round((limitH_y - chromeH) * curAspect));
                                        const maxAllowedW = Math.min(cachedMaxW, limitW_x, limitW_y);

                                        newW = Math.max(minW, Math.min(maxAllowedW, targetW));
                                        newH = Math.round(newW / curAspect) + chromeH;
                                        newLeft = startLeft;
                                        newTop = startTop;

                                        if (newLeft + newW > maxRight) {
                                            newW = maxRight - newLeft;
                                            newH = Math.round(newW / curAspect) + chromeH;
                                        }
                                        if (newTop + newH > maxBottom) {
                                            newH = maxBottom - newTop;
                                            newW = Math.round((newH - chromeH) * curAspect);
                                        }
                                    }
                                }

                                pendingW = newW;
                                pendingH = newH;
                                pendingLeft = newLeft;
                                pendingTop = newTop;

                                if (!resizeRafId) {
                                    resizeRafId = requestAnimationFrame(() => {
                                        resizeRafId = null;
                                        if (!isResizing) return;
                                        currentW = pendingW;
                                        currentH = pendingH;
                                        currentLeft = pendingLeft;
                                        currentTop = pendingTop;

                                        pObj.wrapper.style.setProperty('width', currentW + 'px', 'important');
                                        pObj.wrapper.style.setProperty('height', currentH + 'px', 'important');
                                        pObj.wrapper.style.setProperty('left', currentLeft + 'px', 'important');
                                        pObj.wrapper.style.setProperty('top', currentTop + 'px', 'important');

                                        if (typeof pObj.applyTransform === 'function') {
                                            try { pObj.applyTransform(); } catch (err) {}
                                        }
                                    });
                                }
                            };

                            handle.addEventListener('pointermove', onResizeMove);

                            const stopResize = (e) => {
                                if (!isResizing) return;
                                if (resizeRafId) {
                                    cancelAnimationFrame(resizeRafId);
                                    resizeRafId = null;
                                }
                                isResizing = false;
                                pObj.isResizing = false;
                                delete pObj.resizeAnchor;
                                if (pObj.transformState) delete pObj.transformState.resizeAnchor;
                                window.__pyxisDraggingFloating = false;
                                document.body.classList.remove('pyxis-resizing-active');
                                pObj.wrapper.classList.remove('is-resizing');
                                pObj.activeResizeHandle = null;
                                try { handle.releasePointerCapture(e.pointerId); } catch (err) {}

                                currentW = pendingW;
                                currentH = pendingH;
                                currentLeft = pendingLeft;
                                currentTop = pendingTop;

                                pObj.wrapper.style.setProperty('width', currentW + 'px', 'important');
                                pObj.wrapper.style.setProperty('height', currentH + 'px', 'important');
                                pObj.wrapper.style.setProperty('left', currentLeft + 'px', 'important');
                                pObj.wrapper.style.setProperty('top', currentTop + 'px', 'important');

                                pObj.savedFloatingWidth = currentW + 'px';
                                pObj.savedFloatingHeight = currentH + 'px';
                                pObj.savedFloatingLeft = currentLeft + 'px';
                                pObj.savedFloatingTop = currentTop + 'px';

                                if (pObj.art && typeof pObj.art.resize === 'function') {
                                    try { pObj.art.resize(); } catch (err) {}
                                }
                                if (typeof pObj.applyTransform === 'function') {
                                    try { pObj.applyTransform(); } catch (err) {}
                                }
                                if (pObj.jassub && typeof pObj.jassub.resize === 'function') {
                                    try { pObj.jassub.resize(0, 0, 0, 0, true); } catch (err) {}
                                }

                                pObj.wrapper.style.transition = 'transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), top 0.35s cubic-bezier(0.16, 1, 0.3, 1), left 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s ease';
                                e.stopPropagation();
                            };

                            handle.addEventListener('pointerup', stopResize);
                            handle.addEventListener('pointercancel', stopResize);
                        });
                    }

                    attachPyxisFloatingResizers(p);

                    if (p.art && typeof p.art.resize === 'function') try { p.art.resize(); } catch (e) {}
                    if (typeof p.applyTransform === 'function') try { p.applyTransform(); } catch (e) {}
                    if (p.jassub && typeof p.jassub.resize === 'function') try { p.jassub.resize(0, 0, 0, 0, true); } catch (e) {}

                    requestAnimationFrame(() => {
                        if (p.art && typeof p.art.resize === 'function') try { p.art.resize(); } catch (e) {}
                        if (typeof p.applyTransform === 'function') try { p.applyTransform(); } catch (e) {}
                        if (p.jassub && typeof p.jassub.resize === 'function') try { p.jassub.resize(0, 0, 0, 0, true); } catch (e) {}
                    });

                    if (!p.resizeObserver && window.ResizeObserver) {
                        p.resizeObserver = new ResizeObserver(() => {
                            if (p.isPinned) {
                                const isCurrentlyResizing = Boolean(p.isResizing || window.__pyxisDraggingFloating);
                                if (typeof p.applyTransform === 'function') try { p.applyTransform(); } catch (e) {}
                                if (!isCurrentlyResizing) {
                                    if (p.art && typeof p.art.resize === 'function') try { p.art.resize(); } catch (e) {}
                                    if (p.jassub && typeof p.jassub.resize === 'function') try { p.jassub.resize(); } catch (e) {}
                                }
                            }
                        });
                        p.resizeObserver.observe(p.wrapper);
                    }

                } else {
                    if (p.wrapper) {
                        p.savedFloatingWidth = p.wrapper.style.width;
                        p.savedFloatingHeight = p.wrapper.style.height;
                        p.savedFloatingLeft = p.wrapper.style.left;
                        p.savedFloatingTop = p.wrapper.style.top;
                    }
                    p.wrapper.classList.remove('pyxis-floating-player-wrapper');
                    p.wrapper.removeAttribute('style');
                    p.wrapper.querySelectorAll('.pyxis-floating-resizer').forEach(resizer => resizer.remove());

                    let floatHeader = p.wrapper.querySelector('.pyxis-floating-header');
                    if (floatHeader) {
                        floatHeader.remove();
                    }

                    const layer = document.getElementById('pyxis-canvas-players-layer');
                    if (layer) layer.appendChild(p.wrapper);

                    if (btnPin) {
                        btnPin.classList.remove('active');
                        btnPin.setAttribute('aria-label', window.t ? window.t('preview.pin') : 'Pin player to screen');
                        btnPin.setAttribute('data-i18n-aria-label', 'preview.pin');
                    }
                    if (p.headerActions) {
                        p.headerActions.classList.remove('is-pinned');
                    }

                    if (p.node) {
                        if (p.originalComputeSize) {
                            p.node.computeSize = p.originalComputeSize;
                        } else {
                            delete p.node.computeSize;
                        }
                        if (p.originalOnResize) {
                            p.node.onResize = p.originalOnResize;
                        } else {
                            delete p.node.onResize;
                        }
                        const curAspect = getNodePreviewAspectRatio(p.node);
                        const restoredW = (p.originalSize && p.originalSize[0]) 
                            ? p.originalSize[0] 
                            : ((p.node.properties && p.node.properties.previewer_width) ? Number(p.node.properties.previewer_width) : 520);
                        const restoredH = (p.originalSize && p.originalSize[1])
                            ? p.originalSize[1]
                            : ((p.node.properties && p.node.properties.previewer_height)
                                ? Number(p.node.properties.previewer_height)
                                : (typeof calculatePrevisualizadorNodeHeight === "function" 
                                    ? calculatePrevisualizadorNodeHeight(restoredW, curAspect) 
                                    : 330));

                        p.node.size[0] = restoredW;
                        p.node.size[1] = restoredH;
                        if (p.node.properties) {
                            p.node.properties.is_pinned = false;
                            delete p.node.properties.pinned_width;
                            p.node.properties.previewer_width = restoredW;
                            p.node.properties.previewer_height = restoredH;
                        }
                        if (typeof p.node.setDirtyCanvas === 'function') {
                            p.node.setDirtyCanvas(true, true);
                        }
                        if (window.canvas) {
                            window.canvas.setDirty(true, true);
                            window.canvas.draw(true, true);
                        }
                    }

                    updateInNodePlayersPosition();
                }

                setTimeout(() => {
                    if (p.art && typeof p.art.resize === 'function') {
                        try { p.art.resize(); } catch (e) {}
                    }
                    if (typeof p.applyTransform === 'function') {
                        try { p.applyTransform(); } catch (e) {}
                    }
                    if (p.jassub && typeof p.jassub.resize === 'function') {
                        try { p.jassub.resize(0, 0, 0, 0, true); } catch (e) {}
                    }
                }, 100);
            }

            function loopSync() {
                updateInNodePlayersPosition();
                requestAnimationFrame(loopSync);
            }
            requestAnimationFrame(loopSync);

            function refreshAllPreviews(forceVideoReload = false) {
                const nodes = (window.graph && window.graph._nodes) || [];
                nodes.forEach(node => {
                    if (!node || node.id === undefined) return;
                    const nType = (node.type || '').toLowerCase();
                    const nTitle = (node.title || '').toLowerCase();
                    if (nType.includes('preview') || nType.includes('previsualizador') || nTitle.includes('previsualizador') || nTitle.includes('preview')) {
                        refreshPreview(String(node.id), forceVideoReload);
                    }
                });
            }

            function setPlayerLoading(nodeId, isLoading, messageKey = "preview.loading") {
                const targetId = String(nodeId);
                const p = activePlayers[targetId];
                const backdrop = (p && p.loadingBackdrop) || document.querySelector('#pyxis-player-loading-' + targetId);
                const topBar = (p && p.topProgressBar) || document.querySelector('#pyxis-top-progress-bar-' + targetId);
                if (!backdrop) return;
                if (isLoading) {
                    const textEl = backdrop.querySelector('.pyxis-player-loading-text');
                    if (textEl) {
                        const key = messageKey || textEl.getAttribute('data-i18n') || "preview.loading";
                        const isKey = typeof key === "string" && (key.startsWith("preview.") || key.startsWith("common."));
                        textEl.removeAttribute('data-i18n');
                        if (isKey) {
                            const isEn = (window.PyxisI18n && window.PyxisI18n.currentLang === "en") || (window.currentLanguage === "en");
                            const fallbackMap = {
                                "preview.converting_audio": (isEn ? "Converting incompatible audio..." : "Convirtiendo audio incompatible..."),
                                "preview.loading": (isEn ? "Loading preview..." : "Cargando previsualización..."),
                                "preview.switching_source": (isEn ? "Switching source..." : "Cambiando fuente..."),
                                "preview.generating": (isEn ? "Generating preview..." : "Generando vista previa..."),
                                "preview.updating": (isEn ? "Updating..." : "Actualizando..."),
                                "preview.syncing": (isEn ? "Syncing..." : "Sincronizando...")
                            };
                            let translated = window.t ? window.t(key) : null;
                            if (!translated || translated === key) {
                                translated = fallbackMap[key] || key;
                            }
                            textEl.textContent = translated;
                        } else {
                            textEl.textContent = key;
                        }
                    }

                    // Reset progress indicators to indeterminate 0% state
                    const track = backdrop.querySelector('.pyxis-player-loading-progress-track');
                    const bar = backdrop.querySelector('.pyxis-player-loading-progress-bar');
                    const pctEl = backdrop.querySelector('.pyxis-player-loading-progress-pct');
                    const infoEl = backdrop.querySelector('.pyxis-player-loading-progress-info');
                    const topTrack = (p && p.topProgressTrack) || document.querySelector('#pyxis-top-progress-' + targetId);
                    if (track) track.classList.add('is-indeterminate');
                    if (bar) bar.style.width = '0%';
                    if (pctEl) pctEl.textContent = '0%';
                    if (infoEl) infoEl.textContent = '';
                    if (topTrack) {
                        topTrack.classList.add('is-active', 'is-indeterminate');
                    }
                    if (topBar) topBar.style.width = '0%';

                    backdrop.classList.add('is-loading');
                } else {
                    backdrop.classList.remove('is-loading');
                    const topTrack = (p && p.topProgressTrack) || document.querySelector('#pyxis-top-progress-' + targetId);
                    if (topBar) {
                        topBar.style.width = '100%';
                        setTimeout(() => {
                            if (!backdrop.classList.contains('is-loading')) {
                                if (topBar) topBar.style.width = '0%';
                                if (topTrack) topTrack.classList.remove('is-active', 'is-indeterminate');
                            }
                        }, 400);
                    }
                }
            }

            function showPlayerFFmpegMissingBanner(nodeIdStr) {
                const targetId = String(nodeIdStr);
                const p = activePlayers[targetId];
                if (!p || !p.wrapper) return;
                p.hasFFmpegMissing = true;
                const isPinned = Boolean(p && p.isPinned);
                const borderRadius = isPinned ? '10px' : '6px';

                let banner = p.wrapper.querySelector('.pyxis-player-ffmpeg-missing');
                if (!banner) {
                    banner = document.createElement('div');
                    banner.className = 'pyxis-player-ffmpeg-missing';

                    const msgText = window.t ? window.t("ffmpeg.player_banner_desc") : "FFmpeg is required to generate background media and preview subtitles.";
                    const btnText = window.t ? window.t("ffmpeg.download_btn") : "Download FFmpeg";

                    banner.innerHTML = `
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:32px; height:32px; margin-top:4px; fill:none; stroke:var(--accent-primary, #22858c); stroke-width:2.2; stroke-linecap:round; stroke-linejoin:round; flex-shrink:0; filter:drop-shadow(0 0 12px var(--accent-glow, rgba(34,133,140,0.45)));">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        <div style="font-size:13px; font-weight:500; color:var(--text-main, #ffffff); max-width:320px; line-height:1.4; text-shadow:0 2px 8px rgba(0,0,0,0.6);">
                            ${msgText}
                        </div>
                        <button class="pyxis-btn pyxis-btn-primary pyxis-btn-install-ffmpeg" style="padding:6px 16px; border-radius:6px; cursor:pointer; font-weight:700; font-size:12px; margin-bottom:4px; box-shadow:0 0 14px var(--accent-glow, rgba(34,133,140,0.4));">
                            ${btnText}
                        </button>
                    `;
                    const btn = banner.querySelector('.pyxis-btn-install-ffmpeg');
                    if (btn) {
                        btn.onclick = (e) => {
                            e.stopPropagation();
                            if (typeof window.showFFmpegDownloadModal === 'function') {
                                window.showFFmpegDownloadModal(async (downloaded) => {
                                    if (!downloaded) return;
                                    await loadPreviewMediaAfterFFmpeg(targetId);
                                });
                            }
                        };
                    }
                    p.wrapper.appendChild(banner);
                }
                banner.style.cssText = `position:absolute; inset:0; border-radius:${borderRadius}; z-index:250 !important; display:flex; flex-direction:column; align-items:center; justify-content:center; background:rgba(9, 13, 22, 0.82); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); gap:10px; padding:18px 20px; text-align:center; pointer-events:auto; box-sizing:border-box;`;
                banner.style.display = 'flex';
                if (typeof updateInNodePlayersPosition === 'function') {
                    updateInNodePlayersPosition();
                }
            }

            async function loadPreviewMediaAfterFFmpeg(nodeIdStr) {
                const targetId = String(nodeIdStr);
                hidePlayerFFmpegMissingBanner(targetId);
                const p = activePlayers[targetId];
                if (!p || !p.art) return;
                try {
                    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_preview_video_data_url === 'function') {
                        const curSource = (p.node && p.node.properties && p.node.properties.preview_source) || "base";
                        const connectedOutputIds = (p.node) ? resolveConnectedOutputsForPreview(p.node) : [];
                        const serialized = (window.graph) ? window.graph.serialize() : null;
                        const newVideoUrl = await window.pywebview.api.get_preview_video_data_url(curSource, connectedOutputIds, serialized);
                        if (newVideoUrl && p.videoUrl !== newVideoUrl) {
                            p.videoUrl = newVideoUrl;
                            await safeArtSwitchUrl(p.art, newVideoUrl);
                            try { p.art.pause(); } catch(e) {}
                        }
                    }
                    if (typeof p.updateTimeUI === 'function') {
                        try { p.updateTimeUI(); } catch (e) {}
                    }
                } catch (err) {
                    console.warn("[Pyxis loadPreviewMediaAfterFFmpeg warning]", err);
                }
            }

            function hidePlayerFFmpegMissingBanner(nodeIdStr) {
                const targetId = String(nodeIdStr);
                const p = activePlayers[targetId];
                if (!p || !p.wrapper) return;
                p.hasFFmpegMissing = false;
                const banner = p.wrapper.querySelector('.pyxis-player-ffmpeg-missing');
                if (banner) {
                    banner.style.display = 'none';
                }
                if (typeof updateInNodePlayersPosition === 'function') {
                    updateInNodePlayersPosition();
                }
            }

            let isDaemonSuspended = false;

            function suspendForDaemon() {
                isDaemonSuspended = true;
                try {
                    if (window.PyxisTelemetry && typeof window.PyxisTelemetry.clearData === 'function') {
                        window.PyxisTelemetry.clearData(false);
                    }
                    Object.keys(activePlayers).forEach(nodeId => {
                        const p = activePlayers[nodeId];
                        if (p) {
                            p.hasRefreshed = false;
                        }
                        if (p && p.art) {
                            try { p.art.pause(); } catch(e) {}
                            if (p.art.template && p.art.template.$video) {
                                try {
                                    p.art.template.$video.pause();
                                    p.art.template.$video.muted = true;
                                } catch(e) {}
                            }
                        }
                    });
                    disarmMediaSession();
                } catch (err) {
                    console.warn("[Pyxis Player suspendForDaemon warning]", err);
                }
            }

            function resumeFromDaemon() {
                isDaemonSuspended = false;
                try {
                    Object.keys(activePlayers).forEach(nodeId => {
                        const p = activePlayers[nodeId];
                        if (p && p.art && p.art.template && p.art.template.$video) {
                            try {
                                p.art.template.$video.muted = (p.art.volume === 0);
                            } catch(e) {}
                        }
                    });
                    disarmMediaSession();
                } catch (err) {
                    console.warn("[Pyxis Player resumeFromDaemon warning]", err);
                }
            }

            document.addEventListener("visibilitychange", function() {
                if (document.hidden) {
                    suspendForDaemon();
                } else {
                    resumeFromDaemon();
                }
            });

            function onGlobalPointerRelease() {
                Object.keys(activePlayers).forEach(nodeId => {
                    const p = activePlayers[nodeId];
                    if (p && (p.isResizing || (p.transformState && p.transformState.resizeAnchor))) {
                        p.isResizing = false;
                        delete p.resizeAnchor;
                        if (p.transformState) delete p.transformState.resizeAnchor;
                        if (p.art && typeof p.art.resize === 'function') {
                            try { p.art.resize(); } catch(e) {}
                        }
                        if (typeof p.applyTransform === 'function') {
                            try { p.applyTransform(); } catch(e) {}
                        }
                        if (p.jassub && typeof p.jassub.resize === 'function') {
                            try { p.jassub.resize(0, 0, 0, 0, true); } catch(e) {}
                        }
                    }
                });
                window.__pyxisDraggingFloating = false;
            }
            window.addEventListener('pointerup', onGlobalPointerRelease, { passive: true });
            window.addEventListener('mouseup', onGlobalPointerRelease, { passive: true });

            function clampFloatingPlayersToViewport() {
                const topBar = document.querySelector('.top-bar');
                const topBarH = (topBar && topBar.offsetHeight) ? topBar.offsetHeight : 52;
                Object.keys(activePlayers).forEach(nodeId => {
                    const p = activePlayers[nodeId];
                    if (!p || !p.isPinned || !p.wrapper) return;
                    if (p.isResizing || window.__pyxisDraggingFloating) return;

                    const curW = parseFloat(p.wrapper.style.width) || p.wrapper.offsetWidth || 560;
                    const curH = parseFloat(p.wrapper.style.height) || p.wrapper.offsetHeight || 380;
                    const curLeft = parseFloat(p.wrapper.style.left) || 20;
                    const curTop = parseFloat(p.wrapper.style.top) || (topBarH + 16);

                    const minLeft = 10;
                    const maxLeft = Math.max(minLeft, window.innerWidth - curW - 10);
                    const minTop = topBarH + 8;
                    const maxTop = Math.max(minTop, window.innerHeight - curH - 10);

                    const clampedLeft = Math.max(minLeft, Math.min(curLeft, maxLeft));
                    const clampedTop = Math.max(minTop, Math.min(curTop, maxTop));

                    if (Math.abs(clampedLeft - curLeft) > 1 || Math.abs(clampedTop - curTop) > 1) {
                        p.wrapper.style.left = clampedLeft + 'px';
                        p.wrapper.style.top = clampedTop + 'px';
                        p.savedFloatingLeft = p.wrapper.style.left;
                        p.savedFloatingTop = p.wrapper.style.top;
                    }
                });
            }
            window.addEventListener('resize', clampFloatingPlayersToViewport, { passive: true });

            window.PyxisNodePlayerManager = {
                updateInNodePlayersPosition: updateInNodePlayersPosition,
                refreshPreview: refreshPreview,
                refreshAllPreviews: refreshAllPreviews,
                cancelPreview: cancelPreview,
                updatePlayerProgress: updatePlayerProgress,
                destroyInNodePlayer: destroyInNodePlayer,
                destroyAllPlayers: destroyAllPlayers,
                renderHardsub: renderHardsub,
                togglePinPreview: togglePinPreview,
                togglePreviewSource: togglePreviewSource,
                togglePreviewRenderMode: togglePreviewRenderMode,
                revertToPreviewBase: revertToPreviewBase,
                updateSourceButtonUI: updateSourceButtonUI,
                updateRenderModeButtonUI: updateRenderModeButtonUI,
                setPlayerLoading: setPlayerLoading,
                setAllPlayersLoading: setAllPlayersLoading,
                suspendForDaemon: suspendForDaemon,
                resumeFromDaemon: resumeFromDaemon,
                getPreviewBounds: getPreviewBounds,
                resolveConnectedOutputsForPreview: resolveConnectedOutputsForPreview,
                get isDaemonSuspended() { return isDaemonSuspended; },
                activePlayers: activePlayers
            };
        })();

        // =========================================================================
        // PYXIS TELEMETRY ENGINE & ORBITAL COCKPIT UI
        // =========================================================================
        (function() {
            let lastTelemetryData = null;
            let isScanning = false;
            let isOpen = false;
            let reparentedPlayer = null;
            let rafId = null;
            let lastSyncedFrameIdx = -1;

            const activeMetrics = {
                render_ms: true,
                total_kb: true,
                largest_kb: false,
                objects: false
            };

            const metricScales = {
                render_ms: 'auto',
                total_kb: 'auto',
                largest_kb: 'auto',
                objects: 'auto'
            };

            try {
                const cachedScales = JSON.parse(localStorage.getItem('pyxis_telemetry_scales') || 'null');
                if (cachedScales && typeof cachedScales === 'object') {
                    for (const k of Object.keys(metricScales)) {
                        if (cachedScales[k]) metricScales[k] = String(cachedScales[k]);
                    }
                }
                const cachedActive = JSON.parse(localStorage.getItem('pyxis_telemetry_active_metrics') || 'null');
                if (cachedActive && typeof cachedActive === 'object') {
                    for (const k of Object.keys(activeMetrics)) {
                        if (cachedActive[k] !== undefined) activeMetrics[k] = !!cachedActive[k];
                    }
                }
            } catch (e) {}

            function syncFilterControlsDOM() {
                for (const mKey of Object.keys(metricScales)) {
                    const selEl = document.getElementById('pyxis-tel-scale-' + mKey);
                    if (selEl) {
                        selEl.value = metricScales[mKey] || 'auto';
                    }
                    const pillBtn = document.querySelector(`.pyxis-tel-filter-pill[data-metric="${mKey}"]`);
                    if (pillBtn) {
                        pillBtn.classList.toggle('is-active', !!activeMetrics[mKey]);
                    }
                }
            }

            function persistTelemetryConfig() {
                try {
                    localStorage.setItem('pyxis_telemetry_scales', JSON.stringify(metricScales));
                    localStorage.setItem('pyxis_telemetry_active_metrics', JSON.stringify(activeMetrics));
                } catch (e) {}
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.save_user_config === 'function') {
                    try {
                        window.pywebview.api.save_user_config({
                            telemetry_scales: { ...metricScales },
                            telemetry_active_metrics: { ...activeMetrics }
                        });
                    } catch (e) {}
                }
            }

            function applyPersistedConfig(cfg) {
                if (!cfg || typeof cfg !== 'object') return;
                if (cfg.telemetry_scales && typeof cfg.telemetry_scales === 'object') {
                    for (const k of Object.keys(metricScales)) {
                        if (cfg.telemetry_scales[k] !== undefined && cfg.telemetry_scales[k] !== null) {
                            metricScales[k] = String(cfg.telemetry_scales[k]);
                        }
                    }
                }
                if (cfg.telemetry_active_metrics && typeof cfg.telemetry_active_metrics === 'object') {
                    for (const k of Object.keys(activeMetrics)) {
                        if (cfg.telemetry_active_metrics[k] !== undefined) {
                            activeMetrics[k] = !!cfg.telemetry_active_metrics[k];
                        }
                    }
                }
                try {
                    localStorage.setItem('pyxis_telemetry_scales', JSON.stringify(metricScales));
                    localStorage.setItem('pyxis_telemetry_active_metrics', JSON.stringify(activeMetrics));
                } catch (e) {}
                syncFilterControlsDOM();
                if (isOpen) {
                    renderMainChart();
                }
            }

            const viewport = {
                startIdx: 0,
                endIdx: 100,
                yScale: 1.0,
                yOffset: 0.0
            };

            const hoverState = {
                active: false,
                frameIdx: -1,
                canvasX: 0,
                canvasY: 0,
                clientX: 0,
                clientY: 0
            };

            function formatMsToTimecode(ms) {
                if (typeof ms !== 'number' || isNaN(ms) || ms < 0) ms = 0;
                const totalSec = Math.floor(ms / 1000);
                const m = Math.floor(totalSec / 60);
                const s = totalSec % 60;
                const remMs = Math.floor(ms % 1000);
                return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0') + '.' + String(remMs).padStart(3, '0');
            }

            function formatMemoryLabel(kb) {
                const val = Number(kb) || 0;
                if (val >= 1024) {
                    return (val / 1024).toFixed(2) + ' MB';
                }
                return Math.round(val) + ' KB';
            }

            let lastStatusState = 'idle';

            function hexToRgba(hex, alpha) {
                const a = (alpha !== undefined) ? alpha : 1.0;
                if (!hex || typeof hex !== 'string') return `rgba(84, 140, 135, ${a})`;
                let c = hex.trim();
                if (c.startsWith('rgba(') || c.startsWith('rgb(')) return c;
                if (c.startsWith('#')) c = c.slice(1);
                if (c.length === 3) {
                    c = c[0] + c[0] + c[1] + c[1] + c[2] + c[2];
                }
                if (c.length >= 6) {
                    const r = parseInt(c.slice(0, 2), 16);
                    const g = parseInt(c.slice(2, 4), 16);
                    const b = parseInt(c.slice(4, 6), 16);
                    if (!isNaN(r) && !isNaN(g) && !isNaN(b)) {
                        return `rgba(${r}, ${g}, ${b}, ${a})`;
                    }
                }
                return `rgba(84, 140, 135, ${a})`;
            }

            function getThemeTelemetryPalette() {
                const rootStyle = document.documentElement ? document.documentElement.style : null;
                const t = window.PYXIS_THEME || {};
                const getVar = (name, fallback) => {
                    if (rootStyle) {
                        const v = rootStyle.getPropertyValue(name);
                        if (v && v.trim()) return v.trim();
                    }
                    return fallback;
                };
                const accent = getVar('--accent-primary', t.accentPrimary || '#548C87');
                const accentEnd = getVar('--accent-primary-end', t.accentPrimaryEnd || '#67aba5');
                const accentBright = getVar('--doc-accent-bright', accentEnd || '#67aba5');
                const shimmerCore = getVar('--theme-shimmer-2', accentBright);
                const textMain = getVar('--text-main', t.textMain || '#f3f4f6');
                const textMuted = getVar('--text-muted', t.textMuted || '#9ca3af');
                const bgCanvas = getVar('--bg-canvas', t.canvasBg || '#0f1318');
                const themeId = (document.documentElement && document.documentElement.getAttribute('data-theme')) || 'teal';
                return {
                    themeId,
                    accent,
                    accentEnd,
                    accentBright,
                    shimmerCore,
                    textMain,
                    textMuted,
                    bgCanvas
                };
            }

            function getThermalColor(ratio, alpha) {
                const a = (alpha !== undefined) ? alpha : 1.0;
                if (ratio >= 1.0) {
                    return `rgba(244, 63, 94, ${a})`; // Rose / Crimson
                } else if (ratio >= 0.70) {
                    return `rgba(251, 191, 36, ${a})`; // Amber
                }
                const pal = getThemeTelemetryPalette();
                return hexToRgba(pal.accentBright, a);
            }

            function setStatusUI(state, customLabel) {
                if (state) lastStatusState = state;
                const pal = getThemeTelemetryPalette();
                const badge = document.getElementById('pyxis-tel-status-badge');
                const btnRescan = document.getElementById('btn-telemetry-rescan');
                const btnTop = document.getElementById('btn-telemetry-open');
                if (btnRescan) {
                    btnRescan.classList.toggle('is-scanning', state === 'scanning');
                }
                if (btnTop) {
                    btnTop.classList.toggle('is-scanning', state === 'scanning');
                }
                if (badge) {
                    if (customLabel) {
                        badge.textContent = customLabel;
                    } else if (state === 'scanning') {
                        badge.textContent = window.t ? window.t('telemetry.status_scanning') : 'SCANNING...';
                        badge.style.background = hexToRgba(pal.accent, 0.18);
                        badge.style.borderColor = hexToRgba(pal.accentBright, 0.45);
                        badge.style.color = pal.accentBright;
                    } else if (state === 'ready') {
                        const summary = (lastTelemetryData && lastTelemetryData.summary) ? lastTelemetryData.summary : {};
                        const dropped = Number(summary.dropped_frames) || 0;
                        const bPct = Number(summary.peak_budget_pct) || 0;
                        if (dropped > 0 || bPct >= 100) {
                            badge.textContent = window.t ? window.t('telemetry.status_bottleneck') : 'BOTTLENECK';
                            badge.style.background = 'rgba(244, 63, 94, 0.16)';
                            badge.style.borderColor = 'rgba(244, 63, 94, 0.45)';
                            badge.style.color = '#f43f5e';
                        } else if (bPct >= 70) {
                            badge.textContent = window.t ? window.t('telemetry.status_heavy') : 'HEAVY';
                            badge.style.background = 'rgba(251, 191, 36, 0.16)';
                            badge.style.borderColor = 'rgba(251, 191, 36, 0.45)';
                            badge.style.color = '#fbbf24';
                        } else {
                            badge.textContent = window.t ? window.t('telemetry.status_optimal') : 'OPTIMAL';
                            badge.style.background = 'rgba(16, 185, 129, 0.16)';
                            badge.style.borderColor = 'rgba(16, 185, 129, 0.45)';
                            badge.style.color = '#34d399';
                        }
                    } else if (state === 'idle') {
                        badge.textContent = window.t ? window.t('telemetry.status_idle') : 'WAITING FOR SCAN';
                        badge.style.background = hexToRgba(pal.textMuted, 0.12);
                        badge.style.borderColor = hexToRgba(pal.textMuted, 0.30);
                        badge.style.color = pal.textMuted;
                    } else if (state === 'error') {
                        badge.textContent = window.t ? window.t('telemetry.status_error') : 'ERROR';
                        badge.style.background = 'rgba(244, 63, 94, 0.16)';
                        badge.style.borderColor = 'rgba(244, 63, 94, 0.45)';
                        badge.style.color = '#f43f5e';
                    }
                }
            }

            function updateZoomBadge() {
                const zoomBadge = document.getElementById('pyxis-tel-zoom-badge');
                if (!zoomBadge) return;
                const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : [];
                const totalSpan = Math.max(1, frames.length - 1);
                const curSpan = Math.max(1, viewport.endIdx - viewport.startIdx);
                const xZoom = Math.max(1.0, totalSpan / curSpan);
                zoomBadge.textContent = `${xZoom.toFixed(1)}x X | ${viewport.yScale.toFixed(1)}x Y`;
            }

            function resetViewportToFull() {
                const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : [];
                viewport.startIdx = 0;
                viewport.endIdx = Math.max(1, frames.length - 1);
                viewport.yScale = 1.0;
                viewport.yOffset = 0.0;
                updateZoomBadge();
            }

            function getPreviewerPointColor(val, norm, budgetMs, alpha, pal) {
                const a = (alpha !== undefined) ? alpha : 1.0;
                const p = pal || getThemeTelemetryPalette();
                const budgetRatio = val / Math.max(1.0, budgetMs);
                if (budgetRatio >= 0.85) {
                    return `rgba(244, 63, 94, ${a})`; // Crimson
                }
                if (budgetRatio >= 0.45) {
                    return `rgba(245, 158, 11, ${a})`; // Amber
                }
                if (norm >= 0.78) {
                    return hexToRgba(p.shimmerCore, a);
                }
                if (norm >= 0.42) {
                    return hexToRgba(p.accentBright, a);
                }
                return hexToRgba(p.accent, Number((a * 0.92).toFixed(3)));
            }

            function renderPreviewerHeatmap(canvasEl) {
                if (!canvasEl) return;
                const dpr = window.devicePixelRatio || 1;
                const cssW = canvasEl.clientWidth || 640;
                const cssH = canvasEl.clientHeight || 24;
                const w = Math.max(64, Math.round(cssW * dpr));
                const h = Math.max(16, Math.round(cssH * dpr));

                if (canvasEl.width !== w || canvasEl.height !== h) {
                    canvasEl.width = w;
                    canvasEl.height = h;
                }

                const ctx = canvasEl.getContext('2d');
                if (!ctx) return;
                ctx.clearRect(0, 0, w, h);

                const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : null;
                if (!frames || frames.length < 2) return;

                const pal = getThemeTelemetryPalette();
                const summary = lastTelemetryData.summary || {};
                const budgetMs = Math.max(1.0, Number(summary.frame_budget_ms) || 41.708);
                const isExpanded = cssH >= 36;
                const topPad = isExpanded ? (15 * dpr) : (2.5 * dpr);
                const usableH = Math.max(6 * dpr, h - topPad - (1 * dpr));

                const cacheKey = `${w}x${h}:${isExpanded ? 1 : 0}:${dpr}:${frames.length}:${summary.peak_ms || 0}:${pal.themeId}:${pal.accent}:${pal.accentBright}`;
                if (
                    !canvasEl._baseCacheCanvas ||
                    canvasEl._baseCacheKey !== cacheKey ||
                    canvasEl._baseCacheDataRef !== lastTelemetryData
                ) {
                    const offCanvas = canvasEl._baseCacheCanvas || document.createElement('canvas');
                    if (offCanvas.width !== w || offCanvas.height !== h) {
                        offCanvas.width = w;
                        offCanvas.height = h;
                    }
                    const offCtx = offCanvas.getContext('2d');
                    if (offCtx) {
                        offCtx.clearRect(0, 0, w, h);

                        // High-resolution buckets (up to 1 bucket per CSS pixel or exact frame count) with no blur kernel
                        const numBuckets = Math.min(frames.length, Math.max(256, Math.floor(cssW)));
                        const rawVals = new Array(numBuckets).fill(0);
                        let actualPeakMs = 0;
                        for (let b = 0; b < numBuckets; b++) {
                            const i0 = Math.floor((b / numBuckets) * frames.length);
                            const i1 = Math.max(i0 + 1, Math.floor(((b + 1) / numBuckets) * frames.length));
                            let localMax = 0;
                            for (let i = i0; i < i1 && i < frames.length; i++) {
                                const v = Number(frames[i].render_ms) || 0;
                                if (v > localMax) localMax = v;
                            }
                            rawVals[b] = localMax;
                            if (localMax > actualPeakMs) actualPeakMs = localMax;
                        }

                        actualPeakMs = Math.max(0.15, actualPeakMs, Number(summary.peak_ms) || 0.15);

                        let minActiveMs = Infinity;
                        const activeThreshold = actualPeakMs * 0.05;
                        for (let b = 0; b < numBuckets; b++) {
                            if (rawVals[b] > activeThreshold && rawVals[b] < minActiveMs) {
                                minActiveMs = rawVals[b];
                            }
                        }
                        if (!isFinite(minActiveMs)) minActiveMs = 0;
                        const baseFloor = (minActiveMs > 0 && minActiveMs < actualPeakMs * 0.85) ? (minActiveMs * 0.65) : 0;

                        const pts = [];
                        const hGradFill = offCtx.createLinearGradient(0, 0, w, 0);
                        const hGradStroke = offCtx.createLinearGradient(0, 0, w, 0);
                        const fillAlpha = isExpanded ? 0.62 : 0.54;

                        for (let b = 0; b < numBuckets; b++) {
                            const t = b / Math.max(1, numBuckets - 1);
                            const val = rawVals[b];
                            let norm = 0;
                            if (val > 0.001) {
                                const rel = Math.max(0, (val - baseFloor) / Math.max(0.02, actualPeakMs - baseFloor));
                                norm = Math.min(1.0, 0.14 + 0.86 * Math.pow(rel, 0.82));
                            }
                            const x = t * w;
                            const y = h - Math.max(1.2 * dpr, norm * usableH);
                            pts.push({ x, y, val, norm });

                            hGradFill.addColorStop(t, getPreviewerPointColor(val, norm, budgetMs, fillAlpha, pal));
                            hGradStroke.addColorStop(t, getPreviewerPointColor(val, norm, budgetMs, 0.98, pal));
                        }

                        // Subtle reference grid when expanded on hover
                        if (isExpanded) {
                            offCtx.save();
                            offCtx.strokeStyle = hexToRgba(pal.textMuted, 0.16);
                            offCtx.lineWidth = 1 * dpr;
                            offCtx.setLineDash([3 * dpr, 3 * dpr]);
                            offCtx.beginPath();
                            offCtx.moveTo(0, topPad);
                            offCtx.lineTo(w, topPad);
                            const midY = topPad + usableH * 0.5;
                            offCtx.moveTo(0, midY);
                            offCtx.lineTo(w, midY);
                            offCtx.stroke();
                            offCtx.restore();
                        }

                        // Build high-resolution spline path with tight tension (/ 14)
                        offCtx.save();
                        offCtx.beginPath();
                        offCtx.moveTo(0, h);
                        offCtx.lineTo(pts[0].x, pts[0].y);
                        for (let i = 0; i < pts.length - 1; i++) {
                            const p0 = pts[Math.max(0, i - 1)];
                            const p1 = pts[i];
                            const p2 = pts[i + 1];
                            const p3 = pts[Math.min(pts.length - 1, i + 2)];
                            const cp1x = p1.x + (p2.x - p0.x) / 14;
                            const cp1y = Math.min(h, Math.max(topPad, p1.y + (p2.y - p0.y) / 14));
                            const cp2x = p2.x - (p3.x - p1.x) / 14;
                            const cp2y = Math.min(h, Math.max(topPad, p2.y - (p3.y - p1.y) / 14));
                            offCtx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
                        }
                        offCtx.lineTo(w, h);
                        offCtx.closePath();

                        offCtx.fillStyle = hGradFill;
                        offCtx.fill();

                        // Soft vertical fade mask near the bottom track
                        offCtx.globalCompositeOperation = 'destination-in';
                        const vFade = offCtx.createLinearGradient(0, topPad, 0, h);
                        vFade.addColorStop(0.0, 'rgba(255, 255, 255, 1.0)');
                        vFade.addColorStop(0.80, 'rgba(255, 255, 255, 0.72)');
                        vFade.addColorStop(1.0, 'rgba(255, 255, 255, 0.18)');
                        offCtx.fillStyle = vFade;
                        offCtx.fillRect(0, 0, w, h);
                        offCtx.restore();

                        // Top crisp spline stroke
                        offCtx.save();
                        offCtx.beginPath();
                        offCtx.moveTo(pts[0].x, pts[0].y);
                        for (let i = 0; i < pts.length - 1; i++) {
                            const p0 = pts[Math.max(0, i - 1)];
                            const p1 = pts[i];
                            const p2 = pts[i + 1];
                            const p3 = pts[Math.min(pts.length - 1, i + 2)];
                            const cp1x = p1.x + (p2.x - p0.x) / 14;
                            const cp1y = Math.min(h, Math.max(topPad, p1.y + (p2.y - p0.y) / 14));
                            const cp2x = p2.x - (p3.x - p1.x) / 14;
                            const cp2y = Math.min(h, Math.max(topPad, p2.y - (p3.y - p1.y) / 14));
                            offCtx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
                        }
                        offCtx.strokeStyle = hGradStroke;
                        offCtx.lineWidth = (isExpanded ? 1.85 : 1.5) * dpr;
                        offCtx.stroke();
                        offCtx.restore();

                        canvasEl._baseCacheCanvas = offCanvas;
                        canvasEl._baseCacheKey = cacheKey;
                        canvasEl._baseCacheDataRef = lastTelemetryData;
                        canvasEl._baseCachePts = pts;
                        canvasEl._baseCachePeakMs = actualPeakMs;
                    }
                }

                if (canvasEl._baseCacheCanvas) {
                    ctx.drawImage(canvasEl._baseCacheCanvas, 0, 0);
                }

                const pts = canvasEl._baseCachePts || [];
                const actualPeakMs = canvasEl._baseCachePeakMs || Math.max(0.15, Number(summary.peak_ms) || 0.15);

                // Hover cursor line, peak point marker, and header labels when expanded
                if (isExpanded && pts.length > 0) {
                    const hoverRatioRaw = canvasEl.dataset ? canvasEl.dataset.hoverRatio : undefined;
                    const isOverGraph = canvasEl.dataset && canvasEl.dataset.isOverGraph === '1';
                    if (hoverRatioRaw !== undefined && hoverRatioRaw !== '') {
                        const hr = Math.max(0, Math.min(1, Number(hoverRatioRaw) || 0));
                        const bIdx = Math.min(pts.length - 1, Math.max(0, Math.round(hr * (pts.length - 1))));
                        const hp = pts[bIdx];
                        if (hp) {
                            ctx.save();
                            ctx.strokeStyle = isOverGraph ? hexToRgba(pal.shimmerCore, 0.80) : hexToRgba(pal.textMain, 0.45);
                            ctx.lineWidth = 1 * dpr;
                            ctx.setLineDash([2.5 * dpr, 2.5 * dpr]);
                            ctx.beginPath();
                            ctx.moveTo(hp.x, topPad);
                            ctx.lineTo(hp.x, h);
                            ctx.stroke();
                            ctx.setLineDash([]);

                            ctx.fillStyle = isOverGraph ? pal.shimmerCore : pal.accentBright;
                            ctx.beginPath();
                            ctx.arc(hp.x, hp.y, 3.2 * dpr, 0, Math.PI * 2);
                            ctx.fill();
                            ctx.strokeStyle = pal.bgCanvas;
                            ctx.lineWidth = 1.2 * dpr;
                            ctx.stroke();
                            ctx.restore();
                        }
                    }

                    // Top micro-header bar inside expanded canvas
                    ctx.save();
                    ctx.font = `700 ${Math.round(9.5 * dpr)}px Consolas, monospace`;
                    ctx.textBaseline = 'middle';
                    const hdrY = 7.5 * dpr;
                    ctx.fillStyle = hexToRgba(pal.textMuted, 0.90);
                    ctx.textAlign = 'left';
                    ctx.fillText(`PEAK ${actualPeakMs.toFixed(2)} ms`, 6 * dpr, hdrY);

                    // Top-right Telemetry action label + vector arrow
                    const labelColor = isOverGraph ? pal.shimmerCore : pal.accentBright;
                    ctx.fillStyle = labelColor;
                    ctx.textAlign = 'right';
                    const arrowRight = w - 7 * dpr;
                    ctx.fillText('TELEMETRY', arrowRight - 10 * dpr, hdrY);

                    // Vector diagonal north-east arrow (no emojis)
                    const ax0 = arrowRight - 6 * dpr;
                    const ay0 = hdrY + 2.5 * dpr;
                    const ax1 = arrowRight;
                    const ay1 = hdrY - 3.5 * dpr;
                    ctx.strokeStyle = labelColor;
                    ctx.lineWidth = 1.4 * dpr;
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                    ctx.beginPath();
                    ctx.moveTo(ax0, ay0);
                    ctx.lineTo(ax1, ay1);
                    ctx.moveTo(ax1 - 4 * dpr, ay1);
                    ctx.lineTo(ax1, ay1);
                    ctx.lineTo(ax1, ay1 + 4 * dpr);
                    ctx.stroke();
                    ctx.restore();
                }
            }

            function renderAllPreviewerHeatmaps() {
                const canvases = document.querySelectorAll('.pyxis-pbar-heatmap');
                canvases.forEach(c => renderPreviewerHeatmap(c));
            }

            function getFrameAtRatio(pct) {
                if (!lastTelemetryData || !Array.isArray(lastTelemetryData.frames) || lastTelemetryData.frames.length === 0) {
                    return null;
                }
                const clamped = Math.max(0, Math.min(1, Number(pct) || 0));
                const idx = Math.min(
                    lastTelemetryData.frames.length - 1,
                    Math.max(0, Math.round(clamped * (lastTelemetryData.frames.length - 1)))
                );
                return lastTelemetryData.frames[idx] || null;
            }

            function getTargetPlayer(preferredNodeId) {
                const mgr = window.PyxisNodePlayerManager;
                if (!mgr || !mgr.activePlayers) return null;
                if (preferredNodeId !== undefined && preferredNodeId !== null && mgr.activePlayers[String(preferredNodeId)]) {
                    return { nodeIdStr: String(preferredNodeId), player: mgr.activePlayers[String(preferredNodeId)] };
                }
                if (reparentedPlayer && mgr.activePlayers[reparentedPlayer.nodeIdStr]) {
                    return { nodeIdStr: reparentedPlayer.nodeIdStr, player: mgr.activePlayers[reparentedPlayer.nodeIdStr] };
                }
                const keys = Object.keys(mgr.activePlayers);
                if (keys.length > 0) {
                    return { nodeIdStr: keys[0], player: mgr.activePlayers[keys[0]] };
                }
                return null;
            }

            let pendingTelSeekMs = null;
            let telSeekRafId = null;
            let chartRenderRafId = null;
            let chartRenderNeedMinimap = false;

            function flushTelemetrySeek() {
                telSeekRafId = null;
                if (pendingTelSeekMs === null) return;
                const timeMs = pendingTelSeekMs;
                pendingTelSeekMs = null;
                const target = getTargetPlayer();
                if (!target || !target.player || !target.player.art) return;
                const art = target.player.art;
                const mgr = window.PyxisNodePlayerManager;
                let winStartSec = 0;
                if (mgr && typeof mgr.getPreviewBounds === 'function') {
                    const bounds = mgr.getPreviewBounds(target.nodeIdStr);
                    winStartSec = bounds.winStart || 0;
                }
                const summary = (lastTelemetryData && lastTelemetryData.summary) ? lastTelemetryData.summary : {};
                const clipStartMs = (summary.clip_start_ms !== undefined) ? Number(summary.clip_start_ms) : (winStartSec * 1000);
                const relSec = Math.max(0, (Number(timeMs) - clipStartMs) / 1000.0);
                try {
                    art.currentTime = winStartSec + relSec;
                } catch (e) {}
            }

            function seekVideoToTimeMs(timeMs, immediate = true) {
                pendingTelSeekMs = timeMs;
                if (immediate) {
                    if (telSeekRafId !== null) {
                        cancelAnimationFrame(telSeekRafId);
                        telSeekRafId = null;
                    }
                    flushTelemetrySeek();
                } else if (telSeekRafId === null) {
                    telSeekRafId = requestAnimationFrame(flushTelemetrySeek);
                }
            }

            function scheduleChartRender(withMinimap = false) {
                if (withMinimap) chartRenderNeedMinimap = true;
                if (chartRenderRafId !== null) return;
                chartRenderRafId = requestAnimationFrame(() => {
                    chartRenderRafId = null;
                    const needMini = chartRenderNeedMinimap;
                    chartRenderNeedMinimap = false;
                    renderMainChart();
                    if (needMini) renderMinimap();
                });
            }

            function getCurrentPlayheadFrameIndex() {
                if (!lastTelemetryData || !Array.isArray(lastTelemetryData.frames) || lastTelemetryData.frames.length === 0) {
                    return 0;
                }
                const target = getTargetPlayer();
                if (!target || !target.player || !target.player.art) return 0;
                const art = target.player.art;
                const mgr = window.PyxisNodePlayerManager;
                let winStartSec = 0;
                let winDurSec = 15.0;
                if (mgr && typeof mgr.getPreviewBounds === 'function') {
                    const bounds = mgr.getPreviewBounds(target.nodeIdStr);
                    winStartSec = bounds.winStart || 0;
                    winDurSec = bounds.winDur || 15.0;
                }
                const relSec = Math.max(0, Math.min(winDurSec, (art.currentTime || 0) - winStartSec));
                const pct = (winDurSec > 0) ? (relSec / winDurSec) : 0;
                const frames = lastTelemetryData.frames;
                return Math.max(0, Math.min(frames.length - 1, Math.round(pct * (frames.length - 1))));
            }

            function updateCockpitKPIs() {
                const pal = getThemeTelemetryPalette();
                const summary = (lastTelemetryData && lastTelemetryData.summary) ? lastTelemetryData.summary : null;
                const hotspots = (lastTelemetryData && Array.isArray(lastTelemetryData.hotspots)) ? lastTelemetryData.hotspots : [];

                const metaPill = document.getElementById('pyxis-tel-meta-pill');
                const gaugeArc = document.getElementById('pyxis-tel-gauge-arc');
                const gaugePct = document.getElementById('pyxis-tel-gauge-pct');
                const gaugeMs = document.getElementById('pyxis-tel-gauge-ms');
                const gaugeLimit = document.getElementById('pyxis-tel-gauge-limit');
                const arcStopMid = document.getElementById('pyxis-tel-arc-stop-mid');
                if (arcStopMid) {
                    arcStopMid.setAttribute('stop-color', pal.accentBright);
                }

                const kpiPeak = document.getElementById('pyxis-tel-kpi-peak');
                const kpiPeakSub = document.getElementById('pyxis-tel-kpi-peak-sub');
                const kpiAvg = document.getElementById('pyxis-tel-kpi-avg');
                const kpiP95 = document.getElementById('pyxis-tel-kpi-p95');
                const kpiDrops = document.getElementById('pyxis-tel-kpi-drops');
                const kpiDropsPct = document.getElementById('pyxis-tel-kpi-drops-pct');
                const kpiRam = document.getElementById('pyxis-tel-kpi-ram');
                const kpiLargest = document.getElementById('pyxis-tel-kpi-largest');
                const kpiObjs = document.getElementById('pyxis-tel-kpi-objs');
                const kpiFrames = document.getElementById('pyxis-tel-kpi-frames');
                const kpiWorkers = document.getElementById('pyxis-tel-kpi-workers');
                const kpiElapsed = document.getElementById('pyxis-tel-kpi-elapsed');
                const hotspotsList = document.getElementById('pyxis-tel-hotspots-list');

                const pInfo = window.PyxisPreviewConfig || {};
                const resX = pInfo.res_x || 1280;
                const resY = pInfo.res_y || 720;
                const defaultFps = Number(pInfo.fps) || 23.976;
                const defaultBMs = Number(pInfo.frame_dur) || (1000.0 / defaultFps);

                if (!summary) {
                    if (metaPill) {
                        metaPill.textContent = `${resX}x${resY} | ${defaultFps.toFixed(2)} fps | 0 frames`;
                    }
                    if (gaugeArc) {
                        gaugeArc.style.strokeDashoffset = '268';
                    }
                    if (gaugePct) {
                        gaugePct.textContent = '0.0%';
                        gaugePct.setAttribute('fill', pal.accentBright);
                    }
                    if (gaugeMs) {
                        gaugeMs.textContent = '0.00 ms peak';
                        gaugeMs.setAttribute('fill', pal.textMuted);
                    }
                    if (gaugeLimit) {
                        gaugeLimit.textContent = window.t
                            ? window.t('telemetry.budget_limit', { ms: defaultBMs.toFixed(2), fps: defaultFps.toFixed(2) })
                            : `Limit ${defaultBMs.toFixed(2)} ms (${defaultFps.toFixed(2)} fps)`;
                    }
                    if (kpiPeak) {
                        kpiPeak.textContent = '0.00 ms';
                        kpiPeak.style.color = pal.accentBright;
                    }
                    if (kpiPeakSub) kpiPeakSub.textContent = 'F#0 · 00:00.000';
                    if (kpiAvg) kpiAvg.textContent = '0.00 ms';
                    if (kpiP95) kpiP95.textContent = 'P95: 0.00 ms';
                    if (kpiDrops) {
                        kpiDrops.textContent = '0';
                        kpiDrops.style.color = '#34d399';
                    }
                    if (kpiDropsPct) {
                        kpiDropsPct.textContent = window.t
                            ? window.t('telemetry.of_clip', { pct: '0.00' })
                            : '0.00% of clip';
                    }
                    if (kpiRam) kpiRam.textContent = '0 KB';
                    if (kpiLargest) {
                        kpiLargest.textContent = window.t
                            ? window.t('telemetry.max_single', { val: '0 KB' })
                            : 'Max single: 0 KB';
                    }
                    if (kpiObjs) kpiObjs.textContent = '0';
                    if (kpiFrames) {
                        kpiFrames.textContent = window.t
                            ? window.t('telemetry.frames_analyzed', { count: 0 })
                            : '0 frames analyzed';
                    }
                    if (kpiWorkers) kpiWorkers.textContent = 'libass C';
                    if (kpiElapsed) kpiElapsed.textContent = 'QPC 1us | 0 ms';
                    if (hotspotsList) {
                        const emptyTxt = window.t ? window.t('telemetry.hotspots_empty') : 'Run a scan or refresh the Previewer to detect bottlenecks.';
                        hotspotsList.innerHTML = `<div class="pyxis-tel-hotspots-empty">${emptyTxt}</div>`;
                    }
                    const hudFrame = document.getElementById('pyxis-tel-hud-frame');
                    const hudTime = document.getElementById('pyxis-tel-hud-time');
                    const hudMs = document.getElementById('pyxis-tel-hud-ms');
                    const hudRam = document.getElementById('pyxis-tel-hud-ram');
                    const hudObj = document.getElementById('pyxis-tel-hud-obj');
                    if (hudFrame) hudFrame.textContent = 'F: 0';
                    if (hudTime) hudTime.textContent = '00:00.000';
                    if (hudMs) {
                        hudMs.textContent = '0.00 ms';
                        hudMs.style.color = pal.accentBright;
                    }
                    if (hudRam) hudRam.textContent = '0 KB';
                    if (hudObj) hudObj.textContent = '0 obj';
                    return;
                }

                const fps = Number(summary.fps) || defaultFps;
                const bMs = Number(summary.frame_budget_ms) || defaultBMs;
                const totalFrames = Number(summary.total_frames) || 0;

                if (metaPill) {
                    metaPill.textContent = `${resX}x${resY} | ${fps.toFixed(2)} fps | ${totalFrames} frames`;
                }

                const budgetPct = Math.max(0, Number(summary.peak_budget_pct) || 0);
                const clampedArcPct = Math.min(100, budgetPct);
                const arcLen = 268;
                if (gaugeArc) {
                    gaugeArc.style.strokeDashoffset = String(arcLen * (1 - clampedArcPct / 100));
                }
                if (gaugePct) {
                    gaugePct.textContent = budgetPct.toFixed(1) + '%';
                    gaugePct.setAttribute('fill', getThermalColor(budgetPct / 100, 1.0));
                }
                if (gaugeMs) {
                    gaugeMs.textContent = `${(Number(summary.peak_ms) || 0).toFixed(2)} ms peak`;
                    gaugeMs.setAttribute('fill', getThermalColor(budgetPct / 100, 1.0));
                }
                if (gaugeLimit) {
                    gaugeLimit.textContent = window.t
                        ? window.t('telemetry.budget_limit', { ms: bMs.toFixed(2), fps: fps.toFixed(2) })
                        : `Limit ${bMs.toFixed(2)} ms (${fps.toFixed(2)} fps)`;
                }

                if (kpiPeak) {
                    kpiPeak.textContent = (Number(summary.peak_ms) || 0).toFixed(2) + ' ms';
                    kpiPeak.style.color = getThermalColor(budgetPct / 100, 1.0);
                }
                if (kpiPeakSub) {
                    kpiPeakSub.textContent = `F#${summary.peak_frame || 0} · ${formatMsToTimecode(summary.peak_time_ms || 0)}`;
                }
                if (kpiAvg) {
                    kpiAvg.textContent = (Number(summary.avg_ms) || 0).toFixed(2) + ' ms';
                }
                if (kpiP95) {
                    kpiP95.textContent = `P95: ${(Number(summary.p95_ms) || 0).toFixed(2)} ms`;
                }
                if (kpiDrops) {
                    const dCount = Number(summary.dropped_frames) || 0;
                    kpiDrops.textContent = String(dCount);
                    kpiDrops.style.color = dCount > 0 ? '#f43f5e' : '#34d399';
                }
                if (kpiDropsPct) {
                    const dPctStr = (Number(summary.dropped_pct) || 0).toFixed(2);
                    kpiDropsPct.textContent = window.t
                        ? window.t('telemetry.of_clip', { pct: dPctStr })
                        : `${dPctStr}% of clip`;
                }
                if (kpiRam) {
                    kpiRam.textContent = formatMemoryLabel(summary.peak_total_kb || 0);
                }
                if (kpiLargest) {
                    const lrgStr = formatMemoryLabel(summary.peak_largest_kb || 0);
                    kpiLargest.textContent = window.t
                        ? window.t('telemetry.max_single', { val: lrgStr })
                        : `Max single: ${lrgStr}`;
                }
                if (kpiObjs) {
                    kpiObjs.textContent = String(summary.peak_objects || 0);
                }
                if (kpiFrames) {
                    kpiFrames.textContent = window.t
                        ? window.t('telemetry.frames_analyzed', { count: totalFrames })
                        : `${totalFrames} frames analyzed`;
                }
                if (kpiWorkers) {
                    kpiWorkers.textContent = `libass C · ${summary.workers_used || 1}W`;
                }
                if (kpiElapsed) {
                    kpiElapsed.textContent = `QPC 1us | ${Math.round(Number(summary.elapsed_ms) || 0)} ms`;
                }

                if (hotspotsList) {
                    if (!hotspots || hotspots.length === 0) {
                        const emptyTxt = window.t ? window.t('telemetry.hotspots_empty') : 'Run a scan to detect frame bottlenecks.';
                        hotspotsList.innerHTML = `<div class="pyxis-tel-hotspots-empty">${emptyTxt}</div>`;
                    } else {
                        hotspotsList.innerHTML = hotspots.map(h => {
                            const sev = h.severity || 'nominal';
                            const borderCol = sev === 'critical' ? '#f43f5e' : (sev === 'warning' ? '#fbbf24' : pal.accentBright);
                            const tc = h.display_time || formatMsToTimecode(h.time_ms || 0);
                            const msStr = (Number(h.render_ms) || 0).toFixed(2) + ' ms';
                            const pctStr = (Number(h.budget_pct) || 0).toFixed(1) + '%';
                            const memStr = formatMemoryLabel(h.total_kb || 0);
                            return `
                                <div class="pyxis-tel-hotspot-item" style="border-left-color:${borderCol};" data-time-ms="${h.time_ms || 0}" data-frame="${h.frame || 0}">
                                    <div class="pyxis-tel-hs-time">F#${h.frame || 0} · ${tc}</div>
                                    <div class="pyxis-tel-hs-metrics">
                                        <span style="color:${borderCol};font-weight:700;">${msStr} (${pctStr})</span>
                                        <span style="color:var(--text-muted);">${memStr} · ${h.objects || 0} obj</span>
                                    </div>
                                </div>
                            `;
                        }).join('');

                        hotspotsList.querySelectorAll('.pyxis-tel-hotspot-item').forEach(row => {
                            row.addEventListener('click', () => {
                                const tMs = Number(row.getAttribute('data-time-ms')) || 0;
                                seekVideoToTimeMs(tMs);
                            });
                        });
                    }
                }
            }

            function renderMainChart() {
                const canvas = document.getElementById('pyxis-telemetry-main-chart');
                if (!canvas) return;
                const dpr = window.devicePixelRatio || 1;
                const cssW = canvas.clientWidth || 960;
                const cssH = canvas.clientHeight || 220;
                const w = Math.max(200, Math.round(cssW * dpr));
                const h = Math.max(80, Math.round(cssH * dpr));

                if (canvas.width !== w || canvas.height !== h) {
                    canvas.width = w;
                    canvas.height = h;
                }

                const ctx = canvas.getContext('2d');
                if (!ctx) return;
                ctx.clearRect(0, 0, w, h);

                const pal = getThemeTelemetryPalette();
                const padLeft = 48 * dpr;
                const padRight = 58 * dpr;
                const padTop = 16 * dpr;
                const padBottom = 24 * dpr;
                const plotW = Math.max(50, w - padLeft - padRight);
                const plotH = Math.max(30, h - padTop - padBottom);

                // Background subtle grid
                ctx.save();
                ctx.strokeStyle = hexToRgba(pal.textMuted, 0.10);
                ctx.lineWidth = 1 * dpr;
                const hLines = 4;
                for (let i = 0; i <= hLines; i++) {
                    const gy = padTop + (i / hLines) * plotH;
                    ctx.beginPath();
                    ctx.moveTo(padLeft, gy);
                    ctx.lineTo(padLeft + plotW, gy);
                    ctx.stroke();
                }
                ctx.restore();

                const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : null;
                if (!frames || frames.length < 2) {
                    ctx.save();
                    ctx.fillStyle = hexToRgba(pal.textMuted, 0.55);
                    ctx.font = `${12 * dpr}px "Inter", "Segoe UI", sans-serif`;
                    ctx.textAlign = 'center';
                    const waitTxt = window.t ? window.t('telemetry.status_idle') : 'Waiting for scan';
                    ctx.fillText(waitTxt, w / 2, h / 2);
                    ctx.restore();
                    return;
                }

                const summary = lastTelemetryData.summary || {};
                const budgetMs = Math.max(1.0, Number(summary.frame_budget_ms) || 41.708);
                const yZoom = Math.max(0.15, viewport.yScale);

                // Compute per-metric ceiling based on each metric's own scale selector
                const peakMs = Math.max(0.5, Number(summary.peak_ms) || 4.0);
                let baseMaxMs;
                if (metricScales.render_ms === 'auto') {
                    baseMaxMs = Math.max(1.0, peakMs * 1.22);
                } else if (metricScales.render_ms === 'budget') {
                    baseMaxMs = Math.max(budgetMs * 1.15, peakMs * 1.05);
                } else {
                    baseMaxMs = Math.max(0.5, Number(metricScales.render_ms) || budgetMs);
                }
                const visibleMaxMs = Math.max(0.25, baseMaxMs / yZoom);

                const peakTotalKb = Math.max(8, Number(summary.peak_total_kb) || 256);
                const baseMaxTotalKb = (metricScales.total_kb === 'auto')
                    ? Math.max(16, peakTotalKb * 1.32)
                    : Math.max(8, Number(metricScales.total_kb) || 1024);
                const visibleMaxTotalKb = Math.max(4, baseMaxTotalKb / yZoom);

                let peakLargestKb = Number(summary.peak_largest_kb) || 0;
                if (!peakLargestKb && frames.length) {
                    for (let i = 0; i < frames.length; i++) {
                        if ((frames[i].largest_kb || 0) > peakLargestKb) peakLargestKb = frames[i].largest_kb;
                    }
                }
                peakLargestKb = Math.max(4, peakLargestKb || 64);
                const baseMaxLargestKb = (metricScales.largest_kb === 'auto')
                    ? Math.max(8, peakLargestKb * 1.48)
                    : Math.max(4, Number(metricScales.largest_kb) || 256);
                const visibleMaxLargestKb = Math.max(2, baseMaxLargestKb / yZoom);

                const peakObjects = Math.max(5, Number(summary.peak_objects) || 50);
                const baseMaxObjects = (metricScales.objects === 'auto')
                    ? Math.max(10, peakObjects * 1.40)
                    : Math.max(5, Number(metricScales.objects) || 500);
                const visibleMaxObjects = Math.max(2, baseMaxObjects / yZoom);

                const iStart = Math.max(0, Math.min(frames.length - 2, Math.floor(viewport.startIdx)));
                const iEnd = Math.max(iStart + 1, Math.min(frames.length - 1, Math.ceil(viewport.endIdx)));
                const span = Math.max(1, iEnd - iStart);

                function valToY(normVal) {
                    const shifted = (normVal + viewport.yOffset);
                    return padTop + plotH - (shifted * plotH);
                }

                // Left Y-axis ms labels & Frame Budget line
                ctx.save();
                ctx.font = `${9.5 * dpr}px "JetBrains Mono", Consolas, monospace`;
                ctx.fillStyle = activeMetrics.render_ms ? hexToRgba(pal.accentBright, 0.90) : hexToRgba(pal.textMuted, 0.55);
                ctx.textAlign = 'right';
                ctx.textBaseline = 'middle';
                for (let i = 0; i <= hLines; i++) {
                    const frac = 1.0 - (i / hLines);
                    const msVal = (frac - viewport.yOffset) * visibleMaxMs;
                    if (msVal >= -0.01) {
                        const gy = padTop + (i / hLines) * plotH;
                        ctx.fillText(msVal.toFixed(1) + 'ms', padLeft - 6 * dpr, gy);
                    }
                }

                // Right Y-axis secondary metric scale labels (color-coded to active RAM/Bitmap/Objects metrics)
                const rightAxisSeries = [];
                if (activeMetrics.total_kb) {
                    rightAxisSeries.push({ max: visibleMaxTotalKb, color: '#c084fc', fmt: v => v >= 1024 ? (v / 1024).toFixed(1) + 'M' : Math.round(v) + 'K' });
                }
                if (activeMetrics.largest_kb) {
                    rightAxisSeries.push({ max: visibleMaxLargestKb, color: '#34d399', fmt: v => v >= 1024 ? (v / 1024).toFixed(1) + 'M' : Math.round(v) + 'K' });
                }
                if (activeMetrics.objects) {
                    rightAxisSeries.push({ max: visibleMaxObjects, color: '#fbbf24', fmt: v => Math.round(v) + 'ob' });
                }
                if (rightAxisSeries.length > 0) {
                    ctx.textAlign = 'left';
                    ctx.font = `${9 * dpr}px "JetBrains Mono", Consolas, monospace`;
                    const lineStep = 9.5 * dpr;
                    for (let i = 0; i <= hLines; i++) {
                        const frac = 1.0 - (i / hLines);
                        const relFrac = frac - viewport.yOffset;
                        if (relFrac < -0.01) continue;
                        const gy = padTop + (i / hLines) * plotH;
                        const blockOffset = -((rightAxisSeries.length - 1) * lineStep) / 2;
                        for (let s = 0; s < rightAxisSeries.length; s++) {
                            const ser = rightAxisSeries[s];
                            const val = Math.max(0, relFrac * ser.max);
                            ctx.fillStyle = ser.color;
                            ctx.fillText(ser.fmt(val), padLeft + plotW + 6 * dpr, gy + blockOffset + s * lineStep);
                        }
                    }
                }

                // 100% Frame Budget threshold line
                const budgetNorm = budgetMs / visibleMaxMs;
                const budgetY = valToY(budgetNorm);
                if (budgetY >= padTop && budgetY <= padTop + plotH) {
                    ctx.strokeStyle = 'rgba(244, 63, 94, 0.65)';
                    ctx.lineWidth = 1.2 * dpr;
                    ctx.setLineDash([5 * dpr, 4 * dpr]);
                    ctx.beginPath();
                    ctx.moveTo(padLeft, budgetY);
                    ctx.lineTo(padLeft + plotW, budgetY);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = 'rgba(244, 63, 94, 0.88)';
                    ctx.textAlign = 'left';
                    ctx.fillText(`Budget ${budgetMs.toFixed(1)} ms`, padLeft + 6 * dpr, Math.max(padTop + 8 * dpr, budgetY - 7 * dpr));
                }
                ctx.restore();

                // X-axis frame/timecode ticks
                ctx.save();
                ctx.font = `${10 * dpr}px "JetBrains Mono", Consolas, monospace`;
                ctx.fillStyle = hexToRgba(pal.textMuted, 0.70);
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                const vTicks = 6;
                for (let t = 0; t <= vTicks; t++) {
                    const frac = t / vTicks;
                    const fIdx = Math.min(frames.length - 1, Math.round(iStart + frac * span));
                    const fObj = frames[fIdx];
                    const gx = padLeft + frac * plotW;
                    ctx.strokeStyle = hexToRgba(pal.textMuted, 0.06);
                    ctx.beginPath();
                    ctx.moveTo(gx, padTop);
                    ctx.lineTo(gx, padTop + plotH);
                    ctx.stroke();
                    if (fObj) {
                        ctx.fillText(`F#${fObj.frame} (${formatMsToTimecode(fObj.time_ms)})`, gx, padTop + plotH + 6 * dpr);
                    }
                }
                ctx.restore();

                // Clip plot area
                ctx.save();
                ctx.beginPath();
                ctx.rect(padLeft, padTop, plotW, plotH);
                ctx.clip();

                // Sample step for dense windows
                const maxPoints = Math.min(span + 1, 800);
                const step = Math.max(1, span / maxPoints);

                function drawMetricCurve(extractor, maxRef, strokeColor, fillTopColor, lineWidthDpr) {
                    const pts = [];
                    for (let pos = iStart; pos <= iEnd; pos += step) {
                        const idx0 = Math.floor(pos);
                        const idx1 = Math.min(iEnd, Math.ceil(pos + step));
                        let peakVal = extractor(frames[idx0]);
                        for (let k = idx0 + 1; k <= idx1; k++) {
                            const v = extractor(frames[k]);
                            if (v > peakVal) peakVal = v;
                        }
                        const x = padLeft + ((pos - iStart) / span) * plotW;
                        const norm = peakVal / Math.max(1e-6, maxRef);
                        const y = valToY(norm);
                        pts.push({ x, y, val: peakVal });
                    }
                    if (pts.length < 2) return;

                    if (fillTopColor) {
                        ctx.beginPath();
                        ctx.moveTo(pts[0].x, padTop + plotH);
                        for (let i = 0; i < pts.length; i++) {
                            ctx.lineTo(pts[i].x, pts[i].y);
                        }
                        ctx.lineTo(pts[pts.length - 1].x, padTop + plotH);
                        ctx.closePath();
                        const grad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
                        grad.addColorStop(0.0, fillTopColor);
                        grad.addColorStop(1.0, hexToRgba(pal.bgCanvas, 0.02));
                        ctx.fillStyle = grad;
                        ctx.fill();
                    }

                    ctx.beginPath();
                    ctx.moveTo(pts[0].x, pts[0].y);
                    for (let i = 1; i < pts.length; i++) {
                        ctx.lineTo(pts[i].x, pts[i].y);
                    }
                    ctx.strokeStyle = strokeColor;
                    ctx.lineWidth = lineWidthDpr * dpr;
                    ctx.lineJoin = 'round';
                    ctx.stroke();
                }

                if (activeMetrics.objects) {
                    drawMetricCurve(f => Number(f.objects) || 0, visibleMaxObjects, '#f59e0b', null, 1.5);
                }
                if (activeMetrics.largest_kb) {
                    drawMetricCurve(f => Number(f.largest_kb) || 0, visibleMaxLargestKb, '#10b981', null, 1.5);
                }
                if (activeMetrics.total_kb) {
                    drawMetricCurve(f => Number(f.total_kb) || 0, visibleMaxTotalKb, '#a855f7', 'rgba(168, 85, 247, 0.14)', 1.6);
                }
                if (activeMetrics.render_ms) {
                    drawMetricCurve(f => Number(f.render_ms) || 0, visibleMaxMs, pal.accentBright, hexToRgba(pal.accent, 0.28), 2.0);
                }

                // Synchronized Laser Playhead
                const playIdx = getCurrentPlayheadFrameIndex();
                if (playIdx >= iStart && playIdx <= iEnd) {
                    const px = padLeft + ((playIdx - iStart) / span) * plotW;
                    ctx.save();
                    ctx.strokeStyle = pal.accentBright;
                    ctx.shadowColor = hexToRgba(pal.accentBright, 0.85);
                    ctx.shadowBlur = 8 * dpr;
                    ctx.lineWidth = 1.8 * dpr;
                    ctx.beginPath();
                    ctx.moveTo(px, padTop);
                    ctx.lineTo(px, padTop + plotH);
                    ctx.stroke();

                    // Top diamond cap
                    ctx.fillStyle = pal.accentBright;
                    ctx.beginPath();
                    ctx.moveTo(px, padTop);
                    ctx.lineTo(px - 5 * dpr, padTop + 5 * dpr);
                    ctx.lineTo(px, padTop + 10 * dpr);
                    ctx.lineTo(px + 5 * dpr, padTop + 5 * dpr);
                    ctx.closePath();
                    ctx.fill();
                    ctx.restore();
                }

                // Hover inspection crosshair
                if (hoverState.active && hoverState.frameIdx >= iStart && hoverState.frameIdx <= iEnd) {
                    const hx = padLeft + ((hoverState.frameIdx - iStart) / span) * plotW;
                    ctx.save();
                    ctx.strokeStyle = hexToRgba(pal.textMain, 0.45);
                    ctx.lineWidth = 1 * dpr;
                    ctx.setLineDash([3 * dpr, 3 * dpr]);
                    ctx.beginPath();
                    ctx.moveTo(hx, padTop);
                    ctx.lineTo(hx, padTop + plotH);
                    ctx.stroke();
                    ctx.restore();
                }

                ctx.restore();
            }

            function renderMinimap() {
                const canvas = document.getElementById('pyxis-telemetry-minimap');
                if (!canvas) return;
                const dpr = window.devicePixelRatio || 1;
                const cssW = canvas.clientWidth || 960;
                const cssH = canvas.clientHeight || 22;
                const w = Math.max(120, Math.round(cssW * dpr));
                const h = Math.max(16, Math.round(cssH * dpr));

                if (canvas.width !== w || canvas.height !== h) {
                    canvas.width = w;
                    canvas.height = h;
                }

                const ctx = canvas.getContext('2d');
                if (!ctx) return;
                ctx.clearRect(0, 0, w, h);

                const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : null;
                if (!frames || frames.length < 2) return;

                const pal = getThemeTelemetryPalette();
                const summary = lastTelemetryData.summary || {};
                const peakMs = Math.max(0.20, Number(summary.peak_ms) || 1.0);

                // Mini sparkline auto-scaled to clip peak_ms for full silhouette visibility
                const buckets = Math.min(frames.length, 320);
                ctx.beginPath();
                ctx.moveTo(0, h);
                for (let b = 0; b < buckets; b++) {
                    const i0 = Math.floor((b / buckets) * frames.length);
                    const i1 = Math.max(i0 + 1, Math.floor(((b + 1) / buckets) * frames.length));
                    let localMax = 0;
                    for (let i = i0; i < i1 && i < frames.length; i++) {
                        const v = Number(frames[i].render_ms) || 0;
                        if (v > localMax) localMax = v;
                    }
                    const x = (b / Math.max(1, buckets - 1)) * w;
                    const norm = localMax > 0.001 ? Math.min(1.0, Math.pow(localMax / peakMs, 0.85)) : 0;
                    const y = h - norm * (h - 3 * dpr);
                    ctx.lineTo(x, y);
                }
                ctx.lineTo(w, h);
                ctx.closePath();
                ctx.fillStyle = hexToRgba(pal.accent, 0.32);
                ctx.fill();
                ctx.strokeStyle = hexToRgba(pal.accentBright, 0.78);
                ctx.lineWidth = 1.1 * dpr;
                ctx.stroke();

                // Current zoom window box
                const total = Math.max(1, frames.length - 1);
                const x0 = (viewport.startIdx / total) * w;
                const x1 = (viewport.endIdx / total) * w;
                const boxW = Math.max(8 * dpr, x1 - x0);

                ctx.fillStyle = hexToRgba(pal.accent, 0.16);
                ctx.fillRect(x0, 0, boxW, h);
                ctx.strokeStyle = hexToRgba(pal.accentBright, 0.88);
                ctx.lineWidth = 1.5 * dpr;
                ctx.strokeRect(x0, 0.75 * dpr, boxW, h - 1.5 * dpr);

                // Playhead position line inside minimap
                const playheadIdx = getCurrentPlayheadFrameIndex();
                if (playheadIdx >= 0 && playheadIdx <= total) {
                    const px = (playheadIdx / total) * w;
                    ctx.save();
                    ctx.strokeStyle = hexToRgba(pal.textMain, 0.92);
                    ctx.lineWidth = 1.4 * dpr;
                    ctx.beginPath();
                    ctx.moveTo(px, 0);
                    ctx.lineTo(px, h);
                    ctx.stroke();
                    ctx.restore();
                }
            }

            function syncVideoHudAndPlayhead() {
                if (!isOpen) return;
                const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : null;
                if (frames && frames.length > 0) {
                    const fIdx = getCurrentPlayheadFrameIndex();
                    if (fIdx !== lastSyncedFrameIdx) {
                        lastSyncedFrameIdx = fIdx;
                        const fObj = frames[fIdx];
                        if (fObj) {
                            const hudFrame = document.getElementById('pyxis-tel-hud-frame');
                            const hudTime = document.getElementById('pyxis-tel-hud-time');
                            const hudMs = document.getElementById('pyxis-tel-hud-ms');
                            const hudRam = document.getElementById('pyxis-tel-hud-ram');
                            const hudObj = document.getElementById('pyxis-tel-hud-obj');
                            const budgetMs = (lastTelemetryData.summary && Number(lastTelemetryData.summary.frame_budget_ms)) || 41.708;
                            if (hudFrame) hudFrame.textContent = `F: ${fObj.frame}`;
                            if (hudTime) hudTime.textContent = formatMsToTimecode(fObj.time_ms || 0);
                            if (hudMs) {
                                const ms = Number(fObj.render_ms) || 0;
                                hudMs.textContent = `${ms.toFixed(2)} ms`;
                                hudMs.style.color = getThermalColor(ms / budgetMs, 1.0);
                            }
                            if (hudRam) {
                                hudRam.textContent = formatMemoryLabel(fObj.total_kb || 0);
                            }
                            if (hudObj) {
                                hudObj.textContent = `${fObj.objects || 0} obj`;
                            }
                        }
                        renderMainChart();
                        renderMinimap();
                    }
                }
                rafId = requestAnimationFrame(syncVideoHudAndPlayhead);
            }

            let customCockpitSize = null;
            try {
                const savedSize = JSON.parse(localStorage.getItem('pyxis_telemetry_player_size') || 'null');
                if (savedSize && typeof savedSize === 'object' && savedSize.w > 0 && savedSize.h > 0) {
                    customCockpitSize = savedSize;
                }
            } catch (e) {}

            function getCockpitAspectRatio() {
                let aspect = 16 / 9;
                const target = getTargetPlayer();
                if (target && target.player) {
                    const p = target.player;
                    if (typeof p.getNativeResolution === 'function') {
                        const res = p.getNativeResolution();
                        if (res && res.w > 0 && res.h > 0) {
                            aspect = res.w / res.h;
                        }
                    } else if (p.art && p.art.video && p.art.video.videoWidth > 0 && p.art.video.videoHeight > 0) {
                        aspect = p.art.video.videoWidth / p.art.video.videoHeight;
                    }
                } else if (window.PyxisPreviewConfig && window.PyxisPreviewConfig.res_x > 0 && window.PyxisPreviewConfig.res_y > 0) {
                    aspect = window.PyxisPreviewConfig.res_x / window.PyxisPreviewConfig.res_y;
                }
                return (isFinite(aspect) && aspect > 0.2) ? aspect : (16 / 9);
            }

            function syncCockpitVideoLayout() {
                if (!isOpen) return;
                const stage = document.getElementById('pyxis-tel-video-stage');
                const videoPane = stage ? stage.closest('.pyxis-tel-video-pane') : document.querySelector('.pyxis-tel-video-pane');
                if (!videoPane) return;

                const bodyEl = videoPane.closest('.pyxis-tel-body');
                const bottomBarH = 68;
                const aspect = getCockpitAspectRatio();
                const target = getTargetPlayer();
                const isZoomed = Boolean(target && target.player && target.player.transformState && target.player.transformState.isCustom);

                const bodyW = (bodyEl && bodyEl.clientWidth) ? bodyEl.clientWidth : window.innerWidth;
                const bodyH = (bodyEl && bodyEl.clientHeight) ? bodyEl.clientHeight : (window.innerHeight - 54);
                const minW = 260;
                const maxW = Math.max(320, Math.min(Math.round(window.innerWidth * 0.72), bodyW - 420));
                const minH = 185;
                const maxH = Math.max(230, bodyH - 190);

                if (customCockpitSize && customCockpitSize.w > 0 && customCockpitSize.h > 0) {
                    let targetW, targetH;
                    if (customCockpitSize.free && isZoomed) {
                        targetW = Math.max(minW, Math.min(maxW, Math.round(customCockpitSize.w)));
                        targetH = Math.max(minH, Math.min(maxH, Math.round(customCockpitSize.h)));
                    } else {
                        const effMinW = Math.max(minW, Math.round((minH - bottomBarH) * aspect));
                        const effMaxW = Math.max(effMinW, Math.min(maxW, Math.round((maxH - bottomBarH) * aspect)));
                        targetW = Math.max(effMinW, Math.min(effMaxW, Math.round(customCockpitSize.w)));
                        targetH = Math.round(targetW / aspect) + bottomBarH;
                    }
                    if (bodyEl) {
                        bodyEl.style.gridTemplateRows = `${targetH}px 1fr`;
                    }
                    videoPane.style.width = `${targetW}px`;
                } else {
                    if (bodyEl) {
                        bodyEl.style.gridTemplateRows = '';
                    }
                    const paneH = videoPane.clientHeight || 360;
                    const frameH = Math.max(120, paneH - bottomBarH);
                    const idealPaneW = Math.round(frameH * aspect);
                    const targetW = Math.max(minW, Math.min(maxW, idealPaneW));
                    videoPane.style.width = `${targetW}px`;
                }

                if (reparentedPlayer && reparentedPlayer.player) {
                    const p = reparentedPlayer.player;
                    if (p.art && typeof p.art.resize === 'function') {
                        try { p.art.resize(); } catch (e) {}
                    }
                    if (p.jassub && typeof p.jassub.resize === 'function') {
                        try { p.jassub.resize(); } catch (e) {}
                    }
                    if (typeof p.applyTransform === 'function') {
                        try { p.applyTransform(); } catch (e) {}
                    }
                }
            }

            function attachPlayerToCockpit(preferredNodeId) {
                const stage = document.getElementById('pyxis-tel-video-stage');
                if (!stage) return;

                if (reparentedPlayer) {
                    detachPlayerFromCockpit();
                }

                const target = getTargetPlayer(preferredNodeId);
                if (!target || !target.player || !target.player.box) {
                    syncCockpitVideoLayout();
                    return;
                }

                const p = target.player;
                const box = p.box;
                if (p.isFullscreen && typeof p.toggleFullscreen === 'function') {
                    p.toggleFullscreen(false);
                }
                reparentedPlayer = {
                    nodeIdStr: target.nodeIdStr,
                    player: p,
                    box: box,
                    originalParent: box.parentNode,
                    originalNextSibling: box.nextSibling
                };

                p.inTelemetryCockpit = true;
                const fsBtn = box.querySelector('.pyxis-pbtn-fullscreen');
                if (fsBtn) {
                    fsBtn.style.display = 'none';
                }
                stage.appendChild(box);
                syncCockpitVideoLayout();

                requestAnimationFrame(() => {
                    syncCockpitVideoLayout();
                });
                setTimeout(() => {
                    if (isOpen) syncCockpitVideoLayout();
                }, 120);
            }

            function detachPlayerFromCockpit() {
                if (!reparentedPlayer) return;
                const { player, box, originalParent, originalNextSibling } = reparentedPlayer;
                if (player) {
                    player.inTelemetryCockpit = false;
                }
                if (box) {
                    const fsBtn = box.querySelector('.pyxis-pbtn-fullscreen');
                    if (fsBtn) {
                        fsBtn.style.display = '';
                    }
                }
                if (box && originalParent) {
                    if (originalNextSibling && originalNextSibling.parentNode === originalParent) {
                        originalParent.insertBefore(box, originalNextSibling);
                    } else {
                        originalParent.appendChild(box);
                    }
                }
                reparentedPlayer = null;

                requestAnimationFrame(() => {
                    if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.updateInNodePlayersPosition === 'function') {
                        window.PyxisNodePlayerManager.updateInNodePlayersPosition();
                    }
                    if (player) {
                        if (player.art && typeof player.art.resize === 'function') {
                            try { player.art.resize(); } catch (e) {}
                        }
                        if (player.jassub && typeof player.jassub.resize === 'function') {
                            try { player.jassub.resize(); } catch (e) {}
                        }
                        if (typeof player.applyTransform === 'function') {
                            try { player.applyTransform(); } catch (e) {}
                        }
                    }
                });
            }

            async function triggerFromPreviewer(nodeId, serialized, connectedOutputIds, source, forceRegenerate = false) {
                if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.run_ass_telemetry !== 'function') {
                    return null;
                }
                isScanning = true;
                setStatusUI('scanning');
                try {
                    let clipStartMs = null;
                    let clipEndMs = null;
                    const effNodeId = nodeId || (reparentedPlayer ? reparentedPlayer.nodeIdStr : null);
                    if (effNodeId && window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.getPreviewBounds === 'function') {
                        const bounds = window.PyxisNodePlayerManager.getPreviewBounds(String(effNodeId));
                        if (bounds && typeof bounds.winStart === 'number' && typeof bounds.winEnd === 'number' && bounds.winEnd > bounds.winStart) {
                            clipStartMs = Math.round(bounds.winStart * 1000);
                            clipEndMs = Math.round(bounds.winEnd * 1000);
                        }
                    }
                    const res = await window.pywebview.api.run_ass_telemetry(
                        serialized,
                        connectedOutputIds,
                        source,
                        Boolean(forceRegenerate),
                        clipStartMs,
                        clipEndMs
                    );
                    if (res && res.status === 'cancelled') {
                        return res;
                    }
                    if (res && (res.status === 'ok' || res.success)) {
                        lastTelemetryData = res;
                        isScanning = false;
                        setStatusUI('ready');
                        resetViewportToFull();
                        renderAllPreviewerHeatmaps();
                        if (isOpen) {
                            syncCockpitVideoLayout();
                            updateCockpitKPIs();
                            renderMainChart();
                            renderMinimap();
                        }
                        if (typeof window.triggerWorkloadEstimation === 'function') {
                            try { window.triggerWorkloadEstimation(true); } catch (e) {}
                        }
                        return res;
                    } else {
                        isScanning = false;
                        setStatusUI('error', (res && res.message) ? res.message : null);
                        return res;
                    }
                } catch (err) {
                    isScanning = false;
                    setStatusUI('error');
                    console.error('[PyxisTelemetry] Scan error:', err);
                    return null;
                }
            }

            function clearData(notifyBackend = false) {
                lastTelemetryData = null;
                isScanning = false;
                lastSyncedFrameIdx = -1;
                document.querySelectorAll('.pyxis-pbar-container.is-heatmap-expanded').forEach(el => {
                    el.classList.remove('is-heatmap-expanded');
                });
                setStatusUI('idle');
                resetViewportToFull();
                renderAllPreviewerHeatmaps();
                updateCockpitKPIs();
                renderMainChart();
                renderMinimap();
                if (notifyBackend && window.pywebview && window.pywebview.api && typeof window.pywebview.api.clear_ass_telemetry === 'function') {
                    try { window.pywebview.api.clear_ass_telemetry(); } catch (e) {}
                }
            }

            async function rescan(forceRegen = true) {
                const target = getTargetPlayer();
                const serialized = (window.graph && typeof window.graph.serialize === 'function') ? window.graph.serialize() : null;
                let connectedOutputs = null;
                let source = 'base';
                let nodeId = null;

                if (target && target.player && target.player.node) {
                    nodeId = target.nodeIdStr;
                    const node = target.player.node;
                    source = (node.properties && node.properties.preview_source) || 'base';
                    if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.resolveConnectedOutputsForPreview === 'function') {
                        connectedOutputs = window.PyxisNodePlayerManager.resolveConnectedOutputsForPreview(node);
                    }
                }
                return await triggerFromPreviewer(nodeId, serialized, connectedOutputs, source, Boolean(forceRegen));
            }

            async function open(preferredNodeId) {
                const overlay = document.getElementById('pyxis-telemetry-overlay');
                if (!overlay) return;

                isOpen = true;
                lastSyncedFrameIdx = -1;
                syncFilterControlsDOM();
                overlay.classList.add('is-open', 'visible');
                overlay.setAttribute('aria-hidden', 'false');

                attachPlayerToCockpit(preferredNodeId);
                syncCockpitVideoLayout();

                if (lastTelemetryData) {
                    setStatusUI('ready');
                } else if (!isScanning) {
                    setStatusUI('idle');
                }
                updateCockpitKPIs();
                renderMainChart();
                renderMinimap();

                if (rafId) cancelAnimationFrame(rafId);
                rafId = requestAnimationFrame(syncVideoHudAndPlayhead);
            }

            function close() {
                const overlay = document.getElementById('pyxis-telemetry-overlay');
                if (!overlay) return;
                isOpen = false;
                if (rafId) {
                    cancelAnimationFrame(rafId);
                    rafId = null;
                }
                detachPlayerFromCockpit();
                overlay.classList.remove('is-open', 'visible');
                overlay.setAttribute('aria-hidden', 'true');
            }

            function toggleMetric(metric, btnEl) {
                if (!metric || !activeMetrics.hasOwnProperty(metric)) return;
                activeMetrics[metric] = !activeMetrics[metric];
                if (btnEl) {
                    btnEl.classList.toggle('is-active', activeMetrics[metric]);
                }
                persistTelemetryConfig();
                renderMainChart();
            }

            function setMetricScale(metric, scaleVal) {
                if (!metric || !metricScales.hasOwnProperty(metric)) return;
                metricScales[metric] = scaleVal || 'auto';
                if (!activeMetrics[metric]) {
                    activeMetrics[metric] = true;
                    const selEl = document.getElementById('pyxis-tel-scale-' + metric);
                    const pillBtn = selEl && selEl.parentElement ? selEl.parentElement.querySelector('.pyxis-tel-filter-pill') : null;
                    if (pillBtn) pillBtn.classList.add('is-active');
                }
                persistTelemetryConfig();
                renderMainChart();
            }

            function resetView() {
                resetViewportToFull();
                renderMainChart();
                renderMinimap();
                const target = getTargetPlayer();
                if (target && target.player && typeof target.player.resetTransform === 'function') {
                    const p = target.player;
                    if (p.transformState && p.transformState.isCustom) {
                        p.resetTransform(true);
                    }
                }
            }

            function setupTelemetryDomEvents() {
                // Main chart Blender Motion Tracking 2D Zoom & Pan + LMB Video Scrub
                const mainChart = document.getElementById('pyxis-telemetry-main-chart');
                const chartStage = document.getElementById('pyxis-tel-chart-stage');
                const tooltipEl = document.getElementById('pyxis-tel-chart-tooltip');

                if (mainChart) {
                    let isDraggingMMB = false;
                    let isScrubbingLMB = false;
                    let dragStartX = 0;
                    let dragStartY = 0;
                    let dragStartViewport = null;

                    function canvasClientToFrameIdx(clientX) {
                        const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : null;
                        if (!frames || frames.length < 2) return 0;
                        const rect = mainChart.getBoundingClientRect();
                        const padLeftCss = 48;
                        const padRightCss = 58;
                        const plotWCss = Math.max(40, rect.width - padLeftCss - padRightCss);
                        const relX = Math.max(0, Math.min(plotWCss, clientX - rect.left - padLeftCss));
                        const pct = relX / plotWCss;
                        const span = Math.max(1, viewport.endIdx - viewport.startIdx);
                        return Math.max(0, Math.min(frames.length - 1, Math.round(viewport.startIdx + pct * span)));
                    }

                    mainChart.addEventListener('wheel', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : null;
                        if (!frames || frames.length < 2) return;

                        const rect = mainChart.getBoundingClientRect();
                        const padLeftCss = 48;
                        const padRightCss = 58;
                        const plotWCss = Math.max(40, rect.width - padLeftCss - padRightCss);
                        const cursorPctX = Math.max(0, Math.min(1, (e.clientX - rect.left - padLeftCss) / plotWCss));

                        if (e.ctrlKey || e.shiftKey) {
                            // Vertical Y-axis scale
                            const zoomFactorY = e.deltaY < 0 ? 1.18 : (1 / 1.18);
                            viewport.yScale = Math.max(0.25, Math.min(12.0, viewport.yScale * zoomFactorY));
                        } else {
                            // Horizontal X-axis zoom anchored at cursor
                            const totalMax = frames.length - 1;
                            const curSpan = Math.max(4, viewport.endIdx - viewport.startIdx);
                            const zoomFactorX = e.deltaY < 0 ? 0.80 : 1.25;
                            const newSpan = Math.max(8, Math.min(totalMax, curSpan * zoomFactorX));
                            const anchorIdx = viewport.startIdx + cursorPctX * curSpan;
                            let newStart = anchorIdx - cursorPctX * newSpan;
                            let newEnd = newStart + newSpan;
                            if (newStart < 0) {
                                newStart = 0;
                                newEnd = Math.min(totalMax, newSpan);
                            }
                            if (newEnd > totalMax) {
                                newEnd = totalMax;
                                newStart = Math.max(0, totalMax - newSpan);
                            }
                            viewport.startIdx = newStart;
                            viewport.endIdx = newEnd;
                        }
                        updateZoomBadge();
                        renderMainChart();
                        renderMinimap();
                    }, { passive: false });

                    mainChart.addEventListener('pointerdown', (e) => {
                        if (e.button === 1) {
                            // Middle Mouse Button -> 2D Pan
                            e.preventDefault();
                            isDraggingMMB = true;
                            dragStartX = e.clientX;
                            dragStartY = e.clientY;
                            dragStartViewport = { ...viewport };
                            if (chartStage) chartStage.classList.add('is-panning');
                            try { mainChart.setPointerCapture(e.pointerId); } catch (err) {}
                        } else if (e.button === 0) {
                            // Left Mouse Button -> Scrub video
                            isScrubbingLMB = true;
                            const fIdx = canvasClientToFrameIdx(e.clientX);
                            if (lastTelemetryData && lastTelemetryData.frames && lastTelemetryData.frames[fIdx]) {
                                seekVideoToTimeMs(lastTelemetryData.frames[fIdx].time_ms);
                            }
                            try { mainChart.setPointerCapture(e.pointerId); } catch (err) {}
                        }
                    });

                    mainChart.addEventListener('pointermove', (e) => {
                        const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : null;
                        if (!frames || frames.length < 2) return;

                        if (isDraggingMMB && dragStartViewport) {
                            const rect = mainChart.getBoundingClientRect();
                            const plotWCss = Math.max(40, rect.width - 106);
                            const plotHCss = Math.max(30, rect.height - 40);
                            const dx = e.clientX - dragStartX;
                            const dy = e.clientY - dragStartY;
                            const span = dragStartViewport.endIdx - dragStartViewport.startIdx;
                            const deltaIdx = -(dx / plotWCss) * span;
                            const totalMax = frames.length - 1;

                            let newStart = dragStartViewport.startIdx + deltaIdx;
                            let newEnd = dragStartViewport.endIdx + deltaIdx;
                            if (newStart < 0) {
                                newStart = 0;
                                newEnd = span;
                            }
                            if (newEnd > totalMax) {
                                newEnd = totalMax;
                                newStart = Math.max(0, totalMax - span);
                            }
                            viewport.startIdx = newStart;
                            viewport.endIdx = newEnd;
                            viewport.yOffset = Math.max(-0.8, Math.min(0.8, dragStartViewport.yOffset - (dy / plotHCss)));
                            scheduleChartRender(true);
                            return;
                        }

                        const fIdx = canvasClientToFrameIdx(e.clientX);
                        if (isScrubbingLMB) {
                            if (frames[fIdx]) {
                                seekVideoToTimeMs(frames[fIdx].time_ms, false);
                            }
                        }

                        // Update hover tooltip
                        const frameChanged = (!hoverState.active || hoverState.frameIdx !== fIdx);
                        hoverState.active = true;
                        hoverState.frameIdx = fIdx;
                        const fObj = frames[fIdx];
                        if (fObj && tooltipEl) {
                            const rect = mainChart.getBoundingClientRect();
                            if (frameChanged) {
                                const budgetMs = (lastTelemetryData.summary && Number(lastTelemetryData.summary.frame_budget_ms)) || 41.708;
                                const bPct = ((Number(fObj.render_ms) || 0) / budgetMs) * 100;
                                tooltipEl.innerHTML = `
                                    <div style="font-weight:800;color:var(--doc-accent-bright);margin-bottom:3px;">Frame #${fObj.frame} · ${formatMsToTimecode(fObj.time_ms)}</div>
                                    <div>Render: <strong>${(Number(fObj.render_ms) || 0).toFixed(2)} ms (${bPct.toFixed(1)}%)</strong></div>
                                    <div>Total RAM: <strong>${formatMemoryLabel(fObj.total_kb)}</strong></div>
                                    <div>Largest Bitmap: <strong>${formatMemoryLabel(fObj.largest_kb)}</strong></div>
                                    <div>ASS Objects: <strong>${fObj.objects || 0}</strong></div>
                                `;
                            }
                            tooltipEl.style.display = 'block';
                            const tipX = Math.min(rect.width - 195, Math.max(54, e.clientX - rect.left + 14));
                            const tipY = Math.max(10, Math.min(rect.height - 110, e.clientY - rect.top - 24));
                            tooltipEl.style.left = tipX + 'px';
                            tooltipEl.style.top = tipY + 'px';
                        }
                        if (frameChanged) {
                            scheduleChartRender(false);
                        }
                    });

                    const endChartPointer = (e) => {
                        if (isDraggingMMB || isScrubbingLMB) {
                            isDraggingMMB = false;
                            isScrubbingLMB = false;
                            dragStartViewport = null;
                            if (chartStage) chartStage.classList.remove('is-panning');
                            try { mainChart.releasePointerCapture(e.pointerId); } catch (err) {}
                        }
                    };
                    mainChart.addEventListener('pointerup', endChartPointer);
                    mainChart.addEventListener('pointercancel', endChartPointer);
                    mainChart.addEventListener('mouseleave', () => {
                        hoverState.active = false;
                        if (tooltipEl) tooltipEl.style.display = 'none';
                        scheduleChartRender(false);
                    });
                }

                // Minimap click/drag pan
                const minimap = document.getElementById('pyxis-telemetry-minimap');
                if (minimap) {
                    let isDraggingMini = false;
                    function panMinimapToClientX(clientX) {
                        const frames = (lastTelemetryData && Array.isArray(lastTelemetryData.frames)) ? lastTelemetryData.frames : null;
                        if (!frames || frames.length < 2) return;
                        const rect = minimap.getBoundingClientRect();
                        const pct = Math.max(0, Math.min(1, (clientX - rect.left) / Math.max(1, rect.width)));
                        const totalMax = frames.length - 1;
                        const span = Math.max(4, viewport.endIdx - viewport.startIdx);
                        let newStart = pct * totalMax - span / 2;
                        let newEnd = newStart + span;
                        if (newStart < 0) {
                            newStart = 0;
                            newEnd = Math.min(totalMax, span);
                        }
                        if (newEnd > totalMax) {
                            newEnd = totalMax;
                            newStart = Math.max(0, totalMax - span);
                        }
                        viewport.startIdx = newStart;
                        viewport.endIdx = newEnd;
                        scheduleChartRender(true);
                    }
                    minimap.addEventListener('pointerdown', (e) => {
                        isDraggingMini = true;
                        panMinimapToClientX(e.clientX);
                        try { minimap.setPointerCapture(e.pointerId); } catch (err) {}
                    });
                    minimap.addEventListener('pointermove', (e) => {
                        if (isDraggingMini) panMinimapToClientX(e.clientX);
                    });
                    const endMini = (e) => {
                        if (isDraggingMini) {
                            isDraggingMini = false;
                            try { minimap.releasePointerCapture(e.pointerId); } catch (err) {}
                        }
                    };
                    minimap.addEventListener('pointerup', endMini);
                    minimap.addEventListener('pointercancel', endMini);
                }

                // Keyboard shortcuts when Telemetry is open (Escape to close, R / Home to reset zoom)
                window.addEventListener('keydown', (e) => {
                    if (!isOpen) return;
                    const activeEl = document.activeElement;
                    if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable)) {
                        return;
                    }
                    if (e.key === 'Escape') {
                        e.preventDefault();
                        e.stopPropagation();
                        close();
                    } else if (e.key === 'Home' || e.key === 'r' || e.key === 'R') {
                        resetView();
                    }
                });

                // Real-time interactive video pane resizers (Right, Bottom, Bottom-Right Corner)
                const videoPane = document.getElementById('pyxis-tel-video-pane') || document.querySelector('.pyxis-tel-video-pane');
                if (videoPane) {
                    const bodyEl = videoPane.closest('.pyxis-tel-body');
                    const resizers = videoPane.querySelectorAll('.pyxis-tel-resizer');
                    resizers.forEach((handle) => {
                        const handleType = handle.getAttribute('data-resize') || 'se';
                        let isResizingPane = false;
                        let startX = 0;
                        let startY = 0;
                        let startW = 0;
                        let startH = 0;
                        let cachedAspect = 16 / 9;
                        let resizeRaf = null;

                        handle.addEventListener('pointerdown', (e) => {
                            if (e.button !== 0) return;
                            e.preventDefault();
                            e.stopPropagation();

                            const target = getTargetPlayer();
                            const p = target ? target.player : null;
                            if (p && typeof p.cancelResetAnimation === 'function') {
                                p.cancelResetAnimation();
                            }
                            if (p) {
                                p.isResizing = true;
                            }

                            isResizingPane = true;
                            startX = e.clientX;
                            startY = e.clientY;
                            const rect = videoPane.getBoundingClientRect();
                            startW = rect.width;
                            startH = rect.height;
                            cachedAspect = getCockpitAspectRatio();

                            videoPane.classList.add('is-resizing');
                            document.body.classList.add('pyxis-resizing-active');
                            try { handle.setPointerCapture(e.pointerId); } catch (err) {}
                        });

                        handle.addEventListener('pointermove', (e) => {
                            if (!isResizingPane) return;
                            e.preventDefault();
                            e.stopPropagation();

                            const dx = e.clientX - startX;
                            const dy = e.clientY - startY;
                            const bottomBarH = 68;
                            const bodyW = (bodyEl && bodyEl.clientWidth) ? bodyEl.clientWidth : window.innerWidth;
                            const bodyH = (bodyEl && bodyEl.clientHeight) ? bodyEl.clientHeight : (window.innerHeight - 54);
                            const minW = 260;
                            const maxW = Math.max(320, Math.min(Math.round(window.innerWidth * 0.72), bodyW - 420));
                            const minH = 185;
                            const maxH = Math.max(230, bodyH - 190);

                            const target = getTargetPlayer();
                            const p = target ? target.player : null;
                            const isZoomed = Boolean(p && p.transformState && p.transformState.isCustom);

                            let newW = startW;
                            let newH = startH;

                            if (isZoomed) {
                                if (handleType === 'e') {
                                    newW = Math.max(minW, Math.min(maxW, Math.round(startW + dx)));
                                    newH = Math.max(minH, Math.min(maxH, Math.round(startH)));
                                } else if (handleType === 's') {
                                    newW = Math.max(minW, Math.min(maxW, Math.round(startW)));
                                    newH = Math.max(minH, Math.min(maxH, Math.round(startH + dy)));
                                } else {
                                    newW = Math.max(minW, Math.min(maxW, Math.round(startW + dx)));
                                    newH = Math.max(minH, Math.min(maxH, Math.round(startH + dy)));
                                }
                                customCockpitSize = { w: newW, h: newH, free: true };
                            } else {
                                const effMinW = Math.max(minW, Math.round((minH - bottomBarH) * cachedAspect));
                                const effMaxW = Math.max(effMinW, Math.min(maxW, Math.round((maxH - bottomBarH) * cachedAspect)));

                                if (handleType === 'e') {
                                    newW = Math.max(effMinW, Math.min(effMaxW, Math.round(startW + dx)));
                                } else if (handleType === 's') {
                                    const targetWFromH = Math.round((startH + dy - bottomBarH) * cachedAspect);
                                    newW = Math.max(effMinW, Math.min(effMaxW, targetWFromH));
                                } else {
                                    const deltaW = Math.round((dx * cachedAspect + dy) * cachedAspect / (cachedAspect * cachedAspect + 1));
                                    newW = Math.max(effMinW, Math.min(effMaxW, Math.round(startW + deltaW)));
                                }
                                newH = Math.round(newW / cachedAspect) + bottomBarH;
                                customCockpitSize = { w: newW, h: newH, free: false };
                            }

                            if (!resizeRaf) {
                                resizeRaf = requestAnimationFrame(() => {
                                    resizeRaf = null;
                                    if (!isResizingPane || !customCockpitSize) return;
                                    if (bodyEl) {
                                        bodyEl.style.gridTemplateRows = `${customCockpitSize.h}px 1fr`;
                                    }
                                    videoPane.style.width = `${customCockpitSize.w}px`;

                                    if (reparentedPlayer && reparentedPlayer.player) {
                                        const rp = reparentedPlayer.player;
                                        if (typeof rp.applyTransform === 'function') {
                                            try { rp.applyTransform(); } catch (err) {}
                                        }
                                        if (rp.art && typeof rp.art.resize === 'function') {
                                            try { rp.art.resize(); } catch (err) {}
                                        }
                                        if (rp.jassub && typeof rp.jassub.resize === 'function') {
                                            try { rp.jassub.resize(); } catch (err) {}
                                        }
                                    }
                                    renderMainChart();
                                    renderMinimap();
                                });
                            }
                        });

                        const finishPaneResize = (e) => {
                            if (!isResizingPane) return;
                            isResizingPane = false;
                            if (resizeRaf) {
                                cancelAnimationFrame(resizeRaf);
                                resizeRaf = null;
                            }
                            videoPane.classList.remove('is-resizing');
                            document.body.classList.remove('pyxis-resizing-active');
                            try { handle.releasePointerCapture(e.pointerId); } catch (err) {}

                            const target = getTargetPlayer();
                            const p = target ? target.player : null;
                            if (p) {
                                p.isResizing = false;
                                if (p.transformState) delete p.transformState.resizeAnchor;
                            }
                            if (customCockpitSize) {
                                try {
                                    localStorage.setItem('pyxis_telemetry_player_size', JSON.stringify(customCockpitSize));
                                } catch (err) {}
                            }
                            syncCockpitVideoLayout();
                            renderMainChart();
                            renderMinimap();
                        };

                        handle.addEventListener('pointerup', finishPaneResize);
                        handle.addEventListener('pointercancel', finishPaneResize);

                        handle.addEventListener('dblclick', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            customCockpitSize = null;
                            try { localStorage.removeItem('pyxis_telemetry_player_size'); } catch (err) {}
                            const target = getTargetPlayer();
                            if (target && target.player && typeof target.player.resetTransform === 'function' && target.player.transformState && target.player.transformState.isCustom) {
                                target.player.resetTransform(true);
                            } else {
                                syncCockpitVideoLayout();
                                renderMainChart();
                                renderMinimap();
                            }
                        });
                    });
                }

                syncFilterControlsDOM();

                window.addEventListener('resize', () => {
                    renderAllPreviewerHeatmaps();
                    if (isOpen) {
                        syncCockpitVideoLayout();
                        renderMainChart();
                        renderMinimap();
                    }
                });
            }

            function resetCockpitSizeToAspect() {
                if (customCockpitSize && customCockpitSize.w > 0) {
                    const aspect = getCockpitAspectRatio();
                    const bottomBarH = 68;
                    const bodyEl = document.querySelector('.pyxis-tel-body');
                    const bodyW = (bodyEl && bodyEl.clientWidth) ? bodyEl.clientWidth : window.innerWidth;
                    const bodyH = (bodyEl && bodyEl.clientHeight) ? bodyEl.clientHeight : (window.innerHeight - 54);
                    const minW = 260;
                    const maxW = Math.max(320, Math.min(Math.round(window.innerWidth * 0.72), bodyW - 420));
                    const minH = 185;
                    const maxH = Math.max(230, bodyH - 190);
                    const effMinW = Math.max(minW, Math.round((minH - bottomBarH) * aspect));
                    const effMaxW = Math.max(effMinW, Math.min(maxW, Math.round((maxH - bottomBarH) * aspect)));
                    const targetW = Math.max(effMinW, Math.min(effMaxW, Math.round(customCockpitSize.w)));
                    let targetH = Math.round(targetW / aspect) + bottomBarH;
                    if (targetH > maxH) {
                        targetH = maxH;
                    }
                    customCockpitSize = { w: targetW, h: targetH, free: false };
                    try {
                        localStorage.setItem('pyxis_telemetry_player_size', JSON.stringify(customCockpitSize));
                    } catch (err) {}
                }
            }

            function onCockpitResetComplete(finalW, finalH) {
                if (customCockpitSize) {
                    customCockpitSize = { w: finalW, h: finalH, free: false };
                    try {
                        localStorage.setItem('pyxis_telemetry_player_size', JSON.stringify(customCockpitSize));
                    } catch (err) {}
                }
                syncCockpitVideoLayout();
                renderMainChart();
                renderMinimap();
            }

            function refreshTheme() {
                setStatusUI(lastStatusState);
                renderAllPreviewerHeatmaps();
                updateCockpitKPIs();
                if (isOpen) {
                    renderMainChart();
                    renderMinimap();
                }
            }

            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupTelemetryDomEvents);
            } else {
                setupTelemetryDomEvents();
            }

            window.PyxisTelemetry = {
                open: open,
                close: close,
                rescan: rescan,
                clearData: clearData,
                resetView: resetView,
                toggleMetric: toggleMetric,
                setMetricScale: setMetricScale,
                applyPersistedConfig: applyPersistedConfig,
                syncCockpitVideoLayout: syncCockpitVideoLayout,
                getCockpitAspectRatio: getCockpitAspectRatio,
                getCustomCockpitSize: () => customCockpitSize,
                setCustomCockpitSize: (s) => { customCockpitSize = s; },
                resetCockpitSizeToAspect: resetCockpitSizeToAspect,
                onCockpitResetComplete: onCockpitResetComplete,
                renderChartsLight: () => { renderMainChart(); renderMinimap(); },
                triggerFromPreviewer: triggerFromPreviewer,
                renderPreviewerHeatmap: renderPreviewerHeatmap,
                renderAllPreviewerHeatmaps: renderAllPreviewerHeatmaps,
                refreshTheme: refreshTheme,
                getFrameAtRatio: getFrameAtRatio,
                get isOpen() { return isOpen; },
                get lastData() { return lastTelemetryData; }
            };
        })();
