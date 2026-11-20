import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../model/graph.dart';
import '../state/studio_state.dart';

Color hex(String s, [Color fallback = const Color(0xFF3B82F6)]) {
  final h = s.replaceFirst('#', '');
  final v = int.tryParse(h.length == 6 ? 'FF$h' : h, radix: 16);
  return v == null ? fallback : Color(v);
}

/// Lienzo del editor: nodos arrastrables, enlaces Bezier (arrastra de una salida a una entrada), zoom con la rueda
/// y desplazamiento arrastrando el fondo.
class GraphCanvas extends StatefulWidget {
  const GraphCanvas({super.key, required this.state});
  final StudioState state;

  @override
  State<GraphCanvas> createState() => _GraphCanvasState();
}

class _PendingLink {
  _PendingLink(this.node, this.slot, this.to);
  final int node;
  final int slot;
  Offset to;
}

class _GraphCanvasState extends State<GraphCanvas> {
  final _key = GlobalKey();
  final _focus = FocusNode();
  Offset _pan = const Offset(40, 40);
  double _zoom = 1.0;
  _PendingLink? _pending;

  StudioState get s => widget.state;

  Offset _toScene(Offset global) {
    final box = _key.currentContext!.findRenderObject() as RenderBox;
    final local = box.globalToLocal(global);
    return (local - _pan) / _zoom;
  }

  void _endLink() {
    final p = _pending;
    _pending = null;
    if (p != null) {
      for (final n in s.graph.nodes.values) {
        for (var i = 0; i < n.inputs.length; i++) {
          if ((n.inputPos(i) - p.to).distance < 16) {
            s.connectSlots(p.node, p.slot, n.id, i);
            setState(() {});
            return;
          }
        }
      }
    }
    setState(() {});
  }

  @override
  void dispose() {
    _focus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: s,
      builder: (context, _) {
        final g = s.graph;
        return Focus(
          focusNode: _focus,
          autofocus: true,
          onKeyEvent: (_, e) {
            if (e is KeyDownEvent && (e.logicalKey == LogicalKeyboardKey.delete || e.logicalKey == LogicalKeyboardKey.backspace)) {
              s.deleteSelected();
              return KeyEventResult.handled;
            }
            return KeyEventResult.ignored;
          },
          child: Listener(
            onPointerSignal: (e) {
              if (e is PointerScrollEvent) {
                setState(() => _zoom = (_zoom * (e.scrollDelta.dy > 0 ? 0.9 : 1.1)).clamp(0.25, 2.5));
              }
            },
            child: GestureDetector(
              key: _key,
              behavior: HitTestBehavior.opaque,
              onTap: () {
                _focus.requestFocus();
                s.select(null);
              },
              onPanUpdate: (d) => setState(() => _pan += d.delta),
              child: ClipRect(
                child: CustomPaint(
                  painter: _GridPainter(_pan, _zoom, Theme.of(context).colorScheme.outlineVariant.withValues(alpha: 0.25)),
                  child: Stack(clipBehavior: Clip.none, children: [
                    Transform(
                      transform: Matrix4.identity()
                        ..translateByDouble(_pan.dx, _pan.dy, 0, 1)
                        ..scaleByDouble(_zoom, _zoom, 1, 1),
                      child: Stack(clipBehavior: Clip.none, children: [
                        Positioned.fill(
                          child: IgnorePointer(
                            child: CustomPaint(painter: _LinkPainter(g, _pending, Theme.of(context).colorScheme.primary)),
                          ),
                        ),
                        for (final n in g.nodes.values) _nodeWidget(n),
                      ]),
                    ),
                    Positioned(
                      right: 8,
                      bottom: 8,
                      child: Text('${(_zoom * 100).round()}%  ·  ${g.nodes.length} nodos', style: Theme.of(context).textTheme.labelSmall),
                    ),
                  ]),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _nodeWidget(GNode n) {
    final color = hex(n.color);
    final selected = s.selectedId == n.id;
    final scheme = Theme.of(context).colorScheme;
    return Positioned(
      left: n.x,
      top: n.y,
      width: GNode.width,
      height: n.height,
      child: Stack(clipBehavior: Clip.none, children: [
        Positioned.fill(
          child: GestureDetector(
            onTap: () {
              _focus.requestFocus();
              s.select(n.id);
            },
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHigh,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: selected ? scheme.primary : color.withValues(alpha: 0.6), width: selected ? 2 : 1),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                GestureDetector(
                  onPanUpdate: (d) => s.moveNode(n.id, d.delta.dx / _zoom, d.delta.dy / _zoom),
                  onPanStart: (_) => s.select(n.id),
                  child: Container(
                    height: GNode.headerHeight,
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                    alignment: Alignment.centerLeft,
                    decoration: BoxDecoration(color: color.withValues(alpha: 0.85), borderRadius: const BorderRadius.vertical(top: Radius.circular(7))),
                    child: Text(n.title, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 12)),
                  ),
                ),
                Expanded(
                  child: Row(children: [
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      for (final name in n.inputs) _slotLabel(name, Alignment.centerLeft),
                    ])),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                      for (final name in n.outputs) _slotLabel(name, Alignment.centerRight),
                    ])),
                  ]),
                ),
              ]),
            ),
          ),
        ),
        for (var i = 0; i < n.inputs.length; i++)
          _port(left: -7, top: GNode.headerHeight + GNode.rowHeight * (i + 0.5) - 7, connected: s.graph.linkIntoInput(n.id, i) != null, color: color, onTap: () => s.disconnectInput(n.id, i)),
        for (var i = 0; i < n.outputs.length; i++)
          _port(
            left: GNode.width - 7,
            top: GNode.headerHeight + GNode.rowHeight * (i + 0.5) - 7,
            connected: s.graph.links.any((l) => l.fromNode == n.id && l.fromSlot == i),
            color: color,
            onPanStart: (d) => setState(() => _pending = _PendingLink(n.id, i, _toScene(d.globalPosition))),
            onPanUpdate: (d) => setState(() => _pending?.to = _toScene(d.globalPosition)),
            onPanEnd: (_) => _endLink(),
          ),
      ]),
    );
  }

  Widget _slotLabel(String name, Alignment a) => Container(
        height: GNode.rowHeight,
        alignment: a,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        child: Text(name, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11)),
      );

  Widget _port({
    required double left,
    required double top,
    required bool connected,
    required Color color,
    VoidCallback? onTap,
    GestureDragStartCallback? onPanStart,
    GestureDragUpdateCallback? onPanUpdate,
    GestureDragEndCallback? onPanEnd,
  }) =>
      Positioned(
        left: left,
        top: top,
        child: GestureDetector(
          onTap: onTap,
          onPanStart: onPanStart,
          onPanUpdate: onPanUpdate,
          onPanEnd: onPanEnd,
          child: Container(
            width: 14,
            height: 14,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: connected ? color : Theme.of(context).colorScheme.surface,
              border: Border.all(color: color, width: 2),
            ),
          ),
        ),
      );
}

class _GridPainter extends CustomPainter {
  _GridPainter(this.pan, this.zoom, this.color);
  final Offset pan;
  final double zoom;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final step = 40 * zoom;
    final p = Paint()..color = color;
    for (var x = pan.dx % step; x < size.width; x += step) {
      for (var y = pan.dy % step; y < size.height; y += step) {
        canvas.drawCircle(Offset(x, y), 1, p);
      }
    }
  }

  @override
  bool shouldRepaint(_GridPainter old) => old.pan != pan || old.zoom != zoom;
}

class _LinkPainter extends CustomPainter {
  _LinkPainter(this.g, this.pending, this.accent);
  final GraphModel g;
  final _PendingLink? pending;
  final Color accent;

  void _curve(Canvas c, Offset a, Offset b, Paint paint) {
    final dx = (b.dx - a.dx).abs().clamp(40.0, 220.0) * 0.6;
    final path = Path()
      ..moveTo(a.dx, a.dy)
      ..cubicTo(a.dx + dx, a.dy, b.dx - dx, b.dy, b.dx, b.dy);
    c.drawPath(path, paint);
  }

  @override
  void paint(Canvas canvas, Size size) {
    for (final l in g.links) {
      final a = g.nodes[l.fromNode], b = g.nodes[l.toNode];
      if (a == null || b == null) continue;
      final paint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2
        ..color = l.kind == 'loop' ? const Color(0xFF34D399) : hex(a.color);
      _curve(canvas, a.outputPos(l.fromSlot), b.inputPos(l.toSlot), paint);
    }
    final p = pending;
    final from = p == null ? null : g.nodes[p.node];
    if (p != null && from != null) {
      _curve(canvas, from.outputPos(p.slot), p.to, Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2
        ..color = accent);
    }
  }

  @override
  bool shouldRepaint(_LinkPainter old) => true;
}
