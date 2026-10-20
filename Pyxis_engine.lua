-- Pyxis Effector - Plugin for Aegisub
-- Copyright (C) 2026 @mandholine, @effector2, @pholguinc
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation version 3.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program. If not, see <https://www.gnu.org/licenses/>.
-- For any question you can visit: https://discord.gg/fsxRESeQZN

script_name        = "Pyxis Node Engine"
script_description = "Visual Node-Based Karaoke Automation"
script_author      = "Pyxis Dev Team"
script_version     = "1.1.5"
script_namespace   = "pyxis.NodeEngine"

local ffi = require("ffi")
local unicode = require("aegisub.unicode")

-- [INSTANCE IDENTITY]
-- Generated ONCE when script loads (or on automation rescan).
-- Ensures that if the user has multiple Aegisub instances open simultaneously,
-- each uses its own set of temporary files without collision.
math.randomseed(os.time() + (tonumber(tostring({}):match("0x(%x+)") or "0", 16) or 0) % 1000000)
local instance_id = tostring(os.time()) .. "_" .. tostring(math.random(100000, 999999))

-- [SESSION CONTINUITY FOR THIS INSTANCE]
-- Lives only in memory of this Aegisub process: automatically resets
-- when closing Aegisub or reloading/rescanning automations.
local last_Pyxis_session = nil
local last_sub_state_hash = nil

-- [SAFE KARASKEL LOADING]
local karaskel = nil
local ok_kara, kara_mod = pcall(require, "karaskel-auto4")
if ok_kara and type(kara_mod) == "table" then
    karaskel = kara_mod
else
    pcall(dofile, "karaskel.lua")
    karaskel = _G.karaskel
end

ffi.cdef[[
    void Sleep(int dwMilliseconds);
    int ShellExecuteA(void* hwnd, const char* lpOperation, const char* lpFile, const char* lpParameters, const char* lpDirectory, int nShowCmd);
    uint32_t GetCurrentProcessId(void);
    bool AllowSetForegroundWindow(uint32_t dwProcessId);
    bool CreateDirectoryA(const char* lpPathName, void* lpSecurityAttributes);

    void* InternetOpenA(const char* lpszAgent, uint32_t dwAccessType, const char* lpszProxy, const char* lpszProxyBypass, uint32_t dwFlags);
    void* InternetConnectA(void* hInternet, const char* lpszServerName, uint16_t nServerPort, const char* lpszUsername, const char* lpszPassword, uint32_t dwService, uint32_t dwFlags, uintptr_t dwContext);
    void* HttpOpenRequestA(void* hConnect, const char* lpszVerb, const char* lpszObjectName, const char* lpszVersion, const char* lpszReferrer, const char** lplpszAcceptTypes, uint32_t dwFlags, uintptr_t dwContext);
    bool HttpSendRequestA(void* hRequest, const char* lpszHeaders, uint32_t dwHeadersLength, void* lpOptional, uint32_t dwOptionalLength);
    bool InternetReadFile(void* hFile, void* lpBuffer, uint32_t dwNumberOfBytesToRead, uint32_t* lpdwNumberOfBytesRead);
    bool InternetCloseHandle(void* hInternet);
]]
local kernel32 = ffi.load("kernel32")
local shell32 = ffi.load("shell32")
local user32 = nil
pcall(function() user32 = ffi.load("user32") end)
local wininet = nil
pcall(function() wininet = ffi.load("wininet") end)

local function ping_and_reopen_daemon(payload_json)
    if not wininet then return false end
    local hInternet = wininet.InternetOpenA("PyxisLuaClient", 1, nil, nil, 0)
    if not hInternet or hInternet == ffi.cast("void*", 0) then return false end

    local hConnect = wininet.InternetConnectA(hInternet, "127.0.0.1", 28723, nil, nil, 3, 0, 0)
    if not hConnect or hConnect == ffi.cast("void*", 0) then
        wininet.InternetCloseHandle(hInternet)
        return false
    end

    local hRequest = wininet.HttpOpenRequestA(hConnect, "POST", "/reopen", nil, nil, nil, 0x80000000, 0)
    if not hRequest or hRequest == ffi.cast("void*", 0) then
        wininet.InternetCloseHandle(hConnect)
        wininet.InternetCloseHandle(hInternet)
        return false
    end

    local headers = "Content-Type: application/json\r\n"
    local res = wininet.HttpSendRequestA(hRequest, headers, #headers, ffi.cast("void*", payload_json), #payload_json)
    local reopened = false
    if res then
        local buf = ffi.new("char[512]")
        local bytes_read = ffi.new("uint32_t[1]")
        if wininet.InternetReadFile(hRequest, buf, 512, bytes_read) and bytes_read[0] > 0 then
            local str_resp = ffi.string(buf, bytes_read[0])
            if str_resp:match("reopened") then
                reopened = true
            end
        end
    end

    wininet.InternetCloseHandle(hRequest)
    wininet.InternetCloseHandle(hConnect)
    wininet.InternetCloseHandle(hInternet)

    return reopened
end

local function path_sep()
    return package.config:sub(1,1)
end

local function join_path(a, b)
    local sep = path_sep()
    if a:sub(-1) == sep then
        return a .. b
    end
    return a .. sep .. b
end

local function ensure_dir(path)
    if not path or path == "" then return end
    if kernel32 and kernel32.CreateDirectoryA then
        local current = ""
        for part in path:gmatch("[^\\/]+") do
            if current == "" and (path:sub(2,2) == ":" or path:sub(1,2) == "\\\\") then
                current = part
            else
                current = (current == "" and part) or (current .. "\\" .. part)
                kernel32.CreateDirectoryA(current, nil)
            end
        end
    else
        pcall(function()
            local lfs = require("lfs")
            if lfs and lfs.mkdir then lfs.mkdir(path) end
        end)
    end
end

local function fast_parse_time(t_val)
    if not t_val then return 0 end
    local num = tonumber(t_val)
    if num then return num end
    local c1 = t_val:find(":", 1, true)
    if not c1 then return 0 end
    local c2 = t_val:find(":", c1 + 1, true)
    if not c2 then return 0 end
    local dot = t_val:find(".", c2 + 1, true)
    if not dot then return 0 end
    local h = tonumber(t_val:sub(1, c1 - 1)) or 0
    local m = tonumber(t_val:sub(c1 + 1, c2 - 1)) or 0
    local s = tonumber(t_val:sub(c2 + 1, dot - 1)) or 0
    local cs = tonumber(t_val:sub(dot + 1)) or 0
    return (h * 3600 + m * 60 + s) * 1000 + cs * 10
end
local parse_time = fast_parse_time

local function fast_parse_dialogue_line(line_str)
    local prefix_len = 0
    if line_str:sub(1, 10) == "Dialogue: " then
        prefix_len = 10
    elseif line_str:sub(1, 9) == "Dialogue:" then
        prefix_len = 9
    else
        return nil
    end

    local p1 = line_str:find(",", prefix_len + 1, true)
    if not p1 then return nil end
    local p2 = line_str:find(",", p1 + 1, true)
    if not p2 then return nil end
    local p3 = line_str:find(",", p2 + 1, true)
    if not p3 then return nil end
    local p4 = line_str:find(",", p3 + 1, true)
    if not p4 then return nil end
    local p5 = line_str:find(",", p4 + 1, true)
    if not p5 then return nil end
    local p6 = line_str:find(",", p5 + 1, true)
    if not p6 then return nil end
    local p7 = line_str:find(",", p6 + 1, true)
    if not p7 then return nil end
    local p8 = line_str:find(",", p7 + 1, true)
    if not p8 then return nil end
    local p9 = line_str:find(",", p8 + 1, true)
    if not p9 then return nil end

    return {
        class = "dialogue", section = "[Events]", comment = false,
        layer = tonumber(line_str:sub(prefix_len + 1, p1 - 1)) or 0,
        start_time = fast_parse_time(line_str:sub(p1 + 1, p2 - 1)),
        end_time = fast_parse_time(line_str:sub(p2 + 1, p3 - 1)),
        style = line_str:sub(p3 + 1, p4 - 1),
        actor = line_str:sub(p4 + 1, p5 - 1),
        margin_l = tonumber(line_str:sub(p5 + 1, p6 - 1)) or 0,
        margin_r = tonumber(line_str:sub(p6 + 1, p7 - 1)) or 0,
        margin_t = tonumber(line_str:sub(p7 + 1, p8 - 1)) or 0,
        effect = line_str:sub(p8 + 1, p9 - 1),
        text = line_str:sub(p9 + 1)
    }
end

local function clone_line(line)
    local out = {}
    for k, v in pairs(line) do
        out[k] = v
    end
    return out
end

local function serialize_metrics(line)
    local parts = {}
    parts[#parts+1] = "h=" .. tostring(line.height or 0)
    parts[#parts+1] = "d=" .. tostring(line.descent or 0)
    parts[#parts+1] = "e=" .. tostring(line.extlead or 0)
    parts[#parts+1] = "sel=" .. (line.is_selected and 1 or 0)
    parts[#parts+1] = "rw=" .. tostring(line.width or 0)
    parts[#parts+1] = "l=" .. tostring(line.left or 0)
    parts[#parts+1] = "c=" .. tostring(line.center or 0)
    parts[#parts+1] = "r=" .. tostring(line.right or 0)
    parts[#parts+1] = "t=" .. tostring(line.top or 0)
    parts[#parts+1] = "m=" .. tostring(line.middle or 0)
    parts[#parts+1] = "b=" .. tostring(line.bottom or 0)

    local base_l = line.left or 0
    if line.kara and line.kara.n then
        local syl_lefts, syl_centers, syl_rights, syl_widths, syl_starts, syl_ends = {}, {}, {}, {}, {}, {}
        for i = 0, line.kara.n do
            local s = line.kara[i]
            if s then
                syl_lefts[#syl_lefts+1]   = tostring((s.left or 0) + base_l)
                syl_centers[#syl_centers+1] = tostring((s.center or 0) + base_l)
                syl_rights[#syl_rights+1]  = tostring((s.right or 0) + base_l)
                syl_widths[#syl_widths+1] = tostring(s.width or 0)
                syl_starts[#syl_starts+1] = tostring(s.start_time or 0)
                syl_ends[#syl_ends+1] = tostring(s.end_time or 0)
            end
        end
        parts[#parts+1] = "syl_lefts=" .. table.concat(syl_lefts, ",")
        parts[#parts+1] = "syl_centers=" .. table.concat(syl_centers, ",")
        parts[#parts+1] = "syl_rights=" .. table.concat(syl_rights, ",")
        parts[#parts+1] = "syl_widths=" .. table.concat(syl_widths, ",")
        parts[#parts+1] = "syl_starts=" .. table.concat(syl_starts, ",")
        parts[#parts+1] = "syl_ends=" .. table.concat(syl_ends, ",")
    end

    if line.styleref then
        local w_list = {}
        local stripped = line.text_stripped or line.text:gsub("{.-}", "")
        local acc, cur_w = "", 0
        for c in unicode.chars(stripped) do
            acc = acc .. c
            local w = aegisub.text_extents(line.styleref, acc)
            w_list[#w_list+1] = tostring(w - cur_w)
            cur_w = w
        end
        parts[#parts+1] = "w=" .. table.concat(w_list, ",")
    end

    return table.concat(parts, ";")
end

local function build_style_line(line)
    local function fmt_num(v)
        if v == nil then return "0" end
        local n = tonumber(v)
        if not n then return tostring(v) end
        if n % 1 == 0 then return string.format("%d", n) end
        return string.format("%.3f", n):gsub("%.?0+$", "")
    end
    return string.format(
        "Style: %s,%s,%s,%s,%s,%s,%s,%d,%d,%d,%d,%s,%s,%s,%s,%d,%s,%s,%d,%d,%d,%d,%d",
        line.name, line.fontname, fmt_num(line.fontsize), line.color1, line.color2, line.color3, line.color4,
        line.bold and 1 or 0, line.italic and 1 or 0, line.underline and 1 or 0, line.strikeout and 1 or 0,
        fmt_num(line.scale_x), fmt_num(line.scale_y), fmt_num(line.spacing), fmt_num(line.angle),
        tonumber(line.borderstyle) or 1, fmt_num(line.outline), fmt_num(line.shadow),
        tonumber(line.align) or 2, tonumber(line.margin_l) or 0, tonumber(line.margin_r) or 0, tonumber(line.margin_t) or 0,
        tonumber(line.encoding) or 1
    )
end

-- Reads a session file with short retries.
-- Python guarantees that writing session_file occurs BEFORE destroying the window
-- and BEFORE releasing lock_file; this retry acts as a buffer for disk latency.
local function read_valid_session(path, timeout_ms)
    local elapsed = 0
    local interval = 25

    while elapsed <= timeout_ms do
        local sf = io.open(path, "r")
        if sf then
            local content = sf:read("*all")
            sf:close()

            if content
                and content:match("^%s*{")
                and content:match('"nodes"%s*:') then
                return content
            end
        end

        kernel32.Sleep(interval)
        elapsed = elapsed + interval
    end

    return nil
end

function launch_Pyxis(subs, sel, act)
    -- [OPTIMIZATION PATCH]
    if not aegisub.progress._patched then
        local original_set = aegisub.progress.set
        local original_task = aegisub.progress.task
        local call_count = 0

        aegisub.progress.set = function( pct )
            call_count = call_count + 1
            if call_count % 50 == 0 or pct >= 99.9 then
                if aegisub.progress.is_cancelled() then
                    error("User cancelled", 0)
                end
                original_set( pct )
            end
        end

        aegisub.progress.task = function( msg )
            if call_count % 50 == 0 then
                original_task( msg )
            end
        end
        aegisub.progress._patched = true
    end

    if not karaskel then
        aegisub.dialog.display({{class="label", label="Critical error: karaskel could not be loaded."}})
        return
    end

    local function find_pyxis_nodes_dir()
        local user_autoload = aegisub.decode_path("?user/automation/autoload")
        local p_user = join_path(user_autoload, "PyxisNodes")
        local f_test = io.open(join_path(p_user, "main.py"), "r")
        if f_test then
            f_test:close()
            return p_user
        end

        local data_autoload = aegisub.decode_path("?data/automation/autoload")
        local p_data = join_path(data_autoload, "PyxisNodes")
        local f_test2 = io.open(join_path(p_data, "main.py"), "r")
        if f_test2 then
            f_test2:close()
            return p_data
        end

        local btn, _ = aegisub.dialog.display({
            {class="label", label="Pyxis Effector requiere el entorno completo de ejecucion (PyxisNodes).", x=0, y=0, width=2, height=1},
            {class="label", label="No se encontraron los archivos del motor en tu carpeta de automatizaciones de Aegisub.", x=0, y=1, width=2, height=1},
            {class="label", label="Descarga el paquete oficial desde GitHub Releases para instalarlo.", x=0, y=2, width=2, height=1}
        }, {"Abrir GitHub Releases", "Cerrar"})

        if btn == "Abrir GitHub Releases" and shell32 and shell32.ShellExecuteA then
            shell32.ShellExecuteA(nil, "open", "https://github.com/Mandholine/Pyxis-Effector/releases/latest", nil, nil, 1)
        end

        return nil
    end

    local Pyxis_dir = find_pyxis_nodes_dir()
    if not Pyxis_dir then
        return
    end

    -- Dynamic temporary directory in %APPDATA%\PyxisNodes\temp_cache
    local appdata = os.getenv("APPDATA") or (os.getenv("USERPROFILE") and (os.getenv("USERPROFILE") .. "\\AppData\\Roaming")) or base_dir
    local temp_cache_dir = join_path(join_path(appdata, "PyxisNodes"), "temp_cache")
    ensure_dir(temp_cache_dir)

    -- Exclusive files for THIS Aegisub instance in temp_cache
    local temp_ass = join_path(temp_cache_dir, "Pyxis_temp_" .. instance_id .. ".ass")
    local result_file = join_path(temp_cache_dir, "Pyxis_result_" .. instance_id .. ".txt")
    local lock_file = join_path(temp_cache_dir, "Pyxis_lock_" .. instance_id .. ".txt")
    local session_file = join_path(temp_cache_dir, "Pyxis_session_" .. instance_id .. ".json")
    local main_script = join_path(Pyxis_dir, "main.py")

    aegisub.progress.task("Exporting Aegisub headers and styles...")
    local meta, styles = karaskel.collect_head(subs, false)

    local sel_map = {}
    for _, idx in ipairs(sel) do sel_map[idx] = true end

    local project_props = (aegisub.project_properties and aegisub.project_properties()) or {}
    local audio_file = project_props.audio_file or ""
    local video_file = project_props.video_file or ""
    if audio_file == "?video" and video_file ~= "" then
        audio_file = video_file
    end
    local script_file = (aegisub.file_name and aegisub.file_name()) or ""

    -- 1. Create a "Digital Fingerprint" of current state (Styles, Lines, Selection and Media)
    local current_sub_state = "v:" .. video_file .. "|a:" .. audio_file .. "|s:" .. script_file .. "|"
    for i = 1, styles.n do
        current_sub_state = current_sub_state .. build_style_line(styles[i])
    end
    local exported_dialogue_subs_indices = {}
    for i = 1, #subs do
        local l = subs[i]
        if l.class == "dialogue" and l.effect ~= "pyxis_fx" then
            exported_dialogue_subs_indices[#exported_dialogue_subs_indices + 1] = i
            current_sub_state = current_sub_state .. l.raw .. (sel_map[i] and "1" or "0")
        end
    end

    -- 2. Check if we can skip export (Safe Cache)
    local skip_karaskel = false
    if last_sub_state_hash == current_sub_state then
        local check_file = io.open(temp_ass, "r")
        if check_file then
            local content = check_file:read("*all")
            check_file:close()
            if content and content:match("PyxisMetrics") then
                skip_karaskel = true
            end
        end
    end

    -- 3. If there were changes or file was lost, export raw lines
    if not skip_karaskel then
        aegisub.progress.task("Preparing dialogue lines for Pyxis Engine...")
        local file = io.open(temp_ass, "w")
        if not file then
            aegisub.debug.out("Could not create temporary file: " .. temp_ass .. "\n")
            return
        end

        file:write("[Script Info]\nScriptType: v4.00+\n")
        file:write("PlayResX: " .. tostring(meta.res_x or 1280) .. "\nPlayResY: " .. tostring(meta.res_y or 720) .. "\n\n")

        local msa, msb = nil, nil
        if aegisub.ms_from_frame then
            msa, msb = aegisub.ms_from_frame(1), aegisub.ms_from_frame(101)
        end
        local detected_frame_dur = (msb and msa) and string.format("%.4f", (msb - msa) / 100) or "41.708"
        file:write("[Pyxis Config]\nFrameDuration: " .. detected_frame_dur .. "\n")
        if script_file ~= "" then
            file:write("ScriptFile: " .. tostring(script_file) .. "\n")
        end
        if audio_file ~= "" then
            file:write("AudioFile: " .. tostring(audio_file) .. "\n")
        end
        if video_file ~= "" then
            file:write("VideoFile: " .. tostring(video_file) .. "\n")
        end
        file:write("\n")
        file:write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")

        for i = 1, styles.n do file:write(build_style_line(styles[i]) .. "\n") end

        file:write("\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        local total_lines = #subs
        for i = 1, total_lines do
            local line = subs[i]
            if line.class == "dialogue" and line.effect ~= "pyxis_fx" then
                if sel_map[i] then
                    file:write(string.format(
                        "Comment: %d,%s,%s,%s,%s,%d,%d,%d,PyxisMetrics,sel=1\n",
                        line.layer, line.start_time, line.end_time, line.style, line.actor,
                        line.margin_l, line.margin_r, line.margin_t
                    ))
                end
                file:write(line.raw .. "\n")
            end
            aegisub.progress.set(100 * (i / total_lines))
        end
        file:close()
        last_sub_state_hash = current_sub_state
    else
        aegisub.progress.task("Reusing previous export (Fast launch)...")
    end

    pcall(os.remove, result_file)
    pcall(os.remove, result_file .. "_debug.log")
    pcall(os.remove, lock_file)

    local lf = io.open(lock_file, "w")
    if lf then lf:write("working"); lf:close() end

    -- Prepare session for Python (continuity of THIS Aegisub instance)
    if last_Pyxis_session then
        local sf = io.open(session_file, "w")
        if sf then
            sf:write(last_Pyxis_session)
            sf:close()
        end
    else
        pcall(os.remove, session_file)
    end

    local aegisub_version = "3.4.2"
    local aegisub_pid = kernel32.GetCurrentProcessId()

    -- Try instant launch (0ms) by communicating with background Python Daemon if it exists
    local json_payload = string.format(
        '{"temp_ass":%q,"result_file":%q,"lock_file":%q,"session_file":%q,"aegisub_version":%q,"aegisub_pid":%d}',
        temp_ass, result_file, lock_file, session_file, aegisub_version, aegisub_pid
    )

    -- Grant explicit permission to Windows to bring window to foreground
    if user32 and user32.AllowSetForegroundWindow then
        pcall(user32.AllowSetForegroundWindow, 0xFFFFFFFF)
    end

    local daemon_reopened = ping_and_reopen_daemon(json_payload)

    if not daemon_reopened then
        aegisub.progress.task("Launching Pyxis Node Engine...")
        local params = '-B "' .. main_script .. '" "' .. temp_ass .. '" "' .. result_file .. '" "' .. lock_file .. '" "' .. session_file .. '" "' .. aegisub_version .. '" "' .. tostring(aegisub_pid) .. '"'

        -- Smart detection of Portable vs System Python (prefer pythonw, fallback to python)
        local portable_pythonw = join_path(Pyxis_dir, "python\\pythonw.exe")
        local portable_python = join_path(Pyxis_dir, "python\\python.exe")
        local python_cmd = "pythonw"

        local check_pyw = io.open(portable_pythonw, "r")
        if check_pyw then
            check_pyw:close()
            python_cmd = portable_pythonw
        else
            local check_py = io.open(portable_python, "r")
            if check_py then
                check_py:close()
                python_cmd = portable_python
            end
        end

        local launch_result = shell32.ShellExecuteA(nil, "open", python_cmd, params, Pyxis_dir, 1)
        if launch_result <= 32 then
            -- Fallback if pythonw is not registered in system PATH
            python_cmd = "python"
            launch_result = shell32.ShellExecuteA(nil, "open", python_cmd, params, Pyxis_dir, 1)
        end
        if launch_result <= 32 then
            aegisub.debug.out("Error launching Python (" .. tostring(python_cmd) .. "). Error code: " .. tostring(launch_result) .. "\n")
            pcall(os.remove, lock_file)
            return
        end
    else
        aegisub.progress.task("Instant launch from background daemon...")
    end

    local cancelled = false

    while true do
        if aegisub.progress.is_cancelled() then
            cancelled = true
            break
        end

        local err_check = io.open(result_file .. "_debug.log", "r")
        if err_check then
            err_check:close()
            break
        end

        local check = io.open(lock_file, "r")
        if not check then
            break
        end

        check:close()
        kernel32.Sleep(50)
    end

    if cancelled then
        -- Do not consume or delete session if Aegisub cancelled execution.
        pcall(os.remove, lock_file)
        return sel, act
    end

    -- Python guarantees: save session -> destroy window -> release lock.
    -- This short retry acts as a buffer for disk latency, not a real race condition.
    local recovered_session = read_valid_session(session_file, 100)

    if recovered_session then
        last_Pyxis_session = recovered_session
    end

    pcall(os.remove, session_file)
    pcall(os.remove, session_file .. ".tmp")

    local err_file = io.open(result_file .. "_debug.log", "r")
    if err_file then
        local err_msg = err_file:read("*all")
        err_file:close()
        aegisub.dialog.display({{class="textbox", x=0, y=0, width=60, height=20, value=err_msg}}, {"Close"})
        pcall(os.remove, result_file .. "_debug.log")
        return
    end

    local res_file = io.open(result_file, "r")
    if not res_file then return end

    aegisub.progress.task("Injecting generated effect layers...")
    local new_lines = {}
    local used_subs_indices = {}
    for line_str in res_file:lines() do
        if line_str:sub(1, 16) == "#PYXIS_USED_IDX:" then
            local idx_str = line_str:sub(17)
            for num in idx_str:gmatch("%d+") do
                local d_idx = tonumber(num)
                if d_idx and exported_dialogue_subs_indices[d_idx] then
                    used_subs_indices[exported_dialogue_subs_indices[d_idx]] = true
                end
            end
        else
            local nl = fast_parse_dialogue_line(line_str)
            if nl then
                new_lines[#new_lines + 1] = nl
            end
        end
    end
    res_file:close()

    local total_new = #new_lines
    if total_new == 0 then
        pcall(os.remove, result_file)
        pcall(os.remove, lock_file)
        return
    end

    -- Disable used source lines (Selected, Style, or All as generated by Pyxis)
    local has_used_indices = false
    for idx, _ in pairs(used_subs_indices) do
        has_used_indices = true
        local line = subs[idx]
        if line and line.class == "dialogue" and line.effect ~= "pyxis_fx" then
            line.comment = true
            subs[idx] = line
        end
    end

    -- Fallback if no #PYXIS_USED_IDX header was present
    if not has_used_indices then
        for _, idx in ipairs(sel) do
            local line = subs[idx]
            if line and line.class == "dialogue" and line.effect ~= "pyxis_fx" then
                line.comment = true
                subs[idx] = line
            end
        end
    end

    -- Ultra high-speed O(1) injection using subs.append (push_back in C++)
    local batch_size = 500
    for i = 1, total_new do
        subs.append(new_lines[i])
        if i % batch_size == 0 or i == total_new then
            aegisub.progress.set(100 * (i / total_new))
        end
    end

    pcall(os.remove, result_file)
    pcall(os.remove, lock_file)

    aegisub.set_undo_point("Pyxis Nodes FX")
    return sel, act
end

aegisub.register_macro(script_name, script_description, launch_Pyxis)
