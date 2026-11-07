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
 * @file variable_nodes.js
 * @description UI setups and interactive editors for Variables category nodes.
 * @module PyxisVariableNodes
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function setupMemoryNode(node) {
            if (!node.properties) node.properties = {};
            if (!node.properties.mode) node.properties.mode = "remember";
            if (node.properties.key === undefined) node.properties.key = "ref";
            if (node.properties.value === undefined) node.properties.value = "";
            if (node.properties.default === undefined) node.properties.default = "";
            node.widgets_up = true;

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const m = String(props.mode || "remember").toLowerCase();
                const isRemember = m === "remember" || m === "save";
                const reqInputs = isRemember ? ["Key", "Value"] : ["Key", "Default"];
                
                let base_w = 175;
                let text_req_w = 0;
                for (const p in props) {
                    if (p === "mode") continue;
                    const val = String(props[p] || "");
                    if (val.length > 0) {
                        const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                        if (tw > text_req_w) text_req_w = tw;
                    }
                }
                const right_space = getNodeRightReserve(this);
                const boxW = Math.max(65, Math.ceil(text_req_w + 28));
                return [Math.max(base_w, 22 + boxW + right_space), 11 + reqInputs.length * 23 + 22];
            };

            node.updateTagInputs = updateMemoryInputs;
            node.updateMemoryInputs = updateMemoryInputs;

            function updateMemoryInputs() {
                const m = String(node.properties.mode || "remember").toLowerCase();
                const isRemember = m === "remember" || m === "save";
                const reqInputs = isRemember ? ["Key", "Value"] : ["Key", "Default"];
                
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

                node.widgets = [];

                reqInputs.forEach((paramName, idx) => {
                    const propKey = (paramName === "Default") ? "default" : paramName.toLowerCase();
                    if (node.properties[propKey] === undefined) {
                        node.properties[propKey] = (paramName === "Key") ? "ref" : "";
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
                    node.size = [175, 11 + reqInputs.length * 23 + 24];
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos && local_pos[1] < 0) {
                    const modeInfo = getTitleModeInfo(this);
                    if (modeInfo) {
                        const btnText = modeInfo.currentShort;
                        const textW = (canvas && canvas.ctx) ? canvas.ctx.measureText(btnText).width : 50;
                        const btnW = Math.max(55, textW + 14);
                        const btnX = this.size[0] - btnW - 8;
                        if (local_pos[0] >= btnX - 4 && local_pos[0] <= btnX + btnW + 6) {
                            const nextIdx = (modeInfo.currentIdx + 1) % modeInfo.modeList.length;
                            this.properties.mode = modeInfo.modeList[nextIdx].full;
                            updateMemoryInputs();
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
                        inp.pos = [10, 11 + idx * 23 + 9];
                    });
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateMemoryInputs();
            };

            updateMemoryInputs();
        }

        const RANDOM_DEFINITIONS = {
            "r": { desc: "basic random (integer/float)", preview: "R(min, max, step)" },
            "rs": { desc: "symmetric random (+/-)", preview: "Rs(min, max) -> ±Val" },
            "rr": { desc: "random by resolution ratio", preview: "Rr(min, max) * ratio" },
            "rc": { desc: "hundredths (2 decimals)", preview: "Rc(min, max)" },
            "rd": { desc: "tenths (1 decimal)", preview: "Rd(min, max)" },
            "rm": { desc: "thousandths (3 decimals)", preview: "Rm(min, max)" },
            "rds": { desc: "symmetric tenths (+/-)", preview: "Rds(min, max) -> ±Val" },
            "rcs": { desc: "symmetric hundredths (+/-)", preview: "Rcs(min, max) -> ±Val" },
            "rms": { desc: "symmetric thousandths (+/-)", preview: "Rms(min, max) -> ±Val" },
            "re": { desc: "random choice from list", preview: "Re(opt1, opt2...)" },
            "rfake": { desc: "pseudo-random (i/j)", preview: "Rfake(min, max, ctr)" },
            "rcolor": { desc: "random color (ASS/Hex)", preview: "Rcolor(col1, col2)" },
            "rcol": { desc: "random color (ASS/Hex)", preview: "Rcolor(col1, col2)" },
            "r2d": { desc: "coordinate pair (x, y)", preview: "R2d(min, max, step)" },
            "rbool": { desc: "boolean by probability", preview: "Rbool(prob %)" },
            "rstep": { desc: "truncated to discrete step", preview: "Rstep(min, max, step)" }
        };

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


        function setupGetVarNode(node) {
            if (!node) return;
            if (!node.properties) node.properties = {};
            if (node.properties.var_name === undefined) node.properties.var_name = "j";

            node.widgets_up = true;
            if (!node.outputs || node.outputs.length === 0) {
                node.outputs = [{ name: "Data", type: "data" }];
            }

            node.widgets = [];
            const curVal = String(node.properties.var_name !== undefined ? node.properties.var_name : "j");
            const w = node.addWidget("text", "Name", curVal, function(val) {
                const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                node.properties.var_name = cleanVal;
                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            });
            w.property = "var_name";
            w.y = 11;
            w.last_y = 11;
            setupSingleLineTextWidget(node, w, "Name", "var_name");

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const valStr = String(props.var_name !== undefined ? props.var_name : "j");
                const textWidth = getExactTextWidth(valStr, "bold 11px Consolas, monospace");
                const boxW = Math.max(65, Math.ceil(textWidth + 28));
                const right_space = getNodeRightReserve(this);
                return [Math.max(150, 22 + boxW + right_space), 56];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;
                if (this.widgets && this.widgets[0]) {
                    this.widgets[0].y = 11;
                    this.widgets[0].last_y = 11;
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [this.size[0] - 10, 20];
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (this.widgets && this.widgets[0] && this.properties && this.properties.var_name !== undefined) {
                    this.widgets[0].value = String(this.properties.var_name);
                }
                if (this.computeSize) {
                    node.size = node.computeSize();
                }
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            if (node.computeSize) node.size = node.computeSize();
        }


        function openInlineDefinirVarsEditor(node, propertyName) {
            propertyName = propertyName || "variables";
            const existing = document.getElementById("pyxis-inline-vars-editor-container");
            if (existing) {
                if (typeof existing._saveAndClose === "function") existing._saveAndClose();
                else existing.remove();
            }

            const canvas = LGraphCanvas.active_canvas;
            if (!canvas || !canvas.canvas) return;

            const varWidget = node.widgets ? node.widgets.find(w => w.property === propertyName) : null;
            const curVal = String(node.properties[propertyName] !== undefined ? node.properties[propertyName] : (varWidget ? varWidget.value : ""));

            const drawY = (varWidget && varWidget.last_y !== undefined) ? varWidget.last_y : 48;
            const margin = 12;

            const rect = canvas.canvas.getBoundingClientRect();
            const scale = canvas.ds ? canvas.ds.scale : 1.0;
            const offset = canvas.ds ? canvas.ds.offset : [0, 0];

            const initialNodeW = node._manual_width !== undefined ? node._manual_width : ((node.size && node.size[0] > 0) ? node.size[0] : 220);
            const initialNodeH = node._manual_height !== undefined ? node._manual_height : ((node.size && node.size[1] > 0) ? node.size[1] : 102);

            node.size[0] = Math.max(200, initialNodeW);
            node.size[1] = Math.max(102, initialNodeH);

            const screenX = rect.left + (node.pos[0] + margin + offset[0]) * scale;
            const screenY = rect.top + (node.pos[1] + drawY + offset[1]) * scale;
            const screenW = (node.size[0] - 24) * scale;
            const screenH = Math.max(28, (node.size[1] - drawY - 26)) * scale;

            node._is_editing_vars = true;
            if (canvas.draw) canvas.draw(true, true);

            const container = document.createElement("div");
            container.id = "pyxis-inline-vars-editor-container";
            container.style.position = "fixed";
            container.style.boxSizing = "border-box";
            container.style.left = screenX + "px";
            container.style.top = screenY + "px";
            container.style.width = screenW + "px";
            container.style.height = screenH + "px";
            container.style.zIndex = "90000";
            container.style.background = "#12161f";
            container.style.border = (1.5 * scale) + "px solid #8b5cf6";
            container.style.borderRadius = (8 * scale) + "px";
            container.style.boxShadow = "0 0 14px rgba(139, 92, 246, 0.6)";
            container.style.overflow = "hidden";

            const editorDiv = document.createElement("div");
            editorDiv.id = "pyxis-inline-vars-ace";
            editorDiv.style.position = "absolute";
            editorDiv.style.left = "0px";
            editorDiv.style.top = (2 * scale) + "px";
            editorDiv.style.width = "100%";
            editorDiv.style.height = `calc(100% - ${(2 * scale)}px)`;
            editorDiv.style.background = "transparent";
            container.appendChild(editorDiv);

            const fontSizePx = Math.max(1, 12 * scale);
            const lineHeightPx = Math.max(1, 20 * scale);

            let styleTag = document.getElementById("pyxis-inline-vars-ace-style");
            if (!styleTag) {
                styleTag = document.createElement("style");
                styleTag.id = "pyxis-inline-vars-ace-style";
                document.head.appendChild(styleTag);
            }
            styleTag.textContent = `
                #pyxis-inline-vars-ace {
                    font-family: Consolas, monospace !important;
                    font-weight: bold !important;
                    font-size: ${fontSizePx}px !important;
                    line-height: ${lineHeightPx}px !important;
                    background: transparent !important;
                }
                #pyxis-inline-vars-ace .ace_scroller {
                    padding: 0 !important;
                    overflow-x: hidden !important;
                }
                #pyxis-inline-vars-ace .ace_scrollbar-h,
                #pyxis-inline-vars-ace .ace_scrollbar-h * {
                    display: none !important;
                    height: 0px !important;
                    max-height: 0px !important;
                    visibility: hidden !important;
                    pointer-events: none !important;
                    overflow: hidden !important;
                }
                #pyxis-inline-vars-ace ::-webkit-scrollbar:horizontal {
                    display: none !important;
                    height: 0px !important;
                    width: 0px !important;
                }
                #pyxis-inline-vars-ace .ace_content {
                    background: transparent !important;
                }
                #pyxis-inline-vars-ace .ace_line {
                    font-family: Consolas, monospace !important;
                    font-weight: bold !important;
                    font-size: ${fontSizePx}px !important;
                    line-height: ${lineHeightPx}px !important;
                    height: ${lineHeightPx}px !important;
                    color: #f8f8f2 !important;
                    letter-spacing: 0px !important;
                }
                #pyxis-inline-vars-ace .ace_line * {
                    font-family: Consolas, monospace !important;
                    font-weight: bold !important;
                    font-size: ${fontSizePx}px !important;
                    letter-spacing: 0px !important;
                }
                #pyxis-inline-vars-ace .ace_keyword,
                #pyxis-inline-vars-ace .ace_operator {
                    color: #ff79c6 !important;
                }
                #pyxis-inline-vars-ace .ace_identifier,
                #pyxis-inline-vars-ace .ace_variable {
                    color: #f8f8f2 !important;
                }
                #pyxis-inline-vars-ace .ace_string {
                    color: #f1fa8c !important;
                }
                #pyxis-inline-vars-ace .ace_constant.ace_numeric {
                    color: #bd93f9 !important;
                }
                #pyxis-inline-vars-ace .ace_comment {
                    color: #6272a4 !important;
                }
                #pyxis-inline-vars-ace .ace_cursor {
                    color: #f8f8f2 !important;
                    border-left: 2px solid #f8f8f2 !important;
                }
                #pyxis-inline-vars-ace .ace_selection {
                    background: rgba(139, 92, 246, 0.4) !important;
                }
                #pyxis-inline-vars-ace .ace_scrollbar-v {
                    width: 6px !important;
                    background: transparent !important;
                }
                #pyxis-inline-vars-ace ::-webkit-scrollbar {
                    width: 5px !important;
                }
                #pyxis-inline-vars-ace ::-webkit-scrollbar-track {
                    background: transparent !important;
                }
                #pyxis-inline-vars-ace ::-webkit-scrollbar-thumb {
                    background: rgba(139, 92, 246, 0.45) !important;
                    border-radius: 4px !important;
                }
                #pyxis-inline-vars-ace ::-webkit-scrollbar-thumb:hover {
                    background: rgba(139, 92, 246, 0.85) !important;
                }
                #pyxis-inline-vars-ace {
                    scrollbar-width: thin !important;
                    scrollbar-color: rgba(139, 92, 246, 0.45) transparent !important;
                }
            `;

            document.body.appendChild(container);

            let aceEditor = null;
            if (window.ace) {
                ace.config.set("basePath", "libs/ace");
                ace.config.set("modePath", "libs/ace");
                ace.config.set("themePath", "libs/ace");

                aceEditor = ace.edit(editorDiv);
                aceEditor.setTheme("ace/theme/dracula");
                if (aceEditor.session) {
                    if (aceEditor.session.setUseWorker) aceEditor.session.setUseWorker(false);
                    aceEditor.session.setMode("ace/mode/python");
                    if (typeof aceEditor.session.setUseWrapMode === "function") {
                        aceEditor.session.setUseWrapMode(true);
                    }
                    if (typeof aceEditor.session.setWrapLimitRange === "function") {
                        aceEditor.session.setWrapLimitRange(null, null);
                    }
                    if (aceEditor.session.setOption) {
                        aceEditor.session.setOption("indentedSoftWrap", false);
                        aceEditor.session.setOption("wrap", true);
                    }
                }
                aceEditor.setOptions({
                    useWorker: false,
                    showGutter: false,
                    highlightActiveLine: false,
                    showPrintMargin: false,
                    fontSize: fontSizePx + "px",
                    fontFamily: "Consolas, monospace",
                    enableBasicAutocompletion: true,
                    enableLiveAutocompletion: true,
                    enableSnippets: true,
                    tabSize: 4,
                    useSoftTabs: true,
                    wrap: true,
                    indentedSoftWrap: false,
                    hScrollBarAlwaysVisible: false
                });

                if (aceEditor.renderer) {
                    if (typeof aceEditor.renderer.setHScrollBarAlwaysVisible === "function") {
                        aceEditor.renderer.setHScrollBarAlwaysVisible(false);
                    }
                    if (aceEditor.renderer.scrollBarH) {
                        aceEditor.renderer.scrollBarH.setVisible = function() {
                            this.isVisible = false;
                            if (this.element) {
                                this.element.style.display = "none";
                                this.element.style.height = "0px";
                                this.element.style.visibility = "hidden";
                            }
                        };
                        aceEditor.renderer.scrollBarH.getHeight = function() { return 0; };
                        if (aceEditor.renderer.scrollBarH.element) {
                            aceEditor.renderer.scrollBarH.element.style.display = "none";
                            aceEditor.renderer.scrollBarH.element.style.height = "0px";
                            aceEditor.renderer.scrollBarH.element.style.visibility = "hidden";
                        }
                    }
                    if (typeof aceEditor.renderer.$getLongestLine === "function") {
                        aceEditor.renderer.$getLongestLine = function() { return 0; };
                    }
                }

                aceEditor.container.style.background = "#12161f";
                aceEditor.container.style.lineHeight = lineHeightPx + "px";
                aceEditor.renderer.setShowGutter(false);
                aceEditor.renderer.lineHeight = lineHeightPx;
                aceEditor.renderer.setPadding(Math.round(10 * scale));
                if (aceEditor.renderer.updateFontSize) aceEditor.renderer.updateFontSize();

                window.__active_code_script_node = node;
                if (typeof window.patchAceAutocompleteShiftEnter === "function") {
                    window.patchAceAutocompleteShiftEnter();
                } else if (typeof patchAceAutocompleteShiftEnter === "function") {
                    patchAceAutocompleteShiftEnter();
                }
                const pyxisCompleter = getPyxisCodeCompleter();
                const langTools = ace.require("ace/ext/language_tools");
                if (langTools) {
                    aceEditor.completers = [pyxisCompleter];
                    if (langTools.snippetCompleter) aceEditor.completers.push(langTools.snippetCompleter);
                    if (langTools.keyWordCompleter) aceEditor.completers.push(langTools.keyWordCompleter);
                    if (langTools.textCompleter) aceEditor.completers.push(langTools.textCompleter);
                } else {
                    aceEditor.completers = [pyxisCompleter];
                }

                if (aceEditor.completer && aceEditor.completer.keyboardHandler) {
                    aceEditor.completer.keyboardHandler.bindKeys({
                        "Shift-Return": function(ed) {
                            if (ed && ed.completer) ed.completer.detach();
                            if (ed) ed.insert("\n");
                        },
                        "Shift-Enter": function(ed) {
                            if (ed && ed.completer) ed.completer.detach();
                            if (ed) ed.insert("\n");
                        }
                    });
                }

                aceEditor.setValue(curVal, -1);
                setTimeout(() => {
                    if (aceEditor) {
                        aceEditor.focus();
                        aceEditor.navigateFileStart();
                        aceEditor.renderer.scrollToRow(0);
                    }
                }, 30);

                let isSyncing = false;
                const syncSizeAndCanvas = () => {
                    if (isSyncing) return;
                    isSyncing = true;
                    try {
                        const val = aceEditor ? aceEditor.getValue() : "";
                        node.properties[propertyName] = val;
                        if (varWidget) varWidget.value = val;

                        if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                        if (canvas.draw) canvas.draw(true, true);

                        const curScale = canvas.ds ? canvas.ds.scale : 1.0;
                        const curOffset = canvas.ds ? canvas.ds.offset : [0, 0];
                        const curRect = canvas.canvas.getBoundingClientRect();

                        const newScreenX = curRect.left + (node.pos[0] + margin + curOffset[0]) * curScale;
                        const newScreenY = curRect.top + (node.pos[1] + drawY + curOffset[1]) * curScale;
                        const newScreenW = (node.size[0] - 24) * curScale;
                        const newScreenH = Math.max(36, (node.size[1] - drawY - 26)) * curScale;

                        container.style.left = newScreenX + "px";
                        container.style.top = newScreenY + "px";
                        container.style.width = newScreenW + "px";
                        container.style.height = newScreenH + "px";

                        editorDiv.style.left = "0px";
                        editorDiv.style.top = (2 * curScale) + "px";
                        editorDiv.style.width = "100%";
                        editorDiv.style.height = `calc(100% - ${(2 * curScale)}px)`;
                        aceEditor.renderer.setPadding(Math.round(10 * curScale));

                        aceEditor.resize();
                    } finally {
                        isSyncing = false;
                    }
                };

                aceEditor.session.on('change', syncSizeAndCanvas);

                aceEditor.commands.addCommand({
                    name: "pyxisShiftEnterLineBreak",
                    bindKey: { win: "Shift-Return|Shift-Enter", mac: "Shift-Return|Shift-Enter" },
                    exec: function(ed) {
                        if (ed.completer && ed.completer.activated) {
                            ed.completer.detach();
                        }
                        ed.insert("\n");
                    }
                });

                aceEditor.commands.addCommand({
                    name: "pyxisSaveAndClose",
                    bindKey: { win: "Ctrl-Enter", mac: "Command-Enter" },
                    exec: function() {
                        saveAndClose();
                    }
                });

                aceEditor.commands.addCommand({
                    name: "pyxisCloseOnEsc",
                    bindKey: { win: "Escape", mac: "Escape" },
                    exec: function() {
                        saveAndClose();
                    }
                });
            }

            let closed = false;
            function saveAndClose() {
                if (closed) return;
                closed = true;
                delete node._is_editing_vars;
                const finalVal = aceEditor ? aceEditor.getValue() : "";
                node.properties[propertyName] = finalVal;
                if (varWidget) varWidget.value = finalVal;
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (canvas.setDirtyCanvas) canvas.setDirtyCanvas(true, true);
                if (canvas.draw) canvas.draw(true, true);
                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("def-vars-edit");
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                window.removeEventListener("mousedown", onDocMouseDown, true);
                if (aceEditor) {
                    try { aceEditor.destroy(); } catch(e){}
                }
                container.remove();
            }
            container._saveAndClose = saveAndClose;

            const onDocMouseDown = (e) => {
                if (container.contains(e.target) || (e.target.closest && (e.target.closest('.ace_autocomplete') || e.target.closest('.ace_editor')))) {
                    return;
                }
                saveAndClose();
            };
            setTimeout(() => {
                window.addEventListener("mousedown", onDocMouseDown, true);
            }, 60);
        }

        function showFloatingDefinirVarsEditor(node, propertyName, titleName, clickEvent) {
            openInlineDefinirVarsEditor(node, propertyName);
        }

        function renderPythonHighlightedLine(ctx, text, startX, y) {
            if (!text) return;
            const tokenRegex = /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#[^\r\n]*|\b\d+(?:\.\d+)?|[=+*/%<>&|!~^-]+|\b(?:and|as|assert|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|not|or|pass|raise|return|try|while|with|yield)\b|[a-zA-Z_]\w*|\s+|[^\s\w])/g;
            let match;
            let curX = startX;
            while ((match = tokenRegex.exec(text)) !== null) {
                const tok = match[0];
                if (!tok) {
                    if (tokenRegex.lastIndex === match.index) tokenRegex.lastIndex++;
                    continue;
                }
                let color = "#f8f8f2";
                if (tok.startsWith("#")) {
                    color = "#6272a4";
                } else if (tok.startsWith('"') || tok.startsWith("'")) {
                    color = "#f1fa8c";
                } else if (/^\d/.test(tok)) {
                    color = "#bd93f9";
                } else if (/^[=+*/%<>&|!~^-]+$/.test(tok)) {
                    color = "#ff79c6";
                } else if (/^(and|as|assert|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|not|or|pass|raise|return|try|while|with|yield)$/.test(tok)) {
                    color = "#ff79c6";
                }
                ctx.fillStyle = color;
                ctx.fillText(tok, curX, y);
                curX += ctx.measureText(tok).width;
                if (tokenRegex.lastIndex === match.index) tokenRegex.lastIndex++;
            }
        }

        function setupDefineVarsNode(node) {
            const varWidget = node.widgets ? node.widgets.find(w => w.property === "variables") : null;
            if (!varWidget) return;

            varWidget.type = "custom";

            // Posicionamiento de ayuda '?' especifico para este nodo (libre de colisiones con la caja)
            node.getHelpButtonPos = function(size) {
                size = size || this.size;
                return [14, size[1] - 13];
            };

            node.computeSize = function(textVal) {
                const canvas = (this.graph && this.graph.canvas) || (typeof LGraphCanvas !== "undefined" && LGraphCanvas.active_canvas);
                const isResizingThis = !!(canvas && canvas.resizing_node === this);
                if (isResizingThis) {
                    return [200, 102];
                }

                const curW = (this._manual_width !== undefined) ? this._manual_width : ((this.size && this.size[0] > 0) ? this.size[0] : 220);
                const curH = (this._manual_height !== undefined) ? this._manual_height : ((this.size && this.size[1] > 0) ? this.size[1] : 102);
                return [Math.max(200, curW), Math.max(102, curH)];
            };

            node.onResize = function(size) {
                size[0] = Math.max(200, size[0]);
                size[1] = Math.max(102, size[1]);
                this._manual_width = size[0];
                this._manual_height = size[1];
            };

            varWidget.mouse = function(event, pos, node) {
                if (event.type === "mousedown" || event.type === "click") {
                    if (varWidget._scrollbar_info && pos) {
                        const sb = varWidget._scrollbar_info;
                        if (pos[0] >= sb.barX - 6 && pos[0] <= sb.barX + sb.barW + 6 && pos[1] >= sb.trackY && pos[1] <= sb.trackY + sb.trackH) {
                            const ratio = Math.max(0, Math.min(1, (pos[1] - sb.trackY) / sb.trackH));
                            varWidget._scroll_line = Math.round(ratio * sb.maxScroll);
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            const activeCanvas = (typeof LGraphCanvas !== "undefined" && LGraphCanvas.active_canvas);
                            if (activeCanvas && activeCanvas.draw) activeCanvas.draw(true, true);
                            return true;
                        }
                    }
                    openInlineDefinirVarsEditor(node, "variables");
                    return true;
                }
            };

            varWidget.callback = function(value, canvas, node, pos, event) {
                openInlineDefinirVarsEditor(node, "variables");
            };

            node.onDblClick = function(event, pos) {
                if (pos && pos[1] < 0) return false;
                openInlineDefinirVarsEditor(this, "variables");
                return true;
            };

            node.updateVarsSize = function() {
                if (!node.size || node.size[0] < 200 || node.size[1] < 102) {
                    node.size = [220, 102];
                }
            };

            varWidget.computeSize = function(width) {
                const minSz = node.computeSize ? node.computeSize() : [200, 102];
                return [width - 24, Math.max(28, minSz[1] - 48 - 26)];
            };

            varWidget.draw = function(ctx, node, width, y, height) {
                varWidget.last_y = y;
                if (node._is_editing_vars) {
                    return;
                }
                const text = String(node.properties.variables || varWidget.value || "");
                const trimmed = text.trim();
                const margin = 12;
                const wWidth = width - 24;
                const availableTextW = Math.max(80, wWidth - 20);

                let lines = [];
                if (varWidget._cached_var_text === text &&
                    typeof varWidget._cached_var_w === "number" &&
                    Math.abs(varWidget._cached_var_w - availableTextW) < 0.5 &&
                    Array.isArray(varWidget._cached_var_lines)) {
                    lines = varWidget._cached_var_lines;
                } else {
                    const rawLines = trimmed ? text.split('\n') : [];
                    rawLines.forEach(function(l) {
                        if (typeof containsAssdrawDrawing === "function" && containsAssdrawDrawing(l)) {
                            const wrapped = typeof wrapTextToPixelWidth === "function"
                                ? wrapTextToPixelWidth(l, availableTextW, "bold 12px Consolas, monospace")
                                : [l];
                            wrapped.forEach(function(wl) { lines.push(wl); });
                        } else {
                            lines.push(l);
                        }
                    });
                    varWidget._cached_var_text = text;
                    varWidget._cached_var_w = availableTextW;
                    varWidget._cached_var_lines = lines;
                }
                // La caja se adapta al interior del nodo reservando 26px para el icono de ayuda
                const wHeight = Math.max(28, node.size[1] - y - 26);

                ctx.save();
                ctx.fillStyle = "#12161f";
                ctx.strokeStyle = "#8b5cf6";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(margin, y, wWidth, wHeight, 8);
                else ctx.rect(margin, y, wWidth, wHeight);
                ctx.fill();
                ctx.stroke();

                if (!trimmed) {
                    delete varWidget._scrollbar_info;
                    ctx.fillStyle = "#64748b";
                    ctx.font = "italic 11px sans-serif";
                    ctx.textAlign = "left";
                    var placeholder = window.PyxisI18n ? window.PyxisI18n.t("nodes.placeholders.vars_empty") : "(click to define vars...)";
                    ctx.fillText(placeholder, margin + 10, y + 17);
                } else {
                    ctx.save();
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(margin + 2, y + 2, wWidth - 4, wHeight - 4, 6);
                    else ctx.rect(margin + 2, y + 2, wWidth - 4, wHeight - 4);
                    ctx.clip();

                    ctx.font = "bold 12px Consolas, monospace";
                    ctx.textAlign = "left";

                    const lineHeight = 20;
                    const availableH = wHeight - 10;
                    const maxVisibleLines = Math.max(1, Math.floor(availableH / lineHeight));
                    const totalLines = lines.length;
                    const isOverflowing = totalLines > maxVisibleLines;
                    const maxScroll = Math.max(0, totalLines - maxVisibleLines);
                    varWidget._max_scroll_lines = maxScroll;

                    if (varWidget._scroll_line === undefined || isNaN(varWidget._scroll_line)) {
                        varWidget._scroll_line = 0;
                    } else {
                        varWidget._scroll_line = Math.max(0, Math.min(varWidget._scroll_line, maxScroll));
                    }

                    const startLine = varWidget._scroll_line;

                    for (let i = 0; i < maxVisibleLines; i++) {
                        const lineIdx = startLine + i;
                        if (lineIdx >= totalLines) break;
                        let lineText = lines[lineIdx] || "";
                        if (isOverflowing && i === maxVisibleLines - 1 && lineIdx < totalLines - 1) {
                            if (!lineText.endsWith("...")) {
                                lineText = lineText.length > 20 ? (lineText.substring(0, lineText.length - 3) + "...") : (lineText + "...");
                            }
                        }
                        renderPythonHighlightedLine(ctx, lineText, margin + 10, y + 17 + i * lineHeight);
                    }
                    ctx.restore();

                    // Minimalist scrollbar rendered on top of box
                    if (isOverflowing) {
                        const trackPadding = 4;
                        const barW = 4;
                        const barX = margin + wWidth - barW - 4;
                        const trackY = y + trackPadding;
                        const trackH = Math.max(12, wHeight - trackPadding * 2);

                        varWidget._scrollbar_info = { barX, barW, trackY, trackH, maxScroll, boxX: margin, boxY: y, boxW: wWidth, boxH: wHeight };

                        ctx.save();
                        // Track groove
                        ctx.fillStyle = "rgba(255, 255, 255, 0.05)";
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(barX, trackY, barW, trackH, barW / 2);
                        else ctx.rect(barX, trackY, barW, trackH);
                        ctx.fill();

                        // Thumb
                        const thumbH = Math.max(12, Math.round((maxVisibleLines / totalLines) * trackH));
                        const maxTravel = trackH - thumbH;
                        const thumbY = trackY + (maxScroll > 0 ? (startLine / maxScroll) * maxTravel : 0);

                        ctx.fillStyle = "rgba(139, 92, 246, 0.6)";
                        ctx.beginPath();
                        if (ctx.roundRect) ctx.roundRect(barX, thumbY, barW, thumbH, barW / 2);
                        else ctx.rect(barX, thumbY, barW, thumbH);
                        ctx.fill();
                        ctx.restore();
                    } else {
                        delete varWidget._scrollbar_info;
                    }
                }
                ctx.restore();
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (this.updateVarsSize) this.updateVarsSize();
            };

            if (node.updateVarsSize) node.updateVarsSize();
        }

        window.setupMemoriaNode = setupMemoryNode;
        window.setupMemoryNode = setupMemoryNode;
        window.setupDefinirVarsNode = setupDefineVarsNode;
        window.setupDefineVarsNode = setupDefineVarsNode;


