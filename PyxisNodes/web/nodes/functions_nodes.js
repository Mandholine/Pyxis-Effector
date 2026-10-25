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
 * @file functions_nodes.js
 * @description UI setups and visual configurations for Functions category nodes.
 * @module PyxisFunctionsNodes
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function setupTagMasterNode(node) {
            if (!node.properties) node.properties = {};
            if (!node.properties.tag_type) node.properties.tag_type = "pos";
            node.widgets_up = true;

            function migrateTagProperties(props) {
                if (!props) return;
                const keys = Object.keys(props);
                for (const k of keys) {
                    if (k === "tag_type") continue;
                    const lk = k.toLowerCase();
                    if (lk !== k) {
                        if (props[lk] === undefined) {
                            props[lk] = props[k];
                        }
                        delete props[k];
                    }
                }
            }
            migrateTagProperties(node.properties);

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const tagKey = (props.tag_type || "pos").toLowerCase();
                const tagDef = TAG_DEFINITIONS[tagKey] || { params: ["Value"] };
                const reqParams = tagDef.params || ["Value"];
                
                let base_w = 210;
                let text_req_w = 0;
                for (const p in props) {
                    if (p === "tag_type") continue;
                    const val = String(props[p] || "");
                    if (val.length > 0) {
                        const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                        if (tw > text_req_w) text_req_w = tw;
                    }
                }
                const right_space = getNodeRightReserve(this);
                const boxW = Math.max(65, Math.ceil(text_req_w + 28));
                return [Math.max(base_w, 22 + boxW + right_space), 11 + reqParams.length * 23 + 58];
            };

            node.updateTagInputs = updateTagInputs;

            function updateTagInputs() {
                const tagKey = (node.properties.tag_type || "pos").toLowerCase();
                const tagDef = TAG_DEFINITIONS[tagKey] || { params: ["Value"], defaults: { Valor: "" } };
                const reqParams = tagDef.params || ["Value"];
                
                const currentInputNames = (node.inputs || []).map(inp => inp.name);
                const matches = currentInputNames.length === reqParams.length &&
                                reqParams.every((p, idx) => currentInputNames[idx] === p);

                if (!matches) {
                    const oldLinks = {};
                    if (node.inputs) {
                        node.inputs.forEach((inp) => {
                            if (inp.link !== null && inp.link !== undefined) {
                                oldLinks[inp.name] = inp.link;
                            }
                        });
                    }

                    if (!node.inputs) node.inputs = [];

                    while (node.inputs.length > reqParams.length) {
                        node.removeInput(node.inputs.length - 1);
                    }

                    while (node.inputs.length < reqParams.length) {
                        const idx = node.inputs.length;
                        node.addInput(reqParams[idx], "data");
                    }

                    reqParams.forEach((paramName, idx) => {
                        const inputSlot = node.inputs[idx];
                        inputSlot.name = paramName;
                        inputSlot.type = "data";
                        inputSlot.label = " ";
                        inputSlot.pos = [10, 20 + idx * 23];

                        if (inputSlot.link === null || inputSlot.link === undefined) {
                            if (oldLinks[paramName] !== undefined && node.graph && node.graph.links) {
                                const linkId = oldLinks[paramName];
                                if (node.graph.links[linkId]) {
                                    inputSlot.link = linkId;
                                }
                            }
                        }
                    });
                } else {
                    node.inputs.forEach((inp, idx) => {
                        inp.label = " ";
                        inp.pos = [10, 20 + idx * 23];
                    });
                }

                if (node.widgets) {
                    node.widgets = node.widgets.filter(w => w.property === "tag_type");
                } else {
                    node.widgets = [];
                }

                reqParams.forEach((paramName, idx) => {
                    const tagDefault = (tagDef.defaults && tagDef.defaults[paramName] !== undefined)
                        ? tagDef.defaults[paramName]
                        : "";
                    if (node.properties[paramName] === undefined || node.properties[paramName] === "" || ((tagKey === "pos" || tagKey === "org") && node.properties[paramName] === "0")) {
                        node.properties[paramName] = tagDefault;
                    }

                    const curVal = String(node.properties[paramName] !== undefined ? node.properties[paramName] : tagDefault);
                    const w = node.addWidget("text", paramName, curVal, function(val) {
                        const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                        node.properties[paramName] = cleanVal;
                        if (node.computeSize) {
                            node.size = node.computeSize();
                        }
                        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                    });
                    w.property = paramName;
                    w.last_y = 11 + idx * 23;
                    w.y = 11 + idx * 23;
                    setupSingleLineTextWidget(node, w, paramName, paramName);
                });

                if (node.computeSize) {
                    node.size = node.computeSize();
                } else {
                    node.size = [195, 11 + reqParams.length * 23 + 70];
                }

                if (node.setDirtyCanvas && node.graph) {
                    node.setDirtyCanvas(true, true);
                }
            }

            const tagWidget = node.widgets ? node.widgets.find(w => w.property === "tag_type") : null;
            if (tagWidget) {
                const origCb = tagWidget.callback;
                tagWidget.callback = function(val) {
                    if (origCb) origCb.call(this, val);
                    node.properties.tag_type = val;
                    updateTagInputs();
                };
                tagWidget.onClick = function(w, n, event) {
                    openTagGridPicker(n, w, event);
                };
            }

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos && local_pos[1] < 0) { // Click inside Title Bar area
                    const modeInfo = getTitleModeInfo(this);
                    if (modeInfo) {
                        const btnText = modeInfo.currentShort;
                        const font = "bold 10px monospace";
                        let textW = 50;
                        if (canvas && canvas.ctx) {
                            canvas.ctx.font = font;
                            textW = canvas.ctx.measureText(btnText).width;
                        }
                        const btnW = Math.max(55, textW + 14);
                        const btnX = this.size[0] - btnW - 8;

                        if (local_pos[0] >= btnX - 4 && local_pos[0] <= btnX + btnW + 6) {
                            const nextIdx = (modeInfo.currentIdx + 1) % modeInfo.modeList.length;
                            const nextMode = modeInfo.modeList[nextIdx];
                            this.properties.tag_type = nextMode.full;
                            updateTagInputs();
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("mode-cycle");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        }
                    }
                }
                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            node.onDblClick = function(e, pos) {
                openTagGridPicker(this, null, e);
                return true;
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                const modeInfo = getTitleModeInfo(this);
                if (modeInfo) {
                    const btnText = modeInfo.currentShort;
                    ctx.save();
                    ctx.font = "bold 10px monospace";
                    const textW = ctx.measureText(btnText).width;
                    const btnW = Math.max(55, textW + 14);
                    const btnH = 20;
                    const btnX = this.size[0] - btnW - 8;
                    const btnY = -25;

                    ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                    ctx.strokeStyle = "#8b5cf6";
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(btnX, btnY, btnW, btnH, 10);
                    else ctx.rect(btnX, btnY, btnW, btnH);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = "#a7f3d0";
                    ctx.textAlign = "center";
                    ctx.fillText(btnText, btnX + btnW / 2, btnY + 14);
                    ctx.restore();
                }

                if (this.inputs && this.widgets) {
                    this.inputs.forEach((inp, idx) => {
                        inp.label = " ";
                        const w = this.widgets.find(widget => widget.property === inp.name);
                        if (w && w.last_y !== undefined) {
                            inp.pos = [10, w.last_y + 9];
                        } else {
                            inp.pos = [10, 11 + idx * 23 + 9];
                        }
                    });
                }

                const tagKey = (this.properties.tag_type || "pos").toLowerCase();
                let previewStr = "\\" + tagKey;
                
                const tagDef = TAG_DEFINITIONS[tagKey] || { params: ["Value"] };
                const params = tagDef.params || ["Value"];
                
                const vals = params.map(p => {
                    const raw = getParamValueForPreview(this, p);
                    return formatPreviewVal(tagKey, raw);
                }).filter(v => v !== "");
                
                if (["pos", "move", "org", "fad", "fade", "clip", "iclip", "t"].includes(tagKey)) {
                    previewStr += "(" + vals.join(",") + ")";
                } else if (vals.length > 0) {
                    previewStr += vals.join("");
                }

                ctx.save();
                ctx.font = "italic 11px sans-serif";
                ctx.fillStyle = "#94a3b8";
                ctx.textAlign = "left";
                
                let desc = (window.PyxisI18n && window.PyxisI18n.getTagDesc) ? window.PyxisI18n.getTagDesc(tagKey) : tagDef.desc;
                if (!desc) desc = tagDef.desc || "parámetro";
                ctx.fillText(desc, 12, this.size[1] - 44);

                ctx.font = "bold 13px monospace";
                ctx.fillStyle = "#a7f3d0";
                
                let dispText = previewStr;
                const maxW = this.size[0] - 24;
                if (ctx.measureText(previewStr).width > maxW) {
                    let truncated = previewStr;
                    while (truncated.length > 0 && ctx.measureText(truncated + "...").width > maxW) {
                        truncated = truncated.slice(0, -1);
                    }
                    dispText = truncated + "...";
                }
                
                ctx.fillText(dispText, 12, this.size[1] - 28);
                ctx.restore();
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                migrateTagProperties(this.properties);
                if (oldConfigure) oldConfigure.call(this, info);
                migrateTagProperties(this.properties);
                updateTagInputs();
            };

            updateTagInputs();
        }


        function setupInlineSlotWidgetsNode(node) {
            if (!node) return;
            node.widgets_up = true;

            let widget_offset = 0;
            if (node.widgets) {
                for (let i = 0; i < node.widgets.length; i++) {
                    const w = node.widgets[i];
                    if (w && w.type === "combo") {
                        w.last_y = 6 + i * 30;
                        widget_offset++;
                    }
                }
            }

            if (node.inputs) {
                node.inputs.forEach((inp, idx) => {
                    inp.label = " ";
                    inp.pos = [0, 19 + (idx + widget_offset) * 30];
                });
            }

            if (node.widgets) {
                let text_idx = 0;
                node.widgets.forEach((w) => {
                    if (!w) return;
                    if (w.type === "combo") return;
                    
                    const slot_idx = text_idx + widget_offset;
                    w.last_y = 6 + slot_idx * 30;
                    text_idx++;

                    if (w.type === "text" && w.property) {
                        setupSingleLineTextWidget(node, w, w.name, w.property);
                    }
                });
            }

            node.computeSize = function() {
                let num_in = this.inputs ? this.inputs.length : 0;
                let num_wid = this.widgets ? this.widgets.length : 0;
                let rows = Math.max(num_in + widget_offset, num_wid, 1);

                let title_text = this.title || "";
                let base_w = Math.max(150, title_text.length * 8.5 + 40);

                if (this.properties) {
                    for (const p in this.properties) {
                        const val = String(this.properties[p] || "");
                        if (val.length > 0) {
                            const tw = (typeof getExactTextWidth === "function") ? getExactTextWidth(val, "bold 11px Consolas, monospace") : (val.length * 8.5);
                            base_w = Math.max(base_w, Math.ceil(tw + 60));
                        }
                    }
                }
                if (this.widgets) {
                    for (let i = 0; i < this.widgets.length; i++) {
                        const w = this.widgets[i];
                        if (w && w.value !== undefined && w.value !== null) {
                            const val = String(w.value || "");
                            if (val.length > 0) {
                                const tw = (typeof getExactTextWidth === "function") ? getExactTextWidth(val, "bold 11px Consolas, monospace") : (val.length * 8.5);
                                base_w = Math.max(base_w, Math.ceil(tw + 60));
                            }
                        }
                    }
                }

                let base_h = 12 + rows * 30;
                return [base_w, base_h];
            };

            if (node.computeSize) {
                node.size = node.computeSize();
            }
        }


        function setupConditionerNode(node) {
            if (!node.properties) node.properties = {};
            if (node.properties.condition === undefined) node.properties.condition = "True";
            if (node.properties.if_true === undefined) node.properties.if_true = "";
            if (node.properties.if_false === undefined) node.properties.if_false = "";
            delete node.properties.total;
            delete node.properties.condicion;
            delete node.properties.si_verdadero;
            delete node.properties.si_falso;
            node.widgets_up = true;

            node.computeSize = function() {
                let base_w = 195;
                let text_req_w = 0;
                const props = this.properties || node.properties || {};
                for (const p in props) {
                    const val = String(props[p] || "");
                    if (val.length > 0) {
                        const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                        if (tw > text_req_w) text_req_w = tw;
                    }
                }
                const right_space = getNodeRightReserve(this);
                const boxW = Math.max(65, Math.ceil(text_req_w + 28));
                return [Math.max(base_w, 22 + boxW + right_space), 11 + 3 * 23 + 22];
            };

            function updateCondicionadorInputs() {
                const reqInputs = ["Condition", "If True", "If False"];

                const currentInputNames = (node.inputs || []).map(inp => inp.name);
                const matches = currentInputNames.length === reqInputs.length &&
                                reqInputs.every((p, idx) => currentInputNames[idx] === p);

                if (!matches) {
                    const oldLinks = {};
                    if (node.inputs) {
                        node.inputs.forEach((inp) => {
                            if (inp.link !== null && inp.link !== undefined) {
                                oldLinks[inp.name] = inp.link;
                            }
                        });
                    }

                    if (!node.inputs) node.inputs = [];

                    while (node.inputs.length > reqInputs.length) {
                        node.removeInput(node.inputs.length - 1);
                    }

                    while (node.inputs.length < reqInputs.length) {
                        const idx = node.inputs.length;
                        node.addInput(reqInputs[idx], "data");
                    }

                    reqInputs.forEach((paramName, idx) => {
                        const inputSlot = node.inputs[idx];
                        inputSlot.name = paramName;
                        inputSlot.type = "data";
                        inputSlot.label = " ";
                        inputSlot.pos = [10, 20 + idx * 23];

                        if (inputSlot.link === null || inputSlot.link === undefined) {
                            if (oldLinks[paramName] !== undefined && node.graph && node.graph.links) {
                                const linkId = oldLinks[paramName];
                                if (node.graph.links[linkId]) {
                                    inputSlot.link = linkId;
                                }
                            }
                        }
                    });
                } else {
                    node.inputs.forEach((inp, idx) => {
                        inp.label = " ";
                        inp.pos = [10, 20 + idx * 23];
                    });
                }

                if (!node.outputs || node.outputs.length === 0) {
                    node.addOutput("String", "data");
                }
                while (node.outputs && node.outputs.length > 1) {
                    node.removeOutput(node.outputs.length - 1);
                }

                node.widgets = [];

                reqInputs.forEach((paramName, idx) => {
                    let propKey = "condition";
                    if (paramName === "If True") propKey = "if_true";
                    else if (paramName === "If False") propKey = "if_false";

                    if (node.properties[propKey] === undefined) {
                        if (propKey === "condition") node.properties[propKey] = "True";
                        else node.properties[propKey] = "";
                    }

                    const curVal = String(node.properties[propKey] !== undefined ? node.properties[propKey] : "");
                    const w = node.addWidget("text", paramName, curVal, function(val) {
                        const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                        node.properties[propKey] = cleanVal;
                        node.properties[paramName] = cleanVal;
                        if (node.computeSize) {
                            node.size = node.computeSize();
                        }
                        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                    });
                    w.property = propKey;
                    w.last_y = 11 + idx * 23;
                    w.y = 11 + idx * 23;
                    setupSingleLineTextWidget(node, w, paramName, propKey);
                });

                if (node.computeSize) {
                    node.size = node.computeSize();
                } else {
                    node.size = [195, 11 + reqInputs.length * 23 + 26];
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                if (this.inputs && this.widgets) {
                    this.inputs.forEach((inp, idx) => {
                        inp.label = " ";
                        inp.pos = [10, 11 + idx * 23 + 9];
                    });
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateCondicionadorInputs();
            };

            updateCondicionadorInputs();
        }


        function setupPolarToCartesianNode(node) {
            if (!node.properties) node.properties = {};
            if (node.properties.x === undefined) node.properties.x = "0";
            if (node.properties.y === undefined) node.properties.y = "0";
            if (node.properties.angle === undefined) node.properties.angle = "0";
            if (node.properties.radius === undefined) node.properties.radius = "100";

            node.widgets_up = true;

            const reqInputs = [
                { name: "Origin X", type: "data", label: " " },
                { name: "Origin Y", type: "data", label: " " },
                { name: "Angle (°)", type: "data", label: " " },
                { name: "Radius", type: "data", label: " " }
            ];

            const reqOutputs = [
                { name: "\\pos Tag", type: "data" },
                { name: "X", type: "data" },
                { name: "Y", type: "data" },
                { name: "dX", type: "data" },
                { name: "dY", type: "data" }
            ];

            function updatePolaresInputs() {
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

                if (!node.outputs) node.outputs = [];
                reqOutputs.forEach((req, idx) => {
                    if (idx >= node.outputs.length) {
                        node.addOutput(req.name, req.type);
                    }
                    const out = node.outputs[idx];
                    out.name = req.name;
                    out.type = req.type;
                });

                node.widgets = [];

                const propsConfig = [
                    { name: "Origin X", prop: "x", aliases: ["x", "Origin X"], default: "0", y: 11, dotY: 20 },
                    { name: "Origin Y", prop: "y", aliases: ["y", "Origin Y"], default: "0", y: 34, dotY: 43 },
                    { name: "Angle (°)", prop: "angle", aliases: ["angle", "Angle (°)", "Angle", "ang"], default: "0", y: 57, dotY: 66 },
                    { name: "Radius", prop: "radius", aliases: ["radius", "Radius", "rad", "r"], default: "100", y: 80, dotY: 89 }
                ];

                propsConfig.forEach((item, idx) => {
                    let foundVal = undefined;
                    for (const a of item.aliases) {
                        if (node.properties[a] !== undefined && node.properties[a] !== null) {
                            foundVal = node.properties[a];
                            break;
                        }
                    }
                    const curVal = String(foundVal !== undefined ? foundVal : item.default);
                    node.properties[item.prop] = curVal;
                    item.aliases.forEach(a => { node.properties[a] = curVal; });

                    const w = node.addWidget("text", item.name, curVal, function(val) {
                        const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                        node.properties[item.prop] = cleanVal;
                        item.aliases.forEach(a => { node.properties[a] = cleanVal; });
                        if (node.computeSize) node.size = node.computeSize();
                        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    });
                    w.property = item.prop;
                    w.last_y = item.y;
                    w.y = item.y;
                    setupSingleLineTextWidget(node, w, item.name, item.prop);

                    if (node.inputs[idx]) {
                        node.inputs[idx].label = " ";
                        node.inputs[idx].pos = [10, item.dotY];
                    }
                });

                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            node.computeSize = function() {
                let base_w = 205;
                let text_req_w = 0;
                if (node.properties) {
                    ["x", "y", "angle", "radius"].forEach(k => {
                        const val = String(node.properties[k] || "");
                        if (val.length > 0) {
                            const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                            if (tw > text_req_w) text_req_w = tw;
                        }
                    });
                }
                const right_space = getNodeRightReserve(this);
                const boxW = Math.max(65, Math.ceil(text_req_w + 28));
                return [Math.max(base_w, 22 + boxW + right_space), 126];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                if (this.widgets && this.widgets.length >= 4) {
                    this.widgets[0].y = 11; this.widgets[0].last_y = 11;
                    this.widgets[1].y = 34; this.widgets[1].last_y = 34;
                    this.widgets[2].y = 57; this.widgets[2].last_y = 57;
                    this.widgets[3].y = 80; this.widgets[3].last_y = 80;
                }

                if (this.inputs && this.inputs.length >= 4) {
                    this.inputs[0].label = " "; this.inputs[0].pos = [10, 20];
                    this.inputs[1].label = " "; this.inputs[1].pos = [10, 43];
                    this.inputs[2].label = " "; this.inputs[2].pos = [10, 66];
                    this.inputs[3].label = " "; this.inputs[3].pos = [10, 89];
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updatePolaresInputs();
            };

            updatePolaresInputs();
        }


        function setupImgToPixelsNode(node) {
            if (!node.properties) node.properties = {};
            if (node.properties.image_path === undefined) node.properties.image_path = "";
            if (!node.properties.particle_shape) node.properties.particle_shape = "";
            if (!node.properties.frame) node.properties.frame = "1";
            if (!node.properties.step) node.properties.step = "2";
            if (!node.properties.alpha_threshold) node.properties.alpha_threshold = "128";
            if (!node.properties.scale) node.properties.scale = "1.0";
            if (!node.properties.anchor) node.properties.anchor = "Center";
            if (!node.properties.order) node.properties.order = "79";
            if (!node.properties.view_mode) node.properties.view_mode = "Overlay";

            if (node.widgets) {
                node.widgets.forEach(w => {
                    if (w.property && node.properties[w.property] !== undefined) {
                        w.value = node.properties[w.property];
                    }
                });
            }

            node.widgets_up = true;
            setupDynamicInlineNode(node);

            const scheduleSampling = (nObj, targetFrame) => {
                if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.sample_pixels_api !== 'function') return;
                const imgPath = String(nObj.properties ? (nObj.properties.image_path || "") : "").trim();
                if (!imgPath) return;
                
                const curF = targetFrame !== undefined ? targetFrame : ((nObj._pendingFrame !== undefined && nObj._pendingFrame !== null) ? nObj._pendingFrame : (nObj._currentFrame || 1));
                nObj._currentFrame = curF;
                if (nObj.setDirtyCanvas) nObj.setDirtyCanvas(true, true);

                if (nObj._isTracing) {
                    nObj._pendingFrame = curF;
                    nObj._pendingResample = true;
                    return;
                }

                nObj._isTracing = true;
                nObj._pendingFrame = null;
                nObj._pendingResample = false;
                nObj._sampledPathKey = imgPath;
                const propsCopy = Object.assign({}, nObj.properties, { preview_frame: curF });

                window.pywebview.api.sample_pixels_api(propsCopy).then(res => {
                    nObj._isTracing = false;
                    nObj._lastSampledFrame = curF;
                    if (res) {
                        if (res.pixels_points) nObj._lastSampledPoints = res.pixels_points;
                        if (res.total_pixels !== undefined) nObj._totalPixels = res.total_pixels;
                        if (res.img_width) nObj._imgWidth = res.img_width;
                        if (res.img_height) nObj._imgHeight = res.img_height;
                        if (res.preview_step) nObj._previewStep = res.preview_step;
                        if (res.total_frames) {
                            const prevTot = nObj._totalFrames;
                            nObj._totalFrames = res.total_frames;
                            if (nObj.properties) nObj.properties._total_frames = res.total_frames;
                            if (prevTot !== res.total_frames && window.__pyxis_schedule_save) {
                                window.__pyxis_schedule_save(50);
                            }
                        }
                        if (res.frame_index) {
                            const prevCur = nObj._currentFrame;
                            nObj._currentFrame = res.frame_index;
                            if (nObj.properties) nObj.properties._current_frame = res.frame_index;
                            if (prevCur !== res.frame_index && window.__pyxis_schedule_save) {
                                window.__pyxis_schedule_save(50);
                            }
                        }
                        if (nObj.computeSize) {
                            const sz = nObj.computeSize();
                            if (nObj.size) {
                                nObj.size[0] = Math.max(nObj.size[0], sz[0]);
                                nObj.size[1] = Math.max(nObj.size[1], sz[1]);
                            }
                        }
                    }
                    if (res && res.preview_image_path) {
                        loadPreviewImage(nObj, res.preview_image_path);
                    } else if (nObj.setDirtyCanvas) {
                        nObj.setDirtyCanvas(true, true);
                    }

                    if (nObj._pendingResample || (nObj._pendingFrame !== null && nObj._pendingFrame !== nObj._currentFrame)) {
                        const nextF = nObj._pendingFrame !== null ? nObj._pendingFrame : nObj._currentFrame;
                        nObj._pendingFrame = null;
                        nObj._pendingResample = false;
                        scheduleSampling(nObj, nextF);
                    }
                }).catch(() => {
                    nObj._isTracing = false;
                    if (nObj.setDirtyCanvas) nObj.setDirtyCanvas(true, true);
                    if (nObj._pendingResample || (nObj._pendingFrame !== null && nObj._pendingFrame !== nObj._currentFrame)) {
                        const nextF = nObj._pendingFrame !== null ? nObj._pendingFrame : nObj._currentFrame;
                        nObj._pendingFrame = null;
                        nObj._pendingResample = false;
                        scheduleSampling(nObj, nextF);
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
                scheduleSampling(this);
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
                            scheduleSampling(this, newFrame);
                        }
                        return true;
                    }

                    if (target === "next_frame") {
                        const curF = this._currentFrame || 1;
                        const totF = this._totalFrames || 1;
                        if (totF > 1) {
                            const newFrame = curF < totF ? (curF + 1) : 1;
                            scheduleSampling(this, newFrame);
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
                                scheduleSampling(selfNode, newFrame);
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
                        const VIEW_MODES = ["Overlay", "Image", "Particles"];
                        let curV = (this.properties && this.properties.view_mode) ? this.properties.view_mode : "Overlay";
                        if (curV === "Superposición") curV = "Overlay";
                        if (curV === "Imagen") curV = "Image";
                        if (curV === "Partículas") curV = "Particles";
                        let curIdx = VIEW_MODES.indexOf(curV);
                        if (curIdx < 0) curIdx = 0;
                        const nextIdx = (curIdx + 1) % VIEW_MODES.length;
                        this.properties.view_mode = VIEW_MODES[nextIdx];
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("view_mode-cycle-pixels");
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
                        this._pendingFrame = undefined;
                        scheduleSampling(this);
                        return true;
                    }
                }
                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (this.properties) {
                    if (this.properties._total_frames && !this._totalFrames) {
                        this._totalFrames = Number(this.properties._total_frames) || 1;
                    }
                    if (this.properties._current_frame && !this._currentFrame) {
                        this._currentFrame = Number(this.properties._current_frame) || 1;
                    }
                }
                const sz = this.computeSize ? this.computeSize() : [380, 280];
                if (info && info.size && Array.isArray(info.size)) {
                    this._customSize = [info.size[0], info.size[1]];
                    this.size = [Math.max(info.size[0], sz[0]), Math.max(info.size[1], sz[1])];
                } else {
                    this.size[0] = Math.max(this.size[0] || 0, sz[0]);
                    this.size[1] = Math.max(this.size[1] || 0, sz[1]);
                }
                scheduleSampling(this);
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
                    fileInput.id = "pyxis-file-input-shape";
                    fileInput.name = "pyxis-file-input-shape";
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
                let max_in_text_w = 0;
                if (this.properties) {
                    for (const k in this.properties) {
                        if (k === "anchor" || k === "order" || k === "view_mode" || k.startsWith("_")) continue;
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

                const num_in = this.inputs ? this.inputs.length : 8;
                const left_box_w = Math.max(70, max_in_text_w + 16);
                const left_col_end = 22 + left_box_w;
                const card_w = 150;
                const right_col_w = max_out_w > 0 ? (max_out_w + 38) : 20;
                const side_margin = 20;

                const titleW = getExactTextWidth(String(this.title || "IMG to pixels"), "bold 12px sans-serif");
                const req_w = Math.max(380, left_col_end + side_margin + card_w + side_margin + right_col_w, 25 + titleW + 40);
                const req_h = Math.max(280, 11 + num_in * 23 + 24);

                return [req_w, req_h];
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
                else if (modeText1 === "Partículas" || modeText1 === "Particles") modeText1 = isEs1 ? "Partículas" : "Particles";
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
                if (imagePath && !this._isTracing && this._sampledPathKey !== imagePath) {
                    this._sampledPathKey = imagePath;
                    scheduleSampling(this);
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
                    this._sampledPathKey = null;
                }

                const cardZoom = (typeof this._cardZoom === "number" && !isNaN(this._cardZoom) && this._cardZoom > 0) ? this._cardZoom : 1.0;
                const cardPanX = (typeof this._cardPanX === "number" && !isNaN(this._cardPanX)) ? this._cardPanX : 0;
                const cardPanY = (typeof this._cardPanY === "number" && !isNaN(this._cardPanY)) ? this._cardPanY : 0;

                const iw = (this._imgObj && (this._imgObj.naturalWidth || this._imgObj.width)) || this._imgWidth || 200;
                const ih = (this._imgObj && (this._imgObj.naturalHeight || this._imgObj.height)) || this._imgHeight || 200;
                const fitScale = Math.min((cardW - 8) / iw, (cardH - 8) / ih);
                const drawW = iw * fitScale;
                const drawH = ih * fitScale;
                const drawX = cardX + (cardW - drawW) / 2;
                const drawY = cardY + (cardH - drawH) / 2;

                if (this._imgObj && (viewMode === "Overlay" || viewMode === "Image" || viewMode === "Superposición" || viewMode === "Imagen")) {
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(cardX + 2, cardY + 2, cardW - 4, cardH - 4, 8);
                    else ctx.rect(cardX + 2, cardY + 2, cardW - 4, cardH - 4);
                    ctx.clip();

                    ctx.translate(cardCenterX + cardPanX, cardCenterY + cardPanY);
                    ctx.scale(cardZoom, cardZoom);
                    ctx.translate(-cardCenterX, -cardCenterY);

                    ctx.drawImage(this._imgObj, drawX, drawY, drawW, drawH);
                    ctx.restore();
                }

                const pts = this._lastSampledPoints || [];
                if ((viewMode === "Overlay" || viewMode === "Particles" || viewMode === "Superposición") && pts.length > 0) {
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(cardX + 2, cardY + 2, cardW - 4, cardH - 4, 8);
                    else ctx.rect(cardX + 2, cardY + 2, cardW - 4, cardH - 4);
                    ctx.clip();

                    ctx.translate(cardCenterX + cardPanX, cardCenterY + cardPanY);
                    ctx.scale(cardZoom, cardZoom);
                    ctx.translate(-cardCenterX, -cardCenterY);

                    const actualStep = this._previewStep || Number(this.properties ? (this.properties.step || 2) : 2);
                    const pSize = Math.max(1.0 / cardZoom, actualStep * fitScale + 0.05);

                    const maxGridX = Math.floor((iw - 1) / actualStep) * actualStep;
                    const maxGridY = Math.floor((ih - 1) / actualStep) * actualStep;
                    const totalGridW = maxGridX + actualStep;
                    const totalGridH = maxGridY + actualStep;
                    const offX = (iw - totalGridW) / 2.0;
                    const offY = (ih - totalGridH) / 2.0;

                    for (let i = 0; i < pts.length; i++) {
                        const pt = pts[i];
                        const px = drawX + (pt[0] + offX) * fitScale;
                        const py = drawY + (pt[1] + offY) * fitScale;
                        const r = pt[2], g = pt[3], b = pt[4], a = (pt[5] !== undefined ? pt[5] / 255.0 : 1.0);
                        ctx.fillStyle = `rgba(${r},${g},${b},${a})`;
                        ctx.fillRect(px, py, pSize, pSize);
                    }
                    ctx.restore();
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
                    const statusText = totF > 1 ? ("Frame " + curF + "/" + totF + "...") : (isEs ? "Muestreando..." : "Sampling...");
                    ctx.fillText(statusText, cardCenterX, cardCenterY + 18);
                    ctx.restore();
                } else if (!this._imgObj && viewMode !== "Particles" && pts.length === 0) {
                    ctx.save();
                    ctx.fillStyle = isCardHover ? "#34d399" : "rgba(167, 243, 208, 0.75)";
                    ctx.font = "bold 11px monospace";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("IMG -> PIXELS", cardCenterX, cardCenterY - 10);
                    ctx.fillStyle = isCardHover ? "#e0e7ff" : "rgba(148, 163, 184, 0.85)";
                    ctx.font = "10px sans-serif";
                    const isEs = window.PyxisI18n && PyxisI18n.currentLang === "es";
                    ctx.fillText(isCardHover ? (isEs ? "Doble clic para elegir" : "Double-click to choose") : (isEs ? "Muestreador Partículas" : "Particle Sampler"), cardCenterX, cardCenterY + 10);
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


        function openGlitterInlineEditor(node, rowIndex, colType) {
            const existing = document.getElementById("pyxis-inline-text-editor");
            if (existing) {
                if (typeof existing._saveAndClose === "function") existing._saveAndClose();
                else existing.remove();
            }

            const canvas = LGraphCanvas.active_canvas;
            if (!canvas || !canvas.canvas) return;

            const curVal = String(
                colType === "start_time" ? (node.properties.start_time !== undefined ? node.properties.start_time : "0") :
                colType === "end_time" ? (node.properties.end_time !== undefined ? node.properties.end_time : "fx.dur") :
                colType === "density" ? (node.properties.density !== undefined ? node.properties.density : "1.0") :
                colType === "tag" ? (node.properties.tags[rowIndex] || "\\fscx") :
                colType === "min" ? (node.properties.mins[rowIndex] || "150") :
                (node.properties.maxs[rowIndex] || "250")
            );

            const placeholder =
                colType === "start_time" ? "0" :
                colType === "end_time" ? "fx.dur" :
                colType === "density" ? "1.0" :
                colType === "tag" ? "\\fscx" : (colType === "min" ? "150" : "250");

            const textColor =
                (colType === "start_time" || colType === "end_time" || colType === "density" || colType === "tag") ? "#a7f3d0" :
                (colType === "min" ? "#38bdf8" : "#f472b6");

            node._editing_cell = { row: rowIndex, col: colType };
            if (canvas.draw) canvas.draw(true, true);

            const boxCoords = node.getBoxCoords(rowIndex, colType);
            const rect = canvas.canvas.getBoundingClientRect();
            const scale = canvas.ds ? canvas.ds.scale : 1.0;
            const offset = canvas.ds ? canvas.ds.offset : [0, 0];

            const screenX = rect.left + (node.pos[0] + boxCoords.x + offset[0]) * scale;
            const screenY = rect.top + (node.pos[1] + boxCoords.y + offset[1]) * scale;
            const screenW = boxCoords.w * scale;
            const screenH = boxCoords.h * scale;

            const initialPadLeft = Math.max(4, Math.round(8 * scale));
            const initialPadRight = Math.max(2, Math.round(6 * scale));

            const inputEl = document.createElement("input");
            inputEl.id = "pyxis-inline-text-editor";
            inputEl.name = "pyxis-glitter-text-editor";
            inputEl.type = "text";
            inputEl.value = curVal;
            inputEl.placeholder = placeholder;
            inputEl.style.position = "fixed";
            inputEl.style.left = screenX + "px";
            inputEl.style.top = screenY + "px";
            inputEl.style.width = screenW + "px";
            inputEl.style.height = screenH + "px";
            inputEl.style.boxSizing = "border-box";
            inputEl.style.borderRadius = (5 * scale) + "px";
            inputEl.style.background = "#12161f";
            inputEl.style.border = (1.5 * scale) + "px solid #8b5cf6";
            inputEl.style.color = textColor;
            inputEl.style.font = "bold " + Math.max(9, Math.round(11 * scale)) + "px Consolas, monospace";
            inputEl.style.padding = "0 " + initialPadRight + "px 0 " + initialPadLeft + "px";
            inputEl.style.lineHeight = (screenH - 3 * scale) + "px";
            inputEl.style.zIndex = "90000";
            inputEl.style.outline = "none";
            inputEl.style.textIndent = "0px";
            inputEl.style.textAlign = "left";
            inputEl.style.boxShadow = "0 0 10px rgba(139, 92, 246, 0.6)";
            inputEl.style.overflow = "hidden";

            document.body.appendChild(inputEl);
            let isMounting = true;
            setTimeout(() => {
                isMounting = false;
                inputEl.focus();
                inputEl.setSelectionRange(0, inputEl.value.length);
            }, 30);

            inputEl.oninput = function() {
                const cleanVal = String(inputEl.value || "").replace(/[\r\n]+/g, " ");
                if (colType === "start_time") {
                    node.properties.start_time = cleanVal;
                } else if (colType === "end_time") {
                    node.properties.end_time = cleanVal;
                } else if (colType === "density") {
                    node.properties.density = cleanVal;
                } else if (colType === "tag") {
                    node.properties.tags[rowIndex] = cleanVal;
                    node.properties["tag_" + rowIndex] = cleanVal;
                } else if (colType === "min") {
                    node.properties.mins[rowIndex] = cleanVal;
                    node.properties["min_" + rowIndex] = cleanVal;
                } else if (colType === "max") {
                    node.properties.maxs[rowIndex] = cleanVal;
                    node.properties["max_" + rowIndex] = cleanVal;
                }

                if (typeof node.computeSize === "function") {
                    const minSz = node.computeSize();
                    if (minSz && Array.isArray(minSz)) {
                        node.size = [Math.max(node.size ? node.size[0] : 252, minSz[0]), minSz[1]];
                    }
                }

                if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                if (canvas.draw) canvas.draw(true, true);

                const newRect = canvas.canvas.getBoundingClientRect();
                const newScale = canvas.ds ? canvas.ds.scale : 1.0;
                const newOffset = canvas.ds ? canvas.ds.offset : [0, 0];
                const newCoords = node.getBoxCoords(rowIndex, colType);

                const newScreenX = newRect.left + (node.pos[0] + newCoords.x + newOffset[0]) * newScale;
                const newScreenY = newRect.top + (node.pos[1] + newCoords.y + newOffset[1]) * newScale;
                const newScreenW = newCoords.w * newScale;
                const newScreenH = newCoords.h * newScale;

                inputEl.style.left = newScreenX + "px";
                inputEl.style.top = newScreenY + "px";
                inputEl.style.width = newScreenW + "px";
                inputEl.style.height = newScreenH + "px";
                inputEl.style.borderRadius = (5 * newScale) + "px";
                inputEl.style.border = (1.5 * newScale) + "px solid #8b5cf6";
                inputEl.style.font = "bold " + Math.max(9, Math.round(11 * newScale)) + "px Consolas, monospace";
                const curPadLeft = Math.max(4, Math.round(8 * newScale));
                const curPadRight = Math.max(2, Math.round(6 * newScale));
                inputEl.style.padding = "0 " + curPadRight + "px 0 " + curPadLeft + "px";
                inputEl.style.lineHeight = (newScreenH - 3 * newScale) + "px";
            };

            let isClosed = false;
            function saveAndClose() {
                if (isClosed) return;
                isClosed = true;
                delete node._editing_cell;
                const cleanVal = String(inputEl.value || "").replace(/[\r\n]+/g, " ");
                if (colType === "start_time") {
                    node.properties.start_time = cleanVal;
                } else if (colType === "end_time") {
                    node.properties.end_time = cleanVal;
                } else if (colType === "density") {
                    node.properties.density = cleanVal;
                } else if (colType === "tag") {
                    node.properties.tags[rowIndex] = cleanVal;
                    node.properties["tag_" + rowIndex] = cleanVal;
                } else if (colType === "min") {
                    node.properties.mins[rowIndex] = cleanVal;
                    node.properties["min_" + rowIndex] = cleanVal;
                } else if (colType === "max") {
                    node.properties.maxs[rowIndex] = cleanVal;
                    node.properties["max_" + rowIndex] = cleanVal;
                }

                if (typeof node.computeSize === "function") {
                    const minSz = node.computeSize();
                    if (minSz && Array.isArray(minSz)) {
                        node.size = [Math.max(node.size ? node.size[0] : 252, minSz[0]), minSz[1]];
                    }
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                if (canvas.draw) canvas.draw(true, true);
                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("glitter-edit-" + colType);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                inputEl.onblur = null;
                if (inputEl.parentNode) inputEl.parentNode.removeChild(inputEl);
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
                    isClosed = true;
                    delete node._editing_cell;
                    if (colType === "start_time") {
                        node.properties.start_time = curVal;
                    } else if (colType === "end_time") {
                        node.properties.end_time = curVal;
                    } else if (colType === "density") {
                        node.properties.density = curVal;
                    } else if (colType === "tag") {
                        node.properties.tags[rowIndex] = curVal;
                        node.properties["tag_" + rowIndex] = curVal;
                    } else if (colType === "min") {
                        node.properties.mins[rowIndex] = curVal;
                        node.properties["min_" + rowIndex] = curVal;
                    } else if (colType === "max") {
                        node.properties.maxs[rowIndex] = curVal;
                        node.properties["max_" + rowIndex] = curVal;
                    }
                    inputEl.onblur = null;
                    if (inputEl.parentNode) inputEl.parentNode.removeChild(inputEl);
                    if (node.computeSize) {
                        const minSz = node.computeSize();
                        if (minSz) node.size = [Math.max(node.size ? node.size[0] : 252, minSz[0]), minSz[1]];
                    }
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                    if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                    if (canvas.draw) canvas.draw(true, true);
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

        function setupGlitterNode(node) {
            if (!node.properties) node.properties = {};
            const legacyModeMap = {
                "destellos": "flashes",
                "pulsos": "pulses",
                "oleaje": "waves",
                "ruido": "noise",
                "destello": "flashes",
                "pulso": "pulses",
                "onda": "waves"
            };
            let currentMode = String(node.properties.mode || "flashes").toLowerCase().trim();
            if (legacyModeMap[currentMode]) {
                currentMode = legacyModeMap[currentMode];
            }
            node.properties.mode = currentMode;
            if (node.properties.modo_oscilacion !== undefined) delete node.properties.modo_oscilacion;
            if (node.properties.modo !== undefined) delete node.properties.modo;
            if (node.properties.start_time === undefined) node.properties.start_time = "0";
            if (node.properties.end_time === undefined) node.properties.end_time = "fx.dur";
            if (node.properties.density === undefined) node.properties.density = "1.0";
            if (node.properties.seed === undefined) node.properties.seed = "0";

            if (!Array.isArray(node.properties.tags) || node.properties.tags.length === 0) {
                node.properties.tags = ["\\fscx"];
                node.properties.mins = ["150"];
                node.properties.maxs = ["250"];
            }
            if (!Array.isArray(node.properties.mins)) node.properties.mins = ["150"];
            if (!Array.isArray(node.properties.maxs)) node.properties.maxs = ["250"];

            node.getRowBoxWidths = function() {
                const numRows = (this.properties.tags && Array.isArray(this.properties.tags)) ? this.properties.tags.length : 1;
                let maxTagW = 60;
                let maxMinW = 46;
                let maxMaxW = 46;

                for (let i = 0; i < numRows; i++) {
                    const tagText = String((this.properties.tags && this.properties.tags[i] !== undefined) ? this.properties.tags[i] : "\\fscx");
                    const minText = String((this.properties.mins && this.properties.mins[i] !== undefined) ? this.properties.mins[i] : "150");
                    const maxText = String((this.properties.maxs && this.properties.maxs[i] !== undefined) ? this.properties.maxs[i] : "250");

                    const tw1 = getExactTextWidth(tagText.trim() || "\\fscx", "bold 11px Consolas, monospace");
                    const tw2 = getExactTextWidth(minText.trim() || "150", "bold 11px Consolas, monospace");
                    const tw3 = getExactTextWidth(maxText.trim() || "250", "bold 11px Consolas, monospace");

                    const w1 = Math.max(60, Math.ceil(tw1 + 24));
                    const w2 = Math.max(46, Math.ceil(tw2 + 24));
                    const w3 = Math.max(46, Math.ceil(tw3 + 24));

                    if (w1 > maxTagW) maxTagW = w1;
                    if (w2 > maxMinW) maxMinW = w2;
                    if (w3 > maxMaxW) maxMaxW = w3;
                }

                const stVal = String(this.properties.start_time !== undefined ? this.properties.start_time : "0");
                const etVal = String(this.properties.end_time !== undefined ? this.properties.end_time : "fx.dur");
                const densVal = String(this.properties.density !== undefined ? this.properties.density : "1.0");

                const stW = Math.max(80, Math.ceil(getExactTextWidth(stVal.trim() || "0", "bold 11px Consolas, monospace") + 24));
                const etW = Math.max(80, Math.ceil(getExactTextWidth(etVal.trim() || "fx.dur", "bold 11px Consolas, monospace") + 24));
                const densW = Math.max(60, Math.ceil(getExactTextWidth(densVal.trim() || "1.0", "bold 11px Consolas, monospace") + 24));

                const combinedTagRowW = maxTagW + 6 + maxMinW + 6 + maxMaxW;
                const upperW = Math.max(stW, etW, densW);

                return { tagW: maxTagW, minW: maxMinW, maxW: maxMaxW, startW: upperW, endW: upperW, densW: upperW, combinedTagRowW: combinedTagRowW };
            };

            node.getBoxCoords = function(rowIndex, colType) {
                const widths = this.getRowBoxWidths ? this.getRowBoxWidths() : { tagW: 60, minW: 46, maxW: 46, startW: 80, endW: 80, densW: 80, combinedTagRowW: 178 };
                const h = 18;

                if (colType === "start_time") {
                    return { x: 24, y: 32, w: widths.startW, h: h };
                }
                if (colType === "end_time") {
                    return { x: 24, y: 55, w: widths.endW, h: h };
                }
                if (colType === "density") {
                    return { x: 24, y: 78, w: widths.densW, h: h };
                }

                const tagStartY = 101;
                const rowH = 23;
                const y = tagStartY + rowIndex * rowH;

                const box1X = 24;
                const box1W = widths.tagW;
                const box2X = box1X + box1W + 6;
                const box2W = widths.minW;
                const box3X = box2X + box2W + 6;
                const box3W = widths.maxW;

                if (colType === "tag") return { x: box1X, y: y, w: box1W, h: h };
                if (colType === "min") return { x: box2X, y: y, w: box2W, h: h };
                return { x: box3X, y: y, w: box3W, h: h };
            };

            node.syncSlotsWithRows = function() {
                const numRows = (this.properties.tags && Array.isArray(this.properties.tags)) ? this.properties.tags.length : 1;

                for (let i = 0; i < numRows; i++) {
                    this.properties["tag_" + i] = this.properties.tags[i] || "\\fscx";
                    this.properties["min_" + i] = this.properties.mins[i] || "150";
                    this.properties["max_" + i] = this.properties.maxs[i] || "250";
                }

                const totalInputs = 3 + numRows;
                while (this.inputs && this.inputs.length < totalInputs) {
                    this.addInput(" ", "data");
                }
                while (this.inputs && this.inputs.length > totalInputs) {
                    this.removeInput(this.inputs.length - 1);
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].name = "Start";
                    this.inputs[0].label = " ";
                }
                if (this.inputs && this.inputs[1]) {
                    this.inputs[1].name = "End";
                    this.inputs[1].label = " ";
                }
                if (this.inputs && this.inputs[2]) {
                    this.inputs[2].name = "Density";
                    this.inputs[2].label = " ";
                }
                for (let i = 0; i < numRows; i++) {
                    if (this.inputs && this.inputs[3 + i]) {
                        this.inputs[3 + i].name = "In " + (i + 1);
                        this.inputs[3 + i].label = " ";
                    }
                }

                const listLabel = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot("List") : "List";
                if (!this.outputs || this.outputs.length === 0) {
                    this.addOutput(listLabel, "data");
                } else {
                    this.outputs[0].name = listLabel;
                    this.outputs[0].label = listLabel;
                }
                while (this.outputs.length < numRows + 1) {
                    const idx = this.outputs.length;
                    this.addOutput("TAG " + idx, "data");
                }
                while (this.outputs.length > numRows + 1) {
                    this.removeOutput(this.outputs.length - 1);
                }

                const nodeW = this.size ? this.size[0] : 260;
                const tagStartY = 101;
                const rowH = 23;

                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [nodeW - 10, 13];
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].pos = [10, 32 + 9];
                }
                if (this.inputs && this.inputs[1]) {
                    this.inputs[1].pos = [10, 55 + 9];
                }
                if (this.inputs && this.inputs[2]) {
                    this.inputs[2].pos = [10, 78 + 9];
                }
                for (let i = 0; i < numRows; i++) {
                    const centerY = tagStartY + i * rowH + 9;
                    if (this.inputs && this.inputs[3 + i]) {
                        this.inputs[3 + i].pos = [10, centerY];
                    }
                    if (this.outputs && this.outputs[i + 1]) {
                        this.outputs[i + 1].pos = [nodeW - 10, centerY];
                    }
                }

                if (this.computeSize) {
                    const sz = this.computeSize();
                    this.size = [Math.max(this.size ? this.size[0] : 260, sz[0]), sz[1]];
                }
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            node.syncSlotsWithRows();

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                this.syncSlotsWithRows();
            };

            const oldDrawForeground = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDrawForeground) oldDrawForeground.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                const nodeW = this.size ? this.size[0] : 260;
                const numRows = (this.properties.tags && Array.isArray(this.properties.tags)) ? this.properties.tags.length : 1;
                const tagStartY = 101;
                const rowH = 23;

                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [nodeW - 10, 13];
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].pos = [10, 32 + 9];
                    this.inputs[0].name = "Start";
                    this.inputs[0].label = " ";
                }
                if (this.inputs && this.inputs[1]) {
                    this.inputs[1].pos = [10, 55 + 9];
                    this.inputs[1].name = "End";
                    this.inputs[1].label = " ";
                }
                if (this.inputs && this.inputs[2]) {
                    this.inputs[2].pos = [10, 78 + 9];
                    this.inputs[2].name = "Density";
                    this.inputs[2].label = " ";
                }
                for (let i = 0; i < numRows; i++) {
                    const centerY = tagStartY + i * rowH + 9;
                    if (this.inputs && this.inputs[3 + i]) {
                        this.inputs[3 + i].pos = [10, centerY];
                        this.inputs[3 + i].name = "In " + (i + 1);
                        this.inputs[3 + i].label = " ";
                    }
                    if (this.outputs && this.outputs[i + 1]) {
                        this.outputs[i + 1].pos = [nodeW - 10, centerY];
                    }
                }

                ctx.save();

                const rawMode = this.properties.mode || "flashes";
                const modeText = (window.PyxisI18n && window.PyxisI18n.translateMode) ? window.PyxisI18n.translateMode(rawMode) : rawMode;
                ctx.font = "bold 10px monospace";
                const modeTextW = ctx.measureText(modeText).width;
                const modeBtnW = Math.max(55, modeTextW + 14);
                const modeBtnH = 20;
                const modeBtnX = nodeW - modeBtnW - 8;
                const modeBtnY = -25;

                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = "#8b5cf6";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(modeBtnX, modeBtnY, modeBtnW, modeBtnH, 10);
                else ctx.rect(modeBtnX, modeBtnY, modeBtnW, modeBtnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = "#a7f3d0";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(modeText, modeBtnX + modeBtnW / 2, modeBtnY + 10);

                const cx = Math.floor(nodeW / 2);
                const btnAddX = cx - 24;
                const btnAddY = 5;
                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = "#8b5cf6";
                ctx.lineWidth = 1.4;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnAddX, btnAddY, 20, 18, 5);
                else ctx.rect(btnAddX, btnAddY, 20, 18);
                ctx.fill();
                ctx.stroke();

                ctx.strokeStyle = "#a7f3d0";
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(btnAddX + 5, btnAddY + 9);
                ctx.lineTo(btnAddX + 15, btnAddY + 9);
                ctx.moveTo(btnAddX + 10, btnAddY + 4);
                ctx.lineTo(btnAddX + 10, btnAddY + 14);
                ctx.stroke();

                const btnRemX = cx + 4;
                const btnRemY = 5;
                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = numRows > 1 ? "#8b5cf6" : "#334155";
                ctx.lineWidth = 1.4;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnRemX, btnRemY, 20, 18, 5);
                else ctx.rect(btnRemX, btnRemY, 20, 18);
                ctx.fill();
                ctx.stroke();

                ctx.strokeStyle = numRows > 1 ? "#f472b6" : "#64748b";
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(btnRemX + 5, btnRemY + 9);
                ctx.lineTo(btnRemX + 15, btnRemY + 9);
                ctx.stroke();

                const stCoords = this.getBoxCoords(0, "start_time");
                const stVal = String(this.properties.start_time !== undefined ? this.properties.start_time : "0");
                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = (this._editing_cell && this._editing_cell.col === "start_time") ? "#8b5cf6" : "#475569";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(stCoords.x, stCoords.y, stCoords.w, stCoords.h, 5);
                else ctx.rect(stCoords.x, stCoords.y, stCoords.w, stCoords.h);
                ctx.fill();
                ctx.stroke();

                const isEditingSt = this._editing_cell && this._editing_cell.col === "start_time";
                if (!isEditingSt) {
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(stCoords.x + 2, stCoords.y + 2, stCoords.w - 4, stCoords.h - 4, 3);
                    else ctx.rect(stCoords.x + 2, stCoords.y + 2, stCoords.w - 4, stCoords.h - 4);
                    ctx.clip();

                    ctx.font = "bold 11px Consolas, monospace";
                    ctx.fillStyle = stVal.trim() ? "#a7f3d0" : "#64748b";
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    ctx.fillText(stVal.trim() || "0", stCoords.x + 8, stCoords.y + 9);
                    ctx.restore();
                }

                const etCoords = this.getBoxCoords(0, "end_time");
                const etVal = String(this.properties.end_time !== undefined ? this.properties.end_time : "fx.dur");
                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = (this._editing_cell && this._editing_cell.col === "end_time") ? "#8b5cf6" : "#475569";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(etCoords.x, etCoords.y, etCoords.w, etCoords.h, 5);
                else ctx.rect(etCoords.x, etCoords.y, etCoords.w, etCoords.h);
                ctx.fill();
                ctx.stroke();

                const isEditingEt = this._editing_cell && this._editing_cell.col === "end_time";
                if (!isEditingEt) {
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(etCoords.x + 2, etCoords.y + 2, etCoords.w - 4, etCoords.h - 4, 3);
                    else ctx.rect(etCoords.x + 2, etCoords.y + 2, etCoords.w - 4, etCoords.h - 4);
                    ctx.clip();

                    ctx.font = "bold 11px Consolas, monospace";
                    ctx.fillStyle = etVal.trim() ? "#a7f3d0" : "#64748b";
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    ctx.fillText(etVal.trim() || "fx.dur", etCoords.x + 8, etCoords.y + 9);
                    ctx.restore();
                }

                const densCoords = this.getBoxCoords(0, "density");
                const densVal = String(this.properties.density !== undefined ? this.properties.density : "1.0");
                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = (this._editing_cell && this._editing_cell.col === "density") ? "#8b5cf6" : "#475569";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(densCoords.x, densCoords.y, densCoords.w, densCoords.h, 5);
                else ctx.rect(densCoords.x, densCoords.y, densCoords.w, densCoords.h);
                ctx.fill();
                ctx.stroke();

                const isEditingDens = this._editing_cell && this._editing_cell.col === "density";
                if (!isEditingDens) {
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(densCoords.x + 2, densCoords.y + 2, densCoords.w - 4, densCoords.h - 4, 3);
                    else ctx.rect(densCoords.x + 2, densCoords.y + 2, densCoords.w - 4, densCoords.h - 4);
                    ctx.clip();

                    ctx.font = "bold 11px Consolas, monospace";
                    ctx.fillStyle = densVal.trim() ? "#a7f3d0" : "#64748b";
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    ctx.fillText(densVal.trim() || "1.0", densCoords.x + 8, densCoords.y + 9);
                    ctx.restore();
                }

                const widths = this.getRowBoxWidths ? this.getRowBoxWidths() : { tagW: 60, minW: 46, maxW: 46, startW: 80, endW: 80, densW: 80, combinedTagRowW: 178 };
                const box1X = 24;
                const box1W = widths.tagW;
                const box2X = box1X + box1W + 6;
                const box2W = widths.minW;
                const box3X = box2X + box2W + 6;
                const box3W = widths.maxW;

                for (let i = 0; i < numRows; i++) {
                    const rowY = tagStartY + i * rowH;
                    const tagVal = String(this.properties.tags[i] !== undefined ? this.properties.tags[i] : "\\fscx");
                    const minVal = String(this.properties.mins[i] !== undefined ? this.properties.mins[i] : "150");
                    const maxVal = String(this.properties.maxs[i] !== undefined ? this.properties.maxs[i] : "250");

                    ctx.fillStyle = "#12161f";
                    ctx.strokeStyle = "#8b5cf6";
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(box1X, rowY, box1W, 18, 5);
                    else ctx.rect(box1X, rowY, box1W, 18);
                    ctx.fill();
                    ctx.stroke();

                    const isEditingTag = this._editing_cell && this._editing_cell.row === i && this._editing_cell.col === "tag";
                    if (!isEditingTag) {
                        ctx.save();
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(box1X + 2, rowY + 2, box1W - 4, 14, 3);
                        else ctx.rect(box1X + 2, rowY + 2, box1W - 4, 14);
                        ctx.clip();

                        ctx.font = "bold 11px Consolas, monospace";
                        ctx.fillStyle = tagVal.trim() ? "#a7f3d0" : "#64748b";
                        ctx.textAlign = "left";
                        ctx.textBaseline = "middle";
                        ctx.fillText(tagVal.trim() || "\\fscx", box1X + 8, rowY + 9);
                        ctx.restore();
                    }

                    ctx.fillStyle = "#12161f";
                    ctx.strokeStyle = (this._editing_cell && this._editing_cell.row === i && this._editing_cell.col === "min") ? "#8b5cf6" : "#475569";
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(box2X, rowY, box2W, 18, 5);
                    else ctx.rect(box2X, rowY, box2W, 18);
                    ctx.fill();
                    ctx.stroke();

                    const isEditingMin = this._editing_cell && this._editing_cell.row === i && this._editing_cell.col === "min";
                    if (!isEditingMin) {
                        ctx.save();
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(box2X + 2, rowY + 2, box2W - 4, 14, 3);
                        else ctx.rect(box2X + 2, rowY + 2, box2W - 4, 14);
                        ctx.clip();

                        ctx.font = "bold 11px Consolas, monospace";
                        ctx.fillStyle = minVal.trim() ? "#38bdf8" : "#64748b";
                        ctx.textAlign = "left";
                        ctx.textBaseline = "middle";
                        ctx.fillText(minVal.trim() || "150", box2X + 8, rowY + 9);
                        ctx.restore();
                    }

                    ctx.fillStyle = "#12161f";
                    ctx.strokeStyle = (this._editing_cell && this._editing_cell.row === i && this._editing_cell.col === "max") ? "#8b5cf6" : "#475569";
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(box3X, rowY, box3W, 18, 5);
                    else ctx.rect(box3X, rowY, box3W, 18);
                    ctx.fill();
                    ctx.stroke();

                    const isEditingMax = this._editing_cell && this._editing_cell.row === i && this._editing_cell.col === "max";
                    if (!isEditingMax) {
                        ctx.save();
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(box3X + 2, rowY + 2, box3W - 4, 14, 3);
                        else ctx.rect(box3X + 2, rowY + 2, box3W - 4, 14);
                        ctx.clip();

                        ctx.font = "bold 11px Consolas, monospace";
                        ctx.fillStyle = maxVal.trim() ? "#f472b6" : "#64748b";
                        ctx.textAlign = "left";
                        ctx.textBaseline = "middle";
                        ctx.fillText(maxVal.trim() || "250", box3X + 8, rowY + 9);
                        ctx.restore();
                    }
                }

                ctx.restore();
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos) {
                    const nodeW = this.size ? this.size[0] : 260;
                    const lx = local_pos[0];
                    const ly = local_pos[1];

                    if (ly < 0) {
                        const rawMode = this.properties.mode || "flashes";
                        const modeText = (window.PyxisI18n && window.PyxisI18n.translateMode) ? window.PyxisI18n.translateMode(rawMode) : rawMode;
                        const activeCanvas = canvas || LGraphCanvas.active_canvas;
                        const textW = (activeCanvas && activeCanvas.ctx ? activeCanvas.ctx.measureText(modeText).width : 50);
                        const modeBtnW = Math.max(55, textW + 14);
                        const modeBtnX = nodeW - modeBtnW - 8;
                        const modeBtnY = -25;
                        if (lx >= modeBtnX - 4 && lx <= modeBtnX + modeBtnW + 4 && ly >= modeBtnY - 2 && ly <= modeBtnY + 22) {
                            const modes = ["flashes", "pulses", "waves", "noise"];
                            let curIdx = modes.indexOf(this.properties.mode || "flashes");
                            if (curIdx < 0) curIdx = 0;
                            const nextIdx = (curIdx + 1) % modes.length;
                            this.properties.mode = modes[nextIdx];
                            if (this.properties.modo_oscilacion !== undefined) delete this.properties.modo_oscilacion;
                            if (this.properties.modo !== undefined) delete this.properties.modo;
                            if (this.computeSize) {
                                const sz = this.computeSize();
                                const keepH = (this.size && this.size[1] > 0) ? this.size[1] : sz[1];
                                this.size = [Math.max(this.size ? this.size[0] : 260, sz[0]), keepH];
                            }
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("glitter-mode-cycle");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        }
                    }

                    const cx = Math.floor(nodeW / 2);

                    if (lx >= cx - 26 && lx <= cx - 2 && ly >= 3 && ly <= 24) {
                        if (!Array.isArray(this.properties.tags)) this.properties.tags = ["\\fscx"];
                        if (!Array.isArray(this.properties.mins)) this.properties.mins = ["150"];
                        if (!Array.isArray(this.properties.maxs)) this.properties.maxs = ["250"];

                        this.properties.tags.push("\\fscx");
                        this.properties.mins.push("150");
                        this.properties.maxs.push("250");
                        this.syncSlotsWithRows();
                        if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("glitter-add-row");
                        return true;
                    }
                    if (lx >= cx + 2 && lx <= cx + 26 && ly >= 3 && ly <= 24) {
                        if (Array.isArray(this.properties.tags) && this.properties.tags.length > 1) {
                            this.properties.tags.pop();
                            this.properties.mins.pop();
                            this.properties.maxs.pop();
                            this.syncSlotsWithRows();
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("glitter-rem-row");
                            return true;
                        }
                    }

                    const stCoords = this.getBoxCoords(0, "start_time");
                    if (ly >= stCoords.y && ly <= stCoords.y + stCoords.h && lx >= stCoords.x && lx <= stCoords.x + stCoords.w) {
                        openGlitterInlineEditor(this, 0, "start_time");
                        return true;
                    }

                    const etCoords = this.getBoxCoords(0, "end_time");
                    if (ly >= etCoords.y && ly <= etCoords.y + etCoords.h && lx >= etCoords.x && lx <= etCoords.x + etCoords.w) {
                        openGlitterInlineEditor(this, 0, "end_time");
                        return true;
                    }

                    const densCoords = this.getBoxCoords(0, "density");
                    if (ly >= densCoords.y && ly <= densCoords.y + densCoords.h && lx >= densCoords.x && lx <= densCoords.x + densCoords.w) {
                        openGlitterInlineEditor(this, 0, "density");
                        return true;
                    }

                    const numRows = (this.properties.tags && Array.isArray(this.properties.tags)) ? this.properties.tags.length : 1;
                    const tagStartY = 101;
                    const rowH = 23;
                    const widths = this.getRowBoxWidths ? this.getRowBoxWidths() : { tagW: 60, minW: 46, maxW: 46 };
                    const box1X = 24;
                    const box1W = widths.tagW;
                    const box2X = box1X + box1W + 6;
                    const box2W = widths.minW;
                    const box3X = box2X + box2W + 6;
                    const box3W = widths.maxW;

                    for (let i = 0; i < numRows; i++) {
                        const rowY = tagStartY + i * rowH;
                        if (ly >= rowY && ly <= rowY + 18) {
                            if (lx >= box1X && lx <= box1X + box1W) {
                                openGlitterInlineEditor(this, i, "tag");
                                return true;
                            }
                            if (lx >= box2X && lx <= box2X + box2W) {
                                openGlitterInlineEditor(this, i, "min");
                                return true;
                            }
                            if (lx >= box3X && lx <= box3X + box3W) {
                                openGlitterInlineEditor(this, i, "max");
                                return true;
                            }
                        }
                    }
                }
                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            const oldComputeSize = node.computeSize;
            node.computeSize = function() {
                let max_out_w = 0;
                (this.outputs || []).forEach(out => {
                    if (out.name) {
                        const ow = getExactTextWidth(out.name, "10px sans-serif");
                        if (ow > max_out_w) max_out_w = ow;
                    }
                });

                const numRows = (this.properties.tags && Array.isArray(this.properties.tags)) ? this.properties.tags.length : 1;
                const widths = this.getRowBoxWidths ? this.getRowBoxWidths() : { tagW: 60, minW: 46, maxW: 46, startW: 80, endW: 80, densW: 80, combinedTagRowW: 178 };
                const boxes_end = 24 + widths.combinedTagRowW;
                const upper_end = 24 + widths.startW;
                const right_space = Math.max(45, max_out_w + 22);

                const rawMode = this.properties.mode || "flashes";
                const modeText = (window.PyxisI18n && window.PyxisI18n.translateMode) ? window.PyxisI18n.translateMode(rawMode) : rawMode;
                const modeW = Math.max(55, getExactTextWidth(modeText, "bold 10px monospace") + 16);
                const titleW = getExactTextWidth(String(this.title || "Glitter"), "bold 12px sans-serif");
                const req_w = Math.max(252, boxes_end + right_space, upper_end + right_space, titleW + modeW + 35);
                const req_h = Math.max(145, 101 + numRows * 23 + 24);

                return [req_w, req_h];
            };

            if (node.size && Array.isArray(node.size)) {
                node.size[0] = Math.max(node.size[0], 252);
            }
        }

        function setupAnimationNode(node) {
            if (!node.properties) node.properties = {};
            if (!node.properties.mode) node.properties.mode = "fbf";
            if (node.properties.frames === undefined) node.properties.frames = "";
            if (!node.properties.step_ms) node.properties.step_ms = "41.7";
            if (node.properties.start_time === undefined) node.properties.start_time = "";
            if (node.properties.end_time === undefined) node.properties.end_time = "";
            if (!node.properties.alpha_tag) node.properties.alpha_tag = "\\alpha";
            if (!node.properties.order) node.properties.order = "sequential";
            if (!node.properties.var_name) node.properties.var_name = "an";

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

            const resolveClientSideFrames = (rawStr) => {
                if (!rawStr || typeof rawStr !== "string") return [];
                const s = rawStr.trim();
                if (!s) return [];
                const tokens = s.includes(";") ? s.split(";") : (s.includes("|") ? s.split("|") : (s.includes(",") ? s.split(",") : [s]));
                const out = [];
                for (let tok of tokens) {
                    const t = tok.trim();
                    if (!t) continue;
                    if (/^m\s*[-?\d]/i.test(t)) {
                        out.push(t);
                    } else if (typeof getShapeDefinition === "function") {
                        const cleanKey = t.toLowerCase().replace(/^shape\./, "");
                        if (typeof SHAPES_LIB_GALLERY_DEFINITIONS !== "undefined" && SHAPES_LIB_GALLERY_DEFINITIONS[cleanKey]) {
                            const def = getShapeDefinition(cleanKey);
                            if (def && def.path) out.push(def.path);
                        }
                    }
                }
                return out;
            };

            const buildAnimationPreviewPayload = (selfNode, targetFrame) => {
                const curF = targetFrame !== undefined ? targetFrame : ((selfNode._pendingFrame !== undefined && selfNode._pendingFrame !== null) ? selfNode._pendingFrame : (selfNode._currentFrame || 1));
                const payload = Object.assign({}, selfNode.properties || {}, { preview_frame: curF });
                let upstreamKey = "";

                if (selfNode.graph && selfNode.inputs && selfNode.inputs[0] && selfNode.inputs[0].link != null) {
                    const linkObj = selfNode.graph.links ? selfNode.graph.links[selfNode.inputs[0].link] : null;
                    const originNode = linkObj && selfNode.graph.getNodeById ? selfNode.graph.getNodeById(linkObj.origin_id) : null;
                    if (originNode) {
                        const origType = String(originNode.type || originNode.title || "");
                        const origProps = originNode.properties || {};
                        if (origType.includes("IMG to Shape")) {
                            payload.upstream_img_to_shape = Object.assign({}, origProps);
                            upstreamKey = "img_to_shape:" + JSON.stringify(origProps);
                        } else if (origType.includes("Library")) {
                            if (!String(payload.frames || "").trim() && origProps.shape) {
                                payload.frames = String(origProps.shape);
                            }
                            upstreamKey = "lib:" + String(origProps.shape || "");
                        } else if (origType.includes("Text to Shape")) {
                            if (!String(payload.frames || "").trim() && origProps.text) {
                                payload.frames = String(origProps.text);
                            }
                            if (origProps.font_name) payload.font_name = origProps.font_name;
                            if (origProps.font_size) payload.font_size = origProps.font_size;
                            if (origProps.scale) payload.scale = origProps.scale;
                            upstreamKey = "txt_shape:" + JSON.stringify(origProps);
                        } else if (!String(payload.frames || "").trim()) {
                            const fallbackVal = origProps.value !== undefined ? origProps.value : (origProps.text !== undefined ? origProps.text : (origProps.shape !== undefined ? origProps.shape : ""));
                            if (fallbackVal) {
                                payload.frames = String(fallbackVal);
                                upstreamKey = "str:" + String(fallbackVal);
                            }
                        }
                    }
                }
                payload._upstreamKey = upstreamKey;
                return payload;
            };

            const mapPlaybackStepToFrameIndex = (stepIdxZeroBased, numFrames, orderMode) => {
                if (numFrames <= 1) return 1;
                const ord = String(orderMode || "sequential").trim().toLowerCase();
                if (ord === "reverse") {
                    return numFrames - (stepIdxZeroBased % numFrames);
                }
                if (ord === "pingpong") {
                    const cycleLen = 2 * numFrames - 2;
                    if (cycleLen <= 0) return 1;
                    const pos = stepIdxZeroBased % cycleLen;
                    const idx0 = pos < numFrames ? pos : (cycleLen - pos);
                    return idx0 + 1;
                }
                if (ord === "random") {
                    const x = Math.sin(stepIdxZeroBased * 12.9898 + 78.233) * 43758.5453;
                    const frac = x - Math.floor(x);
                    return Math.floor(frac * numFrames) + 1;
                }
                return (stepIdxZeroBased % numFrames) + 1;
            };

            const hasPlayableAnimation = (selfNode) => {
                const totF = selfNode._totalFrames || 0;
                const framesArr = selfNode._animFrames;
                return Boolean(totF > 1 && Array.isArray(framesArr) && framesArr.length > 1);
            };

            const stopPlaybackLoop = (selfNode) => {
                selfNode._isPlaying = false;
                if (selfNode._playRafId) {
                    cancelAnimationFrame(selfNode._playRafId);
                    selfNode._playRafId = null;
                }
            };

            const startPlaybackLoop = (selfNode) => {
                if (selfNode._playRafId) {
                    cancelAnimationFrame(selfNode._playRafId);
                    selfNode._playRafId = null;
                }
                const tick = (now) => {
                    if (!selfNode._isPlaying || !selfNode.graph || !hasPlayableAnimation(selfNode)) {
                        stopPlaybackLoop(selfNode);
                        if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);
                        return;
                    }
                    const totF = selfNode._totalFrames || 1;
                    const rawStep = parseFloat(selfNode.properties && selfNode.properties.step_ms);
                    const stepMs = (!isNaN(rawStep) && rawStep >= 15) ? rawStep : 41.7;
                    if (!selfNode._lastPlayTick) selfNode._lastPlayTick = now;
                    if (now - selfNode._lastPlayTick >= stepMs) {
                        selfNode._lastPlayTick = now;
                        selfNode._playStepIdx = ((typeof selfNode._playStepIdx === "number") ? selfNode._playStepIdx : 0) + 1;
                        const nextFrame = mapPlaybackStepToFrameIndex(
                            selfNode._playStepIdx,
                            totF,
                            selfNode.properties ? selfNode.properties.order : "sequential"
                        );
                        selfNode._currentFrame = nextFrame;
                        if (Array.isArray(selfNode._animFrames) && selfNode._animFrames.length >= nextFrame) {
                            selfNode._lastTracedShape = selfNode._animFrames[nextFrame - 1] || "";
                        }
                        if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, false);
                        const cObj = (typeof LGraphCanvas !== "undefined" && LGraphCanvas.active_canvas) || window.canvas || window.graphcanvas;
                        if (cObj && typeof cObj.draw === "function") {
                            cObj.draw(true, false);
                        }
                    }
                    selfNode._playRafId = requestAnimationFrame(tick);
                };
                selfNode._playRafId = requestAnimationFrame(tick);
            };

            const scheduleAnimationPreview = (selfNode, targetFrame) => {
                const payload = buildAnimationPreviewPayload(selfNode, targetFrame);
                const curF = payload.preview_frame || 1;
                selfNode._currentFrame = curF;

                const rawFramesStr = String(payload.frames || "").trim();
                const hasUpstreamImg = Boolean(payload.upstream_img_to_shape && String(payload.upstream_img_to_shape.image_path || "").trim());
                selfNode._previewSourceKey = rawFramesStr + "|" + (payload._upstreamKey || "");

                if (!rawFramesStr && !hasUpstreamImg) {
                    selfNode._animFrames = [];
                    selfNode._lastTracedShape = "";
                    selfNode._totalFrames = 1;
                    selfNode._currentFrame = 1;
                    stopPlaybackLoop(selfNode);
                    if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);
                    return;
                }

                // Instant client-side resolution if frames are known presets or raw ASSdraw paths
                if (!hasUpstreamImg && rawFramesStr) {
                    const localFrames = resolveClientSideFrames(rawFramesStr);
                    if (localFrames.length > 0) {
                        selfNode._animFrames = localFrames;
                        selfNode._totalFrames = localFrames.length;
                        const clampedF = Math.max(1, Math.min(curF, localFrames.length));
                        selfNode._currentFrame = clampedF;
                        selfNode._lastTracedShape = localFrames[clampedF - 1] || "";
                        if (localFrames.length <= 1) {
                            stopPlaybackLoop(selfNode);
                        }
                    }
                }

                if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.preview_animation_api !== "function") {
                    if (!hasPlayableAnimation(selfNode)) {
                        stopPlaybackLoop(selfNode);
                    }
                    if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);
                    return;
                }

                if (selfNode._isTracing) {
                    selfNode._pendingFrame = curF;
                    selfNode._pendingRetrace = true;
                    return;
                }

                selfNode._isTracing = true;
                selfNode._pendingFrame = null;
                selfNode._pendingRetrace = false;

                window.pywebview.api.preview_animation_api(payload).then(res => {
                    selfNode._isTracing = false;
                    if (res) {
                        if (Array.isArray(res.frames)) {
                            selfNode._animFrames = res.frames;
                        }
                        if (res.total_frames !== undefined) {
                            const prevTot = selfNode._totalFrames;
                            selfNode._totalFrames = Math.max(1, Number(res.total_frames) || 1);
                            if (selfNode.properties) selfNode.properties._total_frames = selfNode._totalFrames;
                            if (prevTot !== selfNode._totalFrames && window.__pyxis_schedule_save) {
                                window.__pyxis_schedule_save(50);
                            }
                        }
                        if (res.frame_index !== undefined) {
                            selfNode._currentFrame = Math.max(1, Math.min(Number(res.frame_index) || 1, selfNode._totalFrames || 1));
                            if (selfNode.properties) selfNode.properties._current_frame = selfNode._currentFrame;
                        }
                        if (res.shape !== undefined) {
                            selfNode._lastTracedShape = res.shape;
                        } else if (selfNode._animFrames && selfNode._animFrames.length > 0) {
                            selfNode._lastTracedShape = selfNode._animFrames[(selfNode._currentFrame || 1) - 1] || "";
                        }
                    }
                    if (!hasPlayableAnimation(selfNode)) {
                        stopPlaybackLoop(selfNode);
                    } else if (selfNode._startPlayWhenReady) {
                        selfNode._startPlayWhenReady = false;
                        selfNode._isPlaying = true;
                        selfNode._lastPlayTick = performance.now();
                        if (typeof selfNode._playStepIdx !== "number") {
                            selfNode._playStepIdx = Math.max(0, (selfNode._currentFrame || 1) - 1);
                        }
                        startPlaybackLoop(selfNode);
                    }
                    selfNode._startPlayWhenReady = false;
                    if (selfNode.computeSize) {
                        const sz = selfNode.computeSize();
                        if (selfNode.size) {
                            selfNode.size[0] = Math.max(selfNode.size[0], sz[0]);
                            selfNode.size[1] = Math.max(selfNode.size[1], sz[1]);
                        }
                    }
                    if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);

                    if (selfNode._pendingRetrace || (selfNode._pendingFrame !== null && selfNode._pendingFrame !== selfNode._currentFrame)) {
                        const nextF = selfNode._pendingFrame !== null ? selfNode._pendingFrame : selfNode._currentFrame;
                        selfNode._pendingFrame = null;
                        selfNode._pendingRetrace = false;
                        scheduleAnimationPreview(selfNode, nextF);
                    }
                }).catch(() => {
                    selfNode._isTracing = false;
                    selfNode._startPlayWhenReady = false;
                    if (!hasPlayableAnimation(selfNode)) {
                        stopPlaybackLoop(selfNode);
                    }
                    if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);
                });
            };

            const selectFrameIndex = (selfNode, targetFrame) => {
                const totF = selfNode._totalFrames || 1;
                const clamped = Math.max(1, Math.min(targetFrame, totF));
                selfNode._currentFrame = clamped;
                if (selfNode.properties) selfNode.properties._current_frame = clamped;
                if (Array.isArray(selfNode._animFrames) && selfNode._animFrames.length >= clamped) {
                    selfNode._lastTracedShape = selfNode._animFrames[clamped - 1] || "";
                    if (selfNode.setDirtyCanvas) selfNode.setDirtyCanvas(true, true);
                } else {
                    scheduleAnimationPreview(selfNode, clamped);
                }
            };

            const oldPropertyChanged = node.onPropertyChanged;
            node.onPropertyChanged = function(property, value, prev_value) {
                if (oldPropertyChanged) oldPropertyChanged.call(this, property, value, prev_value);
                if (property === "_total_frames" || property === "_current_frame") return;
                if (property === "frames" && value !== prev_value) {
                    this._currentFrame = 1;
                    this._playStepIdx = 0;
                    if (typeof resetImgPreviewTransform === "function") {
                        resetImgPreviewTransform(this, false);
                    }
                    scheduleAnimationPreview(this, 1);
                } else if (property === "mode") {
                    updateNodeModeInputs(this);
                    if (this.computeSize) {
                        const sz = this.computeSize();
                        this.size[0] = Math.max(this.size[0], sz[0]);
                        this.size[1] = Math.max(this.size[1], sz[1]);
                    }
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                }
            };

            const oldConnectionsChange = node.onConnectionsChange;
            node.onConnectionsChange = function(type, slot, connected, link_info, input_info) {
                if (oldConnectionsChange) oldConnectionsChange.call(this, type, slot, connected, link_info, input_info);
                if (slot === 0) {
                    this._currentFrame = 1;
                    this._playStepIdx = 0;
                    scheduleAnimationPreview(this, 1);
                }
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
                        stopPlaybackLoop(this);
                        const curF = this._currentFrame || 1;
                        const totF = this._totalFrames || 1;
                        if (totF > 1) {
                            const newFrame = curF > 1 ? (curF - 1) : totF;
                            selectFrameIndex(this, newFrame);
                        }
                        return true;
                    }

                    if (target === "next_frame") {
                        stopPlaybackLoop(this);
                        const curF = this._currentFrame || 1;
                        const totF = this._totalFrames || 1;
                        if (totF > 1) {
                            const newFrame = curF < totF ? (curF + 1) : 1;
                            selectFrameIndex(this, newFrame);
                        }
                        return true;
                    }

                    if (target === "scrub_track") {
                        stopPlaybackLoop(this);
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
                                selectFrameIndex(selfNode, newFrame);
                            }
                        };

                        updateFrameFromEvent(e);

                        const onWindowMove = (eMove) => { updateFrameFromEvent(eMove); };
                        const onWindowUp = () => {
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
                        if (this._isPlaying) {
                            stopPlaybackLoop(this);
                            this._startPlayWhenReady = false;
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            return true;
                        }

                        const payloadCheck = buildAnimationPreviewPayload(this, this._currentFrame || 1);
                        const curKey = String(payloadCheck.frames || "").trim() + "|" + (payloadCheck._upstreamKey || "");
                        if (this._previewSourceKey !== curKey) {
                            scheduleAnimationPreview(this, this._currentFrame || 1);
                        }

                        if (hasPlayableAnimation(this)) {
                            this._isPlaying = true;
                            this._lastPlayTick = performance.now();
                            if (typeof this._playStepIdx !== "number") {
                                this._playStepIdx = Math.max(0, (this._currentFrame || 1) - 1);
                            }
                            startPlaybackLoop(this);
                        } else if (this._isTracing && curKey !== "|") {
                            this._startPlayWhenReady = true;
                        } else {
                            stopPlaybackLoop(this);
                            this._missingFramesFlash = true;
                            setTimeout(() => {
                                this._missingFramesFlash = false;
                                if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
                            }, 500);
                        }
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        return true;
                    }

                    if (target === "refresh_btn") {
                        scheduleAnimationPreview(this, this._currentFrame || 1);
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

            node.onDblClick = function(e, local_pos) {
                if (!local_pos) return false;
                const [lx, ly] = getSafeLocalPos(this, local_pos);
                const layout = getImgNodePreviewLayout(this);
                const target = hitTestImgPreview(layout, lx, ly);
                if (target === "card") {
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
                        if (k === "mode" || k === "order" || k === "alpha_tag" || k === "var_name" || k.startsWith("_")) continue;
                        let val = String(this.properties[k] || "");
                        if (k === "frames") {
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
                (this.outputs || []).forEach(out => {
                    if (out.name) {
                        const ow = getExactTextWidth(out.name, "10px sans-serif");
                        if (ow > max_out_w) max_out_w = ow;
                    }
                });

                const num_in = this.inputs ? this.inputs.length : 5;
                const left_box_w = Math.max(70, max_in_text_w + 16);
                const left_col_end = 22 + left_box_w;
                const card_w = 150;
                const right_col_w = max_out_w > 0 ? (max_out_w + 38) : 20;
                const side_margin = 20;

                const titleW = getExactTextWidth(String(this.title || "Animation"), "bold 12px sans-serif");
                const base_w = Math.max(380, left_col_end + side_margin + card_w + side_margin + right_col_w, 25 + titleW + 20 + modeW + 14);
                const req_w = Math.round(base_w * 1.1);
                const req_h = Math.max(245, 11 + num_in * 23 + 32);

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
                const sz = this.computeSize();
                if (info && info.size && Array.isArray(info.size)) {
                    const confW = Math.max(info.size[0], sz[0]);
                    const confH = Math.max(info.size[1], sz[1]);
                    this._customSize = [confW, confH];
                    this.size = [confW, confH];
                } else {
                    this.size[0] = Math.max(this.size[0] || 0, sz[0]);
                    this.size[1] = Math.max(this.size[1] || 0, sz[1]);
                }
                scheduleAnimationPreview(this);
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                // Auto-resolve if source changed or not yet resolved (including when cleared to empty)
                const payloadCheck = buildAnimationPreviewPayload(this, this._currentFrame || 1);
                const curKey = String(payloadCheck.frames || "").trim() + "|" + (payloadCheck._upstreamKey || "");
                if (!this._isTracing && this._previewSourceKey !== curKey) {
                    scheduleAnimationPreview(this, this._currentFrame || 1);
                }

                if (this._isPlaying && !hasPlayableAnimation(this)) {
                    stopPlaybackLoop(this);
                }

                const isTracing = Boolean(this._isTracing);
                const totF = this._totalFrames || 1;

                // Handle live playback timer
                if (this._isPlaying && totF > 1) {
                    const now = performance.now();
                    const rawStep = parseFloat(this.properties && this.properties.step_ms);
                    const stepMs = (!isNaN(rawStep) && rawStep >= 15) ? rawStep : 41.7;
                    if (!this._lastPlayTick) this._lastPlayTick = now;
                    if (now - this._lastPlayTick >= stepMs) {
                        this._lastPlayTick = now;
                        this._playStepIdx = ((typeof this._playStepIdx === "number") ? this._playStepIdx : 0) + 1;
                        const nextFrame = mapPlaybackStepToFrameIndex(
                            this._playStepIdx,
                            totF,
                            this.properties ? this.properties.order : "sequential"
                        );
                        this._currentFrame = nextFrame;
                        if (Array.isArray(this._animFrames) && this._animFrames.length >= nextFrame) {
                            this._lastTracedShape = this._animFrames[nextFrame - 1] || "";
                        }
                    }
                    if (!this._playRafId) {
                        startPlaybackLoop(this);
                    }
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
                } else if (isTracing) {
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, false);
                }

                const layout = getImgNodePreviewLayout(this);
                const { cardX, cardY, cardW, cardH, cardCenterX, cardCenterY, barY, btnH, btnX, btnW, refreshX, refreshW } = layout;
                const curF = this._currentFrame || 1;

                if (layout.hasTopBar) {
                    ctx.save();
                    const topBarY = layout.topBarY;
                    const topBarH = layout.topBarH;
                    const stepBtnW = layout.stepBtnW;
                    const trackX = layout.trackX;
                    const trackW = layout.trackW;

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
                    ctx.font = "bold 10px monospace";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("Frame " + curF + " / " + totF, trackX + trackW / 2, topBarY + 9);
                    ctx.restore();
                }

                // Bottom Bar: Play / Pause toggle button + Refresh button
                const isViewHover = this._hoverTarget === "view_btn";
                const isViewPressed = this._pressedTarget === "view_btn";
                const viewYOffset = isViewPressed ? 1 : 0;
                const isPlaying = Boolean(this._isPlaying);

                ctx.save();
                ctx.font = "bold 10px monospace";
                ctx.fillStyle = isViewPressed
                    ? "rgba(91, 33, 182, 0.75)"
                    : (isPlaying ? "rgba(16, 185, 129, 0.25)" : (isViewHover ? "rgba(139, 92, 246, 0.32)" : "#12161f"));
                ctx.strokeStyle = isPlaying ? "#34d399" : (isViewHover ? "#c084fc" : "#8b5cf6");
                ctx.lineWidth = isViewHover ? 1.6 : 1.4;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnX, barY + viewYOffset, btnW, btnH, 5);
                else ctx.rect(btnX, barY + viewYOffset, btnW, btnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = isPlaying ? "#6ee7b7" : (isViewHover ? "#ffffff" : "#a7f3d0");
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                const isEs = window.PyxisI18n && PyxisI18n.currentLang === "es";
                const playLabel = isPlaying ? (isEs ? "⏸ Pausa" : "⏸ Pause") : (isEs ? "▶ Reproducir" : "▶ Play");
                ctx.fillText(playLabel, btnX + btnW / 2, barY + btnH / 2 + 1 + viewYOffset);

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
                if (this._missingFramesFlash) {
                    cardStroke = "#f43f5e";
                } else if (isPlaying) {
                    cardStroke = "rgba(52, 211, 153, 0.9)";
                } else if (isCardHover) {
                    cardStroke = "rgba(52, 211, 153, 0.85)";
                } else if (isTracing) {
                    cardStroke = "rgba(251, 191, 36, 0.9)";
                }

                ctx.save();
                ctx.fillStyle = "rgba(18, 22, 31, 0.95)";
                ctx.strokeStyle = cardStroke;
                ctx.lineWidth = (isCardHover || isPlaying || this._missingFramesFlash) ? 2.0 : 1.6;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(cardX, cardY, cardW, cardH, 10);
                else ctx.rect(cardX, cardY, cardW, cardH);
                ctx.fill();
                ctx.stroke();

                const cardZoom = (typeof this._cardZoom === "number" && !isNaN(this._cardZoom) && this._cardZoom > 0) ? this._cardZoom : 1.0;
                const cardPanX = (typeof this._cardPanX === "number" && !isNaN(this._cardPanX)) ? this._cardPanX : 0;
                const cardPanY = (typeof this._cardPanY === "number" && !isNaN(this._cardPanY)) ? this._cardPanY : 0;

                const activeShape = (Array.isArray(this._animFrames) && this._animFrames.length >= curF)
                    ? this._animFrames[curF - 1]
                    : (this._lastTracedShape || "");

                if (activeShape && typeof activeShape === "string" && activeShape.trim().length > 0) {
                    if (!this._cachedShapePath || this._cachedShapeKey !== activeShape) {
                        const svgD = assPathToSvg(activeShape);
                        this._cachedShapePath = new Path2D(svgD);
                        this._cachedShapeKey = activeShape;
                    }

                    const bbox = getAssPathBBox(activeShape);
                    if (bbox && bbox.w > 0 && bbox.h > 0) {
                        const availW = Math.max(10, cardW - 24);
                        const availH = Math.max(10, cardH - 24);
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
                        ctx.lineWidth = 1.6 / Math.max(0.1, effScale);
                        ctx.lineJoin = "round";
                        ctx.lineCap = "round";
                        ctx.fill(this._cachedShapePath);
                        ctx.stroke(this._cachedShapePath);
                        ctx.restore();
                    }
                } else if (!isTracing) {
                    ctx.save();
                    ctx.fillStyle = "rgba(167, 243, 208, 0.75)";
                    ctx.font = "bold 11px monospace";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("ANIMATION", cardCenterX, cardCenterY - 10);
                    ctx.fillStyle = "rgba(148, 163, 184, 0.85)";
                    ctx.font = "10px sans-serif";
                    ctx.fillText(isEs ? "Secuencia Vectorial" : "Vector Sequence", cardCenterX, cardCenterY + 10);
                    ctx.restore();
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
                    ctx.fillText(isEs ? "Cargando Frames..." : "Loading Frames...", cardCenterX, cardCenterY + 18);
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
            scheduleAnimationPreview(node);
        }

        window.setupCondicionadorNode = setupConditionerNode;
        window.setupConditionerNode = setupConditionerNode;
        window.setupPolaresNode = setupPolarToCartesianNode;
        window.setupPolarToCartesianNode = setupPolarToCartesianNode;
        window.setupAnimationNode = setupAnimationNode;


