import 'dart:io';

import 'package:flutter/material.dart';

import 'api/pyxis_api.dart';
import 'state/studio_state.dart';
import 'ui/welcome_page.dart';

/// URL de la API local: variable `PYXIS_API` o http://127.0.0.1:28723
String apiUrl() => Platform.environment['PYXIS_API'] ?? 'http://127.0.0.1:28723';

void main() {
  runApp(PyxisStudioApp(state: StudioState(PyxisApi(apiUrl()))..connect()));
}

class PyxisStudioApp extends StatelessWidget {
  const PyxisStudioApp({super.key, required this.state});
  final StudioState state;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Pyxis Studio',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      darkTheme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF7C5CFF), brightness: Brightness.dark), useMaterial3: true),
      home: WelcomePage(state: state),
    );
  }
}
