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
 * @file time_nodes.js
 * @description UI setups and time conversion handlers for Time category nodes.
 * @module PyxisTimeNodes
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function setupTimeNode(node) {
            if (!node.properties) node.properties = {};
            const titleStr = String(node.title || node.type || "");
            const isInterpolador = (node.properties.dur !== undefined || titleStr.includes("Interpolator") || titleStr.includes("Ipol") || (node.type && String(node.type).includes("Ipol")));
            const isLoop = (node.properties.mode !== undefined || titleStr.includes("Loop"));
            if (isLoop) {
                const initialMode = node.properties.mode || "leadin";
                node.properties.mode = initialMode;
                if (node.properties.modo !== undefined) delete node.properties.modo;
            }

            node.widgets_up = true;
            
            const reqInputs = isInterpolador ? [
                { name: "Duration (ms)", type: "data", label: " " },
                { name: "Points / Values", type: "data", label: " " },
                { name: "Acceleration", type: "data", label: " " }
            ] : [
                { name: "Delay (ms)", type: "data", label: " " }
            ];

            const reqOutputs = [
                { name: "Data", type: "data" }
            ];

            function updateTimeInputs() {
                if (!node.inputs) node.inputs = [];
                reqInputs.forEach((req, idx) => {
                    if (idx >= node.inputs.length) {
                        node.addInput(req.name, req.type);
                    }
                    const inp = node.inputs[idx];
                    inp.name = req.name;
                    inp.type = req.type;
                    inp.label = req.label;
                    inp.pos = [10, isInterpolador ? (20 + idx * 23) : 20];
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

                const propsConfig = isInterpolador ? [
                    { name: "Duration (ms)", prop: "dur", aliases: ["dur", "Duration (ms)"], default: "syl.duration", y: 11, dotY: 20 },
                    { name: "Points / Values", prop: "points", aliases: ["points", "Points / Values"], default: "0, 100", y: 34, dotY: 43 },
                    { name: "Acceleration", prop: "accel", aliases: ["accel", "Acceleration"], default: "1.0", y: 57, dotY: 66 }
                ] : [
                    { name: "Delay (ms)", prop: "delay", aliases: ["delay", "Delay (ms)"], default: (titleStr.includes("Middle") || titleStr.includes("Loop") ? "30" : "40"), y: 11, dotY: 20 }
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
                let base_w = isInterpolador ? 205 : 165;
                let text_req_w = 0;
                if (node.properties) {
                    for (const k in node.properties) {
                        if (k === "modo") continue;
                        const val = String(node.properties[k] || "");
                        if (val.length > 0) {
                            const tw = getExactTextWidth(val, "bold 11px monospace");
                            if (tw > text_req_w) text_req_w = tw;
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
                const right_space = max_out_w > 0 ? (max_out_w + 38) : 20;
                const boxW = Math.max(65, Math.ceil(text_req_w + 36));
                let base_h = isInterpolador ? 102 : 56;
                return [Math.max(base_w, 22 + boxW + right_space), base_h];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                if (isLoop) {
                    const currentMode = String(this.properties.mode || "leadin");
                    const dispText = currentMode.toUpperCase();

                    ctx.save();
                    ctx.font = "bold 10px monospace";
                    const textW = ctx.measureText(dispText).width;
                    const badgeW = Math.max(54, textW + 14);
                    const badgeH = 20;
                    const badgeX = this.size[0] - badgeW - 8;
                    const badgeY = -25;

                    this._mode_badge_bounds = { x: badgeX, y: badgeY, w: badgeW, h: badgeH };

                    ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                    ctx.strokeStyle = "#2563eb";
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 10);
                    else ctx.rect(badgeX, badgeY, badgeW, badgeH);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = "#60a5fa";
                    ctx.textAlign = "center";
                    ctx.fillText(dispText, badgeX + badgeW / 2, badgeY + 14);
                    ctx.restore();
                }

                if (this.widgets) {
                    const positions = isInterpolador ? [11, 34, 57] : [11];
                    this.widgets.forEach((w, idx) => {
                        if (positions[idx] !== undefined) {
                            w.y = positions[idx];
                            w.last_y = positions[idx];
                        }
                    });
                }

                if (this.inputs) {
                    const dotPositions = isInterpolador ? [20, 43, 66] : [20];
                    this.inputs.forEach((inp, idx) => {
                        if (dotPositions[idx] !== undefined) {
                            inp.label = " ";
                            inp.pos = [10, dotPositions[idx]];
                        }
                    });
                }
            };

            if (isLoop) {
                const oldMouseDown = node.onMouseDown;
                node.onMouseDown = function(e, pos, canvas) {
                    if (oldMouseDown && oldMouseDown.call(this, e, pos, canvas)) return true;

                    if (this._mode_badge_bounds) {
                        const b = this._mode_badge_bounds;
                        if (pos[0] >= b.x && pos[0] <= b.x + b.w &&
                            pos[1] >= b.y && pos[1] <= b.y + b.h) {

                            const modes = ["leadin", "leadout", "middle1", "middle2"];
                            const curM = this.properties.mode || "leadin";
                            let idx = modes.indexOf(curM);
                            if (idx === -1) idx = 0;
                            const nextIdx = (idx + 1) % modes.length;
                            const nextMode = modes[nextIdx];
                            this.properties.mode = nextMode;
                            if (this.properties.modo !== undefined) delete this.properties.modo;

                            if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        }
                    }
                };
            }

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateTimeInputs();
            };

            updateTimeInputs();
        }


        function setupOffsetNode(node) {
            if (!node) return;
            if (!node.properties) node.properties = {};
            if (node.properties.offset === undefined) node.properties.offset = "100";

            node.widgets_up = true;
            if (!node.inputs || node.inputs.length === 0) {
                node.inputs = [{ name: "Base (ms)", type: "data", label: " ", pos: [10, 20] }];
            } else {
                while (node.inputs.length > 1) {
                    node.removeInput(node.inputs.length - 1);
                }
                node.inputs[0].name = "Base (ms)";
                node.inputs[0].type = "data";
                node.inputs[0].label = " ";
                node.inputs[0].pos = [10, 20];
            }
            if (!node.outputs || node.outputs.length === 0) {
                node.outputs = [{ name: "Time (ms)", type: "data", pos: [node.size ? node.size[0] - 10 : 185, 20] }];
            } else {
                while (node.outputs.length > 1) {
                    node.removeOutput(node.outputs.length - 1);
                }
                node.outputs[0].name = "Time (ms)";
                node.outputs[0].type = "data";
                node.outputs[0].pos = [node.size ? node.size[0] - 10 : 185, 20];
            }

            node.widgets = [];
            const curVal = String(node.properties.offset !== undefined ? node.properties.offset : "100");
            const w = node.addWidget("text", "Offset (ms)", curVal, function(val) {
                const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                node.properties.offset = cleanVal;
                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            });
            w.property = "offset";
            w.y = 11;
            w.last_y = 11;
            setupSingleLineTextWidget(node, w, "Offset (ms)", "offset");

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const valStr = String(props.offset !== undefined ? props.offset : "100");
                const textWidth = getExactTextWidth(valStr, "bold 11px Consolas, monospace");
                const boxW = Math.max(65, Math.ceil(textWidth + 28));
                const right_space = getNodeRightReserve(this);
                return [Math.max(195, 22 + boxW + right_space), 56];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;
                if (this.widgets && this.widgets[0]) {
                    this.widgets[0].y = 11;
                    this.widgets[0].last_y = 11;
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].label = " ";
                    this.inputs[0].pos = [10, 20];
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [this.size[0] - 10, 20];
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                while (this.inputs && this.inputs.length > 1) {
                    this.removeInput(this.inputs.length - 1);
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].name = "Base (ms)";
                    this.inputs[0].type = "data";
                    this.inputs[0].label = " ";
                    this.inputs[0].pos = [10, 20];
                }
                while (this.outputs && this.outputs.length > 1) {
                    this.removeOutput(this.outputs.length - 1);
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].name = "Time (ms)";
                    this.outputs[0].type = "data";
                    this.outputs[0].pos = [this.size[0] - 10, 20];
                }
                if (this.widgets && this.widgets[0] && this.properties && this.properties.offset !== undefined) {
                    this.widgets[0].value = String(this.properties.offset);
                }
                if (this.computeSize) {
                    this.size = this.computeSize();
                }
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            if (node.computeSize) node.size = node.computeSize();
        }

        function setupParseASSTimeNode(node) {
            if (!node) return;
            if (!node.properties) node.properties = {};
            if (node.properties.ass_time === undefined) node.properties.ass_time = "0:00:00.00";

            node.widgets_up = true;
            if (!node.inputs || node.inputs.length === 0) {
                node.inputs = [{ name: "ASS Time", type: "data", label: " ", pos: [10, 20] }];
            } else {
                while (node.inputs.length > 1) {
                    node.removeInput(node.inputs.length - 1);
                }
                node.inputs[0].name = "ASS Time";
                node.inputs[0].type = "data";
                node.inputs[0].label = " ";
                node.inputs[0].pos = [10, 20];
            }
            if (!node.outputs || node.outputs.length === 0) {
                node.outputs = [{ name: "Time (ms)", type: "data", pos: [node.size ? node.size[0] - 10 : 215, 20] }];
            } else {
                while (node.outputs.length > 1) {
                    node.removeOutput(node.outputs.length - 1);
                }
                node.outputs[0].name = "Time (ms)";
                node.outputs[0].type = "data";
                node.outputs[0].pos = [node.size ? node.size[0] - 10 : 215, 20];
            }

            node.widgets = [];
            const curVal = String(node.properties.ass_time !== undefined ? node.properties.ass_time : "0:00:00.00");
            const w = node.addWidget("text", "ASS Time", curVal, function(val) {
                const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                node.properties.ass_time = cleanVal;
                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            });
            w.property = "ass_time";
            w.y = 11;
            w.last_y = 11;
            setupSingleLineTextWidget(node, w, "ASS Time", "ass_time");

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const valStr = String(props.ass_time !== undefined ? props.ass_time : "0:00:00.00");
                const textWidth = getExactTextWidth(valStr, "bold 11px Consolas, monospace");
                const boxW = Math.max(85, Math.ceil(textWidth + 28));
                const right_space = getNodeRightReserve(this);
                return [Math.max(215, 22 + boxW + right_space), 56];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;
                if (this.widgets && this.widgets[0]) {
                    this.widgets[0].y = 11;
                    this.widgets[0].last_y = 11;
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].label = " ";
                    this.inputs[0].pos = [10, 20];
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [this.size[0] - 10, 20];
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                while (this.inputs && this.inputs.length > 1) {
                    this.removeInput(this.inputs.length - 1);
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].name = "ASS Time";
                    this.inputs[0].type = "data";
                    this.inputs[0].label = " ";
                    this.inputs[0].pos = [10, 20];
                }
                while (this.outputs && this.outputs.length > 1) {
                    this.removeOutput(this.outputs.length - 1);
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].name = "Time (ms)";
                    this.outputs[0].type = "data";
                    this.outputs[0].pos = [this.size[0] - 10, 20];
                }
                if (this.widgets && this.widgets[0] && this.properties && this.properties.ass_time !== undefined) {
                    this.widgets[0].value = String(this.properties.ass_time);
                }
                if (this.computeSize) {
                    this.size = this.computeSize();
                }
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            if (node.computeSize) node.size = node.computeSize();
        }

        function setupFormatASSTimeNode(node) {
            if (!node) return;
            if (!node.properties) node.properties = {};
            if (node.properties.time === undefined) node.properties.time = "0:00:00.00";

            node.widgets_up = true;
            if (!node.inputs || node.inputs.length === 0) {
                node.inputs = [{ name: "Time (ms)", type: "data", label: " ", pos: [10, 20] }];
            } else {
                while (node.inputs.length > 1) {
                    node.removeInput(node.inputs.length - 1);
                }
                node.inputs[0].name = "Time (ms)";
                node.inputs[0].type = "data";
                node.inputs[0].label = " ";
                node.inputs[0].pos = [10, 20];
            }
            if (!node.outputs || node.outputs.length === 0) {
                node.outputs = [{ name: "ASS Time", type: "data", pos: [node.size ? node.size[0] - 10 : 215, 20] }];
            } else {
                while (node.outputs.length > 1) {
                    node.removeOutput(node.outputs.length - 1);
                }
                node.outputs[0].name = "ASS Time";
                node.outputs[0].type = "data";
                node.outputs[0].pos = [node.size ? node.size[0] - 10 : 215, 20];
            }

            node.widgets = [];
            const curVal = String(node.properties.time !== undefined ? node.properties.time : "0:00:00.00");
            const w = node.addWidget("text", "ASS Time", curVal, function(val) {
                const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                node.properties.time = cleanVal;
                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            });
            w.property = "time";
            w.y = 11;
            w.last_y = 11;
            setupSingleLineTextWidget(node, w, "ASS Time", "time");

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const valStr = String(props.time !== undefined ? props.time : "0:00:00.00");
                const textWidth = getExactTextWidth(valStr, "bold 11px Consolas, monospace");
                const boxW = Math.max(85, Math.ceil(textWidth + 28));
                const right_space = getNodeRightReserve(this);
                return [Math.max(215, 22 + boxW + right_space), 56];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;
                if (this.widgets && this.widgets[0]) {
                    this.widgets[0].y = 11;
                    this.widgets[0].last_y = 11;
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].label = " ";
                    this.inputs[0].pos = [10, 20];
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].pos = [this.size[0] - 10, 20];
                }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                while (this.inputs && this.inputs.length > 1) {
                    this.removeInput(this.inputs.length - 1);
                }
                if (this.inputs && this.inputs[0]) {
                    this.inputs[0].name = "Time (ms)";
                    this.inputs[0].type = "data";
                    this.inputs[0].label = " ";
                    this.inputs[0].pos = [10, 20];
                }
                while (this.outputs && this.outputs.length > 1) {
                    this.removeOutput(this.outputs.length - 1);
                }
                if (this.outputs && this.outputs[0]) {
                    this.outputs[0].name = "ASS Time";
                    this.outputs[0].type = "data";
                    this.outputs[0].pos = [this.size[0] - 10, 20];
                }
                if (this.widgets && this.widgets[0] && this.properties && this.properties.time !== undefined) {
                    this.widgets[0].value = String(this.properties.time);
                }
                if (this.computeSize) {
                    this.size = this.computeSize();
                }
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            if (node.computeSize) node.size = node.computeSize();
        }

        function setupDurationNode(node) {
            if (!node) return;
            if (!node.properties) node.properties = {};
            if (node.properties.start_time === undefined) node.properties.start_time = "line.start_time";
            if (node.properties.end_time === undefined) node.properties.end_time = "line.end_time";

            node.widgets_up = true;
            if (!node.inputs || node.inputs.length < 2) {
                node.inputs = [
                    { name: "Start Time (ms)", type: "data", label: " ", pos: [10, 20] },
                    { name: "End Time (ms)", type: "data", label: " ", pos: [10, 43] }
                ];
            } else {
                node.inputs[0].label = " "; node.inputs[0].pos = [10, 20];
                node.inputs[1].label = " "; node.inputs[1].pos = [10, 43];
            }
            if (!node.outputs || node.outputs.length === 0) {
                node.outputs = [{ name: "Duration (ms)", type: "data" }];
            }

            node.widgets = [];
            const valStart = String(node.properties.start_time);
            const valEnd = String(node.properties.end_time);

            const wStart = node.addWidget("text", "Start Time (ms)", valStart, function(val) {
                const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                node.properties.start_time = cleanVal;
                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            });
            wStart.property = "start_time";
            wStart.y = 11; wStart.last_y = 11;
            setupSingleLineTextWidget(node, wStart, "Start Time (ms)", "start_time");

            const wEnd = node.addWidget("text", "End Time (ms)", valEnd, function(val) {
                const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                node.properties.end_time = cleanVal;
                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
            });
            wEnd.property = "end_time";
            wEnd.y = 34; wEnd.last_y = 34;
            setupSingleLineTextWidget(node, wEnd, "End Time (ms)", "end_time");

            node.computeSize = function() {
                const props = this.properties || node.properties || {};
                const valS = String(props.start_time || "");
                const valE = String(props.end_time || "");
                const tw = Math.max(getExactTextWidth(valS, "bold 11px Consolas, monospace"), getExactTextWidth(valE, "bold 11px Consolas, monospace"));
                const boxW = Math.max(85, Math.ceil(tw + 28));
                const right_space = getNodeRightReserve(this);
                return [Math.max(235, 22 + boxW + right_space), 79];
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;
                if (this.widgets) {
                    if (this.widgets[0]) { this.widgets[0].y = 11; this.widgets[0].last_y = 11; }
                    if (this.widgets[1]) { this.widgets[1].y = 34; this.widgets[1].last_y = 34; }
                }
                if (this.inputs && this.inputs[0]) { this.inputs[0].label = " "; this.inputs[0].pos = [10, 20]; }
                if (this.inputs && this.inputs[1]) { this.inputs[1].label = " "; this.inputs[1].pos = [10, 43]; }
                if (this.outputs && this.outputs[0]) { this.outputs[0].pos = [this.size[0] - 10, 32]; }
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                if (this.widgets) {
                    if (this.widgets[0] && this.properties.start_time !== undefined) this.widgets[0].value = String(this.properties.start_time);
                    if (this.widgets[1] && this.properties.end_time !== undefined) this.widgets[1].value = String(this.properties.end_time);
                }
                if (this.inputs && this.inputs[0]) { this.inputs[0].label = " "; this.inputs[0].pos = [10, 20]; }
                if (this.inputs && this.inputs[1]) { this.inputs[1].label = " "; this.inputs[1].pos = [10, 43]; }
                if (this.computeSize) {
                    const sz = this.computeSize();
                    this.size[0] = Math.max(this.size[0], sz[0]);
                    this.size[1] = Math.max(this.size[1], sz[1]);
                }
                if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
            };

            if (node.computeSize) node.size = node.computeSize();
        }

        window.setupDuracionNode = setupDurationNode;
        window.setupDurationNode = setupDurationNode;


