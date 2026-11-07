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
 * @file system_nodes.js
 * @description UI setups and geometry calculators for System category nodes.
 * @module PyxisSystemNodes
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function getNodePreviewAspectRatio(node) {
            if (node) {
                const nodeIdStr = String(node.id !== undefined ? node.id : "");
                const p = (nodeIdStr && window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) 
                    ? window.PyxisNodePlayerManager.activePlayers[nodeIdStr] 
                    : null;

                if (p && p.art && p.art.template && p.art.template.$video) {
                    const vid = p.art.template.$video;
                    const curSrc = (node.properties && node.properties.preview_source) || "base";
                    const pInfo = (curSrc === "aegisub" && window.PyxisPreviewConfigAegi) 
                        ? window.PyxisPreviewConfigAegi 
                        : ((curSrc === "base" && window.PyxisPreviewConfigBase) ? window.PyxisPreviewConfigBase : window.PyxisPreviewConfig) || {};
                    const hasRealVideo = Boolean(pInfo && pInfo.real_video_file && vid.videoWidth > 0 && vid.videoHeight > 0);
                    if (hasRealVideo) {
                        const probedDar = (pInfo.media_meta && Number(pInfo.media_meta.display_aspect_ratio) > 0)
                            ? Number(pInfo.media_meta.display_aspect_ratio)
                            : 0;
                        const vidAspect = probedDar > 0 ? probedDar : (vid.videoWidth / vid.videoHeight);
                        node.preview_aspect_ratio = vidAspect;
                        if (node.properties) node.properties.preview_aspect_ratio = vidAspect;
                        return vidAspect;
                    }
                }

                if (node.preview_aspect_ratio && !isNaN(node.preview_aspect_ratio) && node.preview_aspect_ratio > 0) {
                    return node.preview_aspect_ratio;
                }
                if (node.properties && node.properties.preview_aspect_ratio && !isNaN(node.properties.preview_aspect_ratio) && node.properties.preview_aspect_ratio > 0) {
                    node.preview_aspect_ratio = node.properties.preview_aspect_ratio;
                    return node.properties.preview_aspect_ratio;
                }

                const curSrc = (node.properties && node.properties.preview_source) || "base";
                if (curSrc === "base" && window.PyxisPreviewConfigBase && window.PyxisPreviewConfigBase.aspect_ratio) {
                    return window.PyxisPreviewConfigBase.aspect_ratio;
                }
                if (curSrc === "aegisub" && window.PyxisPreviewConfigAegi && window.PyxisPreviewConfigAegi.aspect_ratio) {
                    return window.PyxisPreviewConfigAegi.aspect_ratio;
                }
            }

            if (window.PyxisPreviewConfigBase && window.PyxisPreviewConfigBase.aspect_ratio) {
                return window.PyxisPreviewConfigBase.aspect_ratio;
            }
            if (window.PyxisPreviewConfig && window.PyxisPreviewConfig.aspect_ratio && !isNaN(window.PyxisPreviewConfig.aspect_ratio) && window.PyxisPreviewConfig.aspect_ratio > 0) {
                return window.PyxisPreviewConfig.aspect_ratio;
            }

            return 16 / 9;
        }

        function getDynamicMinPreviewWidth(aspect) {
            let a = aspect;
            if (!a || isNaN(a) || a <= 0) {
                a = getNodePreviewAspectRatio(null);
            }
            if (a < 0.75) {
                return 365;
            } else if (a < 1.15) {
                return 380;
            } else if (a < 1.5) {
                return 420;
            } else {
                return 440;
            }
        }

        function calculatePrevisualizadorNodeHeight(w, customAspect) {
            const sideMargin = 10;
            const topOffset = 46;
            const bottomMargin = 10;
            const controlsHeight = 68;
            
            let aspect = customAspect;
            if (!aspect || isNaN(aspect) || aspect <= 0) {
                aspect = getNodePreviewAspectRatio(null);
            }

            const playerW = Math.max(100, w - (sideMargin * 2));
            const videoH = Math.round(playerW / aspect);
            const wrapperH = videoH + controlsHeight;
            return wrapperH + topOffset + bottomMargin;
        }

        function setupPreviewerNode(node) {
            if (!node.properties) node.properties = {};
            if (node.properties.output_ids === undefined) node.properties.output_ids = "";
            if (node.properties.preview_source === undefined) node.properties.preview_source = "base";
            if (node.properties.render_mode !== "mpv" && node.properties.render_mode !== "typesetting") {
                node.properties.render_mode = "typesetting";
            }

            node.widgets_up = true;

            if (!node.inputs || node.inputs.length === 0) {
                node.inputs = [{ name: "Output", type: "data", multiple: true, label: " ", pos: [10, 23] }];
            } else {
                while (node.inputs.length > 1) {
                    node.removeInput(node.inputs.length - 1);
                }
                node.inputs[0].name = "Output";
                node.inputs[0].type = "data";
                node.inputs[0].multiple = true;
                node.inputs[0].label = " ";
                node.inputs[0].pos = [10, 23];
            }

            node.widgets = [];
            let curVal = String(node.properties.output_ids !== undefined ? node.properties.output_ids : "");
            const w = node.addWidget("text", "Output IDs", curVal, function(val) {
                const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                node.properties.output_ids = cleanVal;
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            });
            w.property = "output_ids";
            w.last_y = 14;
            w.y = 14;
            setupSingleLineTextWidget(node, w, "Output IDs", "output_ids");

            node.resizable = true;
            if (!node.flags) node.flags = {};
            node.flags.resizable = true;

            node.computeSize = function() {
                let text_req_w = 0;
                const props = this.properties || node.properties || {};
                const w = (this.widgets && this.widgets.length > 0) ? this.widgets.find(w => w && (w.name === "Output IDs" || w.property === "output_ids")) : null;
                const val = w ? String(w.value !== undefined ? w.value : (props.output_ids || "")) : String(props.output_ids !== undefined ? props.output_ids : "");
                if (val.length > 0) {
                    text_req_w = getExactTextWidth(val, "bold 11px Consolas, monospace");
                }
                const curAspect = getNodePreviewAspectRatio(this);
                const dynMinW = getDynamicMinPreviewWidth(curAspect);
                let boxW = 80;
                if (w && typeof getInlineBoxWidth === 'function') {
                    boxW = getInlineBoxWidth(this, w, "Output IDs", "output_ids", 300);
                } else {
                    boxW = Math.max(76, Math.ceil(text_req_w + 24));
                }
                const pMgr = window.PyxisNodePlayerManager;
                const p = (pMgr && pMgr.activePlayers && this.id !== undefined) ? pMgr.activePlayers[String(this.id)] : null;
                const isPinned = Boolean((p && p.isPinned) || (props && props.is_pinned));
                if (isPinned) {
                    const compactPinnedW = Math.max(270, 22 + boxW + 8 + 164 + 10);
                    return [compactPinnedW, 54];
                }
                const minReqW = Math.max(dynMinW, 22 + boxW + 205);
                const isZoomed = Boolean((p && p.transformState && p.transformState.isCustom) || (props && props.viewport_custom));
                const effectiveW = minReqW;
                const effectiveH = isZoomed ? 140 : calculatePrevisualizadorNodeHeight(effectiveW, curAspect);
                return [effectiveW, effectiveH];
            };

            const curAspect = getNodePreviewAspectRatio(node);
            const dynMinW = getDynamicMinPreviewWidth(curAspect);
            const curSrc = (node.properties && node.properties.preview_source) || "base";
            const cfg = (curSrc === "aegisub" && window.PyxisPreviewConfigAegi)
                ? window.PyxisPreviewConfigAegi
                : (window.PyxisPreviewConfigBase || window.PyxisPreviewConfig);

            let initialW = 520;
            if (cfg && cfg.res_x && cfg.res_x > 0) {
                const scaled = Math.round(cfg.res_x * 0.50);
                initialW = Math.max(dynMinW, Math.min(1280, scaled));
            }
            if (node.properties && node.properties.previewer_width) {
                initialW = Math.max(dynMinW, Number(node.properties.previewer_width));
            } else if (node.size && node.size[0] && node.size[0] > dynMinW && node.size[0] !== 520) {
                initialW = node.size[0];
            }
            const isPinnedInit = Boolean((node.properties && node.properties.is_pinned) || (node.flags && node.flags.pinned));
            const isCustomZoomInit = Boolean(node.properties && node.properties.viewport_custom);
            let initialH;
            if (isPinnedInit) {
                let text_req_w = 0;
                const props = node.properties || {};
                const val = String(props.output_ids !== undefined ? props.output_ids : "");
                if (val.length > 0) {
                    text_req_w = getExactTextWidth(val, "bold 11px Consolas, monospace");
                }
                let boxW = 80;
                if (node.widgets && node.widgets.length > 0 && typeof getInlineBoxWidth === 'function') {
                    const wOut = node.widgets.find(w => w && (w.name === "Output IDs" || w.property === "output_ids"));
                    if (wOut) boxW = getInlineBoxWidth(node, wOut, "Output IDs", "output_ids", 300);
                } else {
                    boxW = Math.max(76, Math.ceil(text_req_w + 24));
                }
                initialH = 54;
                const compactW = Math.max(270, 22 + boxW + 8 + 164 + 10);
                const savedPinnedW = (props && props.pinned_width) ? Number(props.pinned_width) : 0;
                initialW = (savedPinnedW >= compactW) ? savedPinnedW : compactW;
            } else if (isCustomZoomInit && node.properties && node.properties.previewer_height && Number(node.properties.previewer_height) >= 140) {
                initialH = Number(node.properties.previewer_height);
            } else {
                initialH = calculatePrevisualizadorNodeHeight(initialW, curAspect);
            }
            node.size = [initialW, initialH];

            node.onResize = function(size) {
                const curAspect = getNodePreviewAspectRatio(this);
                const dynMinW = getDynamicMinPreviewWidth(curAspect);
                const minSz = (typeof this.computeSize === 'function') ? this.computeSize() : [dynMinW, 0];
                const reqMinW = minSz ? minSz[0] : dynMinW;
                const pMgr = window.PyxisNodePlayerManager;
                const p = (pMgr && pMgr.activePlayers && this.id !== undefined) ? pMgr.activePlayers[String(this.id)] : null;
                if (p && typeof p.cancelResetAnimation === 'function') {
                    p.cancelResetAnimation();
                }
                const isPinned = Boolean((p && p.isPinned) || (this.properties && this.properties.is_pinned));
                if (isPinned) {
                    const minSz = (typeof this.computeSize === 'function') ? this.computeSize() : [270, 54];
                    const minW = minSz ? minSz[0] : 270;
                    size[0] = Math.max(minW, Math.round(size[0]));
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
                    return;
                }
                const isZoomed = Boolean(
                    (p && p.transformState && p.transformState.isCustom) ||
                    (this.properties && this.properties.viewport_custom)
                );

                let w, h;
                if (isZoomed) {
                    w = Math.max(reqMinW, Math.round(size[0]));
                    h = Math.max(140, Math.round(size[1]));
                } else {
                    // Retracted zoom (locked aspect ratio):
                    // Direct 2D orthogonal projection of the mouse vector (size[0], size[1])
                    // onto the aspect ratio ray. Both axes (X and Y) contribute smoothly
                    // and simultaneously to the resizing in proportion to mouse movement.
                    const mouseEffX = Math.max(0, size[0] - 20);
                    const mouseEffY = Math.max(0, size[1] - 124);
                    const A = curAspect;
                    const xProj = (A * (A * mouseEffX + mouseEffY)) / (A * A + 1);
                    w = Math.max(reqMinW, Math.round(20 + xProj));
                    h = calculatePrevisualizadorNodeHeight(w, curAspect);
                }

                size[0] = w;
                size[1] = h;
                this.size[0] = w;
                this.size[1] = h;
                this.lastW = w;
                this.lastH = h;

                if (!this.properties) this.properties = {};
                this.properties.previewer_width = w;
                this.properties.previewer_height = h;

                if (p) {
                    p.isResizing = true;
                    if (p.wrapper && !p.isPinned) {
                        p.wrapper.style.width = Math.max(100, w - 20) + 'px';
                        p.wrapper.style.height = Math.max(100, h - 56) + 'px';
                    }
                }
                if (window.__pyxis_schedule_save) {
                    window.__pyxis_schedule_save(50);
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (!this.properties) this.properties = {};
                this.properties.render_mode = (this.properties.render_mode === "mpv") ? "mpv" : "typesetting";
                if (this.id !== undefined && window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.updateRenderModeButtonUI === "function") {
                    window.PyxisNodePlayerManager.updateRenderModeButtonUI(String(this.id), this.properties.render_mode);
                }
                if (this.properties && this.properties.preview_aspect_ratio) {
                    this.preview_aspect_ratio = this.properties.preview_aspect_ratio;
                }
                const isPinned = Boolean((this.properties && this.properties.is_pinned) || (info && info.flags && info.flags.pinned));
                if (isPinned) {
                    const minSz = (typeof this.computeSize === 'function') ? this.computeSize() : [270, 54];
                    const minW = minSz ? minSz[0] : 270;
                    const savedPinnedW = (this.properties && this.properties.pinned_width)
                        ? Number(this.properties.pinned_width)
                        : ((info && Array.isArray(info.size) && info.size[0] > 0 && info.size[1] <= 60) ? Number(info.size[0]) : minW);
                    const w = (savedPinnedW >= minW) ? savedPinnedW : minW;
                    this.size = [w, 54];
                    this.lastW = w;
                    this.lastH = 54;
                    return;
                }
                const isCustomZoom = Boolean(this.properties && this.properties.viewport_custom);
                const curAspect = getNodePreviewAspectRatio(this);
                const dynMinW = getDynamicMinPreviewWidth(curAspect);
                let w = (this.properties && this.properties.previewer_width)
                    ? Math.max(dynMinW, Number(this.properties.previewer_width))
                    : ((info && Array.isArray(info.size) && info.size[0] > 0) ? Math.max(dynMinW, Number(info.size[0])) : 520);
                
                let h;
                if (isCustomZoom && this.properties && this.properties.previewer_height && Number(this.properties.previewer_height) >= 140) {
                    h = Number(this.properties.previewer_height);
                } else if (isCustomZoom && info && Array.isArray(info.size) && Number(info.size[1]) >= 140) {
                    h = Number(info.size[1]);
                } else {
                    h = calculatePrevisualizadorNodeHeight(w, curAspect);
                }
                this.size = [w, h];
                this.lastW = w;
                this.lastH = h;
                if (!this.properties) this.properties = {};
                this.properties.previewer_width = w;
                this.properties.previewer_height = h;
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                if (this.widgets && this.widgets.length >= 1) {
                    this.widgets[0].y = 14; this.widgets[0].last_y = 14;
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].label = " ";
                    this.inputs[0].pos = [10, 23];
                }
            };
        }


        function setupOutputNode(node) {
            if (!node.properties) node.properties = {};
            if (!node.properties.apply_to) node.properties.apply_to = "Sel. Lines";
            if (node.properties.queue_id === undefined) node.properties.queue_id = "";
            if (node.properties.queue_order === undefined) node.properties.queue_order = "";
            if (node.properties.origin_align === undefined) node.properties.origin_align = 5;

            node.widgets_up = true;
            node._hovered_align_point = null;

            const ALIGN_POINTS = {
                7: { col: 0, row: 0, name: "Top-Left" },
                8: { col: 1, row: 0, name: "Top-Center" },
                9: { col: 2, row: 0, name: "Top-Right" },
                4: { col: 0, row: 1, name: "Mid-Left" },
                5: { col: 1, row: 1, name: "Center" },
                6: { col: 2, row: 1, name: "Mid-Right" },
                1: { col: 0, row: 2, name: "Bottom-Left" },
                2: { col: 1, row: 2, name: "Bottom-Center" },
                3: { col: 2, row: 2, name: "Bottom-Right" }
            };

            function getGridPointCoords(n, alignNum) {
                const info = ALIGN_POINTS[alignNum] || ALIGN_POINTS[5];
                const cx = (n.size[0] || 200) - 55;
                const cy = 82;
                const sp = 33;
                return {
                    x: cx + (info.col - 1) * sp,
                    y: cy + (info.row - 1) * sp,
                    align: alignNum,
                    name: info.name
                };
            }

            const reqInputs = [
                { name: "Loop / Domain", type: "loop", label: "Loop / Domain" },
                { name: "Layer", type: "data", label: "Layer" },
                { name: "Start Time", type: "data", label: "Start Time" },
                { name: "End Time", type: "data", label: "End Time" },
                { name: "Tags", type: "data", label: "Tags" },
                { name: "Return", type: "data", label: "Return" },
                { name: "Queue ID", type: "data", label: " " },
                { name: "Queue Order", type: "data", label: " " }
            ];

            node.computeSize = function() {
                let base_w = 200;
                let text_req_w = 0;
                const props = this.properties || node.properties || {};
                ["queue_id", "queue_order"].forEach(k => {
                    const val = String(props[k] || "");
                    if (val.length > 0) {
                        const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                        if (tw > text_req_w) text_req_w = tw;
                    }
                });
                const rightReserve = getNodeRightReserve(this);
                const boxW = Math.max(75, Math.ceil(text_req_w + 28));
                return [Math.max(base_w, 22 + boxW + rightReserve), 214];
            };

            function updateSalidaInputs() {
                if (!node.inputs) node.inputs = [];
                reqInputs.forEach((req, idx) => {
                    if (idx >= node.inputs.length) {
                        node.addInput(req.name, req.type);
                    }
                    const inp = node.inputs[idx];
                    inp.name = req.name;
                    inp.type = req.type;
                    inp.label = req.label;
                });

                node.widgets = [];

                const curQueueId = String(node.properties.queue_id !== undefined ? node.properties.queue_id : "");
                const w1 = node.addWidget("text", "Queue ID", curQueueId, function(val) {
                    const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                    node.properties.queue_id = cleanVal;
                    if (node.computeSize) {
                        node.size = node.computeSize();
                    }
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                });
                w1.property = "queue_id";
                w1.last_y = 145;
                w1.y = 145;
                setupSingleLineTextWidget(node, w1, "Queue ID", "queue_id");

                const curQueueOrder = String(node.properties.queue_order !== undefined ? node.properties.queue_order : "");
                const w2 = node.addWidget("text", "Queue Order", curQueueOrder, function(val) {
                    const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                    node.properties.queue_order = cleanVal;
                    if (node.computeSize) {
                        node.size = node.computeSize();
                    }
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                });
                w2.property = "queue_order";
                w2.last_y = 168;
                w2.y = 168;
                setupSingleLineTextWidget(node, w2, "Queue Order", "queue_order");

                if (node.inputs.length >= 8) {
                    node.inputs[6].label = " ";
                    node.inputs[6].pos = [10, 154];
                    node.inputs[7].label = " ";
                    node.inputs[7].pos = [10, 177];
                }

                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                if (this.widgets && this.widgets.length >= 2) {
                    this.widgets[0].y = 145;
                    this.widgets[0].last_y = 145;
                    this.widgets[1].y = 168;
                    this.widgets[1].last_y = 168;
                }

                if (this.inputs && this.inputs.length >= 8) {
                    this.inputs[6].label = " ";
                    this.inputs[6].pos = [10, 154];
                    this.inputs[7].label = " ";
                    this.inputs[7].pos = [10, 177];
                }

                ctx.save();

                const applyTo = String(this.properties.apply_to || "Sel. Lines");
                let applyText = window.PyxisI18n ? (window.PyxisI18n.getOutputBadgeText ? window.PyxisI18n.getOutputBadgeText(applyTo) : window.PyxisI18n.getSalidaBadgeText(applyTo)) : "SEL.";
                if (!window.PyxisI18n) {
                    if (applyTo === "Style Lines") applyText = "STYLE";
                    else if (applyTo === "All Lines") applyText = "ALL";
                    else if (applyTo === "Sel. Lines") applyText = "SEL.";
                    else applyText = applyTo.toUpperCase();
                }

                ctx.font = "bold 10px monospace";
                const applyTextW = ctx.measureText(applyText).width;
                const applyBadgeW = Math.max(54, applyTextW + 14);
                const badgeH = 20;
                const applyBadgeX = this.size[0] - applyBadgeW - 8;
                const badgeY = -25;

                this._apply_badge_bounds = { x: applyBadgeX, y: badgeY, w: applyBadgeW, h: badgeH };

                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = "#0ea5e9";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(applyBadgeX, badgeY, applyBadgeW, badgeH, 10);
                else ctx.rect(applyBadgeX, badgeY, applyBadgeW, badgeH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = "#38bdf8";
                ctx.textAlign = "center";
                ctx.fillText(applyText, applyBadgeX + applyBadgeW / 2, badgeY + 14);

                const cx = (this.size[0] || 200) - 55;
                const cy = 82;
                const sp = 33;

                ctx.save();
                ctx.strokeStyle = "rgba(255, 255, 255, 0.16)";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                for (let r = 0; r < 3; r++) {
                    const y = cy + (r - 1) * sp;
                    ctx.moveTo(cx - sp, y);
                    ctx.lineTo(cx + sp, y);
                }
                for (let c = 0; c < 3; c++) {
                    const x = cx + (c - 1) * sp;
                    ctx.moveTo(x, cy - sp);
                    ctx.lineTo(x, cy + sp);
                }
                ctx.stroke();
                ctx.restore();

                const hoveredAlign = this._hovered_align_point;
                for (let a = 1; a <= 9; a++) {
                    const pt = getGridPointCoords(this, a);
                    ctx.save();
                    ctx.beginPath();
                    if (hoveredAlign === a) {
                        ctx.arc(pt.x, pt.y, 5.0, 0, Math.PI * 2);
                        ctx.fillStyle = "#FFFFFF";
                        ctx.shadowColor = "rgba(16, 185, 129, 0.95)";
                        ctx.shadowBlur = 10;
                        ctx.fill();
                    } else {
                        ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2);
                        ctx.fillStyle = "rgba(156, 163, 175, 0.65)";
                        ctx.shadowBlur = 0;
                        ctx.fill();
                    }
                    ctx.restore();
                }

                const activeAlign = Number(this.properties.origin_align || 5);
                const targetPt = getGridPointCoords(this, activeAlign);

                if (this._anim_ball_x === undefined || this._anim_ball_y === undefined || this._last_cx !== cx || this._last_cy !== cy) {
                    this._anim_ball_x = targetPt.x;
                    this._anim_ball_y = targetPt.y;
                    this._last_cx = cx;
                    this._last_cy = cy;
                } else {
                    const dx = targetPt.x - this._anim_ball_x;
                    const dy = targetPt.y - this._anim_ball_y;
                    if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
                        this._anim_ball_x += dx * 0.28;
                        this._anim_ball_y += dy * 0.28;
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                    } else {
                        this._anim_ball_x = targetPt.x;
                        this._anim_ball_y = targetPt.y;
                    }
                }

                const bx = this._anim_ball_x;
                const by = this._anim_ball_y;

                ctx.save();
                ctx.shadowColor = "transparent";
                ctx.shadowBlur = 0;
                const glowGrad = ctx.createRadialGradient(bx, by, 0, bx, by, 18);
                glowGrad.addColorStop(0, "rgba(34, 197, 94, 0.70)");
                glowGrad.addColorStop(0.40, "rgba(16, 185, 129, 0.30)");
                glowGrad.addColorStop(1, "rgba(16, 185, 129, 0)");
                ctx.fillStyle = glowGrad;
                ctx.beginPath();
                ctx.arc(bx, by, 18, 0, Math.PI * 2);
                ctx.fill();

                ctx.beginPath();
                ctx.arc(bx, by, 6.8, 0, Math.PI * 2);
                ctx.fillStyle = "#10B981";
                ctx.fill();

                ctx.lineWidth = 1.8;
                ctx.strokeStyle = "#F3F4F6";
                ctx.stroke();
                ctx.restore();

                ctx.save();
                ctx.font = "bold 10px sans-serif";
                ctx.fillStyle = "rgba(156, 163, 175, 0.75)";
                ctx.textAlign = "center";
                var alignLabel = window.PyxisI18n ? window.PyxisI18n.getAlignTitle() : "Align";
                ctx.fillText(alignLabel, cx, cy + sp + 15);
                ctx.restore();

                ctx.restore();
            };

            const oldMouseMove = node.onMouseMove;
            node.onMouseMove = function(e, pos, canvas) {
                if (oldMouseMove && oldMouseMove.call(this, e, pos, canvas)) return true;
                if (this.flags && this.flags.collapsed) return;

                let closestAlign = null;
                let minDist = 15;
                for (let a = 1; a <= 9; a++) {
                    const pt = getGridPointCoords(this, a);
                    const dist = Math.hypot(pos[0] - pt.x, pos[1] - pt.y);
                    if (dist < minDist) {
                        minDist = dist;
                        closestAlign = a;
                    }
                }

                if (this._hovered_align_point !== closestAlign) {
                    this._hovered_align_point = closestAlign;
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                }
            };

            const oldMouseLeave = node.onMouseLeave;
            node.onMouseLeave = function(e) {
                if (oldMouseLeave) oldMouseLeave.call(this, e);
                if (this._hovered_align_point !== null) {
                    this._hovered_align_point = null;
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                }
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, pos, canvas) {
                if (oldMouseDown && oldMouseDown.call(this, e, pos, canvas)) return true;

                if (this._apply_badge_bounds) {
                    const b = this._apply_badge_bounds;
                    if (pos[0] >= b.x && pos[0] <= b.x + b.w &&
                        pos[1] >= b.y && pos[1] <= b.y + b.h) {

                        const modes = ["Sel. Lines", "Style Lines", "All Lines"];
                        let idx = modes.indexOf(this.properties.apply_to);
                        if (idx === -1) idx = 0;
                        const nextIdx = (idx + 1) % modes.length;
                        this.properties.apply_to = modes[nextIdx];

                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        return true;
                    }
                }

                let closestClick = null;
                let minClickDist = 16;
                for (let a = 1; a <= 9; a++) {
                    const pt = getGridPointCoords(this, a);
                    const dist = Math.hypot(pos[0] - pt.x, pos[1] - pt.y);
                    if (dist < minClickDist) {
                        minClickDist = dist;
                        closestClick = a;
                    }
                }

                if (closestClick !== null) {
                    if (this.properties.origin_align !== closestClick) {
                        this.properties.origin_align = closestClick;
                        if (window.PyxisUndoManager && typeof window.PyxisUndoManager.recordState === "function") {
                            window.PyxisUndoManager.recordState("change_origin_align");
                        }
                        if (this.graph) this.graph.change();
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    }
                    return true;
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateSalidaInputs();
            };

            updateSalidaInputs();
        }

        window.setupSalidaNode = setupOutputNode;
        window.setupOutputNode = setupOutputNode;
        window.setupPrevisualizadorNode = setupPreviewerNode;
        window.setupPreviewerNode = setupPreviewerNode;


