# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any question you can visit: https://discord.gg/rYsARc3fB9

"""Pruebas unitarias para nodos de calculo y sincronizacion de tiempo (Time Nodes)."""

import unittest 
from ass_parser import KaraokeProcessor 
from utils import format_time 
from models import PyxisLine ,PyxisUnit 
from node_engine import GraphEngine 
from nodes .time_nodes import (
time_lead_in ,time_lead_out ,time_middle_1 ,time_middle_2 ,
time_loop_1 ,time_loop_2 ,time_ipol ,time_offset ,time_duration ,
time_parse_ass ,time_format_ass ,time_synchronized_extra_node ,
time_to_frame_node ,frame_to_time_node 
)


def _make_test_unit (i ,n ,start_time ,end_time ,dur ,text ="A"):
    u =PyxisUnit ()
    u .i ,u .n =i ,n 
    u .start_time ,u .end_time ,u .dur =start_time ,end_time ,dur 
    u .text ,u .text_stripped =text ,text 
    return u 


def _make_line (text ="Hello",start =1000 ,end =2000 ,left =100 ,right =200 ,width =100 ):
    line =PyxisLine ()
    line .text =text 
    line .text_stripped =text 
    line .start_time =start 
    line .end_time =end 
    line .duration =end -start 
    line .left =left 
    line .right =right 
    line .width =width 
    line .x =(left +right )/2.0 
    line .y =700.0 
    line .style_name ="Default"
    line .is_selected =True 
    return line 


class TestTimeNodesCore (unittest .TestCase ):
    """Pruebas de funciones de tiempo de Effector 2 (ke.time)."""

    def setUp (self ):
        self .unit1 =_make_test_unit (i =1 ,n =4 ,start_time =1000 ,end_time =2000 ,dur =1000 ,text ="A")
        self .unit2 =_make_test_unit (i =2 ,n =4 ,start_time =1200 ,end_time =2200 ,dur =1000 ,text ="B")
        self .unit4 =_make_test_unit (i =4 ,n =4 ,start_time =1600 ,end_time =2600 ,dur =1000 ,text ="D")

        self .ctx1 ={'active_unit':self .unit1 ,'fx_i':1 ,'fx_n':3 ,'J':1 ,'maxJ':2 }
        self .ctx2 ={'active_unit':self .unit2 ,'fx_i':2 ,'fx_n':3 ,'J':2 ,'maxJ':2 }
        self .ctx4 ={'active_unit':self .unit4 ,'fx_i':3 ,'fx_n':3 ,'J':2 ,'maxJ':2 }

    def test_lead_in (self ):
        self .assertEqual (time_lead_in (self .ctx1 ,delay =40 ),-200.0 )
        self .assertEqual (time_lead_in (self .ctx2 ,delay =40 ),-160.0 )
        self .assertEqual (time_lead_in (self .ctx4 ,delay =40 ),-80.0 )

    def test_lead_out (self ):
        self .assertEqual (time_lead_out (self .ctx1 ,delay =40 ),40.0 )
        self .assertEqual (time_lead_out (self .ctx4 ,delay =40 ),160.0 )

    def test_middle_1 (self ):
        self .assertEqual (time_middle_1 (self .ctx1 ,delay =30 ),-200.0 )
        self .assertEqual (time_middle_1 (self .ctx2 ,delay =30 ),-170.0 )
        self .assertEqual (time_middle_1 (self .ctx4 ,delay =30 ),-185.0 )

    def test_middle_2 (self ):
        self .assertEqual (time_middle_2 (self .ctx1 ,delay =30 ),-215.0 )
        self .assertEqual (time_middle_2 (self .ctx4 ,delay =30 ),-230.0 )

    def test_loop_1 (self ):
        self .assertEqual (time_loop_1 (self .ctx1 ,delay =30 ,mode ="leadin"),-200.0 )
        self .assertEqual (time_loop_1 (self .ctx2 ,delay =30 ,mode ="leadin"),-170.0 )
        self .assertEqual (time_loop_1 (self .ctx4 ,delay =30 ,mode ="leadout"),170.0 )

    def test_loop_2 (self ):
        self .assertEqual (time_loop_2 (self .ctx1 ,delay =30 ,mode ="leadin"),-200.0 )
        self .assertEqual (time_loop_2 (self .ctx2 ,delay =30 ,mode ="leadin"),-170.0 )

    def test_ipol (self ):
        res =time_ipol (self .ctx1 ,dur =1000 ,points ="0, 50, 100",accel =1.0 )
        self .assertIn ("[0.0, 500.0]",res )
        self .assertIn ("[500.0, 1000.0]",res )

    def test_expression_evaluation (self ):
        ctx =dict (self .ctx1 )
        res =time_lead_in (ctx ,delay ="20 * 2")
        self .assertEqual (res ,-200.0 )

    def test_offset_and_duration (self ):
        self .assertEqual (time_offset (None ,base =1000 ,offset =250 ),1250.0 )
        self .assertEqual (time_duration (None ,st =1000 ,et =3500 ),2500.0 )

    def test_parse_and_format_ass_time (self ):
        ms =time_parse_ass (None ,ass_str ="0:01:23.45")
        self .assertEqual (ms ,83450.0 )
        formatted =time_format_ass (None ,ms =83450 )
        self .assertEqual (formatted ,"0:01:23.45")


class TestTimeSynchronized (unittest .TestCase ):
    """Pruebas del algoritmo de calculo de tiempo sincronizado entre lineas sucesivas."""

    def test_single_line_isolated (self ):
        line =_make_line (text ="ABCDE",start =1000 ,end =2000 )
        ctx ={'line':line ,'active_line':line }
        res =time_synchronized_extra_node (ctx ,progression_const =20 ,delay =250 ,max_added_time =2000 )
        self .assertEqual (res ,330.0 )

    def test_single_line_cap_max (self ):
        line =_make_line (text ="A"*100 ,start =1000 ,end =2000 )
        ctx ={'line':line ,'active_line':line }
        res =time_synchronized_extra_node (ctx ,progression_const =50 ,delay =250 ,max_added_time =500 )
        self .assertEqual (res ,500.0 )


class TestSyllableTiming (unittest .TestCase ):
    """Pruebas de tiempos metricos por silaba, caracter y palabra."""

    def test_syllable_and_char_times (self ):
        kp =KaraokeProcessor (res_x =1280 ,res_y =720 )
        raw_dialogue ="Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\\k43}Ma{\\k65}ry {\\k44}te"
        style ={"Fontname":"Arial","Fontsize":40 }

        line =kp .process_line (raw_dialogue ,style )

        self .assertEqual (line .start_time ,5000 )
        self .assertEqual (line .end_time ,10000 )
        self .assertEqual (line .duration ,5000 )

        real_syls =[s for s in line .syls if s .text_spacestripped ]
        self .assertEqual (len (real_syls ),3 )

        syl_ma =real_syls [0 ]
        self .assertEqual (syl_ma .text_spacestripped ,"Ma")
        self .assertEqual (syl_ma .start_time ,5000 )
        self .assertEqual (syl_ma .end_time ,5430 )
        self .assertEqual (syl_ma .duration ,430 )


class TestTimeToFrameAndFrameToTime (unittest .TestCase ):
    """Pruebas para nodos Time to Frame y Frame to Time."""

    def setUp (self ):
        self .unit =_make_test_unit (i =3 ,n =5 ,start_time =1000 ,end_time =2500 ,dur =1500 ,text ="Test")
        self .ctx ={
        'active_unit':self .unit ,
        'j':10 ,
        'J':25 ,
        'frame_dur':40.0 
        }

    def test_time_to_frame_modes (self ):


        self .assertEqual (time_to_frame_node (self .ctx ,time_val =100 ,mode ="Ceil"),3 )
        self .assertEqual (time_to_frame_node (self .ctx ,time_val =100 ,mode ="Floor"),2 )
        self .assertEqual (time_to_frame_node (self .ctx ,time_val =105 ,mode ="Round"),3 )

    def test_time_to_frame_sources (self ):

        self .assertEqual (time_to_frame_node (self .ctx ,source ="Start Time",mode ="Floor"),25 )

        self .assertEqual (time_to_frame_node (self .ctx ,source ="End Time",mode ="Ceil"),63 )

        self .assertEqual (time_to_frame_node (self .ctx ,source ="Duration",mode ="Ceil"),38 )

    def test_time_to_frame_ass_string (self ):

        self .assertEqual (time_to_frame_node (self .ctx ,time_val ="0:00:02.00",mode ="Floor"),50 )

    def test_frame_to_time_formats (self ):

        self .assertEqual (frame_to_time_node (self .ctx ,frames =50 ,format ="MS"),2000.0 )
        self .assertEqual (frame_to_time_node (self .ctx ,frames =50 ,format ="HMS"),"0:00:02.00")
        self .assertEqual (frame_to_time_node (self .ctx ,frames =50 ,format ="SEC"),2.0 )

    def test_frame_to_time_sources (self ):

        self .assertEqual (frame_to_time_node (self .ctx ,source ="j",format ="MS"),400.0 )

        self .assertEqual (frame_to_time_node (self .ctx ,source ="J",format ="MS"),1000.0 )

        self .assertEqual (frame_to_time_node (self .ctx ,source ="i",format ="MS"),120.0 )


        custom_ctx =dict (self .ctx )
        custom_ctx ['k']=7 
        custom_ctx ['step_i']=15 
        custom_ctx ['p_i']=30 


        self .assertEqual (frame_to_time_node (custom_ctx ,source ="Iterador",iter_name ="k",format ="MS"),280.0 )
        self .assertEqual (frame_to_time_node (custom_ctx ,source ="Iterador",iter_name ="step_i",format ="MS"),600.0 )

        self .assertEqual (frame_to_time_node (custom_ctx ,source ="Iterador",iter_name ="",format ="MS"),400.0 )

        self .assertEqual (frame_to_time_node (custom_ctx ,source ="Iterador",iter_name ="k * 2",format ="MS"),560.0 )

        self .assertEqual (frame_to_time_node (custom_ctx ,source ="Custom",frames ="p_i",format ="MS"),1200.0 )

    def test_frame_to_time_dual_output (self ):
        self .assertEqual (frame_to_time_node (self .ctx ,frames =100 ,format ="MS",output_slot_index =1 ),"0:00:04.00")


class TestTimeAMicroBatch(unittest.TestCase):
    """Pruebas unitarias completas para el micro-lote Time-A (Retime, Lead In, Lead Out, Synced)."""

    def setUp(self):
        self.unit1 = _make_test_unit(i=1, n=4, start_time=1000, end_time=2000, dur=1000, text="Lead")
        self.unit2 = _make_test_unit(i=2, n=4, start_time=1200, end_time=2200, dur=1000, text="In")
        self.line1 = _make_line(text="Line 1", start=1000, end=2000, left=100, right=200, width=100)
        self.line2 = _make_line(text="Line 2", start=2500, end=4000, left=250, right=400, width=150)
        self.ctx1 = {
            'active_unit': self.unit1,
            'syl': self.unit1,
            'line': self.line1,
            'active_line': self.line1,
            'next_line': self.line2,
            'fx_i': 1, 'fx_n': 4,
            'fx_st': 1000, 'fx_et': 2000, 'fx_dur': 1000
        }

    def test_time_lead_in_canonical_prop(self):
        # delay_ms canonical prop
        res = time_lead_in(self.ctx1, delay_ms="50")
        self.assertEqual(res, -200.0)
        self.unit1.i = 2
        res2 = time_lead_in(self.ctx1, delay_ms="50")
        self.assertEqual(res2, -150.0)

    def test_time_lead_out_canonical_prop(self):
        # delay_ms canonical prop
        self.unit1.i = 1
        self.unit1.n = 4
        res = time_lead_out(self.ctx1, delay_ms="50")
        self.assertEqual(res, 0.0)
        self.unit1.i = 4
        res2 = time_lead_out(self.ctx1, delay_ms="50")
        self.assertEqual(res2, 150.0)

    def test_time_synced_canonical_props_and_slots(self):
        # Slot 0: Extra ms
        extra_ms = time_synchronized_extra_node(
            self.ctx1,
            progression_const=20,
            fade_dur=300,
            max_added_time=2000,
            delay_ms=250,
            max_gap_threshold=3000,
            output_slot_index=0
        )
        self.assertIsInstance(extra_ms, float)
        self.assertGreater(extra_ms, 0.0)

        # Slot 1: Sync End (line.end_time + extra_ms)
        sync_end = time_synchronized_extra_node(
            self.ctx1,
            progression_const=20,
            fade_dur=300,
            max_added_time=2000,
            delay_ms=250,
            max_gap_threshold=3000,
            output_slot_index=1
        )
        self.assertEqual(sync_end, round(2000.0 + extra_ms, 2))

    def test_time_synced_modes(self):
        l1 = _make_line(text="L1", start=1000, end=2000)
        l1.style_name = "Romaji"
        l1.actor = "SingerA"
        l1.layer = 1
        l1.effect = "fx1"

        l2_interleaved = _make_line(text="L2 Interleaved", start=2100, end=2200)
        l2_interleaved.style_name = "Kanji"
        l2_interleaved.actor = "SingerB"
        l2_interleaved.layer = 2
        l2_interleaved.effect = "fx2"

        l3_match = _make_line(text="L3 Match", start=3000, end=4000)
        l3_match.style_name = "Romaji"
        l3_match.actor = "SingerA"
        l3_match.layer = 1
        l3_match.effect = "fx1"

        ctx = {
            'line': l1,
            'target_lines': [l1, l2_interleaved, l3_match]
        }

        # 1. Mode 'order': next is l2_interleaved (start=2100) -> gap=100 < delay=250 -> 0.0
        res_order = time_synchronized_extra_node(ctx, progression_const=0, delay_ms=250, fade_dur=100, mode="order")
        self.assertEqual(res_order, 0.0)

        # 2. Mode 'style': next is l3_match (start=3000) -> gap=1000 -> 1000 + 125 - 100 = 1025.0
        res_style = time_synchronized_extra_node(ctx, progression_const=0, delay_ms=250, fade_dur=100, mode="style")
        self.assertEqual(res_style, 1025.0)

        # 3. Mode 'actor': next is l3_match -> 1025.0
        res_actor = time_synchronized_extra_node(ctx, progression_const=0, delay_ms=250, fade_dur=100, mode="actor")
        self.assertEqual(res_actor, 1025.0)

        # 4. Mode 'layer': next is l3_match -> 1025.0
        res_layer = time_synchronized_extra_node(ctx, progression_const=0, delay_ms=250, fade_dur=100, mode="layer")
        self.assertEqual(res_layer, 1025.0)

        # 5. Mode 'effect': next is l3_match -> 1025.0
        res_effect = time_synchronized_extra_node(ctx, progression_const=0, delay_ms=250, fade_dur=100, mode="effect")
        self.assertEqual(res_effect, 1025.0)

    def test_user_exact_lines_simulation(self):
        def parse_t(s):
            h, m, sec = s.split(':')
            return int(h)*3600000 + int(m)*60000 + int(round(float(sec)*1000))

        r_times = [
            ('0:19:30.69', '0:19:32.61'), ('0:19:33.00', '0:19:35.28'),
            ('0:19:35.47', '0:19:37.64'), ('0:19:38.00', '0:19:40.19'),
            ('0:19:40.48', '0:19:44.17'), ('0:19:44.51', '0:19:49.07'),
            ('0:19:49.35', '0:19:52.47'), ('0:19:52.71', '0:19:54.58'),
            ('0:19:54.77', '0:19:57.59'), ('0:19:57.91', '0:19:59.67'),
            ('0:19:59.96', '0:20:02.66'), ('0:20:02.85', '0:20:04.47'),
            ('0:20:04.71', '0:20:09.44'), ('0:20:09.82', '0:20:14.39'),
            ('0:20:14.82', '0:20:20.44')
        ]
        def_time = ('0:20:20.44', '0:20:23.94')

        all_lines = []
        for st, et in r_times:
            l = _make_line(text="short text", start=parse_t(st), end=parse_t(et))
            l.style_name = 'EP11INS_R'
            l.layer = 1
            all_lines.append(l)

        d = _make_line(text="", start=parse_t(def_time[0]), end=parse_t(def_time[1]))
        d.style_name = 'Default'
        d.layer = 0
        all_lines.append(d)

        for st, et in r_times:
            l = _make_line(text="very long english translation text with much wider width and more characters", start=parse_t(st), end=parse_t(et))
            l.style_name = 'EP11INS_TL'
            l.layer = 0
            all_lines.append(l)

        # Interleaved order simulation test verifying mode=style vs mode=order
        interleaved_lines = []
        for i in range(15):
            interleaved_lines.append(all_lines[i]) # R_i
            interleaved_lines.append(all_lines[16 + i]) # TL_i
        interleaved_lines.append(all_lines[15]) # Default

        # 1. Under mode='style', R and TL get 100% identical values line by line
        for i in range(15):
            ctx_r = {'line': all_lines[i], 'target_lines': interleaved_lines}
            ctx_tl = {'line': all_lines[16 + i], 'target_lines': interleaved_lines}
            res_r = time_synchronized_extra_node(ctx_r, progression_const=0, fade_dur=0, max_added_time=200, delay_ms=250, max_gap_threshold=3000, mode="style")
            res_tl = time_synchronized_extra_node(ctx_tl, progression_const=0, fade_dur=0, max_added_time=200, delay_ms=250, max_gap_threshold=3000, mode="style")
            self.assertEqual(res_r, res_tl, f"Mismatch at line {i}: R={res_r}, TL={res_tl}")

    def test_retime_node_canonical_evaluation(self):
        from nodes.time_nodes import RetimeNode
        # Slot 0: \t Out
        t_out = RetimeNode(self.ctx1, tags=r"\fscx120\fscy120", phase="syl", offset_in="-50", offset_out="50", accel="1.5", output_slot_index=0)
        self.assertTrue(t_out.startswith(r"\t("))
        self.assertIn(r"\fscx120\fscy120", t_out)

        # Slot 1: Start Time
        st = RetimeNode(self.ctx1, tags="", phase="syl", offset_in="-50", offset_out="50", output_slot_index=1)
        self.assertEqual(st, 950.0)

        # Slot 2: End Time
        et = RetimeNode(self.ctx1, tags="", phase="syl", offset_in="-50", offset_out="50", output_slot_index=2)
        self.assertEqual(et, 2050.0)

        # Slot 3: Duration
        dur = RetimeNode(self.ctx1, tags="", phase="syl", offset_in="-50", offset_out="50", output_slot_index=3)
        self.assertEqual(dur, 1100.0)

    def test_node_engine_evaluation_time_a(self):
        from node_engine import GraphEngine

        # Retime via engine
        node_retime = {
            "id": 1,
            "type": "Time/Retime",
            "properties": {"phase": "syl", "tags": r"\blur2", "offset_in": "0", "offset_out": "0", "accel": "1.0"},
            "inputs": [{"name": r"Tags or \t", "property": "tags"}, {"name": "Offset In (ms)", "property": "offset_in"}, {"name": "Offset Out (ms)", "property": "offset_out"}, {"name": "Accel", "property": "accel"}]
        }
        engine_retime = GraphEngine(graph_data={"nodes": [node_retime], "links": []})
        res_retime = engine_retime.evaluate_data_node(1, self.ctx1, output_slot_index=0)
        self.assertTrue(res_retime.startswith(r"\t("))

        # Lead In via engine
        node_li = {
            "id": 2,
            "type": "Time/Lead In",
            "properties": {"delay_ms": "40"},
            "inputs": [{"name": "Delay (ms)", "property": "delay_ms"}]
        }
        engine_li = GraphEngine(graph_data={"nodes": [node_li], "links": []})
        self.unit1.i = 1
        res_li = engine_li.evaluate_data_node(2, self.ctx1, output_slot_index=0)
        self.assertEqual(float(res_li), -200.0)

        # Lead Out via engine
        node_lo = {
            "id": 3,
            "type": "Time/Lead Out",
            "properties": {"delay_ms": "40"},
            "inputs": [{"name": "Delay (ms)", "property": "delay_ms"}]
        }
        engine_lo = GraphEngine(graph_data={"nodes": [node_lo], "links": []})
        self.unit1.i = 4
        self.unit1.n = 4
        res_lo = engine_lo.evaluate_data_node(3, self.ctx1, output_slot_index=0)
        self.assertEqual(float(res_lo), 160.0)

        # Synced via engine
        node_synced = {
            "id": 4,
            "type": "Time/Synced",
            "properties": {"progression_const": "20", "fade_dur": "300", "max_added_time": "2000", "delay_ms": "250", "max_gap_threshold": "3000"},
            "inputs": [
                {"name": "Constant", "property": "progression_const"},
                {"name": "Fade (ms)", "property": "fade_dur"},
                {"name": "Max Extra", "property": "max_added_time"},
                {"name": "Delay Line", "property": "delay_ms"},
                {"name": "Threshold", "property": "max_gap_threshold"}
            ]
        }
        engine_synced = GraphEngine(graph_data={"nodes": [node_synced], "links": []})
        res_synced_extra = engine_synced.evaluate_data_node(4, self.ctx1, output_slot_index=0)
        self.assertGreater(float(res_synced_extra), 0.0)
        res_synced_end = engine_synced.evaluate_data_node(4, self.ctx1, output_slot_index=1)
        self.assertEqual(float(res_synced_end), round(2000.0 + float(res_synced_extra), 2))

    def test_synced_multiprocessing_consistency(self):
        """Verifica que Time/Synced en modo style mantenga paridad y contexto global en multiprocessing."""
        times = [
            (1170690, 1172610),
            (1173000, 1175280),
            (1175470, 1177640),
            (1178000, 1180190),
            (1180480, 1184170),
            (1184510, 1189070),
            (1189350, 1192470),
            (1192710, 1194580),
            (1194770, 1197590),
            (1197910, 1199670),
            (1199960, 1202660),
            (1202850, 1204470),
            (1204660, 1207900),
            (1208090, 1210110),
            (1210400, 1213450),
        ]
        items = []
        for i, (st, et) in enumerate(times, 1):
            st_str = format_time(st)
            et_str = format_time(et)
            items.append({'raw': f"Dialogue: 0,{st_str},{et_str},Style_R,,0,0,0,,Text R {i}", 'is_selected': True, 'i': i})
        
        items.append({'raw': "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Mid", 'is_selected': False, 'i': 16})
        
        for i, (st, et) in enumerate(times, 1):
            st_str = format_time(st)
            et_str = format_time(et)
            items.append({'raw': f"Dialogue: 0,{st_str},{et_str},Style_TL,,0,0,0,,Text TL {i}", 'is_selected': True, 'i': 16 + i})

        styles = {
            'Style_R': {'Fontname': 'Arial', 'Fontsize': 20},
            'Style_TL': {'Fontname': 'Arial', 'Fontsize': 20},
            'Default': {'Fontname': 'Arial', 'Fontsize': 20},
        }

        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"base_unit": "line", "noblank": "No Blank"},
                    "inputs": []
                },
                {
                    "id": 2,
                    "type": "Time/Synced",
                    "properties": {
                        "mode": "style",
                        "progression_const": "0",
                        "fade_dur": "300",
                        "max_added_time": "2000",
                        "delay_ms": "200",
                        "max_gap_threshold": "3000"
                    },
                    "inputs": []
                },
                {
                    "id": 3,
                    "type": "String",
                    "properties": {"value": "TestText"},
                    "inputs": []
                },
                {
                    "id": 4,
                    "type": "System/Output",
                    "properties": {
                        "apply_to": "Selected Lines"
                    },
                    "inputs": [
                        {"name": "Loop", "type": "data", "link": 101},
                        {"name": "Capa", "type": 0, "link": None},
                        {"name": "Start", "type": 0, "link": None},
                        {"name": "End", "type": 0, "link": 102},
                        {"name": "Tags", "type": 0, "link": None},
                        {"name": "Retorno", "type": "string", "link": 103}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 4, 0, "data"],
                [102, 2, 1, 4, 3, "number"],
                [103, 3, 0, 4, 5, "string"]
            ]
        }

        engine_seq = GraphEngine(graph_data=graph)
        lines_seq = engine_seq.process(items, styles, use_multiprocessing=False)

        engine_mp = GraphEngine(graph_data=graph)
        lines_mp = engine_mp.process(items, styles, use_multiprocessing=True)

        self.assertEqual(len(lines_seq), len(lines_mp))
        self.assertEqual(len(lines_mp), 30)

        for i in range(15):
            line_r = lines_mp[i]
            line_tl = lines_mp[15 + i]
            parts_r = line_r.split(',')
            parts_tl = line_tl.split(',')
            self.assertEqual(parts_r[1], parts_tl[1], f"Mismatch in start time for index {i}")
            self.assertEqual(parts_r[2], parts_tl[2], f"Mismatch in end time for index {i}: {parts_r[2]} vs {parts_tl[2]}")


class TestTimeBMicroBatch(unittest.TestCase):
    """Pruebas unitarias para micro-batch Time-B (Middle 1, Middle 2, Loop 1, Loop 2)."""

    def setUp(self):
        self.unit1 = _make_test_unit(i=1, n=4, start_time=1000, end_time=2000, dur=1000, text="A")
        self.unit2 = _make_test_unit(i=2, n=4, start_time=1200, end_time=2200, dur=1000, text="B")
        self.unit3 = _make_test_unit(i=3, n=4, start_time=1400, end_time=2400, dur=1000, text="C")
        self.unit4 = _make_test_unit(i=4, n=4, start_time=1600, end_time=2600, dur=1000, text="D")

        self.ctx1 = {'active_unit': self.unit1, 'fx_i': 1, 'fx_n': 3, 'J': 1, 'maxJ': 2}
        self.ctx2 = {'active_unit': self.unit2, 'fx_i': 2, 'fx_n': 3, 'J': 2, 'maxJ': 2}
        self.ctx4 = {'active_unit': self.unit4, 'fx_i': 3, 'fx_n': 3, 'J': 2, 'maxJ': 2}

    def test_direct_functions_delay_ms(self):
        # Middle 1
        self.assertEqual(time_middle_1(self.ctx1, delay_ms=30), -200.0)
        self.assertEqual(time_middle_1(self.ctx2, delay_ms=30), -170.0)
        self.assertEqual(time_middle_1(self.ctx4, delay_ms=30), -185.0)

        # Middle 2
        self.assertEqual(time_middle_2(self.ctx1, delay_ms=30), -215.0)
        self.assertEqual(time_middle_2(self.ctx4, delay_ms=30), -230.0)

        # Loop 1
        self.assertEqual(time_loop_1(self.ctx1, delay_ms=30, mode="leadin"), -200.0)
        self.assertEqual(time_loop_1(self.ctx2, delay_ms=30, mode="leadin"), -170.0)
        self.assertEqual(time_loop_1(self.ctx4, delay_ms=30, mode="leadout"), 170.0)

        # Loop 2
        self.assertEqual(time_loop_2(self.ctx1, delay_ms=30, mode="leadin"), -200.0)
        self.assertEqual(time_loop_2(self.ctx2, delay_ms=30, mode="leadin"), -170.0)
        self.assertEqual(time_loop_2(self.ctx4, delay_ms=30, mode="middle1"), -185.0)

    def test_graph_engine_time_b(self):
        from node_engine import GraphEngine

        # Middle 1
        node_m1 = {
            "id": 1,
            "type": "Time/Middle 1",
            "properties": {"delay_ms": "30"},
            "inputs": [{"name": "Delay (ms)", "property": "delay_ms"}]
        }
        engine_m1 = GraphEngine(graph_data={"nodes": [node_m1], "links": []})
        res_m1 = engine_m1.evaluate_data_node(1, self.ctx1, output_slot_index=0)
        self.assertEqual(float(res_m1), -200.0)

        # Middle 2
        node_m2 = {
            "id": 2,
            "type": "Time/Middle 2",
            "properties": {"delay_ms": "30"},
            "inputs": [{"name": "Delay (ms)", "property": "delay_ms"}]
        }
        engine_m2 = GraphEngine(graph_data={"nodes": [node_m2], "links": []})
        res_m2 = engine_m2.evaluate_data_node(2, self.ctx1, output_slot_index=0)
        self.assertEqual(float(res_m2), -215.0)

        # Loop 1
        node_l1 = {
            "id": 3,
            "type": "Time/Loop 1",
            "properties": {"delay_ms": "30", "mode": "leadin"},
            "inputs": [{"name": "Delay (ms)", "property": "delay_ms"}]
        }
        engine_l1 = GraphEngine(graph_data={"nodes": [node_l1], "links": []})
        res_l1 = engine_l1.evaluate_data_node(3, self.ctx1, output_slot_index=0)
        self.assertEqual(float(res_l1), -200.0)

        # Loop 2
        node_l2 = {
            "id": 4,
            "type": "Time/Loop 2",
            "properties": {"delay_ms": "30", "mode": "leadin"},
            "inputs": [{"name": "Delay (ms)", "property": "delay_ms"}]
        }
        engine_l2 = GraphEngine(graph_data={"nodes": [node_l2], "links": []})
        res_l2 = engine_l2.evaluate_data_node(4, self.ctx1, output_slot_index=0)
        self.assertEqual(float(res_l2), -200.0)


class TestTimeCMicroBatch(unittest.TestCase):
    """Pruebas unitarias completas para el micro-lote Time-C (Parse ASS Time, Format ASS Time, Time to Frame, Frame to Time)."""

    def setUp(self):
        self.unit = _make_test_unit(i=3, n=5, start_time=1500, end_time=3000, dur=1500, text="Time-C")
        self.line = _make_line(text="Time-C Test", start=1000, end=4000)
        self.ctx = {
            'active_unit': self.unit,
            'active_line': self.line,
            'j': 10,
            'J': 25,
            'frame_dur': 40.0
        }

    def test_parse_ass_time_canonical(self):
        # Explicit timestamp string
        self.assertEqual(time_parse_ass(self.ctx, ass_time="0:00:01.50"), 1500)
        self.assertEqual(time_parse_ass(self.ctx, ass_time="0:01:23.45"), 83450)
        self.assertEqual(time_parse_ass(self.ctx, ass_time="1:00:00.00"), 3600000)

        # Context fallback (unit / line)
        self.unit.start_str = "0:00:02.50"
        self.assertEqual(time_parse_ass(self.ctx, ass_time=""), 2500)

    def test_format_ass_time_canonical(self):
        # Explicit milliseconds
        self.assertEqual(time_format_ass(self.ctx, time=1500), "0:00:01.50")
        self.assertEqual(time_format_ass(self.ctx, time=83450), "0:01:23.45")
        self.assertEqual(time_format_ass(self.ctx, time=0), "0:00:00.00")

        # Context fallback
        self.assertEqual(time_format_ass(self.ctx, time=""), "0:00:01.50")

    def test_time_to_frame_canonical_modes_and_sources(self):
        # Modes: Ceil, Floor, Round
        self.assertEqual(time_to_frame_node(self.ctx, time_val=100, mode="Ceil"), 3)
        self.assertEqual(time_to_frame_node(self.ctx, time_val=100, mode="Floor"), 2)
        self.assertEqual(time_to_frame_node(self.ctx, time_val=105, mode="Round"), 3)

        # Sources: Start, End, Dur, Custom
        self.assertEqual(time_to_frame_node(self.ctx, source="Start Time", mode="Floor"), 37)
        self.assertEqual(time_to_frame_node(self.ctx, source="End Time", mode="Floor"), 75)
        self.assertEqual(time_to_frame_node(self.ctx, source="Duration", mode="Ceil"), 38)
        self.assertEqual(time_to_frame_node(self.ctx, source="Custom", time_val=200, mode="Floor"), 5)

    def test_frame_to_time_canonical_formats_and_sources(self):
        # Formats: ms, hms, sec
        self.assertEqual(frame_to_time_node(self.ctx, frames=50, format="MS"), 2000.0)
        self.assertEqual(frame_to_time_node(self.ctx, frames=50, format="HMS"), "0:00:02.00")
        self.assertEqual(frame_to_time_node(self.ctx, frames=50, format="SEC"), 2.0)

        # Sources: j, J, i, iter
        self.assertEqual(frame_to_time_node(self.ctx, source="j", format="MS"), 400.0)
        self.assertEqual(frame_to_time_node(self.ctx, source="J", format="MS"), 1000.0)
        self.assertEqual(frame_to_time_node(self.ctx, source="i", format="MS"), 120.0)
        self.assertEqual(frame_to_time_node(dict(self.ctx, k=8), source="Iterator", iter_name="k", format="MS"), 320.0)

        # Slot 1: ASS Timestamp
        self.assertEqual(frame_to_time_node(self.ctx, frames=50, format="MS", output_slot_index=1), "0:00:02.00")

    def test_graph_engine_evaluation_time_c(self):
        from node_engine import GraphEngine

        # Parse ASS Time in GraphEngine
        node_parse = {
            "id": 1,
            "type": "Time/Parse ASS Time",
            "properties": {"ass_time": "0:00:03.20"},
            "inputs": [{"name": "ASS Time", "property": "ass_time"}]
        }
        engine_parse = GraphEngine(graph_data={"nodes": [node_parse], "links": []})
        res_parse = engine_parse.evaluate_data_node(1, self.ctx, output_slot_index=0)
        self.assertEqual(int(res_parse), 3200)

        # Format ASS Time in GraphEngine
        node_format = {
            "id": 2,
            "type": "Time/Format ASS Time",
            "properties": {"time": "3200"},
            "inputs": [{"name": "Time (ms)", "property": "time"}]
        }
        engine_format = GraphEngine(graph_data={"nodes": [node_format], "links": []})
        res_format = engine_format.evaluate_data_node(2, self.ctx, output_slot_index=0)
        self.assertEqual(res_format, "0:00:03.20")

        # Time to Frame in GraphEngine
        node_t2f = {
            "id": 3,
            "type": "Time/Time to Frame",
            "properties": {"mode": "Floor", "source": "Custom", "time": "200", "frame_dur": "40.0"},
            "inputs": [{"name": "Time (ms)", "property": "time"}, {"name": "Frame Dur (ms)", "property": "frame_dur"}]
        }
        engine_t2f = GraphEngine(graph_data={"nodes": [node_t2f], "links": []})
        res_t2f = engine_t2f.evaluate_data_node(3, self.ctx, output_slot_index=0)
        self.assertEqual(int(res_t2f), 5)

        # Frame to Time in GraphEngine
        node_f2t = {
            "id": 4,
            "type": "Time/Frame to Time",
            "properties": {"format": "MS", "source": "Custom", "frames": "25", "frame_dur": "40.0"},
            "inputs": [{"name": "Frames (f)", "property": "frames"}, {"name": "Frame Dur (ms)", "property": "frame_dur"}]
        }
        engine_f2t = GraphEngine(graph_data={"nodes": [node_f2t], "links": []})
        res_f2t_ms = engine_f2t.evaluate_data_node(4, self.ctx, output_slot_index=0)
        self.assertEqual(float(res_f2t_ms), 1000.0)
        res_f2t_ass = engine_f2t.evaluate_data_node(4, self.ctx, output_slot_index=1)
        self.assertEqual(res_f2t_ass, "0:00:01.00")


class TestTimeDMicroBatch(unittest.TestCase):
    """Pruebas unitarias completas para el micro-lote Time-D (Ipol, Duration, Offset)."""

    def setUp(self):
        self.unit = _make_test_unit(i=1, n=3, start_time=1000, end_time=2500, dur=1500, text="Time-D")
        self.line = _make_line(text="Time-D Test", start=1000, end=4000)
        self.ctx = {
            'active_unit': self.unit,
            'active_line': self.line,
            'frame_dur': 40.0
        }

    def test_ipol_canonical(self):
        # Direct call with dur, points, accel
        res = time_ipol(self.ctx, dur=1000, points="0, 50, 100", accel=1.0)
        self.assertIn("[0.0, 500.0]", res)
        self.assertIn("[500.0, 1000.0]", res)

        # Non-linear easing (accel = 2.0)
        res_eased = time_ipol(self.ctx, dur_ms="1000", points="0, 100", accel="2.0")
        self.assertIn("[0.0, 1000.0]", res_eased)

        # Fallback to active_unit duration
        res_fallback = time_ipol(self.ctx, dur_ms="", points="0, 100", accel=1.0)
        self.assertIn("[0.0, 1500.0]", res_fallback)

    def test_offset_canonical(self):
        # Positive and negative offset
        self.assertEqual(time_offset(self.ctx, base=1000, offset=250), 1250)
        self.assertEqual(time_offset(self.ctx, base=1000, offset=-350), 650)

        # Context fallback for base
        self.assertEqual(time_offset(self.ctx, base="", offset_ms="200"), 1200)

        # Expressions in base / offset
        self.assertEqual(time_offset(self.ctx, base="500 * 2", offset="50 * 3"), 1150)

    def test_duration_canonical(self):
        # Explicit start and end
        self.assertEqual(time_duration(self.ctx, st=1000, et=3500), 2500)
        self.assertEqual(time_duration(self.ctx, start_time="500", end_time="1500"), 1000)

        # Context fallback (unit duration)
        self.assertEqual(time_duration(self.ctx, st="", et=""), 1500)

        # Line duration fallback when no active_unit
        ctx_line_only = {'active_unit': None, 'active_line': self.line}
        self.assertEqual(time_duration(ctx_line_only, st="", et=""), 3000)

    def test_graph_engine_evaluation_time_d(self):
        from node_engine import GraphEngine

        # Ipol via GraphEngine
        node_ipol = {
            "id": 1,
            "type": "Time/Ipol",
            "properties": {"dur_ms": "1000", "points": "0, 50, 100", "accel": "1.0"},
            "inputs": [
                {"name": "Duration (ms)", "property": "dur_ms"},
                {"name": "Points / Values", "property": "points"},
                {"name": "Acceleration", "property": "accel"}
            ]
        }
        engine_ipol = GraphEngine(graph_data={"nodes": [node_ipol], "links": []})
        res_ipol = engine_ipol.evaluate_data_node(1, self.ctx, output_slot_index=0)
        self.assertIn("[0.0, 500.0]", res_ipol)

        # Duration via GraphEngine
        node_dur = {
            "id": 2,
            "type": "Time/Duration",
            "properties": {"start_time": "1000", "end_time": "2500"},
            "inputs": [
                {"name": "Start Time (ms)", "property": "start_time"},
                {"name": "End Time (ms)", "property": "end_time"}
            ]
        }
        engine_dur = GraphEngine(graph_data={"nodes": [node_dur], "links": []})
        res_dur = engine_dur.evaluate_data_node(2, self.ctx, output_slot_index=0)
        self.assertEqual(int(res_dur), 1500)

        # Offset via GraphEngine
        node_offset = {
            "id": 3,
            "type": "Time/Offset",
            "properties": {"base": "1000", "offset_ms": "250"},
            "inputs": [
                {"name": "Base (ms)", "property": "base"}
            ]
        }
        engine_offset = GraphEngine(graph_data={"nodes": [node_offset], "links": []})
        res_offset = engine_offset.evaluate_data_node(3, self.ctx, output_slot_index=0)
        self.assertEqual(int(res_offset), 1250)


if __name__ == "__main__":
    unittest.main()




