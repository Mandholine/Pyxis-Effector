import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiException implements Exception {
  ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

class ProcessResult {
  ProcessResult(this.success, this.linesCount, this.seconds, this.error, this.outputPath);
  final bool success;
  final int linesCount;
  final double seconds;
  final String? error;
  final String? outputPath;
}

/// Cliente de la API local (FastAPI) de Pyxis.
class PyxisApi {
  PyxisApi(this.baseUrl, {http.Client? client}) : _http = client ?? http.Client();

  final String baseUrl; // p. ej. http://127.0.0.1:28723
  final http.Client _http;

  String get _v1 => '$baseUrl/api/v1';

  Future<dynamic> _json(Future<http.Response> req) async {
    final r = await req.timeout(const Duration(minutes: 10));
    final body = utf8.decode(r.bodyBytes);
    if (r.statusCode >= 400) {
      var detail = body;
      try {
        detail = '${(jsonDecode(body) as Map)['detail']}';
      } catch (_) {}
      throw ApiException('${r.statusCode}: $detail');
    }
    return body.isEmpty ? null : jsonDecode(body);
  }

  Future<dynamic> _get(String path) => _json(_http.get(Uri.parse('$_v1$path')));
  Future<dynamic> _post(String path, Object body) =>
      _json(_http.post(Uri.parse('$_v1$path'), headers: {'content-type': 'application/json'}, body: jsonEncode(body)));

  Future<bool> health() async {
    try {
      final j = await _get('/health').timeout(const Duration(seconds: 3));
      return (j as Map)['status'] == 'ok';
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, dynamic>> manifest() async => Map<String, dynamic>.from(await _get('/nodes/manifest') as Map);

  Future<Map<String, dynamic>?> sessionInfo() async {
    try {
      return Map<String, dynamic>.from(await _get('/session/info') as Map);
    } on ApiException {
      return null;
    }
  }

  Future<Map<String, dynamic>> validate(Map<String, dynamic> graph) async =>
      Map<String, dynamic>.from(await _post('/graph/validate', {'graph': graph}) as Map);

  Future<List<Map<String, dynamic>>> templates() async =>
      [for (final t in (await _get('/templates')) as List) Map<String, dynamic>.from(t as Map)];

  Future<Map<String, dynamic>> template(String id) async =>
      Map<String, dynamic>.from(await _get('/templates/${Uri.encodeComponent(id)}') as Map);

  Future<String> saveTemplate(String name, Map<String, dynamic> graph, {String category = 'General'}) async =>
      '${(await _post('/templates', {'name': name, 'graph': graph, 'category': category}) as Map)['id']}';

  Future<void> deleteTemplate(String id) async {
    await _json(_http.delete(Uri.parse('$_v1/templates/${Uri.encodeComponent(id)}')));
  }

  /// Registra lo elegido en la pantalla de inicio (`script` | `nodes`) para que el macro de Aegisub lo lea.
  Future<void> setChoice(String mode, String? style) async {
    await _post('/session/choice', {'mode': mode, 'style': style});
  }

  /// Ultimo grafo ejecutado para `key` (normalmente el estilo), o null si no hay.
  Future<Map<String, dynamic>?> cachedGraph(String key) async {
    try {
      final j = await _get('/cache/graph?key=${Uri.encodeQueryComponent(key)}') as Map;
      return Map<String, dynamic>.from(j['graph'] as Map);
    } on ApiException {
      return null;
    }
  }

  Future<void> cacheGraph(String key, Map<String, dynamic> graph) async {
    await _json(_http.put(Uri.parse('$_v1/cache/graph'), headers: {'content-type': 'application/json'}, body: jsonEncode({'key': key, 'graph': graph})));
  }

  Future<void> abort() async {
    await _post('/graph/abort', {});
  }

  /// Procesa el grafo por WebSocket y emite el progreso (`percent`, `phase`); devuelve el resultado final.
  Future<ProcessResult> process(
    Map<String, dynamic> graph, {
    required String assPath,
    required String outputPath,
    String? style,
    void Function(int percent, String phase)? onProgress,
  }) async {
    final ws = WebSocketChannel.connect(Uri.parse('${baseUrl.replaceFirst('http', 'ws')}/api/v1/graph/ws/progress'));
    try {
      await ws.ready;
    } catch (e) {
      throw ApiException('No se pudo conectar con la API: $e');
    }
    final done = Completer<ProcessResult>();
    final sub = ws.stream.listen((raw) {
      final m = Map<String, dynamic>.from(jsonDecode(raw as String) as Map);
      onProgress?.call((m['percent'] as num?)?.toInt() ?? 0, '${m['phase'] ?? ''}');
      if (m.containsKey('success') && !done.isCompleted) {
        done.complete(ProcessResult(m['success'] == true, (m['lines_count'] as num?)?.toInt() ?? 0,
            (m['duration_seconds'] as num?)?.toDouble() ?? 0, m['error'] as String?, m['output_path'] as String?));
      }
    }, onError: (Object e) {
      if (!done.isCompleted) done.completeError(ApiException('$e'));
    }, onDone: () {
      if (!done.isCompleted) done.completeError(ApiException('La conexion con la API se cerro'));
    });
    ws.sink.add(jsonEncode({'action': 'start', 'graph': graph, 'ass_path': assPath, 'output_path': outputPath, 'style': ?style}));
    try {
      return await done.future;
    } finally {
      await sub.cancel();
      await ws.sink.close();
    }
  }

  void close() => _http.close();
}
