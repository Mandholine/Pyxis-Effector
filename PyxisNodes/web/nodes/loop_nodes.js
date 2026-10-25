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
 * @file loop_nodes.js
 * @description UI setups and iteration counter inspectors for Loops category nodes.
 * @module PyxisLoopNodes
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function setupMainLoopNode(node) {
            if (!node.properties) node.properties = {};
            if (!node.properties.iterator) node.properties.iterator = "syl";
            if (!node.properties.blank_mode) node.properties.blank_mode = "No Blank (Ignorar Espacios)";
            if (node.properties.iterador !== undefined) delete node.properties.iterador;
            if (node.properties.noblank !== undefined) delete node.properties.noblank;

            node.widgets = [];

            node.computeSize = function() {
                return [255, 82];
            };
            if (node.size) {
                node.size[0] = Math.max(node.size[0] || 255, 255);
                node.size[1] = 82;
            }

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (info && info.size && Array.isArray(info.size)) {
                    this.size = [Math.max(info.size[0], 255), info.size[1]];
                } else {
                    this.size = this.computeSize();
                }
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                ctx.save();
                ctx.font = "bold 10px monospace";
                const badgeH = 20;
                const badgeY = -25;

                const iter = String(this.properties.iterator || "syl");
                const unitText = iter.toUpperCase();
                const unitTextW = ctx.measureText(unitText).width;
                const unitBadgeW = Math.max(48, unitTextW + 14);
                const unitBadgeX = this.size[0] - unitBadgeW - 8;

                this._unit_badge_bounds = { x: unitBadgeX, y: badgeY, w: unitBadgeW, h: badgeH };

                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = "#0ea5e9";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(unitBadgeX, badgeY, unitBadgeW, badgeH, 10);
                else ctx.rect(unitBadgeX, badgeY, unitBadgeW, badgeH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = "#38bdf8";
                ctx.textAlign = "center";
                ctx.fillText(unitText, unitBadgeX + unitBadgeW / 2, badgeY + 14);

                const isNoBlank = !String(this.properties.noblank || "").includes("Con") && !String(this.properties.noblank || "").includes("With");
                const blankText = window.PyxisI18n ? window.PyxisI18n.getBlankBadgeText(isNoBlank) : (isNoBlank ? "NO BLANK" : "WITH BLANK");
                const blankTextW = ctx.measureText(blankText).width;
                const blankBadgeW = Math.max(68, blankTextW + 14);
                const blankBadgeX = unitBadgeX - blankBadgeW - 6;

                this._blank_badge_bounds = { x: blankBadgeX, y: badgeY, w: blankBadgeW, h: badgeH };

                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = isNoBlank ? "#10b981" : "#64748b";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(blankBadgeX, badgeY, blankBadgeW, badgeH, 10);
                else ctx.rect(blankBadgeX, badgeY, blankBadgeW, badgeH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = isNoBlank ? "#a7f3d0" : "#94a3b8";
                ctx.textAlign = "center";
                ctx.fillText(blankText, blankBadgeX + blankBadgeW / 2, badgeY + 14);

                ctx.font = "italic 11px monospace";
                ctx.fillStyle = "#94a3b8";
                ctx.textAlign = "center";
                const iterStr = String(this.properties.iterator || "syl").toLowerCase();
                const mainLoopCounterText = `${iterStr}.i, ${iterStr}.n`;
                ctx.fillText(mainLoopCounterText, this.size[0] / 2, this.size[1] - 6);

                ctx.restore();
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, pos, canvas) {
                if (oldMouseDown && oldMouseDown.call(this, e, pos, canvas)) return true;

                if (this._unit_badge_bounds) {
                    const b = this._unit_badge_bounds;
                    if (pos[0] >= b.x && pos[0] <= b.x + b.w &&
                        pos[1] >= b.y && pos[1] <= b.y + b.h) {

                        const units = ["syl", "line", "word", "char"];
                        let idx = units.indexOf(this.properties.iterator || "syl");
                        if (idx === -1) idx = 0;
                        const nextIdx = (idx + 1) % units.length;
                        const nextUnit = units[nextIdx];
                        this.properties.iterator = nextUnit;
                        if (this.properties.iterador !== undefined) delete this.properties.iterador;

                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        return true;
                    }
                }

                if (this._blank_badge_bounds) {
                    const b = this._blank_badge_bounds;
                    if (pos[0] >= b.x && pos[0] <= b.x + b.w &&
                        pos[1] >= b.y && pos[1] <= b.y + b.h) {

                        const isNoBlank = !String(this.properties.blank_mode || this.properties.noblank || "").includes("Con") && !String(this.properties.blank_mode || this.properties.noblank || "").includes("With");
                        const nextBlank = isNoBlank ? "With Blanks (All)" : "No Blank (Ignorar Espacios)";
                        this.properties.blank_mode = nextBlank;
                        this.properties.noblank = nextBlank;

                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        return true;
                    }
                }
            };
        }

        const MAXLOOP_MODES = [
            { full: "Normal", short: "NORMAL" },
            { full: "FBF", short: "FBF" }
        ];


        function setupMaxLoopNode(node) {
            if (!node.properties) node.properties = {};
            if (node.properties.mode === undefined) node.properties.mode = "Normal";
            if (node.properties.iterations === undefined) node.properties.iterations = "3";
            if (node.properties.modo !== undefined) delete node.properties.modo;
            if (node.properties.veces !== undefined) delete node.properties.veces;
            if (node.properties.step_ms === undefined) node.properties.step_ms = "41.7";
            if (node.properties.start_time === undefined) node.properties.start_time = "start_time";
            if (node.properties.end_time === undefined) node.properties.end_time = "end_time";
            if (node.properties.var_name === undefined) node.properties.var_name = "j";

            node.widgets_up = true;

            function updateMaxLoopInputs() {
                const curMode = String(node.properties.mode || "Normal");
                const isFBF = (curMode.toLowerCase() === "fbf");

                const oldInputs = node.inputs ? [...node.inputs] : [];

                if (isFBF) {
                    const reqInputs = [
                        { name: "Loop In", type: "loop", label: "Loop In", pos: [10, 18] },
                        { name: "Start", type: "data", label: " ", pos: [10, 66], property: "start_time" },
                        { name: "End", type: "data", label: " ", pos: [10, 89], property: "end_time" }
                    ];

                    node.inputs = [];
                    reqInputs.forEach((req, idx) => {
                        const oldInp = oldInputs.find(i => i && (i.name === req.name || i.property === req.property)) || oldInputs[idx];
                        const linkId = oldInp ? oldInp.link : null;
                        node.inputs.push({
                            name: req.name,
                            type: req.type,
                            label: req.label,
                            pos: req.pos,
                            link: linkId,
                            property: req.property
                        });
                    });
                } else {
                    const link0 = (oldInputs && oldInputs.length > 0 && oldInputs[0]) ? oldInputs[0].link : null;
                    node.inputs = [{ name: "Loop In", type: "loop", label: "Loop In", pos: [10, 18], link: link0 }];
                }

                const varName = String(node.properties.var_name || "j").trim() || "j";
                if (!node.outputs || node.outputs.length < 3) {
                    node.outputs = [
                        { name: "Loop Out", type: "loop" },
                        { name: "Counter", type: "data" },
                        { name: "Total", type: "data" }
                    ];
                } else {
                    node.outputs[1].name = "Counter";
                    node.outputs[2].name = "Total";
                }

                node.widgets = [];

                const propsConfig = isFBF ? [
                    { name: "Step (ms)", prop: "step_ms", default: "41.7", y: 34 },
                    { name: "Inicio (ms)", prop: "start_time", default: "start_time", y: 57 },
                    { name: "Fin (ms)", prop: "end_time", default: "end_time", y: 80 },
                    { name: "Var Name (j)", prop: "var_name", default: "j", y: 103 }
                ] : [
                    { name: "Iterations (N)", prop: "iterations", default: "3", y: 34 },
                    { name: "Var Name (j)", prop: "var_name", default: "j", y: 57 }
                ];

                propsConfig.forEach((item) => {
                    const curVal = String(node.properties[item.prop] !== undefined ? node.properties[item.prop] : item.default);
                    const w = node.addWidget("text", item.name, curVal, function(val) {
                        const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                        node.properties[item.prop] = cleanVal;
                        if (item.prop === "var_name") {
                            updateMaxLoopInputs();
                        }
                        if (node.computeSize) node.size = node.computeSize();
                        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    });
                    w.property = item.prop;
                    w.last_y = item.y;
                    w.y = item.y;
                    setupSingleLineTextWidget(node, w, item.name, item.prop);
                });

                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            node.computeSize = function() {
                const curMode = String(this.properties ? (this.properties.mode || "Normal") : "Normal");
                const isFBF = (curMode.toLowerCase() === "fbf");
                let base_w = isFBF ? 215 : 195;
                let text_req_w = 0;
                if (this.properties) {
                    ["iterations", "step_ms", "start_time", "end_time", "var_name"].forEach(k => {
                        const val = String(this.properties[k] || "");
                        if (val.length > 0) {
                            const tw = getExactTextWidth(val, "bold 11px Consolas, monospace");
                            text_req_w = Math.max(text_req_w, tw);
                        }
                    });
                }
                const right_space = getNodeRightReserve(this);
                const boxW = Math.max(65, Math.ceil(text_req_w + 28));
                const req_h = isFBF ? 150 : 104;
                return [Math.max(base_w, 22 + boxW + right_space), req_h];
            };

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos && local_pos[1] < 0) {
                    const curMode = String(this.properties ? (this.properties.mode || "Normal") : "Normal");
                    let curIdx = MAXLOOP_MODES.findIndex(m => m.full.toLowerCase() === curMode.toLowerCase() || m.short.toLowerCase() === curMode.toLowerCase());
                    if (curIdx < 0) curIdx = 0;
                    const btnText = MAXLOOP_MODES[curIdx].short;
                    const font = "bold 10px monospace";
                    let textW = 50;
                    if (canvas && canvas.ctx) {
                        canvas.ctx.font = font;
                        textW = canvas.ctx.measureText(btnText).width;
                    }
                    const btnW = Math.max(55, textW + 14);
                    const btnX = this.size[0] - btnW - 8;

                    if (local_pos[0] >= btnX - 4 && local_pos[0] <= btnX + btnW + 6) {
                        const nextIdx = (curIdx + 1) % MAXLOOP_MODES.length;
                        const nextMode = MAXLOOP_MODES[nextIdx].full;
                        this.properties.mode = nextMode;
                        if (this.properties.modo !== undefined) delete this.properties.modo;
                        updateMaxLoopInputs();
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("maxloop-mode-change");
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        return true;
                    }
                }
                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            node.onDrawForeground = function(ctx) {
                if (this.flags && this.flags.collapsed) return;
                const nodeW = this.size[0];

                const curMode = String(this.properties ? (this.properties.mode || "Normal") : "Normal");
                const mObj = MAXLOOP_MODES.find(m => m.full.toLowerCase() === curMode.toLowerCase() || m.short.toLowerCase() === curMode.toLowerCase()) || MAXLOOP_MODES[0];
                const isFBF = (mObj.short === "FBF");

                ctx.save();
                ctx.font = "bold 10px monospace";
                const textW = ctx.measureText(mObj.short).width;
                const btnW = Math.max(50, textW + 14);
                const btnH = 20;
                const btnX = this.size[0] - btnW - 8;
                const btnY = -25;

                ctx.fillStyle = isFBF ? "rgba(6, 78, 59, 0.85)" : "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = isFBF ? "#10b981" : "#8b5cf6";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnX, btnY, btnW, btnH, 10);
                else ctx.rect(btnX, btnY, btnW, btnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = isFBF ? "#6ee7b7" : "#a7f3d0";
                ctx.textAlign = "center";
                ctx.fillText(mObj.short, btnX + btnW / 2, btnY + 14);
                ctx.restore();

                if (isFBF) {
                    if (this.widgets && this.widgets.length >= 4) {
                        this.widgets[0].y = 34; this.widgets[0].last_y = 34;
                        this.widgets[1].y = 57; this.widgets[1].last_y = 57;
                        this.widgets[2].y = 80; this.widgets[2].last_y = 80;
                        this.widgets[3].y = 103; this.widgets[3].last_y = 103;
                    }
                    if (this.inputs && this.inputs.length >= 3) {
                        this.inputs[0].label = "Loop In";
                        this.inputs[0].pos = [10, 18];
                        this.inputs[1].label = " ";
                        this.inputs[1].pos = [10, 66];
                        this.inputs[2].label = " ";
                        this.inputs[2].pos = [10, 89];
                    }
                } else {
                    if (this.widgets && this.widgets.length >= 2) {
                        this.widgets[0].y = 34; this.widgets[0].last_y = 34;
                        this.widgets[1].y = 57; this.widgets[1].last_y = 57;
                    }
                    if (this.inputs && this.inputs.length >= 1) {
                        this.inputs[0].label = "Loop In";
                        this.inputs[0].pos = [10, 18];
                    }
                }

                ctx.save();
                ctx.font = "italic 11px monospace";
                ctx.fillStyle = "#94a3b8";
                ctx.textAlign = "center";
                const varName = String(this.properties.var_name || "j").trim() || "j";
                const maxLoopCounterText = `${varName}, max${varName}`;
                ctx.fillText(maxLoopCounterText, this.size[0] / 2, this.size[1] - 6);
                ctx.restore();
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateMaxLoopInputs();
            };

            updateMaxLoopInputs();
        }


