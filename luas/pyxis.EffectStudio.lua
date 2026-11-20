-- Pyxis Effect Studio  (install.py fija las rutas por defecto al instalar)
script_name = "Pyxis Effect Studio"
script_description = "Crea efectos de karaoke en codigo (Python + pyxis-core) y aplicalos al k-time"
script_author = "Pyxis"
script_version = "1.0.0"

local DEFAULTS = { workspace = "/Users/holguin/PyxisEffects", python = "/Users/holguin/PyxisEffects/.venv/bin/python", editor = "\"/Users/holguin/.antigravity-ide/antigravity-ide/bin/antigravity-ide\" --wait", api_python = "/Users/holguin/Documents/proyectos/Pyxis-Effector/pyxis_api/.venv/bin/python", studio_app = "/Users/holguin/Documents/proyectos/Pyxis-Effector/pyxis_studio/build/macos/Build/Products/Release/pyxis_studio.app", api_url = "http://127.0.0.1:28723" }

local is_win = package.config:sub(1, 1) == "\\"
local sep = is_win and "\\" or "/"

-- El macro GENERA el efecto completo (.py) para el estilo elegido, con sus colores reales.
local EFFECT_SOURCE = [==[
# -*- coding: utf-8 -*-
"""@NAME@ -- efecto para el estilo @STYLE_TXT@. Generado por Pyxis Effect Studio; editalo libremente."""
from pyxis_fx import color, fmt, units, retime, rand, T

NAME = "@NAME@"
STYLE = @STYLE@

# Colores tomados del estilo (R, G, B)
PRIMARY = @C1@
SECONDARY = @C2@
OUTLINE = @C3@


def run(line, out):
    # Como `template char noblank`: una iteracion por caracter visible
    for c in units(line, "char", noblank=True):
        pos = "\\an5\\pos(%s,%s)" % (fmt(c.center), fmt(c.middle))
        base = "\\3c%s\\1c%s\\bord2\\blur2\\shad0" % (color(*OUTLINE), color(*PRIMARY))

        # 1) Entrada: aparece antes de su silaba, escalonada por indice de silaba
        s, e = retime(c, "start2syl", -400 + 400 / c.syln * c.si, 0)
        out.add("{%s\\fad(500,0)%s%s%s}%s" % (
                pos, base, T(0, 200, "\\3c" + color(*PRIMARY)),
                T(200, 300, "\\3c" + color(*OUTLINE)), c.text_stripped),
                s, e, layer=2, line=line)

        # 2) Salida: desaparece despues de su silaba
        s, e = retime(c, "syl2end", 0, 400 / c.syln * c.si)
        out.add("{%s\\fad(0,400)%s%s}%s" % (
                pos, base, T(200, 300, "\\3c" + color(*OUTLINE)), c.text_stripped),
                s, e, layer=2, line=line)

        # 3) Mientras suena la silaba: salto, escala y rotacion aleatorias que se relajan
        s, e = retime(c, "syl", 0, 0)
        d = e - s
        out.add("{\\an5\\move(%s,%s,%s,%s)\\be1%s\\fscy%d\\frz%d\\fry%d\\frx%d\\1c%s\\3c%s}{%s}%s" % (
                fmt(c.center), fmt(c.middle - 15), fmt(c.center), fmt(c.middle),
                T(0, d / 12, "\\fscx%d" % rand(130, 160)), rand(130, 160), rand(-30, 30),
                rand(-50, 50), rand(-20, 20), color(*SECONDARY), color(*OUTLINE),
                T(0, d, "\\frx0\\fry0\\frz0\\fscx100\\fscy100"), c.text_stripped),
                s, e, layer=3, line=line)
]==]

local function find_style(subs, name)
    for i = 1, #subs do
        local l = subs[i]
        if l.class == "style" and l.name == name then return l end
    end
end

local function ass_color(c, default)
    -- color de estilo "&HAABBGGRR" -> literal Python "&HBBGGRR&"
    local bb, gg, rr = tostring(c or ""):match("&H%x%x(%x%x)(%x%x)(%x%x)")
    if not rr then return default end
    return '"&H' .. (bb .. gg .. rr):upper() .. '&"'
end

local function build_effect(subs, name, style, source)
    local st, st_txt, c1, c2, c3 = "None", "(todos)", '"&HFFFFFF&"', '"&HFFFFFF&"', '"&HA050FF&"'
    if style and style ~= ALL_STYLES then
        st = '"' .. style:gsub("\\", "\\\\"):gsub('"', '\\"') .. '"'
        st_txt = st
        local sd = find_style(subs, style)
        if sd then
            c1 = ass_color(sd.color1, c1)
            c2 = ass_color(sd.color2, c2)
            c3 = ass_color(sd.color3, c3)
        end
    end
    local rep = {NAME = name, STYLE = st, STYLE_TXT = st_txt, C1 = c1, C2 = c2, C3 = c3}
    return ((source or EFFECT_SOURCE):gsub("@(%u[%u%d_]*)@", function(k) return rep[k] end))
end

-- ------------------------------------------------------------ utilidades ---
local function q(s)
    if is_win then return '"' .. s .. '"' end
    return "'" .. s:gsub("'", "'\\''") .. "'"
end

local function write_file(path, content)
    local f = io.open(path, "wb")
    if not f then return false end
    f:write(content); f:close()
    return true
end

local function read_file(path)
    local f = io.open(path, "rb")
    if not f then return nil end
    local c = f:read("*a"); f:close()
    return c
end

local function exists(path)
    local f = io.open(path, "r")
    if f then f:close() return true end
    return false
end

local function ass_time(ms)
    ms = math.floor(ms / 10 + 0.5) * 10
    local cs = (ms % 1000) / 10
    local s = math.floor(ms / 1000) % 60
    local m = math.floor(ms / 60000) % 60
    local h = math.floor(ms / 3600000)
    return string.format("%d:%02d:%02d.%02d", h, m, s, cs)
end

local function parse_time(t)
    local h, m, s, cs = t:match("^(%d+):(%d+):(%d+)%.(%d+)$")
    if not h then return 0 end
    return ((tonumber(h) * 60 + tonumber(m)) * 60 + tonumber(s)) * 1000 + tonumber(cs) * 10
end

local function parse_dialogue(line)
    local layer, st, et, style, actor, ml, mr, mv, eff, text =
        line:match("^Dialogue:%s*(%-?%d+),([^,]*),([^,]*),([^,]*),([^,]*),(%-?%d+),(%-?%d+),(%-?%d+),([^,]*),(.*)$")
    if not layer then return nil end
    return {
        class = "dialogue", section = "[Events]", comment = false,
        layer = tonumber(layer), start_time = parse_time(st), end_time = parse_time(et),
        style = style, actor = actor, margin_l = tonumber(ml), margin_r = tonumber(mr),
        margin_t = tonumber(mv), effect = eff, text = text,
    }
end

local function style_line(s)
    local function b(v) return v and -1 or 0 end
    return string.format("Style: %s,%s,%s,%s,%s,%s,%s,%d,%d,%d,%d,%s,%s,%s,%s,%d,%s,%s,%d,%d,%d,%d,%d",
        s.name, s.fontname, s.fontsize, s.color1, s.color2, s.color3, s.color4,
        b(s.bold), b(s.italic), b(s.underline), b(s.strikeout),
        s.scale_x, s.scale_y, s.spacing, s.angle, s.borderstyle, s.outline, s.shadow,
        s.align, s.margin_l, s.margin_r, s.margin_t, s.encoding)
end

local function message(text, buttons)
    return aegisub.dialog.display({{class = "textbox", x = 0, y = 0, width = 70, height = 16, value = text}},
        buttons or {"Cerrar"})
end

-- ------------------------------------------------------------ configuracion ---
local function cfg_path() return DEFAULTS.workspace .. sep .. "studio.cfg" end

local function load_cfg()
    local cfg = {python = DEFAULTS.python, editor = DEFAULTS.editor, api_python = DEFAULTS.api_python,
        studio_app = DEFAULTS.studio_app, api_url = DEFAULTS.api_url, mode = "script"}
    local c = read_file(cfg_path())
    if c then
        for k, v in c:gmatch("([%w_]+)=([^\r\n]*)") do
            if v ~= "" then cfg[k] = v end
        end
    end
    return cfg
end

local function save_cfg(cfg)
    write_file(cfg_path(), string.format("python=%s\neditor=%s\napi_python=%s\nstudio_app=%s\napi_url=%s\nmode=%s\n",
        cfg.python, cfg.editor, cfg.api_python, cfg.studio_app, cfg.api_url, cfg.mode))
end

-- ------------------------------------------------------------ efectos ---
local function effects_dir() return DEFAULTS.workspace .. sep .. "effects" end

local function list_effects()
    local names = {}
    local cmd = is_win and ('dir /b "' .. effects_dir() .. '" 2>nul') or ("ls -1 " .. q(effects_dir()) .. " 2>/dev/null")
    local p = io.popen(cmd)
    if p then
        for f in p:lines() do
            local n = f:gsub("\r$", ""):match("^([^_][^/\\]*)%.py$")
            if n then names[#names + 1] = n end
        end
        p:close()
    end
    table.sort(names)
    return names
end

local ALL_STYLES = "(Todos los estilos)"

local function list_styles(subs)
    local names = {ALL_STYLES}
    for i = 1, #subs do
        local l = subs[i]
        if l.class == "style" then names[#names + 1] = l.name end
    end
    return names
end

local function slug(s)
    s = s:gsub("[^%w_%-]+", "_"):gsub("^_+", ""):gsub("_+$", "")
    return s
end

local function effect_path(name) return effects_dir() .. sep .. name .. ".py" end

-- Abre el editor y BLOQUEA hasta que lo cierras (code --wait / open -W).
local function open_editor(cfg, file)
    -- Se abre unicamente el .py del efecto (nunca la carpeta de efectos).
    local e = cfg.editor:lower()
    local vscode_like = e:find("code") or e:find("antigravity") or e:find("cursor") or e:find("windsurf")
    local cmd
    if vscode_like then
        -- Siempre ventana nueva: no reutilizar ni cerrar las ventanas/instancias ya abiertas.
        local editor = cfg.editor
        if not editor:find("%-%-new%-window") and not editor:find("%s%-n%s") then
            editor = editor:gsub("%s+%-%-wait", "") .. " --new-window --wait"
        end
        cmd = string.format("%s %s", editor, q(file))   -- solo el archivo: sin la carpeta, no se listan los demas efectos
    else
        cmd = string.format("%s %s", cfg.editor, q(file))
    end
    if is_win then cmd = '"' .. cmd .. '"' end
    os.execute(cmd)
end

-- ------------------------------------------------------------ ejecutar ---
-- Exporta a `f_in` el .ass que lee el motor (cabecera, estilos y las lineas a procesar).
-- Con estilo definido va a TODAS las lineas (no comentadas) de ese estilo; sin estilo, solo a las seleccionadas.
-- Devuelve idx_map (n-esima linea exportada -> indice real en subs) | nil, mensaje
local function export_session(subs, sel, eff_style, f_in)
    aegisub.progress.task("Exportando lineas...")
    local meta, styles = {}, {}
    for i = 1, #subs do
        local l = subs[i]
        if l.class == "info" then meta[l.key] = l.value
        elseif l.class == "style" then styles[#styles + 1] = l end
    end
    local sel_set = {}
    if eff_style then
        for i = 1, #subs do
            local l = subs[i]
            if l.class == "dialogue" and l.style == eff_style then sel_set[i] = true end
        end
    else
        for _, i in ipairs(sel) do sel_set[i] = true end
    end

    local out = {}
    out[#out + 1] = "[Script Info]\nScriptType: v4.00+"
    out[#out + 1] = "PlayResX: " .. (meta.PlayResX or "1280")
    out[#out + 1] = "PlayResY: " .. (meta.PlayResY or "720") .. "\n"
    out[#out + 1] = "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
    for _, st in ipairs(styles) do out[#out + 1] = style_line(st) end
    out[#out + 1] = "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"

    local idx_map = {}
    for i = 1, #subs do
        local l = subs[i]
        if l.class == "dialogue" and not l.comment and sel_set[i] and l.effect ~= "pyxis_fx" then
            idx_map[#idx_map + 1] = i
            out[#out + 1] = string.format("Dialogue: %d,%s,%s,%s,%s,%d,%d,%d,%s,%s",
                l.layer, ass_time(l.start_time), ass_time(l.end_time), l.style, l.actor,
                l.margin_l, l.margin_r, l.margin_t, l.effect, l.text)
        end
    end
    if #idx_map == 0 then
        if eff_style then
            return nil, "No hay lineas (no comentadas) con el estilo '" .. eff_style .. "'."
        end
        return nil, "Selecciona al menos una linea de karaoke (no comentario) y vuelve a ejecutar."
    end
    write_file(f_in, table.concat(out, "\n") .. "\n")
    return idx_map
end

-- Importa el resultado del motor (`#PYXIS_USED_IDX` + lineas Dialogue): comenta las lineas usadas y anade las nuevas.
local function import_result(subs, idx_map, result)
    local new_lines, used = {}, {}
    for line in result:gmatch("[^\r\n]+") do
        local idxs = line:match("^#PYXIS_USED_IDX:%s*(.*)$")
        if idxs then
            for n in idxs:gmatch("%d+") do
                local real = idx_map[tonumber(n)]
                if real then used[real] = true end
            end
        else
            local nl = parse_dialogue(line)
            if nl then new_lines[#new_lines + 1] = nl end
        end
    end
    if #new_lines == 0 then return nil, "No se generaron lineas (revisa el efecto o el grafo)." end

    local any = next(used) ~= nil
    for _, real in ipairs(idx_map) do
        if used[real] or not any then
            local l = subs[real]
            l.comment = true
            subs[real] = l
        end
    end
    for i, nl in ipairs(new_lines) do
        subs.append(nl)
        if i % 200 == 0 then aegisub.progress.set(100 * i / #new_lines) end
    end
    return true
end

-- Devuelve true | nil, mensaje_de_error
local function apply_effect(subs, sel, cfg, file, style)
    local base = aegisub.decode_path("?temp") .. sep .. "pyxis_fx_" .. os.time()
    local f_in, f_out, f_log = base .. "_in.ass", base .. "_out.ass", base .. ".log"

    -- Estilo efectivo: el del desplegable o, si no, el `STYLE = "..."` del propio efecto.
    local eff_style = (style and style ~= "" and style ~= ALL_STYLES) and style or nil
    if not eff_style then
        local src = read_file(file) or ""
        eff_style = src:match('\n%s*STYLE%s*=%s*"([^"\n]+)"') or src:match('^%s*STYLE%s*=%s*"([^"\n]+)"')
    end
    local idx_map, err = export_session(subs, sel, eff_style, f_in)
    if not idx_map then return nil, err end

    aegisub.progress.task("Ejecutando efecto...")
    local runtime = DEFAULTS.workspace .. sep .. "pyxis_fx.py"
    -- Estilo elegido en el dialogo -> --style (el efecto solo se aplica a lineas de ese estilo)
    local style_arg = ""
    if style and style ~= "" and style ~= ALL_STYLES then style_arg = " --style " .. q(style) end
    local cmd = string.format("%s %s --effect %s --ass %s --out %s%s > %s 2>&1",
        q(cfg.python), q(runtime), q(file), q(f_in), q(f_out), style_arg, q(f_log))
    if is_win then cmd = '"' .. cmd .. '"' end
    os.execute(cmd)

    local result = read_file(f_out)
    local log = read_file(f_log) or "sin salida"
    pcall(os.remove, f_in); pcall(os.remove, f_out); pcall(os.remove, f_log)
    if not result then
        return nil, "El efecto fallo.\nPython: " .. cfg.python ..
            "\n(requiere `pip install pyxis-core` en ese Python; cambialo en Configuracion)\n\n" .. log
    end
    return import_result(subs, idx_map, result)
end

-- Ciclo: abrir editor (opcional) -> al cerrar, ejecutar -> si falla, volver al editor.
local function edit_and_apply(subs, sel, cfg, name, edit_first, style)
    local file = effect_path(name)
    local need_edit = edit_first
    while true do
        if need_edit then open_editor(cfg, file) end
        local ok, err = apply_effect(subs, sel, cfg, file, style)
        if ok then
            aegisub.set_undo_point("Pyxis FX: " .. name)
            return true
        end
        local btn = message(err, {"Editar de nuevo", "Reintentar", "Cerrar"})
        if btn == "Editar de nuevo" then need_edit = true
        elseif btn == "Reintentar" then need_edit = false
        else return false end
    end
end

-- ------------------------------------------------------------ modo nodos ---
-- Modo "Nodos": se levanta la API (FastAPI sobre pyxis-core), se le pasa el .ass exportado y se abre la app
-- Pyxis Studio (Flutter). Al cerrar la app, el resultado que dejo (`<ass>.pyxis.ass`) se importa a Aegisub.
local function sh(cmd)
    if is_win then cmd = '"' .. cmd .. '"' end
    return os.execute(cmd)
end

local function tmp_name(ext)
    return aegisub.decode_path("?temp") .. sep .. "pyxis_nodes_" .. os.time() .. "_" .. math.random(1000, 9999) .. ext
end

local function api_up(cfg)
    local out = tmp_name(".txt")
    sh(string.format("curl -s -m 2 %s > %s 2>&1", q(cfg.api_url .. "/api/v1/health"), q(out)))
    local r = read_file(out) or ""
    pcall(os.remove, out)
    return r:find('"status"%s*:%s*"ok"') ~= nil
end

-- Devuelve true, empezo_el_daemon | false, mensaje
local function ensure_api(cfg)
    if api_up(cfg) then return true, false end
    if not exists(cfg.api_python) then
        return false, "No se encontro el Python de la API:\n" .. cfg.api_python .. "\n(cambialo en Configuracion)"
    end
    local port = cfg.api_url:match(":(%d+)") or "28723"
    local log = tmp_name(".log")
    if is_win then
        sh(string.format('start /B "" %s -m pyxis_api --port %s > %s 2>&1', q(cfg.api_python), port, q(log)))
    else
        sh(string.format("nohup %s -m pyxis_api --port %s > %s 2>&1 &", q(cfg.api_python), port, q(log)))
    end
    for _ = 1, 25 do
        if api_up(cfg) then return true, true end
        sh(is_win and "ping -n 2 127.0.0.1 > nul" or "sleep 1")
    end
    return false, "La API no arranco.\n\n" .. (read_file(log) or "sin salida")
end

local function launch_nodes(subs, sel, cfg, style)
    if not exists(cfg.studio_app) then
        message("No se encontro la app Pyxis Studio:\n" .. cfg.studio_app .. "\n(compilala con `flutter build` y ajusta la ruta en Configuracion)")
        return false
    end
    local eff_style = (style and style ~= "" and style ~= ALL_STYLES) and style or nil
    local f_in = tmp_name(".ass")
    local f_out = f_in:gsub("%.ass$", "") .. ".pyxis.ass"
    local idx_map, err = export_session(subs, sel, eff_style, f_in)
    if not idx_map then message(err); return false end

    aegisub.progress.task("Iniciando la API de Pyxis...")
    local ok, started = ensure_api(cfg)
    if not ok then pcall(os.remove, f_in); message(started); return false end

    -- sesion: la app lee el .ass activo desde la API
    local body = tmp_name(".json")
    local function jstr(t) return '"' .. t:gsub("\\", "\\\\"):gsub('"', '\\"') .. '"' end
    -- el estilo es la clave de la cache: el grafo ejecutado se recupera la proxima vez que se abra con ese estilo
    write_file(body, '{"ass_path": ' .. jstr(f_in) .. ', "style": ' .. (eff_style and jstr(eff_style) or "null") .. "}")
    sh(string.format("curl -s -m 10 -X POST -H %s -d @%s %s > %s 2>&1", q("content-type: application/json"), q(body),
        q(cfg.api_url .. "/api/v1/session/open"), q(body .. ".out")))
    local sess = read_file(body .. ".out") or ""
    pcall(os.remove, body); pcall(os.remove, body .. ".out")
    if not sess:find("lines_count", 1, true) then
        pcall(os.remove, f_in)
        message("No se pudo abrir la sesion en la API:\n" .. sess)
        return false
    end

    aegisub.progress.task("Pyxis Studio abierto: edita el grafo, pulsa Ejecutar y cierra la app.")
    if is_win then
        sh(string.format('set "PYXIS_API=%s" && %s', cfg.api_url, q(cfg.studio_app)))
    elseif cfg.studio_app:match("%.app/?$") then
        sh(string.format("open -W -n --env PYXIS_API=%s %s", q(cfg.api_url), q(cfg.studio_app)))
    else
        sh(string.format("PYXIS_API=%s %s", q(cfg.api_url), q(cfg.studio_app)))
    end

    if started then   -- solo se apaga el daemon si lo arranco este macro
        sh(string.format("curl -s -m 3 -X POST %s > %s 2>&1", q(cfg.api_url .. "/api/v1/session/shutdown"), is_win and "nul" or "/dev/null"))
    end
    local result = read_file(f_out)
    pcall(os.remove, f_in); pcall(os.remove, f_out)
    if not result then
        message("No hay resultado: en Pyxis Studio pulsa Ejecutar antes de cerrar la app.")
        return false
    end
    local done, ierr = import_result(subs, idx_map, result)
    if not done then message(ierr); return false end
    aegisub.set_undo_point("Pyxis FX: nodos")
    return true
end

-- ------------------------------------------------------------ interfaz ---
local function settings_dialog(cfg)
    local btn, res = aegisub.dialog.display({
        {class = "label", x = 0, y = 0, width = 2, label = "Configuracion"},
        {class = "label", x = 0, y = 1, label = "Editor (con --wait):"},
        {class = "edit", x = 1, y = 1, width = 40, name = "editor", value = cfg.editor},
        {class = "label", x = 0, y = 2, label = "Python (scripts):"},
        {class = "edit", x = 1, y = 2, width = 40, name = "python", value = cfg.python},
        {class = "label", x = 0, y = 3, label = "Python de la API:"},
        {class = "edit", x = 1, y = 3, width = 40, name = "api_python", value = cfg.api_python},
        {class = "label", x = 0, y = 4, label = "URL de la API:"},
        {class = "edit", x = 1, y = 4, width = 40, name = "api_url", value = cfg.api_url},
        {class = "label", x = 0, y = 5, label = "App Pyxis Studio:"},
        {class = "edit", x = 1, y = 5, width = 40, name = "studio_app", value = cfg.studio_app},
        {class = "label", x = 0, y = 6, width = 2, label = "Carpeta de trabajo: " .. DEFAULTS.workspace},
    }, {"Guardar", "Cancelar"})
    if btn == "Guardar" then
        cfg.editor, cfg.python, cfg.api_python, cfg.api_url, cfg.studio_app =
            res.editor, res.python, res.api_python, res.api_url, res.studio_app
        save_cfg(cfg)
    end
end

-- Libreria de efectos de Kara Effector 3.6 (3946 efectos, en Python). Se consulta con pyxis_fx.py:
--   --counts, --list-fx --kind K --search TEXTO --limit N, --fx-source NOMBRE --kind K

local function run_fx(cfg, args, ext)
    local tmp = aegisub.decode_path("?temp") .. sep .. "pyxis_fxq_" .. os.time() .. "_" .. math.random(1000, 9999) .. ext
    local cmd = string.format("%s %s %s > %s 2>&1", q(cfg.python), q(DEFAULTS.workspace .. sep .. "pyxis_fx.py"), args, q(tmp))
    if is_win then cmd = '"' .. cmd .. '"' end
    os.execute(cmd)
    local content = read_file(tmp) or ""
    pcall(os.remove, tmp)
    return content
end

local function create_effect(subs, sel, cfg, name, style)
    name = slug(name or "")
    if name == "" then message("Nombre invalido."); return false end
    local file = effect_path(name)
    if exists(file) then
        message("Ya existe un efecto llamado '" .. name .. "'. Elige otro nombre o usa 'Editar efecto'.")
        return false
    end
    -- el codigo base vive en un .py externo editable: <workspace>/effect_base.py
    local base = read_file(DEFAULTS.workspace .. sep .. "effect_base.py")
    write_file(file, build_effect(subs, name, style, base))
    -- el macro ya genero el efecto: abre el editor para retocarlo y, al cerrarlo, lo aplica
    return edit_and_apply(subs, sel, cfg, name, true, nil)
end

local PAGE_SIZE = 5

local function checked_list(names, checked)
    local out = {}
    for _, n in ipairs(names) do
        if checked[n] then out[#out + 1] = n end
    end
    return out
end

-- Lista paginada (5 por pagina) con checkboxes; las acciones van sobre los marcados.
local function open_existing(subs, sel, cfg, styles)
    local checked, page, style = {}, 1, styles[1]
    while true do
        local names = list_effects()
        if #names == 0 then message("Todavia no hay efectos creados."); return false end
        local pages = math.ceil(#names / PAGE_SIZE)
        if page > pages then page = pages end
        if page < 1 then page = 1 end
        local first = (page - 1) * PAGE_SIZE + 1
        local last = math.min(first + PAGE_SIZE - 1, #names)

        local dlg = {
            {class = "label", x = 0, y = 0, width = 2,
             label = string.format("Efectos creados: %d   (pagina %d de %d)", #names, page, pages)},
        }
        for i = first, last do
            dlg[#dlg + 1] = {class = "checkbox", x = 0, y = i - first + 1, width = 2,
                             name = "c" .. i, label = names[i], value = checked[names[i]] or false}
        end
        local yy = PAGE_SIZE + 1
        dlg[#dlg + 1] = {class = "label", x = 0, y = yy, label = "Estilo:"}
        dlg[#dlg + 1] = {class = "dropdown", x = 1, y = yy, width = 20, name = "style", items = styles, value = style}

        local buttons = {"Editar", "Ejecutar", "Eliminar"}
        if page > 1 then buttons[#buttons + 1] = "< Anterior" end
        if page < pages then buttons[#buttons + 1] = "Siguiente >" end
        buttons[#buttons + 1] = "Volver"

        local btn, res = aegisub.dialog.display(dlg, buttons)
        if not btn or btn == "Volver" then return false end

        -- recordar lo marcado (tambien al cambiar de pagina)
        for i = first, last do checked[names[i]] = res["c" .. i] and true or nil end
        style = res.style
        local marked = checked_list(names, checked)

        if btn == "< Anterior" then page = page - 1
        elseif btn == "Siguiente >" then page = page + 1
        elseif #marked == 0 then
            message("Marca al menos un efecto.")
        elseif btn == "Editar" then
            if #marked > 1 then
                message("Para editar marca un solo efecto.")
            else
                return edit_and_apply(subs, sel, cfg, marked[1], true, style)
            end
        elseif btn == "Ejecutar" then
            for _, n in ipairs(marked) do
                if not edit_and_apply(subs, sel, cfg, n, false, style) then return false end
            end
            return true
        elseif btn == "Eliminar" then
            local c = aegisub.dialog.display({
                {class = "label", x = 0, y = 0, label = "Eliminar " .. #marked .. " efecto(s)?\n\n" ..
                    table.concat(marked, "\n") .. "\n\nSe borran los archivos y no se puede deshacer."},
            }, {"Eliminar", "Cancelar"})
            if c == "Eliminar" then
                for _, n in ipairs(marked) do
                    local ok, err = os.remove(effect_path(n))
                    if not ok then message("No se pudo eliminar " .. n .. ":\n" .. tostring(err)) end
                    checked[n] = nil
                end
            end
        end
    end
end

-- ------------------------------------------------------------ presentacion ---
-- Los dialogos de Aegisub no admiten imagenes, colores ni tamanos de letra: el diseno se limita a texto limpio,
-- columnas del mismo ancho y poca decoracion.
local TITLE = "P Y X I S    E F F E C T    S T U D I O"

local function mark(ok) return ok and "✔" or "✘" end

local function editor_path(editor)
    return editor:match('^%s*"([^"]+)"') or editor:match("^%s*(%S+)") or ""
end

local function plural(n, one, many) return n .. " " .. (n == 1 and one or many) end

-- Resumen del archivo abierto
local function project_summary(subs, sel)
    local n_lines, n_styles, rx, ry = 0, 0, "?", "?"
    for i = 1, #subs do
        local l = subs[i]
        if l.class == "dialogue" and not l.comment then n_lines = n_lines + 1
        elseif l.class == "style" then n_styles = n_styles + 1
        elseif l.class == "info" then
            if l.key == "PlayResX" then rx = l.value elseif l.key == "PlayResY" then ry = l.value end
        end
    end
    return string.format("%s   ·   %s   ·   %s×%s   ·   %s", plural(n_lines, "línea", "líneas"),
        plural(n_styles, "estilo", "estilos"), rx, ry, plural(#sel, "seleccionada", "seleccionadas"))
end

local function install_status(cfg)
    return string.format("Instalación:   %s Python     %s Editor     %s API     %s Pyxis Studio",
        mark(exists(cfg.python)), mark(exists(editor_path(cfg.editor))), mark(exists(cfg.api_python)), mark(exists(cfg.studio_app)))
end

-- Modo SCRIPT: crear/editar efectos en Python con tu editor.
local function script_studio(subs, sel, cfg, styles)
    while true do
        local btn, res = aegisub.dialog.display({
            {class = "label", x = 0, y = 0, width = 8, height = 2, label = TITLE .. "\nModo Script  —  efectos en código Python"},
            {class = "label", x = 0, y = 2, width = 8, height = 2,
             label = "Se genera un archivo .py con el efecto completo para el estilo elegido\ny se abre en tu editor. Al cerrarlo, se aplica en Aegisub."},
            {class = "label", x = 0, y = 4, label = "Nombre"},
            {class = "edit", x = 1, y = 4, width = 7, name = "name", value = ""},
            {class = "label", x = 0, y = 5, label = "Estilo"},
            {class = "dropdown", x = 1, y = 5, width = 7, name = "style", items = styles, value = styles[1]},
            {class = "label", x = 0, y = 6, width = 8, label = "Crear efecto: uno nuevo en blanco      Editar efecto: abrir, ejecutar o eliminar"},
        }, {"Crear efecto", "Editar efecto", "Volver"})

        if btn == "Crear efecto" then
            if create_effect(subs, sel, cfg, res.name, res.style) then return true end
        elseif btn == "Editar efecto" then
            if open_existing(subs, sel, cfg, styles) then return true end
        else
            return false
        end
    end
end

-- Modo NODOS: se elige el estilo y se abre la app Flutter (Pyxis Studio) con la API de pyxis-core.
local function nodes_studio(subs, sel, cfg, styles)
    local btn, res = aegisub.dialog.display({
        {class = "label", x = 0, y = 0, width = 8, height = 2, label = TITLE .. "\nModo Nodos  —  grafo visual en Pyxis Studio"},
        {class = "label", x = 0, y = 2, width = 8, height = 5,
         label = "1   Se abre Pyxis Studio (la API arranca sola)\n" ..
                 "2   Arma el grafo con nodos o carga una plantilla\n" ..
                 "3   Pulsa Ejecutar: se guarda y la app se cierra\n" ..
                 "4   Las líneas generadas se pegan en Aegisub\n" ..
                 "Tu último grafo de este estilo se recupera al volver a abrir."},
        {class = "label", x = 0, y = 7, label = "Estilo"},
        {class = "dropdown", x = 1, y = 7, width = 7, name = "style", items = styles, value = styles[1]},
        {class = "label", x = 0, y = 8, width = 8, label = install_status(cfg)},
    }, {"Abrir Pyxis Studio", "Volver"})
    if btn ~= "Abrir Pyxis Studio" then return false end
    return launch_nodes(subs, sel, cfg, res.style)
end

local REPO_URL = "https://github.com/Mandholine/Pyxis-Effector"


local function open_url(target)
    if package.config:sub(1, 1) == "\\" then
        os.execute('start "" "' .. target .. '"')
    else
        local p = io.popen("uname")
        local os_name = p and p:read("*l") or ""
        if p then p:close() end
        os.execute((os_name == "Darwin" and "open " or "xdg-open ") .. '"' .. target .. '"')
    end
end

local LINE = string.rep("─", 58)

-- Acerca de: descripcion, agradecimientos y repositorio (todo dentro del dialogo de Aegisub).
local function about_dialog()
    local btn = aegisub.dialog.display({
        {class = "label", x = 0, y = 0, width = 10, height = 2, label = TITLE .. "\nAcerca de   ·   v" .. script_version},
        {class = "label", x = 0, y = 2, width = 10, label = LINE},
        {class = "label", x = 0, y = 3, width = 10, height = 3,
         label = "Pyxis Effector es software libre para crear efectos de karaoke\n" ..
                 "con Python o con un editor visual de nodos, integrado en Aegisub.\n" ..
                 "Motor: pyxis-core   ·   API local   ·   App: Pyxis Studio"},
        {class = "label", x = 0, y = 6, width = 10, label = LINE},
        {class = "label", x = 0, y = 7, width = 10, label = "AGRADECIMIENTOS"},
        {class = "label", x = 0, y = 8, width = 10, height = 5,
         label = "★  Trota            desarrollo y motor de efectos\n" ..
                 "★  Zagon           desarrollo y pruebas\n" ..
                 "★  Pedro Holguin   pyxis-core, API y Pyxis Studio\n" ..
                 "★  La comunidad de Aegisub y de karaoke, por probar,\n" ..
                 "     reportar errores y compartir plantillas"},
        {class = "label", x = 0, y = 13, width = 10, label = LINE},
        {class = "label", x = 0, y = 14, width = 10, label = "REPOSITORIO EN GITHUB   (puedes copiar el enlace)"},
        {class = "edit", x = 0, y = 15, width = 10, name = "url", value = REPO_URL},
    }, {"Abrir GitHub", "Volver"})
    if btn == "Abrir GitHub" then open_url(REPO_URL) end
end

-- Primera pantalla: como quieres trabajar. Dos columnas del mismo ancho y alto.
local function studio(subs, sel)
    local cfg = load_cfg()
    local styles = list_styles(subs)
    while true do
        local btn = aegisub.dialog.display({
            {class = "label", x = 0, y = 0, width = 10, height = 2, label = TITLE .. "\nEfectos de karaoke con Python y nodos   ·   v" .. script_version},

            {class = "label", x = 0, y = 2, width = 5, height = 7,
             label = "MODO SCRIPT\n" ..
                     "Efectos escritos en Python.\n\n" ..
                     "•  Se editan en tu editor de código\n" ..
                     "•  Control total de tiempos y tags\n" ..
                     "•  Basado en pyxis-core"},
            {class = "label", x = 5, y = 2, width = 5, height = 7,
             label = "MODO NODOS\n" ..
                     "Grafo visual en la app Pyxis Studio.\n\n" ..
                     "•  Plantillas listas para usar\n" ..
                     "•  Progreso y cancelación en vivo\n" ..
                     "•  Guarda tu último grafo por estilo"},

            {class = "label", x = 0, y = 9, width = 10, label = install_status(cfg)},
            {class = "label", x = 0, y = 10, width = 10, label = "Con ♥ de Trota, Zagon y Pedro Holguin   ·   github.com/Mandholine/Pyxis-Effector"},
        }, {"Modo Script", "Modo Nodos", "Configuración", "Acerca de", "Cerrar"})

        if btn == "Modo Script" then
            if script_studio(subs, sel, cfg, styles) then return sel end
        elseif btn == "Modo Nodos" then
            if nodes_studio(subs, sel, cfg, styles) then return sel end
        elseif btn == "Configuración" then
            settings_dialog(cfg)
            cfg = load_cfg()
        elseif btn == "Acerca de" then
            about_dialog()
        else
            return sel
        end
    end
end

aegisub.register_macro(script_name, script_description, studio)
