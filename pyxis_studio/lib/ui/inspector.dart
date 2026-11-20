import 'package:flutter/material.dart';

import '../model/graph.dart';
import '../state/studio_state.dart';

/// Propiedades del nodo seleccionado (combos para las opciones del catalogo, texto para el resto).
class Inspector extends StatelessWidget {
  const Inspector({super.key, required this.state});
  final StudioState state;

  @override
  Widget build(BuildContext context) {
    final n = state.selected;
    if (n == null) {
      return const Center(child: Padding(padding: EdgeInsets.all(16), child: Text('Selecciona un nodo para editar sus propiedades.', textAlign: TextAlign.center)));
    }
    final spec = state.catalog.byType[n.type];
    final combos = {for (final w in spec?.widgets ?? const []) if (w.type == 'combo') w.property: w};
    return ListView(padding: const EdgeInsets.all(12), children: [
      Text(n.title, style: Theme.of(context).textTheme.titleMedium),
      Text('${n.type}  ·  id ${n.id}', style: Theme.of(context).textTheme.labelSmall),
      const SizedBox(height: 12),
      if (n.props.isEmpty) const Text('Este nodo no tiene propiedades.'),
      for (final key in n.props.keys.toList()) _field(n, key, combos[key]?.values),
      const SizedBox(height: 12),
      OutlinedButton.icon(onPressed: state.deleteSelected, icon: const Icon(Icons.delete_outline), label: const Text('Eliminar nodo')),
    ]);
  }

  Widget _field(GNode n, String key, List<String>? options) {
    final value = '${n.props[key] ?? ''}';
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: options != null && options.isNotEmpty
          ? DropdownButtonFormField<String>(
              // la clave incluye el valor: al cambiarlo desde fuera el campo se reconstruye
              key: ValueKey('${n.id}/$key/$value'),
              initialValue: options.contains(value) ? value : null,
              isExpanded: true,
              decoration: InputDecoration(labelText: key, isDense: true, border: const OutlineInputBorder()),
              items: [for (final o in options) DropdownMenuItem(value: o, child: Text(o))],
              onChanged: (v) => v == null ? null : state.setProp(n.id, key, v),
            )
          : TextFormField(
              key: ValueKey('${n.id}/$key'),
              initialValue: value,
              minLines: 1,
              maxLines: (value.length > 40 || value.contains('\n') || key.contains('script') || key == 'variables') ? 8 : 1,
              decoration: InputDecoration(labelText: key, isDense: true, border: const OutlineInputBorder()),
              style: const TextStyle(fontFamily: 'Menlo', fontSize: 12),
              onChanged: (v) {
                // numeros y booleanos conservan su tipo
                final prev = n.props[key];
                n.props[key] = prev is num ? (num.tryParse(v) ?? v) : v;
              },
            ),
    );
  }
}
