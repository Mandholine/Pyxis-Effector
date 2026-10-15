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
 * For any question you can visit: https://discord.gg/rYsARc3fB9
 */

(function () {
    "use strict";

    var save_delay_ms = 100;
    var save_timer = null;
    var save_in_flight = false;
    var save_again = false;
    var last_saved_json = "";
    var started = false;

    function api_ready() {
        return window.pywebview && window.pywebview.api &&
            typeof window.pywebview.api.save_session === "function";
    }

    function graph_ready() {
        var g = window.graph || (typeof graph !== "undefined" ? graph : null);
        return g && typeof g.serialize === "function";
    }

    function initialization_finished() {
        return window.__pyxis_graph_initialized === true;
    }

    function sync_widgets() {
        if (typeof window.syncWidgetsToProperties === "function") {
            window.syncWidgetsToProperties();
            return;
        }
        var g = window.graph || (typeof graph !== "undefined" ? graph : null);
        if (!graph_ready() || !g || !g._nodes) return;
        g._nodes.forEach(function (node) {
            if (!node.properties) node.properties = {};
            if (node.type === "System/Previewer" || node.type === "Previewer" || (node.title && node.title.includes("Previewer"))) {
                var p = (typeof window.get_active_previewer === "function") ? window.get_active_previewer() : null;
                if (!p && window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers && node.id !== undefined) {
                    p = window.PyxisNodePlayerManager.activePlayers[String(node.id)];
                }
                if (p && p.isPinned) {
                    node.properties.is_pinned = true;
                    if (p.originalSize) {
                        node.properties.previewer_width = Math.round(p.originalSize[0]);
                        node.properties.previewer_height = Math.round(p.originalSize[1]);
                    }
                } else {
                    node.properties.is_pinned = false;
                    if (Array.isArray(node.size) && node.size[0] > 0 && node.size[1] >= 140) {
                        node.properties.previewer_width = Math.round(node.size[0]);
                        node.properties.previewer_height = Math.round(node.size[1]);
                    }
                }
                if (p && p.transformState) {
                    node.properties.viewport_zoom = p.transformState.userZoom || 1.0;
                    node.properties.viewport_pan_x = p.transformState.panX || 0;
                    node.properties.viewport_pan_y = p.transformState.panY || 0;
                    node.properties.viewport_custom = !!p.transformState.isCustom;
                }
            }
            if (!node.widgets) return;
            node.widgets.forEach(function (widget) {
                if (widget.type !== "button" && widget.property !== undefined) {
                    if (widget.value !== undefined && widget.value !== null) {
                        node.properties[widget.property] = widget.value;
                    } else if (node.properties[widget.property] !== undefined) {
                        widget.value = node.properties[widget.property];
                    }
                }
            });
        });
    }

    function graph_json() {
        if (!graph_ready()) return "";
        sync_widgets();
        try {
            var g = window.graph || (typeof graph !== "undefined" ? graph : null);
            var serialized = g ? g.serialize() : null;
            if (serialized && typeof serialized === "object") {
                if (!serialized.extra) serialized.extra = {};
                var c = window.canvas || (typeof canvas !== "undefined" ? canvas : null);
                if (c && c.ds) {
                    serialized.extra.canvas_zoom = c.ds.scale;
                    if (c.ds.offset) {
                        serialized.extra.canvas_offset = [c.ds.offset[0], c.ds.offset[1]];
                    }
                }
                if (window.__pyxis_active_template_id) {
                    serialized.extra.active_template_id = window.__pyxis_active_template_id;
                    serialized.extra.active_template_name = window.__pyxis_active_template_name || "Template";
                } else {
                    delete serialized.extra.active_template_id;
                    delete serialized.extra.active_template_name;
                }
            }
            return serialized ? JSON.stringify(serialized) : "";
        } catch (error) {
            console.error("Pyxis: failed to serialize session", error);
            return "";
        }
    }

    function save_now() {
        if (!api_ready() || !initialization_finished()) return;
        if (save_timer !== null) {
            clearTimeout(save_timer);
            save_timer = null;
        }

        var current_json = graph_json();
        if (!current_json || current_json === last_saved_json) return;

        if (save_in_flight) {
            save_again = true;
            return;
        }

        save_in_flight = true;
        window.pywebview.api.save_session(current_json).then(function (saved) {
            if (saved === true) last_saved_json = current_json;
        }).catch(function (error) {
            console.error("Pyxis: error saving session", error);
        }).finally(function () {
            save_in_flight = false;
            if (save_again) {
                save_again = false;
                schedule_save(50);
            }
        });
    }

    function schedule_save(delay) {
        if (!initialization_finished()) return;
        if (save_timer !== null) clearTimeout(save_timer);
        var timeout = (delay !== undefined) ? delay : save_delay_ms;
        save_timer = setTimeout(function () {
            save_timer = null;
            save_now();
        }, timeout);
    }

    function hook_widgets() {
        if (!graph_ready()) return;
        var g = window.graph || (typeof graph !== "undefined" ? graph : null);
        if (!g || !g._nodes) return;
        g._nodes.forEach(function (node) {
            if (!node.widgets) return;
            node.widgets.forEach(function (widget) {
                if (widget.__pyxis_persistence_hooked) return;
                var old_callback = widget.callback;
                widget.callback = function (value) {
                    if (old_callback) old_callback.apply(this, arguments);
                    schedule_save(50);
                    if (typeof window.updateTemplateUIState === "function") {
                        setTimeout(window.updateTemplateUIState, 50);
                    }
                };
                widget.__pyxis_persistence_hooked = true;
            });
        });
    }

    function on_graph_mutation() {
        hook_widgets();
        schedule_save(50);
        if (typeof window.updateTemplateUIState === "function") {
            setTimeout(window.updateTemplateUIState, 50);
        }
    }

    function start() {
        if (started || !api_ready() || !initialization_finished()) return;
        var g = window.graph || (typeof graph !== "undefined" ? graph : null);
        if (!g) return;
        started = true;

        var old_on_change = g.on_change;
        g.on_change = function () {
            if (old_on_change) old_on_change.apply(this, arguments);
            on_graph_mutation();
        };

        var old_onConnectionChange = g.onConnectionChange;
        g.onConnectionChange = function () {
            if (old_onConnectionChange) old_onConnectionChange.apply(this, arguments);
            on_graph_mutation();
        };

        var old_onNodeConnectionChange = g.onNodeConnectionChange;
        g.onNodeConnectionChange = function () {
            if (old_onNodeConnectionChange) old_onNodeConnectionChange.apply(this, arguments);
            on_graph_mutation();
        };

        var old_onNodeAdded = g.onNodeAdded;
        g.onNodeAdded = function () {
            if (old_onNodeAdded) old_onNodeAdded.apply(this, arguments);
            on_graph_mutation();
        };

        var old_onNodeRemoved = g.onNodeRemoved;
        g.onNodeRemoved = function () {
            if (old_onNodeRemoved) old_onNodeRemoved.apply(this, arguments);
            on_graph_mutation();
        };

        var old_afterChange = g.afterChange;
        g.afterChange = function () {
            if (old_afterChange) old_afterChange.apply(this, arguments);
            on_graph_mutation();
        };

        hook_widgets();
        last_saved_json = graph_json();

        window.addEventListener("beforeunload", save_now);
        window.addEventListener("pagehide", save_now);
        window.addEventListener("visibilitychange", function () {
            if (document.visibilityState === "hidden") save_now();
        });
        window.addEventListener("blur", save_now);

        var c = window.canvas || (typeof canvas !== "undefined" ? canvas : null);
        if (c && c.canvas) {
            c.canvas.addEventListener("mouseup", function () {
                schedule_save(100);
                if (typeof window.updateTemplateUIState === "function") {
                    setTimeout(window.updateTemplateUIState, 50);
                }
            });
            c.canvas.addEventListener("touchend", function () {
                schedule_save(100);
                if (typeof window.updateTemplateUIState === "function") {
                    setTimeout(window.updateTemplateUIState, 50);
                }
            });
        }
        if (c && c.ds) {
            var oldOnRedraw = c.ds.onredraw;
            c.ds.onredraw = function () {
                if (oldOnRedraw) oldOnRedraw.apply(this, arguments);
                schedule_save(150);
            };
        }
    }

    function wait_until_ready() {
        if (api_ready() && graph_ready() && initialization_finished()) {
            start();
        } else {
            setTimeout(wait_until_ready, 50);
        }
    }

    window.__pyxis_save_session_now = save_now;
    window.__pyxis_schedule_save = schedule_save;

    window.addEventListener("pywebviewready", wait_until_ready);
    wait_until_ready();
}());