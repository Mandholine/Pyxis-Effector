import os
import json
import pytest
from main import PyxisAPI
from node_engine import GraphEngine

def test_matches_output_node_case_and_custom_names():
    api = PyxisAPI('', '', '')
    
    n1 = {'id': 3, 'type': 'System/Output', 'properties': {'queue_id': 'primero', 'queue_order': '1'}, 'title': 'Salida Principal'}
    n2 = {'id': 14, 'type': 'System/Output', 'properties': {'queue_id': 'segundo', 'queue_order': '2'}, 'title': 'Salida Secundaria'}
    n3 = {'id': 20, 'type': 'System/Output', 'properties': {'queue_id': 'Tercero', 'queue_order': '3'}, 'title': 'Custom FX'}
    all_salidas = [n1, n2, n3]

    # Test 1: Exact case matching
    assert api._matches_output_node(n1, ['primero'], all_salidas) is True
    assert api._matches_output_node(n2, ['primero'], all_salidas) is False
    assert api._matches_output_node(n3, ['primero'], all_salidas) is False

    # Test 2: Case sensitivity (Primero does not match 'primero')
    assert api._matches_output_node(n1, ['Primero'], all_salidas) is False
    assert api._matches_output_node(n3, ['Tercero'], all_salidas) is True
    assert api._matches_output_node(n3, ['tercero'], all_salidas) is False

    # Test 3: Custom node title matching
    assert api._matches_output_node(n1, ['Salida Principal'], all_salidas) is True
    assert api._matches_output_node(n3, ['Custom FX'], all_salidas) is True

    # Test 4: Comma separated IDs
    assert api._matches_output_node(n1, ['primero, segundo'], all_salidas) is True
    assert api._matches_output_node(n2, ['primero, segundo'], all_salidas) is True
    assert api._matches_output_node(n3, ['primero, segundo'], all_salidas) is False

    # Test 5: 1-based index and numeric ID matching
    assert api._matches_output_node(n1, ['1'], all_salidas) is True
    assert api._matches_output_node(n2, ['2'], all_salidas) is True
    assert api._matches_output_node(n1, ['Salida 1'], all_salidas) is True
    assert api._matches_output_node(n2, ['Output 2'], all_salidas) is True
    assert api._matches_output_node(n1, ['3'], all_salidas) is True

def test_generate_preview_ass_with_multiple_salidas():
    api = PyxisAPI('', '', '')
    template_path = r'c:\Users\Trota\AppData\Roaming\PyxisNodes\templates\20260830_223911_prueba_a_revisar_0238e4e7.json'
    if not os.path.exists(template_path):
        pytest.skip('Template file not found')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        tpl = json.load(f)

    graph = tpl['graph']

    # Target: primero
    res1 = api.generate_preview_ass(graph, target_output_id=['primero'], source='base')
    assert res1.get('success') is True
    lines1 = [l for l in res1.get('content', '').splitlines() if l.startswith('Dialogue:')]
    assert len(lines1) > 0
    assert any('primero' in l for l in lines1)
    assert not any('segundo' in l for l in lines1)

    # Target: segundo
    res2 = api.generate_preview_ass(graph, target_output_id=['segundo'], source='base')
    assert res2.get('success') is True
    lines2 = [l for l in res2.get('content', '').splitlines() if l.startswith('Dialogue:')]
    assert len(lines2) > 0
    assert any('segundo' in l for l in lines2)
    assert not any('primero' in l for l in lines2)

    # Target: primero, segundo
    res3 = api.generate_preview_ass(graph, target_output_id=['primero, segundo'], source='base')
    assert res3.get('success') is True
    lines3 = [l for l in res3.get('content', '').splitlines() if l.startswith('Dialogue:')]
    assert any('primero' in l for l in lines3)
    assert any('segundo' in l for l in lines3)
