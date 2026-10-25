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
 * @file shape_nodes.js
 * @description UI setups and vector canvas representations for Shape category nodes.
 * @module PyxisShapeNodes
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function setupTextToShapeNode(node) {
            if (!node.properties) node.properties = {};
            if (node.properties.text === undefined) node.properties.text = "";
            if (node.properties.font_name === undefined) node.properties.font_name = "";
            if (node.properties.font_size === undefined) node.properties.font_size = "";
            if (node.properties.scale === undefined) node.properties.scale = "";

            node.widgets_up = true;

            const reqInputs = [
                { name: "Text", type: "data", prop: "text", default: "", aliases: ["text"] },
                { name: "Font", type: "data", prop: "font_name", default: "", aliases: ["font_name"] },
                { name: "Size", type: "data", prop: "font_size", default: "", aliases: ["font_size"] },
                { name: "Scale", type: "data", prop: "scale", default: "", aliases: ["scale"] }
            ];

            const reqOutputs = [
                { name: "Shape Out", type: "data" },
                { name: "Width", type: "data" },
                { name: "Height", type: "data" }
            ];

            function updateTextToShapeInputs() {
                if (!node.inputs) node.inputs = [];
                reqInputs.forEach((req, idx) => {
                    if (idx >= node.inputs.length) {
                        node.addInput(req.name, req.type);
                    }
                    const inp = node.inputs[idx];
                    inp.name = req.name;
                    inp.type = req.type;
                    inp.label = " ";
                });

                if (!node.outputs) node.outputs = [];
                reqOutputs.forEach((req, idx) => {
                    if (idx >= node.outputs.length) {
                        node.addOutput(req.name, req.type);
                    }
                    const out = node.outputs[idx];
                    out.name = req.name;
                    out.type = req.type;
                    out.label = req.name;
                });

                node.widgets = [];

                reqInputs.forEach((req, idx) => {
                    let curVal = node.properties[req.prop];
                    if (curVal === undefined) {
                        for (let a of req.aliases) {
                            if (node.properties[a] !== undefined) {
                                curVal = node.properties[a];
                                break;
                            }
                        }
                    }
                    if (curVal === undefined) curVal = req.default;
                    curVal = String(curVal);
                    node.properties[req.prop] = curVal;

                    const widgetY = 30 + idx * 23;
                    const w = node.addWidget("text", req.name, curVal, function(val) {
                        const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                        node.properties[req.prop] = cleanVal;
                        req.aliases.forEach(a => { node.properties[a] = cleanVal; });
                        if (node.computeSize) node.size = node.computeSize();
                        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    });
                    w.property = req.prop;
                    w.last_y = widgetY - 19;
                    w.y = widgetY - 19;
                    setupSingleLineTextWidget(node, w, req.name, req.prop);

                    if (node.inputs[idx]) {
                        node.inputs[idx].label = " ";
                        node.inputs[idx].pos = [10, widgetY - 10];
                    }
                });

                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            node.computeSize = function() {
                let base_w = 230;
                let text_req_w = 0;
                if (node.properties) {
                    ["text", "font_name", "font_size", "scale"].forEach(k => {
                        const val = String(node.properties[k] || "");
                        if (val.length > 0) {
                            const tw = getExactTextWidth(val, "bold 11px monospace");
                            if (tw > text_req_w) text_req_w = tw;
                        }
                    });
                }
                const boxW = Math.max(70, Math.ceil(text_req_w + 36));
                const reqW = Math.max(base_w, 22 + boxW + 105);
                const reqH = 11 + 4 * 23 + 22;
                return [reqW, reqH];
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateTextToShapeInputs();
            };

            updateTextToShapeInputs();
        }


        function setupShapesLibNode(node) {
            if (!node.properties) node.properties = {};
            const initialShape = node.properties.shape || "circle";
            const initialCat = (SHAPES_LIB_GALLERY_DEFINITIONS[initialShape] && SHAPES_LIB_GALLERY_DEFINITIONS[initialShape].cat) || node.properties.category || "shapes";
            node.properties.category = initialCat;
            node.properties.shape = initialShape;
            node.widgets_up = true;
            node.resizable = true;
            node.min_size = [140, 175];

            setupDynamicInlineNode(node);

            node.computeSize = function() {
                const curShape = (this.properties && this.properties.shape) || "circle";
                let shapeVarStr = "shape." + curShape;
                const titleW = getExactTextWidth(String(this.title || "Shapes Lib"), "bold 12px sans-serif");
                const varW = getExactTextWidth(shapeVarStr, "italic 11px monospace");
                const req_w = Math.max(156, titleW + 65, varW + 24);
                const req_h = Math.round(req_w * (195 / 156));
                return [req_w, req_h];
            };

            node.onResize = function(size) {
                const minW = 140;
                const aspect = 195 / 156;
                let w = Math.max(minW, Math.round(size[0]));
                if (size[1] && this.size && Math.abs(size[1] - this.size[1]) > Math.abs(size[0] - this.size[0])) {
                    w = Math.max(minW, Math.round(size[1] / aspect));
                }
                const h = Math.round(w * aspect);
                size[0] = w;
                size[1] = h;
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (this.properties) {
                    if (!this.properties.shape) {
                        this.properties.shape = "circle";
                    }
                    if (SHAPES_LIB_GALLERY_DEFINITIONS[this.properties.shape]) {
                        this.properties.category = SHAPES_LIB_GALLERY_DEFINITIONS[this.properties.shape].cat;
                    }
                }
                const sz = this.computeSize();
                this.size[0] = Math.max(this.size[0] || 0, sz[0]);
                this.size[1] = Math.max(this.size[1] || 0, sz[1]);
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                const nodeW = this.size ? this.size[0] : 156;
                const nodeH = this.size ? this.size[1] : 195;

                const availW = Math.max(30, nodeW - 20);
                const availH = Math.max(30, nodeH - 52);
                const cardSide = Math.max(30, Math.min(availW, availH));

                const cardW = cardSide;
                const cardH = cardSide;
                const cardX = Math.floor((nodeW - cardW) / 2);
                const cardY = Math.floor(28 + (availH - cardH) / 2);

                ctx.save();
                ctx.fillStyle = "rgba(18, 22, 31, 0.92)";
                ctx.strokeStyle = "rgba(139, 92, 246, 0.65)";
                ctx.lineWidth = 1.6;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(cardX, cardY, cardW, cardH, 10);
                else ctx.rect(cardX, cardY, cardW, cardH);
                ctx.fill();
                ctx.stroke();

                let curShape = (this.properties && this.properties.shape) || "circle";
                let def = getShapeDefinition(curShape);

                const cardCenterX = cardX + cardW / 2;
                const cardCenterY = cardY + cardH / 2;

                if (curShape === "pixel") {
                    const pw = Math.max(6, Math.floor(cardSide * 0.1));
                    const ph = pw;
                    ctx.save();
                    ctx.fillStyle = "#a7f3d0";
                    ctx.strokeStyle = "#a7f3d0";
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(cardCenterX - pw / 2, cardCenterY - ph / 2, pw, ph, 2);
                    else ctx.rect(cardCenterX - pw / 2, cardCenterY - ph / 2, pw, ph);
                    ctx.fill();
                    ctx.stroke();
                    ctx.restore();
                } else if (def && def.path) {
                    if (!this._cachedShapePath || this._cachedShapeKey !== curShape) {
                        const svgD = assPathToSvg(def.path);
                        this._cachedShapePath = new Path2D(svgD);
                        this._cachedShapeKey = curShape;
                    }

                    const bbox = getAssPathBBox(def.path);
                    const availWCard = Math.max(10, cardW - 24);
                    const availHCard = Math.max(10, cardH - 24);
                    const scale = Math.min(availWCard / bbox.w, availHCard / bbox.h);

                    ctx.save();
                    ctx.translate(cardCenterX, cardCenterY);
                    ctx.scale(scale, scale);
                    ctx.translate(-bbox.cx, -bbox.cy);

                    ctx.fillStyle = "rgba(139, 92, 246, 0.35)";
                    ctx.strokeStyle = "#a7f3d0";
                    ctx.lineWidth = 3.5 / Math.max(0.01, scale);
                    ctx.lineJoin = "round";
                    ctx.lineCap = "round";
                    ctx.fill(this._cachedShapePath);
                    ctx.stroke(this._cachedShapePath);
                    ctx.restore();
                }
                ctx.restore();

                let shapeVarStr = "shape." + curShape;
                ctx.save();
                ctx.font = "italic 11px monospace";
                ctx.fillStyle = "#a7f3d0";
                ctx.textAlign = "center";
                ctx.fillText(shapeVarStr, nodeW / 2, nodeH - 8);
                ctx.restore();

                if (this.outputs && this.outputs.length > 0) {
                    this.outputs[0].pos = [this.size[0] - 10, 16];
                }
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                const nodeW = this.size ? this.size[0] : 156;
                const nodeH = this.size ? this.size[1] : 195;
                const availW = Math.max(30, nodeW - 20);
                const availH = Math.max(30, nodeH - 52);
                const cardSide = Math.max(30, Math.min(availW, availH));

                const cardW = cardSide;
                const cardH = cardSide;
                const cardX = Math.floor((nodeW - cardW) / 2);
                const cardY = Math.floor(28 + (availH - cardH) / 2);

                if (local_pos && local_pos[0] >= cardX - 4 && local_pos[0] <= cardX + cardW + 4 && local_pos[1] >= cardY - 4 && local_pos[1] <= cardY + cardH + 4) {
                    openShapesLibGridPicker(this);
                    return true;
                }
                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            node.onDblClick = function(e, pos) {
                openShapesLibGridPicker(this);
                return true;
            };

            const initSz = node.computeSize();
            node.size = [initSz[0], initSz[1]];
        }


        function setupImgToShapeNode(node) {
            if (!node.properties) node.properties = {};
            if (node.properties.image_path === undefined) node.properties.image_path = "";
            if (!node.properties.threshold) node.properties.threshold = "128";
            if (!node.properties.tolerance) node.properties.tolerance = "1.0";
            if (!node.properties.out_scale) node.properties.out_scale = "1.0";
            if (!node.properties.out_w) node.properties.out_w = "0.0";
            if (!node.properties.out_h) node.properties.out_h = "0.0";
            if (!node.properties.offset_x) node.properties.offset_x = "0.0";
            if (!node.properties.offset_y) node.properties.offset_y = "0.0";
            if (!node.properties.img_scale) node.properties.img_scale = "1.0";
            if (!node.properties.bin_mode) node.properties.bin_mode = "luminance";
            if (!node.properties.alphamax) node.properties.alphamax = "1.0";
            if (!node.properties.opttoler) node.properties.opttoler = "0.2";
            if (!node.properties.invert_img) node.properties.invert_img = "Normal";
            if (!node.properties.mode) node.properties.mode = "Potrace";
            if (node.properties.modo !== undefined) delete node.properties.modo;
            if (!node.properties.anchor) node.properties.anchor = "Center";
            if (!node.properties.invert) node.properties.invert = "Normal";
            if (!node.properties.view_mode) node.properties.view_mode = "Overlay";

            if (node.outputs && node.outputs.length > 0) {
                node.outputs.forEach(out => { delete out.pos; });
            }

            if (node.widgets) {
                node.widgets.forEach(w => {
                    if (w.property && node.properties[w.property] !== undefined) {
                        w.value = node.properties[w.property];
                    }
                });
            }

            node.widgets_up = true;
            setupDynamicInlineNode(node);

            const scheduleImgToShapeFetch = (selfNode, targetFrame) => {
                if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.trace_image_api !== 'function') return;
                const imgPath = String(selfNode.properties ? (selfNode.properties.image_path || "") : "").trim();
                if (!imgPath) return;
                
                const curF = targetFrame !== undefined ? targetFrame : ((selfNode._pendingFrame !== undefined && selfNode._pendingFrame !== null) ? selfNode._pendingFrame : (selfNode._currentFrame || 1));
                selfNode._currentFrame = curF;
                if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);

                if (selfNode._isTracing) {
                    selfNode._pendingFrame = curF;
                    selfNode._pendingRetrace = true;
                    return;
                }

                selfNode._isTracing = true;
                selfNode._pendingFrame = null;
                selfNode._pendingRetrace = false;
                selfNode._tracedPathKey = imgPath;
                const propsCopy = Object.assign({}, selfNode.properties, { preview_frame: curF });

                window.pywebview.api.trace_image_api(propsCopy).then(res => {
                    selfNode._isTracing = false;
                    if (res) {
                        if (res.shape) selfNode._lastTracedShape = res.shape;
                        if (res.total_frames) {
                            const prevTot = selfNode._totalFrames;
                            selfNode._totalFrames = res.total_frames;
                            if (selfNode.properties) selfNode.properties._total_frames = res.total_frames;
                            if (prevTot !== res.total_frames && window.__pyxis_schedule_save) {
                                window.__pyxis_schedule_save(50);
                            }
                        }
                        if (res.frame_index) {
                            const prevCur = selfNode._currentFrame;
                            selfNode._currentFrame = res.frame_index;
                            if (selfNode.properties) selfNode.properties._current_frame = res.frame_index;
                            if (prevCur !== res.frame_index && window.__pyxis_schedule_save) {
                                window.__pyxis_schedule_save(50);
                            }
                        }
                        if (res.preview_image_path) {
                            loadPreviewImage(selfNode, res.preview_image_path);
                        }
                    }
                    if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);

                    if (selfNode._pendingRetrace || (selfNode._pendingFrame !== null && selfNode._pendingFrame !== selfNode._currentFrame)) {
                        const nextF = selfNode._pendingFrame !== null ? selfNode._pendingFrame : selfNode._currentFrame;
                        selfNode._pendingFrame = null;
                        selfNode._pendingRetrace = false;
                        scheduleImgToShapeFetch(selfNode, nextF);
                    }
                }).catch(() => {
                    selfNode._isTracing = false;
                    if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);
                    if (selfNode._pendingRetrace || (selfNode._pendingFrame !== null && selfNode._pendingFrame !== selfNode._currentFrame)) {
                        const nextF = selfNode._pendingFrame !== null ? selfNode._pendingFrame : selfNode._currentFrame;
                        selfNode._pendingFrame = null;
                        selfNode._pendingRetrace = false;
                        scheduleImgToShapeFetch(selfNode, nextF);
                    }
                });
            };

            const oldPropertyChanged = node.onPropertyChanged;
            node.onPropertyChanged = function(property, value, prev_value) {
                if (oldPropertyChanged) oldPropertyChanged.call(this, property, value, prev_value);
                if (property === "_total_frames" || property === "_current_frame") return;
                if (property === "image_path" && value !== prev_value) {
                    this._currentFrame = 1;
                    this._totalFrames = 1;
                    if (this.properties) {
                        this.properties._current_frame = 1;
                        this.properties._total_frames = 1;
                    }
                    if (typeof resetImgPreviewTransform === "function") {
                        resetImgPreviewTransform(this, false);
                    }
                }
                this._pendingFrame = undefined;
                scheduleImgToShapeFetch(this);
            };

            const oldMouseMove = node.onMouseMove;
            node.onMouseMove = function(e, local_pos, canvas) {
                if (local_pos) {
                    const [lx, ly] = getSafeLocalPos(this, local_pos);
                    const layout = getImgNodePreviewLayout(this);
                    const target = hitTestImgPreview(layout, lx, ly);
                    if (this._hoverTarget !== target) {
                        this._hoverTarget = target;
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
                    }
                    updateImgPreviewCursor(this, canvas, target);
                }
                if (oldMouseMove) return oldMouseMove.call(this, e, local_pos, canvas);
            };

            const oldMouseLeave = node.onMouseLeave;
            node.onMouseLeave = function(e, canvas) {
                if (this._hoverTarget || this._pressedTarget) {
                    this._hoverTarget = null;
                    this._pressedTarget = null;
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
                }
                updateImgPreviewCursor(this, canvas, null);
                if (oldMouseLeave) return oldMouseLeave.call(this, e, canvas);
            };

            const oldMouseUp = node.onMouseUp;
            node.onMouseUp = function(e, local_pos, canvas) {
                if (this._pressedTarget) {
                    this._pressedTarget = null;
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
                }
                if (oldMouseUp) return oldMouseUp.call(this, e, local_pos, canvas);
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos) {
                    const [lx, ly] = getSafeLocalPos(this, local_pos);
                    const layout = getImgNodePreviewLayout(this);
                    const target = hitTestImgPreview(layout, lx, ly);

                    if (target) {
                        this._pressedTarget = target;
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
                    }

                    if (target === "prev_frame") {
                        const curF = this._currentFrame || 1;
                        const totF = this._totalFrames || 1;
                        if (totF > 1) {
                            const newFrame = curF > 1 ? (curF - 1) : totF;
                            scheduleImgToShapeFetch(this, newFrame);
                        }
                        return true;
                    }

                    if (target === "next_frame") {
                        const curF = this._currentFrame || 1;
                        const totF = this._totalFrames || 1;
                        if (totF > 1) {
                            const newFrame = curF < totF ? (curF + 1) : 1;
                            scheduleImgToShapeFetch(this, newFrame);
                        }
                        return true;
                    }

                    if (target === "scrub_track") {
                        const selfNode = this;
                        const updateFrameFromEvent = (eMove) => {
                            const canvasObj = canvas || LGraphCanvas.active_canvas || window.canvas || window.graphcanvas;
                            if (!canvasObj || !canvasObj.canvas) return;
                            const rect = canvasObj.canvas.getBoundingClientRect();
                            const scale = (canvasObj.ds && canvasObj.ds.scale) ? canvasObj.ds.scale : 1.0;
                            const tx = (canvasObj.ds && canvasObj.ds.offset) ? canvasObj.ds.offset[0] : 0;
                            const graphX = (eMove.clientX - rect.left) / scale - tx;
                            const nodeLocalX = graphX - selfNode.pos[0];

                            const ratio = Math.max(0, Math.min(1, (nodeLocalX - layout.trackX) / Math.max(1, layout.trackW)));
                            const newFrame = Math.round(1 + ratio * ((selfNode._totalFrames || 1) - 1));
                            if (newFrame !== selfNode._currentFrame) {
                                scheduleImgToShapeFetch(selfNode, newFrame);
                            }
                        };

                        updateFrameFromEvent(e);

                        const onWindowMove = (eMove) => { updateFrameFromEvent(eMove); };
                        const onWindowUp = (eUp) => {
                            if (selfNode._pressedTarget) {
                                selfNode._pressedTarget = null;
                                if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, false);
                            }
                            window.removeEventListener("pointermove", onWindowMove);
                            window.removeEventListener("pointerup", onWindowUp);
                            window.removeEventListener("mousemove", onWindowMove);
                            window.removeEventListener("mouseup", onWindowUp);
                        };

                        window.addEventListener("pointermove", onWindowMove);
                        window.addEventListener("pointerup", onWindowUp);
                        window.addEventListener("mousemove", onWindowMove);
                        window.addEventListener("mouseup", onWindowUp);

                        return true;
                    }

                    if (target === "view_btn") {
                        const VIEW_MODES = ["Overlay", "Image", "Vector"];
                        let curV = (this.properties && this.properties.view_mode) ? this.properties.view_mode : "Overlay";
                        if (curV === "Superposición") curV = "Overlay";
                        if (curV === "Imagen") curV = "Image";
                        let curIdx = VIEW_MODES.indexOf(curV);
                        if (curIdx < 0) curIdx = 0;
                        const nextIdx = (curIdx + 1) % VIEW_MODES.length;
                        this.properties.view_mode = VIEW_MODES[nextIdx];
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("view_mode-cycle");
                        return true;
                    }

                    if (target === "refresh_btn") {
                        const imgPath = String(this.properties ? (this.properties.image_path || "") : "").trim();
                        if (!imgPath) {
                            this._missingImgFlash = Date.now();
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            if (typeof showPyxisToast === "function") {
                                const isEs = window.PyxisI18n && PyxisI18n.currentLang === "es";
                                showPyxisToast(isEs ? "Por favor selecciona una imagen primero" : "Please select an image first", "warning");
                            }
                            return true;
                        }
                        if (this._isTracing) return true;
                        this._isTracing = true;
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);

                        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.trace_image_api === 'function') {
                            window.pywebview.api.trace_image_api(this.properties).then(res => {
                                this._isTracing = false;
                                if (res) {
                                    if (res.shape) this._lastTracedShape = res.shape;
                                    if (res.total_frames) this._totalFrames = res.total_frames;
                                    if (res.frame_index) this._currentFrame = res.frame_index;
                                }
                                if (res && res.preview_image_path) {
                                    loadPreviewImage(this, res.preview_image_path);
                                } else if (this.setDirtyCanvas) {
                                    this.setDirtyCanvas(true, true);
                                }
                            }).catch(() => {
                                this._isTracing = false;
                                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            });
                        } else {
                            this._isTracing = false;
                        }
                        return true;
                    }
                }
                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            const oldResize = node.onResize;
            node.onResize = function(size) {
                if (oldResize) oldResize.call(this, size);
                if (size && size[0] > 0 && size[1] > 0) {
                    this._customSize = [size[0], size[1]];
                }
            };

            node.onDblClick = function(e, local_pos, canvas) {
                if (!local_pos) return false;
                const [lx, ly] = getSafeLocalPos(this, local_pos);
                const layout = getImgNodePreviewLayout(this);
                const target = hitTestImgPreview(layout, lx, ly);

                if (target === "card") {
                    const updateImagePath = (filePath) => {
                        if (!filePath) return;
                        const prev = this.properties["image_path"];
                        this.properties["image_path"] = filePath;
                        if (this.widgets) {
                            this.widgets.forEach(w => {
                                if (w.property === "image_path" || (w.name && (w.name.includes("Shape") || w.name.includes("Ruta") || w.name.includes("image_path")))) {
                                    w.value = filePath;
                                }
                            });
                        }
                        if (typeof this.onPropertyChanged === "function") {
                            this.onPropertyChanged("image_path", filePath, prev);
                        }
                        if (this.computeSize) this.size = this.computeSize();
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    };

                    if (window.pywebview && window.pywebview.api && window.pywebview.api.select_image_dialog) {
                        window.pywebview.api.select_image_dialog().then(filePath => {
                            updateImagePath(filePath);
                        });
                        return true;
                    }
                    let fileInput = document.createElement("input");
                    fileInput.type = "file";
                    fileInput.id = "pyxis-file-input-mesh";
                    fileInput.name = "pyxis-file-input-mesh";
                    fileInput.accept = "image/png, image/jpeg, image/webp, image/gif, image/*";
                    fileInput.onchange = (evt) => {
                        if (evt.target.files && evt.target.files[0]) {
                            const fileObj = evt.target.files[0];
                            const filePath = fileObj.path || fileObj.name;
                            updateImagePath(filePath);
                        }
                    };
                    fileInput.click();
                    return true;
                }
                return false;
            };

            node.computeSize = function() {
                const modeInfo = getTitleModeInfo(this);
                let modeW = 0;
                if (modeInfo) {
                    modeW = Math.max(35, getExactTextWidth(modeInfo.currentShort, "bold 10px monospace") + 12);
                    if (modeInfo.secondaryModes) {
                        modeW += Math.max(35, getExactTextWidth(modeInfo.secondaryShort, "bold 10px monospace") + 12);
                    }
                }

                let max_in_text_w = 0;
                if (this.properties) {
                    for (const k in this.properties) {
                        if (k === "modo" || k === "anchor" || k === "invert" || k === "view_mode" || k === "bin_mode" || k.startsWith("_")) continue;
                        let val = String(this.properties[k] || "");
                        if (k === "image_path") val = "...image.png";
                        if (val.length > 0) {
                            const tw = Math.min(85, getExactTextWidth(val, "bold 11px monospace"));
                            if (tw > max_in_text_w) max_in_text_w = tw;
                        }
                    }
                }

                let max_out_w = 0;
                (this.outputs || []).forEach(out => {
                    if (out.name) {
                        const ow = getExactTextWidth(out.name, "10px sans-serif");
                        if (ow > max_out_w) max_out_w = ow;
                    }
                });

                const num_in = this.inputs ? this.inputs.length : 12;
                const left_box_w = Math.max(70, max_in_text_w + 16);
                const left_col_end = 22 + left_box_w;
                const card_w = 150;
                const right_col_w = max_out_w > 0 ? (max_out_w + 38) : 20;
                const side_margin = 20;

                const titleW = getExactTextWidth(String(this.title || "IMG to Shape"), "bold 12px sans-serif");
                const req_w = Math.max(380, left_col_end + side_margin + card_w + side_margin + right_col_w, 25 + titleW + 20 + modeW + 14);
                const req_h = Math.max(280, 11 + num_in * 23 + 24);

                return [req_w, req_h];
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (this.outputs && this.outputs.length > 0) {
                    this.outputs.forEach(out => { delete out.pos; });
                }
                if (this.properties) {
                    if (this.properties._total_frames && !this._totalFrames) {
                        this._totalFrames = Number(this.properties._total_frames) || 1;
                    }
                    if (this.properties._current_frame && !this._currentFrame) {
                        this._currentFrame = Number(this.properties._current_frame) || 1;
                    }
                }
                if (info && info.size && Array.isArray(info.size)) {
                    this._customSize = [info.size[0], info.size[1]];
                    this.size = [info.size[0], info.size[1]];
                } else {
                    const sz = this.computeSize();
                    this.size[0] = Math.max(this.size[0] || 0, sz[0]);
                    this.size[1] = Math.max(this.size[1] || 0, sz[1]);
                }
                scheduleImgToShapeFetch(this);
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                const isTracing = Boolean(this._isTracing);
                if (isTracing || (this._missingImgFlash && Date.now() - this._missingImgFlash < 800)) {
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
                }

                const layout = getImgNodePreviewLayout(this);
                const { nodeW, nodeH, cardX, cardY, cardW, cardH, cardCenterX, cardCenterY, barY, btnH, btnX, btnW, refreshX, refreshW } = layout;
                let viewMode = (this.properties && this.properties.view_mode) ? this.properties.view_mode : "Overlay";
                if (viewMode === "Superposición") viewMode = "Overlay";
                if (viewMode === "Imagen") viewMode = "Image";

                if (layout.hasTopBar) {
                    ctx.save();
                    const topBarY = layout.topBarY;
                    const topBarH = layout.topBarH;
                    const stepBtnW = layout.stepBtnW;
                    const trackX = layout.trackX;
                    const trackW = layout.trackW;
                    const curF = this._currentFrame || 1;
                    const totF = this._totalFrames || 1;

                    const isPrevHover = this._hoverTarget === "prev_frame";
                    const isPrevPressed = this._pressedTarget === "prev_frame";
                    ctx.fillStyle = isPrevPressed ? "rgba(91, 33, 182, 0.75)" : (isPrevHover ? "rgba(139, 92, 246, 0.32)" : "#12161f");
                    ctx.strokeStyle = totF > 1 ? (isPrevHover ? "#c084fc" : "#8b5cf6") : "#334155";
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(cardX, topBarY, stepBtnW, topBarH, 4);
                    else ctx.rect(cardX, topBarY, stepBtnW, topBarH);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = totF > 1 ? (isPrevHover ? "#ffffff" : "#a7f3d0") : "#475569";
                    const arrowLeftCenterX = cardX + stepBtnW / 2;
                    const arrowLeftCenterY = topBarY + topBarH / 2 + (isPrevPressed ? 1 : 0);
                    ctx.beginPath();
                    ctx.moveTo(arrowLeftCenterX - 3, arrowLeftCenterY);
                    ctx.lineTo(arrowLeftCenterX + 2.5, arrowLeftCenterY - 4);
                    ctx.lineTo(arrowLeftCenterX + 2.5, arrowLeftCenterY + 4);
                    ctx.closePath();
                    ctx.fill();

                    const isNextHover = this._hoverTarget === "next_frame";
                    const isNextPressed = this._pressedTarget === "next_frame";
                    ctx.fillStyle = isNextPressed ? "rgba(91, 33, 182, 0.75)" : (isNextHover ? "rgba(139, 92, 246, 0.32)" : "#12161f");
                    ctx.strokeStyle = totF > 1 ? (isNextHover ? "#c084fc" : "#8b5cf6") : "#334155";
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(cardX + cardW - stepBtnW, topBarY, stepBtnW, topBarH, 4);
                    else ctx.rect(cardX + cardW - stepBtnW, topBarY, stepBtnW, topBarH);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = totF > 1 ? (isNextHover ? "#ffffff" : "#a7f3d0") : "#475569";
                    const arrowRightCenterX = cardX + cardW - stepBtnW / 2;
                    const arrowRightCenterY = topBarY + topBarH / 2 + (isNextPressed ? 1 : 0);
                    ctx.beginPath();
                    ctx.moveTo(arrowRightCenterX + 3, arrowRightCenterY);
                    ctx.lineTo(arrowRightCenterX - 2.5, arrowRightCenterY - 4);
                    ctx.lineTo(arrowRightCenterX - 2.5, arrowRightCenterY + 4);
                    ctx.closePath();
                    ctx.fill();

                    const isTrackHover = this._hoverTarget === "scrub_track";
                    ctx.fillStyle = "#12161f";
                    ctx.strokeStyle = isTrackHover ? "#c084fc" : "#8b5cf6";
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(trackX, topBarY, trackW, topBarH, 5);
                    else ctx.rect(trackX, topBarY, trackW, topBarH);
                    ctx.fill();
                    ctx.stroke();

                    const fillRatio = (curF - 1) / Math.max(1, totF - 1);
                    const fillW = Math.max(6, fillRatio * (trackW - 4));
                    ctx.fillStyle = "rgba(139, 92, 246, 0.35)";
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(trackX + 2, topBarY + 2, fillW, topBarH - 4, 3);
                    else ctx.rect(trackX + 2, topBarY + 2, fillW, topBarH - 4);
                    ctx.fill();

                    const knobX = trackX + 2 + fillRatio * Math.max(0, trackW - 10);
                    ctx.fillStyle = isTrackHover ? "#6ee7b7" : "#34d399";
                    ctx.beginPath();
                    ctx.arc(knobX + 3, topBarY + 9, 4, 0, Math.PI * 2);
                    ctx.fill();

                    ctx.fillStyle = "#e0e7ff";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("Frame " + curF + " / " + totF, trackX + trackW / 2, topBarY + 9);
                    ctx.restore();
                }

                const isViewHover = this._hoverTarget === "view_btn";
                const isViewPressed = this._pressedTarget === "view_btn";
                const viewYOffset = isViewPressed ? 1 : 0;

                ctx.save();
                ctx.font = "bold 10px monospace";
                ctx.fillStyle = isViewPressed ? "rgba(91, 33, 182, 0.75)" : (isViewHover ? "rgba(139, 92, 246, 0.32)" : "#12161f");
                ctx.strokeStyle = isViewHover ? "#c084fc" : "#8b5cf6";
                ctx.lineWidth = isViewHover ? 1.6 : 1.4;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnX, barY + viewYOffset, btnW, btnH, 5);
                else ctx.rect(btnX, barY + viewYOffset, btnW, btnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = isViewHover ? "#ffffff" : "#a7f3d0";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                const isEs1 = window.PyxisI18n && PyxisI18n.currentLang === "es";
                let modeText1 = (this.properties && this.properties.view_mode) ? this.properties.view_mode : "Overlay";
                if (modeText1 === "Superposición" || modeText1 === "Overlay") modeText1 = isEs1 ? "Superposición" : "Overlay";
                else if (modeText1 === "Imagen" || modeText1 === "Image") modeText1 = isEs1 ? "Imagen" : "Image";
                else if (modeText1 === "Vector") modeText1 = "Vector";
                ctx.fillText((isEs1 ? "Vista: " : "View: ") + modeText1, btnX + btnW / 2, barY + btnH / 2 + 1 + viewYOffset);

                const isRefHover = this._hoverTarget === "refresh_btn";
                const isRefPressed = this._pressedTarget === "refresh_btn";
                const refYOffset = isRefPressed ? 1 : 0;

                ctx.fillStyle = isRefPressed ? "rgba(91, 33, 182, 0.75)" : (isTracing ? "#2d1f3d" : (isRefHover ? "rgba(139, 92, 246, 0.32)" : "#12161f"));
                ctx.strokeStyle = isTracing ? "#fbbf24" : (isRefHover ? "#34d399" : "#8b5cf6");
                ctx.lineWidth = isRefHover ? 1.6 : 1.4;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(refreshX, barY + refYOffset, refreshW, btnH, 5);
                else ctx.rect(refreshX, barY + refYOffset, refreshW, btnH);
                ctx.fill();
                ctx.stroke();

                const iconCenterX = refreshX + refreshW / 2;
                const iconCenterY = barY + btnH / 2 + refYOffset;
                ctx.save();
                ctx.translate(iconCenterX, iconCenterY);

                if (isTracing) {
                    const spinAngle = (Date.now() / 120) % (Math.PI * 2);
                    ctx.rotate(spinAngle);
                }

                ctx.strokeStyle = isTracing ? "#fbbf24" : (isRefHover ? "#ffffff" : "#a7f3d0");
                ctx.fillStyle = isTracing ? "#fbbf24" : (isRefHover ? "#ffffff" : "#a7f3d0");
                ctx.lineWidth = 1.5;

                const endAngle = 1.65 * Math.PI;
                ctx.beginPath();
                ctx.arc(0, 0, 4.0, 0.25 * Math.PI, endAngle, false);
                ctx.stroke();

                const endX = 4.0 * Math.cos(endAngle);
                const endY = 4.0 * Math.sin(endAngle);

                ctx.beginPath();
                ctx.moveTo(endX + 3.0, endY - 2.5);
                ctx.lineTo(endX - 1.5, endY - 3.5);
                ctx.lineTo(endX - 0.5, endY + 1.0);
                ctx.closePath();
                ctx.fill();
                ctx.restore();
                ctx.restore();

                const isCardHover = this._hoverTarget === "card";
                let cardStroke = "rgba(139, 92, 246, 0.7)";
                if (this._missingImgFlash && Date.now() - this._missingImgFlash < 800) {
                    const elapsed = Date.now() - this._missingImgFlash;
                    const pulse = 0.5 + 0.5 * Math.sin((elapsed / 800) * Math.PI * 4);
                    cardStroke = `rgba(251, 191, 36, ${0.4 + 0.6 * pulse})`;
                } else if (isCardHover) {
                    cardStroke = "rgba(52, 211, 153, 0.85)";
                } else if (isTracing) {
                    cardStroke = "rgba(251, 191, 36, 0.9)";
                }

                ctx.save();
                ctx.fillStyle = "rgba(18, 22, 31, 0.95)";
                ctx.strokeStyle = cardStroke;
                ctx.lineWidth = (isCardHover || (this._missingImgFlash && Date.now() - this._missingImgFlash < 800)) ? 2.0 : 1.6;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(cardX, cardY, cardW, cardH, 10);
                else ctx.rect(cardX, cardY, cardW, cardH);
                ctx.fill();
                ctx.stroke();

                const imagePath = String(this.properties ? (this.properties.image_path || "") : "").trim();
                if (imagePath && !this._isTracing && this._tracedPathKey !== imagePath) {
                    this._tracedPathKey = imagePath;
                    scheduleImgToShapeFetch(this);
                }
                if (imagePath && (this._imgPathKey !== imagePath || (!this._imgObj && !this._imgLoadedPath))) {
                    this._imgPathKey = imagePath;
                    this._imgLoadedPath = null;
                    const img = new Image();
                    img.onload = () => {
                        if (!this._imgLoadedPath) {
                            this._imgObj = img;
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        }
                    };
                    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_image_file_data_url === 'function') {
                        window.pywebview.api.get_image_file_data_url(imagePath).then(uri => {
                            if (uri && !this._imgLoadedPath) img.src = uri;
                        }).catch(() => {});
                    } else {
                        if (!this._imgLoadedPath) {
                            img.src = imagePath.startsWith("http") ? imagePath : ("file:///" + imagePath.replace(/\\/g, "/"));
                        }
                    }
                } else if (!imagePath) {
                    this._imgObj = null;
                    this._imgLoadedPath = null;
                    this._tracedPathKey = null;
                }

                const cardZoom = (typeof this._cardZoom === "number" && !isNaN(this._cardZoom) && this._cardZoom > 0) ? this._cardZoom : 1.0;
                const cardPanX = (typeof this._cardPanX === "number" && !isNaN(this._cardPanX)) ? this._cardPanX : 0;
                const cardPanY = (typeof this._cardPanY === "number" && !isNaN(this._cardPanY)) ? this._cardPanY : 0;

                if (this._imgObj && (viewMode === "Overlay" || viewMode === "Image" || viewMode === "Superposición" || viewMode === "Imagen")) {
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(cardX + 2, cardY + 2, cardW - 4, cardH - 4, 8);
                    else ctx.rect(cardX + 2, cardY + 2, cardW - 4, cardH - 4);
                    ctx.clip();

                    ctx.translate(cardCenterX + cardPanX, cardCenterY + cardPanY);
                    ctx.scale(cardZoom, cardZoom);
                    ctx.translate(-cardCenterX, -cardCenterY);

                    const iw = this._imgObj.naturalWidth || this._imgObj.width || 1;
                    const ih = this._imgObj.naturalHeight || this._imgObj.height || 1;
                    const fitScale = Math.min((cardW - 8) / iw, (cardH - 8) / ih);
                    const drawW = iw * fitScale;
                    const drawH = ih * fitScale;
                    const drawX = cardX + (cardW - drawW) / 2;
                    const drawY = cardY + (cardH - drawH) / 2;

                    ctx.drawImage(this._imgObj, drawX, drawY, drawW, drawH);
                    ctx.restore();
                }

                let lastShape = this._lastTracedShape || (this.output_values ? this.output_values[0] : null);

                if ((viewMode === "Overlay" || viewMode === "Vector" || viewMode === "Superposición") && lastShape && typeof lastShape === 'string' && lastShape.trim().length > 0) {
                    if (!this._cachedShapePath || this._cachedShapeKey !== lastShape) {
                        const svgD = assPathToSvg(lastShape);
                        this._cachedShapePath = new Path2D(svgD);
                        this._cachedShapeKey = lastShape;
                    }

                    if (this._imgObj) {
                        const iw = this._imgObj.naturalWidth || this._imgObj.width || 1;
                        const ih = this._imgObj.naturalHeight || this._imgObj.height || 1;
                        const fitScale = Math.min((cardW - 8) / iw, (cardH - 8) / ih);
                        const effScale = fitScale * cardZoom;

                        ctx.save();
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(cardX + 2, cardY + 2, cardW - 4, cardH - 4, 8);
                        else ctx.rect(cardX + 2, cardY + 2, cardW - 4, cardH - 4);
                        ctx.clip();

                        ctx.translate(cardCenterX + cardPanX, cardCenterY + cardPanY);
                        ctx.scale(effScale, effScale);

                        ctx.fillStyle = "rgba(139, 92, 246, 0.35)";
                        ctx.strokeStyle = "#a7f3d0";
                        ctx.lineWidth = 1.5 / Math.max(0.1, effScale);
                        ctx.lineJoin = "round";
                        ctx.lineCap = "round";
                        ctx.fill(this._cachedShapePath);
                        ctx.stroke(this._cachedShapePath);
                        ctx.restore();
                    } else {
                        const bbox = getAssPathBBox(lastShape);
                        if (bbox && bbox.w > 0 && bbox.h > 0) {
                            const availW = cardW - 24;
                            const availH = cardH - 24;
                            const scale = Math.min(availW / bbox.w, availH / bbox.h);
                            const effScale = scale * cardZoom;

                            ctx.save();
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(cardX + 2, cardY + 2, cardW - 4, cardH - 4, 8);
                            else ctx.rect(cardX + 2, cardY + 2, cardW - 4, cardH - 4);
                            ctx.clip();

                            ctx.translate(cardCenterX + cardPanX, cardCenterY + cardPanY);
                            ctx.scale(effScale, effScale);
                            ctx.translate(-bbox.cx, -bbox.cy);

                            ctx.fillStyle = "rgba(139, 92, 246, 0.35)";
                            ctx.strokeStyle = "#a7f3d0";
                            ctx.lineWidth = 1.5 / Math.max(0.1, effScale);
                            ctx.lineJoin = "round";
                            ctx.lineCap = "round";
                            ctx.fill(this._cachedShapePath);
                            ctx.stroke(this._cachedShapePath);
                            ctx.restore();
                        }
                    }
                }

                if (isTracing) {
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(cardX + 2, cardY + 2, cardW - 4, cardH - 4, 8);
                    else ctx.rect(cardX + 2, cardY + 2, cardW - 4, cardH - 4);
                    ctx.fillStyle = "rgba(18, 22, 31, 0.65)";
                    ctx.fill();

                    const ringAngle = (Date.now() / 120) % (Math.PI * 2);
                    ctx.strokeStyle = "#34d399";
                    ctx.lineWidth = 2.5;
                    ctx.beginPath();
                    ctx.arc(cardCenterX, cardCenterY - 6, 16, ringAngle, ringAngle + 1.25 * Math.PI);
                    ctx.stroke();

                    ctx.fillStyle = "#fbbf24";
                    ctx.font = "bold 11px monospace";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    const curF = this._currentFrame || 1;
                    const totF = this._totalFrames || 1;
                    const isEs = window.PyxisI18n && PyxisI18n.currentLang === "es";
                    const statusText = totF > 1 ? ("Frame " + curF + "/" + totF + "...") : (isEs ? "Trazando Vector..." : "Tracing Vector...");
                    ctx.fillText(statusText, cardCenterX, cardCenterY + 18);
                    ctx.restore();
                } else if (!this._imgObj && viewMode !== "Vector") {
                    ctx.save();
                    ctx.fillStyle = isCardHover ? "#34d399" : "rgba(167, 243, 208, 0.75)";
                    ctx.font = "bold 11px monospace";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("IMG -> SHAPE", cardCenterX, cardCenterY - 10);
                    ctx.fillStyle = isCardHover ? "#e0e7ff" : "rgba(148, 163, 184, 0.85)";
                    ctx.font = "10px sans-serif";
                    const isEs = window.PyxisI18n && PyxisI18n.currentLang === "es";
                    ctx.fillText(isCardHover ? (isEs ? "Doble clic para elegir" : "Double-click to choose") : (isEs ? "Trazado Vectorial" : "Vector Tracing"), cardCenterX, cardCenterY + 10);
                    ctx.restore();
                }
                ctx.restore();
            };

            const initSz = node.computeSize();
            if (!node.size || node.size[0] <= 0 || node.size[1] <= 0) {
                node.size = [initSz[0], initSz[1]];
            } else {
                node.size[0] = Math.max(node.size[0], initSz[0]);
                node.size[1] = Math.max(node.size[1], initSz[1]);
            }
        }


