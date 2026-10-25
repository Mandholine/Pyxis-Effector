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
 * @file nodes_common.js
 * @description Core node infrastructure, dynamic mode routing, inline text widgets, and LiteGraph node registration.
 * @module PyxisNodesCommon
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function isFilePathPropOrVal(propKey, val) {
            if (!val || typeof val !== "string") return false;
            const p = String(propKey || "").toLowerCase();
            if (p === "text" || p === "texto" || p === "valor" || p === "value" || p === "formato" || p === "format" || p === "key" || p === "default" || p === "tag" || p === "variables" || p === "code" || p.startsWith("in")) {
                return false;
            }
            if (p === "image_path" || p === "audio_path" || p === "file_path" || p === "path" || p.includes("ruta")) {
                return true;
            }
            const str = val.trim();
            if (/^[a-zA-Z]:[\\\/]/.test(str) || /^\\\\[^\\\/]+[\\\/][^\\\/]+/.test(str) || str.startsWith("./") || str.startsWith("../")) {
                return true;
            }
            if ((str.includes("/") || str.includes("\\")) && /\.(png|jpg|jpeg|gif|webp|bmp|wav|mp3|ogg|flac|aac|ass|srt|txt|py|lua|json)$/i.test(str)) {
                return true;
            }
            return false;
        }

        function isCompactTextPropOrVal(propKey, val) {
            const p = String(propKey || "").toLowerCase();
            if (p === "formato" || p === "format" || p.includes("format")) return false;
            if (p === "shape" || p === "forma" || p === "frames" || p === "drawing" || p === "code" || p === "code_val" || p === "shp" || p === "shp_val" || p.includes("drawing") || p.includes("dibujo") || (p.includes("shape") && !p.includes("format"))) {
                return true;
            }
            if (!val || typeof val !== "string") return false;
            const str = val.trim();
            if (/^m\s+[-?\d]/i.test(str) || /^m\s*[-?\d]/i.test(str) || str.startsWith("m ") || str.startsWith("m-") || (str.includes(" b ") && str.startsWith("m"))) {
                return true;
            }
            return false;
        }

        let __pyxis_measure_canvas_ctx = null;
        function getExactTextWidth(text, font) {
            if (!text) return 0;
            try {
                if (!__pyxis_measure_canvas_ctx) {
                    const canvas = document.createElement("canvas");
                    __pyxis_measure_canvas_ctx = canvas.getContext("2d");
                }
                if (__pyxis_measure_canvas_ctx) {
                    let f = font || "bold 11px Consolas, monospace";
                    if (f === "bold 11px monospace") f = "bold 11px Consolas, monospace";
                    __pyxis_measure_canvas_ctx.font = f;
                    return __pyxis_measure_canvas_ctx.measureText(String(text)).width;
                }
            } catch(e) {}
            return String(text).length * 7.2;
        }

        function formatPathForDisplay(val, maxPxWidth, font) {
            if (!val) return "";
            const fontStr = font || "bold 11px monospace";
            const availableWidth = maxPxWidth || 100;
            if (getExactTextWidth(val, fontStr) <= availableWidth) return val;

            const parts = String(val).replace(/\\/g, "/").split("/");
            const filename = parts[parts.length - 1] || val;
            const shortText = ".../" + filename;
            if (getExactTextWidth(shortText, fontStr) <= availableWidth) {
                return shortText;
            }
            let sub = filename;
            while (sub.length > 4 && getExactTextWidth("..." + sub, fontStr) > availableWidth) {
                sub = sub.substring(1);
            }
            return "..." + sub;
        }

        function getNodeRightReserve(node) {
            if (!node) return 20;
            const isSalidaNode = !!(node.title === "Output" || (node.type && String(node.type).includes("Output")));
            if (isSalidaNode) {
                return 95;
            }
            const isPreviewNode = !!((node.type && (String(node.type).toLowerCase().includes("preview") || String(node.type).toLowerCase().includes("previsualizador"))) || (node.title && String(node.title).toLowerCase().includes("previsualizador")));
            if (isPreviewNode) {
                return 155;
            }
            let max_out_w = 0;
            const outputs = node.outputs || [];
            outputs.forEach(out => {
                if (out && (out.name || out.label)) {
                    let outText = out.label != null ? out.label : out.name;
                    if (outText && window.PyxisI18n && outText !== " ") {
                        outText = window.PyxisI18n.translateSlot(outText);
                    }
                    const ow = getExactTextWidth(outText, "11px Arial, sans-serif");
                    if (ow > max_out_w) max_out_w = ow;
                }
            });
            return max_out_w > 0 ? Math.ceil(max_out_w + 38) : 20;
        }

        function getInlineBoxWidth(node, widget, titleName, propertyName, width) {
            if (widget && widget._boxW !== undefined) {
                return widget._boxW;
            }
            const propKey = propertyName || (widget ? widget.property : null);
            const curVal = String((node && node.properties && propKey && node.properties[propKey] !== undefined)
                ? node.properties[propKey]
                : (widget && widget.value !== undefined ? widget.value : ""));
            const nodeW = (node && node.size && node.size[0]) ? node.size[0] : (width || 200);

            const isFormatDinamico = node && (node.type === "Dynamic Format" || (node.title && String(node.title).includes("Format Din")));
            if (isFormatDinamico) {
                const rightReserve = (typeof getNodeRightReserve === "function") ? getNodeRightReserve(node) : 24;
                return Math.max(80, nodeW - 24 - rightReserve);
            }

            const isSalidaNode = !!(node && (node.title === "Output" || (node.type && String(node.type).includes("Output"))));
            const margin = isFormatDinamico ? 12 : 22;
            const rightReserve = getNodeRightReserve(node);

            const rawDisp = (widget ? widget.name : titleName) || "";
            let dispText = curVal.length > 0 ? curVal : ((window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot(rawDisp) : rawDisp);
            const isPathProp = isFilePathPropOrVal(propKey, curVal);
            const isCompactProp = !isFormatDinamico && isCompactTextPropOrVal(propKey, curVal);
            if (curVal.length > 0 && isPathProp) {
                const parts = curVal.replace(/\\/g, "/").split("/");
                dispText = ".../" + (parts[parts.length - 1] || curVal);
            } else if (curVal.length > 0 && isCompactProp) {
                dispText = curVal.length > 10 ? (curVal.substring(0, 10) + "...") : curVal;
            }
            
            let textWidth = getExactTextWidth(dispText, "bold 11px Consolas, monospace");
            if (isPathProp || isCompactProp) {
                textWidth = Math.min(65, textWidth);
            }

            const minBoxW = isSalidaNode ? 75 : 65;
            const calcW = Math.max(minBoxW, Math.ceil(textWidth + 28));
            const isImgNode = !!(node && (node.type === "IMG to Shape" || node.type === "Shape/IMG to Shape" || node.type === "IMG to pixels" || node.type === "Functions/IMG to pixels" || node.type === "Animation" || node.type === "Functions/Animation" || (node.title && (node.title.includes("IMG to") || node.title.includes("Animation")))));
            const cardReserve = isImgNode ? (rightReserve + 150 + 35) : rightReserve;
            const maxW = Math.max(minBoxW, nodeW - margin - cardReserve);
            return Math.min(maxW, calcW);
        }

        function openInlineSingleLineEditor(node, widget, propertyName, titleName, event) {
            const existing = document.getElementById("pyxis-inline-text-editor");
            if (existing) {
                if (typeof existing._saveAndClose === "function") existing._saveAndClose();
                else existing.remove();
            }

            const canvas = LGraphCanvas.active_canvas;
            if (!canvas || !canvas.canvas) return;

            const propKey = propertyName || widget.property;
            const curVal = String((node.properties && propKey && node.properties[propKey] !== undefined)
                ? node.properties[propKey]
                : (widget.value !== undefined ? widget.value : ""));

            const drawY = (widget.last_y !== undefined) ? widget.last_y : ((widget.y !== undefined) ? widget.y : 11);
            const isFormatDinamico = node && (node.type === "Dynamic Format" || (node.title && String(node.title).includes("Format Din")));
            const margin = (widget && widget._boxX !== undefined) ? widget._boxX : (isFormatDinamico ? 12 : 22);
            const isSalidaNode = !!(node && (node.title === "Output" || (node.type && String(node.type).includes("Output"))));
            const textPadLeft = (widget && widget._boxX !== undefined) ? 6 : (isSalidaNode ? 6 : (isFormatDinamico ? 6 : 8));

            const rect = canvas.canvas.getBoundingClientRect();
            const scale = canvas.ds ? canvas.ds.scale : 1.0;
            const offset = canvas.ds ? canvas.ds.offset : [0, 0];

            const wWidth = getInlineBoxWidth(node, widget, titleName, propertyName);
            const wHeight = 18;

            const screenX = rect.left + (node.pos[0] + margin + offset[0]) * scale;
            const screenY = rect.top + (node.pos[1] + drawY + offset[1]) * scale;
            const screenW = wWidth * scale;
            const screenH = wHeight * scale;

            if (widget) widget._is_inline_editing = true;
            if (canvas.draw) canvas.draw(true, true);

            const inputEl = document.createElement("input");
            inputEl.type = "text";
            inputEl.id = "pyxis-inline-text-editor";
            inputEl.name = "pyxis-inline-text-editor";
            inputEl.spellcheck = false;
            inputEl.autocomplete = "off";
            inputEl.autocorrect = "off";
            inputEl.autocapitalize = "off";
            inputEl.value = curVal;
            const rawPlaceholder = (widget && widget._crossCol) ? "0" : (widget.name || titleName || "");
            inputEl.placeholder = (widget && widget._crossCol) ? "0" : ((window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot(rawPlaceholder) : rawPlaceholder);
            
            inputEl.style.position = "fixed";
            inputEl.style.left = screenX + "px";
            inputEl.style.top = screenY + "px";
            inputEl.style.width = screenW + "px";
            inputEl.style.height = screenH + "px";
            inputEl.style.boxSizing = "border-box";
            inputEl.style.borderRadius = (5 * scale) + "px";
            inputEl.style.background = "#12161f";
            inputEl.style.border = (1.5 * scale) + "px solid #8b5cf6";
            inputEl.style.color = "#a7f3d0";
            inputEl.style.fontFamily = "Consolas, monospace";
            inputEl.style.fontSize = (11 * scale) + "px";
            inputEl.style.fontWeight = "bold";
            inputEl.style.letterSpacing = "0px";
            inputEl.style.fontFeatureSettings = "'liga' 0, 'calt' 0";
            inputEl.style.fontVariantLigatures = "none";
            inputEl.style.webkitFontSmoothing = "antialiased";
            inputEl.style.mozOsxFontSmoothing = "grayscale";
            inputEl.style.textRendering = "optimizeLegibility";
            inputEl.style.margin = "0";
            
            const padLeftPx = Math.max(0, (textPadLeft - 1.5) * scale);
            const padRightPx = Math.max(0, 4.5 * scale);
            inputEl.style.padding = `0px ${padRightPx}px 0px ${padLeftPx}px`;
            inputEl.style.lineHeight = (screenH - 3 * scale) + "px";
            inputEl.style.zIndex = "90000";
            inputEl.style.outline = "none";
            inputEl.style.boxShadow = "0 0 10px rgba(139, 92, 246, 0.6)";

            document.body.appendChild(inputEl);
            let isMounting = true;
            setTimeout(() => {
                isMounting = false;
                inputEl.focus();
                inputEl.setSelectionRange(0, inputEl.value.length);
            }, 30);

            inputEl.oninput = function() {
                const cleanVal = String(inputEl.value || "").replace(/[\r\n]+/g, " ");
                if (node.properties && propKey) node.properties[propKey] = cleanVal;
                if (widget) widget.value = cleanVal;

                if (typeof node.computeSize === "function") {
                    const minSz = node.computeSize();
                    if (minSz && Array.isArray(minSz)) {
                        const isPreview = !!((node.type && (String(node.type).toLowerCase().includes("preview") || String(node.type).toLowerCase().includes("previsualizador"))) || (node.title && String(node.title).toLowerCase().includes("previsualizador")));
                        if (isPreview && node.size) {
                            const keepW = Math.max(node.size[0] || 0, minSz[0]);
                            const keepH = node.size[1] || 330;
                            node.size = [keepW, keepH];

                            const pMgr = window.PyxisNodePlayerManager;
                            const p = (pMgr && pMgr.activePlayers && node.id !== undefined) ? pMgr.activePlayers[String(node.id)] : null;
                            if (p) {
                                p.lastW = keepW;
                                p.lastH = keepH;
                                const unscaledW = Math.max(100, keepW - 20);
                                const unscaledH = Math.max(100, keepH - 56);
                                if (p.wrapper && !p.isPinned) {
                                    p.wrapper.style.width = unscaledW + 'px';
                                    p.wrapper.style.height = unscaledH + 'px';
                                }
                                if (p.art && typeof p.art.resize === 'function') {
                                    try { p.art.resize(); } catch (e) {}
                                }
                                if (p.jassub && typeof p.jassub.resize === 'function') {
                                    try { p.jassub.resize(); } catch (e) {}
                                }
                                if (typeof p.applyTransform === 'function') {
                                    p.applyTransform();
                                }
                            }
                        } else {
                            node.size = [minSz[0], minSz[1]];
                        }
                    }
                }

                if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                if (canvas.draw) canvas.draw(true, true);

                const newRect = canvas.canvas.getBoundingClientRect();
                const newScale = canvas.ds ? canvas.ds.scale : 1.0;
                const newOffset = canvas.ds ? canvas.ds.offset : [0, 0];
                const newW = getInlineBoxWidth(node, widget, titleName, propertyName);
                const newH = 18;

                const newScreenX = newRect.left + (node.pos[0] + margin + newOffset[0]) * newScale;
                const newScreenY = newRect.top + (node.pos[1] + drawY + newOffset[1]) * newScale;
                const newScreenW = newW * newScale;
                const newScreenH = newH * newScale;

                inputEl.style.left = newScreenX + "px";
                inputEl.style.top = newScreenY + "px";
                inputEl.style.width = newScreenW + "px";
                inputEl.style.height = newScreenH + "px";
                inputEl.style.borderRadius = (5 * newScale) + "px";
                inputEl.style.border = (1.5 * newScale) + "px solid #8b5cf6";
                inputEl.style.fontSize = (11 * newScale) + "px";
                const curPadLeftPx = Math.max(0, (textPadLeft - 1.5) * newScale);
                const curPadRightPx = Math.max(0, 4.5 * newScale);
                inputEl.style.padding = `0px ${curPadRightPx}px 0px ${curPadLeftPx}px`;
                inputEl.style.lineHeight = (newScreenH - 3 * newScale) + "px";
            };

            inputEl.onkeyup = function() {};

            function saveAndClose() {
                if (widget) delete widget._is_inline_editing;
                const cleanVal = String(inputEl.value || "").replace(/[\r\n]+/g, " ");
                if (node.properties && propKey) node.properties[propKey] = cleanVal;
                widget.value = cleanVal;
                if (typeof node.computeSize === "function") {
                    const minSz = node.computeSize();
                    if (minSz && Array.isArray(minSz)) {
                        const isPreview = !!((node.type && (String(node.type).toLowerCase().includes("preview") || String(node.type).toLowerCase().includes("previsualizador"))) || (node.title && String(node.title).toLowerCase().includes("previsualizador")));
                        if (isPreview && node.size) {
                            const keepW = Math.max(node.size[0] || 0, minSz[0]);
                            const keepH = node.size[1] || 330;
                            node.size = [keepW, keepH];

                            const pMgr = window.PyxisNodePlayerManager;
                            const p = (pMgr && pMgr.activePlayers && node.id !== undefined) ? pMgr.activePlayers[String(node.id)] : null;
                            if (p) {
                                p.lastW = keepW;
                                p.lastH = keepH;
                                const unscaledW = Math.max(100, keepW - 20);
                                const unscaledH = Math.max(100, keepH - 56);
                                if (p.wrapper && !p.isPinned) {
                                    p.wrapper.style.width = unscaledW + 'px';
                                    p.wrapper.style.height = unscaledH + 'px';
                                }
                                if (p.art && typeof p.art.resize === 'function') {
                                    try { p.art.resize(); } catch (e) {}
                                }
                                if (p.jassub && typeof p.jassub.resize === 'function') {
                                    try { p.jassub.resize(); } catch (e) {}
                                }
                                if (typeof p.applyTransform === 'function') {
                                    p.applyTransform();
                                }
                            }
                        } else {
                            node.size = [minSz[0], minSz[1]];
                        }
                    }
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                if (canvas.draw) canvas.draw(true, true);
                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("inline-text-edit");
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                inputEl.onblur = null;
                inputEl.remove();
            }
            inputEl._saveAndClose = saveAndClose;

            inputEl.onkeydown = function(e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    e.stopPropagation();
                    saveAndClose();
                } else if (e.key === "Escape") {
                    e.preventDefault();
                    e.stopPropagation();
                    if (widget) delete widget._is_inline_editing;
                    inputEl.onblur = null;
                    inputEl.remove();
                    if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                }
            };

            inputEl.onblur = function() {
                if (isMounting) {
                    inputEl.focus();
                    return;
                }
                saveAndClose();
            };
        }

        function setupSingleLineTextWidget(node, widget, titleName, propertyName) {
            if (!widget) return;

            widget.type = "custom";
            if (propertyName) widget.property = propertyName;

            widget.isPointInside = function(x, y, n) {
                const targetNode = n || node;
                const isFormatDinamico = targetNode && (targetNode.type === "Dynamic Format" || (targetNode.title && String(targetNode.title).includes("Format Din")));
                const margin = (widget._boxX !== undefined) ? widget._boxX : (isFormatDinamico ? 12 : 22);
                const nodeWidth = (targetNode && targetNode.size && targetNode.size[0]) ? targetNode.size[0] : 200;
                const wWidth = getInlineBoxWidth(targetNode, widget, titleName, propertyName, nodeWidth);
                const drawY = (widget.last_y !== undefined) ? widget.last_y : ((widget.y !== undefined) ? widget.y : 0);
                const wHeight = 18;
                return x >= margin && x <= margin + wWidth && y >= drawY && y <= drawY + wHeight;
            };

            widget.mouse = function(event, pos, node) {
                if (event.type === "mousedown" || event.type === "click") {
                    if (pos && widget.isPointInside && !widget.isPointInside(pos[0], pos[1], node)) {
                        return false;
                    }
                    openInlineSingleLineEditor(node, widget, propertyName, titleName, event);
                    return true;
                }
            };

            widget.callback = function(value, canvas, node, pos, event) {
                openInlineSingleLineEditor(node, widget, propertyName, titleName, event);
            };

            widget.computeSize = function(width) {
                const wWidth = getInlineBoxWidth(node, widget, titleName, propertyName, width);
                return [wWidth + 22, 18];
            };

            widget.draw = function(ctx, node, width, y, height) {
                const drawY = (widget.last_y !== undefined) ? widget.last_y : ((widget.y !== undefined) ? widget.y : y);
                const propKey = propertyName || widget.property;
                const curVal = String((node.properties && propKey && node.properties[propKey] !== undefined)
                    ? node.properties[propKey]
                    : (widget.value !== undefined ? widget.value : ""));
                
                const isFormatDinamico = node && (node.type === "Dynamic Format" || (node.title && String(node.title).includes("Format Din")));
                const margin = (widget._boxX !== undefined) ? widget._boxX : (isFormatDinamico ? 12 : 22);
                const wWidth = getInlineBoxWidth(node, widget, titleName, propertyName, width);
                const rawDisp = widget.name || titleName || "";
                let dispText = curVal.length > 0 ? curVal : (widget._crossCol ? "0" : ((window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot(rawDisp) : rawDisp));
                if (curVal.length > 0 && isFilePathPropOrVal(propKey, curVal)) {
                    dispText = formatPathForDisplay(curVal, wWidth - 16, "bold 11px Consolas, monospace");
                } else if (curVal.length > 0 && !isFormatDinamico && isCompactTextPropOrVal(propKey, curVal)) {
                    dispText = curVal.length > 10 ? (curVal.substring(0, 10) + "...") : curVal;
                }
                const wHeight = 18;
                const borderRadius = 5;

                ctx.save();
                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = "#8b5cf6";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(margin, drawY, wWidth, wHeight, borderRadius);
                else ctx.rect(margin, drawY, wWidth, wHeight);
                ctx.fill();
                ctx.stroke();

                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(margin + 2, drawY + 2, wWidth - 4, wHeight - 4, Math.max(4, borderRadius - 2));
                else ctx.rect(margin + 2, drawY + 2, wWidth - 4, wHeight - 4);
                ctx.clip();

                if (!widget._is_inline_editing) {
                    ctx.fillStyle = curVal.length > 0 ? "#a7f3d0" : "#64748b";
                    ctx.font = "bold 11px Consolas, monospace";
                    ctx.textAlign = "left";

                    const isSalidaNode = !!(node && (node.title === "Output" || (node.type && String(node.type).includes("Output"))));
                    const textPadLeft = (widget._boxX !== undefined) ? 6 : (isSalidaNode ? 6 : (isFormatDinamico ? 6 : 8));
                    ctx.fillText(dispText, margin + textPadLeft, drawY + 13);
                }
                ctx.restore();
            };
        }

        const ORDER_MODES_MULTI_CONCENTRIC = [
            { full: "normal", short: "Normal", i18nKey: "nodes.modes.order_concentric.normal" },
            { full: "invert", short: "Invert", i18nKey: "nodes.modes.order_concentric.invert" },
            { full: "odd_even", short: "Odd/Even", i18nKey: "nodes.modes.order.odd_even" },
            { full: "rand", short: "Rand", i18nKey: "nodes.modes.order.rand" }
        ];

        const ORDER_MODES_MULTI_STRIPES = [
            { full: "79", short: "79 (TL->BR)", i18nKey: "nodes.modes.order_stripes.79" },
            { full: "31", short: "31 (BR->TL)", i18nKey: "nodes.modes.order_stripes.31" },
            { full: "5", short: "5 (Center)", i18nKey: "nodes.modes.order_stripes.5" },
            { full: "-5", short: "-5 (Edges)", i18nKey: "nodes.modes.order_stripes.neg5" },
            { full: "odd_even", short: "Odd/Even", i18nKey: "nodes.modes.order.odd_even" },
            { full: "rand", short: "Rand", i18nKey: "nodes.modes.order.rand" }
        ];

        const ORDER_MODES_MULTI_BORDER = [
            { full: "normal", short: "Normal", i18nKey: "nodes.modes.order_border.normal" },
            { full: "invert", short: "Invert", i18nKey: "nodes.modes.order_border.invert" },
            { full: "5", short: "5 (Center)", i18nKey: "nodes.modes.order_border.5" },
            { full: "-5", short: "-5 (Edges)", i18nKey: "nodes.modes.order_border.neg5" },
            { full: "odd_even", short: "Odd/Even", i18nKey: "nodes.modes.order.odd_even" },
            { full: "rand", short: "Rand", i18nKey: "nodes.modes.order.rand" }
        ];

        const ORDER_MODES_MULTI_ROSETTE = [
            { full: "cw", short: "CW", i18nKey: "nodes.modes.order_radial.cw" },
            { full: "ccw", short: "CCW", i18nKey: "nodes.modes.order_radial.ccw" },
            { full: "5", short: "5 (Center)", i18nKey: "nodes.modes.order_radial.5" },
            { full: "odd_even", short: "Odd/Even", i18nKey: "nodes.modes.order.odd_even" },
            { full: "rand", short: "Rand", i18nKey: "nodes.modes.order.rand" }
        ];

        const ORDER_MODES_MULTI_TUNNEL = [
            { full: "normal", short: "Normal", i18nKey: "nodes.modes.order_tunnel.normal" },
            { full: "invert", short: "Invert", i18nKey: "nodes.modes.order_tunnel.invert" },
            { full: "odd_even", short: "Odd/Even", i18nKey: "nodes.modes.order.odd_even" },
            { full: "rand", short: "Rand", i18nKey: "nodes.modes.order.rand" }
        ];

        const DYNAMIC_NODE_MODES = {
            "Time to Frame": {
                propKey: "mode",
                modes: [
                    { full: "Duration (Ceil)", short: "Ceil" },
                    { full: "Position (Floor)", short: "Floor" },
                    { full: "Nearest (Round)", short: "Round" }
                ],
                secondaryPropKey: "source",
                secondaryModes: [
                    { full: "Custom", short: "Custom" },
                    { full: "Start Time", short: "Start" },
                    { full: "End Time", short: "End" },
                    { full: "Duration", short: "Dur" }
                ]
            },
            "Time/Time to Frame": {
                propKey: "mode",
                modes: [
                    { full: "Duration (Ceil)", short: "Ceil" },
                    { full: "Position (Floor)", short: "Floor" },
                    { full: "Nearest (Round)", short: "Round" }
                ],
                secondaryPropKey: "source",
                secondaryModes: [
                    { full: "Custom", short: "Custom" },
                    { full: "Start Time", short: "Start" },
                    { full: "End Time", short: "End" },
                    { full: "Duration", short: "Dur" }
                ]
            },
            "Frame to Time": {
                propKey: "format",
                modes: [
                    { full: "Milliseconds (ms)", short: "MS" },
                    { full: "ASS Timestamp (HMS)", short: "HMS" },
                    { full: "Seconds (s)", short: "SEC" }
                ],
                secondaryPropKey: "source",
                secondaryModes: [
                    { full: "Custom", short: "Custom" },
                    { full: "Iterator", short: "Iter" },
                    { full: "Index (i)", short: "i" }
                ]
            },
            "Time/Frame to Time": {
                propKey: "format",
                modes: [
                    { full: "Milliseconds (ms)", short: "MS" },
                    { full: "ASS Timestamp (HMS)", short: "HMS" },
                    { full: "Seconds (s)", short: "SEC" }
                ],
                secondaryPropKey: "source",
                secondaryModes: [
                    { full: "Custom", short: "Custom" },
                    { full: "Iterator", short: "Iter" },
                    { full: "Index (i)", short: "i" }
                ]
            },
            "Benchmark Math": {
                propKey: "complexity",
                modes: [
                    { full: "Heavy Math (Trig + Sqrt)", short: "Math" },
                    { full: "Matrix Multiply", short: "Matrix" },
                    { full: "Prime Factorization", short: "Prime" }
                ]
            },
            "Manipulator": {
                propKey: "mode",
                modes: [
                    { full: "Scale", short: "Scale" },
                    { full: "Borders", short: "Borders" },
                    { full: "Deform", short: "Deform" },
                    { full: "Position", short: "Position" },
                    { full: "Redraw", short: "Redraw" },
                    { full: "3D Rotate", short: "3D Rotate" },
                    { full: "Reflect", short: "Reflect" },
                    { full: "Matrix", short: "Matrix" }
                ]
            },
            "Filter": {
                propKey: "mode",
                modes: [
                    { full: "Vertices", short: "Vertices" },
                    { full: "Group", short: "Group" },
                    { full: "Noise", short: "Noise" }
                ]
            },
            "Transform": {
                propKey: "mode",
                modes: [
                    { full: "Inflate", short: "Inflate" },
                    { full: "Skew", short: "Skew" },
                    { full: "Round Corners", short: "Round" },
                    { full: "Flexor", short: "Flexor" },
                    { full: "Distort", short: "Distort" },
                    { full: "Distort2", short: "Distort2" }
                ]
            },
            "Animation": {
                propKey: "mode",
                modes: [
                    { full: "fbf", short: "FBF" },
                    { full: "alpha", short: "Alpha" }
                ],
                secondaryPropKey: "order",
                secondaryModes: [
                    { full: "sequential", short: "SEQ" },
                    { full: "reverse", short: "REV" },
                    { full: "pingpong", short: "PONG" },
                    { full: "random", short: "RAND" }
                ]
            },
            "Functions/Animation": {
                propKey: "mode",
                modes: [
                    { full: "fbf", short: "FBF" },
                    { full: "alpha", short: "Alpha" }
                ],
                secondaryPropKey: "order",
                secondaryModes: [
                    { full: "sequential", short: "SEQ" },
                    { full: "reverse", short: "REV" },
                    { full: "pingpong", short: "PONG" },
                    { full: "random", short: "RAND" }
                ]
            },
            "IMG to Shape": {
                propKey: "mode",
                modes: [
                    { full: "Potrace", short: "Potrace" },
                    { full: "Polygon", short: "Polygon" },
                    { full: "Borders", short: "Borders" }
                ],
                secondaryPropKey: "anchor",
                secondaryModesMap: {
                    "Potrace": [
                        { full: "Center", short: "Center" },
                        { full: "Origin", short: "Origin" },
                        { full: "Absolute", short: "Absolute" }
                    ],
                    "Polygon": [
                        { full: "Center", short: "Center" },
                        { full: "Origin", short: "Origin" },
                        { full: "Absolute", short: "Absolute" }
                    ],
                    "Borders": [
                        { full: "Center", short: "Center" },
                        { full: "Origin", short: "Origin" },
                        { full: "Absolute", short: "Absolute" }
                    ]
                },
                tertiaryPropKey: "invert",
                tertiaryModes: [
                    { full: "Normal", short: "Normal" },
                    { full: "Inverted", short: "Inverted" }
                ]
            },
            "Concatenate": {
                propKey: "separator",
                modes: [
                    { full: "nil", short: "NIL" },
                    { full: "space", short: "SPACE" },
                    { full: "comma", short: "," },
                    { full: "semicolon", short: ";" },
                    { full: "newline", short: "ENTER" },
                    { full: "zip", short: "ZIP" }
                ]
            },
            "Basics/Concatenate": {
                propKey: "separator",
                modes: [
                    { full: "nil", short: "NIL" },
                    { full: "space", short: "SPACE" },
                    { full: "comma", short: "," },
                    { full: "semicolon", short: ";" },
                    { full: "newline", short: "ENTER" },
                    { full: "zip", short: "ZIP" }
                ]
            },
            "Kana Transliteration": [
                { full: "Romaji to Hiragana", short: "Romaji" },
                { full: "Romaji to Katakana", short: "Katakana" },
                { full: "Hiragana to Romaji", short: "Hira→Rom" },
                { full: "Katakana to Romaji", short: "Kata→Rom" }
            ],
            "Bezier Curve": [
                { full: "Cubic 2D", short: "Cubic" },
                { full: "Quadratic 2D", short: "Quadratic" },
                { full: "N-Degree", short: "N-Degree" },
                { full: "Constant Speed", short: "Constant" },
                { full: "Shape Contour", short: "Contour" },
                { full: "Subdivide", short: "Subdiv" },
                { full: "Trajectory", short: "Trajectory" }
            ],
            "Particles": [
                { full: "Outline v2 (bord_to_pixels_v2)", short: "Outline v2" },
                { full: "Border (Outline)", short: "Border" },
                { full: "Inner Fill", short: "Fill" }
            ],
            "Text on Path": {
                propKey: "mode",
                modes: [
                    { full: "Center", short: "Center" },
                    { full: "Left", short: "Left" },
                    { full: "Right", short: "Right" },
                    { full: "Justified", short: "Justified" },
                    { full: "Animated", short: "Animated" }
                ]
            },
            "Math": {
                propKey: "category",
                modes: [
                    { full: "Basic", short: "BASIC" },
                    { full: "Trig", short: "TRIG" },
                    { full: "Easing", short: "EASING" },
                    { full: "Waves", short: "WAVES" },
                    { full: "Utilities", short: "UTILITIES" }
                ],
                secondaryPropKey: "operation",
                secondaryModesMap: {
                    "Basic": [
                        { full: "Add", short: "Add" },
                        { full: "Subtract", short: "Sub" },
                        { full: "Multiply", short: "Mul" },
                        { full: "Divide", short: "Div" },
                        { full: "Modulo", short: "Mod" },
                        { full: "Power", short: "Pow" },
                        { full: "Absolute", short: "Abs" },
                        { full: "Negative", short: "Neg" },
                        { full: "Round", short: "Round" },
                        { full: "Floor", short: "Floor" },
                        { full: "Ceil", short: "Ceil" }
                    ],
                    "Trig": [
                        { full: "Sin", short: "Sin" },
                        { full: "Cos", short: "Cos" },
                        { full: "Tan", short: "Tan" },
                        { full: "ArcSin", short: "ArcSin" },
                        { full: "ArcCos", short: "ArcCos" },
                        { full: "ArcTan", short: "ArcTan" },
                        { full: "ArcTan2", short: "ArcTan2" },
                        { full: "Radians", short: "Rad" },
                        { full: "Degrees", short: "Deg" }
                    ],
                    "Easing": [
                        { full: "EaseIn", short: "EaseIn" },
                        { full: "EaseOut", short: "EaseOut" },
                        { full: "EaseInOut", short: "EaseInOut" },
                        { full: "CubicIn", short: "CubicIn" },
                        { full: "CubicOut", short: "CubicOut" },
                        { full: "Exponential", short: "Expo" },
                        { full: "Elastic", short: "Elastic" },
                        { full: "Bounce", short: "Bounce" },
                        { full: "Back", short: "Back" }
                    ],
                    "Waves": [
                        { full: "Sine", short: "Sine" },
                        { full: "Square", short: "Square" },
                        { full: "Triangle", short: "Triangle" },
                        { full: "Sawtooth", short: "Sawtooth" }
                    ],
                    "Utilities": [
                        { full: "Clamp", short: "Clamp" },
                        { full: "Lerp", short: "Lerp" },
                        { full: "Min", short: "Min" },
                        { full: "Max", short: "Max" },
                        { full: "Random", short: "Random" },
                        { full: "MapRange", short: "MapRange" }
                    ]
                }
            },
            "Basics/Math": {
                propKey: "category",
                modes: [
                    { full: "Basic", short: "BASIC" },
                    { full: "Trig", short: "TRIG" },
                    { full: "Easing", short: "EASING" },
                    { full: "Waves", short: "WAVES" },
                    { full: "Utilities", short: "UTILITIES" }
                ],
                secondaryPropKey: "operation",
                secondaryModesMap: {
                    "Basic": [
                        { full: "Add", short: "Add" },
                        { full: "Subtract", short: "Sub" },
                        { full: "Multiply", short: "Mul" },
                        { full: "Divide", short: "Div" },
                        { full: "Modulo", short: "Mod" },
                        { full: "Power", short: "Pow" },
                        { full: "Absolute", short: "Abs" },
                        { full: "Negative", short: "Neg" },
                        { full: "Round", short: "Round" },
                        { full: "Floor", short: "Floor" },
                        { full: "Ceil", short: "Ceil" }
                    ],
                    "Trig": [
                        { full: "Sin", short: "Sin" },
                        { full: "Cos", short: "Cos" },
                        { full: "Tan", short: "Tan" },
                        { full: "ArcSin", short: "ArcSin" },
                        { full: "ArcCos", short: "ArcCos" },
                        { full: "ArcTan", short: "ArcTan" },
                        { full: "ArcTan2", short: "ArcTan2" },
                        { full: "Radians", short: "Rad" },
                        { full: "Degrees", short: "Deg" }
                    ],
                    "Easing": [
                        { full: "EaseIn", short: "EaseIn" },
                        { full: "EaseOut", short: "EaseOut" },
                        { full: "EaseInOut", short: "EaseInOut" },
                        { full: "CubicIn", short: "CubicIn" },
                        { full: "CubicOut", short: "CubicOut" },
                        { full: "Exponential", short: "Expo" },
                        { full: "Elastic", short: "Elastic" },
                        { full: "Bounce", short: "Bounce" },
                        { full: "Back", short: "Back" }
                    ],
                    "Waves": [
                        { full: "Sine", short: "Sine" },
                        { full: "Square", short: "Square" },
                        { full: "Triangle", short: "Triangle" },
                        { full: "Sawtooth", short: "Sawtooth" }
                    ],
                    "Utilities": [
                        { full: "Clamp", short: "Clamp" },
                        { full: "Lerp", short: "Lerp" },
                        { full: "Min", short: "Min" },
                        { full: "Max", short: "Max" },
                        { full: "Random", short: "Random" },
                        { full: "MapRange", short: "MapRange" }
                    ]
                }
            },
            "Tag Oscillator": {
                propKey: "mode",
                modes: [
                    { full: "wave", short: "WAVE" },
                    { full: "steps", short: "STEPS" },
                    { full: "noise", short: "NOISE" },
                    { full: "pulses", short: "PULSE" },
                    { full: "flashes", short: "STROBE" },
                    { full: "rhythmic", short: "RHYTHM" },
                    { full: "custom", short: "CUSTOM" }
                ],
                secondaryPropKey: "order_mode",
                secondaryModes: [
                    { full: "sequential", short: "SEQ" },
                    { full: "pingpong", short: "PONG" },
                    { full: "random", short: "RAND" },
                    { full: "shuffle", short: "SHUFF" }
                ]
            },
            "Functions/Tag Oscillator": {
                propKey: "mode",
                modes: [
                    { full: "wave", short: "WAVE" },
                    { full: "steps", short: "STEPS" },
                    { full: "noise", short: "NOISE" },
                    { full: "pulses", short: "PULSE" },
                    { full: "flashes", short: "STROBE" },
                    { full: "rhythmic", short: "RHYTHM" },
                    { full: "custom", short: "CUSTOM" }
                ],
                secondaryPropKey: "order_mode",
                secondaryModes: [
                    { full: "sequential", short: "SEQ" },
                    { full: "pingpong", short: "PONG" },
                    { full: "random", short: "RAND" },
                    { full: "shuffle", short: "SHUFF" }
                ]
            },
            "Tag Manipulator": {
                propKey: "mode",
                modes: [
                    { full: "invert", short: "INV" },
                    { full: "reset", short: "RESET" },
                    { full: "extractor", short: "EXTRACT" }
                ]
            },
            "Functions/Tag Manipulator": {
                propKey: "mode",
                modes: [
                    { full: "invert", short: "INV" },
                    { full: "reset", short: "RESET" },
                    { full: "extractor", short: "EXTRACT" }
                ]
            },
            "Retime": {
                propKey: "phase",
                modes: [
                    { full: "syl", short: "SYL" },
                    { full: "presyl", short: "PRESYL" },
                    { full: "postsyl", short: "POSTSYL" },
                    { full: "line", short: "LINE" },
                    { full: "preline", short: "PRELINE" },
                    { full: "postline", short: "POSTLINE" },
                    { full: "start2syl", short: "START2SYL" },
                    { full: "syl2end", short: "SYL2END" },
                    { full: "abs", short: "ABS" },
                    { full: "sylpct", short: "SYLPCT" }
                ]
            },
            "Time/Retime": {
                propKey: "phase",
                modes: [
                    { full: "syl", short: "SYL" },
                    { full: "presyl", short: "PRESYL" },
                    { full: "postsyl", short: "POSTSYL" },
                    { full: "line", short: "LINE" },
                    { full: "preline", short: "PRELINE" },
                    { full: "postline", short: "POSTLINE" },
                    { full: "start2syl", short: "START2SYL" },
                    { full: "syl2end", short: "SYL2END" },
                    { full: "abs", short: "ABS" },
                    { full: "sylpct", short: "SYLPCT" }
                ]
            },
            "Synced": {
                propKey: "mode",
                modes: [
                    { full: "order", short: "ORDER" },
                    { full: "style", short: "STYLE" },
                    { full: "actor", short: "ACTOR" },
                    { full: "layer", short: "LAYER" },
                    { full: "effect", short: "EFFECT" }
                ]
            },
            "Time/Synced": {
                propKey: "mode",
                modes: [
                    { full: "order", short: "ORDER" },
                    { full: "style", short: "STYLE" },
                    { full: "actor", short: "ACTOR" },
                    { full: "layer", short: "LAYER" },
                    { full: "effect", short: "EFFECT" }
                ]
            },
            "Glitter": {
                propKey: "mode",
                modes: [
                    { full: "flashes", short: "Flashes" },
                    { full: "pulses", short: "Pulses" },
                    { full: "waves", short: "Waves" },
                    { full: "noise", short: "Noise" }
                ]
            },
            "Functions/Glitter": {
                propKey: "mode",
                modes: [
                    { full: "flashes", short: "Flashes" },
                    { full: "pulses", short: "Pulses" },
                    { full: "waves", short: "Waves" },
                    { full: "noise", short: "Noise" }
                ]
            },
            "MaxLoop": [
                { full: "normal", short: "NORM" },
                { full: "fbf", short: "FBF" }
            ],
            "Loops/MaxLoop": [
                { full: "normal", short: "NORM" },
                { full: "fbf", short: "FBF" }
            ],
            "Memory": [
                { full: "remember", short: "SAVE" },
                { full: "retrieve", short: "LOAD" }
            ],
            "Variables/Memory": [
                { full: "remember", short: "SAVE" },
                { full: "retrieve", short: "LOAD" }
            ],
            "Sys Var": {
                propKey: "var_name",
                modes: ALL_SYS_VARS_LIST.map(v => ({ full: v, short: v }))
            },
            "Variables/Sys Var": {
                propKey: "var_name",
                modes: ALL_SYS_VARS_LIST.map(v => ({ full: v, short: v }))
            },
            "MultiTag": {
                propKey: "tag_type",
                modes: Object.keys(TAG_DEFINITIONS).map(t => ({ full: t, short: t }))
            },
            "Basics/MultiTag": {
                propKey: "tag_type",
                modes: Object.keys(TAG_DEFINITIONS).map(t => ({ full: t, short: t }))
            },
            "MultiRandom": [
                { full: "R", short: "R" },
                { full: "Rs", short: "Rs" },
                { full: "Rr", short: "Rr" },
                { full: "Rc", short: "Rc" },
                { full: "Rd", short: "Rd" },
                { full: "Rm", short: "Rm" },
                { full: "Rds", short: "Rds" },
                { full: "Rcs", short: "Rcs" },
                { full: "Rms", short: "Rms" },
                { full: "Re", short: "Re" },
                { full: "Rfake", short: "Rfake" },
                { full: "Rcolor", short: "Rcolor" },
                { full: "R2d", short: "R2d" },
                { full: "Rbool", short: "Rbool" },
                { full: "Rstep", short: "Rstep" }
            ],
            "Basics/MultiRandom": [
                { full: "R", short: "R" },
                { full: "Rs", short: "Rs" },
                { full: "Rr", short: "Rr" },
                { full: "Rc", short: "Rc" },
                { full: "Rd", short: "Rd" },
                { full: "Rm", short: "Rm" },
                { full: "Rds", short: "Rds" },
                { full: "Rcs", short: "Rcs" },
                { full: "Rms", short: "Rms" },
                { full: "Re", short: "Re" },
                { full: "Rfake", short: "Rfake" },
                { full: "Rcolor", short: "Rcolor" },
                { full: "R2d", short: "R2d" },
                { full: "Rbool", short: "Rbool" },
                { full: "Rstep", short: "Rstep" }
            ],
            "Slicer": {
                propKey: "mode",
                secondaryPropKey: "loop_mode",
                modes: [
                    { full: "Grid 1D/2D", short: "Grid" },
                    { full: "hex", short: "Hex" },
                    { full: "tri", short: "Tri" },
                    { full: "dia", short: "Diamond" },
                    { full: "ring", short: "Rings" },
                    { full: "voronoi", short: "Voronoi" },
                    { full: "delaunay", short: "Delaunay" },
                    { full: "brick", short: "Brick" },
                    { full: "jigsaw", short: "Jigsaw" },
                    { full: "circuit", short: "Circuit" },
                    { full: "kagome", short: "Kagome" },
                    { full: "rhombille", short: "Cubes" },
                    { full: "herringbone", short: "Herringbone" },
                    { full: "mondrian", short: "Mondrian" },
                    { full: "truchet", short: "Truchet" },
                    { full: "scallop", short: "Scallop" },
                    { full: "ashlar", short: "Ashlar" },
                    { full: "bez", short: "Bezier" },
                    { full: "octagon", short: "Octagon" },
                    { full: "ray", short: "Rays" },
                    { full: "web", short: "Web" },
                    { full: "quad", short: "Quad" },
                    { full: "pattern", short: "Modular" }
                ],
                secondaryModes: [
                    { full: "Loops", short: "Loops" },
                    { full: "Shape", short: "Shape" }
                ]
            },
            "Concentric Borders": {
                propKey: "out_mode",
                modes: [
                    { full: "Shape", short: "Shape" },
                    { full: "Clip", short: "\\clip" },
                    { full: "iClip", short: "\\iclip" }
                ]
            },
            "Walker": {
                propKey: "mode",
                modes: [
                    { full: "Global (Continuous)", short: "Global" },
                    { full: "Per Outline (Parallel)", short: "Outline" }
                ],
                secondaryPropKey: "invert",
                secondaryModes: [
                    { full: "0", short: "Normal" },
                    { full: "1", short: "Invert" }
                ]
            },
            "Clip Gradient": {
                propKey: "out_mode",
                modes: [
                    { full: "clip", short: "\\clip" },
                    { full: "iclip", short: "\\iclip" },
                    { full: "shape", short: "Shape" }
                ]
            },
            "Functions/Clip Gradient": {
                propKey: "out_mode",
                modes: [
                    { full: "clip", short: "\\clip" },
                    { full: "iclip", short: "\\iclip" },
                    { full: "shape", short: "Shape" }
                ]
            },
            "Move Tag": {
                propKey: "mode",
                modes: [
                    { full: "trajectory", short: "Trajectory" },
                    { full: "waypoints", short: "Waypoints" },
                    { full: "jitter", short: "Jitter" }
                ]
            },
            "Functions/Move Tag": {
                propKey: "mode",
                modes: [
                    { full: "trajectory", short: "Trajectory" },
                    { full: "waypoints", short: "Waypoints" },
                    { full: "jitter", short: "Jitter" }
                ]
            },
            "Modulator": {
                propKey: "mode",
                modes: [
                    { full: "rms", short: "RMS" },
                    { full: "peak", short: "Peak" },
                    { full: "bass", short: "Bass" },
                    { full: "mids", short: "Mids" },
                    { full: "highs", short: "Highs" },
                    { full: "custom", short: "Custom" }
                ]
            },
            "Waveform": {
                propKey: "mode",
                modes: [
                    { full: "oscilloscope", short: "Oscillo" },
                    { full: "fftbars", short: "Bars" },
                    { full: "filledwave", short: "Filled" },
                    { full: "radial", short: "Radial" },
                    { full: "points", short: "Points" }
                ]
            },
            "Text": {
                propKey: "operation",
                modes: [
                    { full: "Strip Tags", short: "Strip Tags" },
                    { full: "Upper", short: "Upper" },
                    { full: "Lower", short: "Lower" },
                    { full: "Replace", short: "Replace" },
                    { full: "Substring", short: "Substring" },
                    { full: "Length", short: "Length" },
                    { full: "Contains", short: "Contains" },
                    { full: "Kana", short: "Kana" },
                    { full: "Romaji to Karaoke", short: "To Kara" }
                ]
            },
            "Array": {
                propKey: "out_mode",
                secondaryPropKey: "mode",
                modes: [
                    { full: "Loops", short: "LOOPS" },
                    { full: "Shape", short: "SHAPE" }
                ],
                secondaryModes: [
                    { full: "Grid", short: "GRID" },
                    { full: "Formation", short: "FORM" },
                    { full: "Rings", short: "RINGS" },
                    { full: "Spiral", short: "SPIRAL" },
                    { full: "Scatter", short: "SCATTER" },
                    { full: "Hex", short: "HEX" }
                ]
            },
            "Union & Divide": {
                propKey: "mode",
                modes: [
                    { full: "Divide (PolyTree)", short: "DIVIDE" },
                    { full: "Union (Merge/Union)", short: "UNION" },
                    { full: "Divide (Sub-paths)", short: "SUB-PATHS" },
                    { full: "Fusion (Tags)", short: "FUSION" }
                ]
            },
            "Multi": {
                propKey: "mode",
                secondaryPropKey: "loop_mode",
                modes: [
                    { full: "Concentric Squares", short: "Squares" },
                    { full: "Diagonal Stripes", short: "Stripes" },
                    { full: "Concentric Rings", short: "Rings" },
                    { full: "Polygonal Mosaic", short: "Mosaic" },
                    { full: "Multi-Shape Mosaic", short: "MultiShape" },
                    { full: "Segmented Border", short: "Border" },
                    { full: "Radial Rosette", short: "Rosette" },
                    { full: "Tunnel / Cascade", short: "Tunnel" },
                    { full: "Banner", short: "Banner" },
                    { full: "Gear", short: "Gear" }
                ],
                secondaryModes: [
                    { full: "Shape", short: "Shape" },
                    { full: "Loops", short: "Loops" }
                ]
            },
            "Clipper": {
                propKey: "mode",
                modes: [
                    { full: "difference", short: "DIFF" },
                    { full: "intersection", short: "INTER" },
                    { full: "union", short: "UNION" },
                    { full: "xor", short: "XOR" },
                    { full: "offset", short: "OFFSET" },
                    { full: "minkowski_sum", short: "MINK +" },
                    { full: "minkowski_diff", short: "MINK -" }
                ]
            }
        };


        const _PREVIEW_IMG_CACHE = {};
        function loadPreviewImage(nodeObj, pPath) {
            if (!pPath || !nodeObj) return;
            if (_PREVIEW_IMG_CACHE[pPath]) {
                nodeObj._imgObj = _PREVIEW_IMG_CACHE[pPath];
                nodeObj._imgLoadedPath = pPath;
                if (nodeObj.setDirtyCanvas) nodeObj.setDirtyCanvas(true, true);
                return;
            }
            const imgObj = new Image();
            imgObj.onload = () => {
                _PREVIEW_IMG_CACHE[pPath] = imgObj;
                nodeObj._imgObj = imgObj;
                nodeObj._imgLoadedPath = pPath;
                if (nodeObj.setDirtyCanvas) nodeObj.setDirtyCanvas(true, true);
            };
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_image_file_data_url === 'function') {
                window.pywebview.api.get_image_file_data_url(pPath).then(dataUri => {
                    if (dataUri) imgObj.src = dataUri;
                    else imgObj.src = (pPath.startsWith("http") || pPath.startsWith("file:")) ? pPath : ("file:///" + pPath.replace(/\\/g, "/"));
                }).catch(() => {
                    imgObj.src = (pPath.startsWith("http") || pPath.startsWith("file:")) ? pPath : ("file:///" + pPath.replace(/\\/g, "/"));
                });
            } else {
                imgObj.src = (pPath.startsWith("http") || pPath.startsWith("file:")) ? pPath : ("file:///" + pPath.replace(/\\/g, "/"));
            }
        }

        function getSafeLocalPos(node, raw_pos) {
            if (!raw_pos) return [0, 0];
            let lx = raw_pos[0];
            let ly = raw_pos[1];
            if (node && node.pos && (lx > node.pos[0] + (node.size ? node.size[0] : 0) || ly > node.pos[1] + (node.size ? node.size[1] : 0))) {
                lx = lx - node.pos[0];
                ly = ly - node.pos[1];
            }
            return [lx, ly];
        }

        function getImgNodePreviewLayout(node) {
            const nodeW = node.size ? node.size[0] : 380;
            const nodeH = node.size ? node.size[1] : 230;

            let max_in_text_w = 0;
            if (node.properties) {
                for (const k in node.properties) {
                    if (k === "mode" || k === "modo" || k === "anchor" || k === "invert" || k === "view_mode" || k === "bin_mode" || k === "invert_img" || k === "order" || k === "alpha_tag" || k === "var_name" || k.startsWith("_")) continue;
                    let val = String(node.properties[k] || "");
                    if (k === "image_path") val = "...image.png";
                    else if (k === "frames") {
                        if (val.length === 0) {
                            val = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Shape list") : "Shape list";
                        }
                        if (val.length > 10) val = val.substring(0, 8) + "...";
                    }
                    if (val.length > 0) {
                        const tw = Math.min(85, getExactTextWidth(val, "bold 11px monospace"));
                        if (tw > max_in_text_w) max_in_text_w = tw;
                    }
                }
            }

            let max_out_w = 0;
            (node.outputs || []).forEach(out => {
                if (out.name) {
                    const ow = getExactTextWidth(out.name, "10px sans-serif");
                    if (ow > max_out_w) max_out_w = ow;
                }
            });

            const left_box_w = Math.max(70, max_in_text_w + 16);
            const left_col_end = 22 + left_box_w;
            const right_col_w = max_out_w > 0 ? (max_out_w + 38) : 20;
            const right_col_start = nodeW - right_col_w;

            const hasTopBar = Boolean(node._totalFrames && node._totalFrames > 1);
            // Strict vertical bounds: protect title bar (y <= 0) and footer iterator label (y >= nodeH - 22)
            const minCardY = hasTopBar ? 30 : 12;
            const maxCardBottom = nodeH - 52;

            const availW = Math.max(150, right_col_start - left_col_end - 24);
            const availH = Math.max(80, maxCardBottom - minCardY);
            const cardSize = Math.floor(Math.min(availW, availH));
            const cardW = cardSize;
            const cardH = cardSize;

            const cardX = Math.floor(left_col_end + (right_col_start - left_col_end - cardW) / 2);
            const cardY = Math.max(minCardY, Math.floor(minCardY + (maxCardBottom - minCardY - cardH) / 2));

            const barY = cardY + cardH + 8;
            const barH = 20;
            const btnH = 20;
            const barTotalW = 150;
            const barStartX = Math.floor(cardX + (cardW - barTotalW) / 2);
            const btnW = 118;
            const btnX = barStartX;
            const refreshW = 28;
            const refreshX = barStartX + 122;

            const topBarH = 18;
            const topBarY = cardY - 22;
            const stepBtnW = 18;
            const trackX = cardX + stepBtnW + 4;
            const trackW = cardW - 2 * stepBtnW - 8;

            return {
                nodeW, nodeH,
                cardX, cardY, cardW, cardH,
                cardCenterX: cardX + cardW / 2,
                cardCenterY: cardY + cardH / 2,
                barY, barH, btnH,
                btnX, btnW,
                refreshX, refreshW,
                hasTopBar, topBarY, topBarH, stepBtnW, trackX, trackW
            };
        }

        function hitTestImgPreview(layout, lx, ly) {
            if (!layout) return null;
            const pad = 5;

            if (layout.hasTopBar) {
                if (ly >= layout.topBarY - 3 && ly <= layout.topBarY + layout.topBarH + 3) {
                    if (lx >= layout.cardX - 3 && lx <= layout.cardX + layout.stepBtnW + 2) {
                        return "prev_frame";
                    }
                    if (lx >= layout.cardX + layout.cardW - layout.stepBtnW - 2 && lx <= layout.cardX + layout.cardW + 3) {
                        return "next_frame";
                    }
                    if (lx >= layout.trackX - 2 && lx <= layout.trackX + layout.trackW + 2) {
                        return "scrub_track";
                    }
                }
            }

            if (ly >= layout.barY - pad && ly <= layout.barY + layout.btnH + pad) {
                if (lx >= layout.btnX - pad && lx <= layout.btnX + layout.btnW + 2) {
                    return "view_btn";
                }
                if (lx >= layout.refreshX - 2 && lx <= layout.refreshX + layout.refreshW + pad) {
                    return "refresh_btn";
                }
            }

            if (lx >= layout.cardX && lx <= layout.cardX + layout.cardW && ly >= layout.cardY && ly <= layout.cardY + layout.cardH) {
                return "card";
            }

            return null;
        }

        function updateImgPreviewCursor(node, canvas, target) {
            const cObj = canvas || LGraphCanvas.active_canvas || window.canvas || window.graphcanvas;
            const cElem = cObj ? (cObj.canvas || cObj) : null;
            if (!cElem || !cElem.style) return;

            if (node && node._isCardPanning) {
                cElem.style.cursor = "grabbing";
                return;
            }

            const isAnimNode = Boolean(node && (node.type === "Functions/Animation" || node.title === "Animation"));
            if (target === "view_btn" || target === "refresh_btn" || target === "prev_frame" || target === "next_frame" || target === "scrub_track" || (target === "card" && !isAnimNode)) {
                cElem.style.cursor = "pointer";
            } else {
                if (cElem.style.cursor === "pointer" || cElem.style.cursor === "grabbing") {
                    cElem.style.cursor = "default";
                }
            }
        }

        function resetImgPreviewTransform(node, animated = true) {
            if (!node) return;
            if (node._cardResetAnimId) {
                cancelAnimationFrame(node._cardResetAnimId);
                node._cardResetAnimId = null;
            }
            const startZoom = (typeof node._cardZoom === "number" && !isNaN(node._cardZoom)) ? node._cardZoom : 1.0;
            const startPanX = (typeof node._cardPanX === "number" && !isNaN(node._cardPanX)) ? node._cardPanX : 0;
            const startPanY = (typeof node._cardPanY === "number" && !isNaN(node._cardPanY)) ? node._cardPanY : 0;

            if (!animated || (Math.abs(startZoom - 1.0) < 0.001 && Math.abs(startPanX) < 0.5 && Math.abs(startPanY) < 0.5)) {
                node._cardZoom = 1.0;
                node._cardPanX = 0;
                node._cardPanY = 0;
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                return;
            }

            const duration = 220;
            const startTime = performance.now();
            const step = (now) => {
                const t = Math.min(1, (now - startTime) / duration);
                const ease = 1 - Math.pow(1 - t, 3);
                node._cardZoom = startZoom + (1.0 - startZoom) * ease;
                node._cardPanX = startPanX * (1 - ease);
                node._cardPanY = startPanY * (1 - ease);
                if (t < 1) {
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, false);
                    node._cardResetAnimId = requestAnimationFrame(step);
                } else {
                    node._cardResetAnimId = null;
                    node._cardZoom = 1.0;
                    node._cardPanX = 0;
                    node._cardPanY = 0;
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                }
            };
            node._cardResetAnimId = requestAnimationFrame(step);
        }

        (function initImgPreviewCardZoomPan() {
            function isImgPreviewNode(node) {
                if (!node || (node.flags && node.flags.collapsed)) return false;
                const t = String(node.type || "");
                const title = String(node.title || "");
                return (
                    t === "Shape/IMG to Shape" || t === "IMG to Shape" || title === "IMG to Shape" ||
                    t === "Functions/IMG to pixels" || t === "IMG to pixels" || title === "IMG to pixels" ||
                    t === "Functions/Animation" || t === "Animation" || title === "Animation"
                );
            }

            function getHoveredImgPreviewCardFromEvent(e) {
                const cObj = (window.LGraphCanvas && window.LGraphCanvas.active_canvas) || window.canvas || window.graphcanvas;
                if (!cObj || !cObj.canvas || !cObj.graph) return null;
                if (e && e.target && e.target !== cObj.canvas) return null;

                const rect = cObj.canvas.getBoundingClientRect();
                const scale = (cObj.ds && cObj.ds.scale) ? cObj.ds.scale : 1.0;
                const offset = (cObj.ds && cObj.ds.offset) ? cObj.ds.offset : [0, 0];
                const graphX = (e.clientX - rect.left) / scale - offset[0];
                const graphY = (e.clientY - rect.top) / scale - offset[1];

                const node = cObj.graph.getNodeOnPos(graphX, graphY, cObj.visible_nodes, 5);
                if (!isImgPreviewNode(node) || !node.pos) return null;

                const lx = graphX - node.pos[0];
                const ly = graphY - node.pos[1];
                const layout = getImgNodePreviewLayout(node);
                const target = hitTestImgPreview(layout, lx, ly);
                if (target !== "card") return null;

                return { node, layout, lx, ly, scale, cObj };
            }

            window.addEventListener("wheel", function(e) {
                const hit = getHoveredImgPreviewCardFromEvent(e);
                if (!hit) return;

                if (typeof window.closeAllActiveNodeEditors === "function") {
                    window.closeAllActiveNodeEditors(true);
                }

                e.preventDefault();
                e.stopPropagation();
                if (typeof e.stopImmediatePropagation === "function") {
                    e.stopImmediatePropagation();
                }

                const { node, layout, lx, ly } = hit;
                if (node._cardResetAnimId) {
                    cancelAnimationFrame(node._cardResetAnimId);
                    node._cardResetAnimId = null;
                }

                let delta = 0;
                if (e.deltaY != null && e.deltaY !== 0) delta = -e.deltaY;
                else if (e.wheelDeltaY != null && e.wheelDeltaY !== 0) delta = e.wheelDeltaY;
                else if (e.wheelDelta != null && e.wheelDelta !== 0) delta = e.wheelDelta;
                else if (e.detail != null && e.detail !== 0) delta = e.detail * -60;
                if (delta === 0) return;

                const zoomFactor = delta > 0 ? 1.15 : (1 / 1.15);
                const curZoom = (typeof node._cardZoom === "number" && !isNaN(node._cardZoom) && node._cardZoom > 0) ? node._cardZoom : 1.0;
                const curPanX = (typeof node._cardPanX === "number" && !isNaN(node._cardPanX)) ? node._cardPanX : 0;
                const curPanY = (typeof node._cardPanY === "number" && !isNaN(node._cardPanY)) ? node._cardPanY : 0;

                const newZoom = Math.min(Math.max(curZoom * zoomFactor, 1.0), 15.0);
                if (newZoom <= 1.02 && delta < 0) {
                    resetImgPreviewTransform(node, true);
                    return;
                }

                const dx = lx - layout.cardCenterX;
                const dy = ly - layout.cardCenterY;
                const ratio = newZoom / curZoom;

                node._cardPanX = dx - (dx - curPanX) * ratio;
                node._cardPanY = dy - (dy - curPanY) * ratio;
                node._cardZoom = newZoom;

                if (node.setDirtyCanvas) node.setDirtyCanvas(true, false);
                if (hit.cObj && typeof hit.cObj.draw === "function") hit.cObj.draw(true, false);
            }, { capture: true, passive: false });

            let activePanSession = null;

            function onMiddleDown(e) {
                const isMiddle = (e.button === 1 || e.which === 2);
                if (!isMiddle) return;
                if (activePanSession) return;

                const hit = getHoveredImgPreviewCardFromEvent(e);
                if (!hit) return;

                if (typeof window.closeAllActiveNodeEditors === "function") {
                    window.closeAllActiveNodeEditors(true);
                }

                e.preventDefault();
                e.stopPropagation();
                if (typeof e.stopImmediatePropagation === "function") {
                    e.stopImmediatePropagation();
                }

                const { node, cObj } = hit;
                if (node._cardResetAnimId) {
                    cancelAnimationFrame(node._cardResetAnimId);
                    node._cardResetAnimId = null;
                }

                if (typeof node._cardZoom !== "number" || isNaN(node._cardZoom) || node._cardZoom <= 0) {
                    node._cardZoom = 1.0;
                }
                if (typeof node._cardPanX !== "number" || isNaN(node._cardPanX)) node._cardPanX = 0;
                if (typeof node._cardPanY !== "number" || isNaN(node._cardPanY)) node._cardPanY = 0;

                node._isCardPanning = true;
                updateImgPreviewCursor(node, cObj, "card");

                activePanSession = {
                    node: node,
                    cObj: cObj,
                    lastX: e.clientX,
                    lastY: e.clientY
                };

                const onWindowMove = (eMove) => {
                    if (!activePanSession) return;
                    eMove.preventDefault();
                    eMove.stopPropagation();
                    if (typeof eMove.stopImmediatePropagation === "function") {
                        eMove.stopImmediatePropagation();
                    }

                    const curScale = (activePanSession.cObj && activePanSession.cObj.ds && activePanSession.cObj.ds.scale)
                        ? activePanSession.cObj.ds.scale
                        : 1.0;
                    const dx = (eMove.clientX - activePanSession.lastX) / curScale;
                    const dy = (eMove.clientY - activePanSession.lastY) / curScale;
                    activePanSession.lastX = eMove.clientX;
                    activePanSession.lastY = eMove.clientY;

                    activePanSession.node._cardPanX = (activePanSession.node._cardPanX || 0) + dx;
                    activePanSession.node._cardPanY = (activePanSession.node._cardPanY || 0) + dy;

                    if (activePanSession.node.setDirtyCanvas) activePanSession.node.setDirtyCanvas(true, false);
                    if (activePanSession.cObj && typeof activePanSession.cObj.draw === "function") {
                        activePanSession.cObj.draw(true, false);
                    }
                };

                const onWindowUp = (eUp) => {
                    if (!activePanSession) return;
                    const targetNode = activePanSession.node;
                    const targetCanvas = activePanSession.cObj;
                    activePanSession = null;
                    targetNode._isCardPanning = false;
                    updateImgPreviewCursor(targetNode, targetCanvas, targetNode._hoverTarget || null);
                    if (targetNode.setDirtyCanvas) targetNode.setDirtyCanvas(true, false);

                    window.removeEventListener("pointermove", onWindowMove, true);
                    window.removeEventListener("mousemove", onWindowMove, true);
                    window.removeEventListener("pointerup", onWindowUp, true);
                    window.removeEventListener("mouseup", onWindowUp, true);
                    window.removeEventListener("pointercancel", onWindowUp, true);
                    window.removeEventListener("blur", onWindowUp);
                };

                window.addEventListener("pointermove", onWindowMove, true);
                window.addEventListener("mousemove", onWindowMove, true);
                window.addEventListener("pointerup", onWindowUp, true);
                window.addEventListener("mouseup", onWindowUp, true);
                window.addEventListener("pointercancel", onWindowUp, true);
                window.addEventListener("blur", onWindowUp);
            }

            window.addEventListener("pointerdown", onMiddleDown, { capture: true, passive: false });
            window.addEventListener("mousedown", onMiddleDown, { capture: true, passive: false });

            window.addEventListener("auxclick", function(e) {
                if (e.button === 1 || e.which === 2) {
                    const hit = getHoveredImgPreviewCardFromEvent(e);
                    if (hit) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }
            }, true);

            window.addEventListener("keydown", function(e) {
                if (e.key !== "r" && e.key !== "R") return;
                if (e.ctrlKey || e.metaKey || e.altKey) return;

                const activeEl = document.activeElement;
                if (activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA" || activeEl.isContentEditable || (activeEl.classList && activeEl.classList.contains("ace_text-input")))) {
                    return;
                }

                const cObj = (window.LGraphCanvas && window.LGraphCanvas.active_canvas) || window.canvas || window.graphcanvas;
                if (!cObj || !cObj.graph || !Array.isArray(cObj.graph._nodes)) return;

                for (let i = cObj.graph._nodes.length - 1; i >= 0; i--) {
                    const n = cObj.graph._nodes[i];
                    if (isImgPreviewNode(n) && n.mouseOver && n._hoverTarget === "card") {
                        e.preventDefault();
                        e.stopPropagation();
                        resetImgPreviewTransform(n, true);
                        break;
                    }
                }
            });
        })();


        function getTitleModeInfo(node) {
            if (!node) return null;
            const title = String(node.title || node.type || "");
            const typeStr = String(node.type || "");
            if (title.includes("IMG to pixels") || typeStr.includes("IMG to pixels")) return null;

            function nodeMatchesKey(key, title, typeStr) {
                if (key === "Math") return title === "Math" || typeStr === "Math" || typeStr.endsWith("/Math");
                if (key === "Text") return title === "Text" || typeStr === "Text" || typeStr.endsWith("/Text");
                if (key === "Text on Path") return title === "Text on Path" || typeStr === "Text on Path" || typeStr.endsWith("/Text on Path");
                if (key === "Bezier Curve") return title.includes("Bezier") || title.includes("Curva") || typeStr.includes("Bezier");
                if (key === "Time to Frame") return title === "Time to Frame" || title === "Tiempo a Frame" || typeStr === "Time/Time to Frame" || typeStr === "Time to Frame";
                if (key === "Frame to Time") return title === "Frame to Time" || title === "Frame a Tiempo" || typeStr === "Time/Frame to Time" || typeStr === "Frame to Time";
                if (key === "Move Tag") return title === "Move Tag" || title === "Mover Tags" || typeStr.endsWith("/Move Tag") || typeStr === "Move Tag";
                return title === key || typeStr === key || typeStr.endsWith("/" + key);
            }

            for (const key in DYNAMIC_NODE_MODES) {
                if (nodeMatchesKey(key, title, typeStr)) {
                    const entry = DYNAMIC_NODE_MODES[key];
                    const modeList = Array.isArray(entry) ? entry : (entry.modes || []);
                    const propKey = Array.isArray(entry) ? "mode" : (entry.propKey || "mode");
                    const currentFull = String(node.properties ? (node.properties[propKey] || modeList[0].full) : modeList[0].full);
                    
                    let foundIdx = modeList.findIndex(m => m.full === currentFull || m.short === currentFull);
                    if (foundIdx < 0) foundIdx = 0;

                    const res = {
                        key: key,
                        propKey: propKey,
                        modeList: modeList,
                        currentIdx: foundIdx,
                        currentShort: modeList[foundIdx].short,
                        currentFull: modeList[foundIdx].full,
                        isSlicer: key === "Slicer",
                        isShapesLib: key === "Library"
                    };

                    if (!Array.isArray(entry) && entry.secondaryPropKey && (entry.secondaryModes || entry.secondaryModesMap)) {
                        const secProp = entry.secondaryPropKey;
                        const secModesMap = entry.secondaryModesMap;
                        const secModes = secModesMap ? (secModesMap[res.currentFull] || secModesMap[res.currentShort] || Object.values(secModesMap)[0]) : entry.secondaryModes;
                        const secFull = String(node.properties ? (node.properties[secProp] || secModes[0].full) : secModes[0].full);
                        let secIdx = secModes.findIndex(m => m.full === secFull || m.short === secFull);
                        if (secIdx < 0) secIdx = 0;
                        res.secondaryPropKey = secProp;
                        res.secondaryModes = secModes;
                        res.secondaryIdx = secIdx;
                        res.secondaryShort = secModes[secIdx].short;
                        res.secondaryFull = secModes[secIdx].full;
                    }

                    if (!Array.isArray(entry) && entry.tertiaryPropKey && entry.tertiaryModes) {
                        const terProp = entry.tertiaryPropKey;
                        const terModes = entry.tertiaryModes;
                        const terFull = String(node.properties ? (node.properties[terProp] || terModes[0].full) : terModes[0].full);
                        let terIdx = terModes.findIndex(m => m.full === terFull || m.short === terFull);
                        if (terIdx < 0) terIdx = 0;
                        res.tertiaryPropKey = terProp;
                        res.tertiaryModes = terModes;
                        res.tertiaryIdx = terIdx;
                        res.tertiaryShort = terModes[terIdx].short;
                        res.tertiaryFull = terModes[terIdx].full;
                    }

                    return res;
                }
            }
            return null;
        }

        const MODE_INPUT_SPECS = {
            "Animation": {
                "DEFAULT": [
                    { name: "Shape list", default: "", property: "frames" },
                    { name: "Step (ms)", default: "41.7", property: "step_ms" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "fbf": [
                    { name: "Shape list", default: "", property: "frames" },
                    { name: "Step (ms)", default: "41.7", property: "step_ms" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "alpha": [
                    { name: "Shape list", default: "", property: "frames" },
                    { name: "Step (ms)", default: "41.7", property: "step_ms" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Alpha Tag", default: "\\alpha", property: "alpha_tag", type: "button" }
                ]
            },
            "Functions/Animation": {
                "DEFAULT": [
                    { name: "Shape list", default: "", property: "frames" },
                    { name: "Step (ms)", default: "41.7", property: "step_ms" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "fbf": [
                    { name: "Shape list", default: "", property: "frames" },
                    { name: "Step (ms)", default: "41.7", property: "step_ms" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "alpha": [
                    { name: "Shape list", default: "", property: "frames" },
                    { name: "Step (ms)", default: "41.7", property: "step_ms" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Alpha Tag", default: "\\alpha", property: "alpha_tag", type: "button" }
                ]
            },
            "Time to Frame": {
                "DEFAULT": [
                    { name: "Time (ms)", default: "0", property: "time" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Custom": [
                    { name: "Time (ms)", default: "0", property: "time" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Start Time": [
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "End Time": [
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Duration": [
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ]
            },
            "Time/Time to Frame": {
                "DEFAULT": [
                    { name: "Time (ms)", default: "0", property: "time" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Custom": [
                    { name: "Time (ms)", default: "0", property: "time" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Start Time": [
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "End Time": [
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Duration": [
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ]
            },
            "Frame to Time": {
                "DEFAULT": [
                    { name: "Frames (f)", default: "1", property: "frames" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Custom": [
                    { name: "Frames (f)", default: "1", property: "frames" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Iterator": [
                    { name: "Iterator", default: "", property: "iter_name" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Iter": [
                    { name: "Iterator", default: "", property: "iter_name" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Loop (j)": [
                    { name: "Iterator", default: "", property: "iter_name" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Loop (J)": [
                    { name: "Iterator", default: "", property: "iter_name" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Index (i)": [
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ]
            },
            "Time/Frame to Time": {
                "DEFAULT": [
                    { name: "Frames (f)", default: "1", property: "frames" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Custom": [
                    { name: "Frames (f)", default: "1", property: "frames" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Iterator": [
                    { name: "Iterator", default: "", property: "iter_name" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Iter": [
                    { name: "Iterator", default: "", property: "iter_name" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Loop (j)": [
                    { name: "Iterator", default: "", property: "iter_name" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Loop (J)": [
                    { name: "Iterator", default: "", property: "iter_name" },
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ],
                "Index (i)": [
                    { name: "Frame Dur (ms)", default: "", property: "frame_dur" }
                ]
            },
            "Math": {
                "Add": [{ name: "A", default: "0" }, { name: "B", default: "0" }],
                "Subtract": [{ name: "A", default: "0" }, { name: "B", default: "0" }],
                "Multiply": [{ name: "A", default: "1" }, { name: "B", default: "1" }],
                "Divide": [{ name: "A", default: "0" }, { name: "B", default: "1" }],
                "Modulo": [{ name: "A", default: "0" }, { name: "B", default: "1" }],
                "Power": [{ name: "A", default: "0" }, { name: "B", default: "1" }],
                "Absolute": [{ name: "A", default: "0" }],
                "Negative": [{ name: "A", default: "0" }],
                "Round": [{ name: "A", default: "0" }],
                "Floor": [{ name: "A", default: "0" }],
                "Ceil": [{ name: "A", default: "0" }],
                "Sin": [{ name: "A", default: "0" }],
                "Cos": [{ name: "A", default: "0" }],
                "Tan": [{ name: "A", default: "0" }],
                "ArcSin": [{ name: "A", default: "0" }],
                "ArcCos": [{ name: "A", default: "0" }],
                "ArcTan": [{ name: "A", default: "0" }],
                "ArcTan2": [{ name: "Y", default: "0" }, { name: "X", default: "1" }],
                "Radians": [{ name: "Degrees", default: "0" }],
                "Degrees": [{ name: "Radians", default: "0" }],
                "EaseIn": [{ name: "t", default: "0" }],
                "EaseOut": [{ name: "t", default: "0" }],
                "EaseInOut": [{ name: "t", default: "0" }],
                "CubicIn": [{ name: "t", default: "0" }],
                "CubicOut": [{ name: "t", default: "0" }],
                "Exponential": [{ name: "t", default: "0" }],
                "Elastic": [{ name: "t", default: "0" }],
                "Bounce": [{ name: "t", default: "0" }],
                "Back": [{ name: "t", default: "0" }],
                "Sine": [{ name: "t", default: "0" }, { name: "Frequency", default: "1.0" }, { name: "Amplitude", default: "1.0" }, { name: "Offset", default: "0" }],
                "Square": [{ name: "t", default: "0" }, { name: "Frequency", default: "1.0" }, { name: "Amplitude", default: "1.0" }, { name: "Offset", default: "0" }],
                "Triangle": [{ name: "t", default: "0" }, { name: "Frequency", default: "1.0" }, { name: "Amplitude", default: "1.0" }, { name: "Offset", default: "0" }],
                "Sawtooth": [{ name: "t", default: "0" }, { name: "Frequency", default: "1.0" }, { name: "Amplitude", default: "1.0" }, { name: "Offset", default: "0" }],
                "Clamp": [{ name: "Value", default: "0" }, { name: "Min", default: "0" }, { name: "Max", default: "1" }],
                "Lerp": [{ name: "A", default: "0" }, { name: "B", default: "1" }, { name: "t", default: "0.5" }],
                "Min": [{ name: "A", default: "0" }, { name: "B", default: "0" }],
                "Max": [{ name: "A", default: "0" }, { name: "B", default: "0" }],
                "Random": [{ name: "Min", default: "0" }, { name: "Max", default: "1" }, { name: "Seed", default: "" }],
                "MapRange": [{ name: "Value", default: "0" }, { name: "MinIn", default: "0" }, { name: "MaxIn", default: "1" }, { name: "MinOut", default: "0" }, { name: "MaxOut", default: "100" }]
            },
            "Basics/Math": {
                "Add": [{ name: "A", default: "0" }, { name: "B", default: "0" }],
                "Subtract": [{ name: "A", default: "0" }, { name: "B", default: "0" }],
                "Multiply": [{ name: "A", default: "1" }, { name: "B", default: "1" }],
                "Divide": [{ name: "A", default: "0" }, { name: "B", default: "1" }],
                "Modulo": [{ name: "A", default: "0" }, { name: "B", default: "1" }],
                "Power": [{ name: "A", default: "0" }, { name: "B", default: "1" }],
                "Absolute": [{ name: "A", default: "0" }],
                "Negative": [{ name: "A", default: "0" }],
                "Round": [{ name: "A", default: "0" }],
                "Floor": [{ name: "A", default: "0" }],
                "Ceil": [{ name: "A", default: "0" }],
                "Sin": [{ name: "A", default: "0" }],
                "Cos": [{ name: "A", default: "0" }],
                "Tan": [{ name: "A", default: "0" }],
                "ArcSin": [{ name: "A", default: "0" }],
                "ArcCos": [{ name: "A", default: "0" }],
                "ArcTan": [{ name: "A", default: "0" }],
                "ArcTan2": [{ name: "Y", default: "0" }, { name: "X", default: "1" }],
                "Radians": [{ name: "Degrees", default: "0" }],
                "Degrees": [{ name: "Radians", default: "0" }],
                "EaseIn": [{ name: "t", default: "0" }],
                "EaseOut": [{ name: "t", default: "0" }],
                "EaseInOut": [{ name: "t", default: "0" }],
                "CubicIn": [{ name: "t", default: "0" }],
                "CubicOut": [{ name: "t", default: "0" }],
                "Exponential": [{ name: "t", default: "0" }],
                "Elastic": [{ name: "t", default: "0" }],
                "Bounce": [{ name: "t", default: "0" }],
                "Back": [{ name: "t", default: "0" }],
                "Sine": [{ name: "t", default: "0" }, { name: "Frequency", default: "1.0" }, { name: "Amplitude", default: "1.0" }, { name: "Offset", default: "0" }],
                "Square": [{ name: "t", default: "0" }, { name: "Frequency", default: "1.0" }, { name: "Amplitude", default: "1.0" }, { name: "Offset", default: "0" }],
                "Triangle": [{ name: "t", default: "0" }, { name: "Frequency", default: "1.0" }, { name: "Amplitude", default: "1.0" }, { name: "Offset", default: "0" }],
                "Sawtooth": [{ name: "t", default: "0" }, { name: "Frequency", default: "1.0" }, { name: "Amplitude", default: "1.0" }, { name: "Offset", default: "0" }],
                "Clamp": [{ name: "Value", default: "0" }, { name: "Min", default: "0" }, { name: "Max", default: "1" }],
                "Lerp": [{ name: "A", default: "0" }, { name: "B", default: "1" }, { name: "t", default: "0.5" }],
                "Min": [{ name: "A", default: "0" }, { name: "B", default: "0" }],
                "Max": [{ name: "A", default: "0" }, { name: "B", default: "0" }],
                "Random": [{ name: "Min", default: "0" }, { name: "Max", default: "1" }, { name: "Seed", default: "" }],
                "MapRange": [{ name: "Value", default: "0" }, { name: "MinIn", default: "0" }, { name: "MaxIn", default: "1" }, { name: "MinOut", default: "0" }, { name: "MaxOut", default: "100" }]
            },
            "Text": {
                "Strip Tags": [{ name: "Text", default: "" }],
                "Upper": [{ name: "Text", default: "" }],
                "Lower": [{ name: "Text", default: "" }],
                "Replace": [{ name: "Text", default: "" }, { name: "Search", default: "" }, { name: "Replace With", default: "" }],
                "Substring": [{ name: "Text", default: "" }, { name: "Start", default: "0" }, { name: "Length", default: "10" }],
                "Length": [{ name: "Text", default: "" }],
                "Contains": [{ name: "Text", default: "" }, { name: "Search", default: "" }],
                "Kana": [
                    { name: "Text", default: "", property: "text" },
                    { name: "Kana Mode", default: "Romaji to Hiragana", property: "mode", type: "button", no_socket: true }
                ],
                "Romaji to Karaoke": [
                    { name: "Text", default: "", property: "text" },
                    { name: "K Mode", default: "k", property: "k_mode", type: "button", no_socket: true },
                    { name: "Duration (cs)", default: "", property: "duration" }
                ],
                "To Kara": [
                    { name: "Text", default: "", property: "text" },
                    { name: "K Mode", default: "k", property: "k_mode", type: "button", no_socket: true },
                    { name: "Duration (cs)", default: "", property: "duration" }
                ]
            },
            "Library": {
                "DEFAULT": []
            },
            "Stroke": {
                "DEFAULT": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Width (px)", default: "4.0", property: "width" },
                    { name: "Vertex Mode", default: "Round", property: "join_mode", type: "button", no_socket: true },
                    { name: "Cap Mode", default: "Bezier", property: "cap_mode", type: "button", no_socket: true }
                ]
            },
            "IMG to Shape": {
                "DEFAULT": [
                    { name: "Image Path", default: "", property: "image_path" },
                    { name: "Frame (j)", default: "1", property: "frame_idx" },
                    { name: "Threshold", default: "128", property: "threshold" },
                    { name: "Tolerance", default: "1.0", property: "tolerance" },
                    { name: "Smoothing", default: "1.0", property: "alphamax" },
                    { name: "Optimization", default: "0.2", property: "opttoler" },
                    { name: "Scale Out", default: "1.0", property: "out_scale" },
                    { name: "Width Out", default: "0.0", property: "out_w" },
                    { name: "Height Out", default: "0.0", property: "out_h" },
                    { name: "Offset X", default: "0.0", property: "offset_x" },
                    { name: "Offset Y", default: "0.0", property: "offset_y" },
                    { name: "Image Scale", default: "1.0", property: "img_scale" },
                    { name: "Binarize Mode", default: "luminance", property: "bin_mode", type: "button" }
                ]
            },
            "Waveform": {
                "DEFAULT": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Thickness (px)", default: "2", property: "thickness" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "oscilloscope": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Thickness (px)", default: "2", property: "thickness" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Oscilloscope": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Thickness (px)", default: "2", property: "thickness" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "fftbars": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples / Bars", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Min Hz", default: "20", property: "min_hz" },
                    { name: "Max Hz", default: "16000", property: "max_hz" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "FFT Bars": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples / Bars", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Min Hz", default: "20", property: "min_hz" },
                    { name: "Max Hz", default: "16000", property: "max_hz" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "filledwave": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Filled Wave": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "radial": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "400", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Min Hz", default: "20", property: "min_hz" },
                    { name: "Max Hz", default: "16000", property: "max_hz" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Circular Radial": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "400", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Min Hz", default: "20", property: "min_hz" },
                    { name: "Max Hz", default: "16000", property: "max_hz" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "points": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Thickness (px)", default: "2", property: "thickness" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Points": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Width (px)", default: "400", property: "width" },
                    { name: "Height (px)", default: "60", property: "height" },
                    { name: "Samples", default: "32", property: "samples" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Thickness (px)", default: "2", property: "thickness" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ]
            },
            "Modulator": {
                "DEFAULT": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "rms": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "RMS (Volume)": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "peak": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Peak": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "bass": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Bass (20-250Hz)": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "mids": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Mids (250-4kHz)": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "highs": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Highs (4-16kHz)": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "custom": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Min Hz", default: "20", property: "min_hz" },
                    { name: "Max Hz", default: "250", property: "max_hz" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ],
                "Custom Band": [
                    { name: "Audio Path", default: "", property: "audio_path" },
                    { name: "Tag", default: "fscy", property: "tag_name" },
                    { name: "Min Val", default: "100", property: "min_val" },
                    { name: "Max Val", default: "160", property: "max_val" },
                    { name: "Gain", default: "1.0", property: "gain" },
                    { name: "Step ms", default: "41.7", property: "step_ms" },
                    { name: "Smoothing", default: "0.2", property: "smoothing" },
                    { name: "Min Hz", default: "20", property: "min_hz" },
                    { name: "Max Hz", default: "250", property: "max_hz" },
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" }
                ]
            },
            "Benchmark Math": {
                "DEFAULT": [
                    { name: "Iterations", default: "10000", property: "iterations" }
                ]
            },
            "Text on Path": {
                "DEFAULT": [
                    { name: "Path / Shape", default: "", property: "shape" },
                    { name: "Offset", default: "0", property: "offset" },
                    { name: "Extra Angle", default: "0", property: "extra_angle" },
                    { name: "Subdivs", default: "30", property: "subdivs" }
                ]
            },
            "Ipol": {
                "DEFAULT": [
                    { name: "Duration (ms)", default: "syl.duration", property: "dur" },
                    { name: "Points / Values", default: "0, 100", property: "points" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ]
            },
            "Synced": {
                "DEFAULT": [
                    { name: "Mode:", default: "order", property: "mode", type: "combo", values: ["order", "style", "actor", "layer", "effect"] },
                    { name: "Constant", default: "0", property: "progression_const" },
                    { name: "Fade (ms)", default: "300", property: "fade_dur" },
                    { name: "Max Extra", default: "2000", property: "max_added_time" },
                    { name: "Delay Line", default: "250", property: "delay_ms" },
                    { name: "Threshold", default: "3000", property: "max_gap_threshold" }
                ]
            },
            "Time/Synced": {
                "DEFAULT": [
                    { name: "Mode:", default: "order", property: "mode", type: "combo", values: ["order", "style", "actor", "layer", "effect"] },
                    { name: "Constant", default: "0", property: "progression_const" },
                    { name: "Fade (ms)", default: "300", property: "fade_dur" },
                    { name: "Max Extra", default: "2000", property: "max_added_time" },
                    { name: "Delay Line", default: "250", property: "delay_ms" },
                    { name: "Threshold", default: "3000", property: "max_gap_threshold" }
                ]
            },
            "Concentric Borders": {
                "DEFAULT": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Base Mode", default: "Hollow (borders)", property: "mode", type: "button" },
                    { name: "Max Rings", default: "5", property: "loop_count" },
                    { name: "Separation (px)", default: "5", property: "separation" },
                    { name: "Overlap (px)", default: "0.5", property: "overlap" },
                    { name: "Anchor", default: "relative", property: "anchor", type: "button" }
                ]
            },
            "Clip Gradient": {
                "DEFAULT": [
                    { name: "Cols", default: "5", property: "cols", visualRow: 0 },
                    { name: "Rows", default: "1", property: "rows", visualRow: 1 },
                    { name: "Angle (°)", default: "0", property: "angle", visualRow: 2 },
                    { name: "Pad Top", default: "0", property: "pad_top", no_socket: true, visualRow: 3, crossCol: "center" },
                    { name: "Pad Left", default: "0", property: "pad_left", no_socket: true, visualRow: 4, crossCol: "left" },
                    { name: "Padding (px)", default: "0", property: "padding", no_socket: true, visualRow: 4, crossCol: "center" },
                    { name: "Pad Right", default: "0", property: "pad_right", no_socket: true, visualRow: 4, crossCol: "right" },
                    { name: "Pad Bottom", default: "0", property: "pad_bottom", no_socket: true, visualRow: 5, crossCol: "center" },
                    { name: "Overlap (px)", default: "0.5", property: "overlap", visualRow: 6 },
                    { name: "Order", default: "79", property: "order", type: "button", visualRow: 7 }
                ]
            },
            "Functions/Clip Gradient": {
                "DEFAULT": [
                    { name: "Cols", default: "5", property: "cols", visualRow: 0 },
                    { name: "Rows", default: "1", property: "rows", visualRow: 1 },
                    { name: "Angle (°)", default: "0", property: "angle", visualRow: 2 },
                    { name: "Pad Top", default: "0", property: "pad_top", no_socket: true, visualRow: 3, crossCol: "center" },
                    { name: "Pad Left", default: "0", property: "pad_left", no_socket: true, visualRow: 4, crossCol: "left" },
                    { name: "Padding (px)", default: "0", property: "padding", no_socket: true, visualRow: 4, crossCol: "center" },
                    { name: "Pad Right", default: "0", property: "pad_right", no_socket: true, visualRow: 4, crossCol: "right" },
                    { name: "Pad Bottom", default: "0", property: "pad_bottom", no_socket: true, visualRow: 5, crossCol: "center" },
                    { name: "Overlap (px)", default: "0.5", property: "overlap", visualRow: 6 },
                    { name: "Order", default: "79", property: "order", type: "button", visualRow: 7 }
                ]
            },
            "Interpolator": {
                "DEFAULT": [
                    { name: "Iterator", default: "i", property: "iterator" },
                    { name: "Total", default: "N", property: "total" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "V1", default: "0", property: "v1" },
                    { name: "V2", default: "1", property: "v2" }
                ]
            },
            "Interpolador": {
                "DEFAULT": [
                    { name: "Iterator", default: "i", property: "iterator" },
                    { name: "Total", default: "N", property: "total" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "V1", default: "0", property: "v1" },
                    { name: "V2", default: "1", property: "v2" }
                ]
            },
            "Functions/Interpolator": {
                "DEFAULT": [
                    { name: "Iterator", default: "i", property: "iterator" },
                    { name: "Total", default: "N", property: "total" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "V1", default: "0", property: "v1" },
                    { name: "V2", default: "1", property: "v2" }
                ]
            },
            "Main Loop": {
                "DEFAULT": []
            },
            "Loops/Main Loop": {
                "DEFAULT": []
            },
            "MaxLoop": {
                "DEFAULT": [
                    { name: "Loop In", default: "", property: "loop_in" },
                    { name: "Start", default: "start_time", property: "start_time" },
                    { name: "End", default: "end_time", property: "end_time" }
                ],
                "normal": [
                    { name: "Loop In", default: "", property: "loop_in" }
                ],
                "fbf": [
                    { name: "Loop In", default: "", property: "loop_in" },
                    { name: "Start", default: "start_time", property: "start_time" },
                    { name: "End", default: "end_time", property: "end_time" }
                ]
            },
            "Loops/MaxLoop": {
                "DEFAULT": [
                    { name: "Loop In", default: "", property: "loop_in" },
                    { name: "Start", default: "start_time", property: "start_time" },
                    { name: "End", default: "end_time", property: "end_time" }
                ],
                "normal": [
                    { name: "Loop In", default: "", property: "loop_in" }
                ],
                "fbf": [
                    { name: "Loop In", default: "", property: "loop_in" },
                    { name: "Start", default: "start_time", property: "start_time" },
                    { name: "End", default: "end_time", property: "end_time" }
                ]
            },
            "Module": {
                "DEFAULT": [
                    { name: "Iterator (i)", default: "i", property: "iter" },
                    { name: "Total (N)", default: "N", property: "total" },
                    { name: "Sub-step (m)", default: "0", property: "sub_m" }
                ]
            },
            "Loops/Module": {
                "DEFAULT": [
                    { name: "Iterator (i)", default: "i", property: "iter" },
                    { name: "Total (N)", default: "N", property: "total" },
                    { name: "Sub-step (m)", default: "0", property: "sub_m" }
                ]
            },
            "Sys Var": {
                "DEFAULT": []
            },
            "Variables/Sys Var": {
                "DEFAULT": []
            },
            "Get Var": {
                "DEFAULT": []
            },
            "Variables/Get Var": {
                "DEFAULT": []
            },
            "Define Vars": {
                "DEFAULT": [
                    { name: "In", default: "", property: "in" }
                ]
            },
            "Variables/Define Vars": {
                "DEFAULT": [
                    { name: "In", default: "", property: "in" }
                ]
            },
            "Memory": {
                "DEFAULT": [
                    { name: "Key", default: "ref", property: "key" },
                    { name: "Value", default: "", property: "value" }
                ]
            },
            "Variables/Memory": {
                "DEFAULT": [
                    { name: "Key", default: "ref", property: "key" },
                    { name: "Value", default: "", property: "value" }
                ]
            },
            "MultiTag": {
                "DEFAULT": [
                    { name: "X", default: "0", property: "x" },
                    { name: "Y", default: "0", property: "y" }
                ]
            },
            "Basics/MultiTag": {
                "DEFAULT": [
                    { name: "X", default: "0", property: "x" },
                    { name: "Y", default: "0", property: "y" }
                ]
            },
            "MultiRandom": {
                "DEFAULT": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "R": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rs": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rr": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rc": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rd": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rm": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rds": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rcs": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rms": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Re": [
                    { name: "Options", default: "opc1, opc2, opc3", property: "options" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rfake": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Counter", default: "i", property: "counter" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rcolor": [
                    { name: "Color 1", default: "&HFFFFFF&", property: "min" },
                    { name: "Color 2", default: "&H000000&", property: "max" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "R2d": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rbool": [
                    { name: "Probability (%)", default: "50", property: "min" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rstep": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "360", property: "max" },
                    { name: "Step", default: "45", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ]
            },
            "Basics/MultiRandom": {
                "DEFAULT": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "R": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rs": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rr": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rc": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rd": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rm": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rds": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rcs": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rms": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Re": [
                    { name: "Options", default: "opc1, opc2, opc3", property: "options" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rfake": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Counter", default: "i", property: "counter" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rcolor": [
                    { name: "Color 1", default: "&HFFFFFF&", property: "min" },
                    { name: "Color 2", default: "&H000000&", property: "max" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "R2d": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "100", property: "max" },
                    { name: "Step", default: "", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rbool": [
                    { name: "Probability (%)", default: "50", property: "min" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ],
                "Rstep": [
                    { name: "Min", default: "0", property: "min" },
                    { name: "Max", default: "360", property: "max" },
                    { name: "Step", default: "45", property: "step" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Iterator", default: "", property: "iterator" }
                ]
            },
            "Manipulator": {
                "Scale": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Scale X", default: "100", property: "scale_x" },
                    { name: "Scale Y", default: "100", property: "scale_y" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Borders": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Offset (px)", default: "2.0", property: "offset_border" }
                ],
                "Deform": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Offset X", default: "0", property: "offset_x" },
                    { name: "Offset Y", default: "0", property: "offset_y" },
                    { name: "Def Factor", default: "100", property: "factor" }
                ],
                "Position": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Offset X", default: "0", property: "offset_x" },
                    { name: "Offset Y", default: "0", property: "offset_y" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Redraw": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Density / Step", default: "2.0", property: "density" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "3D Rotate": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Rotate X", default: "0", property: "angle_x" },
                    { name: "Rotate Y", default: "0", property: "angle_y" },
                    { name: "Rotate Z", default: "0", property: "angle_z" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Reflect": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Axis", default: "y", property: "axis", type: "button" },
                    { name: "Offset X", default: "0", property: "offset_x" },
                    { name: "Offset Y", default: "0", property: "offset_y" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Matrix": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Scale X", default: "100", property: "scale_x" },
                    { name: "Scale Y", default: "100", property: "scale_y" },
                    { name: "Skew X", default: "0", property: "skew_x" },
                    { name: "Skew Y", default: "0", property: "skew_y" },
                    { name: "Rotate X", default: "0", property: "angle_x" },
                    { name: "Rotate Y", default: "0", property: "angle_y" },
                    { name: "Rotate Z", default: "0", property: "angle_z" },
                    { name: "Offset X", default: "0", property: "offset_x" },
                    { name: "Offset Y", default: "0", property: "offset_y" },
                    { name: "Offset Border", default: "0", property: "offset_border" },
                    { name: "Axis", default: "none", property: "axis", type: "button" },
                    { name: "Density", default: "0", property: "density" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ]
            },
            "Filter": {
                "Vertices": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Expr X", default: "x", property: "expr_x" },
                    { name: "Expr Y", default: "y", property: "expr_y" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Subdivs", default: "0", property: "subdivs" }
                ],
                "Group": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Rotation Step", default: "0", property: "rot_step" },
                    { name: "Scale Step", default: "100", property: "scale_step" },
                    { name: "Offset X", default: "0", property: "offset_x" },
                    { name: "Offset Y", default: "0", property: "offset_y" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Noise": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Radius X", default: "5.0", property: "radius_x" },
                    { name: "Radius Y", default: "5.0", property: "radius_y" },
                    { name: "Subdivs", default: "2.0", property: "subdivs" },
                    { name: "Seed", default: "0", property: "seed" }
                ]
            },
            "Transform": {
                "Inflate": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Ratio", default: "1.0", property: "ratio" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Skew": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Angle X", default: "0", property: "angle_x" },
                    { name: "Angle Y", default: "0", property: "angle_y" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Round Corners": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Radius (px)", default: "10.0", property: "radius" },
                    { name: "Corner Mode", default: "Round", property: "corner_mode", type: "button", no_socket: true },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Flexor": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Curve / Angle", default: "30", property: "curve" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Distort": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Target Shape", default: "", property: "target_shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Energy", default: "0.35", property: "energy" },
                    { name: "Step (px)", default: "0", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ],
                "Distort2": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Mid Shape", default: "", property: "mid_shape" },
                    { name: "Target Shape", default: "", property: "target_shape" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Energy", default: "0.35", property: "energy" },
                    { name: "Step (px)", default: "0", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" }
                ]
            },
            "Multi": {
                "Concentric Squares": [
                    { name: "Size", default: "100.0", property: "size" },
                    { name: "Thickness (px)", default: "4", property: "px" },
                    { name: "Separation", default: "0.0", property: "separation" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "normal", property: "order", type: "button", order_modes: ORDER_MODES_MULTI_CONCENTRIC },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Diagonal Stripes": [
                    { name: "Width", default: "70.0", property: "width" },
                    { name: "Height", default: "50.0", property: "height" },
                    { name: "Stripe Thickness", default: "6", property: "px" },
                    { name: "Separation", default: "0.0", property: "separation" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button", order_modes: ORDER_MODES_MULTI_STRIPES },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Concentric Rings": [
                    { name: "Base Shape", default: "", property: "shape" },
                    { name: "Size", default: "100.0", property: "size" },
                    { name: "Border Thickness", default: "4", property: "bord" },
                    { name: "Separation", default: "0.0", property: "separation" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "normal", property: "order", type: "button", order_modes: ORDER_MODES_MULTI_CONCENTRIC },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Polygonal Mosaic": [
                    { name: "Size", default: "64.0", property: "size" },
                    { name: "Sides", default: "6", property: "sides" },
                    { name: "Rings", default: "1", property: "rings" },
                    { name: "Layers (N)", default: "25", property: "n_layers" },
                    { name: "Separation", default: "0.0", property: "separation" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "Normal", property: "order", type: "button" },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Multi-Shape Mosaic": [
                    { name: "Shapes", default: "", property: "shape" },
                    { name: "Width", default: "60.0", property: "width" },
                    { name: "Height", default: "50.0", property: "height" },
                    { name: "Spacing X", default: "0.0", property: "dx" },
                    { name: "Spacing Y", default: "0.0", property: "dy" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "Normal", property: "order", type: "button" },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Segmented Border": [
                    { name: "Base Shape", default: "", property: "shape" },
                    { name: "Width", default: "104.0", property: "width" },
                    { name: "Height", default: "104.0", property: "height" },
                    { name: "Border Thickness", default: "4.0", property: "bord" },
                    { name: "Separation", default: "0.0", property: "separation" },
                    { name: "Segment Length", default: "20.0", property: "length" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "normal", property: "order", type: "button", order_modes: ORDER_MODES_MULTI_BORDER },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Radial Rosette": [
                    { name: "Slices", default: "12", property: "parts" },
                    { name: "Outer Radius", default: "50.0", property: "r_out" },
                    { name: "Inner Radius", default: "0.0", property: "r_in" },
                    { name: "Separation", default: "0.0", property: "separation" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "cw", property: "order", type: "button", order_modes: ORDER_MODES_MULTI_ROSETTE },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Tunnel / Cascade": [
                    { name: "Base Shape", default: "", property: "shape" },
                    { name: "Start Size", default: "100.0", property: "size1" },
                    { name: "End Size", default: "10.0", property: "size2" },
                    { name: "Loop Steps", default: "8", property: "loop" },
                    { name: "Separation", default: "0.0", property: "separation" },
                    { name: "Angle", default: "0.0", property: "angle" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "normal", property: "order", type: "button", order_modes: ORDER_MODES_MULTI_TUNNEL },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Banner": [
                    { name: "Width", default: "200.0", property: "width" },
                    { name: "Height", default: "50.0", property: "height" },
                    { name: "Terminal", default: "Arrow", property: "tip_style", type: "button" },
                    { name: "Fold Width", default: "0.0", property: "fold_w" },
                    { name: "Border", default: "0.0", property: "bord" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Gear": [
                    { name: "Teeth Count", default: "8", property: "parts" },
                    { name: "Outer Radius", default: "60.0", property: "r_out" },
                    { name: "Root Radius", default: "45.0", property: "r_in" },
                    { name: "Hole Radius", default: "15.0", property: "r_hole" },
                    { name: "Tooth Slant", default: "0.35", property: "slant" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Tags", default: "", property: "tags" }
                ]
            },
            "Walker": {
                "DEFAULT": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Progress (t)", default: "1.0", property: "progress" },
                    { name: "Start (t)", default: "0.0", property: "start_t" },
                    { name: "Subdivs", default: "30", property: "subdivs" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ]
            },
            "Shape/Walker": {
                "DEFAULT": [
                    { name: "Shape / Text", default: "", property: "shape" },
                    { name: "Progress (t)", default: "1.0", property: "progress" },
                    { name: "Start (t)", default: "0.0", property: "start_t" },
                    { name: "Subdivs", default: "30", property: "subdivs" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ]
            },
            "Color Gradient": {
                "DEFAULT": [
                    { name: "Progress (0-1)", default: "char.i / char.n", property: "prog" },
                    { name: "Color List", default: "#95E648,#3E750C,#ED38CA", property: "colors_str" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "Tag", default: "\\1c", property: "tag_type", type: "button", no_socket: true }
                ]
            },
            "Functions/Color Gradient": {
                "DEFAULT": [
                    { name: "Progress (0-1)", default: "char.i / char.n", property: "prog" },
                    { name: "Color List", default: "#95E648,#3E750C,#ED38CA", property: "colors_str" },
                    { name: "Total (N)", default: "1", property: "total" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "Tag", default: "\\1c", property: "tag_type", type: "button", no_socket: true }
                ]
            },
            "Tag Manipulator": {
                "invert": [
                    { name: "Tags In", default: "", property: "tags" }
                ],
                "reset": [
                    { name: "Tags In", default: "", property: "tags" }
                ],
                "extractor": [
                    { name: "Tags In", default: "", property: "tags" },
                    { name: "Target Tag", default: "frz", property: "target_tag" }
                ],
                "Invert": [
                    { name: "Tags In", default: "", property: "tags" }
                ],
                "Reset": [
                    { name: "Tags In", default: "", property: "tags" }
                ],
                "Extractor": [
                    { name: "Tags In", default: "", property: "tags" },
                    { name: "Target Tag", default: "frz", property: "target_tag" }
                ],
                "DEFAULT": [
                    { name: "Tags In", default: "", property: "tags" }
                ]
            },
            "Functions/Tag Manipulator": {
                "invert": [
                    { name: "Tags In", default: "", property: "tags" }
                ],
                "reset": [
                    { name: "Tags In", default: "", property: "tags" }
                ],
                "extractor": [
                    { name: "Tags In", default: "", property: "tags" },
                    { name: "Target Tag", default: "frz", property: "target_tag" }
                ],
                "Invert": [
                    { name: "Tags In", default: "", property: "tags" }
                ],
                "Reset": [
                    { name: "Tags In", default: "", property: "tags" }
                ],
                "Extractor": [
                    { name: "Tags In", default: "", property: "tags" },
                    { name: "Target Tag", default: "frz", property: "target_tag" }
                ],
                "DEFAULT": [
                    { name: "Tags In", default: "", property: "tags" }
                ]
            },
            "Retime": {
                "DEFAULT": [
                    { name: "Tags or \\t", default: "", property: "tags" },
                    { name: "Offset In (ms)", default: "0", property: "offset_in" },
                    { name: "Offset Out (ms)", default: "0", property: "offset_out" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ]
            },
            "Time/Retime": {
                "DEFAULT": [
                    { name: "Tags or \\t", default: "", property: "tags" },
                    { name: "Offset In (ms)", default: "0", property: "offset_in" },
                    { name: "Offset Out (ms)", default: "0", property: "offset_out" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ]
            },
            "Synced": {
                "DEFAULT": [
                    { name: "Constant", default: "0", property: "progression_const" },
                    { name: "Fade (ms)", default: "300", property: "fade_dur" },
                    { name: "Max Extra", default: "2000", property: "max_added_time" },
                    { name: "Delay Line", default: "250", property: "delay_ms" },
                    { name: "Threshold", default: "3000", property: "max_gap_threshold" }
                ]
            },
            "Time/Synced": {
                "DEFAULT": [
                    { name: "Constant", default: "0", property: "progression_const" },
                    { name: "Fade (ms)", default: "300", property: "fade_dur" },
                    { name: "Max Extra", default: "2000", property: "max_added_time" },
                    { name: "Delay Line", default: "250", property: "delay_ms" },
                    { name: "Threshold", default: "3000", property: "max_gap_threshold" }
                ]
            },
            "Concatenate": {
                "DEFAULT": [
                    { name: "In1", default: "", property: "In1" },
                    { name: "In2", default: "", property: "In2" }
                ]
            },
            "Bezier Curve": {
                "Cubic 2D": [
                    { name: "Origin", default: "", property: "origin" },
                    { name: "P0", default: "0,0", property: "p0" },
                    { name: "P1", default: "50,100", property: "p1" },
                    { name: "P2", default: "150,100", property: "p2" },
                    { name: "P3", default: "200,0", property: "p3" },
                    { name: "t", default: "0.5", property: "t" },
                    { name: "Subdivs", default: "100", property: "subdivs" }
                ],
                "Quadratic 2D": [
                    { name: "Origin", default: "", property: "origin" },
                    { name: "P0", default: "0,0", property: "p0" },
                    { name: "P1", default: "50,100", property: "p1" },
                    { name: "P2", default: "100,0", property: "p2" },
                    { name: "t", default: "0.5", property: "t" },
                    { name: "Subdivs", default: "100", property: "subdivs" }
                ],
                "N-Degree": [
                    { name: "Origin", default: "", property: "origin" },
                    { name: "Points", default: "0,0; 50,100; 150,100; 200,0", property: "points" },
                    { name: "t", default: "0.5", property: "t" },
                    { name: "Subdivs", default: "100", property: "subdivs" }
                ],
                "Constant Speed": [
                    { name: "Origin", default: "", property: "origin" },
                    { name: "P0", default: "0,0", property: "p0" },
                    { name: "P1", default: "50,100", property: "p1" },
                    { name: "P2", default: "150,100", property: "p2" },
                    { name: "P3", default: "200,0", property: "p3" },
                    { name: "t", default: "0.5", property: "t" },
                    { name: "Subdivs", default: "100", property: "subdivs" }
                ],
                "Shape Contour": [
                    { name: "Origin", default: "", property: "origin" },
                    { name: "Shape", default: "", property: "shape" },
                    { name: "t", default: "0.5", property: "t" },
                    { name: "Subdivs", default: "100", property: "subdivs" }
                ],
                "Subdivide": [
                    { name: "Origin", default: "", property: "origin" },
                    { name: "P0", default: "0,0", property: "p0" },
                    { name: "P1", default: "50,100", property: "p1" },
                    { name: "P2", default: "150,100", property: "p2" },
                    { name: "P3", default: "200,0", property: "p3" },
                    { name: "t", default: "0.5", property: "t" }
                ],
                "Trajectory": [
                    { name: "Origin", default: "", property: "origin" },
                    { name: "Trajectory Mode", default: "Free Wander", property: "traj_mode", type: "button", no_socket: true },
                    { name: "Dist Range", default: "50,120", property: "dist_range" },
                    { name: "Seed", default: "1", property: "seed" },
                    { name: "Loops", default: "8", property: "loops" },
                    { name: "t", default: "0.5", property: "t" }
                ]
            },
            "Tag Oscillator": {
                "DEFAULT": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "wave": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "steps": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "100.0", property: "step_ms" },
                    { name: "Tags", default: "\\1c&HFF0000&,\\1c&H00FF00&,\\1c&H0000FF&", property: "tags" }
                ],
                "noise": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "Wave": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "Pulses": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Duty Cycle", default: "0.5", property: "duty_cycle" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" }
                ],
                "pulses": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Duty Cycle", default: "0.5", property: "duty_cycle" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" }
                ],
                "Flashes": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "100.0", property: "step_ms" },
                    { name: "Tags", default: "\\1c&HFF0000&,\\1c&H00FF00&,\\1c&H0000FF&", property: "tags" }
                ],
                "flashes": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "100.0", property: "step_ms" },
                    { name: "Tags", default: "\\1c&HFF0000&,\\1c&H00FF00&,\\1c&H0000FF&", property: "tags" }
                ],
                "Rhythmic": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Rhythm Pattern", default: "100,50,200,50", property: "rhythm_pattern" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "rhythmic": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Rhythm Pattern", default: "100,50,200,50", property: "rhythm_pattern" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "Custom": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Duty Cycle", default: "", property: "duty_cycle" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "Dilate Step", default: "0.0", property: "dilat_step_ms" },
                    { name: "Dilate Trans", default: "0.0", property: "dilat_trans_ms" },
                    { name: "Seq Offset", default: "0.0", property: "offset_seq_ms" },
                    { name: "Rhythm Pattern", default: "", property: "rhythm_pattern" }
                ],
                "custom": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Duty Cycle", default: "", property: "duty_cycle" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "Dilate Step", default: "0.0", property: "dilat_step_ms" },
                    { name: "Dilate Trans", default: "0.0", property: "dilat_trans_ms" },
                    { name: "Seq Offset", default: "0.0", property: "offset_seq_ms" },
                    { name: "Rhythm Pattern", default: "", property: "rhythm_pattern" }
                ]
            },
            "Functions/Tag Oscillator": {
                "DEFAULT": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "wave": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "steps": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "100.0", property: "step_ms" },
                    { name: "Tags", default: "\\1c&HFF0000&,\\1c&H00FF00&,\\1c&H0000FF&", property: "tags" }
                ],
                "noise": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "Wave": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "Pulses": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Duty Cycle", default: "0.5", property: "duty_cycle" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" }
                ],
                "pulses": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Duty Cycle", default: "0.5", property: "duty_cycle" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" }
                ],
                "Flashes": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "100.0", property: "step_ms" },
                    { name: "Tags", default: "\\1c&HFF0000&,\\1c&H00FF00&,\\1c&H0000FF&", property: "tags" }
                ],
                "flashes": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "100.0", property: "step_ms" },
                    { name: "Tags", default: "\\1c&HFF0000&,\\1c&H00FF00&,\\1c&H0000FF&", property: "tags" }
                ],
                "Rhythmic": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Rhythm Pattern", default: "100,50,200,50", property: "rhythm_pattern" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "rhythmic": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Rhythm Pattern", default: "100,50,200,50", property: "rhythm_pattern" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" }
                ],
                "Custom": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Duty Cycle", default: "", property: "duty_cycle" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "Dilate Step", default: "0.0", property: "dilat_step_ms" },
                    { name: "Dilate Trans", default: "0.0", property: "dilat_trans_ms" },
                    { name: "Seq Offset", default: "0.0", property: "offset_seq_ms" },
                    { name: "Rhythm Pattern", default: "", property: "rhythm_pattern" }
                ],
                "custom": [
                    { name: "Start Time", default: "", property: "start_time" },
                    { name: "End Time", default: "", property: "end_time" },
                    { name: "Step (ms)", default: "200.0", property: "step_ms" },
                    { name: "Trans (ms)", default: "50.0", property: "trans_ms" },
                    { name: "Duty Cycle", default: "", property: "duty_cycle" },
                    { name: "Tags", default: "\\frz30\\fry20,\\frz-20\\fry-20", property: "tags" },
                    { name: "Accel", default: "1.0", property: "accel" },
                    { name: "Dilate Step", default: "0.0", property: "dilat_step_ms" },
                    { name: "Dilate Trans", default: "0.0", property: "dilat_trans_ms" },
                    { name: "Seq Offset", default: "0.0", property: "offset_seq_ms" },
                    { name: "Rhythm Pattern", default: "", property: "rhythm_pattern" }
                ]
            },
            "Particles": {
                "Outline v2 (bord_to_pixels_v2)": [
                    { name: "Path / Origin", default: "", property: "shape" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Density", default: "5.0", property: "density" },
                    { name: "RedrawDist", default: "0", property: "redraw_dist" },
                    { name: "Seed", default: "0", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ],
                "Outline v2": [
                    { name: "Path / Origin", default: "", property: "shape" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Density", default: "5.0", property: "density" },
                    { name: "RedrawDist", default: "0", property: "redraw_dist" },
                    { name: "Seed", default: "0", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ],
                "Border (Outline)": [
                    { name: "Path / Origin", default: "", property: "shape" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Density", default: "5.0", property: "density" },
                    { name: "RedrawDist", default: "0", property: "redraw_dist" },
                    { name: "Seed", default: "0", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ],
                "Inner Fill": [
                    { name: "Path / Origin", default: "", property: "shape" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Density", default: "5.0", property: "density" },
                    { name: "RedrawDist", default: "0", property: "redraw_dist" },
                    { name: "Seed", default: "0", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ]
            },
            "Functions/Particles": {
                "Outline v2 (bord_to_pixels_v2)": [
                    { name: "Path / Origin", default: "", property: "shape" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Density", default: "5.0", property: "density" },
                    { name: "RedrawDist", default: "0", property: "redraw_dist" },
                    { name: "Seed", default: "0", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ],
                "Outline v2": [
                    { name: "Path / Origin", default: "", property: "shape" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Density", default: "5.0", property: "density" },
                    { name: "RedrawDist", default: "0", property: "redraw_dist" },
                    { name: "Seed", default: "0", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ],
                "Border (Outline)": [
                    { name: "Path / Origin", default: "", property: "shape" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Density", default: "5.0", property: "density" },
                    { name: "RedrawDist", default: "0", property: "redraw_dist" },
                    { name: "Seed", default: "0", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ],
                "Inner Fill": [
                    { name: "Path / Origin", default: "", property: "shape" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Density", default: "5.0", property: "density" },
                    { name: "RedrawDist", default: "0", property: "redraw_dist" },
                    { name: "Seed", default: "0", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order", type: "button" },
                    { name: "Close Path", default: false, property: "close_path", type: "button", no_socket: true }
                ]
            },
            "IMG to pixels": {
                "DEFAULT": [
                    { name: "Image Path", default: "", property: "image_path" },
                    { name: "Particle", default: "", property: "particle_shape" },
                    { name: "Frame", default: "1", property: "frame" },
                    { name: "Step", default: "2", property: "step" },
                    { name: "Alpha", default: "128", property: "alpha_threshold" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Anchor", default: "Center", property: "anchor", type: "button" },
                    { name: "Numpad Order", default: "79", property: "order", type: "button" }
                ]
            },
            "Kana Transliteration": {
                "Romaji to Hiragana": [{ name: "Text", default: "" }],
                "Romaji to Katakana": [{ name: "Text", default: "" }],
                "Hiragana to Romaji": [{ name: "Text", default: "" }],
                "Katakana to Romaji": [{ name: "Text", default: "" }]
            },
            "Slicer": {
                "Grid 1D/2D": [
                    { name: "Shape", default: "", property: "shape" },
                    { name: "Cols", default: "2", property: "cols" },
                    { name: "Rows", default: "2", property: "rows" },
                    { name: "Angle", default: "0", property: "angle" },
                    { name: "Bleed", default: "0", property: "overlap" },
                    { name: "Accel X", default: "1.0", property: "accel" },
                    { name: "Accel Y", default: "1.0", property: "accel_y" },
                    { name: "Text Scale", default: "1.0", property: "text_scale" },
                    { name: "Pre-Offset", default: "0", property: "pre_offset" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "hex": [
                    { name: "Shape", default: "" },
                    { name: "Radius", default: "15" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "tri": [
                    { name: "Shape", default: "" },
                    { name: "Radius", default: "20" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "dia": [
                    { name: "Shape", default: "" },
                    { name: "Radius", default: "20" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "ring": [
                    { name: "Shape", default: "" },
                    { name: "Ring Width", default: "10" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "ray": [
                    { name: "Shape", default: "" },
                    { name: "Step Angle", default: "15" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "quad": [
                    { name: "Shape", default: "" },
                    { name: "Min Size", default: "10" },
                    { name: "Stop Prob", default: "0.45" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "bez": [
                    { name: "Shape", default: "" },
                    { name: "Grid Size", default: "20" },
                    { name: "Amplitude", default: "1.5" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "voronoi": [
                    { name: "Shape", default: "" },
                    { name: "Cell Size", default: "20" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "ashlar": [
                    { name: "Shape", default: "" },
                    { name: "Min Width", default: "10" },
                    { name: "Max Width", default: "40" },
                    { name: "Row Height", default: "15" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "brick": [
                    { name: "Shape", default: "" },
                    { name: "Width", default: "30" },
                    { name: "Height", default: "15" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "mondrian": [
                    { name: "Shape", default: "" },
                    { name: "Min Size", default: "12" },
                    { name: "Stop Prob", default: "0.45" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "herringbone": [
                    { name: "Shape", default: "" },
                    { name: "Length", default: "30" },
                    { name: "Thickness", default: "10" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "delaunay": [
                    { name: "Shape", default: "" },
                    { name: "Cell Size", default: "15" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "scallop": [
                    { name: "Shape", default: "" },
                    { name: "Radius", default: "12" },
                    { name: "Angle", default: "0" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "web": [
                    { name: "Shape", default: "" },
                    { name: "Rings", default: "5" },
                    { name: "Rays", default: "12" },
                    { name: "Chaos", default: "0.2" },
                    { name: "Center X", default: "0" },
                    { name: "Center Y", default: "0" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "rhombille": [
                    { name: "Shape", default: "" },
                    { name: "Radius", default: "20" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "octagon": [
                    { name: "Shape", default: "" },
                    { name: "Radius", default: "20" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "kagome": [
                    { name: "Shape", default: "" },
                    { name: "Radius", default: "15" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "jigsaw": [
                    { name: "Shape", default: "" },
                    { name: "Piece Size", default: "20" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "truchet": [
                    { name: "Shape", default: "" },
                    { name: "Cell Size", default: "20" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "circuit": [
                    { name: "Shape", default: "" },
                    { name: "Cell Size", default: "20" },
                    { name: "Trace Width", default: "5" },
                    { name: "Via Prob", default: "0.2" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ],
                "pattern": [
                    { name: "Shape", default: "" },
                    { name: "Pattern Shape", default: "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0" },
                    { name: "Cell Size", default: "20" },
                    { name: "Shape Size", default: "16" },
                    { name: "Stagger", default: "false" },
                    { name: "Positive Mode", default: "false" },
                    { name: "Text Scale", default: "1.0" },
                    { name: "Pre-Offset", default: "0" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" },
                    { name: "Bleed", default: "0" },
                    { name: "Order", default: "79" }
                ]
            },
            "Array": {
                "Grid": [
                    { name: "Particle", default: "", property: "particle" },
                    { name: "Cols", default: "5", property: "cols" },
                    { name: "Rows", default: "3", property: "rows" },
                    { name: "Spacing X", default: "0", property: "spacing_x" },
                    { name: "Spacing Y", default: "0", property: "spacing_y" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Formation": [
                    { name: "Particle", default: "", property: "particle" },
                    { name: "Formation", default: "", property: "formation" },
                    { name: "Explosion", default: "0", property: "explosion" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Rings": [
                    { name: "Particle", default: "", property: "particle" },
                    { name: "Rings", default: "3", property: "rings" },
                    { name: "Count / Ring", default: "", property: "count_per_ring" },
                    { name: "Radius", default: "50", property: "radius" },
                    { name: "Radius Step", default: "30", property: "radius_step" },
                    { name: "Rotate Step", default: "0", property: "rotate_step" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Spiral": [
                    { name: "Particle", default: "", property: "particle" },
                    { name: "Count", default: "20", property: "count" },
                    { name: "Turns", default: "2.0", property: "turns" },
                    { name: "Max Radius", default: "100", property: "max_radius" },
                    { name: "Angle Step", default: "0", property: "angle_step" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Scatter": [
                    { name: "Particle", default: "", property: "particle" },
                    { name: "Count", default: "20", property: "count" },
                    { name: "Width", default: "150", property: "area_width" },
                    { name: "Height", default: "100", property: "area_height" },
                    { name: "Seed", default: "1", property: "seed" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" },
                    { name: "Tags", default: "", property: "tags" }
                ],
                "Hex": [
                    { name: "Particle", default: "", property: "particle" },
                    { name: "Cols", default: "5", property: "cols" },
                    { name: "Rows", default: "3", property: "rows" },
                    { name: "Spacing", default: "0", property: "spacing" },
                    { name: "Scale", default: "1.0", property: "scale" },
                    { name: "Factor (t)", default: "1.0", property: "t" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" },
                    { name: "Tags", default: "", property: "tags" }
                ]
            },
            "Union & Divide": {
                "Divide (PolyTree)": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Fill Rule", default: "EvenOdd", property: "fill_type", type: "button" },
                    { name: "Auto-Intersect", default: "1", property: "clean_self_intersect", type: "button" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "DIVIDE": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Fill Rule", default: "EvenOdd", property: "fill_type", type: "button" },
                    { name: "Auto-Intersect", default: "1", property: "clean_self_intersect", type: "button" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "Dividir (PolyTree)": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Fill Rule", default: "EvenOdd", property: "fill_type", type: "button" },
                    { name: "Auto-Intersect", default: "1", property: "clean_self_intersect", type: "button" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "Union (Merge/Union)": [
                    { name: "Shape In (A)", default: "", property: "shape" },
                    { name: "Shape In (B)", default: "", property: "shape_b" },
                    { name: "Fill Rule", default: "NonZero", property: "fill_type", type: "button" },
                    { name: "Auto-Intersect", default: "1", property: "clean_self_intersect", type: "button" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" }
                ],
                "UNION": [
                    { name: "Shape In (A)", default: "", property: "shape" },
                    { name: "Shape In (B)", default: "", property: "shape_b" },
                    { name: "Fill Rule", default: "NonZero", property: "fill_type", type: "button" },
                    { name: "Auto-Intersect", default: "1", property: "clean_self_intersect", type: "button" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" }
                ],
                "Unir (Merge/Union)": [
                    { name: "Shape In (A)", default: "", property: "shape" },
                    { name: "Shape In (B)", default: "", property: "shape_b" },
                    { name: "Fill Rule", default: "NonZero", property: "fill_type", type: "button" },
                    { name: "Auto-Intersect", default: "1", property: "clean_self_intersect", type: "button" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" }
                ],
                "Divide (Sub-paths)": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "SUB-PATHS": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "Dividir (Sub-rutas)": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "Fusion (Tags)": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Tag Mode", default: "ipol", property: "tagmode", type: "button" },
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "FUSION": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Tag Mode", default: "ipol", property: "tagmode", type: "button" },
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "Fusión (Tags)": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Tag Mode", default: "ipol", property: "tagmode", type: "button" },
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ],
                "DEFAULT": [
                    { name: "Shape In", default: "", property: "shape" },
                    { name: "Fill Rule", default: "EvenOdd", property: "fill_type", type: "button" },
                    { name: "Auto-Intersect", default: "1", property: "clean_self_intersect", type: "button" },
                    { name: "Anchor", default: "pieces", property: "anchor", type: "button" },
                    { name: "Order", default: "79", property: "order" }
                ]
            },
            "Move Tag": {
                "trajectory": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Shape (d)", default: "", property: "shape" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "waypoints": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Points (x1,y1; x2,y2)", default: "", property: "points" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "jitter": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Amplitude X (dx)", default: "10.0", property: "dx" },
                    { name: "Amplitude Y (dy)", default: "10.0", property: "dy" },
                    { name: "Step Dur (ms)", default: "50", property: "dur" },
                    { name: "Random Seed", default: "0", property: "seed" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "Trajectory": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Shape (d)", default: "", property: "shape" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "Waypoints": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Points (x1,y1; x2,y2)", default: "", property: "points" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "Jitter": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Amplitude X (dx)", default: "10.0", property: "dx" },
                    { name: "Amplitude Y (dy)", default: "10.0", property: "dy" },
                    { name: "Step Dur (ms)", default: "50", property: "dur" },
                    { name: "Random Seed", default: "0", property: "seed" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ]
            },
            "Functions/Move Tag": {
                "trajectory": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Shape (d)", default: "", property: "shape" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "waypoints": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Points (x1,y1; x2,y2)", default: "", property: "points" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "jitter": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Amplitude X (dx)", default: "10.0", property: "dx" },
                    { name: "Amplitude Y (dy)", default: "10.0", property: "dy" },
                    { name: "Step Dur (ms)", default: "50", property: "dur" },
                    { name: "Random Seed", default: "0", property: "seed" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "Trajectory": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Shape (d)", default: "", property: "shape" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "Waypoints": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Points (x1,y1; x2,y2)", default: "", property: "points" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ],
                "Jitter": [
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Amplitude X (dx)", default: "10.0", property: "dx" },
                    { name: "Amplitude Y (dy)", default: "10.0", property: "dy" },
                    { name: "Step Dur (ms)", default: "50", property: "dur" },
                    { name: "Random Seed", default: "0", property: "seed" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ]
            },
            "Move Text": {
                "DEFAULT": [
                    { name: "Text", default: "", property: "text" },
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Delta X", default: "", property: "dx" },
                    { name: "Delta Y", default: "", property: "dy" },
                    { name: "Offset X", default: "", property: "ox" },
                    { name: "Offset Y", default: "", property: "oy" },
                    { name: "Trajectory", default: "", property: "trajectory" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ]
            },
            "Functions/Move Text": {
                "DEFAULT": [
                    { name: "Text", default: "", property: "text" },
                    { name: "Tags", default: "", property: "tags" },
                    { name: "Delta X", default: "", property: "dx" },
                    { name: "Delta Y", default: "", property: "dy" },
                    { name: "Offset X", default: "", property: "ox" },
                    { name: "Offset Y", default: "", property: "oy" },
                    { name: "Trajectory", default: "", property: "trajectory" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Step (px)", default: "7.5", property: "step_px" },
                    { name: "Start Time (t1)", default: "0", property: "t1" },
                    { name: "End Time (t2)", default: "fx.dur", property: "t2" },
                    { name: "Acceleration", default: "1.0", property: "accel" }
                ]
            },
            "Clipper": {
                "difference": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "DIFF": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "intersection": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "INTER": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "union": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "UNION": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "xor": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "XOR": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "offset": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Delta (px)", default: "0.0", property: "delta" },
                    { name: "Join Mode", default: "round", property: "join_type", type: "button" },
                    { name: "End Mode", default: "closed_polygon", property: "end_type", type: "button" },
                    { name: "Miter Limit", default: "2.0", property: "miter_limit" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "OFFSET": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Delta (px)", default: "0.0", property: "delta" },
                    { name: "Join Mode", default: "round", property: "join_type", type: "button" },
                    { name: "End Mode", default: "closed_polygon", property: "end_type", type: "button" },
                    { name: "Miter Limit", default: "2.0", property: "miter_limit" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "minkowski_sum": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "MINK +": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "minkowski_diff": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "MINK -": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ],
                "DEFAULT": [
                    { name: "Shape A (Subject)", default: "", property: "shape_a" },
                    { name: "Shape B (Clip)", default: "", property: "shape_b" },
                    { name: "Delta (px)", default: "0.0", property: "delta" },
                    { name: "Subj Fill", default: "evenodd", property: "subj_fill", type: "button" },
                    { name: "Clip Fill", default: "evenodd", property: "clip_fill", type: "button" },
                    { name: "Join Mode", default: "round", property: "join_type", type: "button" },
                    { name: "End Mode", default: "closed_polygon", property: "end_type", type: "button" },
                    { name: "Miter Limit", default: "2.0", property: "miter_limit" },
                    { name: "Post-Offset", default: "", property: "post_offset" },
                    { name: "Clean Dist", default: "0.0", property: "clean_dist" },
                    { name: "Strictly Simple", default: "0", property: "strictly_simple", type: "button" },
                    { name: "Reverse Subj", default: "0", property: "reverse_subj", type: "button" },
                    { name: "Reverse Clip", default: "0", property: "reverse_clip", type: "button" },
                    { name: "Anchor", default: "center", property: "anchor", type: "button" },
                    { name: "Output Type", default: "Shape", property: "out_mode", type: "button" }
                ]
            }
        };

        const ANCHOR_PROFILES = {
            shape: [
                { full: "center", short: "Center" },
                { full: "origin", short: "Origin" },
                { full: "relative", short: "Relative" },
                { full: "absolute", short: "Absolute" }
            ],
            piece: [
                { full: "pieces", short: "Pieces" },
                { full: "relative", short: "Relative" },
                { full: "parent_org", short: "Parent Org" },
                { full: "pos", short: "Pos" },
                { full: "absolute", short: "Absolute" }
            ],
            trajectory: [
                { full: "center", short: "Center" },
                { full: "origin", short: "Origin" },
                { full: "first_point", short: "First Pt" }
            ],
            cardinal: [
                { full: "center", short: "Center" },
                { full: "topleft", short: "TopLeft" },
                { full: "topright", short: "TopRight" },
                { full: "bottomleft", short: "BottomLeft" },
                { full: "bottomright", short: "BottomRight" }
            ]
        };

        const SLICER_ANCHOR_MODES = ANCHOR_PROFILES.piece;
        const GEOMETRIC_ANCHOR_MODES = ANCHOR_PROFILES.shape;
        const SHAPE_ANCHOR_MODES = ANCHOR_PROFILES.shape;
        const ANCHOR_MODES = SLICER_ANCHOR_MODES;

        const OUT_MODES = [
            { full: "shape", short: "Shape" },
            { full: "clip", short: "\\clip" },
            { full: "iclip", short: "\\iclip" },
            { full: "loops", short: "Loops" },
            { full: "pieces", short: "Pieces" }
        ];

        function getSpecFromSpecsTable(nodeKey, modeKey) {
            if (!nodeKey) return null;
            const cleanKey = String(nodeKey).replace(/^[^/]+\//, "").trim();
            const spec = MODE_INPUT_SPECS[cleanKey] || MODE_INPUT_SPECS[nodeKey];
            if (spec) {
                if (Array.isArray(spec)) return spec;
                if (modeKey && Array.isArray(spec[modeKey])) return spec[modeKey];
                if (Array.isArray(spec["DEFAULT"])) return spec["DEFAULT"];
                const val = Object.values(spec)[0];
                return Array.isArray(val) ? val : null;
            }
            return null;
        }

        function updateNodeModeInputs(node) {
            if (!node) return;
            const modeInfo = getTitleModeInfo(node);
            const title = String(node.title || node.type || "");
            const nodeKey = modeInfo ? modeInfo.key : (node.type || title);

            let specList = null;
            const isSysVar = title.includes("Sys Var") || title.includes("SysVar");
            if (isSysVar) {
                const varName = String((node.properties ? (node.properties.var_name || node.properties.variable) : "") || "").trim();
                const cleanV = varName.toLowerCase().replace("fx.", "");
                if (MODE_INPUT_SPECS["Sys Var"] && MODE_INPUT_SPECS["Sys Var"][cleanV]) {
                    specList = MODE_INPUT_SPECS["Sys Var"][cleanV];
                } else if (MODE_INPUT_SPECS["Variables/Sys Var"] && MODE_INPUT_SPECS["Variables/Sys Var"][cleanV]) {
                    specList = MODE_INPUT_SPECS["Variables/Sys Var"][cleanV];
                } else if (MODE_INPUT_SPECS["Sys Var"] && MODE_INPUT_SPECS["Sys Var"][varName]) {
                    specList = MODE_INPUT_SPECS["Sys Var"][varName];
                } else {
                    specList = [];
                }
            } else if (modeInfo) {
                const curMode = modeInfo.currentFull;
                if (nodeKey === "Math") {
                    const secMode = node.properties ? (node.properties["operation"] || "Add") : "Add";
                    specList = MODE_INPUT_SPECS["Math"][secMode] || MODE_INPUT_SPECS["Math"]["Add"];
                } else if (nodeKey === "Array") {
                    const secMode = node.properties ? (node.properties["mode"] || "Grid") : "Grid";
                    specList = (MODE_INPUT_SPECS["Array"] && MODE_INPUT_SPECS["Array"][secMode]) || MODE_INPUT_SPECS["Array"]["Grid"];
                } else if (nodeKey === "Time to Frame" || nodeKey === "Time/Time to Frame" || nodeKey === "Tiempo a Frame") {
                    const secMode = node.properties ? (node.properties["source"] || "Custom") : "Custom";
                    specList = (MODE_INPUT_SPECS[nodeKey] && MODE_INPUT_SPECS[nodeKey][secMode]) || (MODE_INPUT_SPECS["Time to Frame"] && MODE_INPUT_SPECS["Time to Frame"][secMode]) || MODE_INPUT_SPECS["Time to Frame"]["DEFAULT"];
                } else if (nodeKey === "Frame to Time" || nodeKey === "Time/Frame to Time" || nodeKey === "Frame a Tiempo") {
                    const secMode = node.properties ? (node.properties["source"] || "Custom") : "Custom";
                    specList = (MODE_INPUT_SPECS[nodeKey] && MODE_INPUT_SPECS[nodeKey][secMode]) || (MODE_INPUT_SPECS["Frame to Time"] && MODE_INPUT_SPECS["Frame to Time"][secMode]) || MODE_INPUT_SPECS["Frame to Time"]["DEFAULT"];
                } else {
                    specList = getSpecFromSpecsTable(nodeKey, curMode);
                }

                if (nodeKey === "MultiRandom") {
                    if (!node.properties) node.properties = {};
                    if (curMode === "Rcolor") {
                        if (node.properties.min === "0" || node.properties.min === "50" || node.properties.min === undefined) {
                            node.properties.min = "&HFFFFFF&";
                        }
                        if (node.properties.max === "100" || node.properties.max === "360" || node.properties.max === undefined) {
                            node.properties.max = "&H000000&";
                        }
                    } else if (curMode === "Rstep") {
                        if (node.properties.max === "100" || node.properties.max === "&H000000&") {
                            node.properties.max = "360";
                        }
                        if (node.properties.step === "" || node.properties.step === undefined) {
                            node.properties.step = "45";
                        }
                        if (node.properties.min && (node.properties.min.startsWith("&H") || node.properties.min.startsWith("#"))) {
                            node.properties.min = "0";
                        }
                    } else if (curMode === "Rbool") {
                        if (node.properties.min === "0" || (node.properties.min && (node.properties.min.startsWith("&H") || node.properties.min.startsWith("#")))) {
                            node.properties.min = "50";
                        }
                    } else if (curMode === "Re") {
                        if (node.properties.options === undefined || node.properties.options === "") {
                            node.properties.options = "opc1, opc2, opc3";
                        }
                    } else if (curMode === "Rfake") {
                        if (node.properties.counter === undefined || node.properties.counter === "") {
                            node.properties.counter = "i";
                        }
                        if (node.properties.min && (node.properties.min.startsWith("&H") || node.properties.min.startsWith("#"))) {
                            node.properties.min = "0";
                        }
                        if (node.properties.max && (node.properties.max.startsWith("&H") || node.properties.max.startsWith("#"))) {
                            node.properties.max = "100";
                        }
                    } else {
                        if (node.properties.min && (node.properties.min.startsWith("&H") || node.properties.min.startsWith("#"))) {
                            node.properties.min = "0";
                        }
                        if (node.properties.max && (node.properties.max.startsWith("&H") || node.properties.max.startsWith("#") || node.properties.max === "360")) {
                            node.properties.max = "100";
                        }
                    }
                }
                if (nodeKey === "Manipulator" || nodeKey === "Shape/Manipulator" || title.includes("Manipulator") || title.includes("Manipulador")) {
                    if (curMode === "Matrix" || curMode === "Matriz") {
                        if (node.properties.axis === undefined || node.properties.axis === "y") {
                            node.properties.axis = "none";
                        }
                        if (node.properties.offset_border === undefined || node.properties.offset_border === "0.0") {
                            node.properties.offset_border = "0";
                        }
                    }
                }
                if (nodeKey === "Move Tag" || title.includes("Move Tag")) {
                    if (node.outputs && node.outputs.length > 0) {
                        node.outputs[0].name = "Data";
                        node.outputs[0].label = "Data";
                    }
                }
                if (nodeKey === "Move Text" || title.includes("Move Text")) {
                    if (node.outputs && node.outputs.length > 0) {
                        node.outputs[0].name = "Text";
                        node.outputs[0].label = "Text";
                    }
                }
                if (nodeKey === "Tag Manipulator" || nodeKey === "Functions/Tag Manipulator" || nodeKey === "Tags/Tag Manipulator" || title.includes("Tag Manipulator") || title.includes("Manipulador de Tags")) {
                    if (curMode === "Extractor") {
                        if (!node.outputs || node.outputs.length !== 3) {
                            const oldLinks = (node.outputs || []).map(o => o.links);
                            node.outputs = [
                                { name: "String", type: "data", label: "String", links: oldLinks[0] || null },
                                { name: "Value", type: "data", label: "Value", links: oldLinks[1] || null },
                                { name: "Raw String", type: "data", label: "Raw String", links: oldLinks[2] || null }
                            ];
                        } else {
                            node.outputs[0].name = "String"; node.outputs[0].label = "String"; node.outputs[0].type = "data";
                            node.outputs[1].name = "Value"; node.outputs[1].label = "Value"; node.outputs[1].type = "data";
                            node.outputs[2].name = "Raw String"; node.outputs[2].label = "Raw String"; node.outputs[2].type = "data";
                        }
                    } else {
                        if (!node.outputs || node.outputs.length !== 1) {
                            const oldLinks = (node.outputs || []).map(o => o.links);
                            node.outputs = [
                                { name: "Tags Out", type: "data", label: "Tags Out", links: oldLinks[0] || null }
                            ];
                        } else {
                            node.outputs[0].name = "Tags Out"; node.outputs[0].label = "Tags Out"; node.outputs[0].type = "data";
                        }
                    }
                }
                if (nodeKey === "Retime" || nodeKey === "Time/Retime" || title.includes("Retime")) {
                    const reqRetimeOutputs = [
                        { name: "\\t Out", type: "data", label: "\\t Out" },
                        { name: "Start Time", type: "data", label: "Start Time" },
                        { name: "End Time", type: "data", label: "End Time" },
                        { name: "Duration", type: "data", label: "Duration" }
                    ];
                    if (!node.outputs || node.outputs.length !== reqRetimeOutputs.length) {
                        const oldLinks = (node.outputs || []).map(o => o.links);
                        node.outputs = reqRetimeOutputs.map((ro, idx) => ({
                            name: ro.name,
                            type: ro.type,
                            label: ro.label,
                            links: oldLinks[idx] || null
                        }));
                    } else {
                        reqRetimeOutputs.forEach((ro, idx) => {
                            node.outputs[idx].name = ro.name;
                            node.outputs[idx].label = ro.label;
                            node.outputs[idx].type = ro.type;
                        });
                    }
                }
                if (nodeKey === "Animation" || nodeKey === "Functions/Animation" || title.includes("Animation")) {
                    const isAlpha = (curMode === "alpha" || (node.properties && String(node.properties.mode).toLowerCase() === "alpha"));
                    const reqAnimationOutputs = isAlpha ? [
                        { name: "Shape Out", type: "data", label: "Shape Out" },
                        { name: "Tags", type: "data", label: "Tags" },
                        { name: "Frame", type: "data", label: "Frame" },
                        { name: "Frames List", type: "data", label: "Frames List" }
                    ] : [
                        { name: "Shape", type: "data", label: "Shape" },
                        { name: "Frame", type: "data", label: "Frame" },
                        { name: "Frames List", type: "data", label: "Frames List" }
                    ];
                    if (!node.outputs || node.outputs.length !== reqAnimationOutputs.length) {
                        const oldLinks = (node.outputs || []).map(o => o.links);
                        node.outputs = reqAnimationOutputs.map((ro, idx) => ({
                            name: ro.name,
                            type: ro.type,
                            label: ro.label,
                            links: oldLinks[idx] || null
                        }));
                    } else {
                        reqAnimationOutputs.forEach((ro, idx) => {
                            node.outputs[idx].name = ro.name;
                            node.outputs[idx].label = ro.label;
                            node.outputs[idx].type = ro.type;
                        });
                    }
                }
            }

            if (!specList) {
                specList = getSpecFromSpecsTable(title, modeInfo ? modeInfo.currentFull : null) || 
                           (node.type ? getSpecFromSpecsTable(node.type, modeInfo ? modeInfo.currentFull : null) : null);
            }

            if (!Array.isArray(specList)) {
                if (node.inputs && node.inputs.length > 0) {
                    specList = node.inputs.map(inp => {
                        const name = inp.name;
                        const propKey = inp.property || (inp.name && inp.name.startsWith("In") ? inp.name : name.toLowerCase());
                        const defVal = (node.properties && node.properties[propKey] !== undefined) ? String(node.properties[propKey]) : "";
                        return { name: name, default: defVal, property: propKey };
                    });
                }
            }

            if (!Array.isArray(specList) || specList.length === 0) return;

            const oldInputs = node.inputs ? [...node.inputs] : [];
            node.inputs = [];
            node.widgets = [];

            const fullSpecList = [...specList];
            if (node.properties && node.properties.expandable) {
                const existingNames = new Set(fullSpecList.map(s => s.name));
                oldInputs.forEach(oldInp => {
                    if (oldInp && oldInp.name && !existingNames.has(oldInp.name)) {
                        existingNames.add(oldInp.name);
                        const pKey = oldInp.property || oldInp.name;
                        const defVal = (node.properties && node.properties[pKey] !== undefined) ? String(node.properties[pKey]) : "";
                        fullSpecList.push({ name: oldInp.name, default: defVal, property: pKey });
                    }
                });
            }

            const graph = node.graph || (window.LGraphCanvas && window.LGraphCanvas.active_canvas ? window.LGraphCanvas.active_canvas.graph : null);
            const remainingOldInputs = [...oldInputs];

            const isTagManip = (nodeKey === "Tag Manipulator" || nodeKey === "Functions/Tag Manipulator" || nodeKey === "Tags/Tag Manipulator" || title.includes("Tag Manipulator") || title.includes("Manipulador de Tags"));
            const startY = isTagManip ? 15 : 11;
            fullSpecList.forEach((spec, idx) => {
                const portName = spec.name;
                const propKey = spec.property || portName;
                if (!node.properties) node.properties = {};
                if (node.properties[propKey] === undefined) {
                    node.properties[propKey] = spec.default;
                }
                
                const oldInpIdx = remainingOldInputs.findIndex(i => (i && i.property && i.property === propKey) || (i && i.name && (i.name === portName || i.name === propKey)));
                let linkId = null;
                if (oldInpIdx !== -1) {
                    const oldInp = remainingOldInputs[oldInpIdx];
                    linkId = oldInp.link;
                    remainingOldInputs.splice(oldInpIdx, 1);
                }

                const rowIdx = (spec.visualRow !== undefined) ? spec.visualRow : idx;
                const yPos = startY + rowIdx * 23;
                const isNoSocket = !!spec.no_socket;

                if (!isNoSocket) {
                    if (linkId !== null && linkId !== undefined && graph && graph.links && graph.links[linkId]) {
                        const linkObj = graph.links[linkId];
                        if (Array.isArray(linkObj)) {
                            linkObj[4] = node.inputs.length;
                        } else if (typeof linkObj === "object") {
                            linkObj.target_slot = node.inputs.length;
                        }
                    }

                    const dotY = yPos + 9;
                    node.inputs.push({
                        name: portName,
                        type: 0,
                        link: linkId,
                        pos: [10, dotY],
                        label: " ",
                        property: propKey
                    });
                }

                const curVal = String(node.properties[propKey] !== undefined ? node.properties[propKey] : spec.default);
                const w = node.addWidget("text", portName, curVal, function(val) {
                    const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                    if (node.properties) {
                        node.properties[propKey] = cleanVal;
                    }
                    if (node.computeSize) {
                        const sz = node.computeSize();
                        node.size[0] = Math.max(node.size[0], sz[0]);
                        node.size[1] = sz[1];
                    }
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                });
                w.property = propKey;
                w._visualRow = rowIdx;
                if (spec.crossCol) {
                    w._crossCol = spec.crossCol;
                    w._boxW = 28;
                    w._boxX = spec.crossCol === "left" ? 14 : (spec.crossCol === "right" ? 78 : 46);
                }
                w.last_y = yPos;
                w.y = yPos;

                if (spec.type === "button" || portName === "Order" || portName === "Numpad Order" || propKey === "order" || propKey === "numpad_order") {
                    w.type = "custom";
                    w.isCyclicButtonWidget = true;
                    w.isPointInside = function(x, y, node) {
                        const drawY = (w.last_y !== undefined) ? w.last_y : (w.y || 0);
                        const bX = (w._btnX !== undefined) ? w._btnX : 20;
                        const bW = (w._btnW !== undefined) ? w._btnW : 75;
                        return x >= bX - 2 && x <= bX + bW + 2 && y >= drawY - 2 && y <= drawY + 20;
                    };
                    if (portName === "Binarize Mode") {
                        const BIN_MODES = [
                            { full: "luminance", short: "Luminance", i18nKey: "nodes.modes.luminance" },
                            { full: "silhouette", short: "Silhouette", i18nKey: "nodes.modes.silhouette" },
                            { full: "borders", short: "Borders", i18nKey: "nodes.modes.borders" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curB = String((n.properties && n.properties.bin_mode) ? n.properties.bin_mode : (w.value || "luminance")).toLowerCase();
                            const bObj = BIN_MODES.find(m => m.full.toLowerCase() === curB || m.short.toLowerCase() === curB || (curB.includes("lumin") && m.full === "luminance") || (curB.includes("gris") && m.full === "luminance") || (curB.includes("sil") && m.full === "silhouette") || (curB.includes("bord") && m.full === "borders")) || BIN_MODES[0];

                            let displayTxt = bObj.short;
                            if (bObj.i18nKey) {
                                if (window.t) displayTxt = window.t(bObj.i18nKey);
                                else if (window.PyxisI18n && window.PyxisI18n.t) displayTxt = window.PyxisI18n.t(bObj.i18nKey);
                            }

                            ctx.save();
                            ctx.font = "bold 11px monospace";

                            const textW = ctx.measureText(displayTxt).width;
                            const btnX = 22;
                            const btnW = Math.max(75, Math.round(textW + 18));
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(displayTxt, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curB = String((node.properties && node.properties.bin_mode) ? node.properties.bin_mode : "luminance").toLowerCase();
                            const curIdx = BIN_MODES.findIndex(m => m.full.toLowerCase() === curB || m.short.toLowerCase() === curB || (curB.includes("lumin") && m.full === "luminance") || (curB.includes("gris") && m.full === "luminance") || (curB.includes("sil") && m.full === "silhouette") || (curB.includes("bord") && m.full === "borders"));
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % BIN_MODES.length);
                            const nextObj = BIN_MODES[nextIdx];
                            node.properties.bin_mode = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("bin_mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);

                            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.trace_image_api === 'function') {
                                node._isTracing = true;
                                window.pywebview.api.trace_image_api(node.properties).then(res => {
                                    node._isTracing = false;
                                    if (res && res.shape) {
                                        node._lastTracedShape = res.shape;
                                    }
                                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                                }).catch(() => { node._isTracing = false; });
                            }
                        };
                    } else if (portName === "Relative" || portName === "Relativo" || portName === "Relative Mode" || portName === "Modo Relativo") {
                        const REL_MODES = [
                            { full: "1", short: "Relativo" },
                            { full: "0", short: "Absoluto" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curR = String((n.properties && n.properties.relative !== undefined) ? n.properties.relative : (w.value || "1")).trim();
                            const rObj = REL_MODES.find(m => m.full === curR || m.short.toLowerCase() === curR.toLowerCase()) || REL_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            const btnX = 22;
                            const btnW = 75;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(rObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curR = String((node.properties && node.properties.relative !== undefined) ? node.properties.relative : "1").trim();
                            const curIdx = REL_MODES.findIndex(m => m.full === curR || m.short.toLowerCase() === curR.toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % REL_MODES.length);
                            const nextObj = REL_MODES[nextIdx];
                            node.properties.relative = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("relative-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Split Axis" || portName === "Eje de División") {
                        const AXIS_MODES = [
                            { full: "both", short: "Ambos" },
                            { full: "x", short: "Solo X" },
                            { full: "y", short: "Solo Y" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curA = String((n.properties && n.properties.axis) ? n.properties.axis : (w.value || "both")).trim().toLowerCase();
                            const aObj = AXIS_MODES.find(m => m.full.toLowerCase() === curA || m.short.toLowerCase() === curA) || AXIS_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            const btnX = 22;
                            const btnW = 75;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(aObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curA = String((node.properties && node.properties.axis) ? node.properties.axis : "both").trim().toLowerCase();
                            const curIdx = AXIS_MODES.findIndex(m => m.full.toLowerCase() === curA || m.short.toLowerCase() === curA);
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % AXIS_MODES.length);
                            const nextObj = AXIS_MODES[nextIdx];
                            node.properties.axis = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("axis-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Terminal" || portName === "Tip Style" || portName === "Terminal Style") {
                        const BANNER_TERMINAL_MODES = [
                            { full: "Arrow", short: "Arrow" },
                            { full: "Notch", short: "Notch" },
                            { full: "Flat", short: "Flat" },
                            { full: "Round", short: "Round" },
                            { full: "Concave", short: "Concave" },
                            { full: "Chamfer", short: "Chamfer" },
                            { full: "Slant", short: "Slant" },
                            { full: "Backslant", short: "Backslant" },
                            { full: "Trapezoid", short: "Trapezoid" },
                            { full: "Brace", short: "Brace" },
                            { full: "Fishtail", short: "Fishtail" },
                            { full: "Crown", short: "Crown" },
                            { full: "Shield", short: "Shield" },
                            { full: "Wave", short: "Wave" },
                            { full: "Sawtooth", short: "Sawtooth" },
                            { full: "Step", short: "Step" },
                            { full: "Hexagon", short: "Hexagon" },
                            { full: "Ticket", short: "Ticket" },
                            { full: "Diamond", short: "Diamond" },
                            { full: "Pennant", short: "Pennant" },
                            { full: "BannerCut", short: "BannerCut" },
                            { full: "Scroll", short: "Scroll" },
                            { full: "Flame", short: "Flame" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curT = String((n.properties && n.properties.tip_style) ? n.properties.tip_style : (w.value || "Arrow")).trim();
                            const tObj = BANNER_TERMINAL_MODES.find(m => m.full.toLowerCase() === curT.toLowerCase() || m.short.toLowerCase() === curT.toLowerCase()) || BANNER_TERMINAL_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            const btnX = 22;
                            const btnW = 85;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(tObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curT = String((node.properties && node.properties.tip_style) ? node.properties.tip_style : (w.value || "Arrow")).trim();
                            const curIdx = BANNER_TERMINAL_MODES.findIndex(m => m.full.toLowerCase() === curT.toLowerCase() || m.short.toLowerCase() === curT.toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % BANNER_TERMINAL_MODES.length);
                            const nextObj = BANNER_TERMINAL_MODES[nextIdx];
                            node.properties.tip_style = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("tip_style-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Anchor" || portName === "Anclaje") {
                        function getAnchorListAndDef(targetNode) {
                            const t = String((targetNode && (targetNode.title || targetNode.type)) || "");
                            if (t.includes("IMG to pixels") || (targetNode.type && String(targetNode.type).includes("IMG to pixels"))) {
                                return { list: ANCHOR_PROFILES.cardinal, def: "center" };
                            }
                            if (t.includes("Move Tag") || t.includes("Move Text") || (targetNode.type && (String(targetNode.type).includes("Move Tag") || String(targetNode.type).includes("Move Text")))) {
                                return { list: ANCHOR_PROFILES.trajectory, def: "center" };
                            }
                            const isMulti = t.includes("Multi") || (targetNode.type && String(targetNode.type).includes("Multi"));
                            if (isMulti) {
                                const isLoop = String((targetNode.properties && (targetNode.properties.loop_mode || targetNode.properties.out_mode)) || "").toLowerCase().includes("loop");
                                if (isLoop) {
                                    return { list: ANCHOR_PROFILES.piece, def: "pieces" };
                                }
                                return { list: ANCHOR_PROFILES.shape, def: "center" };
                            }
                            const isSlicerLike = t.includes("Slicer") || t.includes("Array") || t.includes("Union & Divide") || t.includes("Unir y Dividir") || t.includes("Concentric Borders") || t.includes("Particles") || (targetNode.type && (String(targetNode.type).includes("Slicer") || String(targetNode.type).includes("Array") || String(targetNode.type).includes("Union & Divide") || String(targetNode.type).includes("Unir y Dividir") || String(targetNode.type).includes("Concentric Borders") || String(targetNode.type).includes("Particles")));
                            if (isSlicerLike) {
                                return { list: ANCHOR_PROFILES.piece, def: t.includes("Concentric") ? "relative" : "pieces" };
                            }
                            // Monolithic shapes (Manipulator, Transform, Filter, Multi in Shape mode, IMG to Shape)
                            return { list: ANCHOR_PROFILES.shape, def: "center" };
                        }

                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const { list: anchorList, def: defAnchor } = getAnchorListAndDef(n);
                            const curA = String((n.properties && n.properties.anchor) ? n.properties.anchor : (w.value || defAnchor)).trim();
                            const aObj = anchorList.find(m => m.full.toLowerCase() === curA.toLowerCase() || m.short.toLowerCase() === curA.toLowerCase()) || anchorList[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";

                            const isImgToPx = (n.title && n.title.includes("IMG to pixels")) || (n.type && String(n.type).includes("IMG to pixels"));
                            const textW = ctx.measureText(aObj.short).width;
                            const btnX = 22;
                            const btnW = isImgToPx ? 85 : Math.max(75, Math.round(textW + 18));
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(aObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const { list: anchorList, def: defAnchor } = getAnchorListAndDef(node);
                            const curA = String((node.properties && node.properties.anchor) ? node.properties.anchor : (w.value || defAnchor)).trim();
                            const curIdx = anchorList.findIndex(m => m.full.toLowerCase() === curA.toLowerCase() || m.short.toLowerCase() === curA.toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % anchorList.length);
                            const nextObj = anchorList[nextIdx];
                            node.properties.anchor = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("anchor-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Output Type") {
                        function getOutModesList(n) {
                            return [
                                { full: "Shape", short: "Shape" },
                                { full: "Clip", short: "\\clip" },
                                { full: "iClip", short: "\\iclip" }
                            ];
                        }
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const modes = getOutModesList(n);
                            const defVal = modes[0] ? modes[0].full : "Shape";
                            const curO = (n.properties && n.properties.out_mode) ? n.properties.out_mode : (w.value || defVal);
                            const oObj = modes.find(m => m.full.toLowerCase() === String(curO).toLowerCase()) || modes[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";

                            const textW = ctx.measureText(oObj.short).width;
                            const btnX = 22;
                            const btnW = Math.max(75, Math.round(textW + 18));
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(oObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const modes = getOutModesList(node);
                            const defVal = modes[0] ? modes[0].full : "Shape";
                            const curO = (node.properties && node.properties.out_mode) ? node.properties.out_mode : defVal;
                            const curIdx = modes.findIndex(m => m.full.toLowerCase() === String(curO).toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % modes.length);
                            const nextObj = modes[nextIdx];
                            node.properties.out_mode = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("out_mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Base Mode" || portName === "Modo Anillo") {
                        const BORDER_BASE_MODES = [
                            { full: "Hollow (borders)", short: "Hollow" },
                            { full: "Filled Base (filled_borders)", short: "Filled" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curM = (n.properties && n.properties.mode) ? n.properties.mode : (w.value || "Hollow (borders)");
                            const mObj = BORDER_BASE_MODES.find(m => m.full === curM || (String(curM).includes("Hueco") && m.full.includes("Hollow")) || (String(curM).includes("Relleno") && m.full.includes("Filled"))) || BORDER_BASE_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const modeLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Mode:") : "Mode:";
                            ctx.fillText(modeLabel, 22, drawY + 13);

                            const modoLabelW = ctx.measureText(modeLabel).width;
                            const btnX = Math.round(22 + modoLabelW + 4);
                            const btnW = 68;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(mObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curM = (node.properties && node.properties.mode) ? node.properties.mode : "Hollow (borders)";
                            const curIdx = BORDER_BASE_MODES.findIndex(m => m.full === curM || m.short === curM || m.full.toLowerCase() === String(curM).toLowerCase() || (String(curM).includes("Hueco") && m.full.includes("Hollow")) || (String(curM).includes("Relleno") && m.full.includes("Filled")));
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % BORDER_BASE_MODES.length);
                            const nextObj = BORDER_BASE_MODES[nextIdx];
                            node.properties.mode = nextObj.full;
                            if (node.properties.modo !== undefined) delete node.properties.modo;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("border-mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Order" || portName === "Numpad Order" || propKey === "order" || propKey === "numpad_order") {
                        const ORDER_MODES_1D = [
                            { full: "normal", short: "Normal", i18nKey: "nodes.modes.order_1d.normal" },
                            { full: "reverse", short: "Invert", i18nKey: "nodes.modes.order_1d.reverse" },
                            { full: "center_to_edges", short: "Center", i18nKey: "nodes.modes.order_1d.center_to_edges" },
                            { full: "edges_to_center", short: "Edges", i18nKey: "nodes.modes.order_1d.edges_to_center" },
                            { full: "random", short: "Rand", i18nKey: "nodes.modes.order_1d.random" }
                        ];
                        const ORDER_MODES_2D = [
                            { full: "79", short: "79 (TL->BR)" },
                            { full: "97", short: "97 (TR->BL)" },
                            { full: "13", short: "13 (BL->TR)" },
                            { full: "31", short: "31 (BR->TL)" },
                            { full: "71", short: "71 (TL->BL)" },
                            { full: "17", short: "17 (BL->TL)" },
                            { full: "93", short: "93 (TR->BR)" },
                            { full: "39", short: "39 (BR->TR)" },
                            { full: "5", short: "5 (Radial)" },
                            { full: "-5", short: "-5 (Implos)" },
                            { full: "cw", short: "cw (CW)" },
                            { full: "ccw", short: "ccw (CCW)" },
                            { full: "rand", short: "Rand" },
                            { full: "path", short: "Path" },
                            { full: "path_inv", short: "PathInv" }
                        ];

                        function get1DOrderObj(val) {
                            const s = String(val || "normal").trim().toLowerCase();
                            if (s === "normal" || s === "0") return ORDER_MODES_1D[0];
                            if (s === "reverse" || s === "invert" || s.includes("invert") || s.includes("rev")) return ORDER_MODES_1D[1];
                            if (s === "center_to_edges" || (s.startsWith("centr") && (s.includes("extremo") || s.includes("edge") || s.includes("end") || s.includes("out")))) return ORDER_MODES_1D[2];
                            if (s === "edges_to_center" || ((s.startsWith("extrem") || s.startsWith("edge") || s.startsWith("out")) && (s.includes("centr") || s.includes("center")))) return ORDER_MODES_1D[3];
                            if (s === "center" || s === "centro" || s.startsWith("centr")) return ORDER_MODES_1D[2];
                            if (s === "edges" || s === "extremos" || s.startsWith("extrem") || s.startsWith("edge")) return ORDER_MODES_1D[3];
                            if (s === "random" || s.includes("aleat") || s.includes("rand")) return ORDER_MODES_1D[4];
                            return ORDER_MODES_1D.find(m => m.full.toLowerCase() === s || m.short.toLowerCase() === s) || ORDER_MODES_1D[0];
                        }

                        function get2DOrderObj(val) {
                            const s = String(val || "79").trim().toLowerCase();
                            return ORDER_MODES_2D.find(m => m.full.toLowerCase() === s || m.short.toLowerCase() === s) || ORDER_MODES_2D[0];
                        }

                        function getCustomOrderObj(val, modes) {
                            const s = String(val || (modes[0] ? modes[0].full : "normal")).trim().toLowerCase();
                            const found = modes.find(m => m.full.toLowerCase() === s || m.short.toLowerCase() === s);
                            if (found) return found;
                            if (s === "reverse" || s.includes("invert") || s.includes("rev")) {
                                const inv = modes.find(m => m.full.includes("invert") || m.full.includes("reverse") || m.full === "31" || m.full === "ccw");
                                if (inv) return inv;
                            }
                            if (s.includes("odd") || s.includes("even") || s.includes("par")) {
                                const oe = modes.find(m => m.full.includes("odd"));
                                if (oe) return oe;
                            }
                            if (s.includes("rand") || s.includes("aleat")) {
                                const rd = modes.find(m => m.full.includes("rand"));
                                if (rd) return rd;
                            }
                            return modes[0] || { full: "normal", short: "Normal" };
                        }

                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const propKeyToUse = w.property || "order";
                            const is1D = (spec && spec.order_dim === "1d");
                            const customModes = (spec && spec.order_modes) ? spec.order_modes : (w.spec && w.spec.order_modes ? w.spec.order_modes : null);
                            const activeModes = customModes || (is1D ? ORDER_MODES_1D : ORDER_MODES_2D);
                            const defaultVal = activeModes[0] ? activeModes[0].full : (is1D ? "normal" : "79");
                            const rawO = (n.properties && n.properties[propKeyToUse] !== undefined) ? n.properties[propKeyToUse] : (w.value || defaultVal);
                            const oObj = customModes ? getCustomOrderObj(rawO, customModes) : (is1D ? get1DOrderObj(rawO) : get2DOrderObj(rawO));

                            let displayTxt = oObj.short;
                            if (oObj.i18nKey) {
                                if (window.t) displayTxt = window.t(oObj.i18nKey);
                                else if (window.PyxisI18n && window.PyxisI18n.t) displayTxt = window.PyxisI18n.t(oObj.i18nKey);
                            }

                            ctx.save();
                            ctx.font = "bold 11px monospace";

                            const btnX = 22;
                            const textW = ctx.measureText(displayTxt).width;
                            const btnW = Math.max(75, Math.round(textW + 16));
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(displayTxt, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const propKeyToUse = w.property || "order";
                            const is1D = (w.spec && w.spec.order_dim === "1d");
                            const customModes = (w.spec && w.spec.order_modes) ? w.spec.order_modes : ((spec && spec.order_modes) ? spec.order_modes : null);
                            const activeModes = customModes || (is1D ? ORDER_MODES_1D : ORDER_MODES_2D);
                            const defaultVal = activeModes[0] ? activeModes[0].full : (is1D ? "normal" : "79");

                            const rawO = (node.properties && node.properties[propKeyToUse] !== undefined) ? node.properties[propKeyToUse] : (w.value || defaultVal);
                            const curObj = customModes ? getCustomOrderObj(rawO, customModes) : (is1D ? get1DOrderObj(rawO) : get2DOrderObj(rawO));
                            const curIdx = activeModes.indexOf(curObj);
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % activeModes.length);
                            const nextObj = activeModes[nextIdx];
                            if (!node.properties) node.properties = {};
                            node.properties[propKeyToUse] = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("order-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Vertex Mode" || portName === "Union Mode" || portName === "Join Mode" || propKey === "join_mode" || propKey === "join_type") {
                        const JOIN_MODES = [
                            { full: "round", short: "Round" },
                            { full: "miter", short: "Miter" },
                            { full: "square", short: "Square" },
                            { full: "bevel", short: "Bevel" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curKey = (n.properties && n.properties.join_type !== undefined) ? "join_type" : (propKey || "join_mode");
                            const curJ = (n.properties && n.properties[curKey]) ? n.properties[curKey] : (w.value || "round");
                            const jObj = JOIN_MODES.find(m => m.full.toLowerCase() === String(curJ).toLowerCase() || m.short.toLowerCase() === String(curJ).toLowerCase()) || JOIN_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const jLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Join:") : "Join:";
                            ctx.fillText(jLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(jLabel).width;
                            const btnX = Math.round(22 + labelW + 6);
                            const btnW = 75;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(jObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curKey = (node.properties && node.properties.join_type !== undefined) ? "join_type" : (propKey || "join_mode");
                            const curJ = (node.properties && node.properties[curKey]) ? node.properties[curKey] : "round";
                            let curIdx = JOIN_MODES.findIndex(m => m.full.toLowerCase() === String(curJ).toLowerCase() || m.short.toLowerCase() === String(curJ).toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % JOIN_MODES.length);
                            const nextObj = JOIN_MODES[nextIdx];
                            if (!node.properties) node.properties = {};
                            node.properties[curKey] = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("join_mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "End Mode" || propKey === "end_type") {
                        const END_MODES = [
                            { full: "closed_polygon", short: "Closed Poly" },
                            { full: "closed_line", short: "Closed Line" },
                            { full: "open_round", short: "Open Round" },
                            { full: "open_square", short: "Open Square" },
                            { full: "open_butt", short: "Open Butt" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curE = String((n.properties && n.properties.end_type) ? n.properties.end_type : (w.value || "closed_polygon")).trim().toLowerCase();
                            const eObj = END_MODES.find(m => m.full.toLowerCase() === curE || m.short.toLowerCase() === curE) || END_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const eLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("End:") : "End:";
                            ctx.fillText(eLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(eLabel).width;
                            const btnX = Math.round(22 + labelW + 6);
                            const btnW = 85;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(eObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curE = String((node.properties && node.properties.end_type) ? node.properties.end_type : "closed_polygon").trim().toLowerCase();
                            const curIdx = END_MODES.findIndex(m => m.full.toLowerCase() === curE || m.short.toLowerCase() === curE);
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % END_MODES.length);
                            const nextObj = END_MODES[nextIdx];
                            if (!node.properties) node.properties = {};
                            node.properties.end_type = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("end_type-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Subj Fill" || portName === "Clip Fill" || propKey === "subj_fill" || propKey === "clip_fill") {
                        const FILL_MODES = [
                            { full: "evenodd", short: "EvenOdd" },
                            { full: "nonzero", short: "NonZero" },
                            { full: "positive", short: "Positive" },
                            { full: "negative", short: "Negative" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curKey = propKey || (portName.includes("Subj") ? "subj_fill" : "clip_fill");
                            const curF = String((n.properties && n.properties[curKey]) ? n.properties[curKey] : (w.value || "evenodd")).trim().toLowerCase();
                            const fObj = FILL_MODES.find(m => m.full.toLowerCase() === curF || m.short.toLowerCase() === curF) || FILL_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const isSubj = (curKey === "subj_fill" || portName.includes("Subj"));
                            const rawLabel = isSubj ? "Subj Fill:" : "Clip Fill:";
                            const fLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot(rawLabel) : rawLabel;
                            ctx.fillText(fLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(fLabel).width;
                            const btnX = Math.round(22 + labelW + 6);
                            const btnW = 75;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(fObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curKey = propKey || (portName.includes("Subj") ? "subj_fill" : "clip_fill");
                            const curF = String((node.properties && node.properties[curKey]) ? node.properties[curKey] : (w.value || "evenodd")).trim().toLowerCase();
                            const curIdx = FILL_MODES.findIndex(m => m.full.toLowerCase() === curF || m.short.toLowerCase() === curF);
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % FILL_MODES.length);
                            const nextObj = FILL_MODES[nextIdx];
                            if (!node.properties) node.properties = {};
                            node.properties[curKey] = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("fill-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Strictly Simple" || portName === "Reverse Subj" || portName === "Reverse Clip" ||
                               propKey === "strictly_simple" || propKey === "reverse_subj" || propKey === "reverse_clip") {
                        const curKey = propKey || (portName.toLowerCase().replace(/\s+/g, "_"));
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curVal = (n.properties && n.properties[curKey] !== undefined) ? n.properties[curKey] : (w.value || "0");
                            const isChecked = (curVal === true || curVal === "true" || curVal === "1" || curVal === 1);

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            let rawLabel = "Simple:";
                            if (curKey === "reverse_subj" || portName.includes("Subj")) rawLabel = "Rev Subj:";
                            else if (curKey === "reverse_clip" || portName.includes("Clip")) rawLabel = "Rev Clip:";
                            const bLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot(rawLabel) : rawLabel;
                            ctx.fillText(bLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(bLabel).width;
                            const btnX = Math.round(22 + labelW + 6);
                            const btnW = 55;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = isChecked ? "#1e3a8a" : "#12161f";
                            ctx.strokeStyle = isChecked ? "#38bdf8" : "#475569";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = isChecked ? "#7dd3fc" : "#94a3b8";
                            ctx.textAlign = "center";
                            ctx.fillText(isChecked ? "TRUE" : "FALSE", btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curVal = (node.properties && node.properties[curKey] !== undefined) ? node.properties[curKey] : "0";
                            const isChecked = (curVal === true || curVal === "true" || curVal === "1" || curVal === 1);
                            const nextVal = !isChecked ? "1" : "0";
                            if (!node.properties) node.properties = {};
                            node.properties[curKey] = nextVal;
                            w.value = nextVal;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState(`${curKey}-change`);
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Cap Mode" || propKey === "cap_mode") {
                        const CAP_MODES = [
                            { full: "Bezier", short: "Bezier" },
                            { full: "Square", short: "Square" },
                            { full: "Flat", short: "Flat" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curC = (n.properties && n.properties.cap_mode) ? n.properties.cap_mode : (w.value || "Bezier");
                            const cObj = CAP_MODES.find(m => m.full.toLowerCase() === curC.toLowerCase() || (curC.toLowerCase() === "round" && m.full === "Bezier")) || CAP_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const cLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Cap:") : "Cap:";
                            ctx.fillText(cLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(cLabel).width;
                            const btnX = Math.round(22 + labelW + 8);
                            const btnW = 68;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#38bdf8";
                            ctx.textAlign = "center";
                            ctx.fillText(cObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curC = (node.properties && node.properties.cap_mode) ? node.properties.cap_mode : "Bezier";
                            let curIdx = CAP_MODES.findIndex(m => m.full.toLowerCase() === curC.toLowerCase());
                            if (curIdx === -1 && curC.toLowerCase() === "round") curIdx = 0;
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % CAP_MODES.length);
                            const nextObj = CAP_MODES[nextIdx];
                            node.properties.cap_mode = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("cap_mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Close Path" || portName === "Cerrar Trazo" || propKey === "close_path") {
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curVal = (n.properties && n.properties.close_path !== undefined) ? n.properties.close_path : (w.value || false);
                            const isChecked = (curVal === true || curVal === "true" || curVal === "1" || curVal === 1);

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const closeLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Close Path:") : "Close Path:";
                            ctx.fillText(closeLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(closeLabel).width;
                            const btnX = Math.round(22 + labelW + 8);
                            const boxSize = 16;
                            const btnW = 32;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = isChecked ? "#0f766e" : "#12161f";
                            ctx.strokeStyle = isChecked ? "#2dd4bf" : "#475569";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY + 1, boxSize, boxSize, 4);
                            else ctx.rect(btnX, drawY + 1, boxSize, boxSize);
                            ctx.fill();
                            ctx.stroke();

                            if (isChecked) {
                                ctx.fillStyle = "#ffffff";
                                ctx.textAlign = "center";
                                ctx.font = "bold 11px sans-serif";
                                ctx.fillText("✓", btnX + boxSize / 2, drawY + 13);
                            }
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curVal = (node.properties && node.properties.close_path !== undefined) ? node.properties.close_path : false;
                            const isChecked = (curVal === true || curVal === "true" || curVal === "1" || curVal === 1);
                            const nextVal = !isChecked;
                            if (!node.properties) node.properties = {};
                            node.properties.close_path = nextVal;
                            w.value = nextVal;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("close_path-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Corner Mode" || propKey === "corner_mode") {
                        const CORNER_MODES = [
                            { full: "Round", short: "Bezier" },
                            { full: "Bevel", short: "Bevel" },
                            { full: "Miter", short: "Lowpoly" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curC = (n.properties && n.properties.corner_mode) ? n.properties.corner_mode : (w.value || "Round");
                            const cObj = CORNER_MODES.find(m => m.full.toLowerCase() === curC.toLowerCase() || (m.short.toLowerCase() === curC.toLowerCase())) || CORNER_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const cLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Corner:") : "Corner:";
                            ctx.fillText(cLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(cLabel).width;
                            const btnX = Math.round(22 + labelW + 8);
                            const btnW = 68;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(cObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curC = (node.properties && node.properties.corner_mode) ? node.properties.corner_mode : "Round";
                            let curIdx = CORNER_MODES.findIndex(m => m.full.toLowerCase() === curC.toLowerCase() || m.short.toLowerCase() === curC.toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % CORNER_MODES.length);
                            const nextObj = CORNER_MODES[nextIdx];
                            node.properties.corner_mode = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("corner_mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "K Mode" || propKey === "k_mode") {
                        const K_MODES = [
                            { full: "k", short: "\\k" },
                            { full: "kf", short: "\\kf" },
                            { full: "ko", short: "\\ko" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curK = (n.properties && n.properties.k_mode) ? n.properties.k_mode : (w.value || "k");
                            const kObj = K_MODES.find(m => m.full.toLowerCase() === String(curK).toLowerCase().replace("\\", "")) || K_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const kLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Tag:") : "Tag:";
                            ctx.fillText(kLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(kLabel).width;
                            const btnX = Math.round(22 + labelW + 8);
                            const btnW = 48;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#0d9488";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#2dd4bf";
                            ctx.textAlign = "center";
                            ctx.fillText(kObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curK = (node.properties && node.properties.k_mode) ? node.properties.k_mode : "k";
                            let curIdx = K_MODES.findIndex(m => m.full.toLowerCase() === String(curK).toLowerCase().replace("\\", ""));
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % K_MODES.length);
                            const nextObj = K_MODES[nextIdx];
                            node.properties.k_mode = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("k_mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Kana Mode" || portName === "Modo Kana" || (portName === "Mode" && node.properties && (String(node.properties.operation).toLowerCase() === "kana")) || propKey === "kana_mode" || (propKey === "mode" && node.properties && (String(node.properties.operation).toLowerCase() === "kana"))) {
                        const KANA_MODES = [
                            { full: "Romaji to Hiragana", short: "Rom → Hira" },
                            { full: "Romaji to Katakana", short: "Rom → Kata" },
                            { full: "Hiragana to Katakana", short: "Hira → Kata" },
                            { full: "Katakana to Hiragana", short: "Kata → Hira" },
                            { full: "Kana to Romaji", short: "Kana → Rom" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curM = (n.properties && n.properties.mode) ? n.properties.mode : (w.value || "Romaji to Hiragana");
                            const mObj = KANA_MODES.find(m => m.full.toLowerCase() === String(curM).toLowerCase() || m.short.toLowerCase() === String(curM).toLowerCase()) || KANA_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const mLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Kana:") : "Kana:";
                            ctx.fillText(mLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(mLabel).width;
                            const btnX = Math.round(22 + labelW + 8);
                            const btnW = 76;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#0d9488";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#2dd4bf";
                            ctx.textAlign = "center";
                            ctx.fillText(mObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curM = (node.properties && node.properties.mode) ? node.properties.mode : "Romaji to Hiragana";
                            let curIdx = KANA_MODES.findIndex(m => m.full.toLowerCase() === String(curM).toLowerCase() || m.short.toLowerCase() === String(curM).toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % KANA_MODES.length);
                            const nextObj = KANA_MODES[nextIdx];
                            node.properties.mode = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("kana_mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Axis" || portName === "Axis Mode" || portName === "Eje" || portName === "Modo Eje" || propKey === "axis") {
                        const AXIS_MODES = [
                            { full: "none", short: (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("None") : "None" },
                            { full: "x", short: (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Axis X") : "Axis X" },
                            { full: "y", short: (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Axis Y") : "Axis Y" },
                            { full: "xy", short: (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Both") : "Both" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curAxis = String((n.properties && n.properties.axis !== undefined) ? n.properties.axis : (w.value || "none")).toLowerCase();
                            const aObj = AXIS_MODES.find(m => m.full.toLowerCase() === curAxis || m.short.toLowerCase() === curAxis) || AXIS_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const axisLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Refl.:") : "Refl.:";
                            ctx.fillText(axisLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(axisLabel).width;
                            const btnX = Math.round(22 + labelW + 6);
                            const btnW = 60;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(aObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curAxis = String((node.properties && node.properties.axis !== undefined) ? node.properties.axis : "none").toLowerCase();
                            const curIdx = AXIS_MODES.findIndex(m => m.full.toLowerCase() === curAxis || m.short.toLowerCase() === curAxis);
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % AXIS_MODES.length);
                            const nextObj = AXIS_MODES[nextIdx];
                            node.properties.axis = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("axis-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Tag" || propKey === "tag_type" || portName === "Tag Type") {
                        const COLOR_TAG_OPTIONS = [
                            { full: "\\1c", short: "\\1c" },
                            { full: "\\2c", short: "\\2c" },
                            { full: "\\3c", short: "\\3c" },
                            { full: "\\4c", short: "\\4c" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            let curTag = String((n.properties && n.properties.tag_type) ? n.properties.tag_type : (w.value || "\\1c")).trim();
                            if (!curTag.startsWith("\\")) curTag = "\\" + curTag;
                            const tObj = COLOR_TAG_OPTIONS.find(t => t.full.toLowerCase() === curTag.toLowerCase()) || COLOR_TAG_OPTIONS[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const tagLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Tag:") : "Tag:";
                            ctx.fillText(tagLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(tagLabel).width;
                            const btnX = Math.round(22 + labelW + 8);
                            const btnW = 54;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#38bdf8";
                            ctx.font = "bold 11px monospace";
                            ctx.textAlign = "center";
                            ctx.fillText(tObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            let curTag = String((node.properties && node.properties.tag_type) ? node.properties.tag_type : "\\1c").trim();
                            if (!curTag.startsWith("\\")) curTag = "\\" + curTag;
                            const curIdx = COLOR_TAG_OPTIONS.findIndex(t => t.full.toLowerCase() === curTag.toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % COLOR_TAG_OPTIONS.length);
                            const nextObj = COLOR_TAG_OPTIONS[nextIdx];
                            node.properties.tag_type = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("tag_type-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Alpha Tag" || portName === "Tag Alpha" || propKey === "alpha_tag") {
                        const ALPHA_TAG_OPTIONS = [
                            { full: "\\alpha", short: "\\alpha" },
                            { full: "\\1a", short: "\\1a" },
                            { full: "\\2a", short: "\\2a" },
                            { full: "\\3a", short: "\\3a" },
                            { full: "\\4a", short: "\\4a" },
                            { full: "\\12a", short: "\\12a" },
                            { full: "\\13a", short: "\\13a" },
                            { full: "\\14a", short: "\\14a" },
                            { full: "\\23a", short: "\\23a" },
                            { full: "\\24a", short: "\\24a" },
                            { full: "\\34a", short: "\\34a" },
                            { full: "\\123a", short: "\\123a" },
                            { full: "\\124a", short: "\\124a" },
                            { full: "\\134a", short: "\\134a" },
                            { full: "\\234a", short: "\\234a" },
                            { full: "\\1234a", short: "\\1234a" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            let curTag = String((n.properties && n.properties.alpha_tag) ? n.properties.alpha_tag : (w.value || "\\alpha")).trim();
                            if (!curTag.startsWith("\\")) curTag = "\\" + curTag;
                            const tObj = ALPHA_TAG_OPTIONS.find(t => t.full.toLowerCase() === curTag.toLowerCase()) || ALPHA_TAG_OPTIONS[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            const btnX = 22;
                            const btnW = 58;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#38bdf8";
                            ctx.textAlign = "center";
                            ctx.fillText(tObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            let curTag = String((node.properties && node.properties.alpha_tag) ? node.properties.alpha_tag : "\\alpha").trim();
                            if (!curTag.startsWith("\\")) curTag = "\\" + curTag;
                            const curIdx = ALPHA_TAG_OPTIONS.findIndex(t => t.full.toLowerCase() === curTag.toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % ALPHA_TAG_OPTIONS.length);
                            const nextObj = ALPHA_TAG_OPTIONS[nextIdx];
                            node.properties.alpha_tag = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("alpha_tag-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Fill Rule" || propKey === "fill_type") {
                        const FILL_RULE_MODES = [
                            { full: "EvenOdd", short: "EvenOdd" },
                            { full: "NonZero", short: "NonZero" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curF = (n.properties && n.properties.fill_type) ? n.properties.fill_type : (w.value || "EvenOdd");
                            const fObj = FILL_RULE_MODES.find(m => m.full.toLowerCase() === curF.toLowerCase()) || FILL_RULE_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const fillLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Rule:") : "Rule:";
                            ctx.fillText(fillLabel, 22, drawY + 13);

                            const labelW = ctx.measureText(fillLabel).width;
                            const btnX = Math.round(22 + labelW + 8);
                            const btnW = 68;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(fObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curF = (node.properties && node.properties.fill_type) ? node.properties.fill_type : "EvenOdd";
                            const curIdx = FILL_RULE_MODES.findIndex(m => m.full.toLowerCase() === curF.toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % FILL_RULE_MODES.length);
                            const nextObj = FILL_RULE_MODES[nextIdx];
                            node.properties.fill_type = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("fill_type-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Auto-Intersect" || portName === "Auto-Intersecc." || propKey === "clean_self_intersect") {
                        const AUTO_CLEAN_MODES = [
                            { full: "1", short: "Auto (1)" },
                            { full: "0", short: "Off (0)" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curC = String((n.properties && n.properties.clean_self_intersect !== undefined) ? n.properties.clean_self_intersect : (w.value !== undefined ? w.value : "1"));
                            const cObj = AUTO_CLEAN_MODES.find(m => m.full === curC) || AUTO_CLEAN_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const autoLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Clean:") : "Clean:";
                            ctx.fillText(autoLabel, 22, drawY + 13);

                            const btnX = 76;
                            const btnW = 68;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(cObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curC = String((node.properties && node.properties.clean_self_intersect !== undefined) ? node.properties.clean_self_intersect : "1");
                            const curIdx = AUTO_CLEAN_MODES.findIndex(m => m.full === curC);
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % AUTO_CLEAN_MODES.length);
                            const nextObj = AUTO_CLEAN_MODES[nextIdx];
                            node.properties.clean_self_intersect = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("clean_self_intersect-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Trajectory Mode" || propKey === "traj_mode" || propKey === "trajectory_mode") {
                        const TRAJ_MODES = [
                            { full: "Free Wander", short: "Free" },
                            { full: "Bounded", short: "Bounded" },
                            { full: "Closed Loop", short: "Closed" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curM = (n.properties && (n.properties.traj_mode || n.properties.trajectory_mode)) ? (n.properties.traj_mode || n.properties.trajectory_mode) : (w.value || "Free Wander");
                            const mObj = TRAJ_MODES.find(m => m.full.toLowerCase() === String(curM).toLowerCase() || m.short.toLowerCase() === String(curM).toLowerCase()) || TRAJ_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            const mLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("Mode:") : "Mode:";
                            ctx.fillText(mLabel, 22, drawY + 13);

                            const btnX = 58;
                            const btnW = 86;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a78bfa";
                            ctx.textAlign = "center";
                            const shortTranslated = (window.PyxisI18n && window.PyxisI18n.translateMode) ? window.PyxisI18n.translateMode(mObj.full) : mObj.short;
                            ctx.fillText(shortTranslated || mObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curM = (node.properties && (node.properties.traj_mode || node.properties.trajectory_mode)) ? (node.properties.traj_mode || node.properties.trajectory_mode) : "Free Wander";
                            let curIdx = TRAJ_MODES.findIndex(m => m.full.toLowerCase() === String(curM).toLowerCase() || m.short.toLowerCase() === String(curM).toLowerCase());
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % TRAJ_MODES.length);
                            const nextObj = TRAJ_MODES[nextIdx];
                            node.properties.traj_mode = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("traj_mode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    } else if (portName === "Tag Mode" || propKey === "tagmode") {
                        const TAG_MODES = [
                            { full: "ipol", short: "ipol" },
                            { full: "line", short: "line" }
                        ];
                        w.draw = function(ctx, n, width, y, height) {
                            const drawY = (w.last_y !== undefined) ? w.last_y : y;
                            const curM = String((n.properties && n.properties.tagmode) ? n.properties.tagmode : (w.value || "ipol")).toLowerCase();
                            const mObj = TAG_MODES.find(m => m.full === curM) || TAG_MODES[0];

                            ctx.save();
                            ctx.font = "bold 11px monospace";
                            ctx.fillStyle = "#94a3b8";
                            ctx.textAlign = "left";
                            ctx.fillText("tagmode:", 22, drawY + 13);

                            const labelW = ctx.measureText("tagmode:").width;
                            const btnX = Math.round(22 + labelW + 6);
                            const btnW = 54;
                            const btnH = 18;
                            w._btnX = btnX; w._btnW = btnW;

                            ctx.fillStyle = "#12161f";
                            ctx.strokeStyle = "#8b5cf6";
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX, drawY, btnW, btnH, 5);
                            else ctx.rect(btnX, drawY, btnW, btnH);
                            ctx.fill();
                            ctx.stroke();

                            ctx.fillStyle = "#a7f3d0";
                            ctx.textAlign = "center";
                            ctx.fillText(mObj.short, btnX + btnW / 2, drawY + 13);
                            ctx.restore();
                        };
                        w.onClick = function(canvas) {
                            const curM = String((node.properties && node.properties.tagmode) ? node.properties.tagmode : "ipol").toLowerCase();
                            const curIdx = TAG_MODES.findIndex(m => m.full === curM);
                            const nextIdx = (curIdx === -1) ? 0 : ((curIdx + 1) % TAG_MODES.length);
                            const nextObj = TAG_MODES[nextIdx];
                            node.properties.tagmode = nextObj.full;
                            w.value = nextObj.full;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            if (canvas && canvas.draw) canvas.draw(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("tagmode-change");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        };
                    }
                } else {
                    setupSingleLineTextWidget(node, w, portName, propKey);
                }
            });

            if (node.properties && node.properties.expandable) {
                if (node.widgets) {
                    node.widgets = node.widgets.filter(w => w.name !== "add_sub_buttons");
                }
                const addSubWidget = {
                    name: "add_sub_buttons",
                    type: "custom",
                    width: 100,
                    draw: function(ctx, n, width, y, H) {
                        const drawY = y + 4;
                        this.last_y = drawY;
                        const btnW = 34;
                        const btnH = 22;
                        const gap = 8;
                        const totalW = btnW * 2 + gap;
                        const x1 = Math.max(10, Math.floor((width - totalW) / 2));
                        const x2 = x1 + btnW + gap;

                        ctx.save();
                        ctx.font = "bold 14px sans-serif";
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";

                        ctx.fillStyle = "#1e242d";
                        ctx.strokeStyle = "#8b5cf6";
                        ctx.lineWidth = 1.5;
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(x1, drawY, btnW, btnH, 4);
                        else ctx.rect(x1, drawY, btnW, btnH);
                        ctx.fill();
                        ctx.stroke();

                        ctx.fillStyle = "#ffffff";
                        ctx.fillText("+", x1 + btnW / 2, drawY + btnH / 2 + 1);

                        const minInputs = 2;
                        const canRemove = n.inputs && (n.inputs.length > minInputs);

                        ctx.fillStyle = canRemove ? "#1e242d" : "#12151b";
                        ctx.strokeStyle = canRemove ? "#ef4444" : "#4b5563";
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(x2, drawY, btnW, btnH, 4);
                        else ctx.rect(x2, drawY, btnW, btnH);
                        ctx.fill();
                        ctx.stroke();

                        ctx.fillStyle = canRemove ? "#ffffff" : "#6b7280";
                        ctx.fillText("-", x2 + btnW / 2, drawY + btnH / 2 + 1);

                        ctx.restore();
                    },
                    callback: (w, canvas, n, pos, event) => {
                        const targetNode = n || (canvas && canvas.title ? canvas : node);
                        const localX = pos ? pos[0] : 0;
                        const width = targetNode.size ? targetNode.size[0] : 140;
                        const btnW = 34, gap = 8, totalW = btnW * 2 + gap;
                        const x1 = Math.max(10, Math.floor((width - totalW) / 2));
                        const x2 = x1 + btnW + gap;

                        if (localX >= x1 - 4 && localX <= x1 + btnW + 4) {
                            const inputs = targetNode.inputs || [];
                            let inCount = 0;
                            for (let inp of inputs) {
                                if (inp.name && (inp.name.startsWith("In") || inp.name.startsWith("in"))) {
                                    const num = parseInt(inp.name.replace(/^[a-zA-Z\s_]+/, ""));
                                    if (!isNaN(num) && num > inCount) inCount = num;
                                }
                            }
                            const nextName = "In" + (inCount > 0 ? (inCount + 1) : (inputs.length + 1));
                            targetNode.addInput(nextName, "data");
                            if (!targetNode.properties) targetNode.properties = {};
                            targetNode.properties[nextName] = "";
                            updateNodeModeInputs(targetNode);
                            if (targetNode.computeSize) targetNode.size = targetNode.computeSize();
                            const activeCanvas = LGraphCanvas.active_canvas || canvas;
                            if (activeCanvas) activeCanvas.setDirty(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("add-input");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        } else if (localX >= x2 - 4 && localX <= x2 + btnW + 4) {
                            if (targetNode.inputs && targetNode.inputs.length > 2) {
                                const lastInp = targetNode.inputs[targetNode.inputs.length - 1];
                                const lastProp = lastInp ? (lastInp.property || lastInp.name) : null;
                                targetNode.removeInput(targetNode.inputs.length - 1);
                                if (lastProp && targetNode.properties && targetNode.properties[lastProp] !== undefined) {
                                    delete targetNode.properties[lastProp];
                                }
                                updateNodeModeInputs(targetNode);
                                if (targetNode.computeSize) targetNode.size = targetNode.computeSize();
                                const activeCanvas = LGraphCanvas.active_canvas || canvas;
                                if (activeCanvas) activeCanvas.setDirty(true, true);
                                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("remove-input");
                                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            }
                        }
                    }
                };
                node.addWidget("custom", "+ / -", null, addSubWidget.callback, addSubWidget);
                const addedW = node.widgets[node.widgets.length - 1];
                addedW.draw = addSubWidget.draw;
            }

remainingOldInputs.forEach(unmatchedInp => {
                if (unmatchedInp && unmatchedInp.link !== null && unmatchedInp.link !== undefined) {
                    const oldLinkId = unmatchedInp.link;
                    if (graph && graph.links && graph.links[oldLinkId]) {
                        if (graph.removeLink) {
                            graph.removeLink(oldLinkId);
                        } else {
                            delete graph.links[oldLinkId];
                        }
                    }
                }
            });

            if (node.computeSize) {
                const curW = (node.size && node.size[0] > 0) ? node.size[0] : 0;
                const sz = node.computeSize();
                node.size = [Math.max(curW, sz[0]), sz[1]];
            }
        }

        const CONCATENAR_MODES = [
            { full: "nil", short: "NIL" },
            { full: "espacio", short: "SPACE" },
            { full: "coma", short: "," },
            { full: "punto_coma", short: ";" },
            { full: "salto", short: "ENTER" },
            { full: "zip", short: "ZIP" }
        ];


        function createNodeConstructor(category, node_name, definition, is_system) {
            const node_kind = definition.node_kind || "data";
            return function() {
                this.title = definition.name || node_name;
                this.type = category ? (category + "/" + (definition.name || node_name)) : (definition.name || node_name);
                addProperties(this, definition);
                this.resizable = true;

                const nodeCat = typeof window.getNodeCategory === "function" ? window.getNodeCategory(this) : category;
                const themeCategories = (window.PyxisThemeManager && window.PyxisThemeManager.THEMES && typeof window.PyxisThemeManager.getCurrentTheme === "function" && window.PyxisThemeManager.THEMES[window.PyxisThemeManager.getCurrentTheme()])
                    ? window.PyxisThemeManager.THEMES[window.PyxisThemeManager.getCurrentTheme()].categories
                    : {};
                const themeCatEntry = (window.CATEGORY_COLORS && window.CATEGORY_COLORS[nodeCat]) || (themeCategories && themeCategories[nodeCat]);
                const themeCatColor = typeof themeCatEntry === "object" && themeCatEntry !== null ? themeCatEntry.color : themeCatEntry;
                this.color = themeCatColor || definition.color || "#4b5563";
                this.boxcolor = (window.PYXIS_THEME && window.PYXIS_THEME.textMuted) || "#94a3b8";
                if (window.PYXIS_THEME && window.PYXIS_THEME.nodeBgGradient && window.PYXIS_THEME.nodeBgGradient.start) {
                    this.bgcolor = window.PYXIS_THEME.nodeBgGradient.start;
                }

                this.computeSize = function() {
                    let title_text = this.title || node_name || "";
                    let title_len = title_text.length;
                    
                    let num_in = this.inputs ? this.inputs.length : 0;
                    let num_out = this.outputs ? this.outputs.length : 0;
                    let max_slots = Math.max(num_in, num_out);
                    let num_wid = this.widgets ? this.widgets.length : 0;

                    let max_slot_label_len = 0;
                    let max_in_label_len = 0;
                    if (this.inputs) {
                        for (let i = 0; i < this.inputs.length; i++) {
                            if (this.inputs[i].name) {
                                max_slot_label_len = Math.max(max_slot_label_len, this.inputs[i].name.length);
                                max_in_label_len = Math.max(max_in_label_len, this.inputs[i].name.length);
                            }
                        }
                    }
                    let max_out_label_len = 0;
                    if (this.outputs) {
                        for (let i = 0; i < this.outputs.length; i++) {
                            if (this.outputs[i].name) {
                                max_slot_label_len = Math.max(max_slot_label_len, this.outputs[i].name.length);
                                max_out_label_len = Math.max(max_out_label_len, this.outputs[i].name.length);
                            }
                        }
                    }

                    let combined_slot_w = (max_in_label_len > 0 && max_out_label_len > 0) ? (max_in_label_len * 7 + max_out_label_len * 7 + 45) : (max_slot_label_len * 7 + 34);
                    let req_w = Math.max(105, title_len * 7.5 + 28, combined_slot_w);
                    if (num_wid > 0) {
                        if (node_name === "Concatenate") {
                            req_w = Math.max(145, title_len * 8.5 + 48, max_slot_label_len * 7.5 + 50);
                        } else if (node_name === "Output") {
                            req_w = Math.max(200, title_len * 8.5 + 48, max_slot_label_len * 7.5 + 50);
                        } else if (node_name === "Dynamic Format" || node_name === "Number" || node_name === "Text" || node_name === "Get Var") {
                            req_w = Math.max(130, title_len * 7.5 + 34, max_slot_label_len * 7 + 36);
                        } else if (node_name === "Define Vars") {
                            req_w = Math.max(220, title_len * 7.5 + 34);
                        } else {
                            req_w = Math.max(req_w, 150);
                        }
                    }
                    if (this.title === "Main Loop" || node_name === "Main Loop" || this.title === "Bucle Primario") req_w = 255;
                    if (num_wid === 0 && max_slots <= 1) {
                        req_w = Math.max(105, title_len * 7.2 + 24, max_slot_label_len * 7 + 28);
                    }

                    if (node_name === "Lead In" || node_name === "Lead Out" || node_name === "Middle 1" || node_name === "Middle 2" || node_name === "Loop 1" || node_name === "Loop 2") req_w = Math.max(req_w, 140);
                    else if (node_name === "Benchmark Math") req_w = Math.max(req_w, 225);
                    else if (node_name === "Slicer" || node_name === "Multi" || title_text === "Slicer" || title_text === "Multi") req_w = Math.max(req_w, 235);
                    else if (node_name.includes("Bordes") || title_text.includes("Bordes") || node_name.includes("Concentric") || title_text.includes("Concentric")) req_w = Math.max(req_w, 235);
                    else if (node_name === "Modulator" || title_text === "Modulator" || title_text === "Modulador" || (this.type && this.type.includes("Audio"))) req_w = Math.max(req_w, 225);
                    else if (node_name.includes("MultiRandom") || node_name.includes("MultiTag")) req_w = Math.max(req_w, 210);
                    else if (node_name.includes("module") || title_text.includes("module")) req_w = Math.max(req_w, 145);
                    else if (node_name === "SquareWave" || node_name === "SineWave" || node_name === "SawtoothWave") req_w = Math.max(req_w, 150);
                    else if (node_name.startsWith("Flor Sakura") || node_name.startsWith("Sakura Flower")) req_w = Math.max(req_w, 145);
                    else if (node_name === "Seno" || node_name === "Coseno" || node_name === "Tangente" || node_name === "Sin" || node_name === "Cos" || node_name === "Tan") req_w = Math.max(req_w, 145);
                    else if (node_name === "RadToDeg" || node_name === "DegToRad" || node_name === "Radians" || node_name === "Degrees") req_w = Math.max(req_w, 135);
                    else if (node_name === "EaseIn" || node_name === "EaseOut" || node_name === "EaseInOut") req_w = Math.max(req_w, 155);
                    else if (node_name === "Parse ASS Time") req_w = Math.max(req_w, 205);
                    else if (node_name === "Format ASS Time") req_w = Math.max(req_w, 200);
                    else if (node_name === "Offset") req_w = Math.max(req_w, 200);
                    else if (node_name === "Duration" || node_name === "Duración" || node_name.includes("Duration") || node_name.includes("Duración") || node_name.includes("Duracion")) req_w = Math.max(req_w, 235);
                    else if (node_name === "Move Tag" || node_name === "Mover Tags" || node_name === "Mover Tag" || node_name.includes("Move Tag") || node_name.includes("Mover Tag") || node_name === "Move Text" || node_name === "Mover Texto" || node_name.includes("Move Text") || node_name.includes("Mover Texto")) req_w = Math.max(req_w, 195);
                    else if (node_name === "Round Corners" || node_name === "Esquinas Redondeadas") req_w = Math.max(req_w, 185);
                    else if (node_name === "Heart Border" || node_name === "Corazón Borde") req_w = Math.max(req_w, 135);
                    else if (node_name.startsWith("Musical Note") || node_name.startsWith("Nota Musical")) req_w = Math.max(req_w, 140);
                    else if (node_name === "Lowercase" || node_name === "Minúsculas" || node_name === "Uppercase" || node_name === "Mayúsculas") req_w = Math.max(req_w, 120);

                    let multiline_extra_h = 0;
                    if (this.properties) {
                        for (const propKey in this.properties) {
                            if (propKey === "colors" || propKey === "formats" || propKey === "mode" || propKey === "k_mode" || propKey === "corner_mode" || propKey === "cap_mode" || propKey === "tag_type" || propKey === "alpha_tag" || propKey === "fill_rule" || propKey === "anchor" || propKey === "operation" || propKey === "axis") continue;
                            const propVal = this.properties[propKey];
                            if (propVal !== undefined && propVal !== null) {
                                const text = String(propVal);
                                if (text.length > 0) {
                                    const lines = text.split('\n');
                                    let max_line_tw = 0;
                                    lines.forEach(l => {
                                        const tw = getExactTextWidth(l, "bold 11px Consolas, monospace");
                                        if (tw > max_line_tw) max_line_tw = tw;
                                    });
                                    if (max_line_tw > 0) {
                                        const right_space = getNodeRightReserve(this);
                                        const boxW = Math.max(65, Math.ceil(max_line_tw + 28));
                                        req_w = Math.max(req_w, 22 + boxW + right_space);
                                    }
                                    if (propKey === "variables" && lines.length > 1) {
                                        multiline_extra_h = (lines.length - 1) * 22;
                                    }
                                }
                            }
                        }
                    }
                    if (this.widgets) {
                        for (let i = 0; i < this.widgets.length; i++) {
                            const w = this.widgets[i];
                            if (!w) continue;
                            const isBtn = (w.type === "button" || w._isButton || (w.spec && w.spec.type === "button") || typeof w.onClick === "function");
                            if (isBtn) continue;
                            if (w && w.value !== undefined && w.value !== null) {
                                const wText = String(w.value);
                                if (wText.length > 0) {
                                    const lines = wText.split('\n');
                                    let max_line_tw = 0;
                                    lines.forEach(l => {
                                        const tw = getExactTextWidth(l, "bold 11px Consolas, monospace");
                                        if (tw > max_line_tw) max_line_tw = tw;
                                    });
                                    if (max_line_tw > 0) {
                                        const right_space = getNodeRightReserve(this);
                                        const boxW = Math.max(65, Math.ceil(max_line_tw + 28));
                                        req_w = Math.max(req_w, 22 + boxW + right_space);
                                    }
                                }
                            }
                        }
                    }

                    let slots_h = max_slots * 19;
                    let widgets_h = num_wid > 0 ? (num_wid * 22 + 2) : 0;
                    let req_h = 26 + slots_h + widgets_h + multiline_extra_h + (num_wid > 1 ? 12 : 6);
                    if (node_name === "Ipol" || node_name === "Interpolador" || node_name.endsWith("/Ipol")) req_h += 8;
                    if (category === "Time" || node_name === "Lead In" || node_name === "Lead Out" || node_name === "Middle 1" || node_name === "Middle 2" || node_name === "Loop 1" || node_name === "Loop 2" || node_name === "Offset" || node_name === "Parse ASS Time" || node_name === "Format ASS Time" || node_name === "Duration" || node_name === "Duración" || node_name === "Time to Frame" || node_name === "Frame to Time" || node_name === "Tiempo a Frame" || node_name === "Frame a Tiempo" || node_name === "Text" || node_name === "Texto" || node_name === "String" || node_name === "Number" || node_name === "Número") req_h += 12;
                    if (node_name === "Benchmark Math") req_h = Math.max(req_h, 65);

                    if (this.widgets_up) {
                        req_h = 26 + 22 + 6 + slots_h + 28 + 4;
                    }

                    if (num_wid === 0) {
                        req_h = 26 + slots_h + 4;
                    }

                    if (node_name === "Color Picker") {
                        const num_colors = (this.properties && this.properties.colors && Array.isArray(this.properties.colors)) ? this.properties.colors.length : 1;
                        req_w = Math.max(req_w, 210);
                        req_h = 30 + num_colors * 22 + 28;
                        return [req_w, req_h];
                    }

                    req_h += 12; // Extra surgical space for help '?' icon and resize handle

                    return [req_w, req_h];
                };

                this.updateMultilineSize = function() {
                    const sz = this.computeSize();
                    this.size = [Math.max(this.size ? this.size[0] : 250, sz[0]), sz[1]];
                };

                let initial_size = this.computeSize ? this.computeSize() : [200, 100];
                this.size = [initial_size[0], initial_size[1]];
                this.title_color = "#FFFFFF";

                this.onConfigure = function(info) {
                    let calc_size = this.computeSize ? this.computeSize() : [200, 100];
                    this.size = [
                        Math.max(calc_size[0], Number(this.size ? (this.size[0] || this.size["0"] || calc_size[0]) : calc_size[0])),
                        Math.max(calc_size[1], Number(this.size ? (this.size[1] || this.size["1"] || calc_size[1]) : calc_size[1]))
                    ];
                    if (this.widgets) {
                        for (let i = 0; i < this.widgets.length; ++i) {
                            let w = this.widgets[i];
                            if (w.property && this.properties[w.property] !== undefined) {
                                w.value = this.properties[w.property];
                            }
                        }
                    }
                    if (info.inputs) {
                        let current_inputs = this.inputs ? this.inputs.length : 0;
                        for (let i = current_inputs; i < info.inputs.length; ++i) {
                            this.addInput(info.inputs[i].name, info.inputs[i].type);
                        }
                    }
                };

                (definition.inputs || []).forEach((input_name, input_index) => {
                    let input_type = "data";
                    if (is_system) {
                        if (node_kind === "output" && input_index === 0) input_type = "loop";
                        else if (node_kind === "max_loop" && input_index === 0) input_type = "loop";
                        else if (node_kind === "set_vars" && input_index === 0) input_type = "loop";
                        else if (node_kind === "code_script" && input_index === 0) input_type = "loop";
                        else if (input_name === "Loop In" || input_name === "Loop / Domain" || input_name === "In (loop)" || input_name === "Loop") input_type = "loop";
                    }
                    this.addInput(input_name, input_type);
                });

                (definition.outputs || []).forEach((output_name, output_index) => {
                    let output_type = "data";
                    if (is_system && output_index === 0) {
                        if (node_kind === "main_loop") output_type = "loop";
                        else if (node_kind === "max_loop") output_type = "loop";
                        else if (node_kind === "set_vars") output_type = "loop";
                        else if (node_kind === "code_script") output_type = "loop";
                        else if (output_name === "Loop Out" || output_name === "Loop") output_type = "loop";
                    }
                    this.addOutput(output_name, output_type);
                });

                if (!is_system) {
                    this.addOutput("Data", "data");
                }

                if (node_name === "Color Picker") {
                    setupColorPickerNode(this);
                } else if (node_name === "MultiTag" || definition.node_kind === "tag_master") {
                    (definition.widgets || []).forEach(widget => {
                        const property = widget.property;
                        const initialValue = this.properties[property] !== undefined ? this.properties[property] : (widget.default || "");
                        const callback = value => { this.properties[property] = value; };
                        let created_widget = null;
                        if (widget.type === "combo") {
                            created_widget = this.addWidget("combo", widget.name, initialValue, callback, { values: widget.values || [] });
                        } else {
                            created_widget = this.addWidget("text", widget.name, initialValue, callback);
                        }
                        if (created_widget) created_widget.property = property;
                    });
                    setupTagMasterNode(this);
                } else if (node_name === "Memory" || node_name === "Variables/Memory") {
                    (definition.widgets || []).forEach(widget => {
                        const property = widget.property;
                        const initialValue = this.properties[property] !== undefined ? this.properties[property] : (widget.default || "");
                        const callback = value => { this.properties[property] = value; };
                        let created_widget = null;
                        if (widget.type === "combo") {
                            created_widget = this.addWidget("combo", widget.name, initialValue, callback, { values: widget.values || [] });
                        } else {
                            created_widget = this.addWidget("text", widget.name, initialValue, callback);
                        }
                        if (created_widget) created_widget.property = property;
                    });
                    setupMemoryNode(this);
                } else if (node_name === "Conditioner" || node_name === "Functions/Conditioner") {
                    (definition.widgets || []).forEach(widget => {
                        const property = widget.property;
                        const initialValue = this.properties[property] !== undefined ? this.properties[property] : (widget.default || "");
                        const callback = value => { this.properties[property] = value; };
                        let created_widget = this.addWidget("text", widget.name, initialValue, callback);
                        if (created_widget) created_widget.property = property;
                    });
                    setupConditionerNode(this);
                } else if (node_name === "Define Vars" || node_name === "Variables/Define Vars") {
                    (definition.widgets || []).forEach(widget => {
                        const property = widget.property;
                        const initialValue = this.properties[property] !== undefined ? this.properties[property] : (widget.default || "");
                        const callback = value => { this.properties[property] = value; };
                        let created_widget = this.addWidget("text", widget.name, initialValue, callback);
                        if (created_widget) created_widget.property = property;
                    });
                    setupDefineVarsNode(this);
                } else if (node_name === "Main Loop" || node_name === "Loops/Main Loop") {
                    setupMainLoopNode(this);
                } else if (node_name === "MaxLoop" || node_name === "Loops/MaxLoop") {
                    setupMaxLoopNode(this);
                } else if (node_name === "Output" || node_name === "System/Output") {
                    setupOutputNode(this);
                } else if (node_name === "Previewer" || node_name === "System/Previewer") {
                    setupPreviewerNode(this);
                } else if (node_name === "Polar to Cartesian" || node_name === "Functions/Polar to Cartesian") {
                    setupPolarToCartesianNode(this);
                } else if (node_name === "Script Code" || node_name === "System/Script Code") {
                    setupScriptCodeNode(this);
                } else if (node_name === "Concatenate") {
                    setupConcatenateNode(this);
                } else if (node_name === "Glitter" || node_name.includes("Glitter")) {
                    setupGlitterNode(this);
                } else if (node_name === "Once" || node_name.includes("Once")) {
                    setupOnceNode(this);
                } else if (node_name === "Only" || node_name.includes("Only")) {
                    setupOnlyNode(this);
                } else if (node_name === "Waveform" || node_name === "Audio/Waveform") {
                    setupAudioWaveformNode(this);
                } else if (node_name === "Library" || node_name === "Shape/Library") {
                    setupShapesLibNode(this);
                } else if (node_name === "Text to Shape" || node_name.includes("Text to Shape") || node_name === "Texto a Forma" || node_name.includes("Texto a Forma")) {
                    setupTextToShapeNode(this);
                } else if (node_name === "IMG to Shape" || node_name.includes("IMG to Shape")) {
                    setupImgToShapeNode(this);
                } else if (node_name === "IMG to pixels" || node_name.includes("IMG to pixels")) {
                    setupImgToPixelsNode(this);
                } else if (node_name === "Animation" || node_name === "Functions/Animation") {
                    setupAnimationNode(this);
                } else if (node_name === "MultiRandom" || node_name.includes("MultiRandom")) {
                    setupRandomMasterNode(this);
                } else if (category === "Audio" || category === "Shape" || category === "Functions" || (category === "Math" && node_name !== "MultiRandom") || node_name === "Math" || node_name === "Text" || node_name === "Text on Path" || node_name === "Bezier Curve" || node_name === "Particles" || node_name === "Concentric Borders" || node_name === "Clip Gradient" || node_name === "Tag Oscillator" || node_name === "Tag Manipulator" || node_name === "Retime" || node_name === "Color Gradient" || node_name === "MultiTag" || node_name === "Move Tag" || node_name === "Move Text" || node_name.includes("Move Tag") || node_name.includes("Move Text") || node_name === "Sys Var" || node_name === "Module" || node_name === "Time to Frame" || node_name === "Frame to Time" || node_name === "Tiempo a Frame" || node_name === "Frame a Tiempo" || node_name === "Synced" || node_name === "Interpolator" || node_name === "Benchmark Math") {
                    setupDynamicInlineNode(this);
                } else if (node_name === "Offset" || node_name.includes("Offset")) {
                    setupOffsetNode(this);
                } else if (node_name === "Parse ASS Time" || node_name.includes("Parse ASS Time")) {
                    setupParseASSTimeNode(this);
                } else if (node_name === "Format ASS Time" || node_name.includes("Format ASS Time")) {
                    setupFormatASSTimeNode(this);
                } else if (node_name === "Dynamic Format" || node_name.includes("Dynamic Format") || node_name.includes("Dynamic Format")) {
                    setupDynamicFormatNode(this);
                } else if (node_name === "Get Var" || node_name.includes("Get Var")) {
                    setupGetVarNode(this);
                } else if (node_name === "Duration" || node_name === "Duración" || node_name.includes("Duration") || node_name.includes("Duración") || node_name.includes("Duracion")) {
                    setupDurationNode(this);
                } else if (node_name === "String" || node_name === "Number" || node_name === "Número" || node_name === "Texto") {
                    setupValueUnitNode(this);
                } else if (category === "Time" || node_name === "Lead In" || node_name === "Lead Out" || node_name === "Middle 1" || node_name === "Middle 2" || node_name === "Loop 1" || node_name === "Loop 2") {
                    setupTimeNode(this);
                } else {
                    (definition.widgets || []).forEach(widget => {
                        const property = widget.property;
                        const initialValue = this.properties[property] !== undefined ? this.properties[property] : (widget.default || "");
                        const callback = value => { this.properties[property] = value; };
                        let created_widget = null;
                        if (widget.type === "combo") {
                            created_widget = this.addWidget("combo", widget.name, initialValue, callback, { values: widget.values || [] });
                        } else if (widget.type === "toggle" || widget.type === "checkbox") {
                            const boolVal = (initialValue === true || initialValue === "true" || initialValue === "1" || initialValue === 1);
                            created_widget = this.addWidget("toggle", widget.name, boolVal, callback);
                        } else if (widget.type === "textarea") {
                            const btnName = widget.name ? "Editar " + widget.name : "Abrir Editor";
                            created_widget = this.addWidget("button", btnName, null, () => openInlineMultilineEditor(this, property, widget.name));
                            
                            this.onDblClick = function() {
                                openInlineMultilineEditor(this, property, widget.name);
                                return true;
                            };

                            const oldDraw = this.onDrawForeground;
                            this.onDrawForeground = function(ctx) {
                                if (oldDraw) oldDraw.call(this, ctx);
                                if (this.flags && this.flags.collapsed) return;

                                const text = this.properties[property] || "";
                                if (!text.trim()) return;

                                ctx.fillStyle = "#a7f3d0";
                                ctx.font = "12px monospace";
                                const lines = text.split('\n');
                                let y = 68;
                                for(let i = 0; i < lines.length; i++) {
                                    if (y > this.size[1] - 10) {
                                        ctx.fillText("...", 14, y); break;
                                    }
                                    ctx.fillText(lines[i], 14, y);
                                    y += 18;
                                }
                            };
                        } else {
                            created_widget = this.addWidget("text", widget.name, initialValue, callback);
                            setupSingleLineTextWidget(this, created_widget, widget.name, property);
                        }
                        if (created_widget) created_widget.property = property;
                    });
                }

                if (this.computeSize) {
                    let sz = this.computeSize();
                    if (node_name === "Color Picker") {
                        sz[0] = Math.max(sz[0], 210);
                    } else if (node_name === "Text" || node_name === "Number" || node_name === "Number") {
                        sz[0] = Math.max(sz[0], 130);
                    }
                    if (definition.properties && definition.properties.expandable && node_name !== "Concatenate" && node_name !== "Dynamic Format" && !node_name.includes("Dynamic Format")) {
                        sz[1] += 6;
                    }
                    this.size = sz;
                }

            };
        }

        const FALLBACK_SYSTEM_NODES = {
            "Basics": {
                "Text": {
                    "node_kind": "text", "inputs": ["Text"], "outputs": ["Out"], "color": "#0F766E",
                    "properties": { "operation": "strip_tags" },
                    "widgets": []
                },
                "String": {
                    "node_kind": "data", "inputs": [], "outputs": ["String"], "color": "#4B4B4B",
                    "properties": { "value": "" }, "widgets": [{ "type": "text", "name": "Text", "property": "value" }]
                },
                "Concatenate": {
                    "node_kind": "data", "inputs": ["In1", "In2"], "outputs": ["String"], "color": "#4B4B4B",
                    "properties": { "expandable": true, "separator": "nil" },
                    "widgets": []
                },
                "Dynamic Format": {
                    "node_kind": "data", "inputs": ["In1"], "outputs": ["String"], "color": "#4B4B4B",
                    "properties": { "format": "%s", "expandable": true },
                    "widgets": [{ "type": "text", "name": "Format", "property": "format" }]
                },
                "Number": {
                    "node_kind": "data", "inputs": [], "outputs": ["Number"], "color": "#1A5F4C",
                    "properties": { "value": "0" }, "widgets": [{ "type": "text", "name": "Value", "property": "value" }]
                },
                "Color Picker": {
                    "node_kind": "data", "inputs": [], "outputs": ["Color List", "ASS Color"], "color": "#1A4A5F",
                    "properties": { "colors": ["#FFFFFF"], "formats": ["ASS"] },
                    "widgets": []
                },
                "MultiTag": {
                    "node_kind": "tag_master", "inputs": ["X", "Y"], "outputs": ["String"], "color": "#2D5A7B",
                    "properties": { "tag_type": "pos", "x": "fx.pos_x", "y": "fx.pos_y" },
                    "widgets": []
                },
                "MultiRandom": {
                    "node_kind": "data", "inputs": ["Min", "Max", "Step", "Total (N)", "Iterator"], "outputs": ["Data", "Batch / List"], "color": "#1A5F4C",
                    "properties": { "mode": "R", "min": "0", "max": "100", "step": "", "options": "", "counter": "", "total": "1", "iterator": "" },
                    "widgets": []
                },
                "Math": {
                    "node_kind": "math", "inputs": ["A", "B"], "outputs": ["Out"], "color": "#0D9488",
                    "properties": { "category": "basic", "operation": "add" },
                    "widgets": []
                },
                "Once": {
                    "node_kind": "data", "inputs": ["In"], "outputs": ["Out"], "color": "#6366F1",
                    "properties": { "mode": "line", "iterator": "j" },
                    "widgets": []
                },
                "Only": {
                    "node_kind": "data", "inputs": ["True", "False"], "outputs": ["Out"], "color": "#10B981",
                    "properties": { "condition": "True", "mode": "select" },
                    "widgets": []
                }
            },
            "Loops": {
                "Main Loop": {
                    "node_kind": "main_loop", "inputs": [], "outputs": ["Loop", "Iterator (i)", "Total (N)"], "color": "#1E5F3A",
                    "properties": { "iterator": "syl", "blank_mode": "no_blank" },
                    "widgets": [
                        { "type": "combo", "name": "Iterator:", "property": "iterator", "values": ["syl", "char", "word", "line"] },
                        { "type": "combo", "name": "Blank Mode:", "property": "blank_mode", "values": ["no_blank", "with_blanks"] }
                    ]
                },
                "MaxLoop": {
                    "node_kind": "max_loop", "inputs": ["Loop In", "Start", "End"], "outputs": ["Loop Out", "Counter", "Total"], "color": "#8A2BE2",
                    "properties": { "mode": "normal", "iterations": "3", "step_ms": "41.7", "start_time": "start_time", "end_time": "end_time", "var_name": "j" },
                    "widgets": [
                        { "type": "combo", "name": "Mode:", "property": "mode", "values": ["normal", "fbf"] },
                        { "type": "text", "name": "Iterations (N)", "property": "iterations" },
                        { "type": "text", "name": "Step (ms)", "property": "step_ms" },
                        { "type": "text", "name": "Start", "property": "start_time" },
                        { "type": "text", "name": "End", "property": "end_time" },
                        { "type": "text", "name": "Var Name (j)", "property": "var_name" }
                    ]
                },
                "Module": {
                    "node_kind": "data", "inputs": ["Iterator (i)", "Total (N)", "Sub-step (m)"], "outputs": ["Data"], "color": "#1E5F3A",
                    "properties": { "iter": "i", "total": "N", "sub_m": "0" },
                    "widgets": [
                        { "type": "text", "name": "Iterator (i)", "property": "iter" },
                        { "type": "text", "name": "Total (N)", "property": "total" },
                        { "type": "text", "name": "Sub-step (m)", "property": "sub_m" }
                    ]
                }
            },
            "Variables": {
                "Sys Var": {
                    "node_kind": "variable_master", "inputs": [], "outputs": ["Data"], "color": "#5F1E5E",
                    "properties": { "var_name": "syl.text" },
                    "widgets": [{ "type": "text", "name": "Variable", "property": "var_name" }]
                },
                "Define Vars": {
                    "node_kind": "set_vars", "inputs": ["In"], "outputs": ["Out"], "color": "#5F1E5E",
                    "properties": { "variables": "" },
                    "widgets": [{ "type": "text", "name": "Vars", "property": "variables" }]
                },
                "Get Var": {
                    "node_kind": "data", "inputs": [], "outputs": ["Data"], "color": "#5F1E5E",
                    "properties": { "var_name": "j" },
                    "widgets": [{ "type": "text", "name": "Name", "property": "var_name" }]
                },
                "Memory": {
                    "node_kind": "data", "inputs": ["Key", "Value"], "outputs": ["Data"], "color": "#5F1E5E",
                    "properties": { "mode": "remember", "key": "ref", "value": "", "default": "" },
                    "widgets": [
                        { "type": "combo", "name": "Mode:", "property": "mode", "values": ["remember", "retrieve"] },
                        { "type": "text", "name": "Key:", "property": "key" },
                        { "type": "text", "name": "Value / Default:", "property": "value" }
                    ]
                }
            },
            "System": {
                "Output": {
                    "node_kind": "output",
                    "inputs": ["Loop In", "Tags", "Layer", "Start Time", "End Time", "Origin Align", "Queue ID", "Queue Order"],
                    "outputs": ["Preview"],
                    "color": "#8B0000",
                    "properties": { "apply_to": "all", "queue_id": "", "queue_order": "", "origin_align": 5 },
                    "widgets": [
                        { "type": "combo", "name": "Apply to:", "property": "apply_to", "values": ["all", "selected", "style"] }
                    ]
                },
                "Previewer": {
                    "node_kind": "preview",
                    "inputs": ["Output"],
                    "outputs": [],
                    "color": "#2563EB",
                    "properties": { "output_ids": "" },
                    "widgets": [
                        { "type": "text", "name": "Output IDs", "property": "output_ids" }
                    ]
                },
                "Benchmark Math": {
                    "node_kind": "data", "inputs": ["Iterations"], "outputs": ["Out", "Time ms"], "color": "#D97706",
                    "properties": { "iterations": "10000", "complexity": "Heavy Math (Trig + Sqrt)" },
                    "widgets": [
                        { "type": "combo", "name": "Complexity:", "property": "complexity", "values": ["Heavy Math (Trig + Sqrt)", "Prime Sieve", "Matrix Mult"] }
                    ]
                },
                "Script Code": {
                    "node_kind": "step", "inputs": ["Loop In", "In1", "In2"], "outputs": ["Loop Out", "Result"], "color": "#3B82F6",
                    "properties": { "language": "Python", "script": "result = 'Hello Pyxis ' + str(in1 if in1 else syl.text)", "inputs_count": 2 },
                    "widgets": [
                        { "type": "combo", "name": "Language", "property": "language", "values": ["Python", "Lua"] }
                    ]
                }
            },
            "Functions": {
                "Conditioner": {
                    "node_kind": "data", "inputs": ["Condition", "If True", "If False"], "outputs": ["Out"], "color": "#8B5CF6",
                    "properties": { "condition": "True", "if_true": "", "if_false": "" },
                    "widgets": [
                        { "type": "text", "name": "Condition", "property": "condition" },
                        { "type": "text", "name": "If True", "property": "if_true" },
                        { "type": "text", "name": "If False", "property": "if_false" }
                    ]
                },
                "Color Gradient": {
                    "node_kind": "data", "inputs": ["Progress (0-1)", "Color List", "Total (N)", "Accel"], "outputs": ["ASS Color", "Color List", "Tags"], "color": "#8B5CF6",
                    "properties": { "prog": "char.i / char.n", "colors_str": "#95E648,#3E750C,#ED38CA", "total": "1", "accel": "1.0", "tag_type": "\\1c" },
                    "widgets": []
                },
                "Bezier Curve": {
                    "node_kind": "data", "inputs": ["Origin", "P0", "P1", "P2", "P3", "t", "Subdivs", "Shape", "Points", "Trajectory Mode", "Dist Range", "Seed", "Loops"], "outputs": ["\\pos", "X", "Y", "Tan", "Norm", "Spline", "Spline L", "Spline R"], "color": "#8B5CF6",
                    "properties": { "p0": "0,0", "p1": "50,100", "p2": "150,100", "p3": "200,0", "t": "0.5", "subdivs": "100", "mode": "cubic_2d", "shape": "", "points": "", "origin": "", "traj_mode": "free_wander", "dist_range": "50,120", "seed": "1", "loops": "8" },
                    "widgets": []
                },
                "Interpolator": {
                    "node_kind": "data", "inputs": ["Iterator", "Total", "Accel", "V1", "V2"], "outputs": ["Data", "Batch / List"], "color": "#8B5CF6",
                    "properties": { "iterator": "i", "total": "N", "accel": "1.0", "v1": "0", "v2": "1" },
                    "widgets": []
                },
                "Particles": {
                    "node_kind": "data", "inputs": ["Path / Origin", "Particle", "Density", "RedrawDist", "Seed", "Scale", "Anchor", "Order"], "outputs": ["Shp Out", "\\pos Tag", "X Arr", "Y Arr", "Total"], "color": "#8B5CF6",
                    "properties": { "shape": "", "particle_shape": "", "density": "5.0", "redraw_dist": "0", "seed": "1", "scale": "1.0", "mode": "outline_v2", "anchor": "pieces", "order": "79" },
                    "widgets": []
                },
                "IMG to pixels": {
                    "node_kind": "data", "inputs": ["Image Path", "Particle", "Frame", "Step", "Alpha", "Scale", "Anchor", "Numpad Order"], "outputs": ["Shp Out", "Color Arr", "\\pos Tag", "X Arr", "Y Arr", "Total"], "color": "#8B5CF6",
                    "properties": { "image_path": "", "particle_shape": "", "frame": "1", "step": "2", "alpha_threshold": "128", "scale": "1.0", "anchor": "center", "order": "79" },
                    "widgets": []
                },
                "Animation": {
                    "node_kind": "data", "inputs": ["Shape list", "Step ms", "Start Time", "End Time"], "outputs": ["Shape", "Frame", "Frames List"], "color": "#8B5CF6",
                    "properties": { "mode": "fbf", "frames": "", "step_ms": "41.7", "start_time": "", "end_time": "", "alpha_tag": "\\alpha", "order": "sequential", "var_name": "an" },
                    "widgets": []
                },
                "Glitter": {
                    "node_kind": "data", "inputs": ["Start Time", "End Time", "Density", "In 1"], "outputs": ["List", "TAG 1"], "color": "#8B5CF6",
                    "properties": { "expandable": true, "start_time": "0", "end_time": "fx.dur", "density": "1.0", "mode": "flashes", "seed": "0", "tags": ["\\fscx"], "mins": ["150"], "maxs": ["250"] },
                    "widgets": []
                },
                "Move Tag": {
                    "node_kind": "data", "inputs": ["Tags", "Shape (d)", "Relative Mode", "Start Time (t1)", "End Time (t2)", "Acceleration"], "outputs": ["String"], "color": "#8B5CF6",
                    "properties": { "mode": "trajectory", "tags": "", "shape": "m 0 0 l 100 0", "points": "0,0; 100,50; 200,0", "text": "", "t1": "0", "t2": "300", "accel": "1.0", "relative": "1" },
                    "widgets": []
                },
                "Move Text": {
                    "node_kind": "data", "inputs": ["Text", "Tags", "Delta X", "Delta Y", "Offset X", "Offset Y", "Trajectory", "Anchor", "Step (px)", "Start Time (t1)", "End Time (t2)", "Acceleration"], "outputs": ["Text"], "color": "#8B5CF6",
                    "properties": { "text": "", "tags": "", "dx": "", "dy": "", "ox": "", "oy": "", "trajectory": "", "anchor": "center", "step_px": "7.5", "t1": "0", "t2": "fx.dur", "accel": "1.0" },
                    "widgets": []
                }
            },
            "Shape": {
                "Manipulator": {
                    "node_kind": "data", "inputs": ["Shape / Text", "Factor (t)", "Scale X", "Scale Y", "Anchor"], "outputs": ["Shape"], "color": "#5B2C6F",
                    "properties": { "shape": "", "t": "1.0", "scale_x": "100", "scale_y": "100", "angle": "0", "offset_x": "0", "offset_y": "0", "offset_border": "2.0", "factor": "100", "density": "2.0", "angle_x": "0", "angle_y": "0", "angle_z": "0", "axis": "none", "skew_x": "0", "skew_y": "0", "anchor": "center", "mode": "scale" },
                    "widgets": []
                },
                "Filter": {
                    "node_kind": "data", "inputs": ["Shape / Text", "Expr X", "Expr Y", "Factor (t)", "Subdivs"], "outputs": ["Shape"], "color": "#5B2C6F",
                    "properties": { "shape": "", "mode": "vertices", "expr_x": "x", "expr_y": "y", "t": "1.0", "subdivs": "0", "rot_step": "0", "scale_step": "100", "offset_x": "0", "offset_y": "0", "anchor": "center", "radius_x": "5.0", "radius_y": "5.0", "seed": "0" },
                    "widgets": []
                },
                "Transform": {
                    "node_kind": "data", "inputs": ["Shape / Text", "Factor (t)", "Ratio", "Anchor"], "outputs": ["Shape"], "color": "#7D3C98",
                    "properties": { "shape": "", "mode": "inflate", "t": "1.0", "ratio": "1.0", "inflate_mode": "circle", "angle_x": "0", "angle_y": "0", "radius": "10.0", "corner_mode": "round", "curve": "30", "bend_t": "1.0", "axis": "x", "target_shape": "", "mid_shape": "", "energy": "0.35", "step_px": "0", "anchor": "center" },
                    "widgets": []
                },
                "Multi": {
                    "node_kind": "data", "inputs": ["Size", "Thickness (Px)", "Factor (t)"], "outputs": ["Shape"], "color": "#5B2C6F",
                    "properties": { "mode": "concentric_squares", "size": "100.0", "px": "4", "width": "70.0", "height": "50.0", "bord": "4", "space": "0.0", "length": "20.0", "sides": "6", "rings": "1", "n_layers": "25", "dx": "0.0", "dy": "0.0", "parts": "12", "r_out": "50.0", "r_in": "0.0", "size1": "100.0", "size2": "10.0", "loop": "8", "angle": "0.0", "t": "1.0", "shape": "", "order": "79" },
                    "widgets": []
                },
                "Clipper": {
                    "node_kind": "data", "inputs": ["Shape A", "Shape B", "Mode", "Delta (px)", "Subj Fill", "Clip Fill", "Join Mode", "End Mode", "Miter Limit", "Post-Offset", "Clean Dist", "Anchor"], "outputs": ["Shape Out", "Out List", "BBox Data"], "color": "#5B2C6F",
                    "properties": { "mode": "difference", "shape_a": "", "shape_b": "", "delta": "0.0", "post_offset": "", "subj_fill": "evenodd", "clip_fill": "evenodd", "join_type": "round", "end_type": "closed_polygon", "miter_limit": "2.0", "arc_tolerance": "0.25", "clean_dist": "0.0", "strictly_simple": "0", "reverse_subj": "0", "reverse_clip": "0", "anchor": "center", "out_mode": "shape", "scale": "10000.0" },
                    "widgets": []
                },
                "Union & Divide": {
                    "node_kind": "data", "inputs": ["Shape In", "Fill Rule", "Auto-Intersect", "Anchor", "Order"], "outputs": ["Shape Out", "Out List", "BBox Data"], "color": "#5B2C6F",
                    "properties": { "shape": "", "shape_b": "", "fill_type": "evenodd", "clean_self_intersect": "1", "mode": "divide", "anchor": "pieces", "order": "79", "tagmode": "ipol", "tags": "" },
                    "widgets": []
                }
            },
            "Time": {
                "Lead In": {
                    "node_kind": "data", "inputs": ["Delay (ms)"], "outputs": ["Data"], "color": "#2563EB",
                    "properties": { "delay_ms": "40" },
                    "widgets": [{ "type": "text", "name": "Delay (ms)", "property": "delay_ms" }]
                },
                "Lead Out": {
                    "node_kind": "data", "inputs": ["Delay (ms)"], "outputs": ["Data"], "color": "#2563EB",
                    "properties": { "delay_ms": "40" },
                    "widgets": [{ "type": "text", "name": "Delay (ms)", "property": "delay_ms" }]
                },
                "Middle 1": {
                    "node_kind": "data", "inputs": ["Delay (ms)"], "outputs": ["Data"], "color": "#2563EB",
                    "properties": { "delay_ms": "30" },
                    "widgets": [{ "type": "text", "name": "Delay (ms)", "property": "delay_ms" }]
                },
                "Middle 2": {
                    "node_kind": "data", "inputs": ["Delay (ms)"], "outputs": ["Data"], "color": "#2563EB",
                    "properties": { "delay_ms": "30" },
                    "widgets": [{ "type": "text", "name": "Delay (ms)", "property": "delay_ms" }]
                },
                "Loop 1": {
                    "node_kind": "data", "inputs": ["Delay (ms)"], "outputs": ["Data"], "color": "#2563EB",
                    "properties": { "delay_ms": "30", "mode": "leadin" },
                    "widgets": [{ "type": "text", "name": "Delay (ms)", "property": "delay_ms" }]
                },
                "Loop 2": {
                    "node_kind": "data", "inputs": ["Delay (ms)"], "outputs": ["Data"], "color": "#2563EB",
                    "properties": { "delay_ms": "30", "mode": "leadin" },
                    "widgets": [{ "type": "text", "name": "Delay (ms)", "property": "delay_ms" }]
                },
                "Ipol": {
                    "node_kind": "data", "inputs": ["Duration (ms)", "Points / Values", "Acceleration"], "outputs": ["Data"], "color": "#2563EB",
                    "properties": { "dur": "syl.duration", "points": "0, 100", "accel": "1.0" },
                    "widgets": []
                },
                "Synced": {
                    "node_kind": "data", "inputs": ["Constant", "Fade (ms)", "Max Extra", "Delay Line", "Threshold"], "outputs": ["Extra ms", "Sync End"], "color": "#2563EB",
                    "properties": { "mode": "order", "progression_const": "0", "fade_dur": "300", "max_added_time": "2000", "delay_ms": "250", "max_gap_threshold": "3000" },
                    "widgets": [
                        { "type": "combo", "name": "Mode:", "property": "mode", "values": ["order", "style", "actor", "layer", "effect"] },
                        { "type": "text", "name": "Constant", "property": "progression_const" },
                        { "type": "text", "name": "Fade (ms)", "property": "fade_dur" },
                        { "type": "text", "name": "Max Extra", "property": "max_added_time" },
                        { "type": "text", "name": "Delay Line", "property": "delay_ms" },
                        { "type": "text", "name": "Threshold", "property": "max_gap_threshold" }
                    ]
                },
                "Retime": {
                    "node_kind": "data", "inputs": ["Tags or \\t", "Offset In (ms)", "Offset Out (ms)", "Accel"],
                    "outputs": ["\\t Out", "Start Time", "End Time", "Duration"], "color": "#2563EB",
                    "properties": { "phase": "syl", "tags": "", "offset_in": "0", "offset_out": "0", "accel": "1.0" },
                    "widgets": [
                        { "type": "combo", "name": "Mode:", "property": "phase", "values": [
                            "syl", "presyl", "postsyl", "line", "preline", "postline",
                            "start2syl", "syl2end", "abs", "sylpct"
                        ]},
                        { "type": "text", "name": "Tags or \\t:", "property": "tags" },
                        { "type": "text", "name": "Offset In (ms):", "property": "offset_in" },
                        { "type": "text", "name": "Offset Out (ms):", "property": "offset_out" },
                        { "type": "text", "name": "Accel:", "property": "accel" }
                    ]
                }
            }
        };

        function registerDataNodes(data_nodes, overwrite = false) {
            if (!data_nodes) return;
            for (const category in data_nodes) {
                for (const node_name in data_nodes[category]) {
                    const definition = { inputs: data_nodes[category][node_name], outputs: [], properties: {}, widgets: [] };
                    const full_name = (category && category !== "Root") ? (category + "/" + node_name) : node_name;
                    if (!overwrite && LiteGraph.registered_node_types[full_name]) continue;
                    const DynamicNode = createNodeConstructor(category, node_name, definition, false);
                    DynamicNode.title = node_name;
                    LiteGraph.registerNodeType(full_name, DynamicNode);
                }
            }
        }

        function registerSystemNodes(system_nodes, overwrite = false) {
            if (!system_nodes) return;

            for (const k in LiteGraph.registered_node_types) {
                if (k.startsWith("Shape/Formas/") || k.startsWith("Shape/Estrellas/") ||
                    k.startsWith("Shape/Especiales/") || k.startsWith("Shape/Notas/") ||
                    k.startsWith("Shape/Sakura/") || k.startsWith("Shape/Corte/") ||
                    k.startsWith("Shape/Shape ") ||
                    k.startsWith("Text/Operaciones/") || k.startsWith("Text/Especial/") ||
                    k.startsWith("Time/Operaciones/") || k === "Time/Operaciones" ||
                    k.startsWith("Time/Time ") ||
                    k.startsWith("Audio/Audio ") ||
                    k.startsWith("Particles/")) {
                    delete LiteGraph.registered_node_types[k];
                }
            }


            for (const category in system_nodes) {
                for (const node_name in system_nodes[category]) {
                    const full_name = (category && category !== "Root") ? (category + "/" + node_name) : node_name;
                    if (!overwrite && LiteGraph.registered_node_types[full_name]) continue;
                    const definition = system_nodes[category][node_name];
                    const SystemNode = createNodeConstructor(category, node_name, definition, true);
                    SystemNode.title = node_name;
                    LiteGraph.registerNodeType(full_name, SystemNode);
                }
            }
        }

        function loadDefaultGraph() {
            registerSystemNodes(FALLBACK_SYSTEM_NODES, false);

            if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.destroyAllPlayers === "function") {
                window.PyxisNodePlayerManager.destroyAllPlayers();
            }

            graph.clear();

            if (canvas && canvas.canvas && typeof canvas.resize === "function") {
                canvas.resize();
            }

            let cw = 1280;
            let ch = 720;
            if (canvas && canvas.canvas) {
                if (canvas.canvas.width > 0) cw = canvas.canvas.width;
                else if (canvas.canvas.offsetWidth > 0) cw = canvas.canvas.offsetWidth;
                if (canvas.canvas.height > 0) ch = canvas.canvas.height;
                else if (canvas.canvas.offsetHeight > 0) ch = canvas.canvas.offsetHeight;
            } else if (window.innerWidth) {
                cw = window.innerWidth;
                ch = Math.max(400, window.innerHeight - 52);
            }

            const centerX = cw / 2;
            const centerY = ch / 2;
            const totalW = 720;
            const startX = Math.round(centerX - (totalW / 2));
            const startY = Math.round(centerY - 70);

            var node_loop = LiteGraph.createNode("Loops/Main Loop");
            if (node_loop) { node_loop.pos = [startX, startY]; graph.add(node_loop); }

            var node_vars = LiteGraph.createNode("Variables/Define Vars");
            if (node_vars) { node_vars.pos = [startX + 280, startY]; graph.add(node_vars); }

            var node_out = LiteGraph.createNode("System/Output");
            if (node_out) { node_out.pos = [startX + 540, startY]; graph.add(node_out); }

            if (node_loop && node_vars) node_loop.connect(0, node_vars, 0);
            if (node_vars && node_out) node_vars.connect(0, node_out, 0);

            window.__pyxis_active_template_id = null;
            window.__pyxis_active_template_name = null;
            localStorage.removeItem("pyxis_active_template_id");
            localStorage.removeItem("pyxis_active_template_name");
            localStorage.removeItem("pyxis_last_used_template_id");
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.save_user_config === "function") {
                window.pywebview.api.save_user_config({
                    active_template_id: null,
                    active_template_name: null
                });
            }

            if (typeof window.update_template_checkpoint === "function") {
                window.update_template_checkpoint();
            }

            const btnTop = document.getElementById("btn-quick-save-template");
            if (btnTop) btnTop.style.display = "none";

            if (window.PyxisUndoManager) {
                window.PyxisUndoManager.initInitialState();
            }

            if (typeof window.updateTemplateUIState === "function") window.updateTemplateUIState();
            if (typeof window.__pyxis_schedule_save === "function") window.__pyxis_schedule_save(50);

            resetView();
            canvas.draw(true, true);
            canvas.setDirty(true, true);
        }

        window.loadDefaultGraph = loadDefaultGraph;

        function setLoadingStatus(text) {
            const el = document.getElementById("pyxis-loader-status-text");
            if (el) el.textContent = text;
        }

        function hideLoadingOverlay() {
            const overlay = document.getElementById("pyxis-loading-overlay");
            if (overlay) {
                overlay.classList.add("fade-out");
                setTimeout(() => { overlay.style.display = "none"; }, 450);
            }
        }

        async function initDynamicNodes() {
            setLoadingStatus("Connecting to Python engine...");
            let manifest = {}; let sessionData = ""; let userConfig = null;
            
            let attempts = 0;
            while (attempts < 20) {
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_manifest === "function") {
                    try {
                        setLoadingStatus("Loading node catalog...");
                        const rawManifest = await window.pywebview.api.get_manifest();
                        if (rawManifest && rawManifest.trim().length > 0) {
                            manifest = JSON.parse(rawManifest);
                            break;
                        }
                    } catch (e) {
                        console.warn("Pyxis: retrying IPC manifest read...", attempts);
                    }
                }
                attempts++;
                await new Promise(r => setTimeout(r, 50));
            }

            if (window.pywebview && window.pywebview.api) {
                try { sessionData = await window.pywebview.api.get_session_graph(); } catch (error) {}
                try {
                    userConfig = await window.pywebview.api.get_user_config();
                    if (userConfig) window.userConfig = userConfig;
                } catch (error) {}
                if (window.PyxisThemeManager && typeof window.PyxisThemeManager.syncCustomThemesWithBackend === "function") {
                    try { await window.PyxisThemeManager.syncCustomThemesWithBackend(); } catch (error) {}
                }
            }

            window.__pyxis_reload_subtitles = async function() {
                if (window.PyxisTelemetry && typeof window.PyxisTelemetry.clearData === "function") {
                    try { window.PyxisTelemetry.clearData(false); } catch (e) {}
                }
                if (window.pywebview && window.pywebview.api) {
                    if (typeof window.pywebview.api.get_session_graph === "function") {
                        try {
                            const sData = await window.pywebview.api.get_session_graph();
                            if (sData) {
                                const saved_graph = JSON.parse(sData);
                                if (saved_graph && Array.isArray(saved_graph.nodes) && saved_graph.nodes.length > 0 && window.graph) {
                                    window.graph.configure(saved_graph);
                                    const activeTplId = (saved_graph.extra && saved_graph.extra.active_template_id) || localStorage.getItem("pyxis_active_template_id");
                                    const activeTplName = (saved_graph.extra && saved_graph.extra.active_template_name) || localStorage.getItem("pyxis_active_template_name");
                                    if (activeTplId && activeTplName) {
                                        window.__pyxis_active_template_id = activeTplId;
                                        window.__pyxis_active_template_name = activeTplName;
                                    }
                                    if (window.PyxisUndoManager && typeof window.PyxisUndoManager.initInitialState === "function") {
                                        window.PyxisUndoManager.initInitialState();
                                    }
                                    if (typeof window.sync_template_checkpoint === "function") {
                                        await window.sync_template_checkpoint(activeTplId, activeTplName);
                                    } else if (typeof window.update_checkpoint === "function") {
                                        window.update_checkpoint();
                                    } else if (typeof window.update_template_checkpoint === "function") {
                                        window.update_template_checkpoint();
                                    }
                                    if (typeof window.updateTemplateUIState === "function") window.updateTemplateUIState();
                                    if (saved_graph.extra && typeof window.restoreGraphView === "function") {
                                        window.restoreGraphView(saved_graph.extra);
                                    }
                                    if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                }
                            }
                        } catch (e) {
                            console.error("Pyxis Daemon: error al recargar sesión", e);
                        }
                    }

                    try {
                        let updatedInfoAegi = null;
                        let updatedInfoBase = null;
                        const serialized = (window.graph) ? window.graph.serialize() : null;
                        if (typeof window.pywebview.api.get_preview_info === "function") {
                            updatedInfoAegi = await window.pywebview.api.get_preview_info("aegisub", undefined, serialized);
                            updatedInfoBase = await window.pywebview.api.get_preview_info("base", undefined, serialized);
                            if (updatedInfoAegi) {
                                window.PyxisPreviewConfigAegi = updatedInfoAegi;
                            }
                            if (updatedInfoBase) {
                                window.PyxisPreviewConfigBase = updatedInfoBase;
                            }
                            if (updatedInfoAegi && updatedInfoAegi.has_aegisub) {
                                window.PyxisPreviewConfig = updatedInfoAegi;
                            } else if (updatedInfoBase) {
                                window.PyxisPreviewConfig = updatedInfoBase;
                            } else if (updatedInfoAegi) {
                                window.PyxisPreviewConfig = updatedInfoAegi;
                            }
                        }
                        if (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) {
                            const players = window.PyxisNodePlayerManager.activePlayers;
                            for (const nId in players) {
                                const p = players[nId];
                                if (!p) continue;
                                if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.setPlayerLoading === "function") {
                                    window.PyxisNodePlayerManager.setPlayerLoading(nId, true, "preview.syncing");
                                }
                                if (window.graph) {
                                    const liveNode = window.graph.getNodeById(Number(nId)) || window.graph.getNodeById(nId);
                                    if (liveNode) p.node = liveNode;
                                }
                                const curSrc = (p.node && p.node.properties && p.node.properties.preview_source) || "base";
                                const connectedOutputs = (p.node && typeof resolveConnectedOutputsForPreview === "function")
                                    ? resolveConnectedOutputsForPreview(p.node)
                                    : [];
                                const hasAegi = Boolean(window.PyxisPreviewConfigAegi ? window.PyxisPreviewConfigAegi.has_aegisub : (window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub));
                                p.hasAegisub = hasAegi;
                                if (typeof window.PyxisNodePlayerManager.updateSourceButtonUI === "function") {
                                    window.PyxisNodePlayerManager.updateSourceButtonUI(nId, curSrc, hasAegi);
                                }
                                if (curSrc === "base") {
                                    if (typeof window.pywebview.api.get_preview_video_data_url === "function") {
                                        const newVid = await window.pywebview.api.get_preview_video_data_url("base", connectedOutputs, serialized);
                                        const isArtInError = Boolean(p.art && p.art.template && p.art.template.$player && p.art.template.$player.classList.contains('art-error'));
                                        if (newVid && p.art && (p.videoUrl !== newVid || isArtInError)) {
                                            p.videoUrl = newVid;
                                            if (p.art.template && p.art.template.$player) {
                                                p.art.template.$player.classList.remove('art-error');
                                            }
                                            if (p.art.mask) p.art.mask.show = false;
                                            if (p.art.loading) p.art.loading.show = false;
                                            if (p.art.notice) p.art.notice.show = "";
                                            try {
                                                await p.art.switchUrl(newVid);
                                            } catch(err) {
                                                console.warn("[Pyxis Daemon switchUrl error, retrying directly]", err);
                                                try { p.art.url = newVid; } catch(e) {}
                                            }
                                            if (p.art.template && p.art.template.$player) {
                                                p.art.template.$player.classList.remove('art-error');
                                            }
                                            if (p.art.mask) p.art.mask.show = false;
                                        }
                                    }
                                    if (typeof window.pywebview.api.get_initial_base_ass === "function" && p.jassub) {
                                        const baseAss = await window.pywebview.api.get_initial_base_ass("base", connectedOutputs, serialized);
                                        if (baseAss && typeof updateJassubTrack === "function") {
                                            await updateJassubTrack(p.jassub, baseAss);
                                        }
                                    }
                                    if (typeof window.pywebview.api.get_preview_fonts_map === "function" && p.jassub) {
                                        try {
                                            const reloadFonts = await window.pywebview.api.get_preview_fonts_map("base");
                                            if (reloadFonts && typeof reloadFonts === "object") {
                                                injectFontsIntoJassub(p.jassub, reloadFonts);
                                            }
                                        } catch(e) {}
                                    }
                                    const activeInfo = updatedInfoBase || window.PyxisPreviewConfigBase;
                                    if (p.node && activeInfo && activeInfo.aspect_ratio) {
                                        p.node.preview_aspect_ratio = activeInfo.aspect_ratio;
                                        if (p.node.properties) p.node.properties.preview_aspect_ratio = activeInfo.aspect_ratio;
                                        const nodeAspect = getNodePreviewAspectRatio(p.node);
                                        const isCustomZoom = Boolean(
                                            (p && p.transformState && p.transformState.isCustom) ||
                                            (p.node && p.node.properties && p.node.properties.viewport_custom)
                                        );
                                        if (!p.isPinned) {
                                            const dynMinW = getDynamicMinPreviewWidth(nodeAspect);
                                            const curW = (p.node.size && p.node.size[0] && p.node.size[0] >= dynMinW) ? p.node.size[0] : Math.max(dynMinW, 520);
                                            const curH = (isCustomZoom && p.node.size && p.node.size[1]) 
                                                ? p.node.size[1] 
                                                : (typeof calculatePrevisualizadorNodeHeight === "function" ? calculatePrevisualizadorNodeHeight(curW, nodeAspect) : 330);
                                            if (!p.node.size || p.node.size[0] !== curW || (!isCustomZoom && Math.abs(p.node.size[1] - curH) > 1.5)) {
                                                p.node.size = [curW, curH];
                                                if (p.node.properties) {
                                                    p.node.properties.previewer_width = curW;
                                                    p.node.properties.previewer_height = curH;
                                                }
                                                if (typeof p.node.setDirtyCanvas === 'function') p.node.setDirtyCanvas(true, true);
                                                if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                            }
                                        } else {
                                            p.node.size = [300, 54];
                                            if (typeof p.node.setDirtyCanvas === 'function') p.node.setDirtyCanvas(true, true);
                                            if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                        }
                                    }
                                } else if (curSrc === "aegisub" && hasAegi) {
                                    if (typeof window.pywebview.api.get_preview_video_data_url === "function") {
                                        const newVid = await window.pywebview.api.get_preview_video_data_url("aegisub", connectedOutputs, serialized);
                                        const isArtInError = Boolean(p.art && p.art.template && p.art.template.$player && p.art.template.$player.classList.contains('art-error'));
                                        if (newVid && p.art && (p.videoUrl !== newVid || isArtInError)) {
                                            p.videoUrl = newVid;
                                            if (p.art.template && p.art.template.$player) {
                                                p.art.template.$player.classList.remove('art-error');
                                            }
                                            if (p.art.mask) p.art.mask.show = false;
                                            if (p.art.loading) p.art.loading.show = false;
                                            if (p.art.notice) p.art.notice.show = "";
                                            try {
                                                await p.art.switchUrl(newVid);
                                            } catch(err) {
                                                console.warn("[Pyxis Daemon switchUrl error, retrying directly]", err);
                                                try { p.art.url = newVid; } catch(e) {}
                                            }
                                            if (p.art.template && p.art.template.$player) {
                                                p.art.template.$player.classList.remove('art-error');
                                            }
                                            if (p.art.mask) p.art.mask.show = false;
                                        }
                                    }
                                    p.hasRefreshed = false;
                                    if (typeof window.pywebview.api.get_initial_base_ass === "function" && p.jassub) {
                                        const baseAss = await window.pywebview.api.get_initial_base_ass("aegisub", connectedOutputs, serialized);
                                        if (baseAss && typeof updateJassubTrack === "function") {
                                            await updateJassubTrack(p.jassub, baseAss);
                                        }
                                    }
                                    if (typeof window.pywebview.api.get_preview_fonts_map === "function" && p.jassub) {
                                        try {
                                            const reloadFonts = await window.pywebview.api.get_preview_fonts_map("aegisub");
                                            if (reloadFonts && typeof reloadFonts === "object") {
                                                injectFontsIntoJassub(p.jassub, reloadFonts);
                                            }
                                        } catch(e) {}
                                    }
                                    const activeInfo = updatedInfoAegi || window.PyxisPreviewConfigAegi;
                                    if (p.node && activeInfo && activeInfo.aspect_ratio) {
                                        p.node.preview_aspect_ratio = activeInfo.aspect_ratio;
                                        if (p.node.properties) p.node.properties.preview_aspect_ratio = activeInfo.aspect_ratio;
                                        const nodeAspect = getNodePreviewAspectRatio(p.node);
                                        const isCustomZoom = Boolean(
                                            (p && p.transformState && p.transformState.isCustom) ||
                                            (p.node && p.node.properties && p.node.properties.viewport_custom)
                                        );
                                        if (!p.isPinned) {
                                            const dynMinW = getDynamicMinPreviewWidth(nodeAspect);
                                            const curW = (p.node.size && p.node.size[0] && p.node.size[0] >= dynMinW) ? p.node.size[0] : Math.max(dynMinW, 520);
                                            const curH = (isCustomZoom && p.node.size && p.node.size[1]) 
                                                ? p.node.size[1] 
                                                : (typeof calculatePrevisualizadorNodeHeight === "function" ? calculatePrevisualizadorNodeHeight(curW, nodeAspect) : 330);
                                            if (!p.node.size || p.node.size[0] !== curW || (!isCustomZoom && Math.abs(p.node.size[1] - curH) > 1.5)) {
                                                p.node.size = [curW, curH];
                                                if (p.node.properties) {
                                                    p.node.properties.previewer_width = curW;
                                                    p.node.properties.previewer_height = curH;
                                                }
                                                if (typeof p.node.setDirtyCanvas === 'function') p.node.setDirtyCanvas(true, true);
                                                if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                            }
                                        } else {
                                            p.node.size = [300, 54];
                                            if (typeof p.node.setDirtyCanvas === 'function') p.node.setDirtyCanvas(true, true);
                                            if (window.canvas) { window.canvas.setDirty(true, true); window.canvas.draw(true, true); }
                                        }
                                    }
                                }
                                if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.setPlayerLoading === "function") {
                                    window.PyxisNodePlayerManager.setPlayerLoading(nId, false);
                                }
                            }
                        }
                    } catch (e) {
                        console.error("Pyxis Daemon: error al refrescar estado de preview en reopen", e);
                    }
                }
            };

            registerSystemNodes(FALLBACK_SYSTEM_NODES, false);

            if (userConfig) {
                window.pyxisDaemonMode = userConfig.daemon_mode !== undefined ? !!userConfig.daemon_mode : true;
                if (userConfig.language && window.PyxisI18n) {
                    window.PyxisI18n.setLanguage(userConfig.language, false);
                }
                if (userConfig.theme && window.PyxisThemeManager && typeof window.PyxisThemeManager.applyTheme === "function") {
                    window.PyxisThemeManager.applyTheme(userConfig.theme);
                }
                if (userConfig.grid_mode !== undefined) {
                    window.gridMode = parseInt(userConfig.grid_mode);
                }
                if (userConfig.undo_steps !== undefined && window.PyxisUndoManager) {
                    window.PyxisUndoManager.setMaxSteps(userConfig.undo_steps);
                }
                if (window.PyxisTelemetry && typeof window.PyxisTelemetry.applyPersistedConfig === "function") {
                    window.PyxisTelemetry.applyPersistedConfig(userConfig);
                }
                window.convertVideoSetting = userConfig.convert_video !== undefined ? !!userConfig.convert_video : true;
                window.backgroundImageSettings = {
                    dataUrl: "",
                    videoUrl: "",
                    posterUrl: "",
                    hasBg: !!userConfig.has_bg_image,
                    mediaType: userConfig.bg_media_type || (userConfig.has_bg_image ? "image" : "none"),
                    mode: userConfig.bg_image_mode || "cover",
                    opacity: userConfig.bg_image_opacity !== undefined ? parseFloat(userConfig.bg_image_opacity) : 0.85,
                    isDefault: !!userConfig.is_default_bg
                };
                if (userConfig.has_bg_image && window.pywebview && window.pywebview.api) {
                    const getMediaFn = typeof window.pywebview.api.get_bg_media_data === "function"
                        ? window.pywebview.api.get_bg_media_data
                        : window.pywebview.api.get_bg_image_data;
                    
                    getMediaFn().then(res => {
                        if (res) {
                            if (typeof res === "object") {
                                window.backgroundImageSettings.hasBg = !!res.has_bg;
                                window.backgroundImageSettings.mediaType = res.media_type || "image";
                                window.backgroundImageSettings.videoUrl = res.video_url || "";
                                window.backgroundImageSettings.posterUrl = res.poster_url || "";
                                window.backgroundImageSettings.dataUrl = res.data_url || "";
                                window.backgroundImageSettings.isDefault = !!res.is_default;
                            } else if (typeof res === "string" && res.length > 0) {
                                window.backgroundImageSettings.hasBg = true;
                                window.backgroundImageSettings.mediaType = res.startsWith("http") ? "video" : "image";
                                if (res.startsWith("http")) window.backgroundImageSettings.videoUrl = res;
                                else window.backgroundImageSettings.dataUrl = res;
                            }

                            if (window.updateBgMediaElement) window.updateBgMediaElement();
                            if (canvas) { canvas.setDirty(true, true); canvas.draw(true, true); }
                            
                            const bgInput = document.getElementById("setting-bg-path");
                            if (bgInput) {
                                bgInput.value = window.backgroundImageSettings.mediaType === "video" 
                                    ? (window.t ? window.t("settings.bg_video") : "Video en bucle activo (Acelerado por GPU)") 
                                    : (window.backgroundImageSettings.isDefault ? (window.t ? window.t("settings.bg_default") : "Fondo por defecto (default_back.webp)") : (window.t ? window.t("settings.bg_image") : "Imagen cargada"));
                            }
                            const clearBtn = document.getElementById("btn-clear-bg");
                            if (clearBtn) clearBtn.style.display = "inline-block";
                            const bgOptions = document.getElementById("bg-options-panel");
                            if (bgOptions) bgOptions.style.display = "block";
                        }
                    }).catch(e => console.error("Error cargando fondo multimedia asíncrono", e));
                } else {
                    if (window.updateBgMediaElement) window.updateBgMediaElement();
                    if (canvas) { canvas.setDirty(true, true); canvas.draw(true, true); }
                }
            } else {
                window.gridMode = 1;
                window.backgroundImageSettings = { dataUrl: "", videoUrl: "", posterUrl: "", hasBg: false, mediaType: "none", mode: "cover", opacity: 0.85, isDefault: false };
                if (window.updateBgMediaElement) window.updateBgMediaElement();
                if (canvas) { canvas.setDirty(true, true); canvas.draw(true, true); }
            }

            setLoadingStatus("Building node interface...");
            try {
                const has_new_format = manifest.data_nodes || manifest.system_nodes;
                const data_nodes = has_new_format ? (manifest.data_nodes || {}) : manifest;
                const system_nodes = has_new_format ? (manifest.system_nodes || {}) : {};

                registerDataNodes(data_nodes, true);
                registerSystemNodes(system_nodes, true);
                graph.start();

                let loadedSuccessfully = false;
                let sessionGraphExtra = null;
                if (sessionData) {
                    try {
                        const saved_graph = JSON.parse(sessionData);
                        if (saved_graph && Array.isArray(saved_graph.nodes) && saved_graph.nodes.length > 0) {
                            graph.clear();
                            graph.configure(saved_graph);
                            sessionGraphExtra = saved_graph.extra || null;
                            const valid_nodes = graph._nodes ? graph._nodes.filter(n => n && !n.has_errors && n.type) : [];
                            if (valid_nodes.length > 0) {
                                loadedSuccessfully = true;
                                const activeTplId = (saved_graph.extra && saved_graph.extra.active_template_id) ? saved_graph.extra.active_template_id : (localStorage.getItem("pyxis_active_template_id") || null);
                                const activeTplName = (saved_graph.extra && saved_graph.extra.active_template_name) ? saved_graph.extra.active_template_name : (localStorage.getItem("pyxis_active_template_name") || null);
                                window.__pyxis_active_template_id = activeTplId;
                                window.__pyxis_active_template_name = activeTplName;
                                if (!activeTplId) {
                                    localStorage.removeItem("pyxis_active_template_id");
                                    localStorage.removeItem("pyxis_active_template_name");
                                }
                            }
                        }
                    } catch (error) {
                        console.error("Pyxis: sesión inválida, recurriendo a preset por defecto", error);
                    }
                }
                if (!loadedSuccessfully) {
                    console.warn("Pyxis: no se detectaron nodos válidos en la sesión, cargando preset predeterminado.");
                    loadDefaultGraph();
                }

                if (typeof syncWidgetsToProperties === "function") {
                    syncWidgetsToProperties();
                }
                let viewRestored = false;
                const extraToRestore = sessionGraphExtra || (graph && graph.extra) || (window.graph && window.graph.extra);
                if (loadedSuccessfully && typeof window.restoreGraphView === "function" && extraToRestore) {
                    viewRestored = window.restoreGraphView(extraToRestore);
                }
                if (!viewRestored) {
                    resetView();
                    requestAnimationFrame(() => resetView());
                    setTimeout(resetView, 100);
                    setTimeout(resetView, 350);
                } else {
                    requestAnimationFrame(() => {
                        if (window.restoreGraphView && extraToRestore) {
                            window.restoreGraphView(extraToRestore);
                        }
                    });
                    setTimeout(() => {
                        if (window.restoreGraphView && extraToRestore) {
                            window.restoreGraphView(extraToRestore);
                        }
                    }, 100);
                }
                window.__pyxis_graph_initialized = true;
                if (window.PyxisUndoManager) {
                    window.PyxisUndoManager.initInitialState();
                }
                if (window.__pyxis_active_template_id && typeof window.sync_template_checkpoint === "function") {
                    window.sync_template_checkpoint(window.__pyxis_active_template_id, window.__pyxis_active_template_name);
                } else if (typeof window.updateTemplateUIState === "function") {
                    window.updateTemplateUIState();
                }
            } catch (err) {
                console.error("Pyxis: Error durante inicialización del grafo:", err);
                try { loadDefaultGraph(); } catch (e) {}
            } finally {
                setLoadingStatus("Listo");
                hideLoadingOverlay();
            }
        }

        (function () {
            "use strict";

            var initialization_started = false;

            function start_pyxis_graph() {
                if (initialization_started) return;

                if (!window.pywebview || !window.pywebview.api) {
                    setTimeout(start_pyxis_graph, 50);
                    return;
                }

                initialization_started = true;
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_version_info === "function") {
                    window.pywebview.api.get_version_info().then(function (info) {
                        if (info && info.version) {
                            window.PYXIS_VERSION = info.version;
                            if (info.stage) window.PYXIS_STAGE = info.stage;
                            if (info.full_version) window.PYXIS_FULL_VERSION = info.full_version;
                            if (info.version_string) window.PYXIS_VERSION_STRING = info.version_string;
                            if (window.i18n && typeof window.i18n.applyToDOM === "function") {
                                window.i18n.applyToDOM();
                            }
                        }
                    }).catch(function () {});
                }
                initDynamicNodes();
            }

            window.addEventListener("pywebviewready", start_pyxis_graph);
            start_pyxis_graph();
        }());

