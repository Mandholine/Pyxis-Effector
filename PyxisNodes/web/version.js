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
 * @file version.js
 * @description Frontend Single Source of Truth (SSOT) for Pyxis Effector version state.
 * Synchronously initialises canonical version identifiers onto the global window object
 * for canvas rendering, standalone browser preview, and dynamic DOM badge injection.
 * @module PyxisVersion
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

(function (window) {
    "use strict";

    window.PYXIS_VERSION = "1.1.5";
    window.PYXIS_STAGE = "Beta";
    window.PYXIS_STAGE_SHORT = "beta";
    window.PYXIS_VERSION_STRING = "v" + window.PYXIS_VERSION;
    window.PYXIS_FULL_VERSION = window.PYXIS_STAGE + " " + window.PYXIS_VERSION_STRING;
})(typeof window !== "undefined" ? window : globalThis);
