/// Catalogo de nodos disponibles (viene de `GET /nodes/manifest`, rama `system_nodes`).
class WidgetSpec {
  const WidgetSpec({required this.type, required this.label, required this.property, this.values = const []});

  final String type; // combo | text | ...
  final String label;
  final String property;
  final List<String> values;

  factory WidgetSpec.fromJson(Map<String, dynamic> j) => WidgetSpec(
        type: '${j['type'] ?? 'text'}',
        label: '${j['name'] ?? j['property'] ?? ''}',
        property: '${j['property'] ?? ''}',
        values: [for (final v in (j['values'] as List? ?? const [])) '$v'],
      );
}

class NodeSpec {
  const NodeSpec({
    required this.category,
    required this.name,
    required this.inputs,
    required this.outputs,
    required this.color,
    required this.properties,
    required this.widgets,
  });

  final String category;
  final String name;
  final List<String> inputs;
  final List<String> outputs;
  final String color;
  final Map<String, dynamic> properties;
  final List<WidgetSpec> widgets;

  /// Clave que usa el motor para el tipo de nodo: "Categoria/Nombre".
  String get type => '$category/$name';

  factory NodeSpec.fromJson(String category, String name, Map<String, dynamic> j) => NodeSpec(
        category: category,
        name: name,
        inputs: [for (final v in (j['inputs'] as List? ?? const [])) '$v'],
        outputs: [for (final v in (j['outputs'] as List? ?? const [])) '$v'],
        color: '${j['color'] ?? '#3B82F6'}',
        properties: Map<String, dynamic>.from(j['properties'] as Map? ?? const {}),
        widgets: [
          for (final w in (j['widgets'] as List? ?? const [])) WidgetSpec.fromJson(Map<String, dynamic>.from(w as Map)),
        ],
      );
}

class Catalog {
  Catalog(this.byType);

  final Map<String, NodeSpec> byType;

  factory Catalog.empty() => Catalog({});

  factory Catalog.fromManifest(Map<String, dynamic> manifest) {
    final out = <String, NodeSpec>{};
    final system = Map<String, dynamic>.from(manifest['system_nodes'] as Map? ?? const {});
    system.forEach((cat, nodes) {
      Map<String, dynamic>.from(nodes as Map).forEach((name, spec) {
        final s = NodeSpec.fromJson(cat, name, Map<String, dynamic>.from(spec as Map));
        out[s.type] = s;
      });
    });
    return Catalog(out);
  }

  List<String> get categories => (byType.values.map((s) => s.category).toSet().toList()..sort());

  List<NodeSpec> inCategory(String category) =>
      (byType.values.where((s) => s.category == category).toList()..sort((a, b) => a.name.compareTo(b.name)));

  List<NodeSpec> search(String q) {
    final t = q.trim().toLowerCase();
    if (t.isEmpty) return const [];
    return byType.values.where((s) => s.type.toLowerCase().contains(t)).toList()..sort((a, b) => a.type.compareTo(b.type));
  }
}
