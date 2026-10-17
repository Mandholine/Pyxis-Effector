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
-- For any question you can visit: https://discord.gg/rYsARc3fB9

script_name        = "Pyxis Node Engine"
script_description = "Visual Node-Based Karaoke Automation"
script_author      = "Pyxis Dev Team"
script_version     = "1.1.4"
script_namespace   = "pyxis.NodeEngine"

local depctrl_ok, DependencyControl = pcall(require, "l0.DependencyControl")
local version_record = nil

if depctrl_ok and (type(DependencyControl) == "table" or type(DependencyControl) == "function") then
    pcall(function()
        version_record = DependencyControl{
            feed = "https://raw.githubusercontent.com/Mandholine/Pyxis-Effector/master/DependencyControl.json"
        }
    end)
end

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

-- [CROSS-PLATFORM LAYER]
-- Windows: funciones Win32 vía FFI (kernel32/shell32/user32/wininet).
-- Linux/macOS: equivalencias POSIX (libc vía ffi.C, curl/wget, nohup).
local IS_WINDOWS = package.config:sub(1, 1) == "\\"
local IS_MACOS = (not IS_WINDOWS) and ffi.os == "OSX"

-- Artefacto de release que corresponde a esta plataforma (ver tools/build_release.py).
local function platform_tag()
    if IS_WINDOWS then return "win64" end
    local arm = ffi.arch == "arm64"
    if IS_MACOS then return arm and "macos-arm64" or "macos-x64" end
    return arm and "linux-arm64" or "linux64"
end

-- Repositorio de GitHub del que se descarga el motor (PyxisNodes). Un fork puede cambiar
-- esta constante o exportar PYXIS_RELEASE_REPO=usuario/repositorio antes de abrir Aegisub.
local RELEASE_REPO = "Mandholine/Pyxis-Effector"
do
    local override = os.getenv("PYXIS_RELEASE_REPO")
    if override and override:match("^[%w%-%._]+/[%w%-%._]+$") then
        RELEASE_REPO = override
    end
end

-- URL candidatas del paquete, por orden. Las releases nuevas (tools/build_release.py + CI)
-- usan la etiqueta v<versión>; la primera release, subida a mano, usó otra para Windows.
local function release_urls(zip_name, tag)
    local base = "https://github.com/" .. RELEASE_REPO .. "/releases/download/"
    return {
        base .. "v" .. script_version .. "/" .. zip_name,
        base .. "PyxisEffector-v" .. script_version .. "-" .. tag .. "/" .. zip_name,
    }
end

local function file_size(path)
    local f = io.open(path, "rb")
    if not f then return 0 end
    local size = f:seek("end") or 0
    f:close()
    return size
end

-- Script de instalación de Windows: prueba cada URL con curl.exe y, si todas fallan,
-- con PowerShell (también URL por URL). Función pura para poder probar su flujo.
local function build_installer_bat(zip_path, urls, target_dir)
    local lines = {
        "@echo off",
        "title Descargando Pyxis Effector",
        "echo Descargando motor de Pyxis (~370 MB)...",
    }
    for i, url in ipairs(urls) do
        local cmd = string.format('curl.exe -# -L -f -o "%s" "%s"', zip_path, url)
        lines[#lines + 1] = (i == 1) and cmd or ("if errorlevel 1 " .. cmd)
    end
    local quoted = {}
    for _, url in ipairs(urls) do quoted[#quoted + 1] = "'" .. url .. "'" end
    local ps = string.format(
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; "
        .. "$ProgressPreference = 'Continue'; $wc = New-Object Net.WebClient; $ok = $false; "
        .. "foreach ($u in @(%s)) { if (-not $ok) { try { $wc.DownloadFile($u, '%s'); $ok = $true } catch {} } }; "
        .. "if ($ok) { Expand-Archive -Path '%s' -DestinationPath '%s' -Force; Remove-Item '%s' -Force }",
        table.concat(quoted, ", "), zip_path, zip_path, target_dir, zip_path)
    local tail = {
        "if errorlevel 1 goto fallback",
        "echo Descomprimiendo archivos...",
        string.format('tar.exe -xf "%s" -C "%s"', zip_path, target_dir),
        "if errorlevel 1 goto fallback",
        string.format('del /f /q "%s" >nul 2>&1', zip_path),
        "exit /b 0",
        "",
        ":fallback",
        "echo Reintentando con PowerShell...",
        'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "' .. ps .. '"',
        "exit /b 0",
        "",
    }
    for _, l in ipairs(tail) do lines[#lines + 1] = l end
    return table.concat(lines, "\n")
end

-- Aegisub lanzado desde el Finder/launcher hereda un PATH mínimo; Homebrew y
-- /usr/local no están incluidos, así que se añaden para localizar python3, ffmpeg, etc.
local POSIX_PATH_PREFIX = "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:"

local kernel32 = nil
local shell32 = nil
local user32 = nil
local wininet = nil

if IS_WINDOWS then
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
    kernel32 = ffi.load("kernel32")
    shell32 = ffi.load("shell32")
    pcall(function() user32 = ffi.load("user32") end)
    pcall(function() wininet = ffi.load("wininet") end)
else
    ffi.cdef[[
        int usleep(unsigned int useconds);
        int getpid(void);
    ]]
end

local function sleep_ms(ms)
    if IS_WINDOWS and kernel32 then
        kernel32.Sleep(ms)
    else
        ffi.C.usleep(math.floor(tonumber(ms) or 0) * 1000)
    end
end

local function get_process_id()
    if IS_WINDOWS and kernel32 then
        return tonumber(kernel32.GetCurrentProcessId()) or 0
    end
    return tonumber(ffi.C.getpid()) or 0
end

local function shell_quote(s)
    return "'" .. tostring(s):gsub("'", "'\\''") .. "'"
end

local function has_bin(name)
    local p = io.popen("PATH=\"" .. POSIX_PATH_PREFIX .. "$PATH\" command -v " .. tostring(name) .. " 2>/dev/null")
    if not p then return false end
    local out = p:read("*l")
    p:close()
    return out ~= nil and out ~= ""
end

local function ping_and_reopen_daemon(payload_json)
    if IS_WINDOWS and wininet then
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

    -- Linux/macOS: curl o wget contra el daemon local (127.0.0.1:28723)
    local tmp = os.tmpname()
    local f = io.open(tmp, "w")
    if not f then return false end
    f:write(payload_json)
    f:close()

    local cmd = nil
    if has_bin("curl") then
        cmd = string.format(
            "curl -s -m 2 -X POST -H 'Content-Type: application/json' --data-binary @%s http://127.0.0.1:28723/reopen 2>/dev/null",
            shell_quote(tmp)
        )
    elseif has_bin("wget") then
        cmd = string.format(
            "wget -q -T 2 -O - --post-file=%s --header='Content-Type: application/json' http://127.0.0.1:28723/reopen 2>/dev/null",
            shell_quote(tmp)
        )
    end

    local reopened = false
    if cmd then
        local p = io.popen(cmd)
        if p then
            local body = p:read("*all") or ""
            p:close()
            if body:match("reopened") then
                reopened = true
            end
        end
    end

    os.remove(tmp)
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
    if IS_WINDOWS and kernel32 and kernel32.CreateDirectoryA then
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
        os.execute("mkdir -p " .. shell_quote(path))
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

        sleep_ms(interval)
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

    local function download_and_extract_runtime(target_dir)
        local btn, _ = aegisub.dialog.display({
            {class="label", label="Pyxis Effector requiere el motor de ejecución (~370 MB).", x=0, y=0, width=2, height=1},
            {class="label", label="Repositorio: https://github.com/" .. RELEASE_REPO, x=0, y=1, width=2, height=1},
            {class="label", label="¿Desea iniciar la descarga ahora?", x=0, y=2, width=2, height=1}
        }, {"Descargar", "Cancelar"})

        if btn ~= "Descargar" then
            return nil
        end

        local temp_dir = (IS_WINDOWS and os.getenv("TEMP")) or os.getenv("TMPDIR") or "/tmp"
        local arch_tag = platform_tag()
        local zip_name = "PyxisEffector-v" .. script_version .. "-" .. arch_tag .. ".zip"
        local zip_path = join_path(temp_dir, zip_name)
        local download_urls = release_urls(zip_name, arch_tag)

        if not IS_WINDOWS then
            -- Linux/macOS: curl/wget + unzip/python3 zipfile
            aegisub.progress.task("Descargando motor de Pyxis...")
            local dl_template = nil
            if has_bin("curl") then
                dl_template = "curl -# -L -f -o %s %s"
            elseif has_bin("wget") then
                dl_template = "wget --progress=bar:force -O %s %s"
            end
            local downloaded = false
            if dl_template then
                for _, url in ipairs(download_urls) do
                    pcall(os.remove, zip_path)
                    os.execute(string.format(dl_template, shell_quote(zip_path), shell_quote(url)))
                    if file_size(zip_path) > 0 then
                        downloaded = true
                        break
                    end
                end
                if not downloaded then pcall(os.remove, zip_path) end
            end
            if downloaded then
                if has_bin("unzip") then
                    os.execute(string.format("unzip -o -q %s -d %s", shell_quote(zip_path), shell_quote(target_dir)))
                else
                    -- zipfile no conserva los permisos de ejecución: se restauran a mano
                    os.execute(string.format("python3 -m zipfile -e %s %s", shell_quote(zip_path), shell_quote(target_dir)))
                    local nodes_dir = join_path(target_dir, "PyxisNodes")
                    os.execute(string.format("chmod -R u+x %s %s 2>/dev/null",
                        shell_quote(join_path(join_path(nodes_dir, "python"), "bin")),
                        shell_quote(join_path(nodes_dir, "bin"))))
                end
                if IS_MACOS then
                    -- Evita el bloqueo de Gatekeeper sobre el Python y los binarios descargados
                    os.execute(string.format("xattr -dr com.apple.quarantine %s 2>/dev/null",
                        shell_quote(join_path(target_dir, "PyxisNodes"))))
                end
                pcall(os.remove, zip_path)
            end
        else
            local bat_file = join_path(temp_dir, "pyxis_installer.bat")

            local f = io.open(bat_file, "w")
            if f then
                f:write(build_installer_bat(zip_path, download_urls, target_dir))
                f:close()
                os.execute('cmd.exe /c "' .. bat_file .. '"')
                pcall(os.remove, bat_file)
            end
        end

        local extracted_pyxis = join_path(target_dir, "PyxisNodes")
        local verify_file = io.open(join_path(extracted_pyxis, "main.py"), "r")
        if verify_file then
            verify_file:close()
            return extracted_pyxis
        end

        aegisub.dialog.display({
            {class="label", label="Error: No se pudo descargar o extraer el motor de Pyxis.", x=0, y=0, width=2, height=1},
            {class="label", label="Verifique su conexión a internet o instálelo manualmente desde GitHub Releases.", x=0, y=1, width=2, height=1}
        }, {"Cerrar"})
        return nil
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

        return download_and_extract_runtime(user_autoload)
    end

    local Pyxis_dir = find_pyxis_nodes_dir()
    if not Pyxis_dir then
        return
    end

    -- Dynamic temporary directory in %APPDATA%\PyxisNodes\temp_cache (Linux: XDG_DATA_HOME)
    local data_base
    if IS_WINDOWS then
        data_base = os.getenv("APPDATA") or (os.getenv("USERPROFILE") and (os.getenv("USERPROFILE") .. "\\AppData\\Roaming")) or "."
    else
        data_base = os.getenv("XDG_DATA_HOME") or (os.getenv("HOME") and (os.getenv("HOME") .. "/.local/share")) or "/tmp"
    end
    local temp_cache_dir = join_path(join_path(data_base, "PyxisNodes"), "temp_cache")
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
        if l.class == "dialogue" and l.effect ~= "Pyxis_fx" then
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
            if line.class == "dialogue" and line.effect ~= "Pyxis_fx" then
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
    local aegisub_pid = get_process_id()

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

        if not IS_WINDOWS then
            -- Linux/macOS: intérprete de Python (runtime empaquetado, luego venv, luego PATH)
            local python_cmd = nil
            local bundled_py = join_path(Pyxis_dir, join_path("python", join_path("bin", "python3")))
            local venv_py = join_path(Pyxis_dir, join_path(".venv", join_path("bin", "python3")))
            local check_bundled = io.open(bundled_py, "r")
            local check_venv = io.open(venv_py, "r")
            if check_bundled then
                check_bundled:close()
                if check_venv then check_venv:close() end
                python_cmd = bundled_py
            elseif check_venv then
                check_venv:close()
                python_cmd = venv_py
            elseif has_bin("python3") then
                python_cmd = "python3"
            elseif has_bin("python") then
                python_cmd = "python"
            end

            if not python_cmd then
                aegisub.dialog.display({{class="label", label="Error: no se encontró Python 3. Reinstala el motor de Pyxis desde GitHub Releases o instala python3."}}, {"Cerrar"})
                pcall(os.remove, lock_file)
                return
            end

            local cmd_parts = { shell_quote(python_cmd), "-B", shell_quote(main_script) }
            for _, arg in ipairs({ temp_ass, result_file, lock_file, session_file, aegisub_version, tostring(aegisub_pid) }) do
                cmd_parts[#cmd_parts + 1] = shell_quote(arg)
            end
            local launch_cmd = "PATH=\"" .. POSIX_PATH_PREFIX .. "$PATH\" " .. table.concat(cmd_parts, " ") .. " >/dev/null 2>&1 &"
            os.execute(launch_cmd)
        else
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
        sleep_ms(50)
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
        if line and line.class == "dialogue" and line.effect ~= "Pyxis_fx" then
            line.comment = true
            subs[idx] = line
        end
    end

    -- Fallback if no #PYXIS_USED_IDX header was present
    if not has_used_indices then
        for _, idx in ipairs(sel) do
            local line = subs[idx]
            if line and line.class == "dialogue" and line.effect ~= "Pyxis_fx" then
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

if version_record and version_record.registerMacro then
    version_record:registerMacro(launch_Pyxis)
else
    aegisub.register_macro(script_name, script_description, launch_Pyxis)
end
