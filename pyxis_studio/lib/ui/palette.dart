import 'package:flutter/material.dart';

import '../model/catalog.dart';
import '../state/studio_state.dart';
import 'graph_canvas.dart';

/// Paleta de nodos por categoria, con busqueda; un toque anade el nodo al lienzo.
class NodePalette extends StatefulWidget {
  const NodePalette({super.key, required this.state});
  final StudioState state;

  @override
  State<NodePalette> createState() => _NodePaletteState();
}

class _NodePaletteState extends State<NodePalette> {
  String _q = '';

  Widget _tile(NodeSpec spec) => ListTile(
        dense: true,
        visualDensity: VisualDensity.compact,
        leading: Icon(Icons.circle, size: 10, color: hex(spec.color)),
        title: Text(_q.isEmpty ? spec.name : spec.type, style: const TextStyle(fontSize: 13)),
        subtitle: Text('${spec.inputs.length} in · ${spec.outputs.length} out', style: const TextStyle(fontSize: 11)),
        onTap: () => widget.state.addNode(spec),
      );

  @override
  Widget build(BuildContext context) {
    final cat = widget.state.catalog;
    return Column(children: [
      Padding(
        padding: const EdgeInsets.all(8),
        child: TextField(
          decoration: const InputDecoration(isDense: true, prefixIcon: Icon(Icons.search, size: 18), hintText: 'Buscar nodo...', border: OutlineInputBorder()),
          onChanged: (v) => setState(() => _q = v),
        ),
      ),
      Expanded(
        child: cat.byType.isEmpty
            ? const Center(child: Text('Sin catalogo (¿API conectada?)'))
            : _q.trim().isNotEmpty
                ? ListView(children: [for (final s in cat.search(_q)) _tile(s)])
                : ListView(children: [
                    for (final c in cat.categories)
                      ExpansionTile(
                        title: Text(c, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        dense: true,
                        children: [for (final s in cat.inCategory(c)) _tile(s)],
                      ),
                  ]),
      ),
    ]);
  }
}
