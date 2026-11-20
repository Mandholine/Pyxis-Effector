import 'package:flutter/material.dart';

import '../state/studio_state.dart';
import 'graph_canvas.dart';
import 'inspector.dart';
import 'palette.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key, required this.state});
  final StudioState state;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: state,
      builder: (context, _) => Scaffold(
        appBar: AppBar(
          titleSpacing: 4,
          leading: IconButton(tooltip: 'Inicio', onPressed: () => Navigator.of(context).maybePop(), icon: const Icon(Icons.home_outlined)),
          title: Row(children: [
            const Text('Pyxis Studio'),
            const SizedBox(width: 16),
            Chip(
              avatar: Icon(Icons.circle, size: 10, color: state.connected ? Colors.green : Colors.red),
              label: Text(state.connected ? 'API conectada' : 'API sin conexion', style: const TextStyle(fontSize: 12)),
              visualDensity: VisualDensity.compact,
            ),
            const SizedBox(width: 8),
            if (state.session != null)
              Flexible(child: Text('${(state.assPath ?? '').split(RegExp(r'[\\/]')).last} · ${state.session!['lines_count']} lineas', overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall)),
          ]),
          actions: [
            IconButton(tooltip: 'Reconectar', onPressed: state.connect, icon: const Icon(Icons.refresh)),
            IconButton(tooltip: 'Nuevo grafo', onPressed: state.newGraph, icon: const Icon(Icons.note_add_outlined)),
            TextButton.icon(onPressed: () => _openTemplates(context), icon: const Icon(Icons.folder_open), label: const Text('Plantillas')),
            TextButton.icon(onPressed: () => _saveTemplate(context), icon: const Icon(Icons.save_outlined), label: const Text('Guardar')),
            TextButton.icon(onPressed: state.validate, icon: const Icon(Icons.rule), label: const Text('Validar')),
            const SizedBox(width: 4),
            if (state.running)
              FilledButton.icon(onPressed: state.abort, style: FilledButton.styleFrom(backgroundColor: Colors.red.shade700), icon: const Icon(Icons.stop), label: const Text('Cancelar'))
            else
              FilledButton.icon(onPressed: state.connected ? state.run : null, icon: const Icon(Icons.play_arrow), label: const Text('Ejecutar')),
            const SizedBox(width: 12),
          ],
          bottom: state.running ? PreferredSize(preferredSize: const Size.fromHeight(3), child: LinearProgressIndicator(value: state.percent / 100)) : null,
        ),
        body: Column(children: [
          Expanded(
            child: Row(children: [
              SizedBox(width: 230, child: NodePalette(state: state)),
              const VerticalDivider(width: 1),
              Expanded(child: GraphCanvas(state: state)),
              const VerticalDivider(width: 1),
              SizedBox(width: 300, child: Inspector(state: state)),
            ]),
          ),
          const Divider(height: 1),
          SizedBox(
            height: 96,
            child: ListView(reverse: true, padding: const EdgeInsets.all(8), children: [
              if (state.running) Text('${state.percent}%  ${state.phase}', style: const TextStyle(fontSize: 12)),
              for (final l in state.log.reversed) Text(l, style: const TextStyle(fontFamily: 'Menlo', fontSize: 11)),
            ]),
          ),
        ]),
      ),
    );
  }

  Future<void> _saveTemplate(BuildContext context) async {
    final c = TextEditingController(text: state.templateName);
    final name = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Guardar como plantilla'),
        content: TextField(controller: c, autofocus: true, decoration: const InputDecoration(labelText: 'Nombre')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, c.text.trim()), child: const Text('Guardar')),
        ],
      ),
    );
    if (name != null && name.isNotEmpty) await state.saveTemplate(name);
  }

  Future<void> _openTemplates(BuildContext context) async {
    List<Map<String, dynamic>> items;
    try {
      items = await state.templates();
    } catch (e) {
      state.report('No se pudieron listar las plantillas: $e');
      return;
    }
    if (!context.mounted) return;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Plantillas (${items.length})'),
        content: SizedBox(
          width: 460,
          height: 360,
          child: items.isEmpty
              ? const Center(child: Text('No hay plantillas.'))
              : ListView(children: [
                  for (final t in items)
                    ListTile(
                      dense: true,
                      title: Text('${t['name']}'),
                      subtitle: Text('${t['category']} · ${t['node_count']} nodos'),
                      onTap: () {
                        Navigator.pop(ctx);
                        state.loadTemplate('${t['id']}', '${t['name']}');
                      },
                    ),
                ]),
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cerrar'))],
      ),
    );
  }
}
