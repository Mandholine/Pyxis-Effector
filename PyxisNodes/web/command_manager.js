/**
 * Pyxis Effector — Command Pattern Undo/Redo & State Management System
 * Version 1.0.0
 * 
 * Implements a granular, non-destructive Command Pattern stack for LiteGraph.
 * Eliminates full-graph JSON serialization thrashing, preserves in-node WebAssembly
 * players and Ace Editors, guarantees O(1) dirty-state checks, and prevents camera
 * navigation from ever contaminating the undo history.
 */

(function (global) {
    "use strict";

    /**
     * Abstract base class for all undoable commands.
     */
    class PyxisCommand {
        constructor(description = "Action") {
            this.description = description;
            this.timestamp = Date.now();
        }

        execute() {
            throw new Error("execute() must be implemented by subclass");
        }

        undo() {
            throw new Error("undo() must be implemented by subclass");
        }

        canMergeWith(otherCommand) {
            return false;
        }

        mergeWith(otherCommand) {
            return false;
        }
    }

    /**
     * Command for moving one or multiple nodes.
     */
    class MoveNodesCommand extends PyxisCommand {
        /**
         * @param {Array<{id: number|string, from: [number, number], to: [number, number]}>} moves
         * @param {string} description
         */
        constructor(moves, description) {
            super(description || "Move Nodes");
            this.moves = Array.isArray(moves) ? moves : [];
        }

        execute() {
            if (!global.graph) return;
            this.moves.forEach(m => {
                const node = global.graph.getNodeById(m.id);
                if (node && Array.isArray(m.to)) {
                    node.pos[0] = m.to[0];
                    node.pos[1] = m.to[1];
                    if (typeof node.setDirtyCanvas === "function") {
                        node.setDirtyCanvas(true, true);
                    }
                }
            });
            if (global.canvas) global.canvas.setDirty(true, true);
        }

        undo() {
            if (!global.graph) return;
            this.moves.forEach(m => {
                const node = global.graph.getNodeById(m.id);
                if (node && Array.isArray(m.from)) {
                    node.pos[0] = m.from[0];
                    node.pos[1] = m.from[1];
                    if (typeof node.setDirtyCanvas === "function") {
                        node.setDirtyCanvas(true, true);
                    }
                }
            });
            if (global.canvas) global.canvas.setDirty(true, true);
        }

        canMergeWith(other) {
            if (!(other instanceof MoveNodesCommand)) return false;
            if (other.timestamp - this.timestamp > 800) return false;
            if (this.moves.length !== other.moves.length) return false;
            const thisIds = this.moves.map(m => m.id).sort().join(",");
            const otherIds = other.moves.map(m => m.id).sort().join(",");
            return thisIds === otherIds;
        }

        mergeWith(other) {
            if (!this.canMergeWith(other)) return false;
            // Keep original 'from' positions, update 'to' positions from the latest command
            const otherMap = {};
            other.moves.forEach(m => { otherMap[m.id] = m.to; });
            this.moves.forEach(m => {
                if (otherMap[m.id]) {
                    m.to = otherMap[m.id];
                }
            });
            this.timestamp = other.timestamp;
            return true;
        }
    }

    /**
     * Command for updating a node property.
     */
    class SetPropertyCommand extends PyxisCommand {
        /**
         * @param {number|string} nodeId
         * @param {string} propName
         * @param {*} oldValue
         * @param {*} newValue
         * @param {string} description
         */
        constructor(nodeId, propName, oldValue, newValue, description) {
            super(description || `Change ${propName}`);
            this.nodeId = nodeId;
            this.propName = propName;
            this.oldValue = oldValue;
            this.newValue = newValue;
        }

        _applyValue(val) {
            if (!global.graph) return;
            const node = global.graph.getNodeById(this.nodeId);
            if (!node) return;

            if (!node.properties) node.properties = {};
            node.properties[this.propName] = val;

            // Synchronize corresponding widget if linked
            if (Array.isArray(node.widgets)) {
                node.widgets.forEach(w => {
                    if (w && (w.name === this.propName || (w.options && w.options.property === this.propName))) {
                        w.value = val;
                    }
                });
            }

            if (typeof node.onPropertyChanged === "function") {
                try {
                    node.onPropertyChanged(this.propName, val, val === this.newValue ? this.oldValue : this.newValue);
                } catch (e) {
                    console.warn("[Pyxis SetPropertyCommand onPropertyChanged warning]", e);
                }
            }

            if (typeof node.setDirtyCanvas === "function") {
                node.setDirtyCanvas(true, true);
            }
            if (global.canvas) global.canvas.setDirty(true, true);
        }

        execute() {
            this._applyValue(this.newValue);
        }

        undo() {
            this._applyValue(this.oldValue);
        }

        canMergeWith(other) {
            if (!(other instanceof SetPropertyCommand)) return false;
            if (this.nodeId !== other.nodeId || this.propName !== other.propName) return false;
            // Merge rapid text inputs within 600ms
            return (other.timestamp - this.timestamp < 600);
        }

        mergeWith(other) {
            if (!this.canMergeWith(other)) return false;
            this.newValue = other.newValue;
            this.timestamp = other.timestamp;
            return true;
        }
    }

    /**
     * Command for connecting two node slots.
     */
    class ConnectLinkCommand extends PyxisCommand {
        constructor(originId, originSlot, targetId, targetSlot, linkId, description) {
            super(description || "Connect Cable");
            this.originId = originId;
            this.originSlot = originSlot;
            this.targetId = targetId;
            this.targetSlot = targetSlot;
            this.linkId = linkId || null;
        }

        execute() {
            if (!global.graph) return;
            const originNode = global.graph.getNodeById(this.originId);
            if (!originNode) return;

            // Connect using LiteGraph's native method
            originNode.connect(this.originSlot, this.targetId, this.targetSlot);
            if (global.canvas) global.canvas.setDirty(true, true);
        }

        undo() {
            if (!global.graph) return;
            const targetNode = global.graph.getNodeById(this.targetId);
            if (!targetNode) return;

            // Disconnect input slot
            if (typeof targetNode.disconnectInput === "function") {
                targetNode.disconnectInput(this.targetSlot);
            }
            if (global.canvas) global.canvas.setDirty(true, true);
        }
    }

    /**
     * Command for disconnecting a link.
     */
    class DisconnectLinkCommand extends PyxisCommand {
        constructor(originId, originSlot, targetId, targetSlot, linkId, description) {
            super(description || "Disconnect Cable");
            this.originId = originId;
            this.originSlot = originSlot;
            this.targetId = targetId;
            this.targetSlot = targetSlot;
            this.linkId = linkId || null;
        }

        execute() {
            if (!global.graph) return;
            const targetNode = global.graph.getNodeById(this.targetId);
            if (targetNode && typeof targetNode.disconnectInput === "function") {
                targetNode.disconnectInput(this.targetSlot);
            }
            if (global.canvas) global.canvas.setDirty(true, true);
        }

        undo() {
            if (!global.graph) return;
            const originNode = global.graph.getNodeById(this.originId);
            if (originNode) {
                originNode.connect(this.originSlot, this.targetId, this.targetSlot);
            }
            if (global.canvas) global.canvas.setDirty(true, true);
        }
    }

    /**
     * Command for adding a node to the graph.
     */
    class AddNodeCommand extends PyxisCommand {
        constructor(nodeOrSerialized, description) {
            super(description || "Add Node");
            if (nodeOrSerialized && typeof nodeOrSerialized.serialize === "function") {
                this.nodeData = nodeOrSerialized.serialize();
                this.nodeInstance = nodeOrSerialized;
                this.nodeId = nodeOrSerialized.id;
            } else {
                this.nodeData = nodeOrSerialized;
                this.nodeInstance = null;
                this.nodeId = nodeOrSerialized ? nodeOrSerialized.id : null;
            }
        }

        execute() {
            if (!global.graph || !this.nodeData) return;
            let node = global.graph.getNodeById(this.nodeId);
            if (!node) {
                if (this.nodeInstance && !this.nodeInstance.graph) {
                    node = this.nodeInstance;
                } else if (global.LiteGraph && typeof global.LiteGraph.createNode === "function") {
                    node = global.LiteGraph.createNode(this.nodeData.type);
                    if (node) {
                        node.configure(this.nodeData);
                    }
                }
                if (node) {
                    node.id = this.nodeId;
                    global.graph.add(node, true);
                    this.nodeInstance = node;
                }
            }
            if (global.canvas) global.canvas.setDirty(true, true);
        }

        undo() {
            if (!global.graph || !this.nodeId) return;
            const node = global.graph.getNodeById(this.nodeId);
            if (node) {
                this.nodeInstance = node;
                global.graph.remove(node);
            }
            if (global.canvas) global.canvas.setDirty(true, true);
        }
    }

    /**
     * Command for removing one or multiple nodes with all their connected links.
     */
    class RemoveNodesCommand extends PyxisCommand {
        constructor(nodes, description) {
            super(description || "Remove Node(s)");
            const targetNodes = Array.isArray(nodes) ? nodes : [nodes];
            this.savedData = [];

            if (global.graph) {
                targetNodes.forEach(n => {
                    if (!n) return;
                    const links = [];
                    // Collect connected links before removal
                    if (Array.isArray(n.inputs)) {
                        n.inputs.forEach((inp, slot) => {
                            if (inp && inp.link !== null && inp.link !== undefined) {
                                const l = global.graph.links[inp.link];
                                if (l) {
                                    links.push({
                                        originId: l.origin_id,
                                        originSlot: l.origin_slot,
                                        targetId: n.id,
                                        targetSlot: slot,
                                        linkId: l.id
                                    });
                                }
                            }
                        });
                    }
                    if (Array.isArray(n.outputs)) {
                        n.outputs.forEach((out, slot) => {
                            if (out && Array.isArray(out.links)) {
                                out.links.forEach(lId => {
                                    const l = global.graph.links[lId];
                                    if (l) {
                                        links.push({
                                            originId: n.id,
                                            originSlot: slot,
                                            targetId: l.target_id,
                                            targetSlot: l.target_slot,
                                            linkId: l.id
                                        });
                                    }
                                });
                            }
                        });
                    }
                    this.savedData.push({
                        serialized: n.serialize(),
                        instance: n,
                        links: links
                    });
                });
            }
        }

        execute() {
            if (!global.graph) return;
            this.savedData.forEach(item => {
                const node = global.graph.getNodeById(item.serialized.id);
                if (node) {
                    item.instance = node;
                    global.graph.remove(node);
                }
            });
            if (global.canvas) global.canvas.setDirty(true, true);
        }

        undo() {
            if (!global.graph) return;
            // 1. Restore node instances
            this.savedData.forEach(item => {
                let node = global.graph.getNodeById(item.serialized.id);
                if (!node) {
                    if (item.instance && !item.instance.graph) {
                        node = item.instance;
                    } else if (global.LiteGraph && typeof global.LiteGraph.createNode === "function") {
                        node = global.LiteGraph.createNode(item.serialized.type);
                        if (node) {
                            node.configure(item.serialized);
                        }
                    }
                    if (node) {
                        node.id = item.serialized.id;
                        global.graph.add(node, true);
                        item.instance = node;
                    }
                }
            });

            // 2. Restore links
            this.savedData.forEach(item => {
                item.links.forEach(linkInfo => {
                    const origin = global.graph.getNodeById(linkInfo.originId);
                    const target = global.graph.getNodeById(linkInfo.targetId);
                    if (origin && target) {
                        origin.connect(linkInfo.originSlot, target, linkInfo.targetSlot);
                    }
                });
            });

            if (global.canvas) global.canvas.setDirty(true, true);
        }
    }

    /**
     * Composite command for atomic multi-action transactions (e.g. paste, mode switch).
     */
    class CompositeCommand extends PyxisCommand {
        constructor(commands, description) {
            super(description || "Composite Action");
            this.commands = Array.isArray(commands) ? commands : [];
        }

        add(cmd) {
            if (cmd) this.commands.push(cmd);
        }

        execute() {
            for (let i = 0; i < this.commands.length; i++) {
                this.commands[i].execute();
            }
        }

        undo() {
            // Undo in reverse order
            for (let i = this.commands.length - 1; i >= 0; i--) {
                this.commands[i].undo();
            }
        }
    }

    /**
     * Fallback command for legacy full-graph snapshots.
     */
    class FallbackSnapshotCommand extends PyxisCommand {
        constructor(beforeSnap, afterSnap, description) {
            super(description || "Graph Snapshot");
            this.beforeSnap = beforeSnap;
            this.afterSnap = afterSnap;
        }

        execute() {
            if (!global.graph || !this.afterSnap) return;
            try {
                const parsed = JSON.parse(this.afterSnap);
                if (global.canvas && typeof global.canvas.deselectAllNodes === "function") {
                    global.canvas.deselectAllNodes();
                }
                global.graph.configure(parsed);
                if (typeof global.syncWidgetsToProperties === "function") {
                    global.syncWidgetsToProperties();
                }
                if (global.canvas) global.canvas.setDirty(true, true);
            } catch (e) {
                console.error("[Pyxis FallbackSnapshotCommand execute error]", e);
            }
        }

        undo() {
            if (!global.graph || !this.beforeSnap) return;
            try {
                const parsed = JSON.parse(this.beforeSnap);
                if (global.canvas && typeof global.canvas.deselectAllNodes === "function") {
                    global.canvas.deselectAllNodes();
                }
                global.graph.configure(parsed);
                if (typeof global.syncWidgetsToProperties === "function") {
                    global.syncWidgetsToProperties();
                }
                if (global.canvas) global.canvas.setDirty(true, true);
            } catch (e) {
                console.error("[Pyxis FallbackSnapshotCommand undo error]", e);
            }
        }
    }

    /**
     * Strips volatile viewport camera parameters to maintain canonical determinism.
     */
    function canonicalize(obj) {
        if (obj === null || typeof obj !== "object") {
            return obj;
        }
        if (Array.isArray(obj)) {
            return obj.map(canonicalize);
        }
        const sortedKeys = Object.keys(obj).sort();
        const result = {};
        for (let i = 0; i < sortedKeys.length; i++) {
            const key = sortedKeys[i];
            if (key === "viewport_zoom" || key === "viewport_pan_x" || key === "viewport_pan_y" || key === "viewport_custom") {
                continue;
            }
            result[key] = canonicalize(obj[key]);
        }
        return result;
    }

    /**
     * Serializes current graph without camera pan/zoom values.
     */
    function getSafeSnapshot() {
        if (!global.graph || typeof global.graph.serialize !== "function") return null;
        if (typeof global.syncWidgetsToProperties === "function") {
            global.syncWidgetsToProperties();
        }
        try {
            const raw = global.graph.serialize();
            if (raw && raw.extra) {
                delete raw.extra.canvas_zoom;
                delete raw.extra.canvas_offset;
            }
            return JSON.stringify(canonicalize(raw));
        } catch (e) {
            console.warn("[Pyxis getSafeSnapshot warning]", e);
            return null;
        }
    }

    /**
     * Master Command Stack and State Manager.
     */
    class PyxisCommandManager {
        constructor() {
            this.undoStack = [];
            this.redoStack = [];
            this.savedCheckpoint = 0;
            this.maxSteps = this._loadMaxSteps();
            this.isExecutingCommand = false;
            this.activeTransaction = null;
            this._listeners = new Set();
            this._lastSnapshot = null;
            this._batchTimer = null;
            this._batchReason = "coalesced";
        }

        _loadMaxSteps() {
            try {
                const stored = localStorage.getItem("pyxis_undo_max_steps");
                if (stored) {
                    const parsed = parseInt(stored, 10);
                    if (!isNaN(parsed) && parsed >= 5 && parsed <= 200) {
                        return parsed;
                    }
                }
            } catch (e) {}
            return 40;
        }

        getMaxSteps() {
            return this.maxSteps;
        }

        setMaxSteps(val) {
            const num = Math.min(Math.max(parseInt(val, 10) || 40, 5), 200);
            this.maxSteps = num;
            try {
                localStorage.setItem("pyxis_undo_max_steps", num);
            } catch (e) {}
            this._enforceLimit();
            this._notifyStateChanged();
            return num;
        }

        _enforceLimit() {
            while (this.undoStack.length > this.maxSteps) {
                this.undoStack.shift();
                this.savedCheckpoint--;
            }
        }

        isExecuting() {
            return Boolean(this.isExecutingCommand || global.__pyxis_is_restoring_state);
        }

        canUndo() {
            return this.undoStack.length > 0 && !this.isExecuting();
        }

        canRedo() {
            return this.redoStack.length > 0 && !this.isExecuting();
        }

        /**
         * Begins a composite transaction (all subsequent pushed commands are bundled together).
         * @param {string} description
         */
        beginTransaction(description = "Transaction") {
            if (this.activeTransaction) {
                return; // nested transactions flatten into the active one
            }
            this.activeTransaction = new CompositeCommand([], description);
        }

        /**
         * Commits the active transaction and pushes it to the undo stack.
         */
        commitTransaction() {
            if (!this.activeTransaction) return;
            const txn = this.activeTransaction;
            this.activeTransaction = null;
            if (txn.commands.length > 0) {
                this.pushCommand(txn, false); // already executed in-place
            }
        }

        /**
         * Cancels and rolls back the active uncommitted transaction.
         */
        rollbackTransaction() {
            if (!this.activeTransaction) return;
            const txn = this.activeTransaction;
            this.activeTransaction = null;
            txn.undo();
            this._notifyStateChanged();
        }

        /**
         * Executes and pushes a command onto the undo stack.
         * @param {PyxisCommand} command
         * @param {boolean} executeImmediately Whether to invoke command.execute()
         */
        pushCommand(command, executeImmediately = true) {
            if (!command) return;
            if (this.isExecutingCommand || global.__pyxis_is_restoring_state || global.__pyxis_is_loading_template) {
                return;
            }

            if (this.activeTransaction) {
                if (executeImmediately) {
                    this.isExecutingCommand = true;
                    try { command.execute(); } finally { this.isExecutingCommand = false; }
                }
                this.activeTransaction.add(command);
                return;
            }

            // Attempt micro-merging with previous command (e.g. rapid typing in input or node dragging)
            if (this.undoStack.length > 0) {
                const top = this.undoStack[this.undoStack.length - 1];
                if (top.canMergeWith(command)) {
                    top.mergeWith(command);
                    if (executeImmediately) {
                        this.isExecutingCommand = true;
                        try { command.execute(); } finally { this.isExecutingCommand = false; }
                    }
                    this._notifyStateChanged();
                    return;
                }
            }

            if (executeImmediately) {
                this.isExecutingCommand = true;
                try {
                    command.execute();
                } catch (err) {
                    console.error("[PyxisCommandManager execute error]", err);
                    return;
                } finally {
                    this.isExecutingCommand = false;
                }
            }

            this.undoStack.push(command);
            this.redoStack.length = 0; // Clear redo history on new action
            this._enforceLimit();
            this._notifyStateChanged();
        }

        /**
         * Standard Command Pattern execute method.
         * @param {PyxisCommand} command
         * @param {boolean} skipExecute If true, command was already executed in-place.
         */
        execute(command, skipExecute = false) {
            this.pushCommand(command, !skipExecute);
        }

        undo() {
            if (!this.canUndo()) return;
            if (typeof global.closeAllActiveNodeEditors === "function") {
                try { global.closeAllActiveNodeEditors(false); } catch (e) {}
            }

            const cmd = this.undoStack.pop();
            this.isExecutingCommand = true;
            global.__pyxis_is_restoring_state = true;

            try {
                cmd.undo();
                this.redoStack.push(cmd);
                if (global.PyxisNodePlayerManager && typeof global.PyxisNodePlayerManager.updateInNodePlayersPosition === "function") {
                    global.PyxisNodePlayerManager.updateInNodePlayersPosition();
                }
                console.log(`%c[Pyxis Undo]%c Deshecho evento: "${cmd.description}" (Paso ${this.undoStack.length} de ${this.undoStack.length + this.redoStack.length})`, "color: #38bdf8; font-weight: bold;", "color: inherit;");
                if (typeof global.showPyxisToast === "function") {
                    global.showPyxisToast("toast.undone", "success");
                }
            } catch (err) {
                console.error("[PyxisCommandManager undo error]", err);
            } finally {
                setTimeout(() => {
                    this.isExecutingCommand = false;
                    global.__pyxis_is_restoring_state = false;
                    this._notifyStateChanged();
                }, 50);
                this._notifyStateChanged();
            }
        }

        redo() {
            if (!this.canRedo()) return;
            if (typeof global.closeAllActiveNodeEditors === "function") {
                try { global.closeAllActiveNodeEditors(false); } catch (e) {}
            }

            const cmd = this.redoStack.pop();
            this.isExecutingCommand = true;
            global.__pyxis_is_restoring_state = true;

            try {
                cmd.execute();
                this.undoStack.push(cmd);
                if (global.PyxisNodePlayerManager && typeof global.PyxisNodePlayerManager.updateInNodePlayersPosition === "function") {
                    global.PyxisNodePlayerManager.updateInNodePlayersPosition();
                }
                console.log(`%c[Pyxis Redo]%c Rehecho evento: "${cmd.description}" (Paso ${this.undoStack.length} de ${this.undoStack.length + this.redoStack.length})`, "color: #a855f7; font-weight: bold;", "color: inherit;");
                if (typeof global.showPyxisToast === "function") {
                    global.showPyxisToast("toast.redone", "success");
                }
            } catch (err) {
                console.error("[PyxisCommandManager redo error]", err);
            } finally {
                setTimeout(() => {
                    this.isExecutingCommand = false;
                    global.__pyxis_is_restoring_state = false;
                    this._notifyStateChanged();
                }, 50);
                this._notifyStateChanged();
            }
        }

        /**
         * Checks in O(1) if there are unsaved changes relative to the saved template checkpoint.
         * @returns {boolean}
         */
        hasUnsavedChanges() {
            if (this.undoStack.length !== this.savedCheckpoint) {
                return true;
            }
            if (global.__pyxis_active_template_id && global.__pyxis_template_checkpoint && typeof global.get_graph_content_signature === "function" && global.graph) {
                try {
                    return global.get_graph_content_signature(global.graph) !== global.__pyxis_template_checkpoint;
                } catch (e) {}
            }
            return false;
        }

        /**
         * Marks current stack position as the saved checkpoint (e.g. after template quick save).
         */
        markSavedCheckpoint() {
            this.savedCheckpoint = this.undoStack.length;
            this._notifyStateChanged();
        }

        /**
         * Resets the entire stack to a fresh state (e.g. on new template load).
         */
        clear() {
            this.undoStack.length = 0;
            this.redoStack.length = 0;
            this.savedCheckpoint = 0;
            this.activeTransaction = null;
            this._lastSnapshot = getSafeSnapshot();
            if (this._batchTimer) {
                clearTimeout(this._batchTimer);
                this._batchTimer = null;
            }
            this._notifyStateChanged();
        }

        initInitialState() {
            this.clear();
        }

        addListener(fn) {
            if (typeof fn === "function") this._listeners.add(fn);
        }

        removeListener(fn) {
            this._listeners.delete(fn);
        }

        _notifyStateChanged() {
            // 1. Update toolbar buttons
            const btnUndo = document.getElementById("btn-tb-undo");
            const btnRedo = document.getElementById("btn-tb-redo");
            if (btnUndo) {
                btnUndo.disabled = !this.canUndo();
                if (this.canUndo()) btnUndo.classList.remove("disabled");
                else btnUndo.classList.add("disabled");
            }
            if (btnRedo) {
                btnRedo.disabled = !this.canRedo();
                if (this.canRedo()) btnRedo.classList.remove("disabled");
                else btnRedo.classList.add("disabled");
            }

            // 2. Synchronize "Save Changes" button instantaneously
            if (typeof global.updateTemplateUIState === "function") {
                global.updateTemplateUIState();
            } else {
                const hasChanges = this.hasUnsavedChanges();
                const btnSave = document.getElementById("btn-quick-save-template");
                if (btnSave) {
                    const activeId = global.__pyxis_active_template_id;
                    const activeName = global.__pyxis_active_template_name;
                    if (activeId && activeName && hasChanges) {
                        btnSave.style.display = "inline-flex";
                        btnSave.setAttribute("data-tooltip", `Save changes in "${activeName}" (1 click)`);
                    } else {
                        btnSave.style.display = "none";
                    }
                }
            }

            // 3. Notify external listeners
            this._listeners.forEach(fn => {
                try { fn(this); } catch (e) {}
            });
        }

        // --- Backward Compatibility Bridge for PyxisUndoManager ---

        recordPropertyChange(node, propName, oldValue, newValue, desc) {
            if (oldValue === newValue) return;
            const cmd = new SetPropertyCommand(
                typeof node === "object" ? node.id : node,
                propName,
                oldValue,
                newValue,
                desc || `Change ${propName}`
            );
            this.pushCommand(cmd, true);
        }

        recordState(reason = "user-action") {
            if (this.isExecuting() || global.__pyxis_is_loading_template || global.__pyxis_is_preview_or_hardsub_running || !global.graph) return;
            const currentSnap = getSafeSnapshot();
            if (!currentSnap) return;

            if (this._lastSnapshot === null) {
                this._lastSnapshot = currentSnap;
                return;
            }

            if (this._lastSnapshot === currentSnap) {
                this._notifyStateChanged();
                return;
            }

            const prevSnap = this._lastSnapshot;
            this._lastSnapshot = currentSnap;

            const cmd = new FallbackSnapshotCommand(prevSnap, currentSnap, reason || "user-action");
            this.pushCommand(cmd, false);
        }

        scheduleRecordState(delayMs = 120, reason = "coalesced") {
            if (this.isExecuting() || global.__pyxis_is_loading_template || global.__pyxis_is_preview_or_hardsub_running) return;
            if (this._batchTimer) clearTimeout(this._batchTimer);
            this._batchReason = reason;
            this._batchTimer = setTimeout(() => {
                this._batchTimer = null;
                this.recordState(this._batchReason || "coalesced");
            }, delayMs);
        }

        flushPendingState() {
            if (this._batchTimer) {
                clearTimeout(this._batchTimer);
                this._batchTimer = null;
                this.recordState(this._batchReason || "coalesced");
            }
        }

        pushSnapshot(overrideSnap, reason = "manual-snapshot") {
            if (overrideSnap) {
                const prevSnap = this._lastSnapshot || overrideSnap;
                this._lastSnapshot = overrideSnap;
                const cmd = new FallbackSnapshotCommand(prevSnap, overrideSnap, reason);
                this.pushCommand(cmd, false);
            } else {
                this.recordState(reason);
            }
        }

        captureBeforeState() {
            this._lastSnapshot = getSafeSnapshot();
        }

        getHistoryLength() {
            return this.undoStack.length;
        }

        getPointer() {
            return this.undoStack.length - 1;
        }

        getHistoryReasons() {
            return this.undoStack.map(cmd => cmd.description);
        }

        updateUI() {
            this._notifyStateChanged();
        }
    }

    // Export classes, functions, and singleton instance
    global.PyxisCommand = PyxisCommand;
    global.MoveNodesCommand = MoveNodesCommand;
    global.SetPropertyCommand = SetPropertyCommand;
    global.ConnectLinkCommand = ConnectLinkCommand;
    global.DisconnectLinkCommand = DisconnectLinkCommand;
    global.AddNodeCommand = AddNodeCommand;
    global.RemoveNodesCommand = RemoveNodesCommand;
    global.CompositeCommand = CompositeCommand;
    global.FallbackSnapshotCommand = FallbackSnapshotCommand;
    global.PyxisCommandManager = PyxisCommandManager;
    global.canonicalize = canonicalize;
    global.getSafeSnapshot = getSafeSnapshot;

    global.pyxisCommandManager = new PyxisCommandManager();
    // Expose as global singleton
    global.PyxisUndoManager = global.pyxisCommandManager;

})(typeof window !== "undefined" ? window : this);
