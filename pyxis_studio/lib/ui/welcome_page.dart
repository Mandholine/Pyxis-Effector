import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../state/studio_state.dart';
import 'home_page.dart';

const _violet = Color(0xFF7C5CFF);
const _cyan = Color(0xFF38D9F5);
const _allStyles = '(Todos los estilos)';

/// Pantalla de inicio: cabecera con imagen, resumen del proyecto, selector de estilo y los dos modos de trabajo.
class WelcomePage extends StatelessWidget {
  const WelcomePage({super.key, required this.state});
  final StudioState state;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: state,
      builder: (context, _) => Scaffold(
        backgroundColor: const Color(0xFF0B0B18),
        body: SingleChildScrollView(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1180),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(32, 28, 32, 28),
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  _Hero(state: state),
                  const SizedBox(height: 22),
                  _ProjectCard(state: state),
                  const SizedBox(height: 22),
                  LayoutBuilder(builder: (context, c) {
                    final script = _ModeCard(
                      key: const ValueKey('card-script'),
                      icon: Icons.terminal_rounded,
                      accent: _cyan,
                      title: 'Modo Script',
                      subtitle: 'Efectos escritos en código Python',
                      bullets: const ['Se editan en tu editor de código', 'Control total de tiempos, tags y formas', 'Basado en pyxis-core'],
                      cta: 'Abrir en el editor',
                      enabled: state.connected,
                      onTap: state.chooseScript,
                    );
                    final nodes = _ModeCard(
                      key: const ValueKey('card-nodes'),
                      icon: Icons.account_tree_rounded,
                      accent: _violet,
                      title: 'Modo Nodos',
                      subtitle: 'Grafo visual, sin escribir código',
                      bullets: [
                        'Plantillas listas para usar',
                        'Progreso y cancelación en vivo',
                        state.cachedNodes > 0 ? 'Retoma tu último efecto (${state.cachedNodes} nodos)' : 'Guarda tu último efecto por estilo',
                      ],
                      cta: 'Abrir el editor de nodos',
                      enabled: state.connected,
                      onTap: () async {
                        await state.chooseNodes();
                        if (context.mounted) {
                          Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => HomePage(state: state)));
                        }
                      },
                    );
                    if (c.maxWidth < 760) return Column(children: [script, const SizedBox(height: 18), nodes]);
                    // IntrinsicHeight: ambas tarjetas miden lo mismo y `stretch` no pide altura infinita dentro del scroll
                    return IntrinsicHeight(
                      child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                        Expanded(child: script),
                        const SizedBox(width: 22),
                        Expanded(child: nodes),
                      ]),
                    );
                  }),
                  const SizedBox(height: 22),
                  const _CreditsPanel(),
                  const SizedBox(height: 22),
                  _StatusBar(state: state),
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Hero extends StatelessWidget {
  const _Hero({required this.state});
  final StudioState state;

  @override
  Widget build(BuildContext context) {
    final narrow = MediaQuery.sizeOf(context).width < 820;
    return ClipRRect(
      borderRadius: BorderRadius.circular(22),
      child: SizedBox(
        height: narrow ? 380 : 270,
        child: Stack(fit: StackFit.expand, children: [
          Image.asset('assets/hero.png', fit: BoxFit.cover, alignment: Alignment.centerRight),
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [Color(0xE60B0B18), Color(0x990B0B18), Color(0x000B0B18)], stops: [0, 0.5, 1]),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(34),
            child: Row(children: [
              ClipRRect(borderRadius: BorderRadius.circular(18), child: Image.asset('assets/logo.png', width: 96, height: 96)),
              const SizedBox(width: 24),
              Expanded(
                child: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('Pyxis Effect Studio', style: TextStyle(fontSize: 38, fontWeight: FontWeight.w800, letterSpacing: -0.5, color: Colors.white)),
                  const SizedBox(height: 8),
                  Text('Efectos de karaoke con Python y nodos', style: TextStyle(fontSize: 17, color: Colors.white.withValues(alpha: 0.78))),
                  const SizedBox(height: 18),
                  Wrap(spacing: 10, runSpacing: 8, children: [
                    _Pill(state.connected ? 'API conectada' : 'API sin conexión', state.connected ? const Color(0xFF34D399) : const Color(0xFFF87171)),
                    _Pill('${state.catalog.byType.length} nodos', _violet),
                    const _Pill('v1.0', Colors.white54),
                  ]),
                ]),
              ),
            ]),
          ),
        ]),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill(this.text, this.color);
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(color: color.withValues(alpha: 0.16), borderRadius: BorderRadius.circular(20), border: Border.all(color: color.withValues(alpha: 0.5))),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.circle, size: 8, color: color),
          const SizedBox(width: 7),
          Text(text, style: const TextStyle(fontSize: 12.5, color: Colors.white, fontWeight: FontWeight.w600)),
        ]),
      );
}

class _ProjectCard extends StatelessWidget {
  const _ProjectCard({required this.state});
  final StudioState state;

  @override
  Widget build(BuildContext context) {
    final s = state.session;
    final styles = state.styleNames;
    final file = (state.assPath ?? '').split(RegExp(r'[\\/]')).last;
    final res = s?['resolution'] as Map?;
    return _Panel(
      child: s == null
          ? Row(children: [
              const Icon(Icons.info_outline_rounded, color: Colors.white54),
              const SizedBox(width: 14),
              Expanded(child: Text(state.connected ? 'Sin sesión de Aegisub: abre la app desde el macro para trabajar sobre un archivo.' : 'No se pudo conectar con la API (${state.api.baseUrl}).', style: const TextStyle(color: Colors.white70))),
              TextButton.icon(onPressed: state.connect, icon: const Icon(Icons.refresh_rounded), label: const Text('Reconectar')),
            ])
          : Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 28, runSpacing: 14, children: [
              _Stat(Icons.description_outlined, 'Archivo', file.isEmpty ? '—' : file),
              _Stat(Icons.subtitles_outlined, 'Líneas', '${s['lines_count']}'),
              _Stat(Icons.palette_outlined, 'Estilos', '${styles.length}'),
              if (res != null) _Stat(Icons.aspect_ratio_rounded, 'Resolución', '${res['play_res_x']}×${res['play_res_y']}'),
              SizedBox(
                width: 260,
                child: DropdownButtonFormField<String>(
                  key: ValueKey('style-${state.style}'),
                  initialValue: state.style ?? _allStyles,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Aplicar al estilo', isDense: true, border: OutlineInputBorder()),
                  items: [for (final n in [_allStyles, ...styles]) DropdownMenuItem(value: n, child: Text(n, overflow: TextOverflow.ellipsis))],
                  onChanged: (v) => state.selectStyle(v == null || v == _allStyles ? null : v),
                ),
              ),
            ]),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.icon, this.label, this.value);
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, color: _cyan, size: 22),
        const SizedBox(width: 10),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 300),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(label, style: const TextStyle(fontSize: 11.5, color: Colors.white54)),
            Text(value, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white)),
          ]),
        ),
      ]);
}

class _Panel extends StatelessWidget {
  const _Panel({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(color: const Color(0xFF141428), borderRadius: BorderRadius.circular(18), border: Border.all(color: Colors.white.withValues(alpha: 0.07))),
        child: child,
      );
}

class _ModeCard extends StatefulWidget {
  const _ModeCard({super.key, required this.icon, required this.accent, required this.title, required this.subtitle, required this.bullets, required this.cta, required this.enabled, required this.onTap});
  final IconData icon;
  final Color accent;
  final String title;
  final String subtitle;
  final List<String> bullets;
  final String cta;
  final bool enabled;
  final VoidCallback onTap;

  @override
  State<_ModeCard> createState() => _ModeCardState();
}

class _ModeCardState extends State<_ModeCard> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final a = widget.accent;
    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        transform: Matrix4.translationValues(0, _hover && widget.enabled ? -4 : 0, 0),
        padding: const EdgeInsets.all(26),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(22),
          gradient: LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [a.withValues(alpha: _hover ? 0.28 : 0.16), const Color(0xFF141428)]),
          border: Border.all(color: a.withValues(alpha: _hover ? 0.8 : 0.35), width: 1.4),
          boxShadow: [BoxShadow(color: a.withValues(alpha: _hover ? 0.28 : 0.10), blurRadius: 30, offset: const Offset(0, 12))],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(18), gradient: LinearGradient(colors: [a, a.withValues(alpha: 0.55)])),
            child: Icon(widget.icon, color: Colors.white, size: 34),
          ),
          const SizedBox(height: 20),
          Text(widget.title, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: Colors.white)),
          const SizedBox(height: 4),
          Text(widget.subtitle, style: const TextStyle(fontSize: 15, color: Colors.white70)),
          const SizedBox(height: 18),
          for (final b in widget.bullets)
            Padding(
              padding: const EdgeInsets.only(bottom: 9),
              child: Row(children: [
                Icon(Icons.check_circle_rounded, size: 18, color: a),
                const SizedBox(width: 10),
                Expanded(child: Text(b, style: const TextStyle(fontSize: 14, color: Colors.white))),
              ]),
            ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: a, foregroundColor: Colors.black87, textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
              onPressed: widget.enabled ? widget.onTap : null,
              icon: const Icon(Icons.arrow_forward_rounded),
              label: Text(widget.cta),
            ),
          ),
        ]),
      ),
    );
  }
}

class _StatusBar extends StatelessWidget {
  const _StatusBar({required this.state});
  final StudioState state;

  @override
  Widget build(BuildContext context) => Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.bolt_rounded, size: 16, color: Colors.white.withValues(alpha: 0.4)),
        const SizedBox(width: 6),
        Text('Pyxis Effector  ·  pyxis-core  ·  ${state.api.baseUrl}', style: TextStyle(fontSize: 12, color: Colors.white.withValues(alpha: 0.4))),
      ]);
}

const _repoUrl = 'https://github.com/Mandholine/Pyxis-Effector';
const _contributors = [
  ('Trota', 'Desarrollo y motor de efectos'),
  ('Zagon', 'Desarrollo y pruebas'),
  ('Pedro Holguin', 'pyxis-core, API y Pyxis Studio'),
];

Future<void> _openRepo(BuildContext context) async {
  try {
    final cmd = Platform.isMacOS ? 'open' : (Platform.isWindows ? 'explorer' : 'xdg-open');
    await Process.run(cmd, [_repoUrl]);
  } catch (_) {
    await Clipboard.setData(const ClipboardData(text: _repoUrl));
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Enlace del repositorio copiado al portapapeles')));
    }
  }
}

/// Agradecimientos a contribuidores y enlace al repositorio de GitHub.
class _CreditsPanel extends StatelessWidget {
  const _CreditsPanel();

  @override
  Widget build(BuildContext context) => _Panel(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Wrap(spacing: 14, runSpacing: 12, crossAxisAlignment: WrapCrossAlignment.center, children: [
            ClipRRect(borderRadius: BorderRadius.circular(10), child: Image.asset('assets/logo.png', width: 40, height: 40)),
            const SizedBox(
              width: 420,
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Agradecimientos', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: Colors.white)),
                Text('Pyxis Effector es software libre, hecho por y para la comunidad de karaoke.', style: TextStyle(fontSize: 13, color: Colors.white60)),
              ]),
            ),
            FilledButton.icon(
              key: const ValueKey('btn-github'),
              style: FilledButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.black87),
              onPressed: () => _openRepo(context),
              icon: const Icon(Icons.code_rounded),
              label: const Text('Ver en GitHub'),
            ),
          ]),
          const SizedBox(height: 18),
          Wrap(spacing: 14, runSpacing: 14, children: [
            for (final (name, role) in _contributors)
              Container(
                width: 260,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.04), borderRadius: BorderRadius.circular(14), border: Border.all(color: Colors.white.withValues(alpha: 0.07))),
                child: Row(children: [
                  CircleAvatar(
                    radius: 22,
                    backgroundColor: _violet,
                    child: Text(name[0], style: const TextStyle(fontWeight: FontWeight.w800, color: Colors.white, fontSize: 18)),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white)),
                      Text(role, style: const TextStyle(fontSize: 12, color: Colors.white60)),
                    ]),
                  ),
                ]),
              ),
          ]),
          const SizedBox(height: 14),
          const Text('Gracias también a la comunidad de Aegisub y a todas las personas que prueban, reportan errores y comparten plantillas.', style: TextStyle(fontSize: 12.5, color: Colors.white54)),
        ]),
      );
}
