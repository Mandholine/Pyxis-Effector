import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from node_engine import GraphEngine
from nodes.tag_nodes import eval_tag_manipulator_node
from nodes.time_nodes import eval_retime_node
from models import StyleRef, PyxisLine, PyxisUnit


class TestTagManipulatorNode(unittest.TestCase):

    def setUp(self):
        style_dict = {
            'fontname': 'Arial',
            'fontsize': 45.0,
            'color1': '&H00FFFFFF&',
            'color2': '&H000000FF&',
            'color3': '&H00000000&',
            'color4': '&H00000000&',
            'alpha1': '&H00&',
            'alpha2': '&H00&',
            'alpha3': '&H80&',
            'alpha4': '&HFF&',
            'scale_x': 100.0,
            'scale_y': 100.0,
            'spacing': 0.0,
            'outline': 3.0,
            'shadow': 1.5,
            'angle': 0.0
        }
        self.style = StyleRef(style_dict)
        self.line = PyxisLine()
        self.line.styleref = self.style
        self.line.duration = 2000.0
        self.line.start_time = 0.0
        self.line.end_time = 2000.0

        self.unit = PyxisUnit()
        self.unit.styleref = self.style
        self.unit.start_time = 400.0
        self.unit.end_time = 900.0
        self.unit.duration = 500.0

        self.context = {
            'active_line': self.line,
            'active_unit': self.unit,
            'styleref': self.style,
            'duration': 2000.0,
            'fx_dur': 2000.0
        }

    # -------------------------------------------------------------------------
    # Mode: Invert
    # -------------------------------------------------------------------------
    def test_invert_rotation_and_angles(self):
        res = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\frz45\\frx-30\\fry15.5\\fax0.25')
        self.assertEqual(res, '\\frz-45\\frx30\\fry-15.5\\fax-0.25')

    def test_invert_colors(self):
        # Invert pure Red (&H0000FF&) -> Cyan (&HFFFF00&)
        res = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\1c&H0000FF&')
        self.assertEqual(res, '\\1c&HFFFF00&')

        # Invert pure Green (&H00FF00&) -> Magenta (&HFF00FF&)
        res2 = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\3c&H00FF00&')
        self.assertEqual(res2, '\\3c&HFF00FF&')

    def test_invert_alphas(self):
        # Invert opaque (&H00&) -> fully transparent (&HFF&)
        res = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\alpha&H00&')
        self.assertEqual(res, '\\alpha&HFF&')

        # Invert partial alpha (&H1A& = 26) -> 255 - 26 = 229 = &HE5&
        res2 = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\1a&H1A&')
        self.assertEqual(res2, '\\1a&HE5&')

    def test_invert_resets_borders_and_blur(self):
        res = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\bord4\\blur3.5\\shad2\\be1')
        self.assertEqual(res, '\\bord0\\blur0\\shad0\\be0')

    def test_invert_clips(self):
        res = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\clip(m 0 0 l 10 10)')
        self.assertEqual(res, '\\iclip(m 0 0 l 10 10)')

        res2 = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\iclip(m 0 0 l 10 10)')
        self.assertEqual(res2, '\\clip(m 0 0 l 10 10)')

    def test_invert_nested_inside_t_block(self):
        res = eval_tag_manipulator_node(self.context, mode='Invert', tags='\\frz45\\t(0,300,\\frz-45\\1c&H0000FF&)')
        self.assertEqual(res, '\\frz-45\\t(0,300,\\frz45\\1c&HFFFF00&)')

    # -------------------------------------------------------------------------
    # Mode: Reset
    # -------------------------------------------------------------------------
    def test_reset_specific_tags(self):
        res = eval_tag_manipulator_node(self.context, mode='Reset', tags='\\frz45\\1c&H0000FF&\\bord5')
        self.assertIn('\\1c&HFFFFFF&', res)
        self.assertIn('\\frz0', res)
        self.assertIn('\\bord3', res)

    def test_reset_all(self):
        res = eval_tag_manipulator_node(self.context, mode='Reset', tags='all')
        self.assertIn('\\1c&HFFFFFF&', res)
        self.assertIn('\\fs45', res)
        self.assertIn('\\bord3', res)
        self.assertIn('\\shad1.5', res)
        self.assertIn('\\blur0', res)
        self.assertIn('\\alpha&H00&', res)

    # -------------------------------------------------------------------------
    # Mode: Extractor
    # -------------------------------------------------------------------------
    def test_extractor_numeric_tag(self):
        tags = '\\an5\\pos(640,360)\\fscx150\\frz45.5'
        str_val = eval_tag_manipulator_node(self.context, mode='Extractor', tags=tags, target_tag='frz', output_slot_index=0)
        num_val = eval_tag_manipulator_node(self.context, mode='Extractor', tags=tags, target_tag='frz', output_slot_index=1)
        self.assertEqual(str_val, '45.5')
        self.assertEqual(num_val, 45.5)

    def test_extractor_color_tag(self):
        tags = '\\1c&H00FF00&\\3c&H0000FF&'
        str_val = eval_tag_manipulator_node(self.context, mode='Extractor', tags=tags, target_tag='\\3c', output_slot_index=0)
        self.assertEqual(str_val, '&H0000FF&')

    def test_extractor_last_override_rule(self):
        # Later tags override earlier tags
        tags = '\\frz30\\blur2\\frz-60'
        str_val = eval_tag_manipulator_node(self.context, mode='Extractor', tags=tags, target_tag='frz', output_slot_index=0)
        num_val = eval_tag_manipulator_node(self.context, mode='Extractor', tags=tags, target_tag='frz', output_slot_index=1)
        self.assertEqual(str_val, '-60')
        self.assertEqual(num_val, -60.0)


class TestRetimeNode(unittest.TestCase):

    def setUp(self):
        self.line = PyxisLine()
        self.line.duration = 2000.0
        self.line.start_time = 0.0
        self.line.end_time = 2000.0

        self.unit = PyxisUnit()
        self.unit.start_time = 400.0
        self.unit.end_time = 900.0
        self.unit.duration = 500.0

        self.context = {
            'active_line': self.line,
            'active_unit': self.unit,
            'duration': 2000.0,
            'fx_dur': 2000.0
        }

    def test_retime_syl_active_slot_metrics(self):
        st = eval_retime_node(self.context, phase='Syl Active', output_slot_index=1)
        et = eval_retime_node(self.context, phase='Syl Active', output_slot_index=2)
        dur = eval_retime_node(self.context, phase='Syl Active', output_slot_index=3)
        self.assertEqual(st, 400.0)
        self.assertEqual(et, 900.0)
        self.assertEqual(dur, 500.0)

    def test_retime_syl_active_wrap_plain_tags(self):
        res = eval_retime_node(self.context, phase='Syl Active', tags='\\fscx150\\blur2')
        self.assertEqual(res, '\\t(400,900,\\fscx150\\blur2)')

    def test_retime_start_to_syl_with_offsets(self):
        st = eval_retime_node(self.context, phase='Start to Syl', offset_in=-100, offset_out=50, output_slot_index=1)
        et = eval_retime_node(self.context, phase='Start to Syl', offset_in=-100, offset_out=50, output_slot_index=2)
        dur = eval_retime_node(self.context, phase='Start to Syl', offset_in=-100, offset_out=50, output_slot_index=3)
        self.assertEqual(st, -100.0)
        self.assertEqual(et, 450.0)
        self.assertEqual(dur, 550.0)

    def test_retime_syl_to_end(self):
        st = eval_retime_node(self.context, phase='Syl to End', output_slot_index=1)
        et = eval_retime_node(self.context, phase='Syl to End', output_slot_index=2)
        dur = eval_retime_node(self.context, phase='Syl to End', output_slot_index=3)
        self.assertEqual(st, 900.0)
        self.assertEqual(et, 2000.0)
        self.assertEqual(dur, 1100.0)

    def test_retime_existing_t_block(self):
        res = eval_retime_node(self.context, phase='Syl Active', tags='\\t(0, 200, \\fscx150)')
        self.assertEqual(res, '\\t(400,600,\\fscx150)')

    def test_retime_with_accel(self):
        res = eval_retime_node(self.context, phase='Syl Active', tags='\\fscx150', accel=2.0)
        self.assertEqual(res, '\\t(400,900,2,\\fscx150)')


class TestGraphEngineIntegration(unittest.TestCase):

    def test_graph_engine_tag_manipulator_node(self):
        engine = GraphEngine()
        engine.nodes = {
            1: {
                'id': 1,
                'type': 'Tags/Tag Manipulator',
                'properties': {
                    'mode': 'Invert',
                    'tags': '\\frz60\\1c&H0000FF&'
                },
                'inputs': []
            }
        }
        res = engine.evaluate_data_node(1, {}, output_slot_index=0)
        self.assertEqual(res, '\\frz-60\\1c&HFFFF00&')

    def test_graph_engine_retime_node(self):
        engine = GraphEngine()
        engine.nodes = {
            1: {
                'id': 1,
                'type': 'Time/Retime',
                'properties': {
                    'phase': 'Syl Active',
                    'tags': '\\blur3'
                },
                'inputs': []
            }
        }
        unit = PyxisUnit()
        unit.start_time = 200.0
        unit.end_time = 600.0
        ctx = {'active_unit': unit}
        res = engine.evaluate_data_node(1, ctx, output_slot_index=0)
        self.assertEqual(res, '\\t(200,600,\\blur3)')


if __name__ == '__main__':
    unittest.main()
