import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:pyxis_studio/api/pyxis_api.dart';
import 'package:pyxis_studio/main.dart';
import 'package:pyxis_studio/model/catalog.dart';
import 'package:pyxis_studio/model/graph.dart';
import 'package:pyxis_studio/state/studio_state.dart';

const manifest = {
  'system_nodes': {
    'Loops': {
      'Main Loop': {
        'inputs': [],
        'outputs': ['Loop', 'Iterator (i)', 'Total (N)'],
        'color': '#1E5F3A',
        'properties': {'iterator': 'syl'},
        'widgets': [
          {'type': 'combo', 'name': 'Iterator:', 'property': 'iterator', 'values': ['syl', 'char']},
        ],
      },
    },
    'System': {
      'Output': {
        'inputs': ['Loop / Domain', 'Layer'],
        'outputs': ['Preview'],
        'color': '#8B0000',
        'properties': {'apply_to': 'Sel. Lines'},
        'widgets': [],
      },
    },
  },
};

PyxisApi fakeApi(Map<String, http.Response Function(http.Request)> routes) => PyxisApi(
      'http://test',
      client: MockClient((req) async {
        final r = routes['${req.method} ${req.url.path}'];
        return r == null ? http.Response('{"detail":"no route"}', 404) : r(req);
      }),
    );

http.Response ok(Object body) => http.Response(jsonEncode(body), 200, headers: {'content-type': 'application/json; charset=utf-8'});

void main() {
  final catalog = Catalog.fromManifest(manifest);

  test('catalogo: tipos, categorias y busqueda', () {
    expect(catalog.byType.keys, containsAll(['Loops/Main Loop', 'System/Output']));
    expect(catalog.categories, ['Loops', 'System']);
    expect(catalog.byType['Loops/Main Loop']!.widgets.single.values, ['syl', 'char']);
    expect(catalog.search('output').single.name, 'Output');
  });

  test('grafo: conectar reemplaza enlaces y se serializa como el motor', () {
    final g = GraphModel();
    final loop = g.addNode(catalog.byType['Loops/Main Loop']!, 10, 20);
    final out = g.addNode(catalog.byType['System/Output']!, 300, 20);
    expect(g.connect(loop.id, 0, out.id, 0), isNotNull);
    expect(g.connect(loop.id, 0, loop.id, 0), isNull, reason: 'un nodo no se une a si mismo');
    g.connect(loop.id, 1, out.id, 0); // misma entrada: sustituye
    expect(g.links.length, 1);
    final j = g.toJson();
    expect(j['links'], [
      [2, loop.id, 1, out.id, 0, 'data']
    ]);
    final nodes = j['nodes'] as List;
    expect((nodes[1] as Map)['inputs'][0]['link'], 2);
    expect((nodes[0] as Map)['outputs'][1]['links'], [2]);
    expect(((nodes[0] as Map)['inputs'] as List), isEmpty);
  });

  test('grafo: ida y vuelta JSON conserva nodos, propiedades y enlaces', () {
    final g = GraphModel();
    final a = g.addNode(catalog.byType['Loops/Main Loop']!, 1, 2)..props['iterator'] = 'char';
    final b = g.addNode(catalog.byType['System/Output']!, 5, 6);
    g.connect(a.id, 0, b.id, 1);
    final back = GraphModel.fromJson(jsonDecode(jsonEncode(g.toJson())) as Map<String, dynamic>, catalog: catalog);
    expect(back.nodes.length, 2);
    expect(back.nodes[a.id]!.props['iterator'], 'char');
    expect(back.nodes[b.id]!.inputs, ['Loop / Domain', 'Layer']);
    expect(back.links.single.toSlot, 1);
    expect(back.addNode(catalog.byType['System/Output']!, 0, 0).id, 3, reason: 'los ids continuan');
    g.removeNode(a.id);
    expect(g.links, isEmpty);
  });

  test('estado: carga catalogo y sesion de la API; ejecutar sin .ass avisa', () async {
    final api = fakeApi({
      'GET /api/v1/health': (_) => ok({'status': 'ok'}),
      'GET /api/v1/nodes/manifest': (_) => ok(manifest),
      'GET /api/v1/session/info': (_) => ok({'ass_path': '/x/y.ass', 'lines_count': 3}),
    });
    final s = StudioState(api);
    await s.connect();
    expect(s.connected, isTrue);
    expect(s.catalog.byType.length, 2);
    expect(s.outputPath, '/x/y.pyxis.ass');
    s.session = null;
    expect(await s.run(), isFalse);
    expect(s.log.last, contains('No hay un .ass'));
  });

  test('estado: validar muestra errores del motor', () async {
    final api = fakeApi({
      'GET /api/v1/health': (_) => ok({'status': 'ok'}),
      'GET /api/v1/nodes/manifest': (_) => ok(manifest),
      'GET /api/v1/session/info': (_) => http.Response('{"detail":"x"}', 404),
      'POST /api/v1/graph/validate': (_) => ok({'valid': false, 'errors': ['falta Output'], 'warnings': ['ojo']}),
    });
    final s = StudioState(api);
    await s.connect();
    expect(s.session, isNull);
    await s.validate();
    expect(s.log.join('\n'), allOf(contains('NO valido'), contains('falta Output'), contains('ojo')));
  });

  test('cache: al abrir recupera el ultimo grafo de ese estilo', () async {
    final saved = GraphModel()..addNode(catalog.byType['Loops/Main Loop']!, 5, 6);
    String? askedKey;
    final api = fakeApi({
      'GET /api/v1/health': (_) => ok({'status': 'ok'}),
      'GET /api/v1/nodes/manifest': (_) => ok(manifest),
      'GET /api/v1/session/info': (_) => ok({'ass_path': '/x/y.ass', 'lines_count': 3, 'style': 'Romaji'}),
      'GET /api/v1/cache/graph': (req) {
        askedKey = req.url.queryParameters['key'];
        return ok({'key': 'Romaji', 'graph': saved.toJson()});
      },
    });
    final s = StudioState(api, onDone: () {});
    await s.connect();
    expect(askedKey, 'Romaji');
    expect(s.graph.nodes.length, 1);
    expect(s.graph.nodes[1]!.x, 5);
    expect(s.log.join('\n'), contains('recuperado de la cache'));
  });

  test('ejecutar guarda el grafo en cache ANTES de procesar (aunque falle) y no cierra si falla', () async {
    Map<String, dynamic>? put;
    var closed = false;
    final api = fakeApi({
      'GET /api/v1/health': (_) => ok({'status': 'ok'}),
      'GET /api/v1/nodes/manifest': (_) => ok(manifest),
      'GET /api/v1/session/info': (_) => ok({'ass_path': '/x/y.ass', 'lines_count': 3, 'style': 'Romaji'}),
      'GET /api/v1/cache/graph': (_) => http.Response('{"detail":"no"}', 404),
      'PUT /api/v1/cache/graph': (req) {
        put = jsonDecode(req.body) as Map<String, dynamic>;
        return ok({'saved': 'Romaji'});
      },
    });
    final s = StudioState(api, onDone: () => closed = true);
    await s.connect();
    s.addNode(catalog.byType['System/Output']!);
    expect(await s.run(), isFalse, reason: 'no hay WebSocket en la prueba');
    expect(put!['key'], 'Romaji');
    expect((put!['graph'] as Map)['nodes'], hasLength(1));
    await Future<void>.delayed(const Duration(milliseconds: 600));
    expect(closed, isFalse);
  });

  testWidgets('bienvenida: resumen del proyecto, estilos y dos modos; Nodos abre el editor', (tester) async {
    tester.view.physicalSize = const Size(1500, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    Map<String, dynamic>? choice;
    final api = fakeApi({
      'GET /api/v1/health': (_) => ok({'status': 'ok'}),
      'GET /api/v1/nodes/manifest': (_) => ok(manifest),
      'GET /api/v1/session/info': (_) => ok({
            'ass_path': '/x/y.ass',
            'lines_count': 33,
            'style': null,
            'styles': [
              {'name': 'Romaji'},
              {'name': 'Kanji'}
            ],
            'resolution': {'play_res_x': 1280, 'play_res_y': 720},
          }),
      'GET /api/v1/cache/graph': (_) => http.Response('{"detail":"no"}', 404),
      'POST /api/v1/session/choice': (req) {
        choice = jsonDecode(req.body) as Map<String, dynamic>;
        return ok(choice!);
      },
    });
    final state = StudioState(api, onDone: () {});
    await tester.pumpWidget(PyxisStudioApp(state: state));
    await tester.runAsync(state.connect);
    await tester.pumpAndSettle();

    expect(find.text('Pyxis Effect Studio'), findsOneWidget);
    expect(find.text('API conectada'), findsOneWidget);
    expect(find.text('y.ass'), findsOneWidget);
    expect(find.text('33'), findsOneWidget);
    expect(find.text('1280×720'), findsOneWidget);
    expect(find.text('Modo Script'), findsOneWidget);
    expect(find.text('Modo Nodos'), findsOneWidget);

    await tester.runAsync(() => state.selectStyle('Romaji'));
    await tester.pumpAndSettle();
    expect(state.style, 'Romaji');

    await tester.tap(find.text('Abrir el editor de nodos'));
    await tester.pumpAndSettle();
    expect(choice, {'mode': 'nodes', 'style': 'Romaji'});
    expect(find.text('Validar'), findsOneWidget, reason: 'se abrio el editor');
    await tester.tap(find.text('Loops'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Main Loop').first);
    await tester.pumpAndSettle();
    expect(state.graph.nodes.length, 1);
    expect(state.selected!.type, 'Loops/Main Loop');
    expect(find.text('iterator'), findsOneWidget, reason: 'el inspector muestra las propiedades');
  });

  testWidgets('bienvenida: Modo Script registra la eleccion con el estilo y cierra la app', (tester) async {
    tester.view.physicalSize = const Size(1500, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    Map<String, dynamic>? choice;
    var closed = false;
    final api = fakeApi({
      'GET /api/v1/health': (_) => ok({'status': 'ok'}),
      'GET /api/v1/nodes/manifest': (_) => ok(manifest),
      'GET /api/v1/session/info': (_) => ok({'ass_path': '/x/y.ass', 'lines_count': 3, 'style': 'Kanji', 'styles': [{'name': 'Kanji'}]}),
      'GET /api/v1/cache/graph': (_) => http.Response('{"detail":"no"}', 404),
      'POST /api/v1/session/choice': (req) {
        choice = jsonDecode(req.body) as Map<String, dynamic>;
        return ok(choice!);
      },
    });
    final state = StudioState(api, onDone: () => closed = true);
    await tester.pumpWidget(PyxisStudioApp(state: state));
    await tester.runAsync(state.connect);
    await tester.pumpAndSettle();
    await tester.runAsync(() async {
      await tester.tap(find.text('Abrir en el editor'));
      await Future<void>.delayed(const Duration(milliseconds: 300));
    });
    expect(choice, {'mode': 'script', 'style': 'Kanji'});
    expect(closed, isTrue);
  });

  testWidgets('bienvenida sin API: avisa y deshabilita los modos', (tester) async {
    tester.view.physicalSize = const Size(1500, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final state = StudioState(fakeApi({'GET /api/v1/health': (_) => http.Response('x', 500)}), onDone: () {});
    await tester.pumpWidget(PyxisStudioApp(state: state));
    await tester.runAsync(state.connect);
    await tester.pumpAndSettle();
    expect(find.text('API sin conexión'), findsOneWidget);
    expect(tester.widget<FilledButton>(find.ancestor(of: find.text('Abrir en el editor'), matching: find.byType(FilledButton))).onPressed, isNull);
  });

  for (final size in const [Size(1500, 1000), Size(1100, 760), Size(900, 700), Size(700, 900)]) {
    testWidgets('bienvenida sin desbordes a ${size.width.toInt()}x${size.height.toInt()}', (tester) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final api = fakeApi({
        'GET /api/v1/health': (_) => ok({'status': 'ok'}),
        'GET /api/v1/nodes/manifest': (_) => ok(manifest),
        'GET /api/v1/session/info': (_) => ok({
              'ass_path': '/un/directorio/muy/largo/con_un_nombre_de_archivo_bastante_largo_para_probar.ass',
              'lines_count': 1234,
              'styles': [
                for (final n in ['Romaji', 'Kanji', 'Traduccion con un nombre largo', 'Efectos'])
                  {'name': n}
              ],
              'resolution': {'play_res_x': 1920, 'play_res_y': 1080},
            }),
        'GET /api/v1/cache/graph': (_) => http.Response('{"detail":"no"}', 404),
      });
      final state = StudioState(api, onDone: () {});
      await tester.pumpWidget(PyxisStudioApp(state: state));
      await tester.runAsync(state.connect);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(find.text('Modo Nodos'), findsOneWidget);
    });
  }
}
