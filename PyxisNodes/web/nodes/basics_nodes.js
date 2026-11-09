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
 * @file basics_nodes.js
 * @description UI setups and inline editors for Basics category nodes.
 * @module PyxisBasicsNodes
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function containsAssdrawDrawing(val) {
            if (!val || typeof val !== "string") return false;
            const str = val.trim();
            if (/^m\s+[-?\d]/i.test(str) || /^m\s*[-?\d]/i.test(str) || str.startsWith("m ") || str.startsWith("m-") || str.startsWith("m0")) {
                return true;
            }
            if (/\bm\s+[-?\d]/i.test(str) && (/\b[lbcs]\s+[-?\d]/i.test(str) || str.includes(" b ") || str.includes(" l ") || str.includes(" c ") || str.includes(" s "))) {
                return true;
            }
            if (str.includes("m ") && (str.includes(" l ") || str.includes(" b ") || str.includes(" c ") || str.includes(" s "))) {
                return true;
            }
            return false;
        }
        window.containsAssdrawDrawing = containsAssdrawDrawing;

        function wrapTextToPixelWidth(text, maxPixelWidth, font) {
            if (!text || typeof text !== "string") return [""];
            const maxW = Math.max(20, maxPixelWidth || 300);
            const fontStr = font || "bold 12px Consolas, monospace";

            const rawLines = text.split("\n");
            const result = [];
            const maxResultLines = 200; // Cap to prevent massive arrays for huge text

            for (let i = 0; i < rawLines.length; i++) {
                if (result.length >= maxResultLines) {
                    result.push("...");
                    break;
                }
                const line = rawLines[i];
                if (!line) {
                    result.push("");
                    continue;
                }
                if (getExactTextWidth(line, fontStr) <= maxW) {
                    result.push(line);
                    continue;
                }
                const tokens = line.split(" ");
                let current = "";
                for (let j = 0; j < tokens.length; j++) {
                    if (result.length >= maxResultLines) {
                        current = "";
                        result.push("...");
                        break;
                    }
                    const token = tokens[j];
                    if (token === "" && j > 0) {
                        const testSpace = current + " ";
                        if (getExactTextWidth(testSpace, fontStr) <= maxW) {
                            current = testSpace;
                        } else {
                            result.push(current);
                            current = "";
                        }
                        continue;
                    }
                    const testLine = current ? (current + " " + token) : token;
                    if (getExactTextWidth(testLine, fontStr) <= maxW) {
                        current = testLine;
                    } else {
                        if (current) {
                            result.push(current);
                            current = "";
                            if (result.length >= maxResultLines) {
                                result.push("...");
                                break;
                            }
                        }
                        if (getExactTextWidth(token, fontStr) <= maxW) {
                            current = token;
                        } else {
                            // Character-level fallback matching CSS overflow-wrap / word-break: break-word
                            let sub = "";
                            for (let c = 0; c < token.length; c++) {
                                if (result.length >= maxResultLines) {
                                    sub = "";
                                    result.push("...");
                                    break;
                                }
                                const ch = token[c];
                                const nextSub = sub + ch;
                                if (sub && getExactTextWidth(nextSub, fontStr) > maxW) {
                                    result.push(sub);
                                    sub = ch;
                                } else {
                                    sub = nextSub;
                                }
                            }
                            current = sub;
                        }
                    }
                }
                if (current) {
                    result.push(current);
                }
            }

            return result.length > 0 ? result : [""];
        }
        window.wrapTextToPixelWidth = wrapTextToPixelWidth;

        function getRandomLivePreview(node) {
            const modo = String(node.properties.mode || "R");
            const modoKey = modo.toLowerCase();
            const min = node.properties.min !== undefined && String(node.properties.min).trim() !== "" ? node.properties.min : "0";
            const max = node.properties.max !== undefined && String(node.properties.max).trim() !== "" ? node.properties.max : "100";
            const step = node.properties.step !== undefined && String(node.properties.step).trim() !== "" ? node.properties.step : "1";
            const options = node.properties.options !== undefined && String(node.properties.options).trim() !== "" ? node.properties.options : "A, B, C";
            const counter = node.properties.counter !== undefined && String(node.properties.counter).trim() !== "" ? node.properties.counter : "i";

            if (modoKey === "re") {
                return `Re(${options})`;
            } else if (modoKey === "rfake") {
                return `Rfake(${min}, ${max}, ${counter})`;
            } else if (modoKey === "rcolor" || modoKey === "rcol") {
                return `Rcolor(${min}, ${max})`;
            } else if (modoKey === "rbool") {
                return `Rbool(${min}%)`;
            } else if (modoKey === "r2d") {
                return `R2d(${min}, ${max})`;
            } else if (modoKey === "rstep") {
                return `Rstep(${min}, ${max}, ${step})`;
            } else {
                if (step !== "" && step !== "1" && step !== 1) {
                    return `${modo}(${min}, ${max}, ${step})`;
                }
                return `${modo}(${min}, ${max})`;
            }
        }

        function setupRandomMasterNode(node) {
            if (!node.properties) node.properties = {};
            if (!node.properties.mode) node.properties.mode = "R";
            if (node.properties.modo !== undefined) delete node.properties.modo;
            if (node.properties.min === undefined) node.properties.min = "0";
            if (node.properties.max === undefined) node.properties.max = "100";
            if (node.properties.step === undefined) node.properties.step = "";
            if (node.properties.options === undefined) node.properties.options = "A, B, C";
            if (node.properties.counter === undefined) node.properties.counter = "";
            if (node.properties.total === undefined) node.properties.total = "1";
            if (node.properties.iterator === undefined) node.properties.iterator = "";
            node.widgets_up = true;

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const modo = props.mode || "R";
                let reqInputs = ["Min", "Max", "Step", "Total (N)", "Iterator"];
                if (modo === "Re") {
                    reqInputs = ["Options", "Total (N)", "Iterator"];
                } else if (modo === "Rfake") {
                    reqInputs = ["Min", "Max", "Counter (i/j)", "Total (N)", "Iterator"];
                } else if (modo === "Rcolor" || modo === "Rcol") {
                    reqInputs = ["Color Min", "Color Max", "Total (N)", "Iterator"];
                } else if (modo === "Rbool") {
                    reqInputs = ["Probability (%)", "Total (N)", "Iterator"];
                } else if (modo === "Rstep") {
                    reqInputs = ["Min", "Max", "Step", "Total (N)", "Iterator"];
                }
                
                let base_w = 210;
                let text_req_w = 0;
                for (const p in props) {
                    if (p === "mode" || p === "modo") continue;
                    const val = String(props[p] || "");
                    if (val.length > 0) {
                        const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                        if (tw > text_req_w) text_req_w = tw;
                    }
                }
                const right_space = getNodeRightReserve(this);
                const boxW = Math.max(65, Math.ceil(text_req_w + 28));
                return [Math.max(base_w, 22 + boxW + right_space), 11 + reqInputs.length * 23 + 58];
            };

            node.updateTagInputs = updateRandomInputs;

            function updateRandomInputs() {
                const modo = node.properties.mode || "R";
                let reqInputs = ["Min", "Max", "Step", "Total (N)", "Iterator"];
                if (modo === "Re") {
                    reqInputs = ["Options", "Total (N)", "Iterator"];
                } else if (modo === "Rfake") {
                    reqInputs = ["Min", "Max", "Counter (i/j)", "Total (N)", "Iterator"];
                } else if (modo === "Rcolor" || modo === "Rcol") {
                    reqInputs = ["Color Min", "Color Max", "Total (N)", "Iterator"];
                    if (node.properties.min === "0" || node.properties.min === undefined) {
                        node.properties.min = "#FFFFFF";
                    }
                    if (node.properties.max === "100" || node.properties.max === undefined) {
                        node.properties.max = "#000000";
                    }
                } else if (modo === "Rbool") {
                    reqInputs = ["Probability (%)", "Total (N)", "Iterator"];
                } else if (modo === "Rstep") {
                    reqInputs = ["Min", "Max", "Step", "Total (N)", "Iterator"];
                }

                if (modo !== "Rcolor" && modo !== "Rcol") {
                    if (node.properties.min === "#FFFFFF" || node.properties.min === "&HFFFFFF&") {
                        node.properties.min = "0";
                    }
                    if (node.properties.max === "#000000" || node.properties.max === "&H000000&") {
                        node.properties.max = "100";
                    }
                }

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
                    node.addOutput("Data", "data");
                }
                if (node.outputs.length < 2) {
                    node.addOutput("Batch / List", "data");
                }
                while (node.outputs && node.outputs.length > 2) {
                    node.removeOutput(node.outputs.length - 1);
                }

                node.widgets = [];

                reqInputs.forEach((paramName, idx) => {
                    let propKey = "min";
                    if (paramName === "Max" || paramName === "Color Max") propKey = "max";
                    else if (paramName === "Step") propKey = "step";
                    else if (paramName === "Options") propKey = "options";
                    else if (paramName.includes("Contador") || paramName.includes("Counter")) propKey = "counter";
                    else if (paramName === "Color Min" || paramName.includes("Probabilidad") || paramName.includes("Probability")) propKey = "min";
                    else if (paramName === "Total (N)" || paramName === "Total") propKey = "total";
                    else if (paramName === "Iterator" || paramName.includes("Iterator") || paramName === "Iterador") propKey = "iterator";

                    if (node.properties[propKey] === undefined) {
                        if (propKey === "min") {
                            node.properties[propKey] = (modo === "Rcolor" || modo === "Rcol") ? "#FFFFFF" : (modo === "Rbool" ? "50" : "0");
                        } else if (propKey === "max") {
                            node.properties[propKey] = (modo === "Rcolor" || modo === "Rcol") ? "#000000" : "100";
                        } else if (propKey === "step") {
                            node.properties[propKey] = (modo === "Rstep") ? "45" : "";
                        } else if (propKey === "total") {
                            node.properties[propKey] = "1";
                        } else if (propKey === "iterator") {
                            node.properties[propKey] = "";
                        } else {
                            node.properties[propKey] = "";
                        }
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
                    node.size = [185, 11 + reqInputs.length * 23 + 58];
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos && local_pos[1] < 0) {
                    const modeInfo = getTitleModeInfo(this);
                    if (modeInfo) {
                        const btnText = modeInfo.currentShort;
                        const textW = (canvas && canvas.ctx) ? canvas.ctx.measureText(btnText).width : 40;
                        const btnW = Math.max(50, textW + 14);
                        const btnX = this.size[0] - btnW - 8;
                        if (local_pos[0] >= btnX - 4 && local_pos[0] <= btnX + btnW + 6) {
                            const nextIdx = (modeInfo.currentIdx + 1) % modeInfo.modeList.length;
                            this.properties.mode = modeInfo.modeList[nextIdx].full;
                            if (this.properties.modo !== undefined) delete this.properties.modo;
                            updateRandomInputs();
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        }
                    }
                }
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
                    const btnW = Math.max(50, textW + 14);
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
                        inp.pos = [10, 11 + idx * 23 + 9];
                    });
                }

                const modoKey = String(this.properties.mode || "R").toLowerCase();
                const modeDef = RANDOM_DEFINITIONS[modoKey] || { desc: "aleatorio básico (entero/flotante)", preview: "R(min, max)" };

                ctx.save();
                ctx.font = "italic 11px sans-serif";
                ctx.fillStyle = "#94a3b8";
                ctx.textAlign = "left";
                
                let desc = (window.PyxisI18n && window.PyxisI18n.getRandomDesc) ? window.PyxisI18n.getRandomDesc(modoKey) : modeDef.desc;
                if (!desc) desc = modeDef.desc;
                ctx.fillText(desc, 12, this.size[1] - 44);

                ctx.font = "bold 12px monospace";
                ctx.fillStyle = "#a7f3d0";
                
                let previewStr = getRandomLivePreview(this);
                const maxW = this.size[0] - 24;
                if (ctx.measureText(previewStr).width > maxW) {
                    let truncated = previewStr;
                    while (truncated.length > 0 && ctx.measureText(truncated + "...").width > maxW) {
                        truncated = truncated.slice(0, -1);
                    }
                    previewStr = truncated + "...";
                }
                
                ctx.fillText(previewStr, 12, this.size[1] - 28);
                ctx.restore();
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateRandomInputs();
            };

            updateRandomInputs();
        }


        function setupConcatenateNode(node) {
            node.properties = node.properties || { expandable: true, mode: "basic", separator: "nil" };
            if (!node.properties.mode) node.properties.mode = "basic";
            if (!node.properties.separator) node.properties.separator = "nil";
            if (node.properties.separador !== undefined) delete node.properties.separador;
            node.widgets_up = true;

            const CONCATENATE_MODES = window.CONCATENATE_MODES || [
                { full: "basic", short: "BASIC" },
                { full: "zip", short: "ZIP" },
                { full: "merge", short: "MERGE" }
            ];

            const CONCATENATE_SEPARATORS = window.CONCATENATE_SEPARATORS || [
                { full: "nil", short: "NIL" },
                { full: "space", short: "SPACE" },
                { full: "comma", short: "," },
                { full: "semicolon", short: ";" },
                { full: "newline", short: "ENTER" }
            ];

            node.updateConcatenarInputs = function(targetCount) {
                let count = targetCount;
                if (count === undefined) {
                    count = 0;
                    if (this.inputs) {
                        for (let i = 0; i < this.inputs.length; i++) {
                            if (this.inputs[i].name && this.inputs[i].name.startsWith("In")) count++;
                        }
                    }
                    if (count < 2) count = 2;
                }

                if (!this.inputs) this.inputs = [];
                for (let i = 1; i <= count; i++) {
                    const name = "In" + i;
                    const exists = this.inputs.some(inp => inp.name === name);
                    if (!exists) {
                        this.addInput(name, "data");
                    }
                }

                for (let i = this.inputs.length - 1; i >= 0; i--) {
                    const inp = this.inputs[i];
                    if (inp.name && inp.name.startsWith("In")) {
                        const num = parseInt(inp.name.substring(2));
                        if (num > count) {
                            this.removeInput(i);
                        }
                    }
                }

                if (!this.outputs || this.outputs.length === 0) {
                    this.addOutput("String", "data");
                }

                this.widgets = [];
                for (let i = 1; i <= count; i++) {
                    const prop = "In" + i;
                    const name = "In" + i;
                    if (this.properties[prop] === undefined) {
                        this.properties[prop] = "";
                    }
                    const curVal = String(this.properties[prop] || "");
                    const w = this.addWidget("text", name, curVal, value => {
                        const cleanVal = String(value || "").replace(/[\r\n]+/g, " ");
                        this.properties[prop] = cleanVal;
                        if (this.computeSize) this.size = this.computeSize();
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    });
                    w.property = prop;
                    const widgetY = 30 + (i - 1) * 23;
                    const dotY = widgetY + 9;
                    w.y = widgetY;
                    w.last_y = widgetY;

                    setupSingleLineTextWidget(this, w, name, prop);

                    if (this.inputs[i - 1]) {
                        this.inputs[i - 1].label = " ";
                        this.inputs[i - 1].pos = [10, dotY];
                    }
                }

                if (this.computeSize) {
                    this.size = this.computeSize();
                }
            };

            node.computeSize = function() {
                let base_w = 205;
                let text_req_w = 0;
                const count = this.inputs ? this.inputs.length : 2;
                for (let i = 1; i <= count; i++) {
                    const val = String(this.properties["In" + i] || "");
                    if (val.length > 0) {
                        const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                        if (tw > text_req_w) text_req_w = tw;
                    }
                }
                const right_space = Math.max(getNodeRightReserve(this), 72);
                const boxW = Math.max(65, Math.ceil(text_req_w + 28));
                const reqH = 30 + count * 23 + 22;
                return [Math.max(base_w, 22 + boxW + right_space), reqH];
            };

            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos) {
                    const nodeW = this.size[0];
                    const nodeH = this.size[1];

                    // 1. Header mode pill button click
                    if (local_pos[1] < 0) {
                        const curMode = String(this.properties ? (this.properties.mode || "basic") : "basic");
                        let curIdx = CONCATENATE_MODES.findIndex(m => m.full.toLowerCase() === curMode.toLowerCase() || m.short.toLowerCase() === curMode.toLowerCase());
                        if (curIdx < 0) curIdx = 0;

                        const btnText = CONCATENATE_MODES[curIdx].short;
                        const font = "bold 10px monospace";
                        if (canvas && canvas.ctx) canvas.ctx.font = font;
                        const textW = (canvas && canvas.ctx) ? canvas.ctx.measureText(btnText).width : 30;
                        const modeBtnW = Math.max(48, textW + 12);
                        const modeBtnX = nodeW - modeBtnW - 8;

                        if (local_pos[0] >= modeBtnX - 2 && local_pos[0] <= modeBtnX + modeBtnW + 2) {
                            const nextIdx = (curIdx + 1) % CONCATENATE_MODES.length;
                            this.properties.mode = CONCATENATE_MODES[nextIdx].full;
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("mode-cycle-concat");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        }
                    }

                    // 2. Plus / Minus input slot buttons
                    if (local_pos[1] >= 4 && local_pos[1] <= 26) {
                        const plusBtnX = 22;
                        const plusBtnW = 26;
                        const minusBtnX = 54;
                        const minusBtnW = 26;

                        if (local_pos[0] >= plusBtnX - 2 && local_pos[0] <= plusBtnX + plusBtnW + 2) {
                            const curCount = this.inputs ? this.inputs.length : 2;
                            this.updateConcatenarInputs(curCount + 1);
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            const activeCanvas = LGraphCanvas.active_canvas || canvas;
                            if (activeCanvas) activeCanvas.setDirty(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("add-input");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        }

                        if (local_pos[0] >= minusBtnX - 2 && local_pos[0] <= minusBtnX + minusBtnW + 2) {
                            const curCount = this.inputs ? this.inputs.length : 2;
                            if (curCount > 2) {
                                const removeName = "In" + curCount;
                                if (this.properties && this.properties[removeName] !== undefined) {
                                    delete this.properties[removeName];
                                }
                                this.updateConcatenarInputs(curCount - 1);
                                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                                const activeCanvas = LGraphCanvas.active_canvas || canvas;
                                if (activeCanvas) activeCanvas.setDirty(true, true);
                                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("remove-input");
                                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                                return true;
                            }
                        }
                    }

                    // 3. Bottom-right contextual separator button (only in basic mode)
                    const curMode = String(this.properties ? (this.properties.mode || "basic") : "basic").toLowerCase();
                    if (curMode === "basic") {
                        const curSep = String(this.properties ? (this.properties.separator || "nil") : "nil");
                        let curSepIdx = CONCATENATE_SEPARATORS.findIndex(s => s.full.toLowerCase() === curSep.toLowerCase() || s.short.toLowerCase() === curSep.toLowerCase());
                        if (curSepIdx < 0) curSepIdx = 0;

                        const sepText = CONCATENATE_SEPARATORS[curSepIdx].short;
                        const font = "bold 10px monospace";
                        if (canvas && canvas.ctx) canvas.ctx.font = font;
                        const textW = (canvas && canvas.ctx) ? canvas.ctx.measureText(sepText).width : 25;
                        const sepBtnW = Math.max(48, textW + 12);
                        const sepBtnH = 20;
                        const sepBtnX = nodeW - sepBtnW - 12;
                        const sepBtnY = Math.max(50, nodeH - sepBtnH - 8);

                        if (local_pos[0] >= sepBtnX - 2 && local_pos[0] <= sepBtnX + sepBtnW + 2 &&
                            local_pos[1] >= sepBtnY - 2 && local_pos[1] <= sepBtnY + sepBtnH + 2) {
                            const nextSepIdx = (curSepIdx + 1) % CONCATENATE_SEPARATORS.length;
                            this.properties.separator = CONCATENATE_SEPARATORS[nextSepIdx].full;
                            if (this.properties.separador !== undefined) delete this.properties.separador;
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("separator-cycle-concat");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        }
                    }
                }
            };

            node.onDrawForeground = function(ctx) {
                if (this.flags && this.flags.collapsed) return;
                const nodeW = this.size[0];
                const nodeH = this.size[1];

                ctx.save();

                // 1. Header mode pill button (BASIC / ZIP / MERGE)
                const curMode = String(this.properties ? (this.properties.mode || "basic") : "basic");
                let curIdx = CONCATENATE_MODES.findIndex(m => m.full.toLowerCase() === curMode.toLowerCase() || m.short.toLowerCase() === curMode.toLowerCase());
                if (curIdx < 0) curIdx = 0;
                const btnText = CONCATENATE_MODES[curIdx].short;

                ctx.font = "bold 10px monospace";
                const textW = ctx.measureText(btnText).width;
                const modeBtnW = Math.max(48, textW + 12);
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
                ctx.fillText(btnText, modeBtnX + modeBtnW / 2, modeBtnY + 14);

                // 2. Plus and minus buttons
                const headerY = 6;
                const btnH = 18;
                const plusBtnX = 22;
                const plusBtnW = 26;
                const minusBtnX = 54;
                const minusBtnW = 26;

                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = "#10b981";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(plusBtnX, headerY, plusBtnW, btnH, 5);
                else ctx.rect(plusBtnX, headerY, plusBtnW, btnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = "#a7f3d0";
                ctx.fillText("+", plusBtnX + plusBtnW / 2, headerY + 13);

                const canRemove = this.inputs && (this.inputs.length > 2);
                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = canRemove ? "#ef4444" : "#4b5563";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(minusBtnX, headerY, minusBtnW, btnH, 5);
                else ctx.rect(minusBtnX, headerY, minusBtnW, btnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = canRemove ? "#fca5a5" : "#64748b";
                ctx.fillText("-", minusBtnX + minusBtnW / 2, headerY + 13);

                // 3. Contextual separator selector button in bottom-right (only in basic mode)
                if (curMode.toLowerCase() === "basic") {
                    const curSep = String(this.properties ? (this.properties.separator || "nil") : "nil");
                    let curSepIdx = CONCATENATE_SEPARATORS.findIndex(s => s.full.toLowerCase() === curSep.toLowerCase() || s.short.toLowerCase() === curSep.toLowerCase());
                    if (curSepIdx < 0) curSepIdx = 0;
                    const sepText = CONCATENATE_SEPARATORS[curSepIdx].short;

                    ctx.font = "bold 10px monospace";
                    const sepTextW = ctx.measureText(sepText).width;
                    const sepBtnW = Math.max(48, sepTextW + 12);
                    const sepBtnH = 20;
                    const sepBtnX = nodeW - sepBtnW - 12;
                    const sepBtnY = Math.max(50, nodeH - sepBtnH - 8);

                    ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                    ctx.strokeStyle = "#0284c7";
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(sepBtnX, sepBtnY, sepBtnW, sepBtnH, 10);
                    else ctx.rect(sepBtnX, sepBtnY, sepBtnW, sepBtnH);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = "#38bdf8";
                    ctx.textAlign = "center";
                    ctx.fillText(sepText, sepBtnX + sepBtnW / 2, sepBtnY + 14);
                }

                // 4. Update widget and slot positions
                const count = this.inputs ? this.inputs.length : 2;
                for (let i = 0; i < count; i++) {
                    const widgetY = 30 + i * 23;
                    const dotY = widgetY + 9;

                    if (this.widgets && this.widgets[i]) {
                        this.widgets[i].y = widgetY;
                        this.widgets[i].last_y = widgetY;
                    }
                    if (this.inputs && this.inputs[i]) {
                        this.inputs[i].label = " ";
                        this.inputs[i].pos = [10, dotY];
                    }
                }

                ctx.restore();
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                this.updateConcatenarInputs();
            };

            node.updateConcatenarInputs();
        }

function setupDynamicInlineNode(node) {
            if (!node.properties) node.properties = {};
            node.widgets_up = true;

            if (node.title === "Array" || node.title === "Arreglo" || (node.type && String(node.type).endsWith("/Array"))) {
                const reqOutputs = [
                    { name: "Shape", type: "data" },
                    { name: "\\pos Tag", type: "data" },
                    { name: "X", type: "data" },
                    { name: "Y", type: "data" },
                    { name: "Angle (\\frz)", type: "data" },
                    { name: "Index (a_i)", type: "data" },
                    { name: "Total (a_n)", type: "data" },
                    { name: "Col / Ring", type: "data" },
                    { name: "Row / IdxRing", type: "data" }
                ];
                if (!node.outputs || node.outputs.length !== reqOutputs.length) {
                    const oldLinks = (node.outputs || []).map(o => o.links);
                    node.outputs = reqOutputs.map((o, idx) => ({
                        name: o.name,
                        type: o.type,
                        links: oldLinks[idx] || null
                    }));
                }
            } else if (node.title === "Time to Frame" || node.title === "Tiempo a Frame" || (node.type && String(node.type).endsWith("/Time to Frame"))) {
                const reqOutputs = [
                    { name: "Frame (f)", type: "data" }
                ];
                if (!node.outputs || node.outputs.length !== reqOutputs.length) {
                    const oldLinks = (node.outputs || []).map(o => o.links);
                    node.outputs = reqOutputs.map((o, idx) => ({
                        name: o.name,
                        type: o.type,
                        links: oldLinks[idx] || null
                    }));
                }
            } else if (node.title === "Frame to Time" || node.title === "Frame a Tiempo" || (node.type && String(node.type).endsWith("/Frame to Time"))) {
                const reqOutputs = [
                    { name: "Time", type: "data" },
                    { name: "ASS Time", type: "data" }
                ];
                if (!node.outputs || node.outputs.length !== reqOutputs.length) {
                    const oldLinks = (node.outputs || []).map(o => o.links);
                    node.outputs = reqOutputs.map((o, idx) => ({
                        name: o.name,
                        type: o.type,
                        links: oldLinks[idx] || null
                    }));
                }
            }

            node.updateTagInputs = function() {
                updateNodeModeInputs(this);
            };

            node.updateSysVarInputs = function() {
                updateNodeModeInputs(this);
            };

            updateNodeModeInputs(node);

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos) {
                    const modeInfo = getTitleModeInfo(this);
                    if (local_pos[1] < 0) { // Click inside Title Bar area
                        if (modeInfo) {
                            const font = "bold 10px monospace";
                            if (canvas && canvas.ctx) canvas.ctx.font = font;

                            if (modeInfo.secondaryModes) {
                                const hasTertiary = Boolean(modeInfo.tertiaryModes);
                                const w3 = hasTertiary ? 22 : 0;
                                const isPickerPill1 = modeInfo.isSlicer || modeInfo.isShapesLib;
                                const w2 = Math.max(35, (canvas && canvas.ctx ? canvas.ctx.measureText(modeInfo.secondaryShort).width : 26) + 10);
                                const w1 = Math.max(38, (canvas && canvas.ctx ? canvas.ctx.measureText(modeInfo.currentShort).width : 30) + (isPickerPill1 ? 26 : 10));

                                const btnX3 = hasTertiary ? (this.size[0] - w3 - 8) : this.size[0];
                                const btnX2 = hasTertiary ? (btnX3 - w2 - 5) : (this.size[0] - w2 - 8);
                                const btnX1 = btnX2 - w1 - 5;

                                if (hasTertiary && local_pos[0] >= btnX3 - 4 && local_pos[0] <= btnX3 + w3 + 4) {
                                    const nextIdx = (modeInfo.tertiaryIdx + 1) % modeInfo.tertiaryModes.length;
                                    const nextMode = modeInfo.tertiaryModes[nextIdx];
                                    this.properties[modeInfo.tertiaryPropKey] = nextMode.full;
                                    if (this.widgets) {
                                        const w = this.widgets.find(w => w.property === "invert" || w.name === "Invertir" || w.name === "Invert");
                                        if (w) w.value = nextMode.full;
                                    }
                                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                                    if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("invert-cycle");
                                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);

                                    if (!this._isTracing && window.pywebview && window.pywebview.api && typeof window.pywebview.api.trace_image_api === 'function') {
                                        this._isTracing = true;
                                        window.pywebview.api.trace_image_api(this.properties).then(res => {
                                            this._isTracing = false;
                                            if (res && res.shape) {
                                                this._lastTracedShape = res.shape;
                                            }
                                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                                        }).catch(() => { this._isTracing = false; });
                                    }
                                    return true;
                                }

                                if (local_pos[0] >= btnX2 - 4 && local_pos[0] <= btnX2 + w2 + 4) {
                                    const nextIdx = (modeInfo.secondaryIdx + 1) % modeInfo.secondaryModes.length;
                                    const nextMode = modeInfo.secondaryModes[nextIdx];
                                    this.properties[modeInfo.secondaryPropKey] = nextMode.full;
                                    const titleStr = String(this.title || this.type || "");
                                    if (titleStr.includes("Multi") || titleStr.includes("Slicer") || titleStr.includes("Array")) {
                                        const isLoops = String(nextMode.full).toLowerCase().includes("loop");
                                        const curA = String(this.properties.anchor || "").trim();
                                        if (isLoops) {
                                            const inSlicer = SLICER_ANCHOR_MODES.some(m => m.full.toLowerCase() === curA.toLowerCase() || m.short.toLowerCase() === curA.toLowerCase());
                                            if (!inSlicer || curA.toLowerCase() === "relative" || curA.toLowerCase() === "relativo") {
                                                this.properties.anchor = "pieces";
                                            }
                                        } else {
                                            if (titleStr.includes("Multi")) {
                                                const inGeom = GEOMETRIC_ANCHOR_MODES.some(m => m.full.toLowerCase() === curA.toLowerCase() || m.short.toLowerCase() === curA.toLowerCase());
                                                if (!inGeom) {
                                                    this.properties.anchor = "center";
                                                }
                                            } else {
                                                if (curA.toLowerCase() === "pieces" || curA.toLowerCase() === "piezas") {
                                                    this.properties.anchor = "relative";
                                                }
                                            }
                                        }
                                        if (this.widgets) {
                                            const ancW = this.widgets.find(w => w.name === "Anchor" || w.name === "Anclaje" || w.property === "anchor");
                                            if (ancW) ancW.value = this.properties.anchor;
                                        }
                                    }
                                    const isAnimNodeOrder = (modeInfo.key === "Animation" || modeInfo.key === "Functions/Animation" || titleStr.includes("Animation") || (this.type && String(this.type).includes("Animation")));
                                    const prevWOrder = Math.max((this._customSize && this._customSize[0] > 0) ? this._customSize[0] : 0, (this.size && this.size[0] > 0) ? this.size[0] : 0);
                                    const prevHOrder = Math.max((this._customSize && this._customSize[1] > 0) ? this._customSize[1] : 0, (this.size && this.size[1] > 0) ? this.size[1] : 0);
                                    updateNodeModeInputs(this);
                                    if (this.computeSize) {
                                        const sz = this.computeSize();
                                        if (isAnimNodeOrder) {
                                            const finalW = Math.max(prevWOrder, sz[0]);
                                            const finalH = Math.max(prevHOrder, sz[1]);
                                            this.size = [finalW, finalH];
                                            this._customSize = [finalW, finalH];
                                        } else {
                                            this.size = this.computeSize();
                                        }
                                    }
                                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                                    if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("mode-cycle-order");
                                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                                    return true;
                                }

                                if (local_pos[0] >= btnX1 - 4 && local_pos[0] <= btnX1 + w1 + 4) {
                                    if (modeInfo.isSlicer) {
                                        openMeshGridPicker(this, null, e);
                                        return true;
                                    }
                                    const nextIdx = (modeInfo.currentIdx + 1) % modeInfo.modeList.length;
                                    const nextMode = modeInfo.modeList[nextIdx];
                                    this.properties[modeInfo.propKey] = nextMode.full;
                                    if (modeInfo.key === "Math") {
                                        const entry = DYNAMIC_NODE_MODES["Math"];
                                        const map = entry.secondaryModesMap[nextMode.full] || entry.secondaryModesMap["Basico"];
                                        if (map && map.length > 0) {
                                            this.properties[entry.secondaryPropKey] = map[0].full;
                                        }
                                    }
                                    const titleStr = String(this.title || this.type || "");
                                    const isAnimNodeMode = (modeInfo.key === "Animation" || modeInfo.key === "Functions/Animation" || titleStr.includes("Animation") || (this.type && String(this.type).includes("Animation")));
                                    const prevWMode = Math.max((this._customSize && this._customSize[0] > 0) ? this._customSize[0] : 0, (this.size && this.size[0] > 0) ? this.size[0] : 0);
                                    const prevHMode = Math.max((this._customSize && this._customSize[1] > 0) ? this._customSize[1] : 0, (this.size && this.size[1] > 0) ? this.size[1] : 0);
                                    updateNodeModeInputs(this);
                                    if (this.computeSize) {
                                        const sz = this.computeSize();
                                        if (isAnimNodeMode) {
                                            const finalW = Math.max(prevWMode, sz[0]);
                                            const finalH = Math.max(prevHMode, sz[1]);
                                            this.size = [finalW, finalH];
                                            this._customSize = [finalW, finalH];
                                        } else {
                                            this.size = this.computeSize();
                                        }
                                    }
                                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                                    if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("mode-cycle-osc");
                                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                                    return true;
                                }
                            } else {
                                const btnText = modeInfo.currentShort;
                                let textW = 50;
                                if (canvas && canvas.ctx) {
                                    textW = canvas.ctx.measureText(btnText).width;
                                }
                                const isPickerPill = modeInfo.isSlicer || modeInfo.isShapesLib;
                                const btnW = Math.max(55, textW + (isPickerPill ? 26 : 14));
                                const btnX = this.size[0] - btnW - 8;
                                const isSysVarNode = this.title && (String(this.title).includes("Sys Var") || String(this.title).includes("SysVar"));
                                const isMultiTagNode = this.title && String(this.title).includes("MultiTag");

                                if (local_pos[0] >= btnX - 4 && local_pos[0] <= btnX + btnW + 6) {
                                    if (isSysVarNode) {
                                        openSysVarGridPicker(this, null, e);
                                        return true;
                                    } else if (isMultiTagNode) {
                                        openTagGridPicker(this, null, e);
                                        return true;
                                    } else if (modeInfo.isSlicer) {
                                        openMeshGridPicker(this, null, e);
                                        return true;
                                    } else if (isPickerPill && local_pos[0] >= btnX + btnW - 18) {
                                        openShapesLibGridPicker(this);
                                        return true;
                                    } else {
                                        const nextIdx = (modeInfo.currentIdx + 1) % modeInfo.modeList.length;
                                        const nextMode = modeInfo.modeList[nextIdx];
                                        this.properties[modeInfo.propKey] = nextMode.full;
                                        if (typeof hidePyxisRetimeModeTooltip === "function") hidePyxisRetimeModeTooltip();
                                        updateNodeModeInputs(this);
                                        if (this.computeSize) this.size = this.computeSize();
                                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                                        if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("mode-cycle");
                                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                                        return true;
                                    }
                                }
                            }
                        }
                        return false;
                    } else {
                        if (this.widgets) {
                            for (let i = 0; i < this.widgets.length; i++) {
                                const w = this.widgets[i];
                                if (w) {
                                    if (w.name === "add_sub_buttons" && w.callback) {
                                        const yMin = (w.last_y !== undefined) ? w.last_y : w.y;
                                        if (local_pos[1] >= yMin - 4 && local_pos[1] <= yMin + 28) {
                                            w.callback(w, canvas, this, local_pos, e);
                                            return true;
                                        }
                                    } else if (w.onClick) {
                                        if (w.isPointInside) {
                                            if (w.isPointInside(local_pos[0], local_pos[1], this)) {
                                                w.onClick(canvas);
                                                return true;
                                            }
                                        } else {
                                            const yMin = (w.last_y !== undefined) ? w.last_y : w.y;
                                            if (local_pos[1] >= yMin - 2 && local_pos[1] <= yMin + 20) {
                                                const bX = (w._btnX !== undefined) ? w._btnX : 20;
                                                const bW = (w._btnW !== undefined) ? w._btnW : 75;
                                                if (local_pos[0] >= bX - 2 && local_pos[0] <= bX + bW + 2) {
                                                    w.onClick(canvas);
                                                    return true;
                                                }
                                            }
                                        }
                                    } else if (w._boxX !== undefined && w.isPointInside && w.mouse) {
                                        if (w.isPointInside(local_pos[0], local_pos[1], this)) {
                                            return w.mouse(e, local_pos, this);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                const isShapesLib = this.title === "Library" || this.title === "Biblioteca" || (this.type && String(this.type).endsWith("/Library"));
                if (isShapesLib) {
                    const nw = this.size ? this.size[0] : 156;
                    const nh = this.size ? this.size[1] : 195;
                    const availW = Math.max(30, nw - 20);
                    const availH = Math.max(30, nh - 52);
                    const cardSide = Math.max(30, Math.min(availW, availH));
                    const cardX = Math.floor((nw - cardSide) / 2);
                    const cardY = Math.floor(28 + (availH - cardSide) / 2);

                    if (local_pos[0] >= cardX - 4 && local_pos[0] <= cardX + cardSide + 4 && local_pos[1] >= cardY - 4 && local_pos[1] <= cardY + cardSide + 4) {
                        openShapesLibGridPicker(this);
                        return true;
                    }
                }

                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            node.onDblClick = function(e, pos) {
                if (this.title && (String(this.title).includes("Sys Var") || String(this.title).includes("SysVar"))) {
                    openSysVarGridPicker(this, null, e);
                    return true;
                }
                if (this.title && String(this.title).includes("MultiTag")) {
                    openTagGridPicker(this, null, e);
                    return true;
                }
                if (this.title === "Library" || this.title === "Biblioteca" || (this.type && String(this.type).endsWith("/Library"))) {
                    openShapesLibGridPicker(this);
                    return true;
                }
                if (this.properties && this.properties["image_path"] !== undefined) {
                    const updateImagePath = (filePath) => {
                        if (!filePath) return;
                        const prev = this.properties["image_path"];
                        this.properties["image_path"] = filePath;
                        if (this.widgets) {
                            this.widgets.forEach(w => {
                                if (w.property === "image_path" || w.name === "Image Path" || w.name === "image_path") {
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
                    fileInput.id = "pyxis-file-input-image";
                    fileInput.name = "pyxis-file-input-image";
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
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateNodeModeInputs(this);
                if (this.computeSize) {
                    const sz = this.computeSize();
                    const isFixedWNode = Boolean(this.title && (String(this.title).includes("Concentric") || String(this.title).includes("Bordes")));
                    if (isFixedWNode) {
                        this.size = [sz[0], sz[1]];
                    } else if (this.size && Array.isArray(this.size)) {
                        this.size[0] = Math.max(this.size[0], sz[0]);
                        this.size[1] = sz[1];
                    } else {
                        this.size = [sz[0], sz[1]];
                    }
                }
            };

            node.computeSize = function() {
                let max_input_w = 0;
                const nodeInputs = this.inputs || [];
                nodeInputs.forEach(inp => {
                    const inpName = inp.name || "";
                    const specProp = inp.property || inpName;
                    let v = "";
                    if (this.properties) {
                        if (this.properties[specProp] !== undefined) v = String(this.properties[specProp]);
                        else if (this.properties[inpName] !== undefined) v = String(this.properties[inpName]);
                    }
                    let vToMeasure = v || inpName;
                    if (v && (isFilePathPropOrVal(specProp, v) || isCompactTextPropOrVal(specProp, v))) {
                        if (isFilePathPropOrVal(specProp, v)) {
                            const parts = v.replace(/\\/g, "/").split("/");
                            vToMeasure = ".../" + (parts[parts.length - 1] || v);
                        } else {
                            vToMeasure = v.length > 10 ? (v.substring(0, 10) + "...") : v;
                        }
                        const tw = Math.min(65, getExactTextWidth(vToMeasure, "bold 11px Consolas, monospace"));
                        if (tw > max_input_w) max_input_w = tw;
                    } else {
                        const tw = getExactTextWidth(vToMeasure, "bold 11px Consolas, monospace");
                        if (tw > max_input_w) max_input_w = tw;
                    }
                });

                if (this.widgets) {
                    this.widgets.forEach(w => {
                        if (!w) return;
                        if (w._boxW !== undefined) return;
                        const isBtnWidget = (w.type === "button" || w._isButton || (w.spec && w.spec.type === "button") || typeof w.onClick === "function");
                        if (isBtnWidget) return;
                        const p = w.property;
                        let v = "";
                        if (this.properties && p && this.properties[p] !== undefined) {
                            v = String(this.properties[p]);
                        } else if (w.value !== undefined) {
                            v = String(w.value);
                        }
                        let vToMeasure = v || w.name || "";
                        if (v && (isFilePathPropOrVal(p, v) || isCompactTextPropOrVal(p, v))) {
                            if (isFilePathPropOrVal(p, v)) {
                                const parts = v.replace(/\\/g, "/").split("/");
                                vToMeasure = ".../" + (parts[parts.length - 1] || v);
                            } else {
                                vToMeasure = v.length > 10 ? (v.substring(0, 10) + "...") : v;
                            }
                            const tw = Math.min(65, getExactTextWidth(vToMeasure, "bold 11px Consolas, monospace"));
                            if (tw > max_input_w) max_input_w = tw;
                        } else {
                            const tw = getExactTextWidth(vToMeasure, "bold 11px Consolas, monospace");
                            if (tw > max_input_w) max_input_w = tw;
                        }
                    });
                }

                let max_output_w = 0;
                (this.outputs || []).forEach(out => {
                    if (out && (out.name || out.label)) {
                        let outText = out.label != null ? out.label : out.name;
                        if (outText && window.PyxisI18n && outText !== " ") {
                            outText = window.PyxisI18n.translateSlot(outText);
                        }
                        const ow = getExactTextWidth(outText, "11px Arial, sans-serif");
                        if (ow > max_output_w) max_output_w = ow;
                    }
                });

                const modeInfo = getTitleModeInfo(this);
                let modeW = 0;
                if (modeInfo) {
                    modeW = Math.max(35, getExactTextWidth(modeInfo.currentShort, "bold 10px monospace") + 12);
                    if (modeInfo.secondaryModes) {
                        modeW += Math.max(35, getExactTextWidth(modeInfo.secondaryShort, "bold 10px monospace") + 12);
                    }
                    if (modeInfo.tertiaryModes) {
                        modeW += 26;
                    }
                    if (modeInfo.isSlicer || modeInfo.isShapesLib) {
                                        modeW += 26;
                    }
                }

                const titleText = String(this.title || this.type || "");
                const titleW = getExactTextWidth(titleText, "bold 12px sans-serif");
                const boxW = Math.max(65, Math.ceil(max_input_w + 28));
                const right_space = getNodeRightReserve(this);
                const isTextNode = (titleText === "Text" || titleText === "Texto" || (this.type && (String(this.type).endsWith("/Text") || String(this.type).endsWith("Text") || String(this.type).endsWith("Texto"))));
                const minBaseW = (titleText === "Math" || (this.type && this.type.includes("Math"))) ? 165 : (isTextNode ? 155 : 175);

                const hasLoopFooter = (
                    titleText === "Slicer" ||
                    titleText === "Multi" ||
                    titleText === "Array" ||
                    titleText === "Union & Divide" || titleText === "Unir y Dividir" ||
                    titleText.includes("Text to Particle") || titleText.includes("From Text") ||
                    titleText.includes("Particles") || titleText.includes("Particle") ||
                    titleText.includes("IMG to pixels") || titleText.includes("IMG to Pixels") ||
                    titleText.includes("IMG to Shape") || titleText.includes("IMG to shape") ||
                    titleText.includes("Concentric Borders") || titleText.includes("Bordes") ||
                    titleText.includes("Clip Gradient") || titleText.includes("Clip") ||
                    titleText.includes("MaxLoop") || titleText.includes("Max Loop") ||
                    titleText.includes("Animation") || titleText.includes("Animación") ||
                    titleText.includes("Module")
                );

                let widgetRows = 0;
                if (this.widgets && this.widgets.length > 0) {
                    this.widgets.forEach((w, idx) => {
                        const r = (w && w._visualRow !== undefined) ? (w._visualRow + 1) : (idx + 1);
                        if (r > widgetRows) widgetRows = r;
                    });
                }
                const maxRows = Math.max(nodeInputs.length, widgetRows, (this.outputs ? this.outputs.length : 0));
                let req_w = Math.max(minBaseW, 22 + boxW + right_space, titleW + modeW + 54);
                let req_h = 11 + maxRows * 23 + (hasLoopFooter ? 24 : 22);

                if (titleText === "Animation" || titleText === "Animación" || (this.type && String(this.type).includes("Animation"))) {
                    req_h += 8;
                }

                if (titleText === "Tag Manipulator" || titleText === "Manipulador de Tags" || (this.type && String(this.type).includes("Tag Manipulator"))) {
                    const titleMeasure = Math.max(getExactTextWidth(titleText, "bold 12px sans-serif"), getExactTextWidth("Manipulador de Tags", "bold 12px sans-serif"));
                    const headerMinW = Math.max(240, Math.ceil(titleMeasure + modeW + 68));
                    req_w = Math.max(headerMinW, 22 + boxW + right_space);
                }

                if (titleText === "Slicer" || titleText === "Multi" || titleText === "Array" || titleText === "Arreglo") {
                    req_w = Math.max(req_w, 235);
                } else if (titleText.includes("Benchmark")) {
                    req_w = Math.max(req_w, 215);
                    req_h = 60;
                } else if (titleText.includes("Bordes") || titleText.includes("Concentric")) {
                    req_w = 235;
                } else if (titleText === "Modulator" || titleText === "Modulador" || (this.type && String(this.type).includes("Modulator"))) {
                    req_w = Math.max(req_w, 225);
                } else if (titleText.includes("Curva") || titleText.includes("Bezier")) {
                    req_w = Math.max(req_w, 235);
                    req_h = 188;
                } else if (titleText === "Text on Path" || titleText === "Texto en Ruta" || (this.type && (String(this.type).includes("Text on Path") || String(this.type).includes("Texto en Ruta")))) {
                    req_w = Math.max(req_w, 225);
                    req_h = 138;
                } else if (titleText === "Walker" || titleText === "Recorredor" || (this.type && String(this.type).endsWith("/Walker"))) {
                    req_w = Math.max(req_w, 235);
                    req_h = 152;
                } else if (titleText.includes("Clip") || titleText === "Manipulator" || titleText === "Manipulador" || titleText === "Transform" || titleText === "Transformar" || titleText === "Stroke" || titleText === "Trazo" || titleText === "Ipol" || titleText === "Interpolator" || titleText === "Synced" || titleText === "Union & Divide" || titleText === "Unir y Dividir" || (this.type && (String(this.type).endsWith("/Manipulator") || String(this.type).endsWith("/Transform") || String(this.type).endsWith("/Stroke") || String(this.type).endsWith("/Ipol") || String(this.type).endsWith("/Synced") || String(this.type).endsWith("/Union & Divide")))) {
                    req_w = Math.max(req_w, 225);
                } else if (titleText === "Move Tag" || titleText === "Mover Tags" || titleText === "Mover Tag" || titleText === "Move Text" || titleText === "Mover Texto" || (this.type && (String(this.type).endsWith("/Move Tag") || String(this.type) === "Move Tag" || String(this.type).endsWith("/Move Text") || String(this.type) === "Move Text"))) {
                    req_w = Math.max(req_w, 195);
                } else if (titleText.includes("Time to Frame") || titleText.includes("Tiempo a Frame") || titleText.includes("Frame to Time") || titleText.includes("Frame a Tiempo") || (this.type && (String(this.type).includes("Time to Frame") || String(this.type).includes("Frame to Time")))) {
                    req_w = Math.max(req_w, Math.ceil((titleW + modeW + 54) * 1.10), 220);
                }

                const isShapesLib = titleText === "Library" || titleText === "Biblioteca" || (this.type && String(this.type).endsWith("/Library"));
                if (isShapesLib) {
                    req_w = Math.max(req_w, 205);
                    req_h = Math.max(req_h, 54);
                }
                const isSysVar = titleText.includes("Sys Var") || titleText.includes("SysVar");
                const isModuleNode = titleText.includes("Module") || titleText.includes("Módulo") || titleText.includes("Modulo") || (this.type && this.type.includes("Module"));
                if (isSysVar) {
                    req_w = Math.max(req_w, 185);
                    req_h = (nodeInputs && nodeInputs.length > 0) ? (11 + nodeInputs.length * 23 + 24) : 48;
                } else if (isModuleNode) {
                    req_w = Math.max(req_w, 180);
                    req_h = Math.max(req_h, 95);
                }
                if (this.properties && this.properties.expandable) {
                    req_w = Math.max(req_w, 160);
                    req_h = 11 + nodeInputs.length * 23 + 28;
                }
                return [req_w, req_h];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                const modeInfo = getTitleModeInfo(this);
                if (modeInfo) {
                    ctx.save();
                    ctx.font = "bold 10px monospace";
                    const btnH = 20;
                    const btnY = -25;

                    if (modeInfo.secondaryModes) {
                        const hasTertiary = Boolean(modeInfo.tertiaryModes);
                        const w3 = hasTertiary ? 22 : 0;
                        const isPickerPill1 = modeInfo.isSlicer || modeInfo.isShapesLib;
                        const btnText2 = modeInfo.secondaryShort;
                        const btnText1 = modeInfo.currentShort;
                        const textW2 = ctx.measureText(btnText2).width;
                        const textW1 = ctx.measureText(btnText1).width;
                        const w2 = Math.max(35, textW2 + 10);
                        const w1 = Math.max(38, textW1 + (isPickerPill1 ? 26 : 10));

                        const btnX3 = hasTertiary ? (this.size[0] - w3 - 8) : this.size[0];
                        const btnX2 = hasTertiary ? (btnX3 - w2 - 5) : (this.size[0] - w2 - 8);
                        const btnX1 = btnX2 - w1 - 5;

                        if (hasTertiary) {
                            const terVal = String(modeInfo.tertiaryFull).toLowerCase();
                            const isInverted = terVal === "invertido" || terVal === "invert" || terVal === "true" || terVal === "1";

                            ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                            ctx.strokeStyle = isInverted ? "#f59e0b" : "#8b5cf6";
                            ctx.lineWidth = 1.2;
                            ctx.beginPath();
                            if (ctx.roundRect) ctx.roundRect(btnX3, btnY, w3, btnH, 10);
                            else ctx.rect(btnX3, btnY, w3, btnH);
                            ctx.fill();
                            ctx.stroke();

                            const iconCX = btnX3 + w3 / 2;
                            const iconCY = btnY + btnH / 2;
                            const iconR = 5.0;

                            ctx.save();
                            ctx.beginPath();
                            ctx.arc(iconCX, iconCY, iconR, 0, Math.PI * 2);
                            ctx.fillStyle = "#12161f";
                            ctx.fill();

                            ctx.beginPath();
                            if (isInverted) {
                                ctx.arc(iconCX, iconCY, iconR, Math.PI * 1.5, Math.PI * 0.5, false);
                            } else {
                                ctx.arc(iconCX, iconCY, iconR, Math.PI * 0.5, Math.PI * 1.5, false);
                            }
                            ctx.closePath();
                            ctx.fillStyle = isInverted ? "#fbbf24" : "#a7f3d0";
                            ctx.fill();

                            ctx.beginPath();
                            ctx.arc(iconCX, iconCY, iconR, 0, Math.PI * 2);
                            ctx.strokeStyle = isInverted ? "#fbbf24" : "#a7f3d0";
                            ctx.lineWidth = 1.2;
                            ctx.stroke();
                            ctx.restore();
                        }

                        ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                        ctx.strokeStyle = "#0284c7";
                        ctx.lineWidth = 1.2;
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(btnX2, btnY, w2, btnH, 10);
                        else ctx.rect(btnX2, btnY, w2, btnH);
                        ctx.fill();
                        ctx.stroke();

                        ctx.fillStyle = "#38bdf8";
                        ctx.textAlign = "center";
                        ctx.fillText(btnText2, btnX2 + w2 / 2, btnY + 14);

                        ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                        ctx.strokeStyle = "#8b5cf6";
                        ctx.lineWidth = 1.2;
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(btnX1, btnY, w1, btnH, 10);
                        else ctx.rect(btnX1, btnY, w1, btnH);
                        ctx.fill();
                        ctx.stroke();

                        ctx.fillStyle = "#a7f3d0";
                        ctx.textAlign = isPickerPill1 ? "left" : "center";
                        ctx.fillText(btnText1, btnX1 + (isPickerPill1 ? 7 : w1 / 2), btnY + 14);

                        if (isPickerPill1) {
                            const iconX = btnX1 + w1 - 16;
                            const iconY = btnY + 4;
                            ctx.strokeStyle = "#a7f3d0";
                            ctx.lineWidth = 1.0;
                            if (modeInfo.isSlicer) {
                                ctx.strokeRect(iconX, iconY, 9, 9);
                                ctx.beginPath();
                                ctx.moveTo(iconX + 4.5, iconY);
                                ctx.lineTo(iconX + 4.5, iconY + 9);
                                ctx.moveTo(iconX, iconY + 4.5);
                                ctx.lineTo(iconX + 9, iconY + 4.5);
                                ctx.stroke();
                            } else {
                                ctx.beginPath();
                                ctx.arc(iconX + 4.5, iconY + 4.5, 4, 0, Math.PI * 2);
                                ctx.stroke();
                            }
                        }
                    } else {
                        const btnText = modeInfo.currentShort;
                        const textW = ctx.measureText(btnText).width;
                        const isPickerPill = modeInfo.isSlicer || modeInfo.isShapesLib;
                        const btnW = Math.max(55, textW + (isPickerPill ? 26 : 14));
                        const btnX = this.size[0] - btnW - 8;

                        ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                        ctx.strokeStyle = "#8b5cf6";
                        ctx.lineWidth = 1.2;
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(btnX, btnY, btnW, btnH, 10);
                        else ctx.rect(btnX, btnY, btnW, btnH);
                        ctx.fill();
                        ctx.stroke();

                        ctx.fillStyle = "#a7f3d0";
                        ctx.textAlign = "left";
                        ctx.fillText(btnText, btnX + (isPickerPill ? 7 : (btnW - textW) / 2), btnY + 14);

                        if (isPickerPill) {
                            const iconX = btnX + btnW - 16;
                            const iconY = btnY + 4;
                            ctx.strokeStyle = "#a7f3d0";
                            ctx.lineWidth = 1.0;
                            if (modeInfo.isSlicer) {
                                ctx.strokeRect(iconX, iconY, 9, 9);
                                ctx.beginPath();
                                ctx.moveTo(iconX + 4.5, iconY);
                                ctx.lineTo(iconX + 4.5, iconY + 9);
                                ctx.moveTo(iconX, iconY + 4.5);
                                ctx.lineTo(iconX + 9, iconY + 4.5);
                                ctx.stroke();
                            } else {
                                ctx.beginPath();
                                ctx.arc(iconX + 4.5, iconY + 4.5, 4, 0, Math.PI * 2);
                                ctx.stroke();
                            }
                        }
                    }
                    ctx.restore();
                }

                if (this.widgets) {
                    for (let i = 0; i < this.widgets.length; i++) {
                        const w = this.widgets[i];
                        const rowIdx = (w && w._visualRow !== undefined) ? w._visualRow : i;
                        const yPos = 11 + rowIdx * 23;
                        w.y = yPos;
                        w.last_y = yPos;
                        if (w.draw) {
                            w.draw(ctx, this, this.size[0], yPos, 18);
                        }
                    }
                }

                if (this.inputs) {
                    for (let i = 0; i < this.inputs.length; i++) {
                        const inp = this.inputs[i];
                        const pKey = inp.property || inp.name;
                        const w = this.widgets ? this.widgets.find(wid => (wid.property && wid.property === pKey) || wid.name === pKey || wid.name === inp.name) : null;
                        const yPos = (w && w.last_y !== undefined) ? w.last_y : (w && w.y !== undefined ? w.y : (11 + i * 23));
                        inp.label = " ";
                        inp.pos = [10, yPos + 9];
                    }
                }

                let footerCounterText = "";
                const titleText = String(this.title || this.type || "");
                const isEn = window.PyxisI18n && window.PyxisI18n.currentLang === "en";
                const singleShapeText = isEn ? "Single shape." : "Un solo shape.";

                if (titleText.includes("Slicer")) {
                    const loopMode = String((this.properties && (this.properties.loop_mode !== undefined ? this.properties.loop_mode : "Loops"))).toLowerCase();
                    if (loopMode.includes("loop") || loopMode.includes("pieza")) {
                        footerCounterText = "s_i, s_n";
                        if (this.outputs && this.outputs[0]) this.outputs[0].name = "Piece";
                    } else {
                        footerCounterText = singleShapeText;
                        if (this.outputs && this.outputs[0]) this.outputs[0].name = "Shape Out";
                    }
                } else if (titleText.includes("Multi") || (this.type && String(this.type).includes("Multi"))) {
                    const loopMode = String((this.properties && (this.properties.loop_mode || this.properties.out_mode)) || "Shape").toLowerCase();
                    if (loopMode.includes("loop") || loopMode.includes("pieza")) {
                        footerCounterText = "m_i, m_n";
                        if (this.outputs && this.outputs[0]) this.outputs[0].name = "Piece";
                    } else {
                        footerCounterText = singleShapeText;
                        if (this.outputs && this.outputs[0]) this.outputs[0].name = "Shape Out";
                    }
                } else if (titleText === "Array" || titleText === "Arreglo") {
                    const outMode = String((this.properties && (this.properties.out_mode || this.properties.loop_mode)) || "Loops").toLowerCase();
                    if (outMode.includes("loop") || outMode.includes("pieza")) {
                        footerCounterText = "a_i, a_n";
                        if (this.outputs && this.outputs[0]) this.outputs[0].name = "Piece";
                    } else {
                        footerCounterText = singleShapeText;
                        if (this.outputs && this.outputs[0]) this.outputs[0].name = "Shape Out";
                    }
                } else if (titleText === "Union & Divide" || titleText === "Unir y Dividir") {
                    footerCounterText = "d_i, d_n";
                } else if (titleText.includes("Text to Particle") || titleText.includes("From Text")) {
                    footerCounterText = "tp_i, tp_n";
                } else if (titleText.includes("IMG to pixels") || titleText.includes("IMG to Pixels") || titleText.includes("IMG to Particle")) {
                    footerCounterText = "ip_i, ip_n";
                } else if (titleText.includes("Particles")) {
                    footerCounterText = "p_i, p_n";
                } else if (titleText.includes("IMG to Shape") || titleText.includes("IMG to shape")) {
                    footerCounterText = "ish_i, ish_n";
                } else if (titleText.includes("Concentric Borders") || titleText.includes("Bordes")) {
                    footerCounterText = "b_i, b_n";
                } else if (titleText.includes("Clip Gradient")) {
                    footerCounterText = "c_i, c_n";
                } else if (titleText === "Animation" || titleText === "Animación" || titleText.includes("Animation") || (this.type && String(this.type).includes("Animation"))) {
                    const varName = (this.properties && this.properties.var_name) ? String(this.properties.var_name).trim() : "an";
                    footerCounterText = `${varName}_i, ${varName}_n`;
                } else if (titleText.includes("MaxLoop") || titleText.includes("Max Loop")) {
                    const varName = (this.properties && this.properties.var_name) ? String(this.properties.var_name).trim() : "j";
                    footerCounterText = `${varName}, max${varName}`;
                } else if (titleText.includes("Module") || titleText.includes("Módulo") || titleText.includes("Modulo")) {
                    function resolveLoopPort(graph, inputPort, defaultVal, isTotal) {
                        if (graph && inputPort && inputPort.link !== null && inputPort.link !== undefined) {
                            const linkObj = graph.links[inputPort.link];
                            if (linkObj) {
                                const originNode = graph.getNodeById(linkObj.origin_id);
                                if (originNode) {
                                    const origTitle = String(originNode.title || originNode.type || "");
                                    const slot = linkObj.origin_slot;

                                    if (origTitle.includes("Main Loop") || origTitle.includes("MainLoop")) {
                                        const iter = String((originNode.properties && originNode.properties.iterator) || "syl").toLowerCase();
                                        if (slot === 1) return `${iter}.i`;
                                        if (slot === 2) return `${iter}.n`;
                                        return isTotal ? `${iter}.n` : `${iter}.i`;
                                    }
                                    if (origTitle.includes("MaxLoop") || origTitle.includes("Max Loop")) {
                                        const vName = String((originNode.properties && originNode.properties.var_name) || "j").trim() || "j";
                                        if (slot === 1) return vName;
                                        if (slot === 2) return `max${vName}`;
                                        return isTotal ? `max${vName}` : vName;
                                    }
                                    if (origTitle === "Array" || origTitle.endsWith("/Array") || origTitle === "Arreglo") {
                                        if (slot === 5) return "a_i";
                                        if (slot === 6) return "a_n";
                                        return isTotal ? "a_n" : "a_i";
                                    }
                                    if (origTitle === "Slicer" || origTitle.endsWith("/Slicer")) {
                                        return isTotal ? "s_n" : "s_i";
                                    }
                                    if (origTitle.includes("Text to Particle") || origTitle.includes("From Text")) {
                                        return isTotal ? "tp_n" : "tp_i";
                                    }
                                    if (origTitle.includes("IMG to pixels") || origTitle.includes("IMG to Pixels") || origTitle.includes("IMG to Particle")) {
                                        return isTotal ? "ip_n" : "ip_i";
                                    }
                                    if (origTitle.includes("Particles")) {
                                        return isTotal ? "p_n" : "p_i";
                                    }
                                    if (origTitle.includes("IMG to Shape") || origTitle.includes("IMG to shape")) {
                                        return isTotal ? "ish_n" : "ish_i";
                                    }
                                    if (origTitle.includes("Concentric Borders") || origTitle.includes("Bordes")) {
                                        return isTotal ? "b_n" : "b_i";
                                    }
                                    if (origTitle.includes("Clip Gradient") || origTitle.includes("Clip")) {
                                        return isTotal ? "c_n" : "c_i";
                                    }
                                    if (originNode.outputs && originNode.outputs[slot]) {
                                        const outName = originNode.outputs[slot].name || "";
                                        const mMatch = outName.match(/\(([^)]+)\)/);
                                        return mMatch ? mMatch[1] : outName;
                                    }
                                }
                            }
                        }
                        return defaultVal;
                    }

                    let rawIter = (this.properties && (this.properties.iter !== undefined ? this.properties.iter : this.properties.i)) || "i";
                    let rawTotal = (this.properties && (this.properties.total !== undefined ? this.properties.total : this.properties.N)) || "N";

                    if (this.widgets) {
                        if (this.widgets[0] && this.widgets[0].value !== undefined && String(this.widgets[0].value).trim() !== "") rawIter = String(this.widgets[0].value).trim();
                        if (this.widgets[1] && this.widgets[1].value !== undefined && String(this.widgets[1].value).trim() !== "") rawTotal = String(this.widgets[1].value).trim();
                    }

                    const iterLabel = resolveLoopPort(this.graph, (this.inputs && this.inputs[0]), rawIter, false);
                    const totalLabel = resolveLoopPort(this.graph, (this.inputs && this.inputs[1]), rawTotal, true);

                    footerCounterText = `${iterLabel}, ${totalLabel}`;
                }

                if (footerCounterText) {

                    ctx.save();
                    ctx.font = "italic 11px monospace";
                    ctx.fillStyle = "#94a3b8";
                    ctx.textAlign = "center";
                    ctx.fillText(footerCounterText, this.size[0] / 2, this.size[1] - 6);
                    ctx.restore();
                }
            };
            if (node.computeSize) node.size = node.computeSize();
        }


        function openInlineValueUnitEditor(node, widget, propertyName, titleName, event) {
            const existing = document.getElementById("pyxis-inline-text-editor");
            if (existing) {
                if (typeof existing._saveAndClose === "function") existing._saveAndClose();
                else existing.remove();
            }

            const canvas = (typeof LGraphCanvas !== "undefined" && LGraphCanvas.active_canvas) || window.canvas || window.graphcanvas;
            if (!canvas || !canvas.canvas) return;

            const propKey = propertyName || widget.property || "value";
            const curVal = String((node.properties && propKey && node.properties[propKey] !== undefined)
                ? node.properties[propKey]
                : (widget.value !== undefined ? widget.value : ""));

            const drawY = (widget.last_y !== undefined) ? widget.last_y : ((widget.y !== undefined) ? widget.y : 11);
            const margin = (widget && widget._boxX !== undefined) ? widget._boxX : 28;
            const textPadLeft = 6;
            const textPadRight = 6;
            const textPadTop = 2.5;

            const rect = canvas.canvas.getBoundingClientRect();
            const scale = canvas.ds ? canvas.ds.scale : 1.0;
            const offset = canvas.ds ? canvas.ds.offset : [0, 0];

            const nodeW = (node && node.size && node.size[0]) ? node.size[0] : 184;
            const wWidth = getInlineBoxWidth(node, widget, titleName, propertyName, nodeW);
            const maxAllowedH = (node && node.size && node.size[1]) ? Math.max(38, node.size[1] - drawY - 8) : 38;
            const wHeight = maxAllowedH;

            const halfStroke = 0.75 * scale;
            const screenX = rect.left + (node.pos[0] + margin + offset[0]) * scale - halfStroke;
            const screenY = rect.top + (node.pos[1] + drawY + offset[1]) * scale - halfStroke;
            const screenW = (wWidth * scale) + (1.5 * scale);
            const screenH = (wHeight * scale) + (1.5 * scale);

            if (widget) widget._is_inline_editing = true;
            if (canvas.draw) canvas.draw(true, true);

            const inputEl = document.createElement("textarea");
            inputEl.id = "pyxis-inline-text-editor";
            inputEl.name = "pyxis-inline-text-editor";
            inputEl.spellcheck = false;
            inputEl.autocomplete = "off";
            inputEl.autocorrect = "off";
            inputEl.autocapitalize = "off";
            inputEl.value = curVal;
            const rawPlaceholder = widget.name || titleName || "Value";
            inputEl.placeholder = (window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot(rawPlaceholder) : rawPlaceholder;

            inputEl.style.resize = "none";
            inputEl.style.overflowY = "auto";
            inputEl.style.overflowX = "hidden";
            inputEl.style.whiteSpace = "pre-wrap";
            inputEl.style.overflowWrap = "anywhere";
            inputEl.style.wordBreak = "break-all";
            inputEl.style.lineBreak = "anywhere";
            inputEl.style.hyphens = "none";
            inputEl.style.scrollbarWidth = "none";

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

            const padLeftPx = Math.max(0, (textPadLeft - 0.5) * scale);
            const padRightPx = Math.max(0, (textPadRight - 0.5) * scale);
            const padTopPx = Math.max(0, textPadTop * scale);
            inputEl.style.padding = `${padTopPx}px ${padRightPx}px 0px ${padLeftPx}px`;
            inputEl.style.lineHeight = (16 * scale) + "px";

            inputEl.style.zIndex = "90000";
            inputEl.style.outline = "none";
            inputEl.style.boxShadow = "0 0 10px rgba(139, 92, 246, 0.6)";

            inputEl.addEventListener("wheel", function(e) {
                e.stopPropagation();
            }, { passive: false });

            document.body.appendChild(inputEl);
            const targetContentW = Math.max(20, wWidth - 9.5) * scale;
            const calibratedPadRight = Math.max(0, inputEl.clientWidth - padLeftPx - targetContentW);
            inputEl.style.padding = `${padTopPx}px ${calibratedPadRight}px 0px ${padLeftPx}px`;

            let isMounting = true;
            setTimeout(() => {
                isMounting = false;
                inputEl.focus();
                const len = inputEl.value.length;
                inputEl.setSelectionRange(len, len);
                const curScale = canvas.ds ? canvas.ds.scale : scale;
                const linePx = 16 * curScale;
                if (widget && typeof widget._scroll_line === "number" && widget._scroll_line > 0) {
                    inputEl.scrollTop = widget._scroll_line * linePx;
                } else {
                    inputEl.scrollTop = 0;
                }
            }, 30);

            inputEl.oninput = function() {
                const cleanVal = String(inputEl.value || "").replace(/\r/g, "");
                if (node.properties && propKey) node.properties[propKey] = cleanVal;
                if (widget) {
                    widget.value = cleanVal;
                    delete widget._cached_wrap_text;
                }

                if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                if (canvas.draw) canvas.draw(true, true);

                const newRect = canvas.canvas.getBoundingClientRect();
                const newScale = canvas.ds ? canvas.ds.scale : 1.0;
                const newOffset = canvas.ds ? canvas.ds.offset : [0, 0];
                const newW = getInlineBoxWidth(node, widget, titleName, propertyName);
                const newH = (node && node.size && node.size[1]) ? Math.max(38, node.size[1] - drawY - 8) : 38;

                const curHalfStroke = 0.75 * newScale;
                const newScreenX = newRect.left + (node.pos[0] + margin + newOffset[0]) * newScale - curHalfStroke;
                const newScreenY = newRect.top + (node.pos[1] + drawY + newOffset[1]) * newScale - curHalfStroke;
                const newScreenW = (newW * newScale) + (1.5 * newScale);
                const newScreenH = (newH * newScale) + (1.5 * newScale);

                inputEl.style.left = newScreenX + "px";
                inputEl.style.top = newScreenY + "px";
                inputEl.style.width = newScreenW + "px";
                inputEl.style.height = newScreenH + "px";
                inputEl.style.borderRadius = (5 * newScale) + "px";
                inputEl.style.border = (1.5 * newScale) + "px solid #8b5cf6";
                inputEl.style.fontSize = (11 * newScale) + "px";
                const curPadLeftPx = Math.max(0, (textPadLeft - 0.5) * newScale);
                const curTargetContentW = Math.max(20, newW - 9.5) * newScale;
                const curPadRightPx = Math.max(0, inputEl.clientWidth - curPadLeftPx - curTargetContentW);
                const curPadTopPx = Math.max(0, textPadTop * newScale);
                inputEl.style.padding = `${curPadTopPx}px ${curPadRightPx}px 0px ${curPadLeftPx}px`;
                inputEl.style.lineHeight = (16 * newScale) + "px";
            };

            function saveAndClose() {
                const curScale = canvas.ds ? canvas.ds.scale : scale;
                const linePx = 16 * curScale;
                if (widget) {
                    if (linePx > 0) {
                        widget._scroll_line = Math.max(0, Math.round(inputEl.scrollTop / linePx));
                    }
                    delete widget._is_inline_editing;
                    delete widget._cached_wrap_text;
                }
                const cleanVal = String(inputEl.value || "").replace(/\r/g, "");
                if (node.properties && propKey) node.properties[propKey] = cleanVal;
                widget.value = cleanVal;

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
                    if (e.shiftKey) {
                        return;
                    }
                    e.preventDefault();
                    e.stopPropagation();
                    saveAndClose();
                } else if (e.key === "Escape") {
                    e.preventDefault();
                    e.stopPropagation();
                    if (node.properties && propKey) node.properties[propKey] = curVal;
                    if (widget) {
                        widget.value = curVal;
                        delete widget._is_inline_editing;
                        delete widget._cached_wrap_text;
                    }
                    inputEl.onblur = null;
                    inputEl.remove();
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

        function setupValueUnitTextWidget(node, widget, titleName, propertyName) {
            if (!widget) return;

            widget.type = "custom";
            const propKey = propertyName || widget.property || "value";
            widget.property = propKey;

            widget.isPointInside = function(x, y, n) {
                const targetNode = n || node;
                const margin = (widget._boxX !== undefined) ? widget._boxX : 28;
                const nodeWidth = (targetNode && targetNode.size && targetNode.size[0]) ? targetNode.size[0] : 184;
                const wWidth = getInlineBoxWidth(targetNode, widget, titleName, propertyName, nodeWidth);
                const drawY = (widget.last_y !== undefined) ? widget.last_y : ((widget.y !== undefined) ? widget.y : 11);
                const maxAllowedH = (targetNode && targetNode.size && targetNode.size[1]) ? Math.max(38, targetNode.size[1] - drawY - 8) : 38;
                const wHeight = (widget._boxH !== undefined) ? widget._boxH : maxAllowedH;
                return x >= margin && x <= margin + wWidth && y >= drawY && y <= drawY + wHeight;
            };

            widget.mouse = function(event, pos, node) {
                if (event.type === "mousedown" || event.type === "click") {
                    if (pos && widget.isPointInside && !widget.isPointInside(pos[0], pos[1], node)) {
                        return false;
                    }
                    if (widget._scrollbar_info && pos) {
                        const sb = widget._scrollbar_info;
                        if (pos[0] >= sb.barX - 6 && pos[0] <= sb.barX + sb.barW + 6 && pos[1] >= sb.trackY && pos[1] <= sb.trackY + sb.trackH) {
                            const ratio = Math.max(0, Math.min(1, (pos[1] - sb.trackY) / sb.trackH));
                            widget._scroll_line = Math.round(ratio * sb.maxScroll);
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            const activeCanvas = (typeof LGraphCanvas !== "undefined" && LGraphCanvas.active_canvas);
                            if (activeCanvas && activeCanvas.draw) activeCanvas.draw(true, true);
                            return true;
                        }
                    }
                    openInlineValueUnitEditor(node, widget, propKey, titleName, event);
                    return true;
                }
            };

            widget.callback = function(value, canvas, node, pos, event) {
                openInlineValueUnitEditor(node, widget, propKey, titleName, event);
            };

            widget.computeSize = function(width) {
                const wWidth = getInlineBoxWidth(node, widget, titleName, propertyName, width);
                const drawY = (widget.last_y !== undefined) ? widget.last_y : ((widget.y !== undefined) ? widget.y : 11);
                const maxAllowedH = (node && node.size && node.size[1]) ? Math.max(38, node.size[1] - drawY - 8) : 38;
                return [wWidth + 22, maxAllowedH];
            };

            widget.draw = function(ctx, node, width, y, height) {
                const drawY = (widget.last_y !== undefined) ? widget.last_y : ((widget.y !== undefined) ? widget.y : y);
                const curVal = String((node.properties && propKey && node.properties[propKey] !== undefined)
                    ? node.properties[propKey]
                    : (widget.value !== undefined ? widget.value : ""));

                const margin = (widget._boxX !== undefined) ? widget._boxX : 28;
                const wWidth = getInlineBoxWidth(node, widget, titleName, propertyName, width);
                const rawDisp = widget.name || titleName || "Value";
                let dispText = curVal.length > 0 ? curVal : ((window.PyxisI18n && window.PyxisI18n.translateSlot) ? window.PyxisI18n.translateSlot(rawDisp) : rawDisp);

                const textPadLeft = 6;
                const textPadRight = 6;
                const textPadTop = 2.5;
                const textToWrap = curVal.length > 0 ? curVal : dispText;

                const maxAllowedH = (node && node.size && node.size[1]) ? Math.max(38, node.size[1] - drawY - 8) : 38;
                const wHeight = maxAllowedH;
                widget._boxH = wHeight;
                const borderRadius = 5;

                const lineH = 16;
                const availableH = wHeight - 6;
                const maxVisibleLines = Math.max(1, Math.floor(availableH / lineH));

                // Exact inner content width matching textarea layout box ((wWidth + 1.5) - 2px border - 11px padding = wWidth - 9.5)
                const availableTextW = Math.max(20, wWidth - 9.5);

                let wrappedLines = null;
                if (widget._cached_wrap_text === textToWrap &&
                    typeof widget._cached_wrap_w === "number" &&
                    Math.abs(widget._cached_wrap_w - availableTextW) < 0.5 &&
                    Array.isArray(widget._cached_wrapped_lines)) {
                    wrappedLines = widget._cached_wrapped_lines;
                } else {
                    wrappedLines = typeof wrapTextToPixelWidth === "function"
                        ? wrapTextToPixelWidth(textToWrap, availableTextW, "bold 11px Consolas, monospace")
                        : [textToWrap];
                    widget._cached_wrap_text = textToWrap;
                    widget._cached_wrap_w = availableTextW;
                    widget._cached_wrapped_lines = wrappedLines;
                }

                ctx.save();
                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = "#8b5cf6";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(margin, drawY, wWidth, wHeight, borderRadius);
                else ctx.rect(margin, drawY, wWidth, wHeight);
                ctx.fill();
                if (!widget._is_inline_editing) {
                    ctx.stroke();
                }

                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(margin + 2, drawY + 2, wWidth - 4, wHeight - 4, Math.max(4, borderRadius - 2));
                else ctx.rect(margin + 2, drawY + 2, wWidth - 4, wHeight - 4);
                ctx.clip();

                if (!widget._is_inline_editing) {
                    ctx.fillStyle = curVal.length > 0 ? "#a7f3d0" : "#64748b";
                    ctx.font = "bold 11px Consolas, monospace";
                    ctx.textAlign = "left";

                    const totalLines = wrappedLines.length;
                    const isOverflowing = totalLines > maxVisibleLines;
                    const maxScroll = Math.max(0, totalLines - maxVisibleLines);
                    widget._max_scroll_lines = maxScroll;

                    if (widget._scroll_line === undefined || isNaN(widget._scroll_line)) {
                        widget._scroll_line = 0;
                    } else {
                        widget._scroll_line = Math.max(0, Math.min(widget._scroll_line, maxScroll));
                    }

                    const startLine = widget._scroll_line;

                    for (let lineIdx = 0; lineIdx < maxVisibleLines; lineIdx++) {
                        const curIdx = startLine + lineIdx;
                        if (curIdx >= totalLines) break;
                        let lineTxt = wrappedLines[curIdx] || "";
                        if (isOverflowing && lineIdx === maxVisibleLines - 1 && curIdx < totalLines - 1) {
                            if (!lineTxt.endsWith("...")) {
                                lineTxt = lineTxt.length > 18 ? (lineTxt.substring(0, lineTxt.length - 3) + "...") : (lineTxt + "...");
                            }
                        }
                        ctx.fillText(lineTxt, margin + textPadLeft, drawY + textPadTop + 11.5 + lineIdx * lineH);
                    }
                }
                ctx.restore();

                // Minimalist scrollbar
                if (!widget._is_inline_editing && wrappedLines && wrappedLines.length > 1) {
                    const totalLines = wrappedLines.length;
                    const isOverflowing = totalLines > maxVisibleLines;
                    if (isOverflowing) {
                        const maxScroll = Math.max(0, totalLines - maxVisibleLines);
                        const trackPadding = 3;
                        const barW = 3.5;
                        const barX = margin + wWidth - barW - 3;
                        const trackY = drawY + trackPadding;
                        const trackH = Math.max(8, wHeight - trackPadding * 2);

                        widget._scrollbar_info = { barX, barW, trackY, trackH, maxScroll, boxX: margin, boxY: drawY, boxW: wWidth, boxH: wHeight };

                        ctx.save();
                        ctx.fillStyle = "rgba(255, 255, 255, 0.05)";
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(barX, trackY, barW, trackH, barW / 2);
                        else ctx.rect(barX, trackY, barW, trackH);
                        ctx.fill();

                        const thumbH = Math.max(8, Math.round((maxVisibleLines / totalLines) * trackH));
                        const maxTravel = trackH - thumbH;
                        const curScroll = widget._scroll_line || 0;
                        const thumbY = trackY + (maxScroll > 0 ? (curScroll / maxScroll) * maxTravel : 0);

                        ctx.fillStyle = "rgba(139, 92, 246, 0.6)";
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(barX, thumbY, barW, thumbH, barW / 2);
                        else ctx.rect(barX, thumbY, barW, thumbH);
                        ctx.fill();
                        ctx.restore();
                    } else {
                        delete widget._scrollbar_info;
                    }
                }
            };
        }

        function setupValueUnitNode(node) {
            if (!node) return;
            const titleStr = String(node.title || node.type || "");
            const isNumberNode = titleStr.includes("Number") || titleStr.includes("Número");
            const propKey = "value";
            if (!node.properties) node.properties = {};
            if (node.properties[propKey] === undefined) {
                node.properties[propKey] = "";
            }

            node.widgets = [];
            const curVal = String(node.properties[propKey]);
            const w = node.addWidget("text", "Value", curVal, function(val) {
                const cleanVal = String(val || "").replace(/\r/g, "");
                node.properties[propKey] = cleanVal;
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            });
            w.property = propKey;
            w.y = 11;
            w.last_y = 11;
            w._boxX = 28;
            setupValueUnitTextWidget(node, w, "Value", propKey);

            node.computeSize = function() {
                const canvas = (this.graph && this.graph.canvas) || (typeof LGraphCanvas !== "undefined" && LGraphCanvas.active_canvas);
                const isResizingThis = !!(canvas && canvas.resizing_node === this);
                if (isResizingThis) {
                    return [184, 60];
                }

                const defaultW = 184;
                const defaultH = 60;
                const curW = (this._manual_width !== undefined) ? this._manual_width : defaultW;
                const curH = (this._manual_height !== undefined) ? this._manual_height : defaultH;
                return [Math.max(184, curW), Math.max(60, curH)];
            };

            node.onResize = function(size) {
                size[0] = Math.max(184, size[0]);
                size[1] = Math.max(60, size[1]);
                this._manual_width = size[0];
                this._manual_height = size[1];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                if (this.widgets && this.widgets[0]) {
                    this.widgets[0].y = 11;
                    this.widgets[0].last_y = 11;
                    this.widgets[0]._boxX = 28;
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [this.size[0] - 10, 20];
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (info && info.size && Array.isArray(info.size)) {
                    this._manual_width = info.size[0];
                    this._manual_height = info.size[1];
                    this.size = [info.size[0], info.size[1]];
                }
                if (this.widgets && this.widgets[0]) {
                    const pKey = this.widgets[0].property || propKey;
                    if (this.properties && this.properties[pKey] !== undefined) {
                        this.widgets[0].value = String(this.properties[pKey]);
                    }
                }
                if (this.computeSize) this.size = this.computeSize();
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            if (node._manual_width === undefined && node._manual_height === undefined) {
                node.size = [184, 60];
            } else if (node.computeSize) {
                node.size = node.computeSize();
            }
            if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
        }


        function setupDynamicFormatNode(node) {
            if (!node) return;
            if (!node.properties) node.properties = {};
            if (node.properties.format === undefined) node.properties.format = "%s";
            if (node.properties.Formato !== undefined) delete node.properties.Formato;
            node.properties.expandable = true;
            node.widgets_up = true;

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const valStr = String(props.format !== undefined ? props.format : "%s");
                const textWidth = getExactTextWidth(valStr, "bold 11px Consolas, monospace");
                const rightReserve = (typeof getNodeRightReserve === "function") ? getNodeRightReserve(this) : 24;
                const reqW = Math.max(180, Math.ceil(textWidth + 48 + rightReserve));
                const count = (this.inputs || node.inputs) ? (this.inputs || node.inputs).length : 1;
                const reqH = 60 + (count - 1) * 20 + 36;
                return [reqW, reqH];
            };

            node.updateFormatDinamicoInputs = function(targetCount) {
                let count = targetCount;
                if (count === undefined) {
                    count = 0;
                    if (this.inputs) {
                        for (let i = 0; i < this.inputs.length; i++) {
                            if (this.inputs[i].name && this.inputs[i].name.startsWith("In")) count++;
                        }
                    }
                    if (count < 1) count = 1;
                }

                if (!this.inputs) this.inputs = [];

                for (let i = 1; i <= count; i++) {
                    const name = "In" + i;
                    const exists = this.inputs.some(inp => inp.name === name);
                    if (!exists) {
                        this.addInput(name, "data");
                    }
                }

                for (let i = this.inputs.length - 1; i >= 0; i--) {
                    const inp = this.inputs[i];
                    if (inp.name && inp.name.startsWith("In")) {
                        const num = parseInt(inp.name.substring(2));
                        if (num > count) {
                            this.removeInput(i);
                        }
                    } else if (inp.name === "Formato") {
                        this.removeInput(i);
                    }
                }

                if (!this.outputs || this.outputs.length === 0) {
                    this.addOutput("String", "data");
                }

                for (let i = 0; i < this.inputs.length; i++) {
                    const dotY = 60 + i * 20;
                    this.inputs[i].name = "In" + (i + 1);
                    this.inputs[i].label = " ";
                    this.inputs[i].pos = [10, dotY];
                }

                this.widgets = [];
                const curVal = String(this.properties.format !== undefined ? this.properties.format : "%s");
                const w = this.addWidget("text", "Format", curVal, value => {
                    const cleanVal = String(value || "").replace(/[\r\n]+/g, " ");
                    this.properties.format = cleanVal;
                    if (this.properties.Formato !== undefined) delete this.properties.Formato;
                    if (this.computeSize) {
                        this.size = this.computeSize();
                    }
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                });
                w.property = "format";
                w.y = 32;
                w.last_y = 32;
                setupSingleLineTextWidget(this, w, "Format", "format");

                if (this.computeSize) {
                    this.size = this.computeSize();
                }
            };

            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos) {
                    if (local_pos[1] >= 4 && local_pos[1] <= 26) {
                        const plusBtnX = 22;
                        const plusBtnW = 26;
                        const minusBtnX = 54;
                        const minusBtnW = 26;

                        if (local_pos[0] >= plusBtnX - 2 && local_pos[0] <= plusBtnX + plusBtnW + 2) {
                            const curCount = this.inputs ? this.inputs.length : 1;
                            this.updateFormatDinamicoInputs(curCount + 1);
                            if (this.computeSize) this.size = this.computeSize();
                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            const activeCanvas = LGraphCanvas.active_canvas || canvas;
                            if (activeCanvas) activeCanvas.setDirty(true, true);
                            if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("add-input-format");
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        }

                        if (local_pos[0] >= minusBtnX - 2 && local_pos[0] <= minusBtnX + minusBtnW + 2) {
                            const curCount = this.inputs ? this.inputs.length : 1;
                            if (curCount > 1) {
                                this.updateFormatDinamicoInputs(curCount - 1);
                                if (this.computeSize) this.size = this.computeSize();
                                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                                const activeCanvas = LGraphCanvas.active_canvas || canvas;
                                if (activeCanvas) activeCanvas.setDirty(true, true);
                                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("remove-input-format");
                                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                                return true;
                            }
                        }
                    }
                }
            };

            node.onDrawForeground = function(ctx) {
                if (this.flags && this.flags.collapsed) return;
                const nodeW = this.size[0];

                ctx.save();

                const headerY = 6;
                const btnH = 18;
                const plusBtnX = 22;
                const plusBtnW = 26;
                const minusBtnX = 54;
                const minusBtnW = 26;

                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = "#10b981";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(plusBtnX, headerY, plusBtnW, btnH, 5);
                else ctx.rect(plusBtnX, headerY, plusBtnW, btnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = "#a7f3d0";
                ctx.font = "bold 12px monospace";
                ctx.textAlign = "center";
                ctx.fillText("+", plusBtnX + plusBtnW / 2, headerY + 13);

                const canRemove = this.inputs && (this.inputs.length > 1);
                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = canRemove ? "#ef4444" : "#4b5563";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(minusBtnX, headerY, minusBtnW, btnH, 5);
                else ctx.rect(minusBtnX, headerY, minusBtnW, btnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = canRemove ? "#fca5a5" : "#64748b";
                ctx.fillText("-", minusBtnX + minusBtnW / 2, headerY + 13);

                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [nodeW - 10, 15];
                }

                if (this.widgets && this.widgets[0]) {
                    this.widgets[0].y = 32;
                    this.widgets[0].last_y = 32;
                }

                const count = this.inputs ? this.inputs.length : 1;
                ctx.font = "bold 11px monospace";
                ctx.textAlign = "left";
                for (let i = 0; i < count; i++) {
                    const dotY = 60 + i * 20;
                    if (this.inputs[i]) {
                        this.inputs[i].label = " ";
                        this.inputs[i].pos = [10, dotY];
                    }
                    ctx.fillStyle = "#94a3b8";
                    ctx.fillText("In" + (i + 1), 22, dotY + 4);
                }

                ctx.restore();
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (this.widgets && this.widgets[0] && this.properties && this.properties.Formato !== undefined) {
                    this.widgets[0].value = String(this.properties.Formato);
                }
                this.updateFormatDinamicoInputs();
                if (this.computeSize) this.size = this.computeSize();
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            node.updateFormatDinamicoInputs();
        }


        function openOnceInlineEditor(node, canvas) {
            const activeCanvas = canvas || LGraphCanvas.active_canvas;
            if (!activeCanvas) return;
            const canvasEl = activeCanvas.canvas;
            if (!canvasEl) return;

            const existing = document.getElementById("pyxis-inline-text-editor");
            if (existing) {
                if (typeof existing._saveAndClose === "function") existing._saveAndClose();
                else existing.remove();
            }

            const curVal = String(node.properties.iterator !== undefined ? node.properties.iterator : "j");
            const box = (typeof node.getBoxCoords === "function") ? node.getBoxCoords() : { x: 42, y: 4, w: 100, h: 18 };

            const offset = activeCanvas.ds ? activeCanvas.ds.offset : [0, 0];
            const scale = activeCanvas.ds ? activeCanvas.ds.scale : 1.0;
            const rect = canvasEl.getBoundingClientRect();

            const screenX = rect.left + (node.pos[0] + box.x + offset[0]) * scale;
            const screenY = rect.top + (node.pos[1] + box.y + offset[1]) * scale;
            const screenW = box.w * scale;
            const screenH = box.h * scale;

            const inputEl = document.createElement("input");
            inputEl.id = "pyxis-inline-text-editor";
            inputEl.name = "pyxis-once-text-editor";
            inputEl.type = "text";
            inputEl.value = curVal;
            inputEl.placeholder = "j";
            inputEl.autocomplete = "off";
            inputEl.spellcheck = false;

            const modo = String(node.properties.mode || "loop").toLowerCase();
            node.properties.mode = modo;
            if (node.properties.modo !== undefined) delete node.properties.modo;
            const theme = (typeof getOnceThemeConfig === "function") ? getOnceThemeConfig(modo) : { color: "#f97316", glow: "rgba(249, 115, 22, 0.5)" };
            const padLeft = Math.max(4, Math.round(8 * scale));
            const padRight = Math.max(2, Math.round(6 * scale));

            Object.assign(inputEl.style, {
                position: "fixed",
                left: Math.round(screenX) + "px",
                top: Math.round(screenY) + "px",
                width: Math.round(screenW) + "px",
                height: Math.round(screenH) + "px",
                background: "#12161f",
                color: "#a7f3d0",
                border: Math.max(1, 1.5 * scale) + "px solid #8b5cf6",
                borderRadius: Math.round(5 * scale) + "px",
                boxShadow: "0 0 10px rgba(139, 92, 246, 0.6)",
                fontFamily: "Consolas, monospace",
                fontWeight: "bold",
                fontSize: Math.max(9, Math.round(11 * scale)) + "px",
                padding: "0 " + padRight + "px 0 " + padLeft + "px",
                lineHeight: Math.round(screenH - 3 * scale) + "px",
                boxSizing: "border-box",
                zIndex: "90000",
                outline: "none",
                textAlign: "left"
            });

            document.body.appendChild(inputEl);
            node._editing_iter = true;
            if (activeCanvas.draw) activeCanvas.draw(true, true);

            let isMounting = true;
            setTimeout(() => {
                isMounting = false;
                inputEl.focus();
                inputEl.select();
            }, 30);

            let isClosed = false;
            function saveAndClose() {
                if (isClosed) return;
                isClosed = true;
                delete node._editing_iter;
                const cleanVal = String(inputEl.value || "").replace(/[\r\n]+/g, " ").trim() || "j";
                node.properties.iterator = cleanVal;
                if (node.properties.iterador !== undefined) delete node.properties.iterador;
                node.size = node.computeSize();

                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (activeCanvas.setDirty) activeCanvas.setDirty(true, true);
                if (activeCanvas.draw) activeCanvas.draw(true, true);
                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("once-edit-iterator");
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
                    delete node._editing_iter;
                    node.properties.iterator = curVal;
                    if (node.properties.iterador !== undefined) delete node.properties.iterador;
                    inputEl.onblur = null;
                    if (inputEl.parentNode) inputEl.parentNode.removeChild(inputEl);
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                    if (activeCanvas.setDirty) activeCanvas.setDirty(true, true);
                    if (activeCanvas.draw) activeCanvas.draw(true, true);
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

        function setupOnceNode(node) {
            if (!node) return;
            node.resizable = false;
            if (node.flags) {
                node.flags.resizable = false;
                node.flags.hide_resize = true;
            }
            node._custom_collapsed_width = 115;
            node._collapsed_width = 115;
            node.hide_collapsed_slots = true;
            node.hide_help_button = true;
            if (!node.properties) node.properties = {};
            const initialOnceMode = node.properties.mode || "line";
            const initialOnceIter = node.properties.iterator !== undefined ? node.properties.iterator : "j";
            node.properties.mode = initialOnceMode;
            node.properties.iterator = initialOnceIter;
            if (node.properties.modo !== undefined) delete node.properties.modo;
            if (node.properties.iterador !== undefined) delete node.properties.iterador;

            if (!node.inputs || node.inputs.length === 0) {
                node.addInput("", 0);
            }
            if (node.inputs && node.inputs[0]) {
                node.inputs[0].name = "";
                node.inputs[0].label = "";
            }
            if (!node.outputs || node.outputs.length === 0) {
                node.addOutput("", 0);
            }
            if (node.outputs && node.outputs[0]) {
                node.outputs[0].name = "";
                node.outputs[0].label = "";
            }

            function hexToRgba(hex, alpha) {
                if (!hex || typeof hex !== "string") return `rgba(255, 255, 255, ${alpha})`;
                let clean = hex.replace("#", "").trim();
                if (clean.length === 3) {
                    clean = clean[0] + clean[0] + clean[1] + clean[1] + clean[2] + clean[2];
                }
                const num = parseInt(clean, 16);
                if (isNaN(num) || clean.length !== 6) return `rgba(255, 255, 255, ${alpha})`;
                const r = (num >> 16) & 255;
                const g = (num >> 8) & 255;
                const b = num & 255;
                return `rgba(${r}, ${g}, ${b}, ${alpha})`;
            }

            function getOnceThemeConfig(modo) {
                const pt = window.PYXIS_THEME || {};
                const pal = Array.isArray(pt.colors) ? pt.colors : [];
                const cats = pt.categories || {};
                const pri = pt.accentPrimary || "#10b981";
                const priEnd = pt.accentPrimaryEnd || "#3b82f6";
                const sec = pt.accentSecondary || "#6366f1";
                const secGlow = pt.accentSecondaryGlow || sec;

                let color = "#00f0ff";
                let label = "LINE";

                switch (modo) {
                    case "global":
                        color = pal[0] || pri || "#f59e0b";
                        label = "GLOBAL";
                        break;
                    case "line":
                        color = secGlow || pal[1] || "#00f0ff";
                        label = "LINE";
                        break;
                    case "word":
                        color = pal[2] || (cats["Text"] && cats["Text"].color) || "#10b981";
                        label = "WORD";
                        break;
                    case "syl":
                        color = pal[3] || (cats["Math"] && cats["Math"].color) || "#a855f7";
                        label = "SYL";
                        break;
                    case "char":
                        color = pal[4] || (cats["Variables"] && cats["Variables"].color) || priEnd || "#f43f5e";
                        label = "CHAR";
                        break;
                    case "loop":
                        color = (cats["Loops"] && cats["Loops"].color) || (window.CATEGORY_COLORS && window.CATEGORY_COLORS["Loops"]) || "#f97316";
                        label = "LOOP";
                        break;
                    default:
                        color = pri;
                        label = String(modo || "LINE").toUpperCase();
                        break;
                }

                return {
                    color: color,
                    glow: hexToRgba(color, 0.5),
                    label: label
                };
            }

            const ONCE_MODES = ["global", "line", "word", "syl", "char", "loop"];

            node.getBoxCoords = function() {
                const nodeW = this.size ? this.size[0] : 194;
                const trayX = 26;
                const trayW = Math.max(100, nodeW - 52);
                const boxX = trayX + 10;
                const boxY = 4;
                const boxW = trayW - 20;
                const boxH = 18;
                return {
                    trayX: trayX,
                    trayW: trayW,
                    trayY: -8,
                    trayBottom: 26,
                    trayH: 34,
                    x: boxX,
                    y: boxY,
                    w: boxW,
                    h: boxH
                };
            };

            node.computeSize = function() {
                if (this.flags && this.flags.collapsed) {
                    return [115, 0];
                }
                const modo = String(this.properties.mode || "line").toLowerCase();
                const theme = getOnceThemeConfig(modo);
                const titleW = getExactTextWidth("ONCE", "bold 12px sans-serif");
                const modeTextW = getExactTextWidth(theme.label, "bold 10px sans-serif");
                const modeBtnW = Math.max(66, modeTextW + 26);
                const modeBtnX = Math.round(48 + titleW + 10);
                const req_w = modeBtnX + modeBtnW + 32;
                const req_h = (modo === "loop") ? 28 : 2;
                return [req_w, req_h];
            };

            const origCollapse = node.collapse;
            node.collapse = function(force) {
                if (origCollapse) origCollapse.call(this, force);
                if (this.flags && this.flags.collapsed) {
                    this._collapsed_width = 115;
                    this.size = [115, 0];
                } else {
                    this.size = this.computeSize();
                }
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            if (typeof LGraphCanvas !== "undefined" && LGraphCanvas.prototype && !LGraphCanvas.prototype._pyxis_once_shape_hooked) {
                LGraphCanvas.prototype._pyxis_once_shape_hooked = true;
                const origDrawNodeShape = LGraphCanvas.prototype.drawNodeShape;
                LGraphCanvas.prototype.drawNodeShape = function(node, ctx, size, fgcolor, bgcolor, selected, mouse_over) {
                    if (node && (node.type === "Once" || node.type === "Functions/Once" || node.type === "Basics/Once" || (node.title && node.title === "Once"))) {
                        if (typeof node.onDrawOnceCustomShape === "function") {
                            const handled = node.onDrawOnceCustomShape.call(node, ctx, size, fgcolor, bgcolor, selected, mouse_over, this);
                            if (handled) return;
                        }
                    }
                    if (node && (node.type === "Only" || node.type === "Functions/Only" || node.type === "Basics/Only" || (node.title && node.title === "Only"))) {
                        if (typeof node.onDrawOnlyCustomShape === "function") {
                            const handled = node.onDrawOnlyCustomShape.call(node, ctx, size, fgcolor, bgcolor, selected, mouse_over, this);
                            if (handled) return;
                        }
                    }
                    return origDrawNodeShape.apply(this, arguments);
                };
            }

            node.getTitle = function() {
                if (this.flags && this.flags.collapsed) return "Once";
                return "";
            };
            node.onDrawTitleBox = function() {};
            node.onDrawTitleText = function() {};
            node.onDrawTitleBar = function() {};

            node.onDrawOnceCustomShape = function(ctx, size, fgcolor, bgcolor, selected, mouse_over, canvas) {
                const modo = this.properties.mode || "line";
                const theme = getOnceThemeConfig(modo);
                const isCollapsed = Boolean(this.flags && this.flags.collapsed);
                const nodeW = size ? size[0] : (isCollapsed ? 115 : 210);

                ctx.save();

                const pt = window.PYXIS_THEME || {};
                const bgGradStart = (pt.nodeBgGradient && pt.nodeBgGradient.start) || "#1d2536";
                const bgGradEnd = (pt.nodeBgGradient && pt.nodeBgGradient.end) || "#0d111a";

                const centerY = -15;

                const pillH = 32;
                const pillY = centerY - pillH / 2;
                const pillX = 0;
                const pillW = nodeW;
                const pillR = 16;

                function drawSocketRing(sx, sy) {
                    ctx.save();
                    ctx.strokeStyle = "rgba(0, 0, 0, 0.6)";
                    ctx.lineWidth = 2.5;
                    ctx.beginPath();
                    ctx.arc(sx, sy, 7.5, 0, Math.PI * 2);
                    ctx.stroke();

                    ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.arc(sx, sy, 8.5, 0, Math.PI * 2);
                    ctx.stroke();
                    ctx.restore();
                }

                if (isCollapsed) {
                    this._collapsed_width = 115;

                    const plugGrad = ctx.createLinearGradient(0, pillY, 0, pillY + pillH);
                    plugGrad.addColorStop(0, bgGradStart);
                    plugGrad.addColorStop(1, bgGradEnd);
                    ctx.fillStyle = plugGrad;
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(pillX, pillY, pillW, pillH, pillR);
                    else ctx.rect(pillX, pillY, pillW, pillH);
                    ctx.fill();
                    ctx.stroke();

                    const sheenGrad = ctx.createLinearGradient(0, pillY, 0, pillY + 10);
                    sheenGrad.addColorStop(0, "rgba(255, 255, 255, 0.10)");
                    sheenGrad.addColorStop(1, "rgba(255, 255, 255, 0.0)");
                    ctx.fillStyle = sheenGrad;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(pillX + 2, pillY + 1, pillW - 4, 10, [pillR, pillR, 0, 0]);
                    ctx.fill();

                    drawSocketRing(12, centerY);
                    drawSocketRing(pillW - 12, centerY);
                    if (this.inputs && this.inputs[0]) this.inputs[0].pos = [12, centerY];
                    if (this.outputs && this.outputs[0]) this.outputs[0].pos = [pillW - 12, centerY];

                    ctx.fillStyle = "#e2e8f0";
                    ctx.beginPath();
                    ctx.arc(26, centerY, 4, 0, Math.PI * 2);
                    ctx.fill();

                    ctx.font = "bold 11px sans-serif";
                    ctx.fillStyle = "#ffffff";
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    ctx.fillText("ONCE", 38, centerY + 1.2);

                    ctx.save();
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    ctx.shadowColor = theme.glow;
                    ctx.shadowBlur = 6;
                    ctx.fillStyle = theme.color;
                    ctx.beginPath();
                    ctx.arc(pillW - 28, centerY, 3.5, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();

                    if (selected) {
                        ctx.save();
                        ctx.globalAlpha = 0.40;
                        ctx.strokeStyle = theme.color;
                        ctx.shadowOffsetX = 0;
                        ctx.shadowOffsetY = 0;
                        ctx.shadowColor = theme.color;
                        ctx.shadowBlur = 6;
                        ctx.lineWidth = 1.5;
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(pillX - 2, pillY - 2, pillW + 4, pillH + 4, pillR + 2);
                        else ctx.rect(pillX - 2, pillY - 2, pillW + 4, pillH + 4);
                        ctx.stroke();
                        ctx.restore();
                    }

                    ctx.restore();
                    return true;
                }


                if (modo === "loop") {
                    const box = (typeof this.getBoxCoords === "function") ? this.getBoxCoords() : {
                        trayX: 26, trayW: Math.max(120, nodeW - 52), trayY: -8, trayBottom: 26, trayH: 34,
                        x: 42, y: 4, w: Math.max(120, nodeW - 52) - 32, h: 18
                    };

                    const trayGrad = ctx.createLinearGradient(0, box.trayY, 0, box.trayBottom);
                    trayGrad.addColorStop(0, "#080b12");
                    trayGrad.addColorStop(1, "#0e1420");
                    ctx.fillStyle = (pt.cardBg && pt.cardBg !== "transparent") ? pt.cardBg : trayGrad;
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(box.trayX, box.trayY, box.trayW, box.trayH, [0, 0, 6, 6]);
                    else ctx.rect(box.trayX, box.trayY, box.trayW, box.trayH);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
                    ctx.fillRect(box.trayX + 1, 1, 3, box.trayBottom - 1);
                    ctx.fillRect(box.trayX + box.trayW - 4, 1, 3, box.trayBottom - 1);

                    ctx.save();
                    ctx.strokeStyle = theme.color;
                    ctx.globalAlpha = 0.45;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(box.trayX + 6, 1);
                    ctx.lineTo(box.trayX + box.trayW - 6, 1);
                    ctx.stroke();
                    ctx.restore();

                    ctx.fillStyle = "#12161f";
                    ctx.strokeStyle = this._editing_iter ? "#8b5cf6" : "rgba(255, 255, 255, 0.22)";
                    ctx.lineWidth = this._editing_iter ? 1.5 : 1;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(box.x, box.y, box.w, box.h, 5);
                    else ctx.rect(box.x, box.y, box.w, box.h);
                    ctx.fill();
                    ctx.stroke();

                    if (!this._editing_iter) {
                        ctx.save();
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(box.x + 2, box.y + 2, box.w - 4, box.h - 4, 3);
                        else ctx.rect(box.x + 2, box.y + 2, box.w - 4, box.h - 4);
                        ctx.clip();

                        const iterVal = String(this.properties.iterator !== undefined ? this.properties.iterator : "j");
                        const textPadLeft = 8;
                        const textY = box.y + box.h / 2 + 0.5;

                        ctx.font = "bold 11px Consolas, monospace";
                        ctx.fillStyle = "#64748b";
                        ctx.textAlign = "left";
                        ctx.textBaseline = "middle";
                        ctx.fillText("iter:", box.x + textPadLeft, textY);

                        const labelW = ctx.measureText("iter:").width;
                        ctx.save();
                        ctx.shadowOffsetX = 0;
                        ctx.shadowOffsetY = 0;
                        ctx.font = "bold 11px Consolas, monospace";
                        ctx.fillStyle = "#a7f3d0";
                        ctx.shadowColor = "rgba(167, 243, 208, 0.5)";
                        ctx.shadowBlur = 4;
                        ctx.fillText(iterVal, box.x + textPadLeft + labelW + 6, textY);
                        ctx.restore();

                        ctx.restore();
                    }
                }

                const plugGrad = ctx.createLinearGradient(0, pillY, 0, pillY + pillH);
                plugGrad.addColorStop(0, bgGradStart);
                plugGrad.addColorStop(1, bgGradEnd);
                ctx.fillStyle = plugGrad;
                ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
                ctx.lineWidth = 1;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(pillX, pillY, pillW, pillH, pillR);
                else ctx.rect(pillX, pillY, pillW, pillH);
                ctx.fill();
                ctx.stroke();

                const sheenGrad = ctx.createLinearGradient(0, pillY, 0, pillY + 10);
                sheenGrad.addColorStop(0, "rgba(255, 255, 255, 0.10)");
                sheenGrad.addColorStop(1, "rgba(255, 255, 255, 0.0)");
                ctx.fillStyle = sheenGrad;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(pillX + 2, pillY + 1, pillW - 4, 10, [pillR, pillR, 0, 0]);
                ctx.fill();

                drawSocketRing(14, centerY);
                drawSocketRing(nodeW - 14, centerY);

                ctx.fillStyle = "#e2e8f0";
                ctx.beginPath();
                ctx.arc(36, centerY, 4.5, 0, Math.PI * 2);
                ctx.fill();

                ctx.font = "bold 12px sans-serif";
                ctx.fillStyle = "#ffffff";
                ctx.textAlign = "left";
                ctx.textBaseline = "middle";
                const titleX = 48;
                ctx.fillText("ONCE", titleX, centerY + 1.2);
                const titleW = ctx.measureText("ONCE").width;

                ctx.font = "bold 10px sans-serif";
                const modeText = theme.label;
                const modeTextW = ctx.measureText(modeText).width;
                const modeBtnW = Math.max(66, modeTextW + 26);
                const modeBtnH = 20;
                const modeBtnX = Math.round(titleX + titleW + 10);
                const modeBtnY = centerY - modeBtnH / 2;

                ctx.save();
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 0;
                ctx.shadowColor = theme.glow;
                ctx.shadowBlur = 8;
                ctx.fillStyle = "#080c14";
                ctx.strokeStyle = theme.color;
                ctx.lineWidth = 1.4;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(modeBtnX, modeBtnY, modeBtnW, modeBtnH, 10);
                else ctx.rect(modeBtnX, modeBtnY, modeBtnW, modeBtnH);
                ctx.fill();
                ctx.stroke();
                ctx.restore();

                ctx.save();
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 0;
                ctx.shadowColor = theme.color;
                ctx.shadowBlur = 4;
                ctx.fillStyle = theme.color;
                ctx.beginPath();
                ctx.arc(modeBtnX + 10, centerY, 2.5, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();

                ctx.font = "bold 10px sans-serif";
                ctx.fillStyle = "#ffffff";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(modeText, modeBtnX + modeBtnW / 2 + 5, centerY + 1.2);

                if (selected) {
                    ctx.save();
                    ctx.globalAlpha = 0.40;
                    ctx.strokeStyle = theme.color;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    ctx.shadowColor = theme.color;
                    ctx.shadowBlur = 6;
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(pillX - 2, pillY - 2, pillW + 4, pillH + 4, pillR + 2);
                    else ctx.rect(pillX - 2, pillY - 2, pillW + 4, pillH + 4);
                    ctx.stroke();

                    if (modo === "loop") {
                        const box = (typeof this.getBoxCoords === "function") ? this.getBoxCoords() : { trayX: 26, trayW: Math.max(120, nodeW - 52), trayBottom: 26 };
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(box.trayX - 2, 0, box.trayW + 4, box.trayBottom + 2, [0, 0, 8, 8]);
                        else ctx.rect(box.trayX - 2, 0, box.trayW + 4, box.trayBottom + 2);
                        ctx.stroke();
                    }
                    ctx.restore();
                }

                ctx.restore();
                return true;
            };

            const oldDrawForeground = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDrawForeground) oldDrawForeground.call(this, ctx);
                const centerY = -15;

                if (this.flags && this.flags.collapsed) {
                    const colW = this._collapsed_width || 115;
                    if (this.inputs && this.inputs[0]) {
                        this.inputs[0].pos = [12, centerY];
                        this.inputs[0].name = "";
                        this.inputs[0].label = "";
                    }
                    if (this.outputs && this.outputs[0]) {
                        this.outputs[0].pos = [colW - 12, centerY];
                        this.outputs[0].name = "";
                        this.outputs[0].label = "";
                    }
                    return;
                }

                const nodeW = this.size ? this.size[0] : 210;

                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].pos = [14, centerY];
                    this.inputs[0].name = "";
                    this.inputs[0].label = "";
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [nodeW - 14, centerY];
                    this.outputs[0].name = "";
                    this.outputs[0].label = "";
                }
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                const lx = local_pos[0];
                const ly = local_pos[1];
                const centerY = -15;

                if (this.flags && this.flags.collapsed) {
                    const colW = this._collapsed_width || 115;
                    if (Math.hypot(lx - 26, ly - centerY) <= 8 || lx <= 42) {
                        this.collapse();
                        return true;
                    }
                    if (Math.hypot(lx - (colW - 28), ly - centerY) <= 8) {
                        const modo = this.properties.mode || "line";
                        let curIdx = ONCE_MODES.indexOf(modo);
                        if (curIdx < 0) curIdx = 1;
                        const nextMode = ONCE_MODES[(curIdx + 1) % ONCE_MODES.length];
                        this.properties.mode = nextMode;
                        if (this.properties.modo !== undefined) delete this.properties.modo;
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("once-mode-cycle");
                        return true;
                    }
                    if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
                    return;
                }

                const nodeW = this.size ? this.size[0] : 220;
                const modo = this.properties.mode || "line";
                const theme = getOnceThemeConfig(modo);

                if (Math.hypot(lx - 36, ly - centerY) <= 8) {
                    this.collapse();
                    return true;
                }

                if (ly <= 2) {
                    const activeCanvas = canvas || LGraphCanvas.active_canvas;
                    const textW = (activeCanvas && activeCanvas.ctx ? activeCanvas.ctx.measureText(theme.label).width : 50);
                    const titleW = (activeCanvas && activeCanvas.ctx ? activeCanvas.ctx.measureText("ONCE").width : 37);
                    const modeBtnW = Math.max(66, textW + 26);
                    const modeBtnX = Math.round(48 + titleW + 10);
                    const modeBtnY = centerY - 10;
                    const modeBtnH = 20;

                    if (lx >= modeBtnX - 3 && lx <= modeBtnX + modeBtnW + 3 && ly >= modeBtnY - 3 && ly <= modeBtnY + modeBtnH + 3) {
                        const existing = document.getElementById("pyxis-inline-text-editor");
                        if (existing && typeof existing._saveAndClose === "function") existing._saveAndClose();

                        let curIdx = ONCE_MODES.indexOf(modo);
                        if (curIdx < 0) curIdx = 1;
                        const nextIdx = (curIdx + 1) % ONCE_MODES.length;
                        const nextMode = ONCE_MODES[nextIdx];
                        this.properties.mode = nextMode;
                        if (this.properties.modo !== undefined) delete this.properties.modo;
                        if (this.computeSize) {
                            this.size = this.computeSize();
                        }
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("once-mode-cycle");
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        return true;
                    }
                }

                if (modo === "loop") {
                    const box = (typeof this.getBoxCoords === "function") ? this.getBoxCoords() : {
                        trayX: 26, trayW: Math.max(120, nodeW - 52), trayBottom: 26
                    };
                    if (lx >= box.trayX && lx <= box.trayX + box.trayW && ly >= 1 && ly <= box.trayBottom + 2) {
                        openOnceInlineEditor(this, canvas);
                        return true;
                    }
                }

                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                this.size = this.computeSize();
            };

            node.size = node.computeSize();
        }


        function openOnlyInlineEditor(node, canvas) {
            const activeCanvas = canvas || LGraphCanvas.active_canvas;
            if (!activeCanvas) return;
            const canvasEl = activeCanvas.canvas;
            if (!canvasEl) return;

            const existing = document.getElementById("pyxis-inline-text-editor");
            if (existing) {
                if (typeof existing._saveAndClose === "function") existing._saveAndClose();
                else existing.remove();
            }

            const curVal = String(node.properties.condition !== undefined ? node.properties.condition : "True");
            let box = (typeof node.getBoxCoords === "function") ? node.getBoxCoords() : { x: 36, y: 6, w: 108, h: 18 };

            const offset = activeCanvas.ds ? activeCanvas.ds.offset : [0, 0];
            const scale = activeCanvas.ds ? activeCanvas.ds.scale : 1.0;
            const rect = canvasEl.getBoundingClientRect();

            const screenX = rect.left + (node.pos[0] + box.x + offset[0]) * scale;
            const screenY = rect.top + (node.pos[1] + box.y + offset[1]) * scale;
            const screenW = box.w * scale;
            const screenH = box.h * scale;

            const inputEl = document.createElement("input");
            inputEl.id = "pyxis-inline-text-editor";
            inputEl.name = "pyxis-only-text-editor";
            inputEl.type = "text";
            inputEl.value = curVal;
            inputEl.placeholder = "True";
            inputEl.autocomplete = "off";
            inputEl.spellcheck = false;

            const padHoriz = Math.max(2, Math.round(4 * scale));

            Object.assign(inputEl.style, {
                position: "fixed",
                left: Math.round(screenX) + "px",
                top: Math.round(screenY) + "px",
                width: Math.round(screenW) + "px",
                height: Math.round(screenH) + "px",
                background: "#12161f",
                color: "#a7f3d0",
                border: Math.max(1, 1.5 * scale) + "px solid #8b5cf6",
                borderRadius: Math.round(4 * scale) + "px",
                boxShadow: "0 0 10px rgba(139, 92, 246, 0.6)",
                fontFamily: "Consolas, monospace",
                fontWeight: "bold",
                fontSize: Math.max(9, Math.round(11 * scale)) + "px",
                padding: "0 " + padHoriz + "px",
                lineHeight: Math.round(screenH - 2 * scale) + "px",
                boxSizing: "border-box",
                zIndex: "90000",
                outline: "none",
                textAlign: "center"
            });

            document.body.appendChild(inputEl);
            node._editing_cond = true;
            if (activeCanvas.draw) activeCanvas.draw(true, true);

            let isMounting = true;
            setTimeout(() => {
                isMounting = false;
                inputEl.focus();
                inputEl.select();
            }, 30);

            function updateGeometry() {
                const curBox = (typeof node.getBoxCoords === "function") ? node.getBoxCoords() : { x: 50, y: 6, w: 80, h: 18 };
                const curOffset = activeCanvas.ds ? activeCanvas.ds.offset : [0, 0];
                const curScale = activeCanvas.ds ? activeCanvas.ds.scale : 1.0;
                const curRect = canvasEl.getBoundingClientRect();

                const curScreenX = curRect.left + (node.pos[0] + curBox.x + curOffset[0]) * curScale;
                const curScreenY = curRect.top + (node.pos[1] + curBox.y + curOffset[1]) * curScale;
                const curScreenW = curBox.w * curScale;
                const curScreenH = curBox.h * curScale;

                inputEl.style.left = Math.round(curScreenX) + "px";
                inputEl.style.top = Math.round(curScreenY) + "px";
                inputEl.style.width = Math.round(curScreenW) + "px";
                inputEl.style.height = Math.round(curScreenH) + "px";
                inputEl.style.fontSize = Math.max(9, Math.round(11 * curScale)) + "px";
                inputEl.style.lineHeight = Math.round(curScreenH - 2 * curScale) + "px";
            }

            inputEl.oninput = function() {
                const cleanVal = String(inputEl.value || "").replace(/[\r\n]+/g, " ");
                node.properties.condition = cleanVal;
                if (node.properties.condicion !== undefined) delete node.properties.condicion;
                if (typeof node.computeSize === "function") {
                    node.size = node.computeSize();
                    if (typeof node.updateSocketPositions === "function") {
                        node.updateSocketPositions();
                    }
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (activeCanvas.setDirty) activeCanvas.setDirty(true, true);
                if (activeCanvas.draw) activeCanvas.draw(true, true);

                updateGeometry();
            };

            let isClosed = false;
            function saveAndClose() {
                if (isClosed) return;
                isClosed = true;
                delete node._editing_cond;
                const cleanVal = String(inputEl.value || "").replace(/[\r\n]+/g, " ").trim() || "True";
                node.properties.condition = cleanVal;
                if (node.properties.condicion !== undefined) delete node.properties.condicion;
                node.size = node.computeSize();
                if (typeof node.updateSocketPositions === "function") {
                    node.updateSocketPositions();
                }

                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (activeCanvas.setDirty) activeCanvas.setDirty(true, true);
                if (activeCanvas.draw) activeCanvas.draw(true, true);
                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("only-edit-condicion");
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
                    delete node._editing_cond;
                    node.properties.condition = curVal;
                    if (node.properties.condicion !== undefined) delete node.properties.condicion;
                    node.size = node.computeSize();
                    if (typeof node.updateSocketPositions === "function") {
                        node.updateSocketPositions();
                    }
                    inputEl.onblur = null;
                    if (inputEl.parentNode) inputEl.parentNode.removeChild(inputEl);
                    if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                    if (activeCanvas.setDirty) activeCanvas.setDirty(true, true);
                    if (activeCanvas.draw) activeCanvas.draw(true, true);
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

        function setupOnlyNode(node) {
            if (!node) return;
            node.resizable = false;
            if (node.flags) {
                node.flags.resizable = false;
                node.flags.hide_resize = true;
            }
            node._custom_collapsed_width = 120;
            node._collapsed_width = 120;
            node.hide_collapsed_slots = true;
            node.hide_help_button = true;
            if (!node.properties) node.properties = {};
            const initialOnlyCond = node.properties.condition !== undefined ? node.properties.condition : "True";
            const initialOnlyMode = node.properties.mode || "select";
            node.properties.condition = initialOnlyCond;
            node.properties.mode = initialOnlyMode;
            if (node.properties.condicion !== undefined) delete node.properties.condicion;
            if (node.properties.modo !== undefined) delete node.properties.modo;

            const ONLY_THEME = {
                selectColor: "#10b981",
                selectGlow: "rgba(16, 185, 129, 0.7)",
                splitColor: "#f43f5e",
                splitGlow: "rgba(244, 63, 94, 0.7)",
                cyan: "#22d3ee",
                green: "#22c55e",
                red: "#ef4444"
            };

            node.applyModePorts = function() {
                const modo = this.properties.mode || "select";
                if (modo === "select") {
                    if (!this.inputs) this.inputs = [];
                    while (this.inputs.length < 2) {
                        this.addInput("", 0);
                    }
                    while (this.inputs.length > 2) {
                        this.removeInput(this.inputs.length - 1);
                    }
                    if (this.inputs[0]) { this.inputs[0].name = "True"; this.inputs[0].label = ""; }
                    if (this.inputs[1]) { this.inputs[1].name = "False"; this.inputs[1].label = ""; }

                    if (!this.outputs) this.outputs = [];
                    if (this.outputs.length === 0) {
                        this.addOutput("Out", 0);
                    } else {
                        while (this.outputs.length > 1) {
                            this.removeOutput(this.outputs.length - 1);
                        }
                    }
                    if (this.outputs[0]) { this.outputs[0].name = "Out"; this.outputs[0].label = ""; }
                    this.color = ONLY_THEME.selectColor;
                } else {
                    if (!this.inputs) this.inputs = [];
                    if (this.inputs.length === 0) {
                        this.addInput("", 0);
                    } else {
                        while (this.inputs.length > 1) {
                            this.removeInput(this.inputs.length - 1);
                        }
                    }
                    if (this.inputs[0]) { this.inputs[0].name = ""; this.inputs[0].label = ""; }

                    if (!this.outputs) this.outputs = [];
                    while (this.outputs.length < 2) {
                        this.addOutput("", 0);
                    }
                    while (this.outputs.length > 2) {
                        this.removeOutput(this.outputs.length - 1);
                    }
                    if (this.outputs[0]) { this.outputs[0].name = "True"; this.outputs[0].label = ""; }
                    if (this.outputs[1]) { this.outputs[1].name = "False"; this.outputs[1].label = ""; }
                    this.color = ONLY_THEME.splitColor;
                }
            };

            node.toggleMode = function() {
                const currentMode = this.properties.mode || "select";
                const nextMode = (currentMode === "select") ? "split" : "select";
                this.properties.mode = nextMode;
                if (this.properties.modo !== undefined) delete this.properties.modo;
                this.applyModePorts();
                this.size = this.computeSize();
                this.updateSocketPositions();
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                const ac = LGraphCanvas.active_canvas;
                if (ac && ac.draw) ac.draw(true, true);
                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("only-toggle-mode");
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            };

            node.updateSocketPositions = function() {
                const isCollapsed = Boolean(this.flags && this.flags.collapsed);
                const colW = this._custom_collapsed_width || this._collapsed_width || 120;
                const nodeW = this.size ? this.size[0] : (isCollapsed ? colW : 180);
                const modo = this.properties.mode || "select";

                const centerY = 7;
                const pairY1 = -4;
                const pairY2 = 18;

                if (isCollapsed) {
                    const centerY = -15;
                    if (this.inputs) {
                        for (let i = 0; i < this.inputs.length; i++) {
                            if (this.inputs[i]) this.inputs[i].pos = [14, centerY];
                        }
                    }
                    if (this.outputs) {
                        for (let i = 0; i < this.outputs.length; i++) {
                            if (this.outputs[i]) this.outputs[i].pos = [colW - 14, centerY];
                        }
                    }
                    return;
                }

                if (modo === "select") {
                    if (this.inputs && this.inputs[0]) this.inputs[0].pos = [14, pairY1];
                    if (this.inputs && this.inputs[1]) this.inputs[1].pos = [14, pairY2];
                    if (this.outputs && this.outputs[0]) this.outputs[0].pos = [nodeW - 14, centerY];
                } else {
                    if (this.inputs && this.inputs[0]) this.inputs[0].pos = [14, centerY];
                    if (this.outputs && this.outputs[0]) this.outputs[0].pos = [nodeW - 14, pairY1];
                    if (this.outputs && this.outputs[1]) this.outputs[1].pos = [nodeW - 14, pairY2];
                }
            };

            node.getConnectionPos = function(is_input, slot_number, out) {
                out = out || new Float32Array(2);
                const isCollapsed = Boolean(this.flags && this.flags.collapsed);
                const colW = this._custom_collapsed_width || this._collapsed_width || 120;
                const nodeW = this.size ? this.size[0] : (isCollapsed ? colW : 180);
                const modo = this.properties.mode || "select";

                if (isCollapsed) {
                    const centerY = -15;
                    if (is_input) {
                        out[0] = this.pos[0] + 14;
                        out[1] = this.pos[1] + centerY;
                    } else {
                        out[0] = this.pos[0] + colW - 14;
                        out[1] = this.pos[1] + centerY;
                    }
                    return out;
                }

                const centerY = 7;
                const pairY1 = -4;
                const pairY2 = 18;

                if (modo === "select") {
                    if (is_input) {
                        out[0] = this.pos[0] + 14;
                        out[1] = this.pos[1] + (slot_number === 0 ? pairY1 : pairY2);
                    } else {
                        out[0] = this.pos[0] + nodeW - 14;
                        out[1] = this.pos[1] + centerY;
                    }
                } else {
                    if (is_input) {
                        out[0] = this.pos[0] + 14;
                        out[1] = this.pos[1] + centerY;
                    } else {
                        out[0] = this.pos[0] + nodeW - 14;
                        out[1] = this.pos[1] + (slot_number === 0 ? pairY1 : pairY2);
                    }
                }
                return out;
            };

            node.getBoxCoords = function() {
                const nodeW = this.size ? this.size[0] : 190;
                const condVal = String(this.properties ? (this.properties.condition !== undefined ? this.properties.condition : "True") : "True");
                const condW = getExactTextWidth(condVal, "bold 11px Consolas, monospace");
                const boxW = Math.min(nodeW - 100, Math.max(65, Math.ceil(condW + 28)));
                const boxX = Math.round((nodeW - boxW) / 2);
                const boxY = 6;
                const boxH = 18;
                return {
                    x: boxX,
                    y: boxY,
                    w: boxW,
                    h: boxH
                };
            };

            node.computeSize = function() {
                if (this.flags && this.flags.collapsed) {
                    return [120, 0];
                }
                const condVal = String(this.properties ? (this.properties.condition !== undefined ? this.properties.condition : "True") : "True");
                const condW = getExactTextWidth(condVal, "bold 11px Consolas, monospace");
                const boxW = Math.max(65, Math.ceil(condW + 28));
                const reqW = Math.max(190, Math.ceil(boxW + 110));
                return [reqW, 36];
            };

            const origCollapse = node.collapse;
            node.collapse = function(force) {
                if (origCollapse) origCollapse.call(this, force);
                if (this.flags && this.flags.collapsed) {
                    this._custom_collapsed_width = 120;
                    this._collapsed_width = 120;
                    this.size = [120, 0];
                } else {
                    this.size = this.computeSize();
                }
                this.updateSocketPositions();
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            const oldPropertyChanged = node.onPropertyChanged;
            node.onPropertyChanged = function(name, value) {
                if (oldPropertyChanged) oldPropertyChanged.call(this, name, value);
                if (name === "condition" || name === "mode") {
                    if (name === "mode") {
                        this.applyModePorts();
                    }
                    if (!this.flags || !this.flags.collapsed) {
                        this.size = this.computeSize();
                    }
                    this.updateSocketPositions();
                }
            };

            node.getExtraMenuOptions = function(canvas, options) {
                const self = this;
                const currentMode = this.properties.mode || "select";
                options.push({
                    content: currentMode === "select" ? "Modo: Cambiar a Desviador (1 -> 2)" : "Modo: Cambiar a Selector (2 -> 1)",
                    callback: function() {
                        self.toggleMode();
                    }
                });
            };

            if (typeof LGraphCanvas !== "undefined" && LGraphCanvas.prototype && !LGraphCanvas.prototype._pyxis_only_shape_hooked) {
                LGraphCanvas.prototype._pyxis_only_shape_hooked = true;
                const origDrawNodeShape = LGraphCanvas.prototype.drawNodeShape;
                LGraphCanvas.prototype.drawNodeShape = function(node, ctx, size, fgcolor, bgcolor, selected, mouse_over) {
                    if (node && (node.type === "Only" || node.type === "Functions/Only" || node.type === "Basics/Only" || (node.title && node.title === "Only"))) {
                        if (typeof node.onDrawOnlyCustomShape === "function") {
                            const handled = node.onDrawOnlyCustomShape.call(node, ctx, size, fgcolor, bgcolor, selected, mouse_over, this);
                            if (handled) return;
                        }
                    }
                    if (node && (node.type === "Once" || node.type === "Functions/Once" || node.type === "Basics/Once" || (node.title && node.title === "Once"))) {
                        if (typeof node.onDrawOnceCustomShape === "function") {
                            const handled = node.onDrawOnceCustomShape.call(node, ctx, size, fgcolor, bgcolor, selected, mouse_over, this);
                            if (handled) return;
                        }
                    }
                    return origDrawNodeShape.apply(this, arguments);
                };
            }

            node.getTitle = function() {
                if (this.flags && this.flags.collapsed) return "Only";
                return "";
            };
            node.onDrawTitleBox = function() {};
            node.onDrawTitleText = function() {};
            node.onDrawTitleBar = function() {};

            node.onDrawOnlyCustomShape = function(ctx, size, fgcolor, bgcolor, selected, mouse_over, canvas) {
                const isCollapsed = Boolean(this.flags && this.flags.collapsed);
                const colW = this._custom_collapsed_width || this._collapsed_width || 120;
                if (!isCollapsed && (!this.size || this.size[1] < 36)) {
                    this.size = this.computeSize();
                    if (size) {
                        size[0] = this.size[0];
                        size[1] = Math.max(36, this.size[1]);
                    }
                }
                const nodeW = isCollapsed ? colW : (size ? size[0] : (this.size ? this.size[0] : 180));
                if (isCollapsed) {
                    this._custom_collapsed_width = colW;
                    this._collapsed_width = colW;
                    if (size) size[0] = colW;
                }
                const modo = this.properties.mode || "select";
                const isSelect = (modo === "select");

                const themeColor = isSelect ? ONLY_THEME.selectColor : ONLY_THEME.splitColor;
                const themeGlow = isSelect ? ONLY_THEME.selectGlow : ONLY_THEME.splitGlow;

                ctx.save();

                const pt = window.PYXIS_THEME || {};
                const bgGradStart = (pt.nodeBgGradient && pt.nodeBgGradient.start) || "#1d2536";
                const bgGradEnd = (pt.nodeBgGradient && pt.nodeBgGradient.end) || "#0d111a";

                function drawSocketRing(sx, sy) {
                    ctx.save();
                    ctx.strokeStyle = "rgba(0, 0, 0, 0.6)";
                    ctx.lineWidth = 2.5;
                    ctx.beginPath();
                    ctx.arc(sx, sy, 7.5, 0, Math.PI * 2);
                    ctx.stroke();

                    ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.arc(sx, sy, 8.5, 0, Math.PI * 2);
                    ctx.stroke();
                    ctx.restore();
                }

                if (isCollapsed) {
                    this._custom_collapsed_width = colW;
                    this._collapsed_width = colW;
                    const pillY = -31;
                    const pillH = 32;
                    const pillR = 16;
                    const pillW = colW;

                    const plugGrad = ctx.createLinearGradient(0, pillY, 0, pillY + pillH);
                    plugGrad.addColorStop(0, bgGradStart);
                    plugGrad.addColorStop(1, bgGradEnd);
                    ctx.fillStyle = plugGrad;
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(0, pillY, pillW, pillH, pillR);
                    else ctx.rect(0, pillY, pillW, pillH);
                    ctx.fill();
                    ctx.stroke();

                    const centerY = -15;
                    drawSocketRing(14, centerY);
                    drawSocketRing(pillW - 14, centerY);

                    const badgeY = centerY;
                    ctx.fillStyle = "#e2e8f0";
                    ctx.beginPath();
                    ctx.arc(pillW / 2 - 24, badgeY, 3.5, 0, Math.PI * 2);
                    ctx.fill();

                    ctx.font = "bold 11px sans-serif";
                    ctx.fillStyle = "#ffffff";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("ONLY", pillW / 2, badgeY + 1.2);

                    ctx.save();
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    ctx.shadowColor = themeGlow;
                    ctx.shadowBlur = 6;
                    ctx.fillStyle = themeColor;
                    ctx.beginPath();
                    ctx.arc(pillW / 2 + 24, badgeY, 4, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();

                    if (selected) {
                        ctx.save();
                        ctx.globalAlpha = 0.40;
                        ctx.strokeStyle = themeColor;
                        ctx.shadowColor = themeColor;
                        ctx.shadowBlur = 6;
                        ctx.lineWidth = 1.5;
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(-2, pillY - 2, pillW + 4, pillH + 4, pillR + 2);
                        else ctx.rect(-2, pillY - 2, pillW + 4, pillH + 4);
                        ctx.stroke();
                        ctx.restore();
                    }

                    ctx.restore();
                    return true;
                }

                const pillX = 0;
                const pillY = -18;
                const pillH = 50;
                const pillW = nodeW;
                const pillR = 17;

                const bodyGrad = ctx.createLinearGradient(0, pillY, 0, pillY + pillH);
                bodyGrad.addColorStop(0, bgGradStart);
                bodyGrad.addColorStop(1, bgGradEnd);
                ctx.fillStyle = bodyGrad;
                ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
                ctx.lineWidth = 1;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(pillX, pillY, pillW, pillH, pillR);
                else ctx.rect(pillX, pillY, pillW, pillH);
                ctx.fill();
                ctx.stroke();

                const sheenGrad = ctx.createLinearGradient(0, pillY, 0, pillY + 12);
                sheenGrad.addColorStop(0, "rgba(255, 255, 255, 0.10)");
                sheenGrad.addColorStop(1, "rgba(255, 255, 255, 0.0)");
                ctx.fillStyle = sheenGrad;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(pillX + 2, pillY + 1, pillW - 4, 12, [pillR, pillR, 0, 0]);
                ctx.fill();

                const badgeY = -5;

                ctx.fillStyle = "#e2e8f0";
                ctx.beginPath();
                ctx.arc(nodeW / 2 - 24, badgeY, 3.5, 0, Math.PI * 2);
                ctx.fill();

                ctx.font = "bold 11px sans-serif";
                ctx.fillStyle = "#ffffff";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText("ONLY", nodeW / 2, badgeY + 1.2);

                ctx.save();
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 0;
                ctx.shadowColor = themeGlow;
                ctx.shadowBlur = 7;
                ctx.fillStyle = themeColor;
                ctx.beginPath();
                ctx.arc(nodeW / 2 + 24, badgeY, 4, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();

                const box = (typeof this.getBoxCoords === "function") ? this.getBoxCoords() : {
                    x: Math.round((nodeW - 80) / 2), y: 6, w: 80, h: 18
                };

                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = this._editing_cond ? "#8b5cf6" : "rgba(255, 255, 255, 0.22)";
                ctx.lineWidth = this._editing_cond ? 1.5 : 1;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(box.x, box.y, box.w, box.h, 4);
                else ctx.rect(box.x, box.y, box.w, box.h);
                ctx.fill();
                ctx.stroke();

                if (!this._editing_cond) {
                    const condVal = String((this.properties && this.properties.condition !== undefined) ? this.properties.condition : "True");
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(box.x + 1, box.y + 1, box.w - 2, box.h - 2, 3);
                    else ctx.rect(box.x + 1, box.y + 1, box.w - 2, box.h - 2);
                    ctx.clip();

                    ctx.font = "bold 11px Consolas, monospace";
                    ctx.fillStyle = "#a7f3d0";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    ctx.shadowColor = "rgba(167, 243, 208, 0.5)";
                    ctx.shadowBlur = 4;
                    ctx.fillText(condVal, box.x + box.w / 2, box.y + box.h / 2 + 0.5);
                    ctx.restore();
                }

                const centerY = 7;
                const pairY1 = -4;
                const pairY2 = 18;

                if (isSelect) {
                    drawSocketRing(14, pairY1);
                    drawSocketRing(14, pairY2);

                    ctx.font = "bold 9px Consolas, monospace";
                    ctx.fillStyle = ONLY_THEME.green;
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    ctx.fillText("true", 26, pairY1);

                    ctx.font = "bold 9px Consolas, monospace";
                    ctx.fillStyle = ONLY_THEME.red;
                    ctx.textAlign = "left";
                    ctx.textBaseline = "middle";
                    ctx.fillText("false", 26, pairY2);

                    drawSocketRing(nodeW - 14, centerY);
                } else {
                    drawSocketRing(14, centerY);

                    drawSocketRing(nodeW - 14, pairY1);
                    drawSocketRing(nodeW - 14, pairY2);

                    ctx.font = "bold 9px Consolas, monospace";
                    ctx.fillStyle = ONLY_THEME.green;
                    ctx.textAlign = "right";
                    ctx.textBaseline = "middle";
                    ctx.fillText("true", nodeW - 26, pairY1);

                    ctx.font = "bold 9px Consolas, monospace";
                    ctx.fillStyle = ONLY_THEME.red;
                    ctx.textAlign = "right";
                    ctx.textBaseline = "middle";
                    ctx.fillText("false", nodeW - 26, pairY2);
                }

                if (selected) {
                    ctx.save();
                    ctx.globalAlpha = 0.40;
                    ctx.strokeStyle = themeColor;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    ctx.shadowColor = themeColor;
                    ctx.shadowBlur = 6;
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(pillX - 2, pillY - 2, pillW + 4, pillH + 4, pillR + 2);
                    else ctx.rect(pillX - 2, pillY - 2, pillW + 4, pillH + 4);
                    ctx.stroke();
                    ctx.restore();
                }

                ctx.restore();
                return true;
            };

            const oldDrawForeground = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDrawForeground) oldDrawForeground.call(this, ctx);
                this.updateSocketPositions();
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                const lx = local_pos[0];
                const ly = local_pos[1];
                const isCollapsed = Boolean(this.flags && this.flags.collapsed);
                const colW = this._custom_collapsed_width || this._collapsed_width || 120;
                const nodeW = this.size ? this.size[0] : (isCollapsed ? colW : 180);

                if (isCollapsed) {
                    const badgeY = -15;
                    if (Math.hypot(lx - (colW / 2 + 24), ly - badgeY) <= 8) {
                        this.toggleMode();
                        return true;
                    }
                    if (Math.hypot(lx - (colW / 2 - 24), ly - badgeY) <= 8) {
                        this.collapse();
                        return true;
                    }
                    if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
                    return;
                }

                const badgeY = -5;
                if (Math.hypot(lx - (nodeW / 2 + 24), ly - badgeY) <= 8) {
                    this.toggleMode();
                    return true;
                }

                if (Math.hypot(lx - (nodeW / 2 - 24), ly - badgeY) <= 8) {
                    this.collapse();
                    return true;
                }

                const box = (typeof this.getBoxCoords === "function") ? this.getBoxCoords() : {
                    x: Math.round((nodeW - 80) / 2), y: 6, w: 80, h: 18
                };
                if (lx >= box.x && lx <= box.x + box.w && ly >= box.y && ly <= box.y + box.h) {
                    openOnlyInlineEditor(this, canvas);
                    return true;
                }

                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                this.applyModePorts();
                if (this.flags && this.flags.collapsed) {
                    this.size = [this._custom_collapsed_width || 120, 0];
                } else {
                    const compSz = this.computeSize();
                    this.size = [compSz[0], Math.max(36, compSz[1])];
                }
                this.updateSocketPositions();
            };

            node.applyModePorts();
            node.size = node.computeSize();
            node.updateSocketPositions();
        }

        
        window.setupConcatenarNode = setupConcatenateNode;
        window.setupConcatenateNode = setupConcatenateNode;
        window.setupFormatDinamicoNode = setupDynamicFormatNode;
        window.setupDynamicFormatNode = setupDynamicFormatNode;
        window.setupValueUnitNode = setupValueUnitNode;
        window.setupValueUnitTextWidget = setupValueUnitTextWidget;


