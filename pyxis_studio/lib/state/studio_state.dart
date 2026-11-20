import 'dart:io';

import 'package:flutter/foundation.dart';

import '../api/pyxis_api.dart';
import '../model/catalog.dart';
import '../model/graph.dart';

/// Estado de la aplicacion: grafo en edicion, seleccion, sesion de Aegisub y ejecucion.
class StudioState extends ChangeNotifier {
  StudioState(this.api, {void Function()? onDone}) : onDone = onDone ?? (() => exit(0));

  final PyxisApi api;

  /// Se llama tras ejecutar con exito: por defecto cierra la app para que Aegisub importe las lineas.
  final void Function() onDone;

  Catalog catalog = Catalog.empty();
  GraphModel graph = GraphModel();
  int? selectedId;
  bool connected = false;
  Map<String, dynamic>? session;
  String templateName = '';

  bool running = false;
  int percent = 0;
  String phase = '';
  final List<String> log = [];

  /// Punto de la escena (coordenadas del lienzo) donde aparece el siguiente nodo anadido desde la paleta.
  double spawnX = 80, spawnY = 80;

  GNode? get selected => selectedId == null ? null : graph.nodes[selectedId];
  /// Nombres de estilo del .ass de la sesion (para el selector de la pantalla de inicio).
  List<String> get styleNames => [for (final st in (session?['styles'] as List? ?? const [])) '${(st as Map)['name']}'];

  /// Estilo sobre el que se aplica el efecto (null = todos).
  String? get style => (session?['style'] as String?)?.isNotEmpty == true ? session!['style'] as String : null;

  /// Clave de la cache del efecto: el estilo de la sesion (o `_all`).
  String get cacheKey => (session?['style'] as String?)?.isNotEmpty == true ? session!['style'] as String : '_all';
  String? get assPath => session?['ass_path'] as String?;
  String? get outputPath => assPath == null ? null : '${assPath!.replaceFirst(RegExp(r'\.ass$', caseSensitive: false), '')}.pyxis.ass';

  /// Anade una linea al registro de la ventana.
  void report(String m) {
    _say(m);
    notifyListeners();
  }

  void _say(String m) {
    log.add(m);
    if (log.length > 200) log.removeAt(0);
  }

  Future<void> connect() async {
    connected = await api.health();
    if (connected) {
      try {
        catalog = Catalog.fromManifest(await api.manifest());
        session = await api.sessionInfo();
        _say(session == null ? 'Conectado. Sin sesion de Aegisub.' : 'Sesion: ${session!['ass_path']} (${session!['lines_count']} lineas)');
        if (session != null) await _loadCache();
      } catch (e) {
        _say('Error al cargar el catalogo: $e');
      }
    } else {
      _say('No se pudo conectar con la API (${api.baseUrl}).');
    }
    notifyListeners();
  }

  /// Recupera el ultimo grafo ejecutado para el estilo actual (si lo hay).
  Future<void> _loadCache() async {
    final cached = await api.cachedGraph(cacheKey);
    if (cached != null) {
      graph = GraphModel.fromJson(cached, catalog: catalog);
      cachedNodes = graph.nodes.length;
      _say('Efecto recuperado de la cache (${graph.nodes.length} nodos, estilo: $cacheKey).');
    } else {
      cachedNodes = 0;
    }
  }

  /// Nodos del ultimo efecto guardado para el estilo actual (0 = ninguno).
  int cachedNodes = 0;

  /// Cambia el estilo de la sesion (null = todos) y recupera el efecto guardado para ese estilo.
  Future<void> selectStyle(String? newStyle) async {
    if (session == null) return;
    session = {...session!, 'style': newStyle};
    graph = GraphModel();
    selectedId = null;
    await _loadCache();
    notifyListeners();
  }

  /// Modo Script: se avisa al macro (que abrira el editor con el estilo elegido) y se cierra la app.
  Future<void> chooseScript() async {
    try {
      await api.setChoice('script', style);
    } catch (e) {
      _say('No se pudo registrar la eleccion: $e');
      notifyListeners();
      return;
    }
    onDone();
  }

  /// Modo Nodos: se registra la eleccion (el macro sabra que el resultado vendra de la app).
  Future<void> chooseNodes() async {
    try {
      await api.setChoice('nodes', style);
    } catch (e) {
      _say('No se pudo registrar la eleccion: $e');
      notifyListeners();
    }
  }

  void select(int? id) {
    selectedId = id;
    notifyListeners();
  }

  GNode? addNode(NodeSpec spec) {
    final n = graph.addNode(spec, spawnX, spawnY);
    spawnX += 30;
    spawnY += 30;
    selectedId = n.id;
    notifyListeners();
    return n;
  }

  void moveNode(int id, double dx, double dy) {
    final n = graph.nodes[id];
    if (n == null) return;
    n.x += dx;
    n.y += dy;
    notifyListeners();
  }

  void connectSlots(int fromNode, int fromSlot, int toNode, int toSlot) {
    if (graph.connect(fromNode, fromSlot, toNode, toSlot) != null) notifyListeners();
  }

  void disconnectInput(int node, int slot) {
    graph.disconnectInput(node, slot);
    notifyListeners();
  }

  void deleteSelected() {
    if (selectedId == null) return;
    graph.removeNode(selectedId!);
    selectedId = null;
    notifyListeners();
  }

  void setProp(int id, String key, dynamic value) {
    graph.nodes[id]?.props[key] = value;
    notifyListeners();
  }

  void newGraph() {
    graph = GraphModel();
    selectedId = null;
    templateName = '';
    spawnX = 80;
    spawnY = 80;
    notifyListeners();
  }

  Future<List<Map<String, dynamic>>> templates() => api.templates();

  Future<void> loadTemplate(String id, String name) async {
    try {
      final t = await api.template(id);
      graph = GraphModel.fromJson(Map<String, dynamic>.from(t['graph'] as Map), catalog: catalog);
      selectedId = null;
      templateName = name;
      _say('Plantilla cargada: $name (${graph.nodes.length} nodos)');
    } catch (e) {
      _say('No se pudo cargar la plantilla: $e');
    }
    notifyListeners();
  }

  Future<void> saveTemplate(String name) async {
    try {
      await api.saveTemplate(name, graph.toJson());
      templateName = name;
      _say('Plantilla guardada: $name');
    } catch (e) {
      _say('No se pudo guardar: $e');
    }
    notifyListeners();
  }

  Future<void> validate() async {
    try {
      final r = await api.validate(graph.toJson());
      final errs = List<String>.from(r['errors'] as List);
      final warns = List<String>.from(r['warnings'] as List);
      _say(r['valid'] == true ? 'Grafo valido.' : 'Grafo NO valido:');
      for (final e in errs) {
        _say('  - $e');
      }
      for (final w in warns) {
        _say('  ! $w');
      }
    } catch (e) {
      _say('Error al validar: $e');
    }
    notifyListeners();
  }

  /// Ejecuta el grafo sobre el .ass de la sesion y deja el resultado en `outputPath` (el macro de Aegisub lo importa).
  Future<bool> run() async {
    if (assPath == null) {
      _say('No hay un .ass abierto: abre la app desde el macro de Aegisub.');
      notifyListeners();
      return false;
    }
    await _saveCache(); // antes de ejecutar: aunque falle, el grafo queda guardado para retocarlo
    running = true;
    percent = 0;
    phase = 'Iniciando...';
    notifyListeners();
    try {
      final r = await api.process(graph.toJson(), assPath: assPath!, outputPath: outputPath!, style: style, onProgress: (p, ph) {
        percent = p;
        phase = ph;
        notifyListeners();
      });
      _say(r.success ? 'Listo: ${r.linesCount} lineas en ${r.seconds.toStringAsFixed(2)} s -> ${r.outputPath}' : 'Fallo: ${r.error}');
      if (r.success) {
        // las lineas ya estan en el .ass de salida: se cierra la app y el macro las pega en Aegisub
        await _saveCache();
        Future.delayed(const Duration(milliseconds: 400), onDone);
      }
      return r.success;
    } catch (e) {
      _say('Error al ejecutar: $e');
      return false;
    } finally {
      running = false;
      notifyListeners();
    }
  }

  Future<void> _saveCache() async {
    try {
      await api.cacheGraph(cacheKey, graph.toJson());
    } catch (e) {
      _say('No se pudo guardar en cache: $e');
    }
  }

  Future<void> abort() async {
    try {
      await api.abort();
      _say('Cancelacion solicitada.');
    } catch (e) {
      _say('No se pudo cancelar: $e');
    }
    notifyListeners();
  }
}
