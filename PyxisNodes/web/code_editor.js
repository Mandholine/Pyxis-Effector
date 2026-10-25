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
 * @file code_editor.js
 * @description Code editing, syntax validation, and autocompletion subsystem for Pyxis Effector.
 * Integrates Ace Editor for Python and Lua scripting, provides the context-aware completer
 * (getPyxisCodeCompleter) with hierarchical scoring, and manages script template persistence.
 * @module PyxisCodeEditor
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function setupScriptCodeNode(node) {
            if (!node.properties) node.properties = {};
            if (!node.properties.language) node.properties.language = "Python";
            if (node.properties.script === undefined) {
                node.properties.script = "result = 'Hello Pyxis ' + str(in1 if in1 else syl.text)";
            }
            if (node.properties.inputs_count === undefined) {
                node.properties.inputs_count = 2;
            }

            node.widgets_up = true;

            function updateCodigoScriptInputs() {
                const count = Math.max(1, parseInt(node.properties.inputs_count, 10) || 2);
                node.properties.inputs_count = count;

                const reqInputs = ["Loop In"];
                for (let i = 1; i <= count; i++) {
                    reqInputs.push("In" + i);
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
                        const pName = reqInputs[idx];
                        const pType = (pName === "Loop In") ? "loop" : "data";
                        node.addInput(pName, pType);
                    }

                    reqInputs.forEach((paramName, idx) => {
                        const inputSlot = node.inputs[idx];
                        inputSlot.name = paramName;
                        inputSlot.type = (paramName === "Loop In") ? "loop" : "data";
                        inputSlot.label = (paramName === "Loop In") ? "Loop In" : " ";
                        if (idx === 0) {
                            inputSlot.pos = [10, 18];
                        } else {
                            inputSlot.pos = [10, 34 + (idx - 1) * 23 + 9];
                        }

                        if (inputSlot.link === null || inputSlot.link === undefined) {
                            if (oldLinks[paramName] !== undefined && node.graph && node.graph.links) {
                                const linkId = oldLinks[paramName];
                                if (node.graph.links[linkId]) {
                                    inputSlot.link = linkId;
                                }
                            }
                        }
                    });
                } else if (node.inputs && node.inputs[0]) {
                    node.inputs[0].name = "Loop In";
                    node.inputs[0].label = "Loop In";
                }

                if (!node.outputs || node.outputs.length < 2) {
                    node.outputs = [
                        { name: "Loop Out", type: "loop", links: null },
                        { name: "Result", type: "data", links: null }
                    ];
                } else {
                    while (node.outputs.length > 2) {
                        node.removeOutput(node.outputs.length - 1);
                    }
                    node.outputs[0].name = "Loop Out";
                    node.outputs[0].type = "loop";
                    node.outputs[0].label = "Loop Out";
                    node.outputs[1].name = "Result";
                    node.outputs[1].type = "data";
                    node.outputs[1].label = "Result";
                }

                node.widgets = [];

                for (let i = 1; i <= count; i++) {
                    const paramName = "In" + i;
                    const propKey = paramName;
                    if (node.properties[propKey] === undefined) {
                        node.properties[propKey] = "";
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
                    w.y = 34 + (i - 1) * 23;
                    w.last_y = 34 + (i - 1) * 23;
                    setupSingleLineTextWidget(node, w, paramName, propKey);
                }

                if (node.computeSize) {
                    node.size = node.computeSize();
                } else {
                    node.size = [230, 34 + count * 23 + 52];
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            node.computeSize = function() {
                const count = Math.max(1, parseInt(node.properties.inputs_count, 10) || 2);
                let base_w = 230;
                let text_req_w = 0;
                if (node.properties) {
                    for (const p in node.properties) {
                        if (p === "script" || p === "language" || p === "inputs_count" || p === "outputs_count") continue;
                        const val = String(node.properties[p] || "");
                        if (val.length > 0) {
                            const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                            if (tw > text_req_w) text_req_w = tw;
                        }
                    }
                }
                const right_space = getNodeRightReserve(node);
                const boxW = Math.max(65, Math.ceil(text_req_w + 28));
                const contentH = 34 + count * 23 + 52;
                return [Math.max(base_w, 22 + boxW + right_space), contentH];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                const count = Math.max(1, parseInt(this.properties.inputs_count, 10) || 2);
                const nodeW = this.size[0];
                const centerX = nodeW / 2;

                if (this.inputs) {
                    this.inputs.forEach((inp, idx) => {
                        if (inp.name === "Loop In") {
                            inp.pos = [10, 18];
                            inp.label = "Loop In";
                        } else {
                            inp.label = " ";
                            inp.pos = [10, 34 + (idx - 1) * 23 + 9];
                        }
                    });
                }

                ctx.save();

                const lang = String(this.properties.language || "Python");
                const isPython = (lang === "Python");
                ctx.font = "bold 10px monospace";
                const langTextW = ctx.measureText(lang).width;
                const langBadgeW = Math.max(54, langTextW + 14);
                const langBadgeH = 20;
                const langBadgeX = nodeW - langBadgeW - 8;
                const langBadgeY = -25;

                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = isPython ? "#8b5cf6" : "#10b981";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(langBadgeX, langBadgeY, langBadgeW, langBadgeH, 10);
                else ctx.rect(langBadgeX, langBadgeY, langBadgeW, langBadgeH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = isPython ? "#c084fc" : "#a7f3d0";
                ctx.textAlign = "center";
                ctx.fillText(lang, langBadgeX + langBadgeW / 2, langBadgeY + 14);

                // Check syntax on initial render if not done
                if (this.has_syntax_error === undefined) {
                    const check = validatePyxisScriptSyntax(this.properties.script, lang);
                    this.has_syntax_error = !check.valid;
                    this.syntax_error_msg = check.error;
                }

                // Render Red Pulsing Glowing Warning Icon on Title Bar
                if (this.has_syntax_error) {
                    const time = Date.now();
                    const pulse = 0.5 + 0.5 * Math.sin(time / 220);

                    ctx.save();
                    const errIconX = langBadgeX - 18;
                    const errIconY = -15;
                    const errRadius = 7.5;

                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    ctx.shadowColor = `rgba(239, 68, 68, ${0.65 + pulse * 0.35})`;
                    ctx.shadowBlur = 9 + pulse * 6;

                    ctx.fillStyle = `rgba(239, 68, 68, ${0.85 + pulse * 0.15})`;
                    ctx.beginPath();
                    ctx.arc(errIconX, errIconY, errRadius, 0, Math.PI * 2);
                    ctx.fill();

                    ctx.shadowColor = "transparent";
                    ctx.shadowBlur = 0;
                    ctx.font = "bold 11px sans-serif";
                    ctx.fillStyle = "#FFFFFF";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("!", errIconX, errIconY + 0.5);

                    ctx.restore();

                    if (this.graph && this.graph.canvas) {
                        this.graph.canvas.setDirtyCanvas(true, false);
                    }
                }

                const btnW = 28;
                const btnH = 20;
                const btnY = 8;
                const btnPlusX = centerX - 32;
                const btnMinusX = centerX + 4;

                ctx.fillStyle = "#1e293b";
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnPlusX, btnY, btnW, btnH, 4);
                else ctx.rect(btnPlusX, btnY, btnW, btnH);
                ctx.fill();
                ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.font = "bold 14px sans-serif";
                ctx.fillStyle = "#38bdf8";
                ctx.textAlign = "center";
                ctx.fillText("+", btnPlusX + btnW / 2, btnY + 14);

                const canMinus = count > 1;
                ctx.fillStyle = canMinus ? "#1e293b" : "#0f172a";
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnMinusX, btnY, btnW, btnH, 4);
                else ctx.rect(btnMinusX, btnY, btnW, btnH);
                ctx.fill();
                ctx.strokeStyle = canMinus ? "rgba(255, 255, 255, 0.25)" : "rgba(255, 255, 255, 0.1)";
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.font = "bold 14px sans-serif";
                ctx.fillStyle = canMinus ? "#ef4444" : "#475569";
                ctx.textAlign = "center";
                ctx.fillText("-", btnMinusX + btnW / 2, btnY + 14);

                const previewY = 34 + count * 23 + 14;
                const scriptLines = String(this.properties.script || "").split('\n');
                const previewLine1 = scriptLines[0] || "";
                
                ctx.font = "italic 11px monospace";
                ctx.fillStyle = "#94A3B8";
                ctx.textAlign = "left";

                let disp1 = previewLine1;
                const maxW = nodeW - 24;
                if (ctx.measureText(disp1).width > maxW) {
                    disp1 = disp1.substring(0, 26) + "...";
                }

                ctx.fillText(disp1, 12, previewY);

                const editorBtnX = 12;
                const editorBtnY = previewY + 10;
                const editorBtnW = nodeW - 24;
                const editorBtnH = 22;

                ctx.fillStyle = "#2563EB";
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(editorBtnX, editorBtnY, editorBtnW, editorBtnH, 5);
                else ctx.rect(editorBtnX, editorBtnY, editorBtnW, editorBtnH);
                ctx.fill();

                ctx.font = "bold 11px sans-serif";
                ctx.fillStyle = "#FFFFFF";
                ctx.textAlign = "center";
                var editorBtnText = window.PyxisI18n ? window.PyxisI18n.t("nodes.placeholders.open_script_editor") : "Open Script Editor";
                ctx.fillText(editorBtnText, editorBtnX + editorBtnW / 2, editorBtnY + 15);

                ctx.restore();
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, pos, canvas) {
                if (oldMouseDown && oldMouseDown.call(this, e, pos, canvas)) return true;

                const count = Math.max(1, parseInt(this.properties.inputs_count, 10) || 2);
                const nodeW = this.size[0];
                const centerX = nodeW / 2;

                const langBadgeW = 64;
                const langBadgeH = 20;
                const langBadgeX = nodeW - langBadgeW - 8;
                const langBadgeY = -25;
                if (pos[0] >= langBadgeX && pos[0] <= langBadgeX + langBadgeW &&
                    pos[1] >= langBadgeY && pos[1] <= langBadgeY + langBadgeH) {
                    const curLang = this.properties.language || "Python";
                    const nextLang = (curLang === "Python") ? "Lua" : "Python";
                    this.properties.language = nextLang;
                    const check = validatePyxisScriptSyntax(this.properties.script, nextLang);
                    this.has_syntax_error = !check.valid;
                    this.syntax_error_msg = check.error;
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    return true;
                }

                const btnW = 28;
                const btnH = 20;
                const btnY = 8;
                const btnPlusX = centerX - 32;
                const btnMinusX = centerX + 4;

                if (pos[0] >= btnPlusX && pos[0] <= btnPlusX + btnW &&
                    pos[1] >= btnY && pos[1] <= btnY + btnH) {
                    this.properties.inputs_count = count + 1;
                    updateCodigoScriptInputs();
                    if (this.computeSize) this.size = this.computeSize();
                    if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                    if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    return true;
                }

                if (pos[0] >= btnMinusX && pos[0] <= btnMinusX + btnW &&
                    pos[1] >= btnY && pos[1] <= btnY + btnH) {
                    if (count > 1) {
                        this.properties.inputs_count = count - 1;
                        updateCodigoScriptInputs();
                        if (this.computeSize) this.size = this.computeSize();
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    }
                    return true;
                }

                for (let i = 1; i <= count; i++) {
                    const boxY = 34 + (i - 1) * 23;
                    const margin = 22;
                    const paramName = "In" + i;
                    const propKey = paramName;
                    const w = this.widgets ? this.widgets.find(widget => widget.property === propKey) : null;
                    const wWidth = getInlineBoxWidth(this, w, paramName, propKey);
                    const wHeight = 18;

                    if (pos[0] >= margin - 6 && pos[0] <= margin + wWidth + 10 &&
                        pos[1] >= boxY - 2 && pos[1] <= boxY + wHeight + 4) {
                        openInlineSingleLineEditor(this, w, propKey, paramName, e);
                        return true;
                    }
                }

                const previewY = 34 + count * 23 + 14;
                const editorBtnX = 12;
                const editorBtnY = previewY + 10;
                const editorBtnW = nodeW - 24;
                const editorBtnH = 22;

                if (pos[0] >= editorBtnX && pos[0] <= editorBtnX + editorBtnW &&
                    pos[1] >= editorBtnY && pos[1] <= editorBtnY + editorBtnH) {
                    openCodigoScriptModal(this);
                    return true;
                }

                if (pos[0] >= 0 && pos[0] <= nodeW && pos[1] >= 0 && pos[1] <= this.size[1]) {
                    return true;
                }

                return false;
            };

            node.onDblClick = null;

            const oldMouseMove = node.onMouseMove;
            node.onMouseMove = function(e, pos, canvas) {
                if (oldMouseMove) oldMouseMove.call(this, e, pos, canvas);
                if (this.has_syntax_error) {
                    const nodeW = this.size[0];
                    const langBadgeW = 64;
                    const langBadgeX = nodeW - langBadgeW - 8;
                    const errIconX = langBadgeX - 18;
                    const errIconY = -15;
                    const dist = Math.hypot(pos[0] - errIconX, pos[1] - errIconY);
                    if (dist <= 14) {
                        showPyxisSyntaxErrorTooltip(this, e);
                        return;
                    }
                }
                hidePyxisSyntaxErrorTooltip();
            };

            const oldMouseLeave = node.onMouseLeave;
            node.onMouseLeave = function(e) {
                if (oldMouseLeave) oldMouseLeave.call(this, e);
                hidePyxisSyntaxErrorTooltip();
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateCodigoScriptInputs();
            };

            updateCodigoScriptInputs();
        }

        let __pyxis_ace_completer_registered = false;

        /**
         * Extracts the exact syntactic prefix preceding the cursor position in the code editor.
         * Distinguishes numeric constants from identifiers, handling dot navigation (e.g. "syl.dur"),
         * ASS escape slashes (e.g. "\\pos"), and variable sigils for context-aware autocompletion.
         *
         * @param {string} lineText - Entire line of text where the cursor is situated.
         * @param {number} col - Zero-based column index of the cursor.
         * @returns {string} The resolved token prefix to be matched against completion captions.
         */
        function getExactPyxisPrefix(lineText, col) {
            const textBefore = lineText.slice(0, col);
            const numIdMatch = textBefore.match(/(?:^|[^a-zA-Z0-9_\$])(?:\d+(?:\.\d+)?)([a-zA-Z_\$\\\][a-zA-Z0-9_\.\\\$]*)$/);
            if (numIdMatch) {
                return numIdMatch[1];
            }
            const idMatch = textBefore.match(/([a-zA-Z_\$\\\][a-zA-Z0-9_\.\\\$]*)$/);
            if (idMatch) {
                return idMatch[1];
            }
            return "";
        }

        /**
         * Builds and returns the comprehensive Ace Editor code completer for Pyxis Effector.
         * Registers context-aware autocomplete items covering syllable metrics (syl.*), line properties (line.*),
         * character data (char.*), word data (word.*), easing functions, wave generators, ASS override tags,
         * audio spectrum helpers, and dynamic script node input slots with HTML documentation tooltips.
         *
         * @returns {Object} Ace autocompleter object conforming to the ext-language_tools specification.
         */
        function getPyxisCodeCompleter() {
            const completerObj = {
                identifierRegexps: [/[a-zA-Z_0-9\.\\\$]/],
                autoInsert: false,
                insertMatch: function(editor, data) {
                    if (!data) return false;
                    editor.startOperation({ command: { name: "insertMatch" } });
                    const pos = editor.getCursorPosition();
                    const lineText = editor.session.getLine(pos.row);
                    const exactPrefix = getExactPyxisPrefix(lineText, pos.column);
                    const Range = ace.require("ace/range").Range;
                    const replaceRange = new Range(pos.row, pos.column - exactPrefix.length, pos.row, pos.column);
                    
                    if (data.snippet) {
                        editor.session.remove(replaceRange);
                        const snippetManager = ace.require("ace/snippets").snippetManager;
                        if (snippetManager) {
                            snippetManager.insertSnippet(editor, data.snippet);
                        } else {
                            editor.execCommand("insertstring", data.value || data.caption);
                        }
                    } else {
                        editor.session.replace(replaceRange, data.value || data.caption);
                    }
                    editor.endOperation();
                    return true;
                },
                getCompletions: function(editor, session, pos, prefix, callback) {
                    const node = window.__active_code_script_node;
                    const inputCount = (node && node.properties && node.properties.inputs_count) ? parseInt(node.properties.inputs_count, 10) : 2;
                    const isPython = !(node && node.properties && node.properties.language === "Lua");

                    const exactPrefix = getExactPyxisPrefix(session.getLine(pos.row), pos.column);
                    const checkPrefix = exactPrefix || prefix;

                    const isManual = editor.completer && editor.completer.autoShownManual;
                    if (!isManual && checkPrefix && checkPrefix.length < 3 && !checkPrefix.includes(".") && !checkPrefix.startsWith("\\")) {
                        return callback(null, []);
                    }

                    const completions = [
                        // --- 1. Syllable (syl) Context Properties ---
                        { caption: "syl.text", value: "syl.text", meta: "syl (str)", docHTML: "<b>syl.text</b>: Clean text of the current syllable", score: 1000 },
                        { caption: "syl.text_stripped", value: "syl.text_stripped", meta: "syl (str)", docHTML: "<b>syl.text_stripped</b>: Syllable text without inline tags", score: 980 },
                        { caption: "syl.text_spacestripped", value: "syl.text_spacestripped", meta: "syl (str)", docHTML: "<b>syl.text_spacestripped</b>: Syllable text without whitespace", score: 970 },
                        { caption: "syl.i", value: "syl.i", meta: "syl (int)", docHTML: "<b>syl.i</b>: Syllable index in the line (1-based)", score: 1000 },
                        { caption: "syl.n", value: "syl.n", meta: "syl (int)", docHTML: "<b>syl.n</b>: Total number of syllables in the line", score: 1000 },
                        { caption: "syl.duration", value: "syl.duration", meta: "syl (int)", docHTML: "<b>syl.duration</b>: Syllable duration in milliseconds", score: 1000 },
                        { caption: "syl.dur", value: "syl.dur", meta: "syl (int)", docHTML: "<b>syl.dur</b>: Alias of syl.duration (ms)", score: 990 },
                        { caption: "syl.start_time", value: "syl.start_time", meta: "syl (int)", docHTML: "<b>syl.start_time</b>: Absolute start time in ms", score: 1000 },
                        { caption: "syl.end_time", value: "syl.end_time", meta: "syl (int)", docHTML: "<b>syl.end_time</b>: Absolute end time in ms", score: 1000 },
                        { caption: "syl.mid_time", value: "syl.mid_time", meta: "syl (float)", docHTML: "<b>syl.mid_time</b>: Absolute midpoint time in ms", score: 980 },
                        { caption: "syl.syl_start", value: "syl.syl_start", meta: "syl (int)", docHTML: "<b>syl.syl_start</b>: Relative start offset from line start (ms)", score: 1000 },
                        { caption: "syl.syl_end", value: "syl.syl_end", meta: "syl (int)", docHTML: "<b>syl.syl_end</b>: Relative end offset from line start (ms)", score: 1000 },
                        { caption: "syl.syl_mid", value: "syl.syl_mid", meta: "syl (float)", docHTML: "<b>syl.syl_mid</b>: Relative midpoint offset from line start (ms)", score: 980 },
                        { caption: "syl.x", value: "syl.x", meta: "syl (float)", docHTML: "<b>syl.x</b>: Calculated X position (syllable center)", score: 1000 },
                        { caption: "syl.y", value: "syl.y", meta: "syl (float)", docHTML: "<b>syl.y</b>: Calculated Y position (baseline)", score: 1000 },
                        { caption: "syl.center", value: "syl.center", meta: "syl (float)", docHTML: "<b>syl.center</b>: Syllable center X coordinate", score: 980 },
                        { caption: "syl.middle", value: "syl.middle", meta: "syl (float)", docHTML: "<b>syl.middle</b>: Syllable middle Y coordinate", score: 980 },
                        { caption: "syl.left", value: "syl.left", meta: "syl (float)", docHTML: "<b>syl.left</b>: Left edge in pixels", score: 980 },
                        { caption: "syl.right", value: "syl.right", meta: "syl (float)", docHTML: "<b>syl.right</b>: Right edge in pixels", score: 980 },
                        { caption: "syl.top", value: "syl.top", meta: "syl (float)", docHTML: "<b>syl.top</b>: Top edge in pixels", score: 980 },
                        { caption: "syl.bottom", value: "syl.bottom", meta: "syl (float)", docHTML: "<b>syl.bottom</b>: Bottom edge in pixels", score: 980 },
                        { caption: "syl.width", value: "syl.width", meta: "syl (float)", docHTML: "<b>syl.width</b>: Typographic width of the syllable", score: 980 },
                        { caption: "syl.height", value: "syl.height", meta: "syl (float)", docHTML: "<b>syl.height</b>: Typographic height of the syllable", score: 980 },
                        { caption: "syl.prespace", value: "syl.prespace", meta: "syl (str)", docHTML: "<b>syl.prespace</b>: Leading whitespace", score: 950 },
                        { caption: "syl.postspace", value: "syl.postspace", meta: "syl (str)", docHTML: "<b>syl.postspace</b>: Trailing whitespace", score: 950 },
                        { caption: "syl.descent", value: "syl.descent", meta: "syl (float)", docHTML: "<b>syl.descent</b>: Typographic font descent", score: 950 },
                        { caption: "syl.actor", value: "syl.actor", meta: "syl (str)", docHTML: "<b>syl.actor</b>: Line actor name", score: 950 },
                        { caption: "syl.style", value: "syl.style", meta: "syl (str)", docHTML: "<b>syl.style</b>: Line ASS style name", score: 950 },
                        { caption: "syl.effect", value: "syl.effect", meta: "syl (str)", docHTML: "<b>syl.effect</b>: Line ASS Effect field", score: 950 },
                        { caption: "syl.layer", value: "syl.layer", meta: "syl (int)", docHTML: "<b>syl.layer</b>: ASS rendering layer", score: 950 },
                        { caption: "syl.is_first", value: "syl.is_first", meta: "syl (bool)", docHTML: "<b>syl.is_first</b>: True if first syllable in line", score: 960 },
                        { caption: "syl.is_last", value: "syl.is_last", meta: "syl (bool)", docHTML: "<b>syl.is_last</b>: True if last syllable in line", score: 960 },
                        { caption: "syl.has_prev", value: "syl.has_prev", meta: "syl (bool)", docHTML: "<b>syl.has_prev</b>: True if preceding syllable exists", score: 960 },
                        { caption: "syl.has_next", value: "syl.has_next", meta: "syl (bool)", docHTML: "<b>syl.has_next</b>: True if succeeding syllable exists", score: 960 },
                        { caption: "syl.color1", value: "syl.color1", meta: "syl (str)", docHTML: "<b>syl.color1</b>: Primary fill color of the syllable (ASS format)", score: 960 },
                        { caption: "syl.color2", value: "syl.color2", meta: "syl (str)", docHTML: "<b>syl.color2</b>: Secondary karaoke color of the syllable", score: 950 },
                        { caption: "syl.color3", value: "syl.color3", meta: "syl (str)", docHTML: "<b>syl.color3</b>: Outline / border color of the syllable", score: 960 },
                        { caption: "syl.color4", value: "syl.color4", meta: "syl (str)", docHTML: "<b>syl.color4</b>: Shadow color of the syllable", score: 950 },
                        { caption: "syl.fontsize", value: "syl.fontsize", meta: "syl (float)", docHTML: "<b>syl.fontsize</b>: Font size of the syllable in pt/px", score: 970 },
                        { caption: "syl.fontname", value: "syl.fontname", meta: "syl (str)", docHTML: "<b>syl.fontname</b>: Font family name of the syllable", score: 960 },
                        { caption: "syl.bold", value: "syl.bold", meta: "syl (bool)", docHTML: "<b>syl.bold</b>: True if syllable font is bold", score: 950 },
                        { caption: "syl.italic", value: "syl.italic", meta: "syl (bool)", docHTML: "<b>syl.italic</b>: True if syllable font is italic", score: 950 },
                        { caption: "syl.scale_x", value: "syl.scale_x", meta: "syl (float)", docHTML: "<b>syl.scale_x</b>: Horizontal font scale percentage (100 = 100%)", score: 960 },
                        { caption: "syl.scale_y", value: "syl.scale_y", meta: "syl (float)", docHTML: "<b>syl.scale_y</b>: Vertical font scale percentage (100 = 100%)", score: 960 },
                        { caption: "syl.spacing", value: "syl.spacing", meta: "syl (float)", docHTML: "<b>syl.spacing</b>: Inter-character tracking / spacing (\\fsp)", score: 960 },
                        { caption: "syl.outline", value: "syl.outline", meta: "syl (float)", docHTML: "<b>syl.outline</b>: Outline width in pixels (\\bord)", score: 960 },
                        { caption: "syl.shadow", value: "syl.shadow", meta: "syl (float)", docHTML: "<b>syl.shadow</b>: Shadow distance in pixels (\\shad)", score: 950 },
                        { caption: "syl.align", value: "syl.align", meta: "syl (int)", docHTML: "<b>syl.align</b>: Active numpad alignment (1-9)", score: 950 },
                        { caption: "syl.pos_x", value: "syl.pos_x", meta: "syl (float)", docHTML: "<b>syl.pos_x</b>: Active X coordinate override or anchor", score: 960 },
                        { caption: "syl.pos_y", value: "syl.pos_y", meta: "syl (float)", docHTML: "<b>syl.pos_y</b>: Active Y coordinate override or anchor", score: 960 },
                        { caption: "syl.org_x", value: "syl.org_x", meta: "syl (float)", docHTML: "<b>syl.org_x</b>: Active origin X coordinate (\\org)", score: 950 },
                        { caption: "syl.org_y", value: "syl.org_y", meta: "syl (float)", docHTML: "<b>syl.org_y</b>: Active origin Y coordinate (\\org)", score: 950 },

                        // --- 2. Character (char) Context Properties ---
                        { caption: "char.text", value: "char.text", meta: "char (str)", docHTML: "<b>char.text</b>: Text of current character", score: 1000 },
                        { caption: "char.text_stripped", value: "char.text_stripped", meta: "char (str)", docHTML: "<b>char.text_stripped</b>: Character text without inline tags", score: 980 },
                        { caption: "char.i", value: "char.i", meta: "char (int)", docHTML: "<b>char.i</b>: Character index in line/syllable (1-based)", score: 1000 },
                        { caption: "char.n", value: "char.n", meta: "char (int)", docHTML: "<b>char.n</b>: Total number of characters", score: 1000 },
                        { caption: "char.duration", value: "char.duration", meta: "char (int)", docHTML: "<b>char.duration</b>: Character duration in milliseconds", score: 1000 },
                        { caption: "char.dur", value: "char.dur", meta: "char (int)", docHTML: "<b>char.dur</b>: Alias of char.duration", score: 990 },
                        { caption: "char.start_time", value: "char.start_time", meta: "char (int)", docHTML: "<b>char.start_time</b>: Character absolute start time in ms", score: 1000 },
                        { caption: "char.end_time", value: "char.end_time", meta: "char (int)", docHTML: "<b>char.end_time</b>: Character absolute end time in ms", score: 1000 },
                        { caption: "char.mid_time", value: "char.mid_time", meta: "char (float)", docHTML: "<b>char.mid_time</b>: Character absolute midpoint in ms", score: 980 },
                        { caption: "char.char_start", value: "char.char_start", meta: "char (int)", docHTML: "<b>char.char_start</b>: Relative start offset of character from line (ms)", score: 1000 },
                        { caption: "char.char_end", value: "char.char_end", meta: "char (int)", docHTML: "<b>char.char_end</b>: Relative end offset of character from line (ms)", score: 1000 },
                        { caption: "char.char_mid", value: "char.char_mid", meta: "char (float)", docHTML: "<b>char.char_mid</b>: Relative midpoint offset of character (ms)", score: 980 },
                        { caption: "char.x", value: "char.x", meta: "char (float)", docHTML: "<b>char.x</b>: Calculated X position (character center)", score: 1000 },
                        { caption: "char.y", value: "char.y", meta: "char (float)", docHTML: "<b>char.y</b>: Calculated Y position of the character", score: 1000 },
                        { caption: "char.center", value: "char.center", meta: "char (float)", docHTML: "<b>char.center</b>: Character center X coordinate", score: 980 },
                        { caption: "char.middle", value: "char.middle", meta: "char (float)", docHTML: "<b>char.middle</b>: Character middle Y coordinate", score: 980 },
                        { caption: "char.left", value: "char.left", meta: "char (float)", docHTML: "<b>char.left</b>: Character left edge in pixels", score: 980 },
                        { caption: "char.right", value: "char.right", meta: "char (float)", docHTML: "<b>char.right</b>: Character right edge in pixels", score: 980 },
                        { caption: "char.top", value: "char.top", meta: "char (float)", docHTML: "<b>char.top</b>: Character top edge in pixels", score: 980 },
                        { caption: "char.bottom", value: "char.bottom", meta: "char (float)", docHTML: "<b>char.bottom</b>: Character bottom edge in pixels", score: 980 },
                        { caption: "char.width", value: "char.width", meta: "char (float)", docHTML: "<b>char.width</b>: Character width in pixels", score: 980 },
                        { caption: "char.height", value: "char.height", meta: "char (float)", docHTML: "<b>char.height</b>: Character height in pixels", score: 980 },
                        { caption: "char.actor", value: "char.actor", meta: "char (str)", docHTML: "<b>char.actor</b>: Line actor name", score: 950 },
                        { caption: "char.style", value: "char.style", meta: "char (str)", docHTML: "<b>char.style</b>: ASS style name", score: 950 },
                        { caption: "char.is_first", value: "char.is_first", meta: "char (bool)", docHTML: "<b>char.is_first</b>: True if first character", score: 960 },
                        { caption: "char.is_last", value: "char.is_last", meta: "char (bool)", docHTML: "<b>char.is_last</b>: True if last character", score: 960 },

                        // --- 3. Word (word) Context Properties ---
                        { caption: "word.text", value: "word.text", meta: "word (str)", docHTML: "<b>word.text</b>: Clean text of the current word", score: 1000 },
                        { caption: "word.text_stripped", value: "word.text_stripped", meta: "word (str)", docHTML: "<b>word.text_stripped</b>: Word text without inline tags", score: 980 },
                        { caption: "word.i", value: "word.i", meta: "word (int)", docHTML: "<b>word.i</b>: Word index in line (1-based)", score: 1000 },
                        { caption: "word.n", value: "word.n", meta: "word (int)", docHTML: "<b>word.n</b>: Total number of words in line", score: 1000 },
                        { caption: "word.duration", value: "word.duration", meta: "word (int)", docHTML: "<b>word.duration</b>: Word duration in milliseconds", score: 1000 },
                        { caption: "word.dur", value: "word.dur", meta: "word (int)", docHTML: "<b>word.dur</b>: Alias of word.duration", score: 990 },
                        { caption: "word.start_time", value: "word.start_time", meta: "word (int)", docHTML: "<b>word.start_time</b>: Absolute start time in ms", score: 1000 },
                        { caption: "word.end_time", value: "word.end_time", meta: "word (int)", docHTML: "<b>word.end_time</b>: Absolute end time in ms", score: 1000 },
                        { caption: "word.mid_time", value: "word.mid_time", meta: "word (float)", docHTML: "<b>word.mid_time</b>: Absolute midpoint time in ms", score: 980 },
                        { caption: "word.word_start", value: "word.word_start", meta: "word (int)", docHTML: "<b>word.word_start</b>: Relative start offset of word from line (ms)", score: 1000 },
                        { caption: "word.word_end", value: "word.word_end", meta: "word (int)", docHTML: "<b>word.word_end</b>: Relative end offset of word from line (ms)", score: 1000 },
                        { caption: "word.word_mid", value: "word.word_mid", meta: "word (float)", docHTML: "<b>word.word_mid</b>: Relative midpoint offset of word (ms)", score: 980 },
                        { caption: "word.x", value: "word.x", meta: "word (float)", docHTML: "<b>word.x</b>: Calculated X position (word center)", score: 1000 },
                        { caption: "word.y", value: "word.y", meta: "word (float)", docHTML: "<b>word.y</b>: Calculated Y position (word baseline)", score: 1000 },
                        { caption: "word.center", value: "word.center", meta: "word (float)", docHTML: "<b>word.center</b>: Word center X coordinate", score: 980 },
                        { caption: "word.middle", value: "word.middle", meta: "word (float)", docHTML: "<b>word.middle</b>: Word middle Y coordinate", score: 980 },
                        { caption: "word.left", value: "word.left", meta: "word (float)", docHTML: "<b>word.left</b>: Word left edge in pixels", score: 980 },
                        { caption: "word.right", value: "word.right", meta: "word (float)", docHTML: "<b>word.right</b>: Word right edge in pixels", score: 980 },
                        { caption: "word.top", value: "word.top", meta: "word (float)", docHTML: "<b>word.top</b>: Word top edge in pixels", score: 980 },
                        { caption: "word.bottom", value: "word.bottom", meta: "word (float)", docHTML: "<b>word.bottom</b>: Word bottom edge in pixels", score: 980 },
                        { caption: "word.width", value: "word.width", meta: "word (float)", docHTML: "<b>word.width</b>: Word typographical width in pixels", score: 980 },
                        { caption: "word.height", value: "word.height", meta: "word (float)", docHTML: "<b>word.height</b>: Word typographical height in pixels", score: 980 },
                        { caption: "word.is_first", value: "word.is_first", meta: "word (bool)", docHTML: "<b>word.is_first</b>: True if first word in line", score: 960 },
                        { caption: "word.is_last", value: "word.is_last", meta: "word (bool)", docHTML: "<b>word.is_last</b>: True if last word in line", score: 960 },

                        // --- 4. Line (line / l) Context Properties ---
                        { caption: "line.text", value: "line.text", meta: "line (str)", docHTML: "<b>line.text</b>: Clean text of the full line", score: 990 },
                        { caption: "line.raw_text", value: "line.raw_text", meta: "line (str)", docHTML: "<b>line.raw_text</b>: Text with original ASS tags", score: 990 },
                        { caption: "line.i", value: "line.i", meta: "line (int)", docHTML: "<b>line.i</b>: Line number or index in file", score: 980 },
                        { caption: "line.n", value: "line.n", meta: "line (int)", docHTML: "<b>line.n</b>: Total number of lines", score: 980 },
                        { caption: "line.duration", value: "line.duration", meta: "line (int)", docHTML: "<b>line.duration</b>: Total duration of the line (ms)", score: 980 },
                        { caption: "line.dur", value: "line.dur", meta: "line (int)", docHTML: "<b>line.dur</b>: Alias of line.duration", score: 980 },
                        { caption: "line.start_time", value: "line.start_time", meta: "line (int)", docHTML: "<b>line.start_time</b>: Line start time (ms)", score: 980 },
                        { caption: "line.end_time", value: "line.end_time", meta: "line (int)", docHTML: "<b>line.end_time</b>: Line end time (ms)", score: 980 },
                        { caption: "line.mid_time", value: "line.mid_time", meta: "line (float)", docHTML: "<b>line.mid_time</b>: Line midpoint time (ms)", score: 970 },
                        { caption: "line.layer", value: "line.layer", meta: "line (int)", docHTML: "<b>line.layer</b>: ASS layer of the line", score: 980 },
                        { caption: "line.style", value: "line.style", meta: "line (str)", docHTML: "<b>line.style</b>: ASS style name", score: 980 },
                        { caption: "line.actor", value: "line.actor", meta: "line (str)", docHTML: "<b>line.actor</b>: Actor name", score: 980 },
                        { caption: "line.effect", value: "line.effect", meta: "line (str)", docHTML: "<b>line.effect</b>: ASS Effect field", score: 980 },
                        { caption: "line.margin_l", value: "line.margin_l", meta: "line (int)", docHTML: "<b>line.margin_l</b>: Left margin in px", score: 980 },
                        { caption: "line.margin_r", value: "line.margin_r", meta: "line (int)", docHTML: "<b>line.margin_r</b>: Right margin in px", score: 980 },
                        { caption: "line.margin_v", value: "line.margin_v", meta: "line (int)", docHTML: "<b>line.margin_v</b>: Vertical margin in px", score: 980 },
                        { caption: "line.width", value: "line.width", meta: "line (float)", docHTML: "<b>line.width</b>: Total line width in px", score: 970 },
                        { caption: "line.height", value: "line.height", meta: "line (float)", docHTML: "<b>line.height</b>: Total line height in px", score: 970 },
                        { caption: "line.center", value: "line.center", meta: "line (float)", docHTML: "<b>line.center</b>: Line center X coordinate", score: 970 },
                        { caption: "line.middle", value: "line.middle", meta: "line (float)", docHTML: "<b>line.middle</b>: Line middle Y coordinate", score: 970 },
                        { caption: "line.left", value: "line.left", meta: "line (float)", docHTML: "<b>line.left</b>: Line left edge", score: 970 },
                        { caption: "line.right", value: "line.right", meta: "line (float)", docHTML: "<b>line.right</b>: Line right edge", score: 970 },

                        { caption: "l.width", value: "l.width", meta: "l (float)", docHTML: "<b>l.width</b>: Alias of line.width (Line width)", score: 970 },
                        { caption: "l.height", value: "l.height", meta: "l (float)", docHTML: "<b>l.height</b>: Alias of line.height (Line height)", score: 970 },
                        { caption: "l.center", value: "l.center", meta: "l (float)", docHTML: "<b>l.center</b>: Alias of line.center (Center X)", score: 970 },
                        { caption: "l.middle", value: "l.middle", meta: "l (float)", docHTML: "<b>l.middle</b>: Alias of line.middle (Center Y)", score: 970 },
                        { caption: "l.left", value: "l.left", meta: "l (float)", docHTML: "<b>l.left</b>: Alias of line.left (Left edge)", score: 970 },
                        { caption: "l.right", value: "l.right", meta: "l (float)", docHTML: "<b>l.right</b>: Alias of line.right (Right edge)", score: 970 },
                        { caption: "l.text", value: "l.text", meta: "l (str)", docHTML: "<b>l.text</b>: Alias of line.text", score: 970 },
                        { caption: "l.duration", value: "l.duration", meta: "l (int)", docHTML: "<b>l.duration</b>: Alias of line.duration", score: 970 },
                        { caption: "l.dur", value: "l.dur", meta: "l (int)", docHTML: "<b>l.dur</b>: Alias of line.dur", score: 970 },
                        { caption: "l.start_time", value: "l.start_time", meta: "l (int)", docHTML: "<b>l.start_time</b>: Alias of line.start_time", score: 970 },
                        { caption: "l.end_time", value: "l.end_time", meta: "l (int)", docHTML: "<b>l.end_time</b>: Alias of line.end_time", score: 970 },
                        { caption: "l.i", value: "l.i", meta: "l (int)", docHTML: "<b>l.i</b>: Alias of line.i", score: 970 },
                        { caption: "l.n", value: "l.n", meta: "l (int)", docHTML: "<b>l.n</b>: Alias of line.n", score: 970 },
                        { caption: "l.layer", value: "l.layer", meta: "l (int)", docHTML: "<b>l.layer</b>: Alias of line.layer", score: 970 },
                        { caption: "l.style", value: "l.style", meta: "l (str)", docHTML: "<b>l.style</b>: Alias of line.style", score: 970 },

                        // --- 5. Effect Frame (fx) Context Properties ---
                        { caption: "fx.pos_x", value: "fx.pos_x", meta: "fx (float)", docHTML: "<b>fx.pos_x</b>: Calculated X position for the effect", score: 990 },
                        { caption: "fx.pos_y", value: "fx.pos_y", meta: "fx (float)", docHTML: "<b>fx.pos_y</b>: Calculated Y position for the effect", score: 990 },
                        { caption: "fx.x", value: "fx.x", meta: "fx (float)", docHTML: "<b>fx.x</b>: Alias of fx.pos_x", score: 980 },
                        { caption: "fx.y", value: "fx.y", meta: "fx (float)", docHTML: "<b>fx.y</b>: Alias of fx.pos_y", score: 980 },
                        { caption: "fx.org_x", value: "fx.org_x", meta: "fx (float)", docHTML: "<b>fx.org_x</b>: Origin anchor X coordinate", score: 980 },
                        { caption: "fx.org_y", value: "fx.org_y", meta: "fx (float)", docHTML: "<b>fx.org_y</b>: Origin anchor Y coordinate", score: 980 },
                        { caption: "fx.i", value: "fx.i", meta: "fx (int)", docHTML: "<b>fx.i</b>: Active iteration index in fx", score: 980 },
                        { caption: "fx.n", value: "fx.n", meta: "fx (int)", docHTML: "<b>fx.n</b>: Total iterations in fx", score: 980 },
                        { caption: "fx.start_time", value: "fx.start_time", meta: "fx (int)", docHTML: "<b>fx.start_time</b>: Start time of fx frame/unit", score: 980 },
                        { caption: "fx.end_time", value: "fx.end_time", meta: "fx (int)", docHTML: "<b>fx.end_time</b>: End time of fx frame/unit", score: 980 },
                        { caption: "fx.dur", value: "fx.dur", meta: "fx (int)", docHTML: "<b>fx.dur</b>: Duration of fx frame/unit", score: 980 },
                        { caption: "fx.align", value: "fx.align", meta: "fx (int)", docHTML: "<b>fx.align</b>: Active effect alignment (1..9)", score: 970 },

                        // --- 6. Neighbor Units (prev / next) & Relational Flags ---
                        { caption: "prev.text", value: "prev.text", meta: "prev (str)", docHTML: "<b>prev.text</b>: Text of the previous unit", score: 980 },
                        { caption: "prev.x", value: "prev.x", meta: "prev (float)", docHTML: "<b>prev.x</b>: X position of the previous unit", score: 980 },
                        { caption: "prev.y", value: "prev.y", meta: "prev (float)", docHTML: "<b>prev.y</b>: Y position of the previous unit", score: 980 },
                        { caption: "prev.start_time", value: "prev.start_time", meta: "prev (int)", docHTML: "<b>prev.start_time</b>: Start time of the previous unit (ms)", score: 980 },
                        { caption: "prev.end_time", value: "prev.end_time", meta: "prev (int)", docHTML: "<b>prev.end_time</b>: End time of the previous unit (ms)", score: 980 },
                        { caption: "prev.dur", value: "prev.dur", meta: "prev (int)", docHTML: "<b>prev.dur</b>: Duration of previous unit (ms)", score: 980 },
                        { caption: "next.text", value: "next.text", meta: "next (str)", docHTML: "<b>next.text</b>: Text of the next unit", score: 980 },
                        { caption: "next.x", value: "next.x", meta: "next (float)", docHTML: "<b>next.x</b>: X position of the next unit", score: 980 },
                        { caption: "next.y", value: "next.y", meta: "next (float)", docHTML: "<b>next.y</b>: Y position of the next unit", score: 980 },
                        { caption: "next.start_time", value: "next.start_time", meta: "next (int)", docHTML: "<b>next.start_time</b>: Start time of the next unit (ms)", score: 980 },
                        { caption: "next.end_time", value: "next.end_time", meta: "next (int)", docHTML: "<b>next.end_time</b>: End time of the next unit (ms)", score: 980 },
                        { caption: "next.dur", value: "next.dur", meta: "next (int)", docHTML: "<b>next.dur</b>: Duration of next unit (ms)", score: 980 },
                        { caption: "is_first", value: "is_first", meta: "bool", docHTML: "<b>is_first</b>: True if active unit is first in sequence", score: 970 },
                        { caption: "is_last", value: "is_last", meta: "bool", docHTML: "<b>is_last</b>: True if active unit is last in sequence", score: 970 },
                        { caption: "has_prev", value: "has_prev", meta: "bool", docHTML: "<b>has_prev</b>: True if preceding unit exists", score: 970 },
                        { caption: "has_next", value: "has_next", meta: "bool", docHTML: "<b>has_next</b>: True if succeeding unit exists", score: 970 },

                        // --- 7. Ink Metrics (True Glyph Contours) ---
                        { caption: "ink.width", value: "ink.width", meta: "ink (float)", docHTML: "<b>ink.width</b>: Visual contour ink bounding box width (px)", score: 980 },
                        { caption: "ink.height", value: "ink.height", meta: "ink (float)", docHTML: "<b>ink.height</b>: Visual contour ink bounding box height (px)", score: 980 },
                        { caption: "ink.center", value: "ink.center", meta: "ink (float)", docHTML: "<b>ink.center</b>: Visual contour center X coordinate", score: 980 },
                        { caption: "ink.middle", value: "ink.middle", meta: "ink (float)", docHTML: "<b>ink.middle</b>: Visual contour middle Y coordinate", score: 980 },
                        { caption: "ink.left", value: "ink.left", meta: "ink (float)", docHTML: "<b>ink.left</b>: Visual contour left edge", score: 970 },
                        { caption: "ink.right", value: "ink.right", meta: "ink (float)", docHTML: "<b>ink.right</b>: Visual contour right edge", score: 970 },
                        { caption: "ink.top", value: "ink.top", meta: "ink (float)", docHTML: "<b>ink.top</b>: Visual contour top edge", score: 970 },
                        { caption: "ink.bottom", value: "ink.bottom", meta: "ink (float)", docHTML: "<b>ink.bottom</b>: Visual contour bottom edge", score: 970 },
                        { caption: "ink.x", value: "ink.x", meta: "ink (float)", docHTML: "<b>ink.x</b>: Visual contour center X position", score: 970 },
                        { caption: "ink.y", value: "ink.y", meta: "ink (float)", docHTML: "<b>ink.y</b>: Visual contour middle Y position", score: 970 },

                        // --- 8. Output Variable ---
                        { caption: "result", value: "result", meta: "out", docHTML: "<b>result</b>: Return variable / final text string outputted to Result pin", score: 1000 },

                        // --- 9. Global Spatial & Context Variables ---
                        { caption: "start_time", value: "start_time", meta: "time (ms)", docHTML: "<b>start_time</b>: Active start time in ms", score: 960 },
                        { caption: "end_time", value: "end_time", meta: "time (ms)", docHTML: "<b>end_time</b>: Active end time in ms", score: 960 },
                        { caption: "line_start_time", value: "line_start_time", meta: "time (ms)", docHTML: "<b>line_start_time</b>: Line start time in ms", score: 960 },
                        { caption: "line_end_time", value: "line_end_time", meta: "time (ms)", docHTML: "<b>line_end_time</b>: Line end time in ms", score: 960 },
                        { caption: "syl_start_time", value: "syl_start_time", meta: "time (ms)", docHTML: "<b>syl_start_time</b>: Syllable start time in ms", score: 960 },
                        { caption: "syl_end_time", value: "syl_end_time", meta: "time (ms)", docHTML: "<b>syl_end_time</b>: Syllable end time in ms", score: 960 },
                        { caption: "st", value: "st", meta: "alias (ms)", docHTML: "<b>st</b>: Short alias of start_time", score: 950 },
                        { caption: "et", value: "et", meta: "alias (ms)", docHTML: "<b>et</b>: Short alias of end_time", score: 950 },
                        { caption: "dur", value: "dur", meta: "alias (ms)", docHTML: "<b>dur</b>: Duration in milliseconds", score: 950 },
                        { caption: "duration", value: "duration", meta: "alias (ms)", docHTML: "<b>duration</b>: Duration in milliseconds", score: 950 },
                        { caption: "i", value: "i", meta: "var (int)", docHTML: "<b>i</b>: Global index of current unit (1-based)", score: 950 },
                        { caption: "n", value: "n", meta: "var (int)", docHTML: "<b>n</b>: Total units in the line", score: 950 },
                        { caption: "rx", value: "rx", meta: "var (float)", docHTML: "<b>rx</b>: Accumulated horizontal offset", score: 950 },
                        { caption: "ry", value: "ry", meta: "var (float)", docHTML: "<b>ry</b>: Accumulated vertical offset", score: 950 },
                        { caption: "fd", value: "fd", meta: "var (float)", docHTML: "<b>fd</b>: Frame duration in milliseconds", score: 950 },
                        { caption: "frame_dur", value: "frame_dur", meta: "var (float)", docHTML: "<b>frame_dur</b>: Frame duration in milliseconds (e.g. 41.7ms)", score: 950 },
                        { caption: "fps", value: "fps", meta: "var (float)", docHTML: "<b>fps</b>: Video frames per second", score: 950 },
                        { caption: "ratio", value: "ratio", meta: "var (float)", docHTML: "<b>ratio</b>: Video aspect ratio or scaling factor", score: 950 },
                        { caption: "ini", value: "ini", meta: "var (float)", docHTML: "<b>ini</b>: Initial time reference offset", score: 950 },
                        { caption: "pos_x", value: "pos_x", meta: "var (float)", docHTML: "<b>pos_x</b>: Primary horizontal position", score: 950 },
                        { caption: "pos_y", value: "pos_y", meta: "var (float)", docHTML: "<b>pos_y</b>: Primary vertical position", score: 950 },
                        { caption: "center", value: "center", meta: "var (float)", docHTML: "<b>center</b>: Horizontal center coordinate", score: 950 },
                        { caption: "middle", value: "middle", meta: "var (float)", docHTML: "<b>middle</b>: Vertical middle coordinate", score: 950 },
                        { caption: "left", value: "left", meta: "var (float)", docHTML: "<b>left</b>: Left bounding coordinate", score: 950 },
                        { caption: "right", value: "right", meta: "var (float)", docHTML: "<b>right</b>: Right bounding coordinate", score: 950 },
                        { caption: "top", value: "top", meta: "var (float)", docHTML: "<b>top</b>: Top bounding coordinate", score: 950 },
                        { caption: "bottom", value: "bottom", meta: "var (float)", docHTML: "<b>bottom</b>: Bottom bounding coordinate", score: 950 },
                        { caption: "width", value: "width", meta: "var (float)", docHTML: "<b>width</b>: Active unit width", score: 950 },
                        { caption: "height", value: "height", meta: "var (float)", docHTML: "<b>height</b>: Active unit height", score: 950 },
                        { caption: "val_x", value: "val_x", meta: "var (float)", docHTML: "<b>val_x</b>: Context position X", score: 940 },
                        { caption: "val_y", value: "val_y", meta: "var (float)", docHTML: "<b>val_y</b>: Context position Y", score: 940 },
                        { caption: "val_start", value: "val_start", meta: "var (float)", docHTML: "<b>val_start</b>: Context start time", score: 940 },
                        { caption: "val_end", value: "val_end", meta: "var (float)", docHTML: "<b>val_end</b>: Context end time", score: 940 },
                        { caption: "val_dur", value: "val_dur", meta: "var (float)", docHTML: "<b>val_dur</b>: Context duration", score: 940 },

                        // --- 10. Iterators (Slicer, Loop, Array) ---
                        { caption: "s_i", value: "s_i", meta: "slicer (int)", docHTML: "<b>s_i</b>: Active Slicer piece index (1-based)", score: 1000 },
                        { caption: "s_n", value: "s_n", meta: "slicer (int)", docHTML: "<b>s_n</b>: Total Slicer piece count", score: 1000 },
                        { caption: "slice_i", value: "slice_i", meta: "slicer (int)", docHTML: "<b>slice_i</b>: Alias of s_i", score: 980 },
                        { caption: "slice_n", value: "slice_n", meta: "slicer (int)", docHTML: "<b>slice_n</b>: Alias of s_n", score: 980 },
                        { caption: "j", value: "j", meta: "loop (int)", docHTML: "<b>j</b>: Active MaxLoop iteration index (1-based)", score: 1000 },
                        { caption: "maxloop", value: "maxloop", meta: "loop (int)", docHTML: "<b>maxloop</b>: Total MaxLoop iterations", score: 1000 },
                        { caption: "col", value: "col", meta: "grid (int)", docHTML: "<b>col</b>: Spatial column index in slicer/mesh", score: 950 },
                        { caption: "row", value: "row", meta: "grid (int)", docHTML: "<b>row</b>: Spatial row index in slicer/mesh", score: 950 },
                        { caption: "a_i", value: "a_i", meta: "array (int)", docHTML: "<b>a_i</b>: Active Array/Particle element index", score: 950 },
                        { caption: "a_n", value: "a_n", meta: "array (int)", docHTML: "<b>a_n</b>: Total Array/Particle elements count", score: 950 },

                        // --- 11. Time Modifiers & Calculations ---
                        { caption: "time_lead_in", snippet: "time_lead_in(${1:40})", meta: "time (ms)", docHTML: "<b>time_lead_in(delay, base_ms)</b>: Prior lead-in time calculation per unit", score: 960 },
                        { caption: "time_lead_out", snippet: "time_lead_out(${1:40})", meta: "time (ms)", docHTML: "<b>time_lead_out(delay, base_ms)</b>: Subsequent lead-out time calculation per unit", score: 960 },
                        { caption: "time_middle_1", snippet: "time_middle_1(${1:40})", meta: "time (ms)", docHTML: "<b>time_middle_1(delay, base_ms)</b>: Sequential time from center outward", score: 960 },
                        { caption: "time_middle_2", snippet: "time_middle_2(${1:40})", meta: "time (ms)", docHTML: "<b>time_middle_2(delay, base_ms)</b>: Sequential time from edges inward", score: 960 },
                        { caption: "time_loop_1", snippet: "time_loop_1(${1:40})", meta: "time (ms)", docHTML: "<b>time_loop_1(delay, base_ms)</b>: Continuous entrance loop time", score: 960 },
                        { caption: "time_loop_2", snippet: "time_loop_2(${1:40})", meta: "time (ms)", docHTML: "<b>time_loop_2(delay, base_ms)</b>: Continuous exit loop time", score: 960 },
                        { caption: "li", snippet: "li(${1:40})", meta: "time (fn)", docHTML: "<b>li(delay, base)</b>: Compact time_lead_in helper", score: 950 },
                        { caption: "lo", snippet: "lo(${1:40})", meta: "time (fn)", docHTML: "<b>lo(delay, base)</b>: Compact time_lead_out helper", score: 950 },
                        { caption: "m1", snippet: "m1(${1:30})", meta: "time (fn)", docHTML: "<b>m1(delay, base)</b>: Compact time_middle_1 helper", score: 950 },
                        { caption: "m2", snippet: "m2(${1:30})", meta: "time (fn)", docHTML: "<b>m2(delay, base)</b>: Compact time_middle_2 helper", score: 950 },
                        { caption: "l1", snippet: "l1(${1:30})", meta: "time (fn)", docHTML: "<b>l1(delay, base)</b>: Compact time_loop_1 helper", score: 950 },
                        { caption: "l2", snippet: "l2(${1:30})", meta: "time (fn)", docHTML: "<b>l2(delay, base)</b>: Compact time_loop_2 helper", score: 950 },
                        { caption: "time_to_frame", snippet: "time_to_frame(${1:ms}, ${2:23.976})", meta: "time (fn)", docHTML: "<b>time_to_frame(ms, fps)</b>: Converts milliseconds to frame number", score: 930 },
                        { caption: "duration", snippet: "duration(${1:syl})", meta: "time (fn)", docHTML: "<b>duration(obj)</b>: Retrieves duration in ms from object or context", score: 930 },
                        { caption: "parse_ass_time", snippet: "parse_ass_time('${1:0:00:00.00}')", meta: "time (fn)", docHTML: "<b>parse_ass_time(str)</b>: Converts ASS timestamp string to ms", score: 920 },
                        { caption: "format_ass_time", snippet: "format_ass_time(${1:ms})", meta: "time (fn)", docHTML: "<b>format_ass_time(ms)</b>: Converts ms to ASS timestamp (H:MM:SS.cs)", score: 920 },
                        { caption: "format", snippet: "format(\"${1:%s}\", ${2:val})", meta: "str (fn)", docHTML: "<b>format(fmt, ...)</b>: String formatting function (alias of string.format in Lua)", score: 930 },
                        { caption: "calculate_sync_gap", snippet: "calculate_sync_gap('${1:next}', '${2:order}', ${3:2000})", meta: "time (fn)", docHTML: "<b>calculate_sync_gap(dir, mode, max_gap)</b>: Gap to adjacent dialogue line", score: 920 },
                        { caption: "strip_tags", snippet: "strip_tags(${1:line.raw_text})", meta: "text (fn)", docHTML: "<b>strip_tags(text)</b>: Removes all ASS override tags from string", score: 920 },
                        { caption: "kana", snippet: "kana(${1:syl.text})", meta: "text (fn)", docHTML: "<b>kana(text)</b>: Strips and sanitizes karaoke text", score: 920 },

                        // --- 12. Sync Helper & Adjacent Line Gaps ---
                        { caption: "sync", snippet: "sync(${1:next}, ${2:order}, ${3:2000})", meta: "time (func)", docHTML: "<b>sync(direction, mode, max_gap)</b>: Calculates the gap (in ms) to the adjacent line.<br>• <b>direction</b>: <code>next</code> or <code>prev</code><br>• <b>mode</b>: <code>order</code> (1), <code>style</code> (2), <code>actor</code> (3), <code>effect</code> (4), <code>layer</code> (5)<br>• <b>max_gap</b>: upper limit in ms (default 2000 or custom <code>maxgap</code>).<br><i>Returns negative value for overlapping lines.</i>", score: 1050 },
                        { caption: "sync.next", value: "sync.next", meta: "time (float)", docHTML: "<b>sync.next</b>: Gap in ms to next dialogue line in order (capped at maxgap/2000ms)", score: 1040 },
                        { caption: "sync.prev", value: "sync.prev", meta: "time (float)", docHTML: "<b>sync.prev</b>: Gap in ms to previous dialogue line in order (capped at maxgap/2000ms)", score: 1040 },
                        { caption: "sync.order_next", value: "sync.order_next", meta: "time (float)", docHTML: "<b>sync.order_next</b>: Gap in ms to next line in subtitle order", score: 1030 },
                        { caption: "sync.order_prev", value: "sync.order_prev", meta: "time (float)", docHTML: "<b>sync.order_prev</b>: Gap in ms to previous line in subtitle order", score: 1030 },
                        { caption: "sync.style_next", value: "sync.style_next", meta: "time (float)", docHTML: "<b>sync.style_next</b>: Gap in ms to next line with matching style", score: 1030 },
                        { caption: "sync.style_prev", value: "sync.style_prev", meta: "time (float)", docHTML: "<b>sync.style_prev</b>: Gap in ms to previous line with matching style", score: 1030 },
                        { caption: "sync.actor_next", value: "sync.actor_next", meta: "time (float)", docHTML: "<b>sync.actor_next</b>: Gap in ms to next line with matching actor", score: 1020 },
                        { caption: "sync.actor_prev", value: "sync.actor_prev", meta: "time (float)", docHTML: "<b>sync.actor_prev</b>: Gap in ms to previous line with matching actor", score: 1020 },
                        { caption: "sync.effect_next", value: "sync.effect_next", meta: "time (float)", docHTML: "<b>sync.effect_next</b>: Gap in ms to next line with matching effect", score: 1020 },
                        { caption: "sync.effect_prev", value: "sync.effect_prev", meta: "time (float)", docHTML: "<b>sync.effect_prev</b>: Gap in ms to previous line with matching effect", score: 1020 },
                        { caption: "sync.layer_next", value: "sync.layer_next", meta: "time (float)", docHTML: "<b>sync.layer_next</b>: Gap in ms to next line with matching layer", score: 1020 },
                        { caption: "sync.layer_prev", value: "sync.layer_prev", meta: "time (float)", docHTML: "<b>sync.layer_prev</b>: Gap in ms to previous line with matching layer", score: 1020 },

                        // --- 13. Shared Memory & Conditioning ---
                        { caption: "remember", snippet: "remember('${1:clave}', ${2:valor})", meta: "func", docHTML: "<b>remember(key, value)</b>: Stores in shared memory across syllables and lines", score: 940 },
                        { caption: "recall", snippet: isPython ? "recall('${1:clave}', ${2:None})" : "recall('${1:clave}', ${2:nil})", meta: "func", docHTML: "<b>recall(key, default)</b>: Retrieves from shared memory", score: 940 },
                        { caption: "tag_only", snippet: "tag_only(${1:condicion}, '${2:\\\\pos(0,0)}')", meta: "func", docHTML: "<b>tag_only(cond, tag)</b>: Returns tag only if condition is true", score: 930 },

                        // --- 14. Easing & Interpolation ---
                        { caption: "clamp", snippet: "clamp(${1:valor}, ${2:min}, ${3:max})", meta: "math", docHTML: "<b>clamp(val, min, max)</b>: Clamps number between min and max", score: 910 },
                        { caption: "lerp", snippet: "lerp(${1:a}, ${2:b}, ${3:t})", meta: "math", docHTML: "<b>lerp(a, b, t)</b>: Linear interpolation between a and b", score: 910 },
                        { caption: "map_range", snippet: "map_range(${1:val}, ${2:0}, ${3:1}, ${4:0}, ${5:100})", meta: "math", docHTML: "<b>map_range(val, in_min, in_max, out_min, out_max)</b>: Remaps range linearly", score: 910 },
                        { caption: "ease_in", snippet: "ease_in(${1:t})", meta: "easing", docHTML: "<b>ease_in(t)</b>: Quadratic ease-in curve (t in [0..1])", score: 900 },
                        { caption: "ease_out", snippet: "ease_out(${1:t})", meta: "easing", docHTML: "<b>ease_out(t)</b>: Quadratic ease-out curve (t in [0..1])", score: 900 },
                        { caption: "ease_in_out", snippet: "ease_in_out(${1:t})", meta: "easing", docHTML: "<b>ease_in_out(t)</b>: Smooth quadratic ease-in-out curve (t in [0..1])", score: 900 },
                        { caption: "cubic_in", snippet: "cubic_in(${1:t})", meta: "easing", docHTML: "<b>cubic_in(t)</b>: Cubic ease-in curve (t in [0..1])", score: 900 },
                        { caption: "cubic_out", snippet: "cubic_out(${1:t})", meta: "easing", docHTML: "<b>cubic_out(t)</b>: Cubic ease-out curve (t in [0..1])", score: 900 },
                        { caption: "elastic", snippet: "elastic(${1:t})", meta: "easing", docHTML: "<b>elastic(t)</b>: Elastic spring oscillating curve (t in [0..1])", score: 900 },
                        { caption: "bounce", snippet: "bounce(${1:t})", meta: "easing", docHTML: "<b>bounce(t)</b>: Bouncing decay curve (t in [0..1])", score: 900 },
                        { caption: "back", snippet: "back(${1:t})", meta: "easing", docHTML: "<b>back(t)</b>: Anticipation and overshoot curve (t in [0..1])", score: 900 },
                        { caption: "ipol", snippet: "ipol(${1:t}, ${2:a}, ${3:b}, '${4:linear}')", meta: "easing", docHTML: "<b>ipol(t, a, b, curve)</b>: Interpolates using curve ('ease_in', 'ease_out', 'cubic_in', etc.)", score: 900 },
                        { caption: "bezier", snippet: "bezier(${1:t}, ${2:p0}, ${3:p1}, ${4:p2}, ${5:p3})", meta: "math", docHTML: "<b>bezier(t, p0, p1, p2, p3)</b>: Cubic Bezier parametric curve", score: 900 },

                        // --- 15. Wave Oscillators & Vectors ---
                        { caption: "sine_wave", snippet: "sine_wave(${1:t}, ${2:1.0}, ${3:1.0}, ${4:0.0})", meta: "wave", docHTML: "<b>sine_wave(t, freq, amp, offset)</b>: Sine wave harmonic oscillator", score: 900 },
                        { caption: "square_wave", snippet: "square_wave(${1:t}, ${2:1.0}, ${3:1.0}, ${4:0.0})", meta: "wave", docHTML: "<b>square_wave(t, freq, amp, offset)</b>: Square wave discrete oscillator", score: 900 },
                        { caption: "triangle_wave", snippet: "triangle_wave(${1:t}, ${2:1.0}, ${3:1.0}, ${4:0.0})", meta: "wave", docHTML: "<b>triangle_wave(t, freq, amp, offset)</b>: Triangle wave linear oscillator", score: 900 },
                        { caption: "sawtooth_wave", snippet: "sawtooth_wave(${1:t}, ${2:1.0}, ${3:1.0}, ${4:0.0})", meta: "wave", docHTML: "<b>sawtooth_wave(t, freq, amp, offset)</b>: Sawtooth wave ramp oscillator", score: 900 },
                        { caption: "polar", snippet: "polar(${1:angle}, ${2:dist})", meta: "math", docHTML: "<b>polar(angle, dist)</b>: Converts polar coordinates (deg, dist) to (x, y)", score: 900 },

                        // --- 16. Audio Metric Analyzers ---
                        { caption: "audio_rms", snippet: "audio_rms(${1:start_time}, ${2:end_time})", meta: "audio", docHTML: "<b>audio_rms(start, end, path)</b>: Root Mean Square audio amplitude (0..1)", score: 920 },
                        { caption: "audio_peak", snippet: "audio_peak(${1:start_time}, ${2:end_time})", meta: "audio", docHTML: "<b>audio_peak(start, end, path)</b>: Peak audio amplitude (0..1)", score: 920 },
                        { caption: "audio_band", snippet: "audio_band(${1:start_time}, ${2:end_time}, ${3:20}, ${4:250})", meta: "audio", docHTML: "<b>audio_band(start, end, min_hz, max_hz, path)</b>: Filtered audio band energy", score: 920 },
                        { caption: "audio_fft", snippet: "audio_fft(${1:start_time}, ${2:end_time}, ${3:16})", meta: "audio", docHTML: "<b>audio_fft(start, end, num_bands, min_hz, max_hz, path)</b>: FFT spectrum frequency array", score: 920 },

                        // --- 17. Functional ASS Tag Generators (Python & Lua) ---
                        { caption: "pos", snippet: "pos(${1:syl.x}, ${2:syl.y})", meta: "tag (fn)", docHTML: "<b>pos(x, y)</b>: Generates \\pos(x, y) string", score: 930 },
                        { caption: "move", snippet: "move(${1:x1}, ${2:y1}, ${3:x2}, ${4:y2}, ${5:0}, ${6:syl.duration})", meta: "tag (fn)", docHTML: "<b>move(x1, y1, x2, y2, t1, t2)</b>: Generates \\move(...) string", score: 930 },
                        { caption: "org", snippet: "org(${1:syl.x}, ${2:syl.y})", meta: "tag (fn)", docHTML: "<b>org(x, y)</b>: Generates \\org(x, y) origin string", score: 930 },
                        { caption: "fad", snippet: "fad(${1:150}, ${2:150})", meta: "tag (fn)", docHTML: "<b>fad(tin, tout)</b>: Generates \\fad(tin, tout) string", score: 930 },
                        { caption: "fade", snippet: "fade(${1:a1}, ${2:a2}, ${3:a3}, ${4:t1}, ${5:t2}, ${6:t3}, ${7:t4})", meta: "tag (fn)", docHTML: "<b>fade(a1, a2, a3, t1, t2, t3, t4)</b>: Generates \\fade(...) string", score: 920 },
                        { caption: "clip", snippet: "clip(${1:x1}, ${2:y1}, ${3:x2}, ${4:y2})", meta: "tag (fn)", docHTML: "<b>clip(x1, y1, x2, y2)</b>: Generates \\clip(...) rectangular mask", score: 920 },
                        { caption: "iclip", snippet: "iclip(${1:x1}, ${2:y1}, ${3:x2}, ${4:y2})", meta: "tag (fn)", docHTML: "<b>iclip(x1, y1, x2, y2)</b>: Generates \\iclip(...) inverse mask", score: 920 },
                        { caption: "c1", snippet: "c1('${1:&HFFFFFF&}')", meta: "tag (fn)", docHTML: "<b>c1(color)</b>: Primary fill color \\1c tag", score: 930 },
                        { caption: "c2", snippet: "c2('${1:&H0000FF&}')", meta: "tag (fn)", docHTML: "<b>c2(color)</b>: Secondary karaoke color \\2c tag", score: 930 },
                        { caption: "c3", snippet: "c3('${1:&H000000&}')", meta: "tag (fn)", docHTML: "<b>c3(color)</b>: Border color \\3c tag", score: 930 },
                        { caption: "c4", snippet: "c4('${1:&H000000&}')", meta: "tag (fn)", docHTML: "<b>c4(color)</b>: Shadow color \\4c tag", score: 930 },
                        { caption: "a1", snippet: "a1('${1:&H00&}')", meta: "tag (fn)", docHTML: "<b>a1(alpha)</b>: Primary transparency \\1a tag", score: 920 },
                        { caption: "a2", snippet: "a2('${1:&H00&}')", meta: "tag (fn)", docHTML: "<b>a2(alpha)</b>: Secondary transparency \\2a tag", score: 920 },
                        { caption: "a3", snippet: "a3('${1:&H00&}')", meta: "tag (fn)", docHTML: "<b>a3(alpha)</b>: Border transparency \\3a tag", score: 920 },
                        { caption: "a4", snippet: "a4('${1:&H00&}')", meta: "tag (fn)", docHTML: "<b>a4(alpha)</b>: Shadow transparency \\4a tag", score: 920 },
                        { caption: "alpha", snippet: "alpha('${1:&H00&}')", meta: "tag (fn)", docHTML: "<b>alpha(val)</b>: Global transparency \\alpha tag", score: 920 },
                        { caption: "fscx", snippet: "fscx(${1:100})", meta: "tag (fn)", docHTML: "<b>fscx(v)</b>: Horizontal scale \\fscx tag", score: 930 },
                        { caption: "fscy", snippet: "fscy(${1:100})", meta: "tag (fn)", docHTML: "<b>fscy(v)</b>: Vertical scale \\fscy tag", score: 930 },
                        { caption: "fscxy", snippet: "fscxy(${1:100}, ${2:100})", meta: "tag (fn)", docHTML: "<b>fscxy(x, y)</b>: Paired scale \\fscx and \\fscy tags", score: 930 },
                        { caption: "frz", snippet: "frz(${1:0})", meta: "tag (fn)", docHTML: "<b>frz(v)</b>: Z-axis rotation \\frz tag", score: 930 },
                        { caption: "frx", snippet: "frx(${1:0})", meta: "tag (fn)", docHTML: "<b>frx(v)</b>: X-axis rotation \\frx tag", score: 920 },
                        { caption: "fry", snippet: "fry(${1:0})", meta: "tag (fn)", docHTML: "<b>fry(v)</b>: Y-axis rotation \\fry tag", score: 920 },
                        { caption: "fax", snippet: "fax(${1:0})", meta: "tag (fn)", docHTML: "<b>fax(v)</b>: X-axis shear \\fax tag", score: 920 },
                        { caption: "fay", snippet: "fay(${1:0})", meta: "tag (fn)", docHTML: "<b>fay(v)</b>: Y-axis shear \\fay tag", score: 920 },
                        { caption: "bord", snippet: "bord(${1:2})", meta: "tag (fn)", docHTML: "<b>bord(v)</b>: Border thickness \\bord tag", score: 930 },
                        { caption: "shad", snippet: "shad(${1:0})", meta: "tag (fn)", docHTML: "<b>shad(v)</b>: Shadow depth \\shad tag", score: 930 },
                        { caption: "blur", snippet: "blur(${1:2})", meta: "tag (fn)", docHTML: "<b>blur(v)</b>: Gaussian blur \\blur tag", score: 930 },
                        { caption: "an", snippet: "an(${1:5})", meta: "tag (fn)", docHTML: "<b>an(v)</b>: Alignment \\an tag (1..9)", score: 930 },
                        { caption: "trans", snippet: "trans(${1:0}, ${2:syl.duration}, '${3:\\\\fscx120\\\\fscy120}')", meta: "tag (fn)", docHTML: "<b>trans(t1, t2, tags)</b>: Tag transition \\t(t1, t2, tags)", score: 930 },
                        { caption: "ass_color", snippet: "ass_color(${1:255}, ${2:255}, ${3:255})", meta: "tag (fn)", docHTML: "<b>ass_color(r, g, b)</b>: Converts RGB to ASS hex format (&HBBGGRR&)", score: 920 },
                        { caption: "ass_alpha", snippet: "ass_alpha(${1:0})", meta: "tag (fn)", docHTML: "<b>ass_alpha(a)</b>: Converts opacity/alpha to ASS hex (&HAA&)", score: 920 },
                        { caption: "random_color", snippet: "random_color()", meta: "tag (fn)", docHTML: "<b>random_color()</b>: Generates random ASS color hex (&HBBGGRR&)", score: 920 },
                        { caption: "random_alpha", snippet: "random_alpha()", meta: "tag (fn)", docHTML: "<b>random_alpha()</b>: Generates random ASS alpha hex (&HAA&)", score: 920 },

                        // --- 18. Shape Generators & Shape Presets ---
                        { caption: "shape_star", snippet: "shape_star()", meta: "shape (fn)", docHTML: "<b>shape_star()</b>: Five-pointed star ASS vector path", score: 920 },
                        { caption: "shape_heart", snippet: "shape_heart()", meta: "shape (fn)", docHTML: "<b>shape_heart()</b>: Heart ASS vector path", score: 920 },
                        { caption: "shape_circle", snippet: "shape_circle()", meta: "shape (fn)", docHTML: "<b>shape_circle()</b>: Perfect circle ASS vector path", score: 920 },
                        { caption: "shape_square", snippet: "shape_square()", meta: "shape (fn)", docHTML: "<b>shape_square()</b>: Square ASS vector path", score: 920 },
                        { caption: "shape_triangle", snippet: "shape_triangle()", meta: "shape (fn)", docHTML: "<b>shape_triangle()</b>: Triangle ASS vector path", score: 920 },
                        { caption: "shape_rhombus", snippet: "shape_rhombus()", meta: "shape (fn)", docHTML: "<b>shape_rhombus()</b>: Diamond / rhombus ASS vector path", score: 910 },
                        { caption: "shape_rounded_corners", snippet: "shape_rounded_corners()", meta: "shape (fn)", docHTML: "<b>shape_rounded_corners()</b>: Rounded rectangle ASS vector path", score: 910 },
                        { caption: "shape_pentagon", snippet: "shape_pentagon()", meta: "shape (fn)", docHTML: "<b>shape_pentagon()</b>: Regular pentagon ASS vector path", score: 910 },
                        { caption: "shape_hexagon", snippet: "shape_hexagon()", meta: "shape (fn)", docHTML: "<b>shape_hexagon()</b>: Regular hexagon ASS vector path", score: 910 },
                        { caption: "shape_octagon", snippet: "shape_octagon()", meta: "shape (fn)", docHTML: "<b>shape_octagon()</b>: Regular octagon ASS vector path", score: 910 },
                        { caption: "resolve_shape", snippet: "resolve_shape('${1:star}')", meta: "shape (fn)", docHTML: "<b>resolve_shape(name)</b>: Resolves named vector preset into ASS drawing", score: 920 },

                        // --- 19. Stochastic Functions & Scoped Random ---
                        { caption: "R", snippet: "R(${1:min}, ${2:max})", meta: "math", docHTML: "<b>R(min, max)</b>: Deterministic random integer per unit", score: 910 },
                        { caption: "Rs", snippet: "Rs(${1:min}, ${2:max})", meta: "math", docHTML: "<b>Rs(min, max)</b>: Deterministic random float per unit", score: 910 },
                        { caption: "Rc", snippet: "Rc(${1:min}, ${2:max})", meta: "math", docHTML: "<b>Rc(min, max)</b>: Centesimal random float (2 decimals)", score: 910 },
                        { caption: "Rcs", snippet: "Rcs(${1:min}, ${2:max})", meta: "math", docHTML: "<b>Rcs(min, max)</b>: Centesimal bipolar float (+/-)", score: 910 },
                        { caption: "Rd", snippet: "Rd(${1:min}, ${2:max})", meta: "math", docHTML: "<b>Rd(min, max)</b>: Decimal float (1 decimal)", score: 910 },
                        { caption: "Rds", snippet: "Rds(${1:min}, ${2:max})", meta: "math", docHTML: "<b>Rds(min, max)</b>: Decimal bipolar float (+/-)", score: 910 },
                        { caption: "Rm", snippet: "Rm(${1:min}, ${2:max})", meta: "math", docHTML: "<b>Rm(min, max)</b>: Millesimal float (3 decimals)", score: 910 },
                        { caption: "Rms", snippet: "Rms(${1:min}, ${2:max})", meta: "math", docHTML: "<b>Rms(min, max)</b>: Millesimal bipolar float (+/-)", score: 910 },
                        { caption: "Rr", snippet: "Rr(${1:min}, ${2:max})", meta: "math", docHTML: "<b>Rr(min, max)</b>: Resolution-scaled random", score: 910 },
                        { caption: "Rstep", snippet: "Rstep(${1:min}, ${2:max}, ${3:step})", meta: "math", docHTML: "<b>Rstep(min, max, step)</b>: Quantised step random", score: 910 },
                        { caption: "R2d", snippet: "R2d(${1:min}, ${2:max})", meta: "math", docHTML: "<b>R2d(min, max)</b>: 2D coordinate pair string", score: 910 },
                        { caption: "Rbool", snippet: "Rbool(${1:50})", meta: "math", docHTML: "<b>Rbool(prob)</b>: Probabilistic boolean True/False", score: 910 },
                        { caption: "Re", snippet: "Re('${1:opc1, opc2, opc3}')", meta: "math", docHTML: "<b>Re(options)</b>: Selects random element from comma-separated list", score: 910 },
                        { caption: "Rfake", snippet: "Rfake()", meta: "math", docHTML: "<b>Rfake()</b>: Generates deterministic pseudo-random float", score: 900 },
                        { caption: "Rcolor", snippet: "Rcolor('${1:#FFFFFF}', '${2:#000000}')", meta: "math", docHTML: "<b>Rcolor(c1, c2)</b>: Random ASS color interpolated between two colors", score: 900 },
                        { caption: "rand", snippet: "rand(${1:min}, ${2:max})", meta: "math", docHTML: "<b>rand(min, max)</b>: Alias of R(min, max)", score: 900 },
                        { caption: "by", value: "by", meta: "dispatcher", docHTML: "<b>by.&lt;iterator&gt;.&lt;R_mode&gt;</b>: Scoped stochastic random generator tied to an iterator (e.g. by.s_i.Rms, by.j.Rs, by.syl.R)", score: 1100 },

                        // --- 20. Language Built-ins & Conversion Helpers ---
                        { caption: "char", snippet: isPython ? "chr(${1:65})" : "string.char(${1:65})", meta: "func", docHTML: "<b>char / chr</b>: Converts ASCII/Unicode code to character", score: 920 },
                        { caption: "chr", snippet: "chr(${1:65})", meta: "func", docHTML: "<b>chr(code)</b>: Returns character corresponding to ASCII code", score: 920 },
                        { caption: "ord", snippet: isPython ? "ord('${1:A}')" : "string.byte('${1:A}')", meta: "func", docHTML: "<b>ord / string.byte</b>: ASCII/Unicode code of character", score: 910 },
                        { caption: "len", snippet: isPython ? "len(${1:syl.text})" : "string.len(${1:syl.text})", meta: "func", docHTML: "<b>len</b>: Length of string or array", score: 910 },
                        { caption: "str", snippet: "str(${1:valor})", meta: "func", docHTML: "<b>str(val)</b>: Converts to string", score: 910 },
                        { caption: "int", snippet: "int(${1:valor})", meta: "func", docHTML: "<b>int(val)</b>: Converts to integer", score: 910 },
                        { caption: "float", snippet: "float(${1:valor})", meta: "func", docHTML: "<b>float(val)</b>: Converts to float", score: 910 },

                        // --- 21. Raw ASS Tags ---
                        { caption: "\\pos", snippet: "\\\\pos(${1:syl.x},${2:syl.y})", meta: "ass", docHTML: "<b>\\pos(x, y)</b>: Absolute positioning", score: 890 },
                        { caption: "\\move", snippet: "\\\\move(${1:x1},${2:y1},${3:x2},${4:y2},${5:0},${6:syl.duration})", meta: "ass", docHTML: "<b>\\move(x1, y1, x2, y2, t1, t2)</b>: Timed movement", score: 890 },
                        { caption: "\\an", snippet: "\\\\an${1:5}", meta: "ass", docHTML: "<b>\\an5</b>: Alignment (1..9)", score: 890 },
                        { caption: "\\c", snippet: "\\\\c${1:&HFFFFFF&}", meta: "ass", docHTML: "<b>\\c&HBBGGRR&</b>: Primary color", score: 890 },
                        { caption: "\\1c", snippet: "\\\\1c${1:&HFFFFFF&}", meta: "ass", docHTML: "<b>\\1c&HBBGGRR&</b>: Primary fill color", score: 890 },
                        { caption: "\\2c", snippet: "\\\\2c${1:&H0000FF&}", meta: "ass", docHTML: "<b>\\2c&HBBGGRR&</b>: Secondary color (karaoke fill)", score: 890 },
                        { caption: "\\3c", snippet: "\\\\3c${1:&H000000&}", meta: "ass", docHTML: "<b>\\3c&HBBGGRR&</b>: Border color", score: 890 },
                        { caption: "\\4c", snippet: "\\\\4c${1:&H000000&}", meta: "ass", docHTML: "<b>\\4c&HBBGGRR&</b>: Shadow color", score: 890 },
                        { caption: "\\alpha", snippet: "\\\\alpha${1:&H00&}", meta: "ass", docHTML: "<b>\\alpha&HAA&</b>: Global transparency (00..FF)", score: 890 },
                        { caption: "\\1a", snippet: "\\\\1a${1:&H00&}", meta: "ass", docHTML: "<b>\\1a&HAA&</b>: Fill transparency", score: 890 },
                        { caption: "\\3a", snippet: "\\\\3a${1:&H00&}", meta: "ass", docHTML: "<b>\\3a&HAA&</b>: Border transparency", score: 890 },
                        { caption: "\\fscx", snippet: "\\\\fscx${1:100}", meta: "ass", docHTML: "<b>\\fscx100</b>: Horizontal scale (%)", score: 890 },
                        { caption: "\\fscy", snippet: "\\\\fscy${1:100}", meta: "ass", docHTML: "<b>\\fscy100</b>: Vertical scale (%)", score: 890 },
                        { caption: "\\frz", snippet: "\\\\frz${1:0}", meta: "ass", docHTML: "<b>\\frz0</b>: Z-axis rotation (degrees)", score: 890 },
                        { caption: "\\blur", snippet: "\\\\blur${1:2}", meta: "ass", docHTML: "<b>\\blur2</b>: Gaussian blur", score: 890 },
                        { caption: "\\bord", snippet: "\\\\bord${1:2}", meta: "ass", docHTML: "<b>\\bord2</b>: Border thickness", score: 890 },
                        { caption: "\\shad", snippet: "\\\\shad${1:0}", meta: "ass", docHTML: "<b>\\shad0</b>: Shadow depth", score: 890 },
                        { caption: "\\fad", snippet: "\\\\fad(${1:150},${2:150})", meta: "ass", docHTML: "<b>\\fad(tin, tout)</b>: Fade in and out", score: 890 },
                        { caption: "\\t", snippet: "\\\\t(${1:0},${2:syl.duration},${3:\\\\fscx120\\\\fscy120})", meta: "ass", docHTML: "<b>\\t(t1, t2, tags)</b>: Tag animation and interpolation", score: 890 },
                        { caption: "\\clip", snippet: "\\\\clip(${1:x1},${2:y1},${3:x2},${4:y2})", meta: "ass", docHTML: "<b>\\clip(x1,y1,x2,y2)</b>: Rectangular clip mask", score: 890 },

                        // --- 22. Standard Math Functions ---
                        { caption: "math.sin", snippet: "math.sin(${1:x})", meta: "math", docHTML: "<b>math.sin(x)</b>: Sine of angle in radians", score: 880 },
                        { caption: "math.cos", snippet: "math.cos(${1:x})", meta: "math", docHTML: "<b>math.cos(x)</b>: Cosine of angle in radians", score: 880 },
                        { caption: "math.tan", snippet: "math.tan(${1:x})", meta: "math", docHTML: "<b>math.tan(x)</b>: Tangent of angle", score: 880 },
                        { caption: "math.sqrt", snippet: "math.sqrt(${1:x})", meta: "math", docHTML: "<b>math.sqrt(x)</b>: Square root", score: 880 },
                        { caption: "math.floor", snippet: "math.floor(${1:x})", meta: "math", docHTML: "<b>math.floor(x)</b>: Round down", score: 880 },
                        { caption: "math.ceil", snippet: "math.ceil(${1:x})", meta: "math", docHTML: "<b>math.ceil(x)</b>: Round up", score: 880 },
                        { caption: "math.abs", snippet: "math.abs(${1:x})", meta: "math", docHTML: "<b>math.abs(x)</b>: Absolute value", score: 880 },
                        { caption: "math.pi", value: "math.pi", meta: "math", docHTML: "<b>math.pi</b>: Pi constant (3.14159...)", score: 880 },
                        { caption: "math.radians", snippet: isPython ? "math.radians(${1:deg})" : "math.rad(${1:deg})", meta: "math", docHTML: "<b>math.radians / math.rad</b>: Converts degrees to radians", score: 880 },
                        { caption: "math.degrees", snippet: isPython ? "math.degrees(${1:rad})" : "math.deg(${1:rad})", meta: "math", docHTML: "<b>math.degrees / math.deg</b>: Converts radians to degrees", score: 880 }
                    ];

                    if (isPython) {
                        completions.push(
                            { caption: "range", snippet: "range(${1:stop})", meta: "python", docHTML: "<b>range(stop)</b>: Python range sequence generator", score: 890 },
                            { caption: "enumerate", snippet: "enumerate(${1:iterable})", meta: "python", docHTML: "<b>enumerate(iterable)</b>: Indexed iteration tuple", score: 890 },
                            { caption: "zip", snippet: "zip(${1:iter1}, ${2:iter2})", meta: "python", docHTML: "<b>zip(a, b)</b>: Parallel element pairs iterator", score: 890 },
                            { caption: "isinstance", snippet: "isinstance(${1:obj}, ${2:type})", meta: "python", docHTML: "<b>isinstance(obj, type)</b>: Type checking boolean", score: 880 },
                            { caption: "round", snippet: "round(${1:val}, ${2:2})", meta: "python", docHTML: "<b>round(val, n)</b>: Rounds float to n decimals", score: 890 }
                        );
                    } else {
                        completions.push(
                            { caption: "ipairs", snippet: "ipairs(${1:tbl})", meta: "lua", docHTML: "<b>ipairs(tbl)</b>: Numerical array iterator", score: 890 },
                            { caption: "pairs", snippet: "pairs(${1:tbl})", meta: "lua", docHTML: "<b>pairs(tbl)</b>: Key-value table iterator", score: 890 },
                            { caption: "tostring", snippet: "tostring(${1:val})", meta: "lua", docHTML: "<b>tostring(val)</b>: Converts value to string", score: 890 },
                            { caption: "tonumber", snippet: "tonumber(${1:val})", meta: "lua", docHTML: "<b>tonumber(val)</b>: Converts value to number", score: 890 },
                            { caption: "table.insert", snippet: "table.insert(${1:tbl}, ${2:val})", meta: "lua", docHTML: "<b>table.insert(tbl, val)</b>: Appends element to Lua table", score: 890 },
                            { caption: "table.concat", snippet: "table.concat(${1:tbl}, '${2:,}')", meta: "lua", docHTML: "<b>table.concat(tbl, sep)</b>: Joins Lua table array elements", score: 890 }
                        );
                    }

                    for (let i = 1; i <= Math.max(inputCount, 1); i++) {
                        completions.push({
                            caption: "in" + i,
                            value: "in" + i,
                            meta: "input",
                            docHTML: "<b>in" + i + "</b>: Insumo conectado al puerto In" + i + " o su valor de texto",
                            score: 990
                        });
                    }

                    if (checkPrefix && checkPrefix.includes(".")) {
                        const parts = checkPrefix.split(".");
                        const obj = parts[0];
                        if (obj === "by") {
                            const iterators = ["s_i", "j", "syl", "char", "word", "line", "a_i", "p_i", "col", "row"];
                            if (parts.length === 2) {
                                iterators.forEach(it => {
                                    completions.push({
                                        caption: "by." + it,
                                        value: "by." + it,
                                        meta: "iterator",
                                        docHTML: "<b>by." + it + "</b>: Scoped stochastic random generator tied to " + it,
                                        score: 3000
                                    });
                                });
                            } else if (parts.length >= 3) {
                                const itName = parts[1];
                                const randomModes = [
                                    { name: "R", args: "min, max", doc: "Uniform random integer/float" },
                                    { name: "Rs", args: "min, max", doc: "Symmetric bipolar random (+/-)" },
                                    { name: "Rc", args: "min, max", doc: "Centesimal float (2 decimal places)" },
                                    { name: "Rcs", args: "min, max", doc: "Centesimal bipolar float (+/-)" },
                                    { name: "Rd", args: "min, max", doc: "Decimal float (1 decimal place)" },
                                    { name: "Rds", args: "min, max", doc: "Decimal bipolar float (+/-)" },
                                    { name: "Rm", args: "min, max", doc: "Millesimal float (3 decimal places)" },
                                    { name: "Rms", args: "min, max", doc: "Millesimal bipolar float (+/-)" },
                                    { name: "Rr", args: "min, max", doc: "Resolution-scaled random" },
                                    { name: "Rstep", args: "min, max, step", doc: "Quantised step random" },
                                    { name: "R2d", args: "min, max", doc: "2D Cartesian coordinate pair" },
                                    { name: "Rbool", args: "prob=50", doc: "Probabilistic boolean" },
                                    { name: "Rcolor", args: "c1, c2", doc: "Random color interpolation" },
                                    { name: "Re", args: "options", doc: "Discrete option list selector" },
                                    { name: "Rfake", args: "", doc: "Deterministic pseudo-random" },
                                    { name: "rand", args: "min, max", doc: "Alias of R" }
                                ];
                                randomModes.forEach(rm => {
                                    completions.push({
                                        caption: "by." + itName + "." + rm.name,
                                        snippet: "by." + itName + "." + rm.name + "(${1:" + rm.args + "})",
                                        meta: "random",
                                        docHTML: "<b>by." + itName + "." + rm.name + "</b>: " + rm.doc + " evaluated once per " + itName,
                                        score: 3500
                                    });
                                });
                            }
                        } else if (obj === "syl") {
                            ["text", "text_stripped", "text_spacestripped", "i", "n", "syl_i", "char_i", "word_i", "duration", "dur", "start_time", "end_time", "mid_time", "syl_start", "syl_end", "syl_mid", "x", "y", "center", "middle", "left", "right", "top", "bottom", "width", "height", "prespace", "postspace", "descent", "extlead", "actor", "style", "effect", "layer", "is_first", "is_last", "has_prev", "has_next", "ink", "color1", "color2", "color3", "color4", "alpha1", "alpha2", "alpha3", "alpha4", "fontname", "fontsize", "bold", "italic", "underline", "strikeout", "scale_x", "scale_y", "spacing", "outline", "shadow", "frz", "frx", "fry", "fax", "fay", "align", "pos_x", "pos_y", "org_x", "org_y"].forEach(p => {
                                completions.push({
                                    caption: "syl." + p,
                                    value: "syl." + p,
                                    meta: "syl",
                                    score: 2000
                                });
                            });
                        } else if (obj === "char") {
                            ["text", "text_stripped", "i", "n", "char_i", "duration", "dur", "start_time", "end_time", "mid_time", "char_start", "char_end", "char_mid", "x", "y", "center", "middle", "left", "right", "top", "bottom", "width", "height", "prespace", "postspace", "actor", "style", "is_first", "is_last", "has_prev", "has_next", "ink", "color1", "color2", "color3", "color4", "alpha1", "alpha2", "alpha3", "alpha4", "fontname", "fontsize", "bold", "italic", "underline", "strikeout", "scale_x", "scale_y", "spacing", "outline", "shadow", "frz", "frx", "fry", "fax", "fay", "align", "pos_x", "pos_y", "org_x", "org_y"].forEach(p => {
                                completions.push({
                                    caption: "char." + p,
                                    value: "char." + p,
                                    meta: "char",
                                    score: 2000
                                });
                            });
                        } else if (obj === "word") {
                            ["text", "text_stripped", "i", "n", "word_i", "duration", "dur", "start_time", "end_time", "mid_time", "word_start", "word_end", "word_mid", "x", "y", "center", "middle", "left", "right", "top", "bottom", "width", "height", "prespace", "postspace", "actor", "style", "is_first", "is_last", "has_prev", "has_next", "ink", "color1", "color2", "color3", "color4", "alpha1", "alpha2", "alpha3", "alpha4", "fontname", "fontsize", "bold", "italic", "underline", "strikeout", "scale_x", "scale_y", "spacing", "outline", "shadow", "frz", "frx", "fry", "fax", "fay", "align", "pos_x", "pos_y", "org_x", "org_y"].forEach(p => {
                                completions.push({
                                    caption: "word." + p,
                                    value: "word." + p,
                                    meta: "word",
                                    score: 2000
                                });
                            });
                        } else if (obj === "line" || obj === "l") {
                            ["text", "raw_text", "i", "n", "duration", "dur", "start_time", "end_time", "mid_time", "start", "end", "st", "et", "layer", "style", "actor", "effect", "margin_l", "margin_r", "margin_v", "width", "height", "center", "middle", "left", "right", "top", "bottom", "x", "y", "ink", "color1", "color2", "color3", "color4", "alpha1", "alpha2", "alpha3", "alpha4", "fontname", "fontsize", "bold", "italic", "underline", "strikeout", "scale_x", "scale_y", "spacing", "outline", "shadow", "frz", "frx", "fry", "fax", "fay", "align", "pos_x", "pos_y", "org_x", "org_y"].forEach(p => {
                                completions.push({
                                    caption: obj + "." + p,
                                    value: obj + "." + p,
                                    meta: obj,
                                    score: 2000
                                });
                            });
                        } else if (obj === "prev") {
                            ["text", "text_stripped", "i", "n", "duration", "dur", "start_time", "end_time", "mid_time", "x", "y", "center", "middle", "left", "right", "top", "bottom", "width", "height", "actor", "style", "ink", "color1", "color2", "color3", "color4", "alpha1", "alpha2", "alpha3", "alpha4", "fontname", "fontsize", "bold", "italic", "underline", "strikeout", "scale_x", "scale_y", "spacing", "outline", "shadow", "frz", "frx", "fry", "fax", "fay", "align", "pos_x", "pos_y", "org_x", "org_y"].forEach(p => {
                                completions.push({
                                    caption: "prev." + p,
                                    value: "prev." + p,
                                    meta: "prev",
                                    score: 2000
                                });
                            });
                        } else if (obj === "next") {
                            ["text", "text_stripped", "i", "n", "duration", "dur", "start_time", "end_time", "mid_time", "x", "y", "center", "middle", "left", "right", "top", "bottom", "width", "height", "actor", "style", "ink", "color1", "color2", "color3", "color4", "alpha1", "alpha2", "alpha3", "alpha4", "fontname", "fontsize", "bold", "italic", "underline", "strikeout", "scale_x", "scale_y", "spacing", "outline", "shadow", "frz", "frx", "fry", "fax", "fay", "align", "pos_x", "pos_y", "org_x", "org_y"].forEach(p => {
                                completions.push({
                                    caption: "next." + p,
                                    value: "next." + p,
                                    meta: "next",
                                    score: 2000
                                });
                            });
                        } else if (obj === "ink") {
                            ["width", "height", "center", "middle", "left", "right", "top", "bottom", "x", "y", "syl", "char", "word", "line", "l"].forEach(p => {
                                completions.push({
                                    caption: "ink." + p,
                                    value: "ink." + p,
                                    meta: "ink (contour)",
                                    score: 2200
                                });
                            });
                        } else if (obj === "fx") {
                            ["pos_x", "pos_y", "x", "y", "org_x", "org_y", "i", "n", "start_time", "end_time", "dur", "st", "et", "align"].forEach(p => {
                                completions.push({
                                    caption: "fx." + p,
                                    value: "fx." + p,
                                    meta: "fx",
                                    score: 2000
                                });
                            });
                        } else if (obj === "shape") {
                            ["circle", "triangle", "rectangle", "circangle", "pixel", "pentagon", "hexagon", "octagon", "diamond", "heart", "heart2t", "heartb", "shine1t", "shine2t", "shine3t", "shine4t", "clover", "feather", "feather2", "gear", "bubble", "note1t", "note2t", "note3t", "note4t", "star", "star1t", "star2t", "star3t", "star4t", "star5t", "star6t", "star7t", "star8t", "star9t", "star10t", "sakura", "sakura1t", "sakura2t", "sakura3t", "sakura4t", "sakura5t", "sakura6t", "sakura7t", "snowflake1t", "snowflake2t", "snowflake3t", "flower1t", "flower2t", "flower3t", "flower4t", "flower5t", "flower6t", "flower7t", "flower8t", "flower9t", "flower10t", "flower11t", "flower12t", "flower13t", "flower14t", "flower15t", "flower16t", "flower17t", "flower18t", "flower19t", "flower20t", "flower21t", "flower22t", "flower23t", "flower24t", "flower25t", "flower26t", "flower27t", "flower28t", "flower29t", "crystal17", "geometric10", "diagonal13r", "diagonal13l"].forEach(p => {
                                completions.push({
                                    caption: "shape." + p,
                                    value: "shape." + p,
                                    meta: "shape (preset)",
                                    docHTML: "<b>shape." + p + "</b>: Pyxis canonical ASS vector preset",
                                    score: 2200
                                });
                            });
                        } else if (obj === "sync") {
                            ["next", "prev", "order_next", "order_prev", "style_next", "style_prev", "actor_next", "actor_prev", "effect_next", "effect_prev", "layer_next", "layer_prev"].forEach(p => {
                                completions.push({
                                    caption: obj + "." + p,
                                    value: obj + "." + p,
                                    meta: "sync (float)",
                                    docHTML: "<b>" + obj + "." + p + "</b>: Inter-line gap in ms (capped at maxgap/2000ms)",
                                    score: 2500
                                });
                            });
                        } else if (obj === "math") {
                            ["sin", "cos", "tan", "sqrt", "floor", "ceil", "abs", "pi", "radians", "degrees", "rad", "deg", "atan2", "hypot", "log", "exp", "random"].forEach(p => {
                                completions.push({
                                    caption: "math." + p,
                                    value: "math." + p,
                                    meta: "math",
                                    score: 2000
                                });
                            });
                        } else if (obj === "string") {
                            ["format", "sub", "len", "upper", "lower", "reverse", "gsub", "match", "byte", "char", "find"].forEach(p => {
                                completions.push({
                                    caption: "string." + p,
                                    value: "string." + p,
                                    meta: "string",
                                    score: 2000
                                });
                            });
                        } else if (obj === "table") {
                            ["insert", "concat", "remove", "sort"].forEach(p => {
                                completions.push({
                                    caption: "table." + p,
                                    value: "table." + p,
                                    meta: "table",
                                    score: 2000
                                });
                            });
                        }
                    }

                    const taggedCompletions = completions.map(c => Object.assign({}, c, { completer: completerObj }));
                    callback(null, taggedCompletions);
                }
            };
            return completerObj;
        }

        let __cached_user_code_templates = null;

        function loadStoredUserTemplates() {
            if (__cached_user_code_templates !== null) return __cached_user_code_templates;
            let templates = {};
            try {
                const local = localStorage.getItem("pyxis_code_script_templates");
                if (local) {
                    templates = JSON.parse(local) || {};
                }
            } catch (e) {
                console.warn("Pyxis: error al leer templates de localStorage", e);
            }
            __cached_user_code_templates = templates;
            return templates;
        }

        function persistUserTemplates(templates) {
            __cached_user_code_templates = templates;
            try {
                localStorage.setItem("pyxis_code_script_templates", JSON.stringify(templates));
            } catch (e) {
                console.warn("Pyxis: error saving to localStorage", e);
            }
            if (window.pywebview && window.pywebview.api && window.pywebview.api.save_code_templates) {
                window.pywebview.api.save_code_templates(templates).catch(err => {
                    console.warn("Pyxis: error persisting user_code_templates to disk", err);
                });
            }
        }

        function refreshCodeTemplatesDropdown(selectedKey) {
            const select = document.getElementById("pyxis-code-template-select");
            if (!select) return;

            const node = window.__active_code_script_node;
            const currentLang = (node && node.properties && node.properties.language === "Lua") ? "Lua" : "Python";

            const userTemplates = loadStoredUserTemplates();
            const selectText = window.t ? window.t("code_editor.select_template") : "-- Select template --";
            let html = `<option value="">${escapeHtml(selectText)}</option>`;

            const exampleGroupLabel = window.t ? window.t("code_editor.example_group", { lang: currentLang }) : `Example Template (${currentLang})`;
            const defaultTplName = window.t ? window.t(`code_editor.${currentLang.toLowerCase()}_default_tpl_name`) : `${currentLang}: Alternate colors by syllable index`;

            if (currentLang === "Python") {
                html += `
                    <optgroup label="${escapeHtml(exampleGroupLabel)}">
                        <option value="python_default">${escapeHtml(defaultTplName)}</option>
                    </optgroup>
                `;
            } else {
                html += `
                    <optgroup label="${escapeHtml(exampleGroupLabel)}">
                        <option value="lua_default">${escapeHtml(defaultTplName)}</option>
                    </optgroup>
                `;
            }

            const userKeys = Object.keys(userTemplates).filter(key => {
                const tpl = userTemplates[key];
                return (tpl && (tpl.lang === currentLang || (!tpl.lang && currentLang === "Python")));
            });

            if (userKeys.length > 0) {
                const myTemplatesLabel = window.t ? window.t("code_editor.my_templates_group", { lang: currentLang }) : `My Templates (${currentLang})`;
                html += `<optgroup label="${escapeHtml(myTemplatesLabel)}">`;
                userKeys.forEach(key => {
                    const tpl = userTemplates[key];
                    const name = tpl.name || key;
                    html += `<option value="${escapeHtml(key)}">${escapeHtml(name)}</option>`;
                });
                html += `</optgroup>`;
            }

            select.innerHTML = html;
            if (selectedKey) {
                select.value = selectedKey;
            }
        }

        function saveCustomCodeTemplate() {
            let code = "";
            if (window.__pyxis_ace_editor) {
                code = window.__pyxis_ace_editor.getValue();
            } else {
                const textarea = document.getElementById("pyxis-code-textarea");
                if (textarea) code = textarea.value;
            }

            if (!code || !code.trim()) {
                alert(window.t ? window.t("code_editor.alert_empty") : "The code editor is empty. Write something before saving it as a template.");
                return;
            }

            const node = window.__active_code_script_node;
            const currentLang = (node && node.properties && node.properties.language) ? node.properties.language : "Python";

            const defaultName = window.t ? window.t("code_editor.default_new_template_name", { lang: currentLang }) : `${currentLang}: My Custom Template`;
            const promptMsg = window.t ? window.t("code_editor.prompt_name", { lang: currentLang }) : `Enter a name for the new template (${currentLang}):`;
            const name = prompt(promptMsg, defaultName);
            if (!name || !name.trim()) return;

            const tplKey = "user_tpl_" + Date.now();
            const userTemplates = loadStoredUserTemplates();
            userTemplates[tplKey] = {
                name: name.trim(),
                lang: currentLang,
                code: code,
                created_at: new Date().toISOString()
            };

            persistUserTemplates(userTemplates);
            refreshCodeTemplatesDropdown(tplKey);
        }

        function deleteCustomCodeTemplate() {
            const select = document.getElementById("pyxis-code-template-select");
            if (!select || !select.value) {
                alert(window.t ? window.t("code_editor.alert_select_to_delete") : "Please select one of your custom templates from the list first to delete it.");
                return;
            }

            const tplKey = select.value;
            const userTemplates = loadStoredUserTemplates();

            if (!userTemplates[tplKey]) {
                alert(window.t ? window.t("code_editor.alert_cannot_delete_builtin") : "System example templates cannot be deleted. You can only delete your custom templates.");
                return;
            }

            const tplName = userTemplates[tplKey].name || "this template";
            const confirmMsg = window.t ? window.t("code_editor.confirm_delete", { name: tplName }) : `Are you sure you want to permanently delete template "${tplName}"?`;
            const confirmed = confirm(confirmMsg);
            if (!confirmed) return;

            delete userTemplates[tplKey];
            persistUserTemplates(userTemplates);
            refreshCodeTemplatesDropdown("");
        }

        function getPyxisT(key, params, defaultEnText) {
            if (window.PyxisI18n && typeof window.PyxisI18n.t === "function") {
                return window.PyxisI18n.t(key, params, defaultEnText);
            }
            if (typeof window.t === "function") {
                return window.t(key, params, defaultEnText);
            }
            let res = defaultEnText;
            if (params) {
                for (let p in params) {
                    res = res.split("{" + p + "}").join(params[p]);
                }
            }
            return res;
        }

        function showPyxisSyntaxErrorTooltip(node, e) {
            let tooltip = document.getElementById("pyxis-syntax-warning-tooltip");
            if (!tooltip) {
                tooltip = document.createElement("div");
                tooltip.id = "pyxis-syntax-warning-tooltip";
                tooltip.style.cssText = "position: fixed; z-index: 99999; display: none; opacity: 0; transition: opacity 0.15s ease, transform 0.15s ease; transform: translateY(4px); pointer-events: none; background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(239, 68, 68, 0.5); border-radius: 8px; padding: 10px 14px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px rgba(239, 68, 68, 0.2); max-width: 320px; font-family: system-ui, -apple-system, sans-serif;";
                document.body.appendChild(tooltip);
            }

            const titleText = getPyxisT("code_editor.syntax_error_title", null, "Syntax Error Detected:");
            const errorDetail = node.syntax_error_msg || getPyxisT("code_editor.syntax_error_default", null, "A syntax error was detected in the script. Click to open editor and fix it.");

            tooltip.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; color: #ef4444; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
                    <svg style="width: 14px; height: 14px; fill: currentColor; flex-shrink: 0;" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                    <span>${titleText}</span>
                </div>
                <div style="color: #f1f5f9; font-size: 12px; line-height: 1.4; word-break: break-word;">
                    ${errorDetail}
                </div>
            `;

            const mouseX = e.clientX || (e.canvasX ? e.canvasX : 100);
            const mouseY = e.clientY || (e.canvasY ? e.canvasY : 100);

            tooltip.style.left = (mouseX + 14) + "px";
            tooltip.style.top = (mouseY + 14) + "px";
            tooltip.style.display = "block";
            requestAnimationFrame(() => {
                tooltip.style.opacity = "1";
                tooltip.style.transform = "translateY(0)";
            });
        }

        function hidePyxisSyntaxErrorTooltip() {
            const tooltip = document.getElementById("pyxis-syntax-warning-tooltip");
            if (tooltip && tooltip.style.display !== "none") {
                tooltip.style.opacity = "0";
                tooltip.style.transform = "translateY(4px)";
                setTimeout(() => {
                    if (tooltip.style.opacity === "0") tooltip.style.display = "none";
                }, 150);
            }
        }

        /**
         * Validates script syntax in real time for Python and Lua code snippets.
         * Detects unbalanced delimiters (brackets, braces, parentheses), unterminated string literals,
         * missing colons in Python control structures, and unmatched block statements in Lua.
         *
         * @param {string} script - Source code to validate.
         * @param {string} [language="Python"] - Programming language target ("Python" or "Lua").
         * @returns {{valid: boolean, line?: number, error?: string}} Validation result object.
         */
        function validatePyxisScriptSyntax(script, language) {
            const code = String(script || "").trim();
            if (!code) return { valid: true, error: null };

            const lang = String(language || "Python").trim().toLowerCase();
            const isPython = (lang === "python");

            if (isPython) {
                const stack = [];
                const pairs = { '(': ')', '[': ']', '{': '}' };
                const closing = { ')': '(', ']': '[', '}': '{' };
                const lines = code.split('\n');

                let inString = false;
                let stringChar = '';

                for (let lIdx = 0; lIdx < lines.length; lIdx++) {
                    const line = lines[lIdx];
                    const trimmed = line.trim();

                    if (trimmed.startsWith('#')) continue;

                    const ctrlMatch = trimmed.match(/^(if|elif|else|def|class|for|while|try|except|finally|with)\b/);
                    if (ctrlMatch && !trimmed.endsWith(':') && !trimmed.endsWith('\\') && !trimmed.endsWith('(') && !trimmed.endsWith('[')) {
                        if (!trimmed.includes(':') && !line.endsWith(',')) {
                            return {
                                valid: false,
                                line: lIdx + 1,
                                error: getPyxisT("code_editor.err_missing_colon", { statement: ctrlMatch[1], line: lIdx + 1 }, `Missing ':' at end of '${ctrlMatch[1]}' statement (line ${lIdx + 1})`)
                            };
                        }
                    }

                    for (let i = 0; i < line.length; i++) {
                        const ch = line[i];
                        if (inString) {
                            if (ch === stringChar && line[i - 1] !== '\\') {
                                inString = false;
                                stringChar = '';
                            }
                        } else {
                            if (ch === '"' || ch === "'") {
                                if (line.substr(i, 3) === '"""' || line.substr(i, 3) === "'''") {
                                    const tq = line.substr(i, 3);
                                    const rest = code.substring(code.indexOf(tq) + 3);
                                    if (!rest.includes(tq)) {
                                        return {
                                            valid: false,
                                            line: lIdx + 1,
                                            error: getPyxisT("code_editor.err_unclosed_triple_quotes", { tq, line: lIdx + 1 }, `Unclosed triple quotes ${tq} (line ${lIdx + 1})`)
                                        };
                                    }
                                    i += 2;
                                } else {
                                    inString = true;
                                    stringChar = ch;
                                }
                            } else if (pairs[ch]) {
                                stack.push({ ch, line: lIdx + 1 });
                            } else if (closing[ch]) {
                                if (stack.length === 0 || pairs[stack[stack.length - 1].ch] !== ch) {
                                    return {
                                        valid: false,
                                        line: lIdx + 1,
                                        error: getPyxisT("code_editor.err_mismatched_close", { ch, line: lIdx + 1 }, `Mismatched closing character '${ch}' (line ${lIdx + 1})`)
                                    };
                                }
                                stack.pop();
                            }
                        }
                    }

                    if (inString && !line.includes('"""') && !line.includes("'''")) {
                        return {
                            valid: false,
                            line: lIdx + 1,
                            error: getPyxisT("code_editor.err_unclosed_quote", { stringChar, line: lIdx + 1 }, `Unclosed quote ${stringChar} (line ${lIdx + 1})`)
                        };
                    }
                    inString = false;
                }

                if (stack.length > 0) {
                    const top = stack[stack.length - 1];
                    return {
                        valid: false,
                        line: top.line,
                        error: getPyxisT("code_editor.err_unclosed_open", { ch: top.ch, line: top.line }, `Unclosed opening character '${top.ch}' (line ${top.line})`)
                    };
                }

                const lastLine = lines[lines.length - 1].trim();
                if (/[\+\-\*\/\%\=\<\>\,\.]\s*$/.test(lastLine) && !lastLine.endsWith('\\')) {
                    return {
                        valid: false,
                        line: lines.length,
                        error: getPyxisT("code_editor.err_incomplete", { line: lines.length }, `Incomplete statement or trailing operator at line ${lines.length}`)
                    };
                }
            } else {
                const stack = [];
                const pairs = { '(': ')', '[': ']', '{': '}' };
                const closing = { ')': '(', ']': '[', '}': '{' };
                const lines = code.split('\n');

                let inString = false;
                let stringChar = '';

                for (let lIdx = 0; lIdx < lines.length; lIdx++) {
                    const line = lines[lIdx];
                    const trimmed = line.trim();

                    if (trimmed.startsWith('--')) continue;

                    if (/^\s*(if|elseif)\b/.test(trimmed) && !/\bthen\b/.test(trimmed) && !trimmed.endsWith('(') && !trimmed.endsWith(',')) {
                        return {
                            valid: false,
                            line: lIdx + 1,
                            error: getPyxisT("code_editor.err_missing_then", { line: lIdx + 1 }, `Missing 'then' after 'if/elseif' (line ${lIdx + 1})`)
                        };
                    }

                    if (/^\s*(for|while)\b/.test(trimmed) && !/\bdo\b/.test(trimmed) && !trimmed.endsWith('(') && !trimmed.endsWith(',')) {
                        return {
                            valid: false,
                            line: lIdx + 1,
                            error: getPyxisT("code_editor.err_missing_do", { line: lIdx + 1 }, `Missing 'do' after 'for/while' (line ${lIdx + 1})`)
                        };
                    }

                    for (let i = 0; i < line.length; i++) {
                        const ch = line[i];
                        if (inString) {
                            if (ch === stringChar && line[i - 1] !== '\\') {
                                inString = false;
                                stringChar = '';
                            }
                        } else {
                            if (ch === '"' || ch === "'") {
                                inString = true;
                                stringChar = ch;
                            } else if (pairs[ch]) {
                                stack.push({ ch, line: lIdx + 1 });
                            } else if (closing[ch]) {
                                if (stack.length === 0 || pairs[stack[stack.length - 1].ch] !== ch) {
                                    return {
                                        valid: false,
                                        line: lIdx + 1,
                                        error: getPyxisT("code_editor.err_mismatched_close", { ch, line: lIdx + 1 }, `Mismatched closing character '${ch}' (line ${lIdx + 1})`)
                                    };
                                }
                                stack.pop();
                            }
                        }
                    }

                    if (inString) {
                        return {
                            valid: false,
                            line: lIdx + 1,
                            error: getPyxisT("code_editor.err_unclosed_quote", { stringChar, line: lIdx + 1 }, `Unclosed quote ${stringChar} (line ${lIdx + 1})`)
                        };
                    }
                }

                if (stack.length > 0) {
                    const top = stack[stack.length - 1];
                    return {
                        valid: false,
                        line: top.line,
                        error: getPyxisT("code_editor.err_unclosed_open", { ch: top.ch, line: top.line }, `Unclosed opening character '${top.ch}' (line ${top.line})`)
                    };
                }

                let openCount = 0;
                let closeCount = 0;
                lines.forEach(l => {
                    const tr = l.trim();
                    if (tr.startsWith('--')) return;
                    const openMatches = tr.match(/\b(function|if|for|while)\b/g);
                    if (openMatches) openCount += openMatches.length;
                    const closeMatches = tr.match(/\b(end)\b/g);
                    if (closeMatches) closeCount += closeMatches.length;
                });

                if (openCount > closeCount) {
                    return {
                        valid: false,
                        line: lines.length,
                        error: getPyxisT("code_editor.err_missing_end", { count: openCount - closeCount }, `Missing 'end' block at end of Lua script (${openCount - closeCount} unclosed)`)
                    };
                } else if (closeCount > openCount) {
                    return {
                        valid: false,
                        line: lines.length,
                        error: getPyxisT("code_editor.err_extra_end", null, `Extra 'end' blocks in Lua script`)
                    };
                }
            }

            if (window.__pyxis_ace_editor && window.__pyxis_ace_editor.session) {
                const annos = window.__pyxis_ace_editor.session.getAnnotations() || [];
                const errAnno = annos.find(a => a.type === "error");
                if (errAnno) {
                    return {
                        valid: false,
                        line: errAnno.row + 1,
                        error: getPyxisT("code_editor.err_ace_syntax", { line: errAnno.row + 1, msg: errAnno.text }, `Syntax error (line ${errAnno.row + 1}): ${errAnno.text}`)
                    };
                }
            }

            return { valid: true, error: null };
        }

        function openCodigoScriptModal(node, propertyName, titleName) {
            if (window.__pyxis_ace_editor) {
                try { window.__pyxis_ace_editor.destroy(); } catch(e){}
                window.__pyxis_ace_editor = null;
            }

            let modalOverlay = document.getElementById("pyxis-code-editor-modal");
            if (!modalOverlay) {
                modalOverlay = document.createElement("div");
                modalOverlay.id = "pyxis-code-editor-modal";
                modalOverlay.className = "pyxis-modal-overlay";
                document.body.appendChild(modalOverlay);
            }

            const isDefinirVars = (node && (node.title === "Define Vars" || (node.type && String(node.type).includes("Define Vars"))));
            const targetProp = propertyName || (isDefinirVars ? "variables" : "script");
            const targetTitle = titleName || (isDefinirVars ? (window.t ? window.t("code_editor.title_vars") : "Variables Editor") : (window.t ? window.t("code_editor.title_script") : "Script Code Editor"));
            const currentLang = String(node.properties.language || "Python");
            const currentScript = String(node.properties[targetProp] || "");

            modalOverlay.innerHTML = `
                <div class="pyxis-code-modal">
                    <div class="pyxis-code-header">
                        <div class="pyxis-code-title">
                            <svg class="svg-icon" style="width: 18px; height: 18px; color: #38BDF8;" viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                            <span>${escapeHtml(targetTitle)}</span>
                            <span class="pyxis-code-badge" id="modal-lang-badge" style="background: ${currentLang === 'Python' ? '#8B5CF6' : '#10B981'};">${currentLang}</span>
                        </div>
                        <button class="pyxis-code-btn pyxis-code-btn-secondary" onclick="closeCodigoScriptModal()" style="padding: 4px 8px; display: inline-flex; align-items: center; justify-content: center;" title="${window.t ? window.t("common.close") : "Close"}">
                            <svg class="svg-icon" style="width: 14px; height: 14px;" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                    <div class="pyxis-code-body">
                        <div class="pyxis-code-main">
                            <div class="pyxis-template-select-row">
                                <span style="font-size: 12px; font-weight: 600; color: #94A3B8;">${window.t ? window.t("code_editor.templates") : "Templates:"}</span>
                                <select class="pyxis-template-select" id="pyxis-code-template-select" name="pyxis-code-template-select" onchange="applyCodeTemplate(this.value)">
                                    <option value="">${window.t ? window.t("code_editor.select_template") : "-- Select template --"}</option>
                                </select>
                            </div>
                            <div class="pyxis-code-editor-container">
                                <div id="pyxis-ace-editor" style="width: 100%; height: 100%;"></div>
                                <textarea id="pyxis-code-textarea" name="pyxis-code-textarea" style="display: none; width: 100%; height: 100%; background: #12161f; color: #a7f3d0; border: 1px solid #8b5cf6; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 13px; resize: none;"></textarea>
                            </div>
                        </div>
                    </div>
                    <div class="pyxis-code-footer">
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <button class="pyxis-code-btn pyxis-code-btn-secondary" onclick="saveCustomCodeTemplate()" title="${window.t ? window.t("code_editor.save_template_tooltip") : "Save current script as reusable template"}" style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px;">
                                <svg class="svg-icon" style="width: 14px; height: 14px; color: #38BDF8;" viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                                <span>${window.t ? window.t("code_editor.save_template") : "Save Template"}</span>
                            </button>
                            <button class="pyxis-code-btn pyxis-code-btn-secondary pyxis-btn-danger" id="btn-delete-template" onclick="deleteCustomCodeTemplate()" title="${window.t ? window.t("code_editor.delete_template_tooltip") : "Delete selected custom template"}" style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px;">
                                <svg class="svg-icon" style="width: 14px; height: 14px; color: #F87171;" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                                <span>${window.t ? window.t("code_editor.delete_template") : "Delete Template"}</span>
                            </button>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <button class="pyxis-code-btn pyxis-code-btn-secondary" onclick="closeCodigoScriptModal()">${window.t ? window.t("common.cancel") : "Cancel"}</button>
                            <button class="pyxis-code-btn pyxis-code-btn-primary" onclick="saveCodigoScriptModal()" style="display: inline-flex; align-items: center; gap: 6px;">
                                <svg class="svg-icon" style="width: 14px; height: 14px;" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                                <span>${window.t ? window.t("common.save") : "Save"}</span>
                            </button>
                        </div>
                    </div>
                </div>
            `;

            modalOverlay.style.display = "flex";
            window.__active_code_script_node = node;
            window.__active_code_script_property = targetProp;

            refreshCodeTemplatesDropdown();
            if (window.pywebview && window.pywebview.api && window.pywebview.api.get_code_templates) {
                window.pywebview.api.get_code_templates().then(saved => {
                    if (saved && typeof saved === "object" && Object.keys(saved).length > 0) {
                        const local = loadStoredUserTemplates();
                        __cached_user_code_templates = Object.assign({}, local, saved);
                        try { localStorage.setItem("pyxis_code_script_templates", JSON.stringify(__cached_user_code_templates)); } catch(e){}
                        refreshCodeTemplatesDropdown();
                    }
                }).catch(() => {});
            }

            try {
                if (window.ace) {
                    ace.config.set("basePath", "libs/ace");
                    ace.config.set("modePath", "libs/ace");
                    ace.config.set("themePath", "libs/ace");

                    const editor = ace.edit("pyxis-ace-editor");
                    editor.setTheme("ace/theme/dracula");
                    if (editor.session && editor.session.setUseWorker) editor.session.setUseWorker(false);
                    editor.session.setMode(currentLang === "Python" ? "ace/mode/python" : "ace/mode/lua");
                    editor.setOptions({
                        useWorker: false,
                        enableBasicAutocompletion: true,
                        enableLiveAutocompletion: true,
                        enableSnippets: true,
                        fontSize: "13px",
                        fontFamily: "monospace, 'Fira Code', Consolas",
                        showPrintMargin: false,
                        tabSize: 4,
                        useSoftTabs: true,
                        wrap: true
                    });

                    const pyxisCompleter = getPyxisCodeCompleter();
                    const langTools = ace.require("ace/ext/language_tools");
                    if (langTools) {
                        editor.completers = [pyxisCompleter];
                        if (langTools.snippetCompleter) editor.completers.push(langTools.snippetCompleter);
                        if (langTools.keyWordCompleter) editor.completers.push(langTools.keyWordCompleter);
                        if (langTools.textCompleter) editor.completers.push(langTools.textCompleter);
                    } else {
                        editor.completers = [pyxisCompleter];
                    }

                    editor.commands.addCommand({
                        name: "pyxisStartAutocomplete",
                        bindKey: { win: "Ctrl-Space", mac: "Command-Space" },
                        exec: function(ed) {
                            if (ed.completer) {
                                ed.completer.showPopup(ed);
                            } else {
                                ed.execCommand("startAutocomplete");
                            }
                        }
                    });

                    editor.setValue(currentScript, -1);
                    editor.clearSelection();
                    window.__pyxis_ace_editor = editor;

                    setTimeout(() => {
                        editor.resize();
                        editor.focus();
                    }, 50);
                } else {
                    const fallbackTa = document.getElementById("pyxis-code-textarea");
                    if (fallbackTa) {
                        fallbackTa.style.display = "block";
                        fallbackTa.value = currentScript;
                    }
                }
            } catch (err) {
                console.error("Error inicializando Ace Editor:", err);
                const fallbackTa = document.getElementById("pyxis-code-textarea");
                if (fallbackTa) {
                    fallbackTa.style.display = "block";
                    fallbackTa.value = currentScript;
                }
            }
        }

        function escapeHtml(str) {
            return String(str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
        }

        function closeCodigoScriptModal() {
            const modalOverlay = document.getElementById("pyxis-code-editor-modal");
            if (modalOverlay) modalOverlay.remove();
            window.__active_code_script_node = null;
            window.__active_code_script_property = null;
        }

        function saveCodigoScriptModal() {
            const node = window.__active_code_script_node;
            const propName = window.__active_code_script_property || "script";
            if (node) {
                let code = "";
                if (window.__pyxis_ace_editor && typeof window.__pyxis_ace_editor.getValue === "function") {
                    code = window.__pyxis_ace_editor.getValue();
                } else {
                    const textarea = document.getElementById("pyxis-code-textarea");
                    if (textarea) code = textarea.value;
                }
                node.properties[propName] = code;

                const lang = String(node.properties.language || "Python");
                const check = validatePyxisScriptSyntax(code, lang);
                node.has_syntax_error = !check.valid;
                node.syntax_error_msg = check.error;

                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.validate_script_syntax === "function") {
                    window.pywebview.api.validate_script_syntax(code, lang).then(res => {
                        if (res && res.valid === false) {
                            node.has_syntax_error = true;
                            node.syntax_error_msg = res.error;
                        } else if (!check.valid) {
                            node.has_syntax_error = true;
                            node.syntax_error_msg = check.error;
                        } else {
                            node.has_syntax_error = false;
                            node.syntax_error_msg = null;
                        }
                        if (node.graph && node.graph.setDirtyCanvas) node.graph.setDirtyCanvas(true, true);
                        if (LGraphCanvas.active_canvas && LGraphCanvas.active_canvas.setDirtyCanvas) LGraphCanvas.active_canvas.setDirtyCanvas(true, true);
                    }).catch(() => {});
                }

                if (node.widgets) {
                    const w = node.widgets.find(w => w.property === propName || w.name === propName || w.name === "Variables");
                    if (w) w.value = code;
                }
                if (node.computeSize) node.size = node.computeSize();
                if (node.graph && node.graph.setDirtyCanvas) node.graph.setDirtyCanvas(true, true);
                if (LGraphCanvas.active_canvas && LGraphCanvas.active_canvas.setDirtyCanvas) LGraphCanvas.active_canvas.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("code-editor-save");
            }
            closeCodigoScriptModal();
        }

        function applyCodeTemplate(tplKey) {
            if (!tplKey) return;

            const isEn = window.PyxisI18n && window.PyxisI18n.getCurrentLanguage && window.PyxisI18n.getCurrentLanguage() === "en";
            const pyComment = isEn ? "# Toggle ASS colors by syllable index (odd/even)" : "# Alternar colores ASS por índice de sílaba (impar/par)";
            const luaComment = isEn ? "-- Toggle ASS colors by syllable index (odd/even)" : "-- Alternar colores ASS por índice de sílaba (impar/par)";

            const builtInTpls = {
                "python_default": {
                    lang: "Python",
                    code: `${pyComment}\nif syl.i % 2 == 1:\n    result = in1 if in1 else '&H0000FF&'\nelse:\n    result = in2 if in2 else '&H00FFFF&'`
                },
                "lua_default": {
                    lang: "Lua",
                    code: `${luaComment}\nif syl.i % 2 == 1 then\n    result = (in1 and in1 ~= '') and in1 or '&H0000FF&'\nelse\n    result = (in2 and in2 ~= '') and in2 or '&H00FFFF&'\nend`
                }
            };

            const userTemplates = loadStoredUserTemplates();
            let selectedTpl = builtInTpls[tplKey] || userTemplates[tplKey];

            if (selectedTpl && selectedTpl.code) {
                if (window.__pyxis_ace_editor) {
                    window.__pyxis_ace_editor.setValue(selectedTpl.code, 1);
                    window.__pyxis_ace_editor.focus();
                }
            }
        }


window.getPyxisCodeCompleter = typeof getPyxisCodeCompleter === 'function' ? getPyxisCodeCompleter : window.getPyxisCodeCompleter;
window.openCodigoScriptModal = typeof openCodigoScriptModal === 'function' ? openCodigoScriptModal : window.openCodigoScriptModal;
window.setupCodigoScriptNode = typeof setupScriptCodeNode === 'function' ? setupScriptCodeNode : window.setupCodigoScriptNode;
window.setupScriptCodeNode = typeof setupScriptCodeNode === 'function' ? setupScriptCodeNode : window.setupScriptCodeNode;
