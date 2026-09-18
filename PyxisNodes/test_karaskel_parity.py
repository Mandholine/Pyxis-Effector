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


"""Suite de pruebas de paridad y certificación para karaskel_engine.py y font_engine.py."""

import unittest 
from font_engine import FontEngine 
from karaskel_engine import (
KaraskelEngine ,KaraskelMeta ,KaraskelLine ,KaraskelSyllable ,KaraskelFurigana 
)


class TestKaraskelEngine (unittest .TestCase ):

    def setUp (self ):
        self .script_info ={
        "PlayResX":"1280",
        "PlayResY":"720"
        }
        self .default_style ={
        "name":"Default",
        "fontname":"Arial",
        "fontsize":35 ,
        "bold":False ,
        "italic":False ,
        "underline":False ,
        "strikeout":False ,
        "scale_x":100.0 ,
        "scale_y":100.0 ,
        "spacing":0.0 ,
        "margin_l":10 ,
        "margin_r":10 ,
        "margin_t":10 ,
        "margin_b":10 ,
        "align":2 
        }
        self .styles ={"Default":self .default_style }

    def test_collect_head_furigana_generation (self ):
        meta ,styles =KaraskelEngine .collect_head (self .script_info ,self .styles ,generate_furigana =True )
        self .assertEqual (meta .res_x ,1280 )
        self .assertEqual (meta .res_y ,720 )
        self .assertIn ("Default-furigana",styles )
        furi_style =styles ["Default-furigana"]
        self .assertEqual (furi_style ["fontsize"],17.5 )
        self .assertEqual (furi_style ["outline"],1.0 )
        self .assertEqual (furi_style ["shadow"],0.5 )

    def test_preproc_line_text_basic_karaoke (self ):
        meta ,styles =KaraskelEngine .collect_head (self .script_info ,self .styles )
        line =KaraskelLine (
        raw_text =r"{\k39}y {\k59}se {\k59}lo {\k39}hi{\k59}cie{\k79}ron",
        start_time =1000 ,
        end_time =4000 ,
        style ="Default"
        )
        KaraskelEngine .preproc_line_text (meta ,styles ,line )


        self .assertEqual (len (line .kara ),7 )
        self .assertEqual (line .kara [0 ].i ,0 )
        self .assertEqual (line .kara [0 ].text_stripped ,"")
        self .assertEqual (line .kara [1 ].text_spacestripped ,"y")
        self .assertEqual (line .kara [1 ].duration ,390 )
        self .assertEqual (line .kara [2 ].text_spacestripped ,"se")
        self .assertEqual (line .kara [2 ].duration ,590 )

    def test_multi_highlight_syllable (self ):
        meta ,styles =KaraskelEngine .collect_head (self .script_info ,self .styles )
        line =KaraskelLine (
        raw_text =r"{\k50}a{\k30}#b",
        start_time =0 ,
        end_time =1000 ,
        style ="Default"
        )
        KaraskelEngine .preproc_line_text (meta ,styles ,line )

        self .assertEqual (len (line .kara ),2 )
        syl1 =line .kara [1 ]
        self .assertEqual (len (syl1 .highlights ),2 )
        self .assertEqual (syl1 .duration ,800 )

    def test_furigana_parsing_and_prefix_stripping (self ):
        meta ,styles =KaraskelEngine .collect_head (self .script_info ,self .styles ,generate_furigana =True )
        line =KaraskelLine (
        raw_text =r"{\k50}漢|!かん{\k50}字|<じ",
        start_time =0 ,
        end_time =1000 ,
        style ="Default"
        )
        KaraskelEngine .preproc_line_text (meta ,styles ,line )

        self .assertEqual (len (line .furi ),2 )
        furi1 =line .furi [0 ]
        furi2 =line .furi [1 ]


        self .assertEqual (furi1 .text ,"かん")
        self .assertTrue (furi1 .isbreak )
        self .assertFalse (furi1 .spillback )

        self .assertEqual (furi2 .text ,"じ")
        self .assertTrue (furi2 .isbreak )
        self .assertTrue (furi2 .spillback )

    def test_full_line_positioning_and_alignment (self ):
        meta ,styles =KaraskelEngine .collect_head (self .script_info ,self .styles )
        line =KaraskelLine (
        raw_text =r"{\k50}Test Line",
        start_time =0 ,
        end_time =1000 ,
        style ="Default"
        )
        KaraskelEngine .preproc_line (meta ,styles ,line )

        self .assertGreater (line .width ,0.0 )
        self .assertGreater (line .height ,0.0 )

        expected_center =640.0 
        self .assertAlmostEqual (line .center ,expected_center ,delta =1.0 )
        self .assertAlmostEqual (line .bottom ,710.0 ,delta =1.0 )


        for i in range (len (line .kara )-1 ):
            self .assertLessEqual (line .kara [i ].left ,line .kara [i +1 ].left )


if __name__ =="__main__":
    unittest .main ()
