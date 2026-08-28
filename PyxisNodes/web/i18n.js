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

(function (window) {
    "use strict";

    const TRANSLATIONS = {
        es: {
            "topbar.save": "Guardar",
            "topbar.save_tooltip": "Guardar cambios en la plantilla activa",
            "topbar.save_as": "Guardar como...",
            "topbar.save_as_tooltip": "Guardar como archivo externo (.json)",
            "topbar.library": "Biblioteca",
            "topbar.library_tooltip": "Abrir biblioteca de plantillas",
            "topbar.quick_save_tooltip": "Guardar cambios en plantilla de biblioteca",
            "topbar.settings_tooltip": "Ajustes y temas visuales",
            "topbar.generate": "Generar Capas",
            "topbar.cancelling": "Cancelando...",
            "topbar.generating": "Generando...",
            "topbar.lang_tooltip": "Cambiar idioma (Español / English)",

            "estimation.title": "Estimación de Carga",
            "estimation.calculating": "Calculando...",
            "estimation.lines_to_generate": "Líneas a generar",
            "estimation.base_units": "Unidades base",
            "estimation.input_lines": "Líneas entrada",
            "estimation.complexity": "Complejidad",
            "estimation.complexity_low": "Baja",
            "estimation.complexity_med": "Media",
            "estimation.complexity_high": "Alta",

            "toolbar.undo": "Deshacer (Ctrl+Z)",
            "toolbar.redo": "Rehacer (Ctrl+Y)",
            "toolbar.reset_view": "Centrar vista (Inicio)",
            "toolbar.zoom_in": "Acercar (+)",
            "toolbar.zoom_out": "Alejar (-)",
            "toolbar.load_default": "Restablecer preset por defecto",

            "settings.title": "Ajustes & Temas Visuales",
            "settings.themes_section": "Temas Visuales de la Interfaz:",
            "settings.create_theme": "Crear Nuevo Tema",
            "settings.saved_by_you": "Guardados por ti",
            "settings.presets": "Temas Predefinidos",
            "settings.badge_custom": "Personalizado",
            "settings.edit_theme": "Editar este tema",
            "settings.delete_theme": "Eliminar este tema",
            "settings.canvas_section": "Personalización del Canvas & Medios de Fondo",
            "settings.daemon": "Persistencia en Segundo Plano:",
            "settings.daemon_desc": "Apertura instantánea (0ms) tras la primera vez",
            "settings.daemon_tooltip": "Mantiene el servidor Python en segundo plano (~60MB RAM) para que Pyxis abra de forma instantánea (0ms) desde Aegisub.",
            "settings.language": "Idioma de la Interfaz:",
            "settings.lang_es": "Español",
            "settings.lang_en": "Inglés (English)",
            "settings.grid_style": "Estilo de Rejilla:",
            "settings.grid_lines": "Líneas",
            "settings.grid_dots": "Puntos (Defecto)",
            "settings.grid_disabled": "Desactivado",
            "settings.undo_steps": "Pasos de Deshacer / Rehacer (Undo/Redo):",
            "settings.canvas_bg": "Fondo del Canvas (Imagen o Video Cíclico):",
            "settings.canvas_bg_formats": "Soporta MP4, WebM, MOV, MKV, PNG, JPG, WebP",
            "settings.browse": "Examinar...",
            "settings.remove": "Quitar",
            "settings.bg_none": "Ninguno seleccionado",
            "settings.bg_default": "Fondo por defecto (default_back.webp)",
            "settings.bg_video": "Video en bucle activo (Acelerado por GPU)",
            "settings.bg_image": "Imagen cargada",
            "settings.optimize_video": "Convertir / Optimizar Video con FFmpeg",
            "settings.optimize_video_tooltip": "Optimiza el video a formato H.264/MP4 ligero sin audio para máxima fluidez y mínimo consumo de GPU/CPU.",
            "settings.opacity": "Opacidad del Fondo:",
            "settings.fit_mode": "Modo de Ajuste:",
            "settings.fit_cover": "Rellenar",
            "settings.fit_contain": "Ajustar",
            "settings.fit_stretch": "Estirar",
            "settings.fit_tile": "Mosaico",
            "settings.fit_center": "Centro",
            "settings.clean_temp": "Limpiar Temporales (> 72h)",

            "theme_editor.title_new": "Crear Nuevo Tema Personalizado",
            "theme_editor.title_edit": "Editar Tema Personalizado",
            "theme_editor.name": "Nombre del Tema:",
            "theme_editor.desc": "Descripción:",
            "theme_editor.canvas_bg": "Color de Fondo del Lienzo:",
            "theme_editor.panel_bg": "Color de Paneles y Diálogos:",
            "theme_editor.topbar_bg": "Color de Barra Superior:",
            "theme_editor.card_bg": "Color de Tarjetas / Widgets:",
            "theme_editor.text_main": "Texto Principal:",
            "theme_editor.text_muted": "Texto Atenuado:",
            "theme_editor.accent_primary": "Color Primario de Acento:",
            "theme_editor.accent_secondary": "Color Secundario de Acento:",
            "theme_editor.border_subtle": "Color de Bordes Sutiles:",
            "theme_editor.cancel": "Cancelar",
            "theme_editor.save": "Guardar Tema",
            "theme_editor.delete_confirm_title": "Eliminar Tema Personalizado",
            "theme_editor.delete_confirm_msg": "¿Estás seguro de que deseas eliminar permanentemente el tema <strong>\"{name}\"</strong>? Esta acción no se puede deshacer.",
            "theme_editor.delete_btn": "Eliminar Tema",

            "library.title": "Biblioteca de Templates",
            "library.search_placeholder": "Buscar templates...",
            "library.tab_all": "Todos",
            "library.tab_favorites": "Favoritos",
            "library.tab_recent": "Recientes",
            "library.tab_system": "Sistema",
            "library.empty": "No se encontraron templates.",
            "library.empty_desc": "Guarda tus grafos de nodos como templates para reutilizarlos en cualquier momento.",
            "library.load": "Cargar Plantilla",
            "library.export": "Exportar",
            "library.delete": "Eliminar",
            "library.close": "Cerrar",
            "library.last_used": "Último usado",
            "library.favorite_title": "Marcar como favorito",
            "library.save_modal_title": "Guardar Plantilla en Biblioteca",
            "library.tpl_name": "Nombre de la plantilla:",
            "library.tpl_desc": "Descripción (opcional):",
            "library.tpl_tags": "Etiquetas (separadas por comas):",
            "library.unsaved_title": "Cambios sin guardar",
            "library.unsaved_msg": "El grafo actual tiene cambios que se perderán al cargar otra plantilla.",
            "library.discard": "Descartar cambios",
            "library.save_and_continue": "Guardar en biblioteca y cargar",
            "library.overwrite_title": "Sobrescribir plantilla existente",
            "library.overwrite_msg": "Ya existe una plantilla activa: <strong>\"{name}\"</strong>.<br>¿Deseas sobrescribirla o guardar una nueva?",
            "library.overwrite_btn": "Sobrescribir activa",
            "library.save_as_new_lib": "Guardar como nueva en biblioteca",
            "library.save_as_disk": "Guardar como archivo en disco (.json)",

            "code_editor.title_script": "Editor de Código Script",
            "code_editor.title_vars": "Editor de Variables",
            "code_editor.templates": "Plantillas:",
            "code_editor.select_template": "-- Seleccionar plantilla --",
            "code_editor.save_template": "Guardar Plantilla",
            "code_editor.save_template_tooltip": "Guardar el script actual como plantilla reutilizable",
            "code_editor.delete_template": "Borrar Plantilla",
            "code_editor.delete_template_tooltip": "Eliminar la plantilla personalizada seleccionada",
            "code_editor.cancel": "Cancelar",
            "code_editor.save": "Guardar",

            "color_picker.title": "Selector de Color Profesional",
            "color_picker.cancel": "Cancelar",
            "color_picker.save": "Guardar Color",

            "common.cancel": "Cancelar",
            "common.save": "Guardar",
            "common.confirm": "Confirmar",
            "common.close": "Cerrar",
            "common.delete": "Eliminar",
            "common.error": "Error",
            "common.success": "Éxito",
            "common.loading": "Cargando...",

            "toast.theme_saved_applied": "Tema \"{name}\" guardado y aplicado",
            "toast.theme_saved": "Tema \"{name}\" guardado en la lista",
            "toast.theme_deleted": "Tema \"{name}\" eliminado",
            "toast.template_saved": "Plantilla guardada con éxito",
            "toast.template_loaded": "Plantilla cargada: {name}",
            "toast.template_deleted": "Plantilla eliminada",
            "toast.lang_switched": "Idioma cambiado a {lang}",
            "toast.session_saved": "Sesión guardada",
            "toast.generation_started": "Iniciando generación de efectos...",
            "toast.generation_cancelled": "Generación cancelada por el usuario",
            "toast.generation_finished": "Generación completada con éxito",
            "toast.bg_cleared": "Fondo multimedia eliminado",
            "toast.bg_applied": "Nuevo fondo aplicado correctamente",

            // --- Categorías de Nodos ---
            "nodes.categories.Loops": "Bucles",
            "nodes.categories.Variables": "Variables",
            "nodes.categories.System": "Sistema",
            "nodes.categories.Functions": "Funciones",
            "nodes.categories.Shape": "Formas",
            "nodes.categories.Time": "Tiempo",
            "nodes.categories.Audio": "Audio",
            "nodes.categories.Math": "Mates",
            "nodes.categories.Text": "Texto",

            // --- Títulos de Nodos ---
            "nodes.titles.Main Loop": "Bucle Primario",
            "nodes.titles.MaxLoop": "Bucle Máximo",
            "nodes.titles.Maxloop": "Bucle Máximo",
            "nodes.titles.Module": "Módulo",
            "nodes.titles.Define Vars": "Definir Vars",
            "nodes.titles.Get Var": "Obtener Var",
            "nodes.titles.Memory": "Memoria",
            "nodes.titles.Sys Var": "Sys Var",
            "nodes.titles.Output": "Salida",
            "nodes.titles.Previewer": "Previsualizador",
            "nodes.titles.Script Code": "Código Script",
            "nodes.titles.Benchmark Math": "Benchmark Math",
            "nodes.titles.Interpolator": "Interpolador",
            "nodes.titles.Conditioner": "Condicionador",
            "nodes.titles.Bezier Curve": "Curva Bézier",
            "nodes.titles.Color Gradient": "Gradiente Color",
            "nodes.titles.Color Picker": "Selector de Color",
            "nodes.titles.Particles": "Partículas",
            "nodes.titles.IMG to Pixels": "Imagen a Partículas",
            "nodes.titles.IMG to pixels": "Imagen a Partículas",
            "nodes.titles.IMG to Shape": "Imagen a Forma",
            "nodes.titles.Text to Shape": "Text to Shape",
            "nodes.titles.Polar to Cartesian": "Polares a Cartesiana",
            "nodes.titles.Tag Oscillator": "Tag Oscilador",
            "nodes.titles.Shapes Library": "Shapes Lib",
            "nodes.titles.Shape Slicer": "Shape Slicer",
            "nodes.titles.Shape Transform": "Trans. Shape",
            "nodes.titles.Concentric Borders": "Bordes Concéntricos",
            "nodes.titles.Clip Gradient": "Clip Gradient",
            "nodes.titles.Time Ipol": "Ipol Tiempos",
            "nodes.titles.Synced Time": "Tiempo Sincronizado",
            "nodes.titles.Lead In": "Lead In",
            "nodes.titles.Lead Out": "Lead Out",
            "nodes.titles.Middle 1": "Middle 1",
            "nodes.titles.Middle 2": "Middle 2",
            "nodes.titles.Loop 1": "Loop 1",
            "nodes.titles.Loop 2": "Loop 2",
            "nodes.titles.Offset": "Offset",
            "nodes.titles.Duration": "Duración",
            "nodes.titles.Parse ASS Time": "Parse ASS Time",
            "nodes.titles.Format ASS Time": "Format ASS Time",
            "nodes.titles.Audio Modulator": "Audio Modulador",
            "nodes.titles.Audio Waveform": "Audio Waveform",
            "nodes.titles.Number": "Número",
            "nodes.titles.Concatenate": "Concatenar",
            "nodes.titles.Dynamic Format": "Format Dinámico",
            "nodes.titles.MultiTag": "MultiTag",
            "nodes.titles.MultiRandom": "MultiRandom",
            "nodes.titles.Math": "Mates",
            "nodes.titles.Text": "String",
            "nodes.titles.String": "String",

            // --- Slots (Entradas / Salidas) ---
            "nodes.slots.Loop": "Bucle",
            "nodes.slots.Loop In": "Bucle In",
            "nodes.slots.Loop Out": "Bucle Out",
            "nodes.slots.Loop / Domain": "Bucle / Dominio",
            "nodes.slots.Iterator (i)": "Iterador (i)",
            "nodes.slots.Iterator (j)": "Iterador (j)",
            "nodes.slots.Total (N)": "Total (N)",
            "nodes.slots.Iterations (N)": "Vueltas (N)",
            "nodes.slots.Sub-step (m)": "Sub-paso (m)",
            "nodes.slots.Flow In": "Flujo In",
            "nodes.slots.Flow Out": "Flujo Out",
            "nodes.slots.Result": "Resultado",
            "nodes.slots.Output": "Salida",
            "nodes.slots.Data": "Dato",
            "nodes.slots.Value": "Valor",
            "nodes.slots.Current Value": "Valor Actual",
            "nodes.slots.Duration (ms)": "Duración (ms)",
            "nodes.slots.Base (ms)": "Base (ms)",
            "nodes.slots.Delay (ms)": "Delay (ms)",
            "nodes.slots.Start Time (ms)": "Start Time (ms)",
            "nodes.slots.End Time (ms)": "End Time (ms)",
            "nodes.slots.ASS Time": "ASS Time",
            "nodes.slots.Time (ms)": "Tiempo (ms)",
            "nodes.slots.Offset (ms)": "Offset (ms)",
            "nodes.slots.Points / Values": "Puntos / Valores",
            "nodes.slots.Acceleration": "Aceleración",
            "nodes.slots.Start": "Inicio",
            "nodes.slots.End": "Fin",
            "nodes.slots.Step": "Paso",
            "nodes.slots.Width": "Ancho",
            "nodes.slots.Height": "Alto",
            "nodes.slots.Anchor": "Anclaje",
            "nodes.slots.Order": "Orden",
            "nodes.slots.Output Type": "Tipo Salida",
            "nodes.slots.Piece": "Pieza",
            "nodes.slots.Shape": "Forma",
            "nodes.slots.Shape / Text": "Forma / Texto",
            "nodes.slots.Bleed": "Sangrado",
            "nodes.slots.Angle": "Ángulo",
            "nodes.slots.Angle (°)": "Ángulo (°)",
            "nodes.slots.Seed": "Semilla",
            "nodes.slots.Separation": "Separación",
            "nodes.slots.Overlap": "Solape",
            "nodes.slots.Smoothing": "Suavizado",
            "nodes.slots.Frame": "Cuadro / Frame",
            "nodes.slots.Frame (j)": "Fotograma (j)",
            "nodes.slots.Density": "Densidad",
            "nodes.slots.Thickness": "Grosor",
            "nodes.slots.Radius": "Radio",
            "nodes.slots.Threshold": "Umbral",
            "nodes.slots.Tolerance": "Tolerancia",
            "nodes.slots.Condition": "Condición",
            "nodes.slots.If True": "Si Verdadero",
            "nodes.slots.If False": "Si Falso",
            "nodes.slots.Constant": "Constante",
            "nodes.slots.Key": "Clave",
            "nodes.slots.Font": "Fuente",
            "nodes.slots.Size": "Tamaño",
            "nodes.slots.Stripes": "Franjas",
            "nodes.slots.Rhythm Pattern": "Patron Ritmo",
            "nodes.slots.Audio Path": "Ruta Audio",
            "nodes.slots.Image Path": "Ruta Img",
            "nodes.slots.Particle": "Partícula",
            "nodes.slots.Index": "Índice",
            "nodes.slots.Progress (0-1)": "Progreso (0-1)",
            "nodes.slots.Base Mode": "Modo Base",
            "nodes.slots.Binarize Mode": "Modo Binariz",
            "nodes.slots.Dilate Step": "Dilat Paso",
            "nodes.slots.Dilate Trans": "Dilat Trans",
            "nodes.slots.Border Offset": "Offset Borde",
            "nodes.slots.Seq Offset": "Offset Seq",
            "nodes.slots.Color List": "Lista Colores",
            "nodes.slots.Image Scale": "Escala Img",
            "nodes.slots.Scale Out": "Escala Out",
            "nodes.slots.Scale": "Escala",
            "nodes.slots.Optimization": "Optimizacion",
            "nodes.slots.Max Rings": "Max Anillos",
            "nodes.slots.Max Extra": "Max Extra",
            "nodes.slots.Max Val": "Max Val",
            "nodes.slots.Min Val": "Min Val",
            "nodes.slots.Start Time": "Start Time",
            "nodes.slots.End Time": "End Time",
            "nodes.slots.Layer": "Capa",
            "nodes.slots.Tags": "Tags",
            "nodes.slots.Return": "Retorno",
            "nodes.slots.String": "Texto",

            // --- Placeholders, Badges y Canvas ---
            "nodes.placeholders.vars_empty": "(clic para definir vars...)",
            "nodes.placeholders.open_script_editor": "Abrir Editor Script",
            "nodes.placeholders.align": "Alineación",
            "nodes.badges.sel": "SELEC.",
            "nodes.badges.all": "TODO",
            "nodes.badges.style": "ESTILO",
            "nodes.badges.no_blank": "NO BLANK",
            "nodes.badges.with_blank": "CON BLANK",

            // --- MultiTag descripciones (ES) ---
            "nodes.tags.pos": "posición (x, y)",
            "nodes.tags.move": "movimiento (x1, y1 -> x2, y2)",
            "nodes.tags.org": "origen de rotación (x, y)",
            "nodes.tags.fad": "desvanecimiento simple (in, out)",
            "nodes.tags.fade": "desvanecimiento complejo (7 args)",
            "nodes.tags.clip": "máscara / dibujo vectorial",
            "nodes.tags.iclip": "máscara invertida",
            "nodes.tags.1c": "color primario",
            "nodes.tags.2c": "color secundario (karaoke)",
            "nodes.tags.3c": "color de borde",
            "nodes.tags.4c": "color de sombra",
            "nodes.tags.alpha": "transparencia general",
            "nodes.tags.1a": "transparencia primaria",
            "nodes.tags.2a": "transparencia secundaria",
            "nodes.tags.3a": "transparencia borde",
            "nodes.tags.4a": "transparencia sombra",
            "nodes.tags.fscx": "escala horizontal %",
            "nodes.tags.fscy": "escala vertical %",
            "nodes.tags.frz": "rotación z (ángulo)",
            "nodes.tags.frx": "rotación x (perspectiva)",
            "nodes.tags.fry": "rotación y (perspectiva)",
            "nodes.tags.fax": "cizallado / inclinación x",
            "nodes.tags.fay": "cizallado / inclinación y",
            "nodes.tags.bord": "ancho de borde",
            "nodes.tags.shad": "distancia de sombra",
            "nodes.tags.blur": "desenfoque gaussiano",
            "nodes.tags.be": "desenfoque de bordes",
            "nodes.tags.fs": "tamaño de fuente (px)",
            "nodes.tags.fsp": "espaciado de letras",
            "nodes.tags.an": "alineación (1-9)",
            "nodes.tags.b": "negrita (0/1)",
            "nodes.tags.i": "cursiva (0/1)",
            "nodes.tags.u": "subrayado (0/1)",
            "nodes.tags.s": "tachado (0/1)",
            "nodes.tags.k": "duración karaoke",
            "nodes.tags.kf": "relleno karaoke",
            "nodes.tags.ko": "borde karaoke",
            "nodes.tags.p": "modo dibujo (escala)",
            "nodes.tags.t": "transformación animada",

            // --- MultiRandom descripciones (ES) ---
            "nodes.randoms.rnd": "aleatorio básico (entero/flotante)",
            "nodes.randoms.rnd_sym": "aleatorio simétrico (+/-)",
            "nodes.randoms.rnd_skew": "aleatorio con curvatura",
            "nodes.randoms.rnd_choice": "elección en lista (comas)",
            "nodes.randoms.rnd_perlin": "ruido perlin 1D/2D",
            "nodes.randoms.rnd_step": "aleatorio cuantizado por pasos",
            "nodes.randoms.rnd_burst": "ráfaga / explosión aleatoria",
            "nodes.randoms.rnd_decay": "decaimiento exponencial",
            "nodes.randoms.rnd_gauss": "distribución gaussiana normal",
            "nodes.randoms.rnd_walk": "caminata aleatoria continua",
            "nodes.randoms.rnd_jitter": "vibración / temblor sutil",
            "nodes.randoms.rnd_shake": "sacudida fuerte / terremoto",
            "nodes.randoms.rnd_orbit": "desplazamiento orbital (r, theta)",
            "nodes.randoms.rnd_flicker": "parpadeo estroboscópico",
            "nodes.randoms.rnd_pulse": "pulso rítmico aleatorio"
        },
        en: {
            "topbar.save": "Save",
            "topbar.save_tooltip": "Save changes to active template",
            "topbar.save_as": "Save As...",
            "topbar.save_as_tooltip": "Save as external file (.json)",
            "topbar.library": "Library",
            "topbar.library_tooltip": "Open template library",
            "topbar.quick_save_tooltip": "Save changes to library template",
            "topbar.settings_tooltip": "Settings and visual themes",
            "topbar.generate": "Generate Layers",
            "topbar.cancelling": "Cancelling...",
            "topbar.generating": "Generating...",
            "topbar.lang_tooltip": "Switch language (Español / English)",

            "estimation.title": "Workload Estimation",
            "estimation.calculating": "Calculating...",
            "estimation.lines_to_generate": "Lines to generate",
            "estimation.base_units": "Base units",
            "estimation.input_lines": "Input lines",
            "estimation.complexity": "Complexity",
            "estimation.complexity_low": "Low",
            "estimation.complexity_med": "Medium",
            "estimation.complexity_high": "High",

            "toolbar.undo": "Undo (Ctrl+Z)",
            "toolbar.redo": "Redo (Ctrl+Y)",
            "toolbar.reset_view": "Center view (Home)",
            "toolbar.zoom_in": "Zoom In (+)",
            "toolbar.zoom_out": "Zoom Out (-)",
            "toolbar.load_default": "Reset to default preset",

            "settings.title": "Settings & Visual Themes",
            "settings.themes_section": "Interface Visual Themes:",
            "settings.create_theme": "Create New Theme",
            "settings.saved_by_you": "Saved by you",
            "settings.presets": "Preset Themes",
            "settings.badge_custom": "Custom",
            "settings.edit_theme": "Edit this theme",
            "settings.delete_theme": "Delete this theme",
            "settings.canvas_section": "Canvas Customization & Background Media",
            "settings.daemon": "Background Daemon Persistence:",
            "settings.daemon_desc": "Instant launch (0ms) after first startup",
            "settings.daemon_tooltip": "Keeps the Python server running in the background (~60MB RAM) for instant launch (0ms) from Aegisub.",
            "settings.language": "Interface Language:",
            "settings.lang_es": "Spanish (Español)",
            "settings.lang_en": "English",
            "settings.grid_style": "Grid Style:",
            "settings.grid_lines": "Lines",
            "settings.grid_dots": "Dots (Default)",
            "settings.grid_disabled": "Disabled",
            "settings.undo_steps": "Undo / Redo Steps:",
            "settings.canvas_bg": "Canvas Background (Image or Looping Video):",
            "settings.canvas_bg_formats": "Supports MP4, WebM, MOV, MKV, PNG, JPG, WebP",
            "settings.browse": "Browse...",
            "settings.remove": "Remove",
            "settings.bg_none": "None selected",
            "settings.bg_default": "Default background (default_back.webp)",
            "settings.bg_video": "Active video loop (GPU Accelerated)",
            "settings.bg_image": "Image loaded",
            "settings.optimize_video": "Convert / Optimize Video with FFmpeg",
            "settings.optimize_video_tooltip": "Optimizes video into lightweight audio-less H.264/MP4 for maximum fluidity and minimal CPU/GPU usage.",
            "settings.opacity": "Background Opacity:",
            "settings.fit_mode": "Fit Mode:",
            "settings.fit_cover": "Fill",
            "settings.fit_contain": "Fit",
            "settings.fit_stretch": "Stretch",
            "settings.fit_tile": "Tile",
            "settings.fit_center": "Center",
            "settings.clean_temp": "Clean Temp Files (> 72h)",

            "theme_editor.title_new": "Create New Custom Theme",
            "theme_editor.title_edit": "Edit Custom Theme",
            "theme_editor.name": "Theme Name:",
            "theme_editor.desc": "Description:",
            "theme_editor.canvas_bg": "Canvas Background Color:",
            "theme_editor.panel_bg": "Panels & Dialogs Background Color:",
            "theme_editor.topbar_bg": "Topbar Background Color:",
            "theme_editor.card_bg": "Cards & Widgets Color:",
            "theme_editor.text_main": "Main Text Color:",
            "theme_editor.text_muted": "Muted Text Color:",
            "theme_editor.accent_primary": "Primary Accent Color:",
            "theme_editor.accent_secondary": "Secondary Accent Color:",
            "theme_editor.border_subtle": "Subtle Border Color:",
            "theme_editor.cancel": "Cancel",
            "theme_editor.save": "Save Theme",
            "theme_editor.delete_confirm_title": "Delete Custom Theme",
            "theme_editor.delete_confirm_msg": "Are you sure you want to permanently delete the theme <strong>\"{name}\"</strong>? This action cannot be undone.",
            "theme_editor.delete_btn": "Delete Theme",

            "library.title": "Template Library",
            "library.search_placeholder": "Search templates...",
            "library.tab_all": "All",
            "library.tab_favorites": "Favorites",
            "library.tab_recent": "Recent",
            "library.tab_system": "System",
            "library.empty": "No templates found.",
            "library.empty_desc": "Save your node graphs as templates to reuse them anytime.",
            "library.load": "Load Template",
            "library.export": "Export",
            "library.delete": "Delete",
            "library.close": "Close",
            "library.last_used": "Last used",
            "library.favorite_title": "Mark as favorite",
            "library.save_modal_title": "Save Template to Library",
            "library.tpl_name": "Template name:",
            "library.tpl_desc": "Description (optional):",
            "library.tpl_tags": "Tags (comma separated):",
            "library.unsaved_title": "Unsaved changes",
            "library.unsaved_msg": "The current graph has changes that will be lost when loading another template.",
            "library.discard": "Discard changes",
            "library.save_and_continue": "Save to library & load",
            "library.overwrite_title": "Overwrite existing template",
            "library.overwrite_msg": "An active template already exists: <strong>\"{name}\"</strong>.<br>Do you want to overwrite it or save as new?",
            "library.overwrite_btn": "Overwrite active",
            "library.save_as_new_lib": "Save as new in library",
            "library.save_as_disk": "Save as file on disk (.json)",

            "code_editor.title_script": "Script Code Editor",
            "code_editor.title_vars": "Variables Editor",
            "code_editor.templates": "Templates:",
            "code_editor.select_template": "-- Select template --",
            "code_editor.save_template": "Save Template",
            "code_editor.save_template_tooltip": "Save current script as reusable template",
            "code_editor.delete_template": "Delete Template",
            "code_editor.delete_template_tooltip": "Delete selected custom template",
            "code_editor.cancel": "Cancel",
            "code_editor.save": "Save",

            "color_picker.title": "Professional Color Picker",
            "color_picker.cancel": "Cancel",
            "color_picker.save": "Save Color",

            "common.cancel": "Cancel",
            "common.save": "Save",
            "common.confirm": "Confirm",
            "common.close": "Close",
            "common.delete": "Delete",
            "common.error": "Error",
            "common.success": "Success",
            "common.loading": "Loading...",

            "toast.theme_saved_applied": "Theme \"{name}\" saved and applied",
            "toast.theme_saved": "Theme \"{name}\" saved to list",
            "toast.theme_deleted": "Theme \"{name}\" deleted",
            "toast.template_saved": "Template saved successfully",
            "toast.template_loaded": "Template loaded: {name}",
            "toast.template_deleted": "Template deleted",
            "toast.lang_switched": "Language switched to {lang}",
            "toast.session_saved": "Session saved",
            "toast.generation_started": "Starting effect generation...",
            "toast.generation_cancelled": "Generation cancelled by user",
            "toast.generation_finished": "Generation completed successfully",
            "toast.bg_cleared": "Background media removed",
            "toast.bg_applied": "New background applied successfully",

            // --- Node Categories ---
            "nodes.categories.Loops": "Loops",
            "nodes.categories.Variables": "Variables",
            "nodes.categories.System": "System",
            "nodes.categories.Functions": "Functions",
            "nodes.categories.Shape": "Shape",
            "nodes.categories.Time": "Time",
            "nodes.categories.Audio": "Audio",
            "nodes.categories.Math": "Math",
            "nodes.categories.Text": "Text",

            // --- Node Titles ---
            "nodes.titles.Main Loop": "Main Loop",
            "nodes.titles.MaxLoop": "MaxLoop",
            "nodes.titles.Maxloop": "MaxLoop",
            "nodes.titles.Module": "Module",
            "nodes.titles.Define Vars": "Define Vars",
            "nodes.titles.Get Var": "Get Var",
            "nodes.titles.Memory": "Memory",
            "nodes.titles.Sys Var": "Sys Var",
            "nodes.titles.Output": "Output",
            "nodes.titles.Previewer": "Previewer",
            "nodes.titles.Script Code": "Script Code",
            "nodes.titles.Benchmark Math": "Benchmark Math",
            "nodes.titles.Interpolator": "Interpolator",
            "nodes.titles.Conditioner": "Conditioner",
            "nodes.titles.Bezier Curve": "Bezier Curve",
            "nodes.titles.Color Gradient": "Color Gradient",
            "nodes.titles.Color Picker": "Color Picker",
            "nodes.titles.Particles": "Particles",
            "nodes.titles.IMG to Pixels": "IMG to Pixels",
            "nodes.titles.IMG to pixels": "IMG to pixels",
            "nodes.titles.IMG to Shape": "IMG to Shape",
            "nodes.titles.Text to Shape": "Text to Shape",
            "nodes.titles.Polar to Cartesian": "Polar to Cartesian",
            "nodes.titles.Tag Oscillator": "Tag Oscillator",
            "nodes.titles.Shapes Library": "Shapes Library",
            "nodes.titles.Shape Slicer": "Shape Slicer",
            "nodes.titles.Shape Transform": "Shape Transform",
            "nodes.titles.Concentric Borders": "Concentric Borders",
            "nodes.titles.Clip Gradient": "Clip Gradient",
            "nodes.titles.Time Ipol": "Time Ipol",
            "nodes.titles.Synced Time": "Synced Time",
            "nodes.titles.Lead In": "Lead In",
            "nodes.titles.Lead Out": "Lead Out",
            "nodes.titles.Middle 1": "Middle 1",
            "nodes.titles.Middle 2": "Middle 2",
            "nodes.titles.Loop 1": "Loop 1",
            "nodes.titles.Loop 2": "Loop 2",
            "nodes.titles.Offset": "Offset",
            "nodes.titles.Duration": "Duration",
            "nodes.titles.Parse ASS Time": "Parse ASS Time",
            "nodes.titles.Format ASS Time": "Format ASS Time",
            "nodes.titles.Audio Modulator": "Audio Modulator",
            "nodes.titles.Audio Waveform": "Audio Waveform",
            "nodes.titles.Number": "Number",
            "nodes.titles.Concatenate": "Concatenate",
            "nodes.titles.Dynamic Format": "Dynamic Format",
            "nodes.titles.MultiTag": "MultiTag",
            "nodes.titles.MultiRandom": "MultiRandom",
            "nodes.titles.Math": "Math",
            "nodes.titles.Text": "String",
            "nodes.titles.String": "String",

            // --- Slots (Inputs / Outputs) ---
            "nodes.slots.Loop": "Loop",
            "nodes.slots.Loop In": "Loop In",
            "nodes.slots.Loop Out": "Loop Out",
            "nodes.slots.Loop / Domain": "Loop / Domain",
            "nodes.slots.Iterator (i)": "Iterator (i)",
            "nodes.slots.Iterator (j)": "Iterator (j)",
            "nodes.slots.Total (N)": "Total (N)",
            "nodes.slots.Iterations (N)": "Iterations (N)",
            "nodes.slots.Sub-step (m)": "Sub-step (m)",
            "nodes.slots.Flow In": "Flow In",
            "nodes.slots.Flow Out": "Flow Out",
            "nodes.slots.Result": "Result",
            "nodes.slots.Output": "Output",
            "nodes.slots.Data": "Data",
            "nodes.slots.Value": "Value",
            "nodes.slots.Current Value": "Current Value",
            "nodes.slots.Duration (ms)": "Duration (ms)",
            "nodes.slots.Base (ms)": "Base (ms)",
            "nodes.slots.Delay (ms)": "Delay (ms)",
            "nodes.slots.Start Time (ms)": "Start Time (ms)",
            "nodes.slots.End Time (ms)": "End Time (ms)",
            "nodes.slots.ASS Time": "ASS Time",
            "nodes.slots.Time (ms)": "Time (ms)",
            "nodes.slots.Offset (ms)": "Offset (ms)",
            "nodes.slots.Points / Values": "Points / Values",
            "nodes.slots.Acceleration": "Acceleration",
            "nodes.slots.Start": "Start",
            "nodes.slots.End": "End",
            "nodes.slots.Step": "Step",
            "nodes.slots.Width": "Width",
            "nodes.slots.Height": "Height",
            "nodes.slots.Anchor": "Anchor",
            "nodes.slots.Order": "Order",
            "nodes.slots.Output Type": "Output Type",
            "nodes.slots.Piece": "Piece",
            "nodes.slots.Shape": "Shape",
            "nodes.slots.Shape / Text": "Shape / Text",
            "nodes.slots.Bleed": "Bleed",
            "nodes.slots.Angle": "Angle",
            "nodes.slots.Angle (°)": "Angle (°)",
            "nodes.slots.Seed": "Seed",
            "nodes.slots.Separation": "Separation",
            "nodes.slots.Overlap": "Overlap",
            "nodes.slots.Smoothing": "Smoothing",
            "nodes.slots.Frame": "Frame",
            "nodes.slots.Frame (j)": "Frame (j)",
            "nodes.slots.Density": "Density",
            "nodes.slots.Thickness": "Thickness",
            "nodes.slots.Radius": "Radius",
            "nodes.slots.Threshold": "Threshold",
            "nodes.slots.Tolerance": "Tolerance",
            "nodes.slots.Condition": "Condition",
            "nodes.slots.If True": "If True",
            "nodes.slots.If False": "If False",
            "nodes.slots.Constant": "Constant",
            "nodes.slots.Key": "Key",
            "nodes.slots.Font": "Font",
            "nodes.slots.Size": "Size",
            "nodes.slots.Stripes": "Stripes",
            "nodes.slots.Rhythm Pattern": "Rhythm Pattern",
            "nodes.slots.Audio Path": "Audio Path",
            "nodes.slots.Image Path": "Image Path",
            "nodes.slots.Particle": "Particle",
            "nodes.slots.Index": "Index",
            "nodes.slots.Progress (0-1)": "Progress (0-1)",
            "nodes.slots.Base Mode": "Base Mode",
            "nodes.slots.Binarize Mode": "Binarize Mode",
            "nodes.slots.Dilate Step": "Dilate Step",
            "nodes.slots.Dilate Trans": "Dilate Trans",
            "nodes.slots.Border Offset": "Border Offset",
            "nodes.slots.Seq Offset": "Seq Offset",
            "nodes.slots.Color List": "Color List",
            "nodes.slots.Image Scale": "Image Scale",
            "nodes.slots.Scale Out": "Scale Out",
            "nodes.slots.Scale": "Scale",
            "nodes.slots.Optimization": "Optimization",
            "nodes.slots.Max Rings": "Max Rings",
            "nodes.slots.Max Extra": "Max Extra",
            "nodes.slots.Max Val": "Max Val",
            "nodes.slots.Min Val": "Min Val",
            "nodes.slots.Start Time": "Start Time",
            "nodes.slots.End Time": "End Time",
            "nodes.slots.Layer": "Layer",
            "nodes.slots.Tags": "Tags",
            "nodes.slots.Return": "Return",
            "nodes.slots.String": "String",

            // --- Placeholders, Badges and Canvas ---
            "nodes.placeholders.vars_empty": "(click to define vars...)",
            "nodes.placeholders.open_script_editor": "Open Script Editor",
            "nodes.placeholders.align": "Align",
            "nodes.badges.sel": "SEL.",
            "nodes.badges.all": "ALL",
            "nodes.badges.style": "STYLE",
            "nodes.badges.no_blank": "NO BLANK",
            "nodes.badges.with_blank": "WITH BLANK",

            // --- MultiTag descriptions (EN) ---
            "nodes.tags.pos": "position (x, y)",
            "nodes.tags.move": "movement (x1, y1 -> x2, y2)",
            "nodes.tags.org": "rotation origin (x, y)",
            "nodes.tags.fad": "simple fade (in, out)",
            "nodes.tags.fade": "complex fade (7 args)",
            "nodes.tags.clip": "clip mask / drawing",
            "nodes.tags.iclip": "inverted clip",
            "nodes.tags.1c": "primary color",
            "nodes.tags.2c": "secondary color (karaoke)",
            "nodes.tags.3c": "outline color",
            "nodes.tags.4c": "shadow color",
            "nodes.tags.alpha": "general transparency",
            "nodes.tags.1a": "primary alpha",
            "nodes.tags.2a": "secondary alpha",
            "nodes.tags.3a": "outline alpha",
            "nodes.tags.4a": "shadow alpha",
            "nodes.tags.fscx": "horizontal scale %",
            "nodes.tags.fscy": "vertical scale %",
            "nodes.tags.frz": "z rotation (angle)",
            "nodes.tags.frx": "x rotation (perspective)",
            "nodes.tags.fry": "y rotation (perspective)",
            "nodes.tags.fax": "x shear / slant",
            "nodes.tags.fay": "y shear / slant",
            "nodes.tags.bord": "outline width",
            "nodes.tags.shad": "shadow distance",
            "nodes.tags.blur": "gaussian blur",
            "nodes.tags.be": "edge blur",
            "nodes.tags.fs": "font size (px)",
            "nodes.tags.fsp": "font spacing",
            "nodes.tags.an": "alignment (1-9)",
            "nodes.tags.b": "bold (0/1)",
            "nodes.tags.i": "italic (0/1)",
            "nodes.tags.u": "underline (0/1)",
            "nodes.tags.s": "strikeout (0/1)",
            "nodes.tags.k": "karaoke duration",
            "nodes.tags.kf": "karaoke fill",
            "nodes.tags.ko": "karaoke outline",
            "nodes.tags.p": "draw mode (scale)",
            "nodes.tags.t": "animated transform",

            // --- MultiRandom descriptions (EN) ---
            "nodes.randoms.rnd": "basic random (integer/float)",
            "nodes.randoms.rnd_sym": "symmetric random (+/-)",
            "nodes.randoms.rnd_skew": "skewed random (curvature)",
            "nodes.randoms.rnd_choice": "list choice (comma separated)",
            "nodes.randoms.rnd_perlin": "perlin noise 1D/2D",
            "nodes.randoms.rnd_step": "quantized step random",
            "nodes.randoms.rnd_burst": "burst / spike random",
            "nodes.randoms.rnd_decay": "decaying random (exponential)",
            "nodes.randoms.rnd_gauss": "gaussian / normal distribution",
            "nodes.randoms.rnd_walk": "random walk (drunkard)",
            "nodes.randoms.rnd_jitter": "subtle jitter / tremble",
            "nodes.randoms.rnd_shake": "heavy shake / earthquake",
            "nodes.randoms.rnd_orbit": "orbital offset random (r, theta)",
            "nodes.randoms.rnd_flicker": "flicker / strobe (binary)",
            "nodes.randoms.rnd_pulse": "rhythmic pulse random"
        }
    };

    let currentLanguage = "es";
    try {
        const stored = localStorage.getItem("pyxis_language");
        if (stored === "en" || stored === "es") {
            currentLanguage = stored;
        }
    } catch (e) {}

    function t(key, params, fallback) {
        const dict = TRANSLATIONS[currentLanguage] || TRANSLATIONS.es;
        let str = dict[key];
        if (str === undefined) {
            str = TRANSLATIONS.es[key];
        }
        if (str === undefined) {
            str = fallback !== undefined ? fallback : key;
        }
        if (params && typeof params === "object") {
            for (const p in params) {
                str = str.replace(new RegExp(`\\{${p}\\}`, "g"), params[p]);
            }
        }
        return str;
    }

    function getNodeTitle(nodeOrType) {
        if (!nodeOrType) return "";
        let typeOrTitle = typeof nodeOrType === "string" ? nodeOrType : (nodeOrType.title || nodeOrType.type || "");
        if (currentLanguage === "en") {
            if (typeOrTitle.includes("/")) {
                const parts = typeOrTitle.split("/");
                return parts[parts.length - 1];
            }
            return typeOrTitle;
        }
        let clean = typeOrTitle;
        if (clean.includes("/")) {
            const parts = clean.split("/");
            clean = parts[parts.length - 1];
        }
        const key = "nodes.titles." + clean;
        return t(key, null, clean);
    }

    function translateSlot(slotText) {
        if (!slotText || slotText.trim() === "") return slotText;
        if (currentLanguage === "en") return slotText;
        const key = "nodes.slots." + slotText.trim();
        return t(key, null, slotText);
    }

    function getCategoryTitle(category) {
        if (!category) return "";
        if (currentLanguage === "en") return category;
        const key = "nodes.categories." + category;
        return t(key, null, category);
    }

    function getTagDesc(tagKey) {
        if (!tagKey) return "";
        const clean = tagKey.replace(/^\\+/, "").toLowerCase();
        const key = "nodes.tags." + clean;
        return t(key, null, "");
    }

    function getRandomDesc(randomKey) {
        if (!randomKey) return "";
        const clean = randomKey.toLowerCase();
        const key = "nodes.randoms." + clean;
        return t(key, null, "");
    }

    function getSalidaBadgeText(applyTo) {
        const val = String(applyTo || "").toLowerCase();
        if (val.includes("sel")) {
            return t("nodes.badges.sel");
        } else if (val.includes("style")) {
            return t("nodes.badges.style");
        } else {
            return t("nodes.badges.all");
        }
    }

    function getBlankBadgeText(isNoBlank) {
        return isNoBlank ? t("nodes.badges.no_blank") : t("nodes.badges.with_blank");
    }

    function getAlignTitle() {
        return t("nodes.placeholders.align");
    }

    function applyToDOM(root) {
        const container = root || document;

        // 1. Textos directos
        container.querySelectorAll("[data-i18n]").forEach(el => {
            const key = el.getAttribute("data-i18n");
            if (key) {
                el.textContent = t(key);
            }
        });

        // 2. Tooltips
        container.querySelectorAll("[data-i18n-tooltip]").forEach(el => {
            const key = el.getAttribute("data-i18n-tooltip");
            if (key) {
                el.setAttribute("data-tooltip", t(key));
            }
        });

        // 3. Atributos title
        container.querySelectorAll("[data-i18n-title]").forEach(el => {
            const key = el.getAttribute("data-i18n-title");
            if (key) {
                el.setAttribute("title", t(key));
            }
        });

        // 4. Placeholders
        container.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
            const key = el.getAttribute("data-i18n-placeholder");
            if (key) {
                el.setAttribute("placeholder", t(key));
            }
        });

        // Actualizar botón de idioma en modal de Ajustes si existe
        const settingsLangBtn = document.getElementById("btn-settings-lang-toggle");
        if (settingsLangBtn) {
            settingsLangBtn.querySelectorAll(".pyxis-lang-pill").forEach(pill => {
                const code = pill.getAttribute("data-lang") || pill.textContent.trim().toLowerCase();
                if (code === currentLanguage) {
                    pill.classList.add("active");
                } else {
                    pill.classList.remove("active");
                }
            });
            settingsLangBtn.setAttribute("title", t("topbar.lang_tooltip"));
        }

        // Actualizar indicador visual de botón de idioma en Topbar si existe
        const indicator = document.getElementById("lang-indicator");
        if (indicator) {
            indicator.textContent = currentLanguage.toUpperCase();
        }
        const langToggleBtn = document.getElementById("btn-lang-toggle");
        if (langToggleBtn) {
            langToggleBtn.setAttribute("data-tooltip", t("topbar.lang_tooltip"));
        }
    }

    async function setLanguage(lang, persist = true) {
        if (lang !== "es" && lang !== "en") return;
        currentLanguage = lang;
        try {
            localStorage.setItem("pyxis_language", lang);
        } catch (e) {}

        if (document.documentElement) {
            document.documentElement.lang = lang;
        }

        applyToDOM(document);

        // Notificar a observadores o modales abiertos
        window.dispatchEvent(new CustomEvent("pyxis:languageChanged", { detail: { language: lang } }));

        if (persist && window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_user_config === "function") {
            try {
                const config = await window.pywebview.api.get_user_config();
                config.language = lang;
                if (typeof window.pywebview.api.save_user_config === "function") {
                    await window.pywebview.api.save_user_config(config);
                }
            } catch (e) {
                console.warn("Pyxis i18n: error al persistir idioma en user_config", e);
            }
        }
    }

    function toggleLanguage() {
        const next = currentLanguage === "es" ? "en" : "es";
        setLanguage(next, true);
        if (window.showPyxisToast) {
            const langName = next === "en" ? "English" : "Español";
            window.showPyxisToast(t("toast.lang_switched", { lang: langName }), "info", 2000);
        }
    }

    const PyxisI18n = {
        get currentLang() { return currentLanguage; },
        t: t,
        setLanguage: setLanguage,
        toggleLanguage: toggleLanguage,
        applyToDOM: applyToDOM,
        getTranslations: () => TRANSLATIONS,
        getNodeTitle: getNodeTitle,
        translateSlot: translateSlot,
        getCategoryTitle: getCategoryTitle,
        getTagDesc: getTagDesc,
        getRandomDesc: getRandomDesc,
        getSalidaBadgeText: getSalidaBadgeText,
        getBlankBadgeText: getBlankBadgeText,
        getAlignTitle: getAlignTitle
    };

    window.PyxisI18n = PyxisI18n;
    window.t = t; // Helper global rápido

    // Inicializar idioma en DOMContentLoaded
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            applyToDOM(document);
        });
    } else {
        applyToDOM(document);
    }
})(window);
