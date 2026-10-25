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
 * @file audio_nodes.js
 * @description UI setups and waveform canvas representations for Audio category nodes.
 * @module PyxisAudioNodes
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

const WAVEFORM_MODES = [
    { full: "oscilloscope", es: "Osciloscopio", short: "Oscillo" },
    { full: "fftbars", es: "Barras FFT", short: "Bars" },
    { full: "filledwave", es: "Onda Rellena", short: "Filled" },
    { full: "radial", es: "Radial Circular", short: "Radial" },
    { full: "points", es: "Puntos", short: "Points" }
];

function setupAudioWaveformNode(node) {
            if (!node.properties) node.properties = {};
            if (node.properties.audio_path === undefined) node.properties.audio_path = "";
            const initialMode = node.properties.mode || "oscilloscope";
            node.properties.mode = initialMode;
            if (node.properties.modo !== undefined) delete node.properties.modo;

            if (node.properties.width === undefined) node.properties.width = node.properties.ancho !== undefined ? node.properties.ancho : "400";
            if (node.properties.height === undefined) node.properties.height = node.properties.alto !== undefined ? node.properties.alto : "60";
            if (node.properties.samples === undefined) node.properties.samples = node.properties.muestras !== undefined ? node.properties.muestras : "32";
            if (node.properties.gain === undefined) node.properties.gain = "1.0";
            if (node.properties.thickness === undefined) node.properties.thickness = node.properties.grosor !== undefined ? node.properties.grosor : "2";
            if (node.properties.scale === undefined) node.properties.scale = node.properties.escala !== undefined ? node.properties.escala : "1.0";
            if (node.properties.min_hz === undefined) node.properties.min_hz = "20";
            if (node.properties.max_hz === undefined) node.properties.max_hz = "16000";
            if (node.properties.start_time === undefined) node.properties.start_time = "";
            if (node.properties.end_time === undefined) node.properties.end_time = "";

            node.widgets_up = true;

            const reqInputs = [
                { name: "Audio Path", default: "", property: "audio_path" },
                { name: "Width (px)", default: "400", property: "width", alias: "ancho" },
                { name: "Height (px)", default: "60", property: "height", alias: "alto" },
                { name: "Samples", default: "32", property: "samples", alias: "muestras" },
                { name: "Gain", default: "1.0", property: "gain", alias: "ganancia" },
                { name: "Thickness (px)", default: "2", property: "thickness", alias: "grosor" },
                { name: "Scale", default: "1.0", property: "scale", alias: "escala" },
                { name: "Min Hz", default: "20", property: "min_hz" },
                { name: "Max Hz", default: "16000", property: "max_hz" },
                { name: "Start Time", default: "", property: "start_time" },
                { name: "End Time", default: "", property: "end_time" }
            ];

            node.computeSize = function() {
                let max_input_w = 0;
                const props = this.properties || node.properties || {};
                reqInputs.forEach(spec => {
                    const val = String(props[spec.property] !== undefined ? props[spec.property] : (spec.alias && props[spec.alias] !== undefined ? props[spec.alias] : spec.default));
                    const tw = getExactTextWidth(val || spec.name, "bold 11px Consolas, monospace");
                    if (tw > max_input_w) max_input_w = tw;
                });
                const neededBoxW = Math.max(65, Math.ceil(max_input_w + 36));
                const rightReserve = 110;
                const req_w = Math.max(225, 22 + neededBoxW + rightReserve);
                const req_h = Math.max(180, 11 + reqInputs.length * 23 + 24);
                return [req_w, req_h];
            };

            function updateWaveformInputs() {
                const oldInputs = node.inputs ? [...node.inputs] : [];
                node.inputs = [];

                const startY = 11;
                reqInputs.forEach((spec, idx) => {
                    const oldInp = oldInputs.find(i => i && (i.name === spec.name || i.property === spec.property || (spec.alias && (i.name === spec.alias || i.property === spec.alias)))) || oldInputs[idx];
                    const linkId = oldInp ? oldInp.link : null;
                    const yPos = startY + idx * 23;
                    const dotY = yPos + 9;

                    node.inputs.push({
                        name: spec.name,
                        type: "data",
                        link: linkId,
                        pos: [10, dotY],
                        label: " ",
                        property: spec.property
                    });
                });

                if (!node.outputs || node.outputs.length < 5) {
                    node.outputs = [
                        { name: "Shape Out", type: "data" },
                        { name: "\\pos Tag", type: "data" },
                        { name: "X Array", type: "data" },
                        { name: "Y Array", type: "data" },
                        { name: "Bandas Array", type: "data" }
                    ];
                }

                node.widgets = [];
                reqInputs.forEach((spec, idx) => {
                    const curVal = String(node.properties[spec.property] !== undefined ? node.properties[spec.property] : (spec.alias && node.properties[spec.alias] !== undefined ? node.properties[spec.alias] : spec.default));
                    const yPos = startY + idx * 23;
                    const w = node.addWidget("text", spec.name, curVal, function(val) {
                        const cleanVal = String(val || "").replace(/[\r\n]+/g, " ");
                        node.properties[spec.property] = cleanVal;
                        if (spec.alias) node.properties[spec.alias] = cleanVal;
                        if (node.computeSize) {
                            const sz = node.computeSize();
                            node.size[0] = Math.max(node.size[0], sz[0]);
                            node.size[1] = sz[1];
                        }
                        if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                    });
                    w.property = spec.property;
                    w.last_y = yPos;
                    w.y = yPos;
                    setupSingleLineTextWidget(node, w, spec.name, spec.property);
                });

                if (node.computeSize) {
                    node.size = node.computeSize();
                }
                if (node.setDirtyCanvas && node.graph) node.setDirtyCanvas(true, true);
            }

            const oldMouseDown = node.onMouseDown;
            node.onMouseDown = function(e, local_pos, canvas) {
                if (local_pos && local_pos[1] < 0) {
                    const nodeW = this.size[0];
                    const curModo = String(this.properties.mode || "Oscilloscope");
                    let curIdx = WAVEFORM_MODES.findIndex(m =>
                        m.full.toLowerCase() === curModo.toLowerCase() ||
                        m.short.toLowerCase() === curModo.toLowerCase() ||
                        (m.es && m.es.toLowerCase() === curModo.toLowerCase())
                    );
                    if (curIdx < 0) curIdx = 0;
                    const btnText = WAVEFORM_MODES[curIdx].short;
                    const font = "bold 10px monospace";
                    let textW = 50;
                    if (canvas && canvas.ctx) {
                        canvas.ctx.font = font;
                        textW = canvas.ctx.measureText(btnText).width;
                    }
                    const btnW = Math.max(55, textW + 14);
                    const btnX = nodeW - btnW - 8;

                    if (local_pos[0] >= btnX - 4 && local_pos[0] <= btnX + btnW + 6) {
                        const nextIdx = (curIdx + 1) % WAVEFORM_MODES.length;
                        const nextFull = WAVEFORM_MODES[nextIdx].full;
                        this.properties.mode = nextFull;
                        if (this.properties.modo !== undefined) delete this.properties.modo;
                        if (this.setDirtyCanvas) this.setDirtyCanvas(true, true);
                        if (window.PyxisUndoManager) window.PyxisUndoManager.recordState("waveform-mode-change");
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        return true;
                    }
                }
                if (oldMouseDown) return oldMouseDown.call(this, e, local_pos, canvas);
            };

            const oldDraw = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
                if (oldDraw) oldDraw.call(this, ctx);
                if (this.flags && this.flags.collapsed) return;

                const nodeW = this.size[0];
                const curModo = String(this.properties.mode || "Oscilloscope");
                const mObj = WAVEFORM_MODES.find(m =>
                    m.full.toLowerCase() === curModo.toLowerCase() ||
                    m.short.toLowerCase() === curModo.toLowerCase() ||
                    (m.es && m.es.toLowerCase() === curModo.toLowerCase())
                ) || WAVEFORM_MODES[0];

                ctx.save();
                ctx.font = "bold 10px monospace";
                const textW = ctx.measureText(mObj.short).width;
                const modeBtnW = Math.max(55, textW + 14);
                const modeBtnH = 20;
                const modeBtnX = nodeW - modeBtnW - 8;
                const modeBtnY = -25;

                ctx.fillStyle = "rgba(18, 22, 31, 0.85)";
                ctx.strokeStyle = "#0284c7";
                ctx.lineWidth = 1.2;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(modeBtnX, modeBtnY, modeBtnW, modeBtnH, 10);
                else ctx.rect(modeBtnX, modeBtnY, modeBtnW, modeBtnH);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = "#38bdf8";
                ctx.textAlign = "center";
                ctx.fillText(mObj.short, modeBtnX + modeBtnW / 2, modeBtnY + 14);
                ctx.restore();
            };

            const oldConfigure = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfigure) oldConfigure.call(this, info);
                updateWaveformInputs();
            };

            updateWaveformInputs();
        }


