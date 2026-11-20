import 'dart:ui';

import 'catalog.dart';

/// Nodo del grafo. `inputs`/`outputs` son los nombres de las ranuras.
class GNode {
  GNode({
    required this.id,
    required this.type,
    required this.x,
    required this.y,
    required this.inputs,
    required this.outputs,
    required this.props,
    this.color = '#3B82F6',
  });

  final int id;
  final String type;
  double x;
  double y;
  List<String> inputs;
  List<String> outputs;
  Map<String, dynamic> props;
  String color;

  String get category => type.contains('/') ? type.split('/').first : '';
  String get title => type.contains('/') ? type.substring(type.indexOf('/') + 1) : type;
  int get rows => inputs.length > outputs.length ? inputs.length : outputs.length;

  static const double width = 210;
  static const double headerHeight = 26;
  static const double rowHeight = 22;
  double get height => headerHeight + (rows == 0 ? 1 : rows) * rowHeight + 8;

  Offset outputPos(int slot) => Offset(x + width, y + headerHeight + rowHeight * (slot + 0.5));
  Offset inputPos(int slot) => Offset(x, y + headerHeight + rowHeight * (slot + 0.5));
}

class GLink {
  GLink({required this.id, required this.fromNode, required this.fromSlot, required this.toNode, required this.toSlot, this.kind = 'data'});

  final int id;
  final int fromNode;
  final int fromSlot;
  final int toNode;
  final int toSlot;
  final String kind;
}

/// Grafo en el mismo formato JSON que usa el motor (`nodes` + `links`: [id, nodo_origen, ranura_origen, nodo_destino, ranura_destino, tipo]).
class GraphModel {
  GraphModel();

  final Map<int, GNode> nodes = {};
  final List<GLink> links = [];
  int lastNodeId = 0;
  int lastLinkId = 0;
  Map<String, dynamic> extra = {};

  static String slotKind(String name) => name.toLowerCase().contains('loop') ? 'loop' : 'data';

  GNode addNode(NodeSpec spec, double x, double y) {
    final n = GNode(
      id: ++lastNodeId,
      type: spec.type,
      x: x,
      y: y,
      inputs: List.of(spec.inputs),
      outputs: List.of(spec.outputs),
      props: Map<String, dynamic>.from(spec.properties),
      color: spec.color,
    );
    nodes[n.id] = n;
    return n;
  }

  void removeNode(int id) {
    nodes.remove(id);
    links.removeWhere((l) => l.fromNode == id || l.toNode == id);
  }

  /// Une una salida con una entrada; una entrada solo admite un enlace (se sustituye el anterior).
  GLink? connect(int fromNode, int fromSlot, int toNode, int toSlot) {
    if (fromNode == toNode) return null;
    final a = nodes[fromNode], b = nodes[toNode];
    if (a == null || b == null || fromSlot >= a.outputs.length || toSlot >= b.inputs.length) return null;
    links.removeWhere((l) => l.toNode == toNode && l.toSlot == toSlot);
    final link = GLink(id: ++lastLinkId, fromNode: fromNode, fromSlot: fromSlot, toNode: toNode, toSlot: toSlot, kind: slotKind(a.outputs[fromSlot]));
    links.add(link);
    return link;
  }

  void disconnectInput(int toNode, int toSlot) => links.removeWhere((l) => l.toNode == toNode && l.toSlot == toSlot);

  GLink? linkIntoInput(int toNode, int toSlot) {
    for (final l in links) {
      if (l.toNode == toNode && l.toSlot == toSlot) return l;
    }
    return null;
  }

  Map<String, dynamic> toJson() {
    final nodeList = <Map<String, dynamic>>[];
    var order = 0;
    for (final n in nodes.values) {
      nodeList.add({
        'id': n.id,
        'type': n.type,
        'pos': [n.x, n.y],
        'size': [GNode.width, n.height],
        'flags': {},
        'order': order++,
        'mode': 0,
        'inputs': [
          for (var i = 0; i < n.inputs.length; i++)
            {'name': n.inputs[i], 'type': slotKind(n.inputs[i]), 'link': linkIntoInput(n.id, i)?.id},
        ],
        'outputs': [
          for (var i = 0; i < n.outputs.length; i++)
            {
              'name': n.outputs[i],
              'type': slotKind(n.outputs[i]),
              'links': [for (final l in links) if (l.fromNode == n.id && l.fromSlot == i) l.id],
              'slot_index': i,
            },
        ],
        'properties': n.props,
        'color': n.color,
      });
    }
    return {
      'last_node_id': lastNodeId,
      'last_link_id': lastLinkId,
      'nodes': nodeList,
      'links': [for (final l in links) [l.id, l.fromNode, l.fromSlot, l.toNode, l.toSlot, l.kind]],
      'groups': [],
      'config': {},
      'extra': extra,
      'version': 0.4,
    };
  }

  factory GraphModel.fromJson(Map<String, dynamic> j, {Catalog? catalog}) {
    final g = GraphModel();
    g.extra = Map<String, dynamic>.from(j['extra'] as Map? ?? const {});
    for (final raw in (j['nodes'] as List? ?? const [])) {
      final m = Map<String, dynamic>.from(raw as Map);
      final type = '${m['type']}';
      final spec = catalog?.byType[type];
      final pos = (m['pos'] as List?) ?? const [0, 0];
      List<String> names(String key, List<String>? fallback) {
        final l = m[key] as List?;
        if (l != null) return [for (final s in l) '${(s as Map)['name']}'];
        return fallback ?? const [];
      }

      g.nodes[(m['id'] as num).toInt()] = GNode(
        id: (m['id'] as num).toInt(),
        type: type,
        x: (pos[0] as num).toDouble(),
        y: (pos[1] as num).toDouble(),
        inputs: names('inputs', spec?.inputs),
        outputs: names('outputs', spec?.outputs),
        props: Map<String, dynamic>.from(m['properties'] as Map? ?? spec?.properties ?? const {}),
        color: '${m['color'] ?? spec?.color ?? '#3B82F6'}',
      );
    }
    for (final raw in (j['links'] as List? ?? const [])) {
      final l = raw as List;
      g.links.add(GLink(
        id: (l[0] as num).toInt(),
        fromNode: (l[1] as num).toInt(),
        fromSlot: (l[2] as num).toInt(),
        toNode: (l[3] as num).toInt(),
        toSlot: (l[4] as num).toInt(),
        kind: l.length > 5 ? '${l[5]}' : 'data',
      ));
    }
    final maxNode = g.nodes.keys.fold<int>(0, (a, b) => a > b ? a : b);
    final maxLink = g.links.fold<int>(0, (a, b) => a > b.id ? a : b.id);
    g.lastNodeId = (j['last_node_id'] as num?)?.toInt() ?? maxNode;
    g.lastLinkId = (j['last_link_id'] as num?)?.toInt() ?? maxLink;
    if (g.lastNodeId < maxNode) g.lastNodeId = maxNode;
    if (g.lastLinkId < maxLink) g.lastLinkId = maxLink;
    return g;
  }
}
