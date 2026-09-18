import unittest
from nodes.time_nodes import RetimeNode, _resolve_phase_interval, _resolve_unit_and_line_times

class DummyUnit:
    def __init__(self, start_time, end_time, duration=None, unit_type='syl'):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration if duration is not None else (end_time - start_time)
        self.unit_type = unit_type

class DummyLine:
    def __init__(self, start_time, end_time, duration=None):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration if duration is not None else (end_time - start_time)

class TestRetimeNodes(unittest.TestCase):
    def setUp(self):
        self.line = DummyLine(1000, 5000, 4000)
        self.syl = DummyUnit(500, 900, 400, 'syl')
        self.context = {
            'active_line': self.line,
            'active_unit': self.syl,
            'syl': self.syl,
            'line': self.line,
            'duration': 4000.0,
            'fx_dur': 4000.0
        }

    def test_all_ten_modes(self):
        cases = [
            ('syl', -50, 100, (450.0, 1000.0)),
            ('presyl', -50, 100, (450.0, 600.0)),
            ('postsyl', -50, 100, (850.0, 1000.0)),
            ('line', -50, 100, (-50.0, 4100.0)),
            ('preline', -50, 100, (-50.0, 100.0)),
            ('postline', -50, 100, (3950.0, 4100.0)),
            ('start2syl', -50, 100, (-50.0, 600.0)),
            ('syl2end', -50, 100, (850.0, 4100.0)),
            ('abs', -50, 100, (-50.0, 100.0)),
            ('sylpct', -50, 100, (300.0, 900.0)),
        ]
        times = _resolve_unit_and_line_times(self.context)
        for mode, oi, oo, expected in cases:
            res = _resolve_phase_interval(mode, times, off_in=oi, off_out=oo)
            self.assertEqual(res, expected, f'Failed on mode {mode}')

    def test_retime_node_outputs(self):
        res_flat = RetimeNode(self.context, tags=r'\fscx120\fscy120', phase='syl', offset_in=-50, offset_out=50)
        self.assertEqual(res_flat, r'\t(450,950,\fscx120\fscy120)')

        res_nested = RetimeNode(self.context, tags=r'\t(0, 100, \blur2)', phase='presyl', offset_in=-100, offset_out=0)
        self.assertEqual(res_nested, r'\t(400,500,\blur2)')

        res_accel = RetimeNode(self.context, tags=r'\fscx200', phase='abs', offset_in=100, offset_out=600, accel=2.5)
        self.assertEqual(res_accel, r'\t(100,600,2.5,\fscx200)')

    def test_retime_with_effect_context_lead_in(self):
        # Line from 1000 to 5000, but effect starts earlier at 700 (300ms lead-in)
        ctx = {
            'active_line': self.line,
            'active_unit': self.syl, # syl is at 1500-1900 global (local 500-900 to line)
            'syl': self.syl,
            'line': self.line,
            'fx_st': 700.0,
            'fx_et': 5000.0,
            'fx_dur': 4300.0
        }
        # Syl in global timeline is 1500 to 1900.
        # Relative to fx_st (700): local syl is 800 to 1200.
        res = RetimeNode(ctx, tags=r'\blur3', phase='syl', offset_in=0, offset_out=0)
        self.assertEqual(res, r'\t(800,1200,\blur3)')

    def test_retime_with_preline_effect_line(self):
        # Effect line generated for preline: 500 to 1000 (duration 500ms)
        ctx = {
            'active_line': self.line, # original line starts at 1000
            'line': self.line,
            'fx_st': 500.0,
            'fx_et': 1000.0,
            'fx_dur': 500.0
        }
        # In preline phase with off_in=-500, off_out=0:
        # Global preline: [1000 - 500, 1000 + 0] = [500, 1000]
        # Relative to fx_st (500): [0, 500]
        res = RetimeNode(ctx, tags=r'\alpha&H00&', phase='preline', offset_in=-500, offset_out=0)
        self.assertEqual(res, r'\t(0,500,\alpha&H00&)')

        # Line phase inside this preline effect line should also be [0, 500]
        res_line = RetimeNode(ctx, tags=r'\alpha&H00&', phase='line', offset_in=0, offset_out=0)
        self.assertEqual(res_line, r'\t(0,500,\alpha&H00&)')

    def test_retime_output_slots_global(self):
        ctx = {
            'active_line': self.line, # 1000 to 5000
            'line': self.line,
        }
        # preline with -500, 0:
        st = RetimeNode(ctx, phase='preline', offset_in=-500, offset_out=0, output_slot_index=1)
        et = RetimeNode(ctx, phase='preline', offset_in=-500, offset_out=0, output_slot_index=2)
        dur = RetimeNode(ctx, phase='preline', offset_in=-500, offset_out=0, output_slot_index=3)
        self.assertEqual(st, 500.0)
        self.assertEqual(et, 1000.0)
        self.assertEqual(dur, 500.0)

if __name__ == '__main__':
    unittest.main()
