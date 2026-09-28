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


import math 
import os 
import re 
import time 
import threading 
import multiprocessing 
import concurrent .futures 
from typing import Any, Dict, Optional, List, Tuple 
from utils import format_time 
from decorators import NODE_REGISTRY ,PYXIS_DB 
import nodes_library 
from models import PyxisLine ,PyxisUnit 

_AN_RE = re.compile(r'\\an(?:\d*|(?=[\\\}\s]|$))')
_POS_RE =re .compile (r'\\pos\(')
_MOVE_RE =re .compile (r'\\move\(')
_TAG_BLOCK_RE =re .compile (r'\{.*?\}')


def _has_visible_content (unit )->bool :
    return bool (str (getattr (unit ,'text_stripped','')).strip ())


def _final_text_has_content (rendered :str )->bool :
    stripped =_TAG_BLOCK_RE .sub ('',str (rendered ))
    stripped =stripped .replace (r'\N',' ').replace (r'\n',' ').replace (r'\h',' ')
    return stripped .strip ()!=""


def _is_empty_value (value )->bool :
    return value is None or str (value ).strip ()==""


def _to_int_or_default (value ,default ,context =None ):
    if _is_empty_value (value ):
        if isinstance (default ,(int ,float )):
            return int (round (default ))
        if context is not None and isinstance (default ,str )and default .strip ():
            try :
                res_def =_eval_num_expr (default ,context ,default =0.0 )
                return int (round (float (res_def )))
            except Exception :
                pass 
        try :
            return int (round (float (default )))
        except (TypeError ,ValueError ):
            return 0 

    try :
        return int (round (float (value )))
    except (TypeError ,ValueError ):
        pass 
    if context is not None :
        try :
            res =_eval_num_expr (value ,context ,default =default )
            return int (round (float (res )))
        except Exception :
            pass 
    try :
        return int (round (float (default )))
    except (TypeError ,ValueError ):
        return 0 


def merge_ass_tags (return_tags_str :str ,port_tags_str :str ,context :Optional [Dict [str ,Any ]]=None )->str :
    r"""Combina y desduplica limpiamente las etiquetas ASS de Return y Tags port.
    Las etiquetas del puerto Tags tienen prioridad absoluta y reemplazan a las de Return en caso de colisión.
    Soporta secuencias complejas de etiquetas con cierre/apertura de llaves (ej: \p1}m 0 0 m 100 100 {\p0\r).
    """
    if not return_tags_str and not port_tags_str :
        return ""

    def _extract_head_and_tail (s_raw ):
        s = str (s_raw or '').strip ()
        if not s :
            return '', ''
        if s .startswith ('{') and s .endswith ('}'):
            s_inner = s [1 :-1 ].strip ()
        elif s .startswith ('{'):
            s_inner = s [1 :].strip ()
        else :
            s_inner = s
        if '}' in s_inner :
            parts = s_inner .split ('}', 1 )
            return parts [0 ], '}' + parts [1 ]
        return s_inner , ''

    clean_port_tags , port_tail = _extract_head_and_tail (port_tags_str )
    clean_return_tags , return_tail = _extract_head_and_tail (return_tags_str )

    try:
        from string_evaluator import expand_custom_dark_tags
        clean_port_tags = expand_custom_dark_tags(clean_port_tags, context)
        clean_return_tags = expand_custom_dark_tags(clean_return_tags, context)
    except Exception:
        pass

    def _parse_tag_dict (s_raw ):
        if not s_raw :return {}
        s =re .sub (r'[\{\}]','',str (s_raw )).strip ()
        if not s: return {}
        pattern = r'(\\[a-zA-Z0-9]+(?:\([^)]*\)|&[hH][0-9a-fA-F]+&|[0-9a-fA-F]+|[^\\\(]*))'
        matches =re .findall (pattern ,s )
        t_dict ={}
        t_cnt =0 
        for m in matches :
            m_str =m .strip ()
            if not m_str :continue 
            if m_str .startswith ('\\pos'):k ='pos'
            elif m_str .startswith ('\\org'):k ='org'
            elif m_str .startswith ('\\move'):k ='move'
            elif m_str .startswith ('\\iclip'):k ='iclip'
            elif m_str .startswith ('\\clip'):k ='clip'
            elif m_str .startswith ('\\fad')or m_str .startswith ('\\fade'):k ='fad'
            elif m_str .startswith ('\\t'):
                k =f't_{t_cnt }'
                t_cnt +=1 
            elif m_str .startswith ('\\an')or (m_str .startswith ('\\a')and not m_str .startswith ('\\alpha')and not re.match(r'^\\[1-4]a', m_str)):k ='an'
            elif m_str .startswith ('\\1c')or m_str .startswith ('\\c'):k ='1c'
            elif m_str .startswith ('\\2c'):k ='2c'
            elif m_str .startswith ('\\3c'):k ='3c'
            elif m_str .startswith ('\\4c'):k ='4c'
            elif m_str .startswith ('\\1a'):k ='1a'
            elif m_str .startswith ('\\2a'):k ='2a'
            elif m_str .startswith ('\\3a'):k ='3a'
            elif m_str .startswith ('\\4a'):k ='4a'
            elif m_str .startswith ('\\alpha'):k ='alpha'
            elif m_str .startswith ('\\fscx'):k ='fscx'
            elif m_str .startswith ('\\fscy'):k ='fscy'
            elif m_str .startswith ('\\frz')or (m_str .startswith ('\\fr') and not m_str.startswith('\\frx') and not m_str.startswith('\\fry')):k ='frz'
            elif m_str .startswith ('\\frx'):k ='frx'
            elif m_str .startswith ('\\fry'):k ='fry'
            elif m_str .startswith ('\\fax'):k ='fax'
            elif m_str .startswith ('\\fay'):k ='fay'
            elif m_str .startswith ('\\xbord'):k ='xbord'
            elif m_str .startswith ('\\ybord'):k ='ybord'
            elif m_str .startswith ('\\bord'):k ='bord'
            elif m_str .startswith ('\\xshad'):k ='xshad'
            elif m_str .startswith ('\\yshad'):k ='yshad'
            elif m_str .startswith ('\\shad'):k ='shad'
            elif m_str .startswith ('\\blur'):k ='blur'
            elif m_str .startswith ('\\be'):k ='be'
            elif m_str .startswith ('\\p'):k ='p'
            elif m_str .startswith ('\\q'):k ='q'
            elif m_str .startswith ('\\fn'):k ='fn'
            elif m_str .startswith ('\\fs') and not m_str.startswith('\\fsc') and not m_str.startswith('\\fsp'):k ='fs'
            elif m_str .startswith ('\\fsp'):k ='fsp'
            elif m_str .startswith ('\\b') and not m_str.startswith('\\blur') and not m_str.startswith('\\be') and not m_str.startswith('\\bord'):k ='b'
            elif m_str .startswith ('\\i') and not m_str.startswith('\\iclip'):k ='i'
            elif m_str .startswith ('\\u'):k ='u'
            elif m_str .startswith ('\\s') and not m_str.startswith('\\shad'):k ='s'
            elif m_str .startswith ('\\r'):k ='r'
            else :
                k =f"tag_{t_cnt}_{m_str}"
                t_cnt +=1
            t_dict [k ]=m_str 
        return t_dict 

    ret_dict =_parse_tag_dict (clean_return_tags )
    port_dict =_parse_tag_dict (clean_port_tags )

    ret_dict .update (port_dict )

    sorted_keys =sorted (ret_dict .keys (),key =lambda k :(
    0 if k =='an'else 
    1 if k in ('pos','move')else 
    2 if k =='org'else 
    3 if k in ('1c','2c','3c','4c','alpha','1a','2a','3a','4a')else 
    9 if k =='p'else 5 
    ))

    merged_head = ''.join (ret_dict [k ]for k in sorted_keys )
    tail = port_tail or return_tail
    return merged_head + tail


def _split_tokens_respecting_delimiters (s :str )->list :
    """Divide un string separado por comas, puntos y comas o saltos de línea respetando paréntesis () y llaves {}."""
    if not s :
        return []
    s =str (s ).strip ()
    tokens =[]
    curr =[]
    paren_depth =0 
    brace_depth =0 
    for ch in s :
        if ch =='(':
            paren_depth +=1 
            curr .append (ch )
        elif ch ==')':
            paren_depth =max (0 ,paren_depth -1 )
            curr .append (ch )
        elif ch =='{':
            brace_depth +=1 
            curr .append (ch )
        elif ch =='}':
            brace_depth =max (0 ,brace_depth -1 )
            curr .append (ch )
        elif ch in (',',';','\n')and paren_depth ==0 and brace_depth ==0 :
            token ="".join (curr ).strip ()
            if token :
                tokens .append (token )
            curr =[]
        else :
            curr .append (ch )
    if curr :
        token ="".join (curr ).strip ()
        if token :
            tokens .append (token )
    return tokens 


def _format_tagged_item (tag_prefix :str ,val )->str :
    """Aplica un prefijo de tag ASS a un valor formateando colores, alphas, coordenadas y escalares adecuadamente."""
    if val is None :
        return ""

    clean_prefix =str (tag_prefix ).strip ()
    if clean_prefix and not clean_prefix .startswith ('\\')and not clean_prefix .startswith ('{'):
        if not (clean_prefix .startswith ('&H')or clean_prefix .startswith ('&h')or clean_prefix .startswith ('#')):
            clean_prefix ='\\'+clean_prefix 

    s_val =str (val ).strip ()
    if not clean_prefix :
        return s_val 
    if not s_val :
        return clean_prefix 

    if s_val .startswith (clean_prefix ):
        return s_val 

    lower_pref =clean_prefix .lower ()


    if lower_pref in ('\\1c','\\2c','\\3c','\\4c','\\c'):
        if s_val .startswith ('\\'):
            return s_val 
        if s_val .startswith ('&H')or s_val .startswith ('&h'):
            ass_col =s_val if s_val .endswith ('&')else f"{s_val }&"
        elif s_val .startswith ('#')or (len (s_val )in (6 ,8 )and all (c in '0123456789abcdefABCDEF'for c in s_val )):
            try :
                from utils import parse_color_to_rgb ,rgb_to_ass_color 
                r ,g ,b =parse_color_to_rgb (s_val )
                ass_col =rgb_to_ass_color (r ,g ,b )
            except Exception :
                ass_col =s_val 
        else :
            ass_col =s_val 
        return f"{clean_prefix }{ass_col }"


    if lower_pref in ('\\1a','\\2a','\\3a','\\4a','\\alpha'):
        if s_val .startswith ('\\'):
            return s_val 
        if (s_val .startswith ('&H')or s_val .startswith ('&h'))and s_val .endswith ('&'):
            ass_alpha =s_val 
        else :
            try :
                clean_a =s_val .replace ('&H','').replace ('&h','').replace ('&','').replace ('#','').strip ()
                if len (clean_a )<=2 and all (c in '0123456789abcdefABCDEF'for c in clean_a ):
                    iv =int (clean_a ,16 )
                else :
                    iv =int (float (s_val ))
                iv =max (0 ,min (255 ,iv ))
                ass_alpha =f"&H{iv :02X}&"
            except Exception :
                ass_alpha =s_val 
        return f"{clean_prefix }{ass_alpha }"


    if lower_pref in ('\\pos','\\org','\\move','\\clip','\\iclip'):
        if s_val .startswith ('\\'):
            return s_val 
        if s_val .startswith ('(')and s_val .endswith (')'):
            return f"{clean_prefix }{s_val }"
        return f"{clean_prefix }({s_val })"


    if isinstance (val ,float )and val .is_integer ():
        s_val =str (int (val ))

    return f"{clean_prefix }{s_val }"


def _clean_key (k ):
    s =str (k ).lower ().strip ()
    s =s .replace ('ñ','n').replace ('º','').replace ('°','').replace ('(','').replace (')','').replace (',','')
    s =s .replace ('[','').replace (']','').replace ('\\','').replace ('/','_').replace ('-','_').replace ('.','')
    s =s .replace ('ión','ion').replace ('í','i').replace ('á','a').replace ('é','e').replace ('ó','o').replace ('ú','u')
    s =re .sub (r'\s+','_',s )
    s =re .sub (r'_+','_',s )
    return s .strip ('_')


def _get_prop_value (props ,key ,default =""):
    if not isinstance (props ,dict ):
        return default 
    if key in props and props [key ]is not None and str (props [key ]).strip ()!="":
        return props [key ]

    ck =_clean_key (key )
    for p ,v in props .items ():
        if v is not None and str (v ).strip ()!="":
            if _clean_key (p )==ck :
                return v 

    return default 



class ShapePresetsNamespace :
    """Helper namespace para exponer formas prediseñadas vía sintaxis shape.nombre (ej. shape.corazon, shape.circulo, shape.estrella_5t)."""
    def __getattr__ (self ,name ):
        from nodes .shape_nodes import resolve_shape_value 
        return resolve_shape_value (f"shape.{name }")

    def __getitem__ (self ,name ):
        return getattr (self ,name )

    def get (self ,name ,default =""):
        res =getattr (self ,name )
        return res if res else default 

    def __str__ (self ):
        return "ShapePresetsNamespace"


def _apply_fx_setting(name, value, context):
    if not isinstance(context, dict):
        return
    u = context.get("active_unit")
    if name in ("pos_x", "x"):
        val = float(value)
        context["fx_pos_x"] = val
        context["x"] = val
        context["val_x"] = val
        context["pos_x"] = val
        context["pos_overridden"] = True
        if u:
            try: setattr(u, "x", val)
            except Exception: pass
            try: setattr(u, "center", val)
            except Exception: pass
    elif name in ("pos_y", "y"):
        val = float(value)
        context["fx_pos_y"] = val
        context["y"] = val
        context["val_y"] = val
        context["pos_y"] = val
        context["pos_overridden"] = True
        if u:
            try: setattr(u, "y", val)
            except Exception: pass
            try: setattr(u, "middle", val)
            except Exception: pass
    elif name in ("start_time", "st", "time_start"):
        val = float(value)
        context["fx_start_time"] = val
        context["start_time"] = val
        context["st"] = val
        context["val_start"] = val
        if u:
            try: setattr(u, "start_time", val)
            except Exception: pass
            try: setattr(u, "st", val)
            except Exception: pass
    elif name in ("end_time", "et", "time_end", "time_fin"):
        val = float(value)
        context["fx_end_time"] = val
        context["end_time"] = val
        context["et"] = val
        context["val_end"] = val
        if u:
            try: setattr(u, "end_time", val)
            except Exception: pass
            try: setattr(u, "et", val)
            except Exception: pass
    elif name in ("dur", "duration", "time_dur"):
        val = float(value)
        context["fx_dur"] = val
        context["dur"] = val
        context["duration"] = val
        context["val_dur"] = val
        if u:
            try: setattr(u, "dur", val)
            except Exception: pass
            try: setattr(u, "duration", val)
            except Exception: pass
    elif name in ("org_x", "fx_org_x"):
        val = float(value)
        context["fx_org_x"] = val
        context["org_x"] = val
        context["has_org"] = True
    elif name in ("org_y", "fx_org_y"):
        val = float(value)
        context["fx_org_y"] = val
        context["org_y"] = val
        context["has_org"] = True
    elif name in ("align", "fx_align"):
        val = int(value)
        context["fx_align"] = val
    elif name == "origin_align":
        val = int(value)
        context["origin_align"] = val
    elif name in ("i", "fx_i"):
        val = int(value)
        context["fx_i"] = val
        context["i"] = val
        context["val_i"] = val
    elif name in ("n", "fx_n"):
        val = int(value)
        context["fx_n"] = val
        context["n"] = val
        context["val_n"] = val
    else:
        context[f"fx_{name}"] = value
        context[name] = value


class FxContext :
    """Helper class para exponer variables de efectos (fx.pos_x, fx.pos_y, fx.i, fx.n, etc.)."""
    def __init__ (self ,ctx ):
        object.__setattr__(self, "_ctx", ctx if isinstance (ctx ,dict )else {})

    def __setattr__(self, name, value):
        if name == "_ctx":
            object.__setattr__(self, "_ctx", value)
            return
        ctx = object.__getattribute__(self, "_ctx")
        if isinstance(ctx, dict):
            _apply_fx_setting(name, value, ctx)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)

    def __getattr__ (self ,name ):
        if name =="shape":
            return ShapePresetsNamespace ()
        if name .startswith ("shape."):
            return getattr (ShapePresetsNamespace (),name [6 :])


        if name in ("dur","duration","time_dur"):
            for k in ("fx_dur","effect_dur"):
                if k in self ._ctx :
                    return self ._ctx [k ]
            u =self ._ctx .get ("active_unit")
            l =self ._ctx .get ("line")
            return self ._ctx .get ("dur",getattr (u ,"duration",getattr (u ,"dur",getattr (l ,"duration",0.0 ))))


        if name in ("start_time","st","time_start"):
            for k in ("fx_start_time","fx_st","effect_st"):
                if k in self ._ctx :
                    return self ._ctx [k ]
            u =self ._ctx .get ("active_unit")
            l =self ._ctx .get ("line")
            return self ._ctx .get ("start_time",getattr (u ,"start_time",getattr (l ,"start_time",0.0 )))


        if name in ("end_time","et","time_end","time_fin"):
            for k in ("fx_end_time","fx_et","effect_et"):
                if k in self ._ctx :
                    return self ._ctx [k ]
            u =self ._ctx .get ("active_unit")
            l =self ._ctx .get ("line")
            return self ._ctx .get ("end_time",getattr (u ,"end_time",getattr (l ,"end_time",0.0 )))


        if name in ("x","pos_x"):
            return self ._ctx .get ("fx_pos_x",self ._ctx .get ("x",0.0 ))
        if name in ("y","pos_y"):
            return self ._ctx .get ("fx_pos_y",self ._ctx .get ("y",0.0 ))
        if name =="align":
            return self ._ctx .get ("fx_align",5 )


        if name =="i":
            return self ._ctx .get ("fx_i",self ._ctx .get ("i",1 ))
        if name =="n":
            return self ._ctx .get ("fx_n",self ._ctx .get ("n",1 ))


        fx_name =f"fx_{name }"
        if fx_name in self ._ctx :
            return self ._ctx [fx_name ]


        if name in ("val_left","left"):
            return self ._ctx .get ("val_left",getattr (self ._ctx .get ("active_unit"),"left",0.0 ))
        if name in ("val_center","center"):
            return self ._ctx .get ("val_center",getattr (self ._ctx .get ("active_unit"),"center",0.0 ))
        if name in ("val_right","right"):
            return self ._ctx .get ("val_right",getattr (self ._ctx .get ("active_unit"),"right",0.0 ))
        if name in ("val_top","top"):
            return self ._ctx .get ("val_top",getattr (self ._ctx .get ("active_unit"),"top",0.0 ))
        if name in ("val_middle","middle"):
            return self ._ctx .get ("val_middle",getattr (self ._ctx .get ("active_unit"),"middle",0.0 ))
        if name in ("val_bottom","bottom"):
            return self ._ctx .get ("val_bottom",getattr (self ._ctx .get ("active_unit"),"bottom",0.0 ))
        if name in ("val_width","width"):
            return self ._ctx .get ("val_width",getattr (self ._ctx .get ("active_unit"),"width",0.0 ))
        if name in ("val_height","height"):
            return self ._ctx .get ("val_height",getattr (self ._ctx .get ("active_unit"),"height",0.0 ))
        if name in ("val_start","val_st"):
            return self ._ctx .get ("val_start",0.0 )
        if name in ("val_end","val_et"):
            return self ._ctx .get ("val_end",0.0 )
        if name in ("val_dur",):
            return self ._ctx .get ("val_dur",0.0 )
        if name in ("val_mid",):
            return self ._ctx .get ("val_mid",0.0 )
        if name in ("val_i",):
            return self ._ctx .get ("val_i",1 )
        if name in ("val_n",):
            return self ._ctx .get ("val_n",1 )


        if name in self ._ctx :
            return self ._ctx [name ]
        return 0.0 

    def __getitem__ (self ,name ):
        return getattr (self ,name )


def _eval_sys_var (var_name :Any ,context :Any )->Any :
    if not var_name :
        return ""
    if not isinstance (context ,dict ):
        context ={}

    var_str =str (var_name ).strip ()

    if var_str .lower ().startswith ("shape."):
        from nodes .shape_nodes import resolve_shape_value 
        return resolve_shape_value (var_str ,context )


    if var_str =="frame_dur":
        return context .get ("frame_dur",40.0 )
    if var_str =="ratio":
        return context .get ("ratio",context .get ("module",0.0 ))

    active_unit =context .get ("active_unit")
    active_line =context .get ("active_line",context .get ("line"))
    if not active_line and hasattr (active_unit ,"line")and getattr (active_unit ,"line",None ):
        active_line =getattr (active_unit ,"line")
    if not active_line and active_unit and hasattr (active_unit ,"style_name"):
        active_line =active_unit 


    if var_str .startswith ("val_"):
        attr_name =var_str [4 :]
        if var_str in context :
            return context [var_str ]
        if attr_name in ("left","right","center","top","middle","bottom","width","height","x","y"):
            return getattr (active_unit ,attr_name ,0.0 )if active_unit else 0.0 
        if attr_name in ("start","st"):
            return getattr (active_unit ,"start_time",0.0 )if active_unit else 0.0 
        if attr_name in ("end","et"):
            return getattr (active_unit ,"end_time",0.0 )if active_unit else 0.0 
        if attr_name =="dur":
            return getattr (active_unit ,"dur",getattr (active_unit ,"duration",0.0 ))if active_unit else 0.0 
        if attr_name =="mid":
            st =getattr (active_unit ,"start_time",0.0 )if active_unit else 0.0 
            dur =getattr (active_unit ,"dur",getattr (active_unit ,"duration",0.0 ))if active_unit else 0.0 
            return st +(dur /2.0 )
        if attr_name =="i":
            return getattr (active_unit ,"i",1 )if active_unit else 1 
        if attr_name =="n":
            return getattr (active_unit ,"n",1 )if active_unit else 1 


    lookup_str =var_str 
    if lookup_str .startswith ("l."):
        lookup_str ="line."+lookup_str [2 :]


    if lookup_str =="line.style_name":
        lookup_str ="line.style"


    if lookup_str .startswith ("fx."):
        attr_name =lookup_str [3 :]
        if attr_name in ("start_time","st","time_start"):
            return context .get ("fx_start_time",context .get ("start_time",getattr (active_unit ,"start_time",0.0 )))
        if attr_name in ("end_time","et","time_end","time_fin"):
            return context .get ("fx_end_time",context .get ("end_time",getattr (active_unit ,"end_time",0.0 )))
        if attr_name in ("dur","duration","time_dur"):
            return context .get ("fx_dur",context .get ("effect_dur",context .get ("dur",getattr (active_unit ,"dur",getattr (active_unit ,"duration",0.0 )))))
        if attr_name =="i":
            return context .get ("fx_i",context .get ("i",getattr (active_unit ,"i",1 )))
        if attr_name =="n":
            return context .get ("fx_n",context .get ("n",getattr (active_unit ,"n",1 )))
        if attr_name in ("x","pos_x"):
            return context .get ("fx_pos_x",context .get ("x",getattr (active_unit ,"x",0.0 )))
        if attr_name in ("y","pos_y"):
            return context .get ("fx_pos_y",context .get ("y",getattr (active_unit ,"y",0.0 )))
        if attr_name in ("module","m"):
            return context .get ("module",0.0 )
        return context .get (f"fx_{attr_name }",context .get (attr_name ,0.0 ))


    if lookup_str .startswith ("time."):
        time_type =lookup_str [5 :]
        from nodes .time_nodes import time_lead_in ,time_lead_out ,time_middle_1 ,time_middle_2 ,time_loop_1 ,time_loop_2 
        if time_type =="lead_in":return time_lead_in (context )
        if time_type =="lead_out":return time_lead_out (context )
        if time_type =="middle_1":return time_middle_1 (context )
        if time_type =="middle_2":return time_middle_2 (context )
        if time_type =="loop_1":return time_loop_1 (context )
        if time_type =="loop_2":return time_loop_2 (context )


    if lookup_str .startswith ("line."):
        attr_name =lookup_str [5 :]
        target_obj =active_line if active_line else active_unit 
        if not target_obj :
            return ""
        if attr_name =="text":
            return getattr (target_obj ,"text_stripped",getattr (target_obj ,"text",""))
        if attr_name in ("dur","duration"):
            return getattr (target_obj ,"dur",getattr (target_obj ,"duration",0 ))
        if attr_name =="style":
            return getattr (target_obj ,"style",getattr (target_obj ,"style_name","Default"))
        if hasattr (target_obj ,attr_name ):
            val =getattr (target_obj ,attr_name )
            return val ()if callable (val )else val 
        styleref =getattr (target_obj ,"styleref",None )
        if styleref and hasattr (styleref ,attr_name ):
            val =getattr (styleref ,attr_name )
            return val ()if callable (val )else val 
        return ""


    if lookup_str .startswith ("syl."):
        attr_name =lookup_str [4 :]
        target_obj =context .get ("syl",active_unit )
        if not target_obj :return ""
        if attr_name =="text":
            return getattr (target_obj ,"text_stripped",getattr (target_obj ,"text",""))
        if attr_name in ("dur","duration"):
            return getattr (target_obj ,"dur",getattr (target_obj ,"duration",0 ))
        if hasattr (target_obj ,attr_name ):
            val =getattr (target_obj ,attr_name )
            return val ()if callable (val )else val 
        return ""


    if lookup_str .startswith ("char."):
        attr_name =lookup_str [5 :]
        target_obj =context .get ("char",active_unit )
        if not target_obj :return ""
        if attr_name in ("dur","duration"):
            return getattr (target_obj ,"dur",getattr (target_obj ,"duration",0 ))
        if hasattr (target_obj ,attr_name ):
            val =getattr (target_obj ,attr_name )
            return val ()if callable (val )else val 
        return ""


    if lookup_str .startswith ("word."):
        attr_name =lookup_str [5 :]
        target_obj =context .get ("word",active_unit )
        if not target_obj :return ""
        if attr_name =="text":
            return getattr (target_obj ,"text_stripped",getattr (target_obj ,"text",""))
        if attr_name in ("dur","duration"):
            return getattr (target_obj ,"dur",getattr (target_obj ,"duration",0 ))
        if hasattr (target_obj ,attr_name ):
            val =getattr (target_obj ,attr_name )
            return val ()if callable (val )else val 
        return ""


    if lookup_str .startswith ("meta."):
        attr_name =lookup_str [5 :]
        if attr_name =="res_x":
            proc =context .get ("processor")
            return proc .res_x if proc else context .get ("res_x",1280 )
        if attr_name =="res_y":
            proc =context .get ("processor")
            return proc .res_y if proc else context .get ("res_y",720 )


    if lookup_str in context :
        return context [lookup_str ]
    if active_unit and hasattr (active_unit ,lookup_str ):
        val =getattr (active_unit ,lookup_str )
        return val ()if callable (val )else val 

    return ""

_EVAL_EXPR_CACHE ={}
_STATIC_EVAL_GLOBALS =None 

def _get_static_eval_globals ():
    global _STATIC_EVAL_GLOBALS 
    if _STATIC_EVAL_GLOBALS is not None :
        return _STATIC_EVAL_GLOBALS 

    import math 
    safe_builtins ={
    "min":min ,"max":max ,"abs":abs ,"round":round ,
    "int":int ,"float":float ,"pow":pow ,"sum":sum ,
    "len":len ,"str":str ,"bool":bool 
    }
    g ={"math":math ,"__builtins__":safe_builtins }
    for k ,v in safe_builtins .items ():
        g [k ]=v 
    for fn in ("sin","cos","tan","sqrt","ceil","floor","atan2","degrees","radians","hypot","log","exp","pi"):
        if hasattr (math ,fn ):
            g [fn ]=getattr (math ,fn )
    from decorators import NODE_REGISTRY 
    for k ,v in NODE_REGISTRY .items ():
        fn_name =v .__name__ 
        g [fn_name ]=v 

    from nodes .audio_nodes import audio_rms ,audio_peak ,audio_band ,audio_fft 
    g ["audio_rms"]=audio_rms 
    g ["audio_peak"]=audio_peak 
    g ["audio_band"]=audio_band 
    g ["audio_fft"]=audio_fft 

    from nodes .math_nodes import math_random_master 
    g ["R"]=math_random_master 
    g ["Rs"]=math_random_master 
    g ["Rc"]=math_random_master 
    g ["shape"]=ShapePresetsNamespace ()

    try:
        from nodes.code_nodes import (
            _pyxis_pos, _pyxis_move, _pyxis_org, _pyxis_fad, _pyxis_fade,
            _pyxis_clip, _pyxis_iclip, _pyxis_c1, _pyxis_c2, _pyxis_c3, _pyxis_c4,
            _pyxis_a1, _pyxis_a2, _pyxis_a3, _pyxis_a4, _pyxis_alpha, _pyxis_trans,
            _pyxis_fscx, _pyxis_fscy, _pyxis_fscxy, _pyxis_frz, _pyxis_frx, _pyxis_fry,
            _pyxis_fax, _pyxis_fay, _pyxis_bord, _pyxis_shad, _pyxis_blur, _pyxis_an,
            _pyxis_ass_color, _pyxis_ass_alpha, _pyxis_random_color, _pyxis_random_alpha,
            _pyxis_clamp, _pyxis_lerp, _pyxis_map_range, _pyxis_ease_in, _pyxis_ease_out,
            _pyxis_ease_in_out, _pyxis_cubic_in, _pyxis_cubic_out, _pyxis_elastic,
            _pyxis_bounce, _pyxis_back, _pyxis_sine_wave, _pyxis_square_wave,
            _pyxis_triangle_wave, _pyxis_sawtooth_wave, _pyxis_polar, _pyxis_bezier,
            _pyxis_ipol, _pyxis_time_to_frame, _pyxis_duration, _pyxis_parse_ass_time,
            _pyxis_format_ass_time, _pyxis_strip_tags, _pyxis_kana
        )
        g.update({
            "pos": _pyxis_pos, "move": _pyxis_move, "org": _pyxis_org, "fad": _pyxis_fad, "fade": _pyxis_fade,
            "clip": _pyxis_clip, "iclip": _pyxis_iclip, "c1": _pyxis_c1, "c2": _pyxis_c2, "c3": _pyxis_c3, "c4": _pyxis_c4,
            "color_1": _pyxis_c1, "color_2": _pyxis_c2, "color_3": _pyxis_c3, "color_4": _pyxis_c4,
            "a1": _pyxis_a1, "a2": _pyxis_a2, "a3": _pyxis_a3, "a4": _pyxis_a4, "alpha": _pyxis_alpha,
            "trans": _pyxis_trans, "fscx": _pyxis_fscx, "fscy": _pyxis_fscy, "fscxy": _pyxis_fscxy,
            "frz": _pyxis_frz, "frx": _pyxis_frx, "fry": _pyxis_fry, "fax": _pyxis_fax, "fay": _pyxis_fay,
            "bord": _pyxis_bord, "shad": _pyxis_shad, "blur": _pyxis_blur, "an": _pyxis_an,
            "ass_color": _pyxis_ass_color, "ass_alpha": _pyxis_ass_alpha,
            "random_color": _pyxis_random_color, "random_alpha": _pyxis_random_alpha,
            "clamp": _pyxis_clamp, "lerp": _pyxis_lerp, "map_range": _pyxis_map_range, "map_value": _pyxis_map_range,
            "ease_in": _pyxis_ease_in, "ease_out": _pyxis_ease_out, "ease_in_out": _pyxis_ease_in_out,
            "cubic_in": _pyxis_cubic_in, "cubic_out": _pyxis_cubic_out, "elastic": _pyxis_elastic,
            "bounce": _pyxis_bounce, "back": _pyxis_back,
            "sine_wave": _pyxis_sine_wave, "square_wave": _pyxis_square_wave,
            "triangle_wave": _pyxis_triangle_wave, "sawtooth_wave": _pyxis_sawtooth_wave,
            "polar": _pyxis_polar, "bezier": _pyxis_bezier, "ipol": _pyxis_ipol,
            "time_to_frame": _pyxis_time_to_frame, "duration": _pyxis_duration,
            "parse_ass_time": _pyxis_parse_ass_time, "format_ass_time": _pyxis_format_ass_time,
            "strip_tags": _pyxis_strip_tags, "kana": _pyxis_kana
        })
    except ImportError:
        pass

    _STATIC_EVAL_GLOBALS =g 
    return _STATIC_EVAL_GLOBALS 


class AttrDict (dict ):
    """Permite acceso por atributo (.campo) a diccionarios en expresiones de eval()."""
    def __getattr__ (self ,name ):
        if name in self :
            val =self [name ]
            return AttrDict (val )if isinstance (val ,dict )else val 
        raise AttributeError (f"'dict' object has no attribute '{name }'")

    def __setattr__ (self ,name ,value ):
        self [name ]=value 


def _eval_num_expr (val ,context =None ,default =0.0 ):
    if val is None or val =="":
        return default 
    if isinstance (val ,(int ,float )):
        return float (val )
    val_str =str (val ).strip ()
    if not val_str :
        return default 


    m_comma =re .match (r"^([+-]?\d+),(\d+)$",val_str )
    if m_comma :
        try :
            return float (f"{m_comma .group (1 )}.{m_comma .group (2 )}")
        except Exception :
            pass 


    m_hex =re .match (r"^&[hH]([0-9a-fA-F]+)&?$",val_str )
    if m_hex :
        try :
            return float (int (m_hex .group (1 ),16 ))
        except Exception :
            pass 

    try :
        return float (val_str )
    except (ValueError ,TypeError ):
        pass 

    try :
        code_obj =_EVAL_EXPR_CACHE .get (val_str )
        if code_obj is None :

            clean_expr =re .sub (r'&[hH]([0-9a-fA-F]+)&?',r'0x\1',val_str )
            frame_dur = context.get("frame_dur", 41.708333333333336) if isinstance(context, dict) else 41.708333333333336
            ratio = context.get("ratio", context.get("module", 1.0)) if isinstance(context, dict) else 1.0
            clean_expr = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*f\b', rf'(\1 * {frame_dur})', clean_expr)
            clean_expr = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*r\b', rf'(\1 * {ratio})', clean_expr)
            clean_expr = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*(li|lo|m1|m2|l1|l2)\b',r'\1 * \2',clean_expr )
            code_obj =compile (clean_expr ,"<eval_expr>","eval")
            _EVAL_EXPR_CACHE [val_str ]=code_obj 

        eval_globals =_get_static_eval_globals ()
        eval_locals =dict (context )if isinstance (context ,dict )else {}
        for k ,v in list (eval_locals .items ()):
            if isinstance (v ,dict )and not isinstance (v ,AttrDict ):
                eval_locals [k ]=AttrDict (v )

        try:
            from nodes.code_nodes import PyxisTimeModifier
            from nodes.time_nodes import time_lead_in, time_lead_out, time_middle_1, time_middle_2, time_loop_1, time_loop_2
            eval_locals ["time_lead_in"]=lambda delay=40, base=None: time_lead_in(context, delay=delay, base=base)
            eval_locals ["time_lead_out"]=lambda delay=40, base=None: time_lead_out(context, delay=delay, base=base)
            eval_locals ["time_middle_1"]=lambda delay=30, base=None: time_middle_1(context, delay=delay, base=base)
            eval_locals ["time_middle_2"]=lambda delay=30, base=None: time_middle_2(context, delay=delay, base=base)
            eval_locals ["time_loop_1"]=lambda delay=30, mode="leadin", base=None: time_loop_1(context, delay=delay, mode=mode, base=base)
            eval_locals ["time_loop_2"]=lambda delay=30, mode="leadin", base=None: time_loop_2(context, delay=delay, mode=mode, base=base)

            eval_locals ["li"]=PyxisTimeModifier(time_lead_in, context, default_delay=40.0)
            eval_locals ["lo"]=PyxisTimeModifier(time_lead_out, context, default_delay=40.0)
            eval_locals ["m1"]=PyxisTimeModifier(time_middle_1, context, default_delay=30.0)
            eval_locals ["m2"]=PyxisTimeModifier(time_middle_2, context, default_delay=30.0)
            eval_locals ["l1"]=PyxisTimeModifier(time_loop_1, context, default_delay=30.0, mode="leadin")
            eval_locals ["l2"]=PyxisTimeModifier(time_loop_2, context, default_delay=30.0, mode="leadin")
        except Exception:
            pass

        eval_locals ["audio_rms"]=lambda *args ,**kwargs :eval_globals ["audio_rms"](*args ,context =context ,**kwargs )
        eval_locals ["audio_peak"]=lambda *args ,**kwargs :eval_globals ["audio_peak"](*args ,context =context ,**kwargs )
        eval_locals ["audio_band"]=lambda *args ,**kwargs :eval_globals ["audio_band"](*args ,context =context ,**kwargs )
        eval_locals ["audio_fft"]=lambda *args ,**kwargs :eval_globals ["audio_fft"](*args ,context =context ,**kwargs )
        eval_locals ["R"]=lambda min_v =0 ,max_v =100 ,step_v =1 :eval_globals ["R"](context ,modo ="R",min_val =min_v ,max_val =max_v ,step =step_v )
        eval_locals ["Rs"]=lambda min_v =0 ,max_v =100 :eval_globals ["Rs"](context ,modo ="Rs",min_val =min_v ,max_val =max_v )
        eval_locals ["Rc"]=lambda min_v =0 ,max_v =100 :eval_globals ["Rc"](context ,modo ="Rc",min_val =min_v ,max_val =max_v )

        if "active_unit"in eval_locals and eval_locals ["active_unit"]:
            unit_obj =eval_locals ["active_unit"]
            if "syl"not in eval_locals or eval_locals ["syl"]is None :
                eval_locals ["syl"]=unit_obj 
            if "line"not in eval_locals and hasattr (unit_obj ,"line")and unit_obj .line :
                eval_locals ["line"]=unit_obj .line 

        if "line"in eval_locals and ("l"not in eval_locals or eval_locals ["l"]is None ):
            eval_locals ["l"]=eval_locals ["line"]

        if "maxj"not in eval_locals :
            eval_locals ["maxj"]=eval_locals .get ("fx_n",eval_locals .get ("maxloop",1 ))
        if "maxloop"not in eval_locals :
            eval_locals ["maxloop"]=eval_locals .get ("maxj",eval_locals .get ("fx_n",1 ))
        if "max_loop"not in eval_locals :
            eval_locals ["max_loop"]=eval_locals .get ("maxj",eval_locals .get ("fx_n",1 ))
        if "j"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["j"]=eval_locals ["fx_i"]
        if "a_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["a_i"]=eval_locals ["fx_i"]
        if "a_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["a_n"]=eval_locals ["fx_n"]
        if "a_max"not in eval_locals :
            eval_locals ["a_max"]=eval_locals .get ("a_n",eval_locals .get ("maxloop",1 ))
        if "s_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["s_i"]=eval_locals ["fx_i"]
        if "s_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["s_n"]=eval_locals ["fx_n"]
        if "s_max"not in eval_locals :
            eval_locals ["s_max"]=eval_locals .get ("s_n",eval_locals .get ("maxloop",1 ))
        if "p_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["p_i"]=eval_locals ["fx_i"]
        if "p_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["p_n"]=eval_locals ["fx_n"]
        if "p_max"not in eval_locals :
            eval_locals ["p_max"]=eval_locals .get ("p_n",eval_locals .get ("maxloop",1 ))
        if "tp_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["tp_i"]=eval_locals ["fx_i"]
        if "tp_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["tp_n"]=eval_locals ["fx_n"]
        if "tp_max"not in eval_locals :
            eval_locals ["tp_max"]=eval_locals .get ("tp_n",eval_locals .get ("maxloop",1 ))
        if "an_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["an_i"]=eval_locals ["fx_i"]
        if "an_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["an_n"]=eval_locals ["fx_n"]
        if "an_max"not in eval_locals :
            eval_locals ["an_max"]=eval_locals .get ("an_n",eval_locals .get ("maxloop",1 ))
        if "anim_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["anim_i"]=eval_locals ["fx_i"]
        if "anim_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["anim_n"]=eval_locals ["fx_n"]
        if "anim_max"not in eval_locals :
            eval_locals ["anim_max"]=eval_locals .get ("anim_n",eval_locals .get ("maxloop",1 ))
        if "b_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["b_i"]=eval_locals ["fx_i"]
        if "b_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["b_n"]=eval_locals ["fx_n"]
        if "b_max"not in eval_locals :
            eval_locals ["b_max"]=eval_locals .get ("b_n",eval_locals .get ("maxloop",1 ))
        if "c_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["c_i"]=eval_locals ["fx_i"]
        if "c_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["c_n"]=eval_locals ["fx_n"]
        if "c_max"not in eval_locals :
            eval_locals ["c_max"]=eval_locals .get ("c_n",eval_locals .get ("maxloop",1 ))
        if "d_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["d_i"]=eval_locals ["fx_i"]
        if "d_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["d_n"]=eval_locals ["fx_n"]
        if "d_max"not in eval_locals :
            eval_locals ["d_max"]=eval_locals .get ("d_n",eval_locals .get ("maxloop",1 ))
        if "m_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["m_i"]=eval_locals ["fx_i"]
        if "m_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["m_n"]=eval_locals ["fx_n"]
        if "m_max"not in eval_locals :
            eval_locals ["m_max"]=eval_locals .get ("m_n",eval_locals .get ("maxloop",1 ))
        if "multi_i"not in eval_locals and "fx_i"in eval_locals :
            eval_locals ["multi_i"]=eval_locals ["fx_i"]
        if "multi_n"not in eval_locals and "fx_n"in eval_locals :
            eval_locals ["multi_n"]=eval_locals ["fx_n"]
        if "multi_max"not in eval_locals :
            eval_locals ["multi_max"]=eval_locals .get ("multi_n",eval_locals .get ("maxloop",1 ))

        if "fx"not in eval_locals or eval_locals ["fx"]is None or not isinstance (eval_locals ["fx"],FxContext )or eval_locals ["fx"]._ctx is not eval_locals :
            eval_locals ["fx"]=FxContext (eval_locals )

        res =eval (code_obj ,eval_globals ,eval_locals )
        return float (res )if res is not None else float (default )
    except Exception :
        return default 


_PROFILER_ENABLED =False 
_GLOBAL_ACTIVE_EXECUTOR =None 
_WORKER_LINE_COUNTER =None 
_WORKER_CANCEL_FLAG =None 

def _worker_init (line_counter ,cancel_flag ):
    global _WORKER_LINE_COUNTER ,_WORKER_CANCEL_FLAG 
    _WORKER_LINE_COUNTER =line_counter 
    _WORKER_CANCEL_FLAG =cancel_flag 

def abort_global_multiprocessing ():
    global _GLOBAL_ACTIVE_EXECUTOR 
    if _GLOBAL_ACTIVE_EXECUTOR is not None :
        try :
            _GLOBAL_ACTIVE_EXECUTOR .shutdown (wait =False ,cancel_futures =True )
        except Exception :
            pass 
        _GLOBAL_ACTIVE_EXECUTOR =None 


class GraphEngine :
    def __init__ (self ,graph_data =None ,rx =1280 ,ry =720 ,fd =41.708 ,default_audio_source =""):
        if graph_data is None :
            graph_data ={"nodes":[],"links":[]}
        self .raw_graph =graph_data 
        self .nodes ={n ['id']:n for n in graph_data .get ('nodes',[])}
        self .links =graph_data .get ('links',[])
        self .all_generated_lines =[]
        self .rx ,self .ry ,self .fd =rx ,ry ,fd 
        self .default_audio_source =default_audio_source 
        self .is_cancelled =False 
        self ._cancel_check_counter =0 
        self .memory ={}
        self ._once_cache ={}
        self ._has_audio_nodes =any (
        'audio'in str (n .get ('type','')).lower ()or 
        'waveform'in str (n .get ('type','')).lower ()or 
        'modulador'in str (n .get ('type','')).lower ()
        for n in self .nodes .values ()
        )

    def remember (self ,key ,val ):
        self .memory [str (key )]=val 
        return val 

    def recall (self ,key ,default =""):
        return self .memory .get (str (key ),default )

    def is_port_connected (self ,target_node ,input_index ):
        inputs =target_node .get ('inputs',[])
        if len (inputs )<=input_index :return False 
        inp =inputs [input_index ]
        if not inp or not isinstance (inp ,dict ):return False 
        return bool (inp .get ('link')is not None or (isinstance (inp .get ('links'),list )and len (inp .get ('links'))>0 ))

    def get_input_value (self ,target_node ,input_index ,context ):
        if not self .is_port_connected (target_node ,input_index ):
            inputs =target_node .get ('inputs',[])
            if input_index <len (inputs ):
                inp =inputs [input_index ]
                if inp and isinstance (inp ,dict ):
                    p_name =inp .get ('property')or inp .get ('name')
                    props =target_node .get ('properties',{})
                    if p_name :
                        val =_get_prop_value (props ,p_name ,default ="")
                        if val !="":
                            if str (val ).strip ().lower ().startswith ("shape."):
                                from nodes .shape_nodes import resolve_shape_value 
                                return resolve_shape_value (val ,context )
                            return str (val )
                    if inp .get ('name'):
                        val =_get_prop_value (props ,inp .get ('name'),default ="")
                        if val !="":
                            if str (val ).strip ().lower ().startswith ("shape."):
                                from nodes .shape_nodes import resolve_shape_value 
                            return resolve_shape_value (val ,context )
                        return str (val )
                    if 'value'in inp and inp ['value']is not None and str (inp ['value']).strip ()!="":
                        raw_val =str (inp ['value']).strip ()
                        if raw_val .lower ().startswith ("shape."):
                            from nodes .shape_nodes import resolve_shape_value 
                            return resolve_shape_value (raw_val ,context )
                        return raw_val 
            return ""
        inputs =target_node .get ('inputs',[])
        if input_index <len (inputs ):
            inp =inputs [input_index ]
            if not inp or not isinstance (inp ,dict ):
                return ""
            link_ids =[]
            if isinstance (inp .get ('links'),list )and len (inp ['links'])>0 :
                link_ids =inp ['links']
            elif inp .get ('link')is not None :
                link_ids =[inp ['link']]

            results =[]
            for l_id in link_ids :
                link =next ((l for l in self .links if l [0 ]==l_id ),None )
                if link :
                    val =self .evaluate_data_node (link [1 ],context ,output_slot_index =link [2 ])
                    if val is not None and str (val )!="":
                        results .append (str (val ))
            if len (results )>1 :
                return "".join (results )
            elif len (results )==1 :
                return results [0 ]
        return ""

    def bind_active_unit (self ,context ,unit ,is_noblank =True ,output_node =None ):
        context ['active_unit']=unit 
        context ['default_audio_source']=self .default_audio_source 
        if unit :
            if not context .get ('syl'):
                context ['syl']=getattr (unit ,'syl',unit )
            if not context .get ('sili'):
                context ['sili']=context ['syl']
            if not context .get ('char')and hasattr (unit ,'char'):
                context ['char']=getattr (unit ,'char',None )
            if not context .get ('word')and hasattr (unit ,'word'):
                context ['word']=getattr (unit ,'word',None )

            if is_noblank :
                ci_val =int (getattr (unit ,'ci',getattr (unit ,'i',1 )))
                cn_val =int (getattr (unit ,'cn',getattr (unit ,'n',1 )))
                unit .i =ci_val 
                unit .n =cn_val 
                context ['i']=ci_val 
                context ['n']=cn_val 
                context ['fx_i']=ci_val 
                context ['fx_n']=cn_val 
            else :
                i_val =int (getattr (unit ,'i',1 ))
                n_val =int (getattr (unit ,'n',1 ))
                context ['i']=i_val 
                context ['n']=n_val 
                context ['fx_i']=i_val 
                context ['fx_n']=n_val 

            def _safe_float_val (v ,default =0.0 ):
                if v is None :
                    return float (default )
                try :
                    return float (v )
                except Exception :
                    return float (default )

            u_center =_safe_float_val (getattr (unit ,'center',0.0 ),0.0 )
            u_middle =_safe_float_val (getattr (unit ,'middle',0.0 ),0.0 )
            u_left =_safe_float_val (getattr (unit ,'left',u_center ),u_center )
            u_right =_safe_float_val (getattr (unit ,'right',u_center ),u_center )
            u_top =_safe_float_val (getattr (unit ,'top',u_middle ),u_middle )
            u_bottom =_safe_float_val (getattr (unit ,'bottom',u_middle ),u_middle )
            u_width =_safe_float_val (getattr (unit ,'width',max (0.0 ,u_right -u_left )),max (0.0 ,u_right -u_left ))
            u_height =_safe_float_val (getattr (unit ,'height',max (0.0 ,u_bottom -u_top )),max (0.0 ,u_bottom -u_top ))
            u_x =_safe_float_val (getattr (unit ,'x',u_center ),u_center )
            u_y =_safe_float_val (getattr (unit ,'y',u_middle ),u_middle )

            if output_node is None :
                output_node =context .get ('output_node')
                if output_node is None and hasattr (self ,'get_output_nodes'):
                    outs =self .get_output_nodes ()
                    if outs :
                        output_node =outs [0 ]

            origin_align =5 
            if output_node and isinstance (output_node ,dict ):
                props =output_node .get ('properties',{})
                try :
                    origin_align =int (props .get ('origin_align',5 ))
                    if origin_align <1 or origin_align >9 :
                        origin_align =5 
                except Exception :
                    origin_align =5 
            elif isinstance (context ,dict )and 'origin_align'in context :
                try :
                    origin_align =int (context .get ('origin_align',5 ))
                    if origin_align <1 or origin_align >9 :
                        origin_align =5 
                except Exception :
                    origin_align =5 

            context ['origin_align']=origin_align 
            context ['fx_align']=5 

            if origin_align in (7 ,4 ,1 ):
                final_x =u_left 
            elif origin_align in (9 ,6 ,3 ):
                final_x =u_right 
            else :
                final_x =u_center if u_center !=0.0 else u_x 

            if origin_align in (7 ,8 ,9 ):
                final_y =u_top 
            elif origin_align in (1 ,2 ,3 ):
                final_y =u_bottom 
            else :
                final_y =u_middle if u_middle !=0.0 else u_y 

            context ['fx_pos_x']=round (final_x ,3 )
            context ['fx_pos_y']=round (final_y ,3 )
            context ['x']=final_x 
            context ['y']=final_y 
            context ['fx_start_time']=getattr (unit ,'start_time',0 )
            context ['fx_end_time']=getattr (unit ,'end_time',0 )
            context ['fx_dur']=getattr (unit ,'dur',getattr (unit ,'duration',0 ))


            context ['val_left']=round (u_left ,3 )
            context ['val_center']=round (u_center ,3 )
            context ['val_right']=round (u_right ,3 )
            context ['val_top']=round (u_top ,3 )
            context ['val_middle']=round (u_middle ,3 )
            context ['val_bottom']=round (u_bottom ,3 )
            context ['val_width']=round (u_width ,3 )
            context ['val_height']=round (u_height ,3 )
            context ['val_x']=round (final_x ,3 )
            context ['val_y']=round (final_y ,3 )

        line_obj =context .get ('line')
        line_st =float (getattr (line_obj ,'start_time',0.0 ))if line_obj else 0.0 
        line_et =float (getattr (line_obj ,'end_time',0.0 ))if line_obj else 0.0 
        context ['line_start_time']=line_st 
        context ['line_end_time']=line_et 
        context ['line_dur']=max (0.0 ,line_et -line_st )

        unit_st =float (getattr (unit ,'start_time',line_st ))if unit else line_st 
        unit_et =float (getattr (unit ,'end_time',line_et ))if unit else line_et 
        unit_dur =float (getattr (unit ,'dur',getattr (unit ,'duration',max (0.0 ,unit_et -unit_st ))))if unit else max (0.0 ,unit_et -unit_st )

        context ['start_time']=unit_st 
        context ['end_time']=unit_et 
        context ['st']=unit_st 
        context ['et']=unit_et 
        context ['dur']=unit_dur 
        context ['duration']=unit_dur 
        context ['val_start']=unit_st 
        context ['val_end']=unit_et 
        context ['val_dur']=unit_dur 
        context ['val_mid']=round (unit_st +(unit_dur /2.0 ),3 )
        context ['val_i']=context .get ('i',1 )
        context ['val_n']=context .get ('n',1 )
        context ['syl_start_time']=float (getattr (getattr (unit ,'syl',unit ),'start_time',unit_st ))
        context ['syl_end_time']=float (getattr (getattr (unit ,'syl',unit ),'end_time',unit_et ))
        context ['fx_align']=5 
        if 'line'in context and context ['line']:
            context ['l']=context ['line']
        context ['fx']=FxContext (context )
        context ['engine']=self 
        context ['remember']=self .remember 
        context ['recall']=self .recall 
        self ._update_module_context (context )
        return context 

    def _update_module_context (self ,context ):
        j =float (context .get ('j',context .get ('fx_i',1 )))
        maxj =float (context .get ('maxj',context .get ('fx_n',1 )))

        module =round ((j -1.0 )/(maxj -1.0 ),4 )if maxj >1 else 0.0 
        context ['module']=module 
        context ['m']=module 
        return context 

    def _apply_defaults (self ,active_unit ,layer_raw ,st_raw ,et_raw ,tags_raw ,return_raw ,context =None ):
        default_st =context .get ('start_time',getattr (active_unit ,'start_time',0 ))if (context and 'start_time'in context )else getattr (active_unit ,'start_time',0 )
        default_et =context .get ('end_time',getattr (active_unit ,'end_time',0 ))if (context and 'end_time'in context )else getattr (active_unit ,'end_time',0 )
        layer =_to_int_or_default (layer_raw ,0 ,context =context )
        if context and context.get('anim_step_ms') and context.get('in_auto_slicer_loop') and 'st' in context:
            st = _to_int_or_default(context['st'], default_st, context=context)
        else:
            st = _to_int_or_default(st_raw, default_st, context=context)
        if context and context.get('anim_step_ms') and context.get('in_auto_slicer_loop') and 'et' in context:
            et = _to_int_or_default(context['et'], default_et, context=context)
        else:
            et = _to_int_or_default(et_raw, default_et, context=context)

        tags_raw =""if _is_empty_value (tags_raw )else str (tags_raw ).strip ()
        return_connected =bool (context and context .get ('_return_port_connected'))
        return_node_is_shape =bool (context and context .get ('_return_node_is_shape'))
        if not return_connected :
            return_raw =getattr (active_unit ,'text_stripped','')if _is_empty_value (return_raw )else str (return_raw ).strip ()
        else :
            return_raw =""if _is_empty_value (return_raw )else str (return_raw ).strip ()


        if return_raw and return_raw .startswith ("[")and return_raw .endswith ("]"):
            try :
                import json 
                parsed_json =json .loads (return_raw )
                if isinstance (parsed_json ,list ):
                    return_raw ="".join (str (p )for p in parsed_json )
            except Exception :
                pass 



        leading_tags_list =[]
        while return_raw and str (return_raw ).lstrip ().startswith ("{"):
            ret_s =str (return_raw ).lstrip ()
            close_brace =ret_s .find ("}")
            if close_brace ==-1 :
                break 
            leading_tags_list .append (ret_s [1 :close_brace ])
            return_raw =ret_s [close_brace +1 :]


        while return_raw and (str (return_raw ).lstrip ().startswith (r"\clip")or str (return_raw ).lstrip ().startswith (r"\iclip")):
            m_clip =re .match (r'^\s*(\\i?clip\([^)]*\))\s*',str (return_raw ))
            if m_clip :
                leading_tags_list .append (m_clip .group (1 ))
                return_raw =str (return_raw )[m_clip .end ():]
            else :
                break 

        if leading_tags_list :
            combined_leading ="".join (leading_tags_list )
            tags_raw =merge_ass_tags (return_tags_str =combined_leading ,port_tags_str =tags_raw )


        if not return_connected and not return_raw and active_unit :
            return_raw =getattr (active_unit ,'text_stripped',getattr (active_unit ,'text',''))


        if (return_raw and (return_raw .startswith ("m ")or re .search (r'\bm\s+-?\d+',return_raw )))or (return_node_is_shape and return_connected ):
            last_block = tags_raw .rsplit ('}', 1 )[-1 ]if '}' in tags_raw else tags_raw 
            p_matches = re .findall (r'\\p(\d+)', last_block )
            if not (p_matches and int (p_matches [-1 ]) > 0 ):
                tags_raw += "\\p1"

        ctx =context if isinstance (context ,dict )else {}
        origin_align =5 
        try :
            origin_align =int (ctx .get ('origin_align',5 ))
            if origin_align <1 or origin_align >9 :
                origin_align =5 
        except Exception :
            origin_align =5 


        if not _AN_RE .search (tags_raw ):
            tags_raw =r"\an5"+tags_raw 


        tags_raw =re .sub (r'\\{2,}',r'\\',tags_raw )


        u_left =float (ctx .get ('val_left',getattr (active_unit ,'left',getattr (active_unit ,'center',0.0 ))if active_unit else 0.0 ))
        u_center =float (ctx .get ('val_center',getattr (active_unit ,'center',0.0 )if active_unit else 0.0 ))
        u_right =float (ctx .get ('val_right',getattr (active_unit ,'right',getattr (active_unit ,'center',0.0 ))if active_unit else 0.0 ))
        u_top =float (ctx .get ('val_top',getattr (active_unit ,'top',getattr (active_unit ,'middle',0.0 ))if active_unit else 0.0 ))
        u_middle =float (ctx .get ('val_middle',getattr (active_unit ,'middle',0.0 )if active_unit else 0.0 ))
        u_bottom =float (ctx .get ('val_bottom',getattr (active_unit ,'bottom',getattr (active_unit ,'middle',0.0 ))if active_unit else 0.0 ))

        if origin_align in (7 ,4 ,1 ):
            default_orig_x =u_left 
        elif origin_align in (9 ,6 ,3 ):
            default_orig_x =u_right 
        else :
            default_orig_x =u_center 

        if origin_align in (7 ,8 ,9 ):
            default_orig_y =u_top 
        elif origin_align in (1 ,2 ,3 ):
            default_orig_y =u_bottom 
        else :
            default_orig_y =u_middle 

        def _fmt_coord (v ):
            try :
                fv =float (v )
                return f"{fv :.2f}".rstrip ('0').rstrip ('.')if (fv %1 !=0 )else f"{int (fv )}"
            except Exception :
                return str (v )


        if ctx .get ('pos_overridden'):
            pos_x =ctx .get ('x',default_orig_x )
            pos_y =ctx .get ('y',default_orig_y )
            pos_str =f"\\pos({_fmt_coord (pos_x )},{_fmt_coord (pos_y )})"
            if _POS_RE .search (tags_raw ):
                tags_raw =_POS_RE .sub (lambda m :pos_str ,tags_raw )
            elif not _MOVE_RE .search (tags_raw ):
                tags_raw +=pos_str 
        elif not _POS_RE .search (tags_raw )and not _MOVE_RE .search (tags_raw ):
            pos_x =default_orig_x 
            pos_y =default_orig_y 
            tags_raw +=f"\\pos({_fmt_coord (pos_x )},{_fmt_coord (pos_y )})"


        if ctx .get ('has_org'):
            org_x =ctx .get ('org_x',ctx .get ('x',default_orig_x ))
            org_y =ctx .get ('org_y',ctx .get ('y',default_orig_y ))
            org_str =f"\\org({_fmt_coord (org_x )},{_fmt_coord (org_y )})"
            if re .search (r'\\org\([^)]*\)',tags_raw ):
                tags_raw =re .sub (r'\\org\([^)]*\)',lambda m :org_str ,tags_raw )
            else :
                tags_raw +=org_str 
        elif ctx .get ('has_org')is False and re .search (r'\\org\([^)]*\)',tags_raw ):
            tags_raw =re .sub (r'\\org\([^)]*\)','',tags_raw )


        tags_raw =merge_ass_tags (return_tags_str ="",port_tags_str =tags_raw )

        return layer ,st ,et ,tags_raw ,return_raw 

    def trace_loop_chain (self ,output_node ):
        chain =[]
        current_node =output_node 
        input_port_index =0 
        visited =set ()

        while current_node and current_node ['id']not in visited :
            visited .add (current_node ['id'])
            if not self .is_port_connected (current_node ,input_port_index ):
                found_idx =None 
                for idx ,inp in enumerate (current_node .get ('inputs',[])):
                    if self .is_port_connected (current_node ,idx ):
                        found_idx =idx 
                        break 
                if found_idx is not None :
                    input_port_index =found_idx 
                else :
                    break 

            inputs =current_node .get ('inputs',[])
            if input_port_index >=len (inputs ):
                break 
            link_id =inputs [input_port_index ].get ('link')
            link =next ((l for l in self .links if l [0 ]==link_id ),None )
            if not link :
                break 

            origin_node =self .nodes .get (link [1 ])
            if not origin_node :
                break 
            node_type =origin_node .get ('type','')
            props =origin_node .get ('properties',{})

            if node_type in ["Loops/Main Loop","Main Loop"]:
                chain .append ({'type':'base','val':props .get ('iterator',props .get ('iterador',props .get ('base_unit','syl')))})
                break 
            elif node_type in ["Loops/MaxLoop","MaxLoop"]:
                chain .append ({
                'type':'maxloop',
                'node':origin_node ,
                'mode':props .get ('mode',props .get ('modo','Normal')),
                'val':props .get ('iterations',props .get ('veces',props .get ('vueltas','1'))),
                'step_ms':props .get ('step_ms','41.7'),
                'start_time':props .get ('start_time',''),
                'end_time':props .get ('end_time',''),
                'var_name':props .get ('var_name','j')
                })
                current_node =origin_node 
                input_port_index =0 
            elif node_type in ["Variables/Define Vars","Define Vars"]:
                chain .append ({'type':'set_vars','val':props .get ('variables','')})
                current_node =origin_node 
                input_port_index =0 
            elif node_type in ["System/Script Code","Script Code"]:
                chain .append ({'type':'code_script','node':origin_node })
                current_node =origin_node 
                input_port_index =0 
            else :
                current_node =origin_node 
                input_port_index =0 

        res_chain =list (reversed (chain ))
        has_base =any (c .get ('type')=='base'for c in res_chain )
        if not has_base :
            res_chain .insert (0 ,{'type':'base','val':'syl'})

        return res_chain 

    def evaluate_data_node (self ,node_id ,context ,output_slot_index =0 ):
        if _PROFILER_ENABLED :
            _t0 =time .perf_counter ()
            res =self ._evaluate_data_node_body (node_id ,context ,output_slot_index )
            _dur =time .perf_counter ()-_t0 
            try :
                from pyxis_profiler import PyxisProfiler 
                prof =PyxisProfiler .get_active ()
                if prof :
                    prof .record_node_eval (node_id ,self .nodes [node_id ].get ('type',''),_dur )
            except Exception :
                pass 
            return res 
        return self ._evaluate_data_node_body (node_id ,context ,output_slot_index )

    def _evaluate_data_node_body (self ,node_id ,context ,output_slot_index =0 ):
        node =self .nodes [node_id ]
        node_type =node ['type']
        props =node .get ('properties',{})
        if '/'in node_type :
            category ,name =node_type .rsplit ('/',1 )
        else :
            category ,name ="",node_type 




        if node_type in ["MultiTag","MultiTag/MultiTag","Tags/MultiTag","Functions/MultiTag","Basics/MultiTag"]or name =="MultiTag":
            tag_type =str (_get_prop_value (props ,"tag_type",_get_prop_value (props ,"tag","pos"))).strip ()
            from nodes .tag_nodes import tag_master 
            kwargs ={str (k ):v for k ,v in props .items ()}
            kwargs .pop ("tag_type",None )
            inputs_list =node .get ("inputs",[])
            for i ,input_obj in enumerate (inputs_list ):
                input_name =input_obj .get ("name","")
                prop_key =input_obj .get ("property")or input_name 
                val =self .get_input_value (node ,i ,context )
                if val =="":
                    prop_val =str (_get_prop_value (props ,prop_key ,_get_prop_value (props ,input_name ,""))).strip ()
                    if prop_val ==""and "value"in input_obj and input_obj ["value"]is not None :
                        prop_val =str (input_obj ["value"]).strip ()
                    if prop_val !="":
                        val =prop_val 
                if val !="":
                    if input_name :
                        kwargs [str (input_name )]=val 
                    if prop_key :
                        kwargs [str (prop_key )]=val 
                    kwargs [str (i )]=val 
                    kwargs [f"in_{i }"]=val 
                    kwargs [f"in{i +1 }"]=val 
            return tag_master (context ,tag_type =tag_type ,**kwargs )

        elif node_type in ["Basics/MultiRandom", "MultiRandom", "Math/MultiRandom"] or name == "MultiRandom":
            modo =str (_get_prop_value (props ,"mode","R")).strip ()

            inputs_list =node .get ("inputs",[])
            connected_vals ={}
            for i ,input_obj in enumerate (inputs_list ):
                input_name =input_obj .get ("name","")
                val =self .get_input_value (node ,i ,context )
                if val !="":
                    connected_vals [input_name ]=val 
                    connected_vals [i ]=val 

            def get_rnd_param (name ,prop_key ,pos_idx ,default ):
                if name in connected_vals :
                    return connected_vals [name ]
                if prop_key in connected_vals :
                    return connected_vals [prop_key ]
                if pos_idx >=0 and pos_idx in connected_vals :
                    return connected_vals [pos_idx ]
                return _get_prop_value (props ,prop_key ,_get_prop_value (props ,name ,default ))

            min_val =get_rnd_param ("Min","min",0 if modo not in ("Re",)else -1 ,"0")
            max_val =get_rnd_param ("Max","max",1 if modo not in ("Re","Rbool")else -1 ,"100")
            step =get_rnd_param ("Step","step",2 if modo not in ("Re","Rfake","Rcolor","Rbool")else -1 ,"1")
            options =get_rnd_param ("Options","options",0 if modo =="Re"else -1 ,"")
            counter =get_rnd_param ("Counter","counter",2 if modo =="Rfake"else -1 ,"")
            seed = get_rnd_param("Seed", "seed", -1, "")
            total_raw = get_rnd_param("Total (N)", "total", len(inputs_list) - 1 if len(inputs_list) > 0 else -1, "1")

            from nodes .math_nodes import math_random_master 
            if output_slot_index == 1:
                n_val = max(1, int(round(float(_eval_num_expr(total_raw, context, 1)))))
                res_list = []
                for k in range(1, n_val + 1):
                    step_counter = counter if (counter and str(counter).strip() != "") else str(k)
                    res_list.append(str(math_random_master(context, mode=modo, min_val=min_val, max_val=max_val, step=step, options=options, counter=step_counter, seed=seed)))
                return ", ".join(res_list)

            return str(math_random_master(context, mode=modo, min_val=min_val, max_val=max_val, step=step, options=options, counter=counter, seed=seed))

        elif node_type in ["Basics/Math", "Math", "Math/Math"] or name == "Math":
            try :
                inputs_list =node .get ("inputs",[])
                kwargs ={}
                for i ,inp_obj in enumerate (inputs_list ):
                    inp_name =inp_obj .get ("name","")
                    inp_prop =inp_obj .get ("property")or inp_name 
                    val =self .get_input_value (node ,i ,context )
                    if val =="":
                        prop_val =str (_get_prop_value (props ,inp_prop ,_get_prop_value (props ,inp_name ,""))).strip ()
                        if prop_val ==""and "value"in inp_obj and inp_obj ["value"]is not None :
                            prop_val =str (inp_obj ["value"]).strip ()
                        val =prop_val 
                    if val !="":
                        if inp_name :
                            kwargs [str (inp_name )]=val 
                        if inp_prop :
                            kwargs [str (inp_prop )]=val 

                for k ,v in props .items ():
                    if k not in kwargs :
                        kwargs [k ]=v 

                from nodes .math_nodes import eval_math_node 
                res_num =eval_math_node (context ,**kwargs )
                if isinstance (res_num ,(int ,float )):
                    if float (res_num ).is_integer ():
                        return str (int (res_num ))
                    return f"{res_num :.4f}".rstrip ('0').rstrip ('.')
                return str (res_num )
            except Exception as e :
                import traceback 
                print (f"[Pyxis Engine Error] Math node evaluation failed: {e }")
                traceback .print_exc ()
                return "0"

        elif node_type in ["Basics/Text", "Text"] or name == "Text":
            try :
                inputs_list =node .get ("inputs",[])
                kwargs ={}
                for i ,inp_obj in enumerate (inputs_list ):
                    inp_name =inp_obj .get ("name","")
                    inp_prop =inp_obj .get ("property")or inp_name 
                    val =self .get_input_value (node ,i ,context )
                    if val =="":
                        prop_val =str (_get_prop_value (props ,inp_prop ,_get_prop_value (props ,inp_name ,""))).strip ()
                        if prop_val ==""and "value"in inp_obj and inp_obj ["value"]is not None :
                            prop_val =str (inp_obj ["value"]).strip ()
                        val =prop_val 
                    if val !="":
                        if inp_name :
                            kwargs [str (inp_name )]=val 
                        if inp_prop :
                            kwargs [str (inp_prop )]=val 

                for k ,v in props .items ():
                    if k not in kwargs :
                        kwargs [k ]=v 

                from nodes .text_nodes import eval_text_node 
                return str (eval_text_node (context ,**kwargs ))
            except Exception as e :
                import traceback 
                print (f"[Pyxis Engine Error] Text node evaluation failed: {e }")
                traceback .print_exc ()
                return ""

        elif node_type in ["Basics/Number", "Number"] or name == "Number":
            val_raw = _get_prop_value(props, "value", "0")
            res = _eval_num_expr(val_raw, context, default=0.0)
            if isinstance(res, (int, float)):
                if float(res).is_integer():
                    return str(int(res))
                return f"{res:.4f}".rstrip('0').rstrip('.')
            return str(res)

        elif node_type in ["Basics/String", "String"] or name == "String":
            return str(_get_prop_value(props, "value", ""))

        elif node_type in ["Tag Manipulator", "Tags/Tag Manipulator", "Functions/Tag Manipulator"] or name == "Tag Manipulator":
            try:
                inputs_list = node.get("inputs", [])
                kwargs = {}
                for i, inp_obj in enumerate(inputs_list):
                    inp_name = inp_obj.get("name", "")
                    inp_prop = inp_obj.get("property") or inp_name
                    val = self.get_input_value(node, i, context)
                    if val == "":
                        prop_val = str(_get_prop_value(props, inp_prop, _get_prop_value(props, inp_name, ""))).strip()
                        if prop_val == "" and "value" in inp_obj and inp_obj["value"] is not None:
                            prop_val = str(inp_obj["value"]).strip()
                        val = prop_val
                    if val != "":
                        if inp_name:
                            kwargs[str(inp_name)] = val
                        if inp_prop:
                            kwargs[str(inp_prop)] = val
                        kwargs[str(i)] = val
                        kwargs[f"in_{i}"] = val

                for k, v in props.items():
                    if k not in kwargs and str(v).strip() != "":
                        kwargs[k] = v

                kwargs["output_slot_index"] = output_slot_index
                from nodes.tag_nodes import eval_tag_manipulator_node
                res = eval_tag_manipulator_node(context, **kwargs)
                return res
            except Exception as e:
                import traceback
                print(f"[Pyxis Engine Error] Tag Manipulator evaluation failed: {e}")
                traceback.print_exc()
                return ""

        elif node_type in ["Retime", "Time/Retime"] or name == "Retime":
            try:
                inputs_list = node.get("inputs", [])
                kwargs = {}
                for i, inp_obj in enumerate(inputs_list):
                    inp_name = inp_obj.get("name", "")
                    inp_prop = inp_obj.get("property") or inp_name
                    val = self.get_input_value(node, i, context)
                    if val == "":
                        prop_val = str(_get_prop_value(props, inp_prop, _get_prop_value(props, inp_name, ""))).strip()
                        if prop_val == "" and "value" in inp_obj and inp_obj["value"] is not None:
                            prop_val = str(inp_obj["value"]).strip()
                        val = prop_val
                    if val != "":
                        if inp_name:
                            kwargs[str(inp_name)] = val
                        if inp_prop:
                            kwargs[str(inp_prop)] = val
                        kwargs[str(i)] = val
                        kwargs[f"in_{i}"] = val

                for k, v in props.items():
                    if k not in kwargs:
                        kwargs[k] = v

                kwargs["output_slot_index"] = output_slot_index
                from nodes.time_nodes import eval_retime_node
                res = eval_retime_node(context, **kwargs)
                return res
            except Exception as e:
                import traceback
                print(f"[Pyxis Engine Error] Retime node evaluation failed: {e}")
                traceback.print_exc()
                return ""

        elif node_type in ["Shape/Library", "Library"]:
            try :
                inputs_list =node .get ("inputs",[])
                kwargs ={}
                for i ,inp_obj in enumerate (inputs_list ):
                    inp_name =inp_obj .get ("name","")
                    inp_prop =inp_obj .get ("property")or inp_name 
                    val =self .get_input_value (node ,i ,context )
                    if val =="":
                        prop_val =str (_get_prop_value (props ,inp_prop ,_get_prop_value (props ,inp_name ,""))).strip ()
                        if prop_val ==""and "value"in inp_obj and inp_obj ["value"]is not None :
                            prop_val =str (inp_obj ["value"]).strip ()
                        val =prop_val 
                    if val !="":
                        if inp_name :
                            kwargs [str (inp_name )]=val 
                        if inp_prop :
                            kwargs [str (inp_prop )]=val 

                for k ,v in props .items ():
                    if k not in kwargs :
                        kwargs [k ]=v 

                from nodes .shape_nodes import eval_shapes_lib_node 
                return str (eval_shapes_lib_node (context ,**kwargs ))
            except Exception as e :
                import traceback 
                print (f"[Pyxis Engine Error] Shapes Lib node evaluation failed: {e }")
                traceback .print_exc ()
                return ""

        elif node_type in ["Functions/Conditioner","Conditioner"]:
            cond_raw =self .get_input_value (node ,0 ,context )
            if cond_raw =="":cond_raw =_get_prop_value (props ,"condition",_get_prop_value (props ,"condicion","True"))
            si_verdadero =self .get_input_value (node ,1 ,context )
            if si_verdadero =="":si_verdadero =_get_prop_value (props ,"if_true",_get_prop_value (props ,"si_verdadero",_get_prop_value (props ,"true_val","")))
            si_falso =self .get_input_value (node ,2 ,context )
            if si_falso =="":si_falso =_get_prop_value (props ,"if_false",_get_prop_value (props ,"si_falso",_get_prop_value (props ,"false_val","")))

            from nodes .tag_nodes import node_conditioner 
            return str (node_conditioner (
            context ,
            condicion =cond_raw ,
            condition =cond_raw ,
            si_verdadero =si_verdadero ,
            if_true =si_verdadero ,
            si_falso =si_falso ,
            if_false =si_falso 
            ))

        elif node_type in ["Basics/Dynamic Format", "Dynamic Format", "String/Dynamic Format"] or name == "Dynamic Format":
            try :
                fmt =str (_get_prop_value (props ,"format",_get_prop_value (props ,"Formato","%s")))
                inputs_list =node .get ('inputs',[])
                inputs_count =len (inputs_list )

                values =[]
                for i in range (inputs_count ):
                    val =self .get_input_value (node ,i ,context )
                    if val is None or str (val )=="":
                        prop_name =f"In{i +1 }"
                        val =props .get (prop_name ,props .get (f"in{i +1 }",props .get (f"Entrada {i +1 }","")))
                    values .append (str (val )if val is not None else "")

                if not values and "%"not in fmt :
                    return fmt 

                def _format_entry (fmt_pattern ,arg_values ):
                    specifiers =re .findall (r'%[0-9.-]*[sdfixX]',fmt_pattern )
                    if specifiers :
                        converted_values =[]
                        for j ,spec in enumerate (specifiers ):
                            val_str =arg_values [j ]if j <len (arg_values )else ""
                            if spec .endswith (('d','i','x','X')):
                                try :
                                    converted_values .append (int (float (_eval_num_expr (val_str ,context ,0 ))))
                                except Exception :
                                    converted_values .append (0 )
                            elif spec .endswith ('f'):
                                try :
                                    converted_values .append (float (_eval_num_expr (val_str ,context ,0.0 )))
                                except Exception :
                                    converted_values .append (0.0 )
                            else :
                                converted_values .append (str (val_str ))

                        while len (converted_values )<len (specifiers ):
                            converted_values .append ("")

                        try :
                            return fmt_pattern %tuple (converted_values [:len (specifiers )])
                        except Exception :
                            pass 


                    res =fmt_pattern 
                    for val in arg_values :
                        if "%s"in res :
                            res =res .replace ("%s",str (val ),1 )
                        else :
                            break 
                    return res 


                val_lists =[]
                has_list =False 
                max_len =1 
                for v in values :
                    s_v =str (v )
                    if ","in s_v :
                        parts =[p .strip ()for p in s_v .split (",")if p .strip ()]
                        if len (parts )>1 :
                            has_list =True 
                            max_len =max (max_len ,len (parts ))
                            val_lists .append (parts )
                            continue 
                    val_lists .append ([s_v ])

                if has_list :
                    batch_res =[]
                    for k in range (max_len ):
                        k_args =[vlist [k %len (vlist )]if vlist else ""for vlist in val_lists ]
                        batch_res .append (_format_entry (fmt ,k_args ))
                    return ", ".join (batch_res )

                return _format_entry (fmt ,values )
            except Exception as e :
                return f"[Err Format: {e }]"

        elif node_type in ["System/Script Code","Script Code"]:
            script = props.get("script", "")
            language = props.get("language", props.get("lenguaje", "Python"))
            inputs_list = node.get("inputs", [])
            inputs_map = {}
            for idx in range(1, 17):
                inputs_map[f"in{idx}"] = ""
                inputs_map[f"in_{idx}"] = ""

            data_port_idx = 1
            for i, input_obj in enumerate(inputs_list):
                input_name = input_obj.get("name", "")
                if input_name in ["Loop In", "In (bucle)", "In (loop)", "Loop / Domain", "bucle", "Loop", "Bucle", "Bucle In", "loop"]:
                    continue
                val = self.get_input_value(node, i, context)
                if val == "":
                    val = str(_get_prop_value(props, input_name, "")).strip()
                if input_name:
                    inputs_map[input_name] = val
                    inputs_map[input_name.lower()] = val
                inputs_map[f"in{data_port_idx}"] = val
                inputs_map[f"in_{data_port_idx}"] = val
                data_port_idx += 1

            from nodes.code_nodes import code_script_master
            return code_script_master(context, script=script, language=language, **inputs_map)




        if node_type in ["Shape/Slicer", "Slicer"]:
            try :
                modo_alias_map ={
                "hex":"hex","hexagonal":"hex","malla hexagonal":"hex",
                "tri":"tri","triangular":"tri","malla triangular":"tri",
                "dia":"dia","diamante":"dia","diamond":"dia","rombos":"dia",
                "ring":"ring","rings":"ring","anillos":"ring",
                "ray":"ray","rays":"ray","radial":"ray","rayos":"ray",
                "quad":"quad","quadtree":"quad",
                "bez":"bez","bézier":"bez","bezier":"bez","ondas":"bez",
                "jigsaw":"jigsaw","puzzle":"jigsaw","rompecabezas":"jigsaw",
                "voronoi":"voronoi","vor":"voronoi","cristales":"voronoi",
                "ashlar":"ashlar","mamposteria":"ashlar",
                "brick":"brick","ladrillo":"brick","ladrillos":"brick",
                "mondrian":"mondrian",
                "herringbone":"herringbone","espiga":"herringbone","zig-zag":"herringbone",
                "delaunay":"delaunay","low-poly":"delaunay","lowpoly":"delaunay",
                "scallop":"scallop","escamas":"scallop",
                "web":"web","spiderweb":"web","telaraña":"web",
                "rhombille":"rhombille","cubos":"rhombille","cubes":"rhombille",
                "octagon":"octagon","mosaico":"octagon","octogonos":"octagon",
                "kagome":"kagome","trihexagonal":"kagome",
                "truchet":"truchet","tuberias":"truchet","laberinto":"truchet",
                "circuit":"circuit","circuito":"circuit","tech":"circuit",
                "pattern":"pattern","patrón":"pattern","patron":"pattern","modular":"modular",
                "rejilla 1d/2d":"grid","grid":"grid","grid 1d/2d":"grid"
                }

                modo = props.get("mode", props.get("modo", "grid"))
                modo_str =str (modo ).strip ()
                modo_key =modo_str .lower ()
                norm_engine_mode =modo_alias_map .get (modo_key ,modo_str )

                inputs_list =node .get ("inputs",[])

                def get_val (port_name_or_aliases ,default_val =""):
                    if isinstance (port_name_or_aliases ,str ):
                        aliases =[port_name_or_aliases ]
                    else :
                        aliases =list (port_name_or_aliases )

                    for alias in aliases :
                        clean_alias =_clean_key (alias )
                        for i ,inp_obj in enumerate (inputs_list ):
                            inp_name =inp_obj .get ("name","")
                            if _clean_key (inp_name )==clean_alias :
                                val =self .get_input_value (node ,i ,context )
                                if val !="":return val 
                                if "value"in inp_obj and inp_obj ["value"]is not None and str (inp_obj ["value"]).strip ()!="":
                                    return str (inp_obj ["value"])
                                widget_obj =inp_obj .get ("widget",{})
                                if isinstance (widget_obj ,dict )and "value"in widget_obj and widget_obj ["value"]is not None and str (widget_obj ["value"]).strip ()!="":
                                    return str (widget_obj ["value"])

                    for alias in aliases :
                        clean_alias =_clean_key (alias )
                        prop_val =_get_prop_value (props ,clean_alias ,"")
                        if prop_val !="":
                            return str (prop_val )

                    return str (default_val )

                shp =get_val (["Shape","shape","texto","drawing"],props .get ("shape",""))
                from nodes .shape_nodes import resolve_shape_value 
                shp =resolve_shape_value (shp ,context )
                if not shp :
                    shp ='m 0 0 l 100 0 l 100 100 l 0 100'

                def safe_float (v ,default =0.0 ):
                    if v is None or str (v ).strip ()=="":return default 
                    try :
                        return float (v )
                    except Exception :
                        pass 
                    return float (_eval_num_expr (v ,context ,default =default ))

                def safe_int (v ,default =1 ):
                    if v is None or str (v ).strip ()=="":return default 
                    try :
                        return int (float (v ))
                    except Exception :
                        pass 
                    return int (round (float (_eval_num_expr (v ,context ,default =float (default )))))

                cols =safe_int (get_val (["Cols","cols","Rings","rings","Num Rings","num_rings"],"2"),2 )
                rows =safe_int (get_val (["Rows","rows","Rays","rays","Num Rays","num_rays"],"2"),2 )
                size_x =safe_float (get_val ([
                "Radius","radius","Min Size","min_size","Grid Size","grid_size",
                "Piece Size","piece_size","Cell Size","cell_size","Min Width","min_width",
                "Width","width","Length","length","Ring Width","ring_width",
                "Step Angle","step_angle","Size X","size_x"
                ],20.0 ),20.0 )
                size_y =safe_float (get_val ([
                "Max Width","max_width","Row Height","row_height","Height","height",
                "Thickness","thickness","Amplitude","amplitude","Trace Width","trace_width",
                "Shape Size","shape_size","Size Y","size_y"
                ],20.0 ),20.0 )
                scale_x =safe_float (get_val (["Scale X","scale_x","Scale","scale"],"1.0"),1.0 )
                scale_y =safe_float (get_val (["Scale Y","scale_y"],"1.0"),1.0 )
                off_x =safe_float (get_val (["Center X","center_x","centerx","cx","Off X","off_x","offset_x"],"0"),0.0 )
                off_y =safe_float (get_val (["Center Y","center_y","centery","cy","Off Y","off_y","offset_y"],"0"),0.0 )
                angle =safe_float (get_val (["Angle","angle","Step Angle","step_angle","step_deg","step"],"0"),0.0 )
                overlap =safe_float (get_val (["Bleed","overlap","ov"],"0"),0.0 )

                stagger_raw =get_val (["Stagger","stagger"],"")
                if str (stagger_raw ).lower ()in ["true","1","yes"]:
                    accel_x_default ="2.0"
                else :
                    accel_x_default ="1.0"

                accel_x =safe_float (get_val ([
                "Stop Prob","stop_prob","Chaos","chaos","Via Prob","via_prob",
                "Accel X","accel_x","Accel","accel","Jitter","jitter"
                ],accel_x_default ),float (accel_x_default ))
                accel_y =safe_float (get_val (["Accel Y","accel_y","Accel","accel"],"1.0"),1.0 )

                pattern_shape =get_val (["Pattern Shape","pattern_shape","Shape String","shape_string"],"")

                text_scale =safe_float (get_val (["Text Scale","text_scale"],"1.0"),1.0 )
                pre_offset =safe_float (get_val (["Pre-Offset","pre_offset","preoffset","Pre Offset","pre-offset"],"0"),0.0 )
                order =safe_int (get_val (["Order","order"],"79"),79 )

                unit =context .get ('active_unit')if isinstance (context ,dict )else None 
                parent_x =float (context .get ('pos_x',context .get ('line_x',context .get ('syl_x',context .get ('x',0.0 )))))
                parent_y =float (context .get ('pos_y',context .get ('line_y',context .get ('syl_y',context .get ('y',0.0 )))))
                if unit :
                    if hasattr (unit ,'center')and unit .center is not None :parent_x =float (unit .center )
                    elif hasattr (unit ,'pos_x')and unit .pos_x is not None :parent_x =float (unit .pos_x )
                    elif hasattr (unit ,'x')and unit .x is not None :parent_x =float (unit .x )

                    if hasattr (unit ,'middle')and unit .middle is not None :parent_y =float (unit .middle )
                    elif hasattr (unit ,'pos_y')and unit .pos_y is not None :parent_y =float (unit .pos_y )
                    elif hasattr (unit ,'y')and unit .y is not None :parent_y =float (unit .y )

                from clipper_engine import ClipperEngine 


                slicer_node_id =node .get ('id',0 )
                slicer_sig =(
                slicer_node_id ,
                str (shp ),
                norm_engine_mode ,
                cols ,rows ,
                size_x ,size_y ,
                scale_x ,scale_y ,
                off_x ,off_y ,
                angle ,overlap ,
                accel_x ,accel_y ,
                order ,text_scale ,
                pre_offset ,
                pattern_shape 
                )

                unit_cache =None 
                if unit is not None :
                    if not hasattr (unit ,'_slicer_cache')or not isinstance (unit ._slicer_cache ,dict ):
                        unit ._slicer_cache ={}
                    unit_cache =unit ._slicer_cache 
                elif isinstance (context .get ('_global_slicer_cache'),dict ):
                    unit_cache =context ['_global_slicer_cache']
                else :
                    if not isinstance (context .get ('_slicer_pieces'),dict ):
                        context ['_slicer_pieces']={}
                    unit_cache =context ['_slicer_pieces']

                if slicer_sig in unit_cache :
                    pieces =unit_cache [slicer_sig ]
                elif slicer_node_id in unit_cache and not isinstance (unit_cache [slicer_node_id ],dict ):
                    pieces =unit_cache [slicer_node_id ]
                else :
                    pieces =ClipperEngine .slice_grid (
                    shp ,cols =cols ,rows =rows ,size_x =size_x ,size_y =size_y ,
                    scale_x =scale_x ,scale_y =scale_y ,offset_x =off_x ,offset_y =off_y ,
                    angle =angle ,overlap =overlap ,accel =accel_x ,accel_x =accel_x ,accel_y =accel_y ,order =order ,
                    text_scale =text_scale ,pre_offset =pre_offset ,engine_mode =norm_engine_mode ,
                    pattern_shape =pattern_shape 
                    )
                    if not pieces :
                        pieces =[{"code":shp ,"cx":0 ,"cy":0 ,"col":1 ,"row":1 }]
                    unit_cache [slicer_sig ]=pieces 
                    unit_cache [slicer_node_id ]=pieces 

                if not isinstance (context .get ('_slicer_pieces'),dict ):
                    context ['_slicer_pieces']={}
                context ['_slicer_pieces'][slicer_node_id ]=pieces 

                total_pieces =len (pieces )

                anchor_mode = get_val(["Anchor", "anchor", "anclaje"], props.get("anchor", "pieces")).lower()
                loop_mode = get_val(["Loop Mode", "loop_mode", "modo_bucle"], props.get("loop_mode", "Loops")).lower()
                out_mode = get_val(["Output Type", "out_mode", "output_type", "tipo_salida"], props.get("out_mode", "Shape")).lower()

                is_shape_mode = ("shape" in loop_mode and "loop" not in loop_mode and "pieza" not in loop_mode)


                s_val = int(context.get('s_i', context.get('slice_i', context.get('j', context.get('J', 1)))))

                if is_shape_mode:
                    context['s_i'] = 1
                    context['s_n'] = 1
                    context['s_max'] = 1
                    context['slice_i'] = 1
                    context['slice_n'] = 1
                    context['slice_max'] = 1
                    context['maxloop'] = 1
                else:
                    context['s_i'] = s_val
                    context['s_n'] = total_pieces
                    context['s_max'] = total_pieces
                    context['slice_i'] = s_val
                    context['slice_n'] = total_pieces
                    context['slice_max'] = total_pieces
                    context['maxloop'] = total_pieces


                if is_shape_mode:
                    from nodes.shape_nodes import resolve_piece_anchor
                    piece_drawings = []
                    for p_item in pieces:
                        c_val = str(p_item.get("code", ""))
                        p_cx, p_cy = float(p_item.get("cx", 0)), float(p_item.get("cy", 0))
                        anc_res = resolve_piece_anchor(c_val, piece_cx=p_cx, piece_cy=p_cy, parent_x=parent_x, parent_y=parent_y, anchor=anchor_mode, context=context)
                        piece_drawings.append(anc_res['formatted_code'])

                    combined_code = " ".join(piece_drawings)
                    if "iclip" in out_mode:
                        final_res = f"{{\\iclip({combined_code})}}"
                    elif "clip" in out_mode:
                        final_res = f"{{\\clip({combined_code})}}"
                    else:
                        final_res = combined_code

                    if output_slot_index == 1: return str(parent_x)
                    elif output_slot_index == 2: return str(parent_y)
                    elif output_slot_index == 3: return "1"
                    elif output_slot_index == 4: return "1"
                    return str(final_res)


                piece_idx = max(0, min(s_val - 1, total_pieces - 1))
                piece = pieces[piece_idx]
                cx, cy = float(piece.get("cx", 0)), float(piece.get("cy", 0))

                abs_x = parent_x + cx
                abs_y = parent_y + cy

                code_val = str(piece.get("code", ""))

                from nodes.shape_nodes import resolve_piece_anchor
                anc_res = resolve_piece_anchor(code_val, piece_cx=cx, piece_cy=cy, parent_x=parent_x, parent_y=parent_y, anchor=anchor_mode, context=context)
                formatted_code = anc_res['formatted_code']
                if isinstance(context, dict):
                    context['col'] = piece.get("col", 1)
                    context['row'] = piece.get("row", 1)
                    if anc_res['pos_overridden']:
                        context['x'] = abs_x
                        context['y'] = abs_y
                        context['fx_pos_x'] = abs_x
                        context['fx_pos_y'] = abs_y


                if "iclip"in out_mode :
                    abs_code =ClipperEngine .transform_shape (code_val ,mode ="Offset",offset_x =parent_x ,offset_y =parent_y )
                    final_res =f"{{\\iclip({abs_code })}}"
                elif "clip"in out_mode :
                    abs_code =ClipperEngine .transform_shape (code_val ,mode ="Offset",offset_x =parent_x ,offset_y =parent_y )
                    final_res =f"{{\\clip({abs_code })}}"
                else :
                    final_res =formatted_code 

                if output_slot_index ==1 :return str (abs_x )
                elif output_slot_index ==2 :return str (abs_y )
                elif output_slot_index ==3 :return str (piece .get ("col",1 ))
                elif output_slot_index ==4 :return str (piece .get ("row",1 ))
                return str (final_res )
            except Exception as e :
                import traceback 
                traceback .print_exc ()
                return f"[Err Slicer: {e}]"

        if node_type in ["Shape/Manipulator", "Manipulator"]:
            try :
                modo =str (props .get ("mode",props .get ("modo","scale"))).strip ()
                shp_val =self .get_input_value (node ,0 ,context )
                if shp_val =="":shp_val =str (_get_prop_value (props ,"shape","")).strip ()
                from nodes .shape_nodes import resolve_shape_value ,shape_manipulator 
                shp_val =resolve_shape_value (shp_val ,context )
                if not shp_val :
                    unit =context .get ('active_unit')if isinstance (context ,dict )else (context .get ('syl')if isinstance (context ,dict )else None )
                    line =context .get ('active_line')if isinstance (context ,dict )else (context .get ('line')if isinstance (context ,dict )else None )
                    shp_val =getattr (unit ,'text_stripped',getattr (unit ,'text',''))or getattr (line ,'text_stripped',getattr (line ,'text',''))

                modo_clean =modo .lower ()
                if "borde"in modo_clean or "border"in modo_clean :
                    t_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    offset_border =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"offset_border","2.0"),context ,2.0 )
                    anchor =str (_get_prop_value (props ,"anchor","center")).strip ()
                    return shape_manipulator (context ,drawing =shp_val ,offset_border =offset_border ,mode =anchor ,op_mode ="Borders",t =t_val )
                elif "deform"in modo_clean :
                    t_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    offset_x =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"offset_x","0"),context ,0.0 )
                    offset_y =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"offset_y","0"),context ,0.0 )
                    factor =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"factor","100"),context ,100.0 )
                    anchor =str (_get_prop_value (props ,"anchor","center")).strip ()
                    return shape_manipulator (context ,drawing =shp_val ,scale_x =factor /100.0 ,scale_y =factor /100.0 ,offset_x =offset_x ,offset_y =offset_y ,mode =anchor ,op_mode ="Deform",t =t_val )
                elif "posici"in modo_clean or "posic"in modo_clean or "position"in modo_clean or "pos"in modo_clean :
                    t_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    offset_x =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"offset_x","0"),context ,0.0 )
                    offset_y =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"offset_y","0"),context ,0.0 )
                    anchor =str (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"anchor","center")).strip ()
                    return shape_manipulator (context ,drawing =shp_val ,offset_x =offset_x ,offset_y =offset_y ,mode =anchor ,op_mode ="Position",t =t_val )
                elif "redibuj"in modo_clean or "redraw"in modo_clean :
                    t_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    density =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"density",_get_prop_value (props ,"factor","2.0")),context ,2.0 )
                    anchor =str (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"anchor","center")).strip ()
                    return shape_manipulator (context ,drawing =shp_val ,mode =anchor ,op_mode ="Redraw",density =density ,t =t_val )
                elif "giro"in modo_clean or "3d"in modo_clean or "matrix"in modo_clean or "matriz"in modo_clean or "rotar"in modo_clean or "rot"in modo_clean or "rotate"in modo_clean :
                    t_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    angle_x =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"angle_x","0"),context ,0.0 )
                    angle_y =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"angle_y","0"),context ,0.0 )
                    angle_z =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"angle_z",_get_prop_value (props ,"angle","0")),context ,0.0 )
                    anchor =str (self .get_input_value (node ,5 ,context )or _get_prop_value (props ,"anchor","center")).strip ()
                    return shape_manipulator (context ,drawing =shp_val ,mode =anchor ,op_mode ="3D Rotate",angle_x =angle_x ,angle_y =angle_y ,angle_z =angle_z ,t =t_val )
                elif "refle"in modo_clean or "reflect"in modo_clean or "espejo"in modo_clean or "mirror"in modo_clean :
                    t_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    axis =str (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"axis","y")).strip ()
                    offset_x =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"offset_x","0"),context ,0.0 )
                    offset_y =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"offset_y","0"),context ,0.0 )
                    anchor =str (self .get_input_value (node ,5 ,context )or _get_prop_value (props ,"anchor","center")).strip ()
                    return shape_manipulator (context ,drawing =shp_val ,mode =anchor ,op_mode ="Reflect",axis =axis ,offset_x =offset_x ,offset_y =offset_y ,t =t_val )
                else :
                    t_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    scale_x =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"scale_x","100"),context ,100.0 )
                    scale_y =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"scale_y","100"),context ,100.0 )
                    anchor =str (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"anchor","center")).strip ()
                    return shape_manipulator (context ,drawing =shp_val ,scale_x =scale_x /100.0 ,scale_y =scale_y /100.0 ,mode =anchor ,op_mode ="Scale",t =t_val )
            except Exception as e :
                return f"[Err Manipulator: {e}]"

        if node_type in ["Shape/Filter", "Filter"]:
            try :
                modo =str (props .get ("mode",props .get ("modo","vertices"))).strip ()
                shp_val =self .get_input_value (node ,0 ,context )
                if shp_val =="":shp_val =str (_get_prop_value (props ,"shape","")).strip ()
                from nodes .shape_nodes import resolve_shape_value ,shape_filter 
                shp_val =resolve_shape_value (shp_val ,context )
                if not shp_val :
                    unit =context .get ('active_unit')if isinstance (context ,dict )else (context .get ('syl')if isinstance (context ,dict )else None )
                    line =context .get ('active_line')if isinstance (context ,dict )else (context .get ('line')if isinstance (context ,dict )else None )
                    shp_val =getattr (unit ,'text_stripped',getattr (unit ,'text',''))or getattr (line ,'text_stripped',getattr (line ,'text',''))

                modo_clean =modo .lower ().replace ("é","e").replace ("á","a").replace ("í","i").replace ("ó","o").replace ("ú","u")
                if "vert"in modo_clean or "expr"in modo_clean :
                    expr_x =self .get_input_value (node ,1 ,context )
                    if expr_x is None or str (expr_x ).strip ()=="":expr_x =_get_prop_value (props ,"expr_x","x")
                    expr_y =self .get_input_value (node ,2 ,context )
                    if expr_y is None or str (expr_y ).strip ()=="":expr_y =_get_prop_value (props ,"expr_y","y")
                    t_val =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    subdivs =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"subdivs","0"),context ,0.0 )
                    return shape_filter (context ,drawing =shp_val ,mode ="Vertices",expr_x =expr_x ,expr_y =expr_y ,t =t_val ,subdivs =subdivs )

                elif "grup"in modo_clean or "group"in modo_clean or "piez"in modo_clean :
                    t_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    rot_step =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"rot_step","0"),context ,0.0 )
                    scale_step =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"scale_step","100"),context ,100.0 )
                    offset_x =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"offset_x","0"),context ,0.0 )
                    offset_y =_eval_num_expr (self .get_input_value (node ,5 ,context )or _get_prop_value (props ,"offset_y","0"),context ,0.0 )
                    anchor =str (self .get_input_value (node ,6 ,context )or _get_prop_value (props ,"anchor","center")).strip ()
                    return shape_filter (context ,drawing =shp_val ,mode ="Group",t =t_val ,rot_step =rot_step ,scale_step =scale_step ,offset_x =offset_x ,offset_y =offset_y ,anchor =anchor )

                elif "ruid"in modo_clean or "noise"in modo_clean or "rand"in modo_clean :
                    radius_x =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"radius_x","5.0"),context ,5.0 )
                    radius_y =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"radius_y","5.0"),context ,5.0 )
                    subdivs =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"subdivs","2.0"),context ,2.0 )
                    seed =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"seed","0"),context ,0 )
                    return shape_filter (context ,drawing =shp_val ,mode ="Noise",radius_x =radius_x ,radius_y =radius_y ,subdivs =subdivs ,seed =seed )

                else :
                    props_copy =dict (props )
                    props_copy .pop ("mode",None )
                    props_copy .pop ("modo",None )
                    props_copy .pop ("shape",None )
                    return shape_filter (context ,drawing =shp_val ,mode =modo ,**props_copy )
            except Exception as e :
                return f"[Err Filter: {e}]"

        if node_type in ["Shape/Transform", "Transform"]:
            try :
                modo =str (props .get ("mode",props .get ("modo","inflate"))).strip ()
                shp_val =self .get_input_value (node ,0 ,context )
                if shp_val =="":shp_val =str (_get_prop_value (props ,"shape","")).strip ()
                from nodes .shape_nodes import resolve_shape_value ,shape_transform 
                shp_val =resolve_shape_value (shp_val ,context )
                if not shp_val :
                    unit =context .get ('active_unit')if isinstance (context ,dict )else (context .get ('syl')if isinstance (context ,dict )else None )
                    line =context .get ('active_line')if isinstance (context ,dict )else (context .get ('line')if isinstance (context ,dict )else None )
                    shp_val =getattr (unit ,'text_stripped',getattr (unit ,'text',''))or getattr (line ,'text_stripped',getattr (line ,'text',''))

                modo_clean =modo .lower ()
                if "skew"in modo_clean or "cizall"in modo_clean or "inclin"in modo_clean :
                    in_t =self .get_input_value (node ,1 ,context )
                    if in_t is None or in_t =="":in_t =_get_prop_value (props ,"t","1.0")
                    t_val =_eval_num_expr (in_t ,context ,1.0 )

                    in_ax =self .get_input_value (node ,2 ,context )
                    if in_ax is None or in_ax =="":in_ax =_get_prop_value (props ,"angle_x",_get_prop_value (props ,"ang_x",_get_prop_value (props ,"angle","0")))
                    angle_x =_eval_num_expr (in_ax ,context ,0.0 )

                    in_ay =self .get_input_value (node ,3 ,context )
                    if in_ay is None or in_ay =="":in_ay =_get_prop_value (props ,"angle_y",_get_prop_value (props ,"ang_y","0"))
                    angle_y =_eval_num_expr (in_ay ,context ,0.0 )

                    in_anc =self .get_input_value (node ,4 ,context )
                    if in_anc is None or in_anc =="":in_anc =_get_prop_value (props ,"anchor",_get_prop_value (props ,"anclaje","center"))
                    anchor_val =str (in_anc ).strip ()
                    return shape_transform (context ,drawing =shp_val ,mode ="Skew",t =t_val ,angle_x =angle_x ,angle_y =angle_y ,anchor =anchor_val )
                elif "round"in modo_clean or "redond"in modo_clean or "esquina"in modo_clean :
                    in_t =self .get_input_value (node ,1 ,context )
                    if in_t is None or in_t =="":in_t =_get_prop_value (props ,"t","1.0")
                    t_val =_eval_num_expr (in_t ,context ,1.0 )

                    in_rad =self .get_input_value (node ,2 ,context )
                    if in_rad is None or in_rad =="":in_rad =_get_prop_value (props ,"radius","10.0")
                    radius_val =_eval_num_expr (in_rad ,context ,10.0 )

                    in_anc =self .get_input_value (node ,3 ,context )
                    if in_anc is None or in_anc =="":in_anc =_get_prop_value (props ,"anchor","center")
                    anchor_val =str (in_anc ).strip ()

                    corner_mode =str (_get_prop_value (props ,"corner_mode","Round")).strip ()
                    return shape_transform (context ,drawing =shp_val ,mode ="Round Corners",t =t_val ,radius =radius_val ,corner_mode =corner_mode ,anchor =anchor_val )
                elif "flexor"in modo_clean or "curv"in modo_clean or "dobl"in modo_clean :
                    in_t =self .get_input_value (node ,1 ,context )
                    if in_t is None or in_t =="":in_t =_get_prop_value (props ,"t",_get_prop_value (props ,"bend_t","1.0"))
                    bend_t =_eval_num_expr (in_t ,context ,1.0 )

                    curve_in =self .get_input_value (node ,2 ,context )
                    if curve_in is None or curve_in =="":curve_in =str (_get_prop_value (props ,"curve","30")).strip ()

                    in_anc =self .get_input_value (node ,3 ,context )
                    if in_anc is None or in_anc =="":in_anc =_get_prop_value (props ,"anchor","center")
                    anchor_val =str (in_anc ).strip ()

                    axis_val =str (_get_prop_value (props ,"axis","x")).strip ()
                    return shape_transform (context ,drawing =shp_val ,mode ="Flexor",curve =curve_in ,t =bend_t ,bend_t =bend_t ,axis =axis_val ,anchor =anchor_val )
                elif "distort2"in modo_clean or "distort 2"in modo_clean or "distort_2"in modo_clean :
                    mid_val =self .get_input_value (node ,1 ,context )
                    if mid_val is None or mid_val =="":mid_val =str (_get_prop_value (props ,"mid_shape",_get_prop_value (props ,"shape_mid",""))).strip ()
                    mid_val =resolve_shape_value (mid_val ,context )

                    tgt_val =self .get_input_value (node ,2 ,context )
                    if tgt_val is None or tgt_val =="":tgt_val =str (_get_prop_value (props ,"target_shape","")).strip ()
                    tgt_val =resolve_shape_value (tgt_val ,context )

                    in_t =self .get_input_value (node ,3 ,context )
                    if in_t is None or in_t =="":in_t =_get_prop_value (props ,"t","1.0")
                    t_val =_eval_num_expr (in_t ,context ,1.0 )

                    in_slot_4 =self .get_input_value (node ,4 ,context )
                    in_slot_5 =self .get_input_value (node ,5 ,context )
                    in_slot_6 =self .get_input_value (node ,6 ,context )
                    known_anchors ={"center","origin","zero","pos","topleft","bottomleft","topright","bottomright","relativo","absoluto"}

                    prop_energy =_get_prop_value (props ,"energy",_get_prop_value (props ,"fluidez",_get_prop_value (props ,"fluidity","0.35")))
                    prop_step =_get_prop_value (props ,"step_px",_get_prop_value (props ,"step","0"))
                    prop_anchor =_get_prop_value (props ,"anchor","center")

                    energy_val =_eval_num_expr (prop_energy ,context ,0.35 )
                    step_val =_eval_num_expr (prop_step ,context ,0.0 )
                    anchor_val =str (prop_anchor ).strip ()

                    if in_slot_4 is not None and str (in_slot_4 ).strip ()!="":
                        s4_str =str (in_slot_4 ).strip ().lower ()
                        if s4_str in known_anchors :
                            anchor_val =str (in_slot_4 ).strip ()
                        else :
                            energy_val =_eval_num_expr (in_slot_4 ,context ,energy_val )

                    if in_slot_5 is not None and str (in_slot_5 ).strip ()!="":
                        s5_str =str (in_slot_5 ).strip ().lower ()
                        if s5_str in known_anchors :
                            anchor_val =str (in_slot_5 ).strip ()
                        else :
                            step_val =_eval_num_expr (in_slot_5 ,context ,step_val )

                    if in_slot_6 is not None and str (in_slot_6 ).strip ()!="":
                        anchor_val =str (in_slot_6 ).strip ()

                    return shape_transform (context ,drawing =shp_val ,mode ="Distort2",mid_shape =mid_val ,target_shape =tgt_val ,t =t_val ,step_px =step_val ,energy =energy_val ,anchor =anchor_val )
                elif "distort"in modo_clean or "deform"in modo_clean or "morph"in modo_clean :
                    tgt_val =self .get_input_value (node ,1 ,context )
                    if tgt_val is None or tgt_val =="":tgt_val =str (_get_prop_value (props ,"target_shape","")).strip ()
                    tgt_val =resolve_shape_value (tgt_val ,context )

                    in_t =self .get_input_value (node ,2 ,context )
                    if in_t is None or in_t =="":in_t =_get_prop_value (props ,"t","1.0")
                    t_val =_eval_num_expr (in_t ,context ,1.0 )

                    in_slot_3 =self .get_input_value (node ,3 ,context )
                    in_slot_4 =self .get_input_value (node ,4 ,context )
                    in_slot_5 =self .get_input_value (node ,5 ,context )
                    known_anchors ={"center","origin","zero","pos","topleft","bottomleft","topright","bottomright","relativo","absoluto"}

                    prop_energy =_get_prop_value (props ,"energy",_get_prop_value (props ,"fluidez",_get_prop_value (props ,"fluidity","0.35")))
                    prop_step =_get_prop_value (props ,"step_px",_get_prop_value (props ,"step","0"))
                    prop_anchor =_get_prop_value (props ,"anchor","center")

                    energy_val =_eval_num_expr (prop_energy ,context ,0.35 )
                    step_val =_eval_num_expr (prop_step ,context ,0.0 )
                    anchor_val =str (prop_anchor ).strip ()

                    if in_slot_3 is not None and str (in_slot_3 ).strip ()!="":
                        s3_str =str (in_slot_3 ).strip ().lower ()
                        if s3_str in known_anchors :
                            anchor_val =str (in_slot_3 ).strip ()
                        else :
                            energy_val =_eval_num_expr (in_slot_3 ,context ,energy_val )

                    if in_slot_4 is not None and str (in_slot_4 ).strip ()!="":
                        s4_str =str (in_slot_4 ).strip ().lower ()
                        if s4_str in known_anchors :
                            anchor_val =str (in_slot_4 ).strip ()
                        else :
                            step_val =_eval_num_expr (in_slot_4 ,context ,step_val )

                    if in_slot_5 is not None and str (in_slot_5 ).strip ()!="":
                        anchor_val =str (in_slot_5 ).strip ()

                    return shape_transform (context ,drawing =shp_val ,mode ="Distort",target_shape =tgt_val ,t =t_val ,step_px =step_val ,energy =energy_val ,anchor =anchor_val )
                else :
                    in_t =self .get_input_value (node ,1 ,context )
                    if in_t is None or in_t =="":in_t =_get_prop_value (props ,"t","1.0")
                    t_val =_eval_num_expr (in_t ,context ,1.0 )

                    in_r =self .get_input_value (node ,2 ,context )
                    if in_r is None or in_r =="":in_r =_get_prop_value (props ,"ratio","1.0")
                    ratio_val =_eval_num_expr (in_r ,context ,1.0 )

                    in_anc =self .get_input_value (node ,3 ,context )
                    if in_anc is None or in_anc =="":in_anc =_get_prop_value (props ,"anchor","center")
                    anchor_val =str (in_anc ).strip ()

                    inf_mode =str (_get_prop_value (props ,"inflate_mode","Circle")).strip ()
                    return shape_transform (context ,drawing =shp_val ,mode ="Inflate",t =t_val ,ratio =ratio_val ,inflate_mode =inf_mode ,anchor =anchor_val )
            except Exception as e :
                return f"[Err Transform: {e}]"

        if node_type in ["Shape/Multi", "Multi"]:
            try :
                modo = str(_get_prop_value(props, "mode", _get_prop_value(props, "modo", "concentric_squares"))).strip()
                from nodes .shape_nodes import shape_multi ,resolve_shape_value 
                modo_clean =modo .lower ().replace ("é","e").replace ("á","a").replace ("í","i").replace ("ó","o").replace ("ú","u")
                out_mode_val = str(_get_prop_value(props, "out_mode", "shape")).strip()
                loop_mode_val = str(_get_prop_value(props, "loop_mode", "shape")).strip()

                tags_raw =None 
                for idx ,inp in enumerate (node .get ("inputs",[])):
                    if str (inp .get ("name","")).strip ().lower ()in ["tags","tag"]:
                        tags_raw =self .get_input_value (node ,idx ,context )
                        break 
                if tags_raw is None or str (tags_raw ).strip ()=="":
                    tags_raw =str (_get_prop_value (props ,"tags",_get_prop_value (props ,"tag",""))).strip ()

                if "cuadro"in modo_clean or "cuadrad"in modo_clean or "square"in modo_clean or "multi1"in modo_clean :
                    size_val =_eval_num_expr (self .get_input_value (node ,0 ,context )or _get_prop_value (props ,"size","100.0"),context ,100.0 )
                    px_val =self .get_input_value (node ,1 ,context )
                    if px_val is None or str (px_val ).strip ()=="":px_val =_get_prop_value (props ,"px","4")
                    sep_val =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"separation",_get_prop_value (props ,"sep","0.0")),context ,0.0 )
                    t_val =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    anc_val =self .get_input_value (node ,4 ,context )
                    if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")
                    res = shape_multi (context ,mode ="Concentric Squares",size =size_val ,px =px_val ,separation =sep_val ,t =t_val ,anchor =anc_val ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                elif "franja"in modo_clean or "diagonal"in modo_clean or "stripe"in modo_clean or "multi2"in modo_clean :
                    w_val =_eval_num_expr (self .get_input_value (node ,0 ,context )or _get_prop_value (props ,"width","70.0"),context ,70.0 )
                    h_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"height","50.0"),context ,50.0 )
                    px_val =self .get_input_value (node ,2 ,context )
                    if px_val is None or str (px_val ).strip ()=="":px_val =_get_prop_value (props ,"px","6")
                    sep_val =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"separation",_get_prop_value (props ,"sep","0.0")),context ,0.0 )
                    t_val =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    anc_val =self .get_input_value (node ,5 ,context )
                    if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")
                    res = shape_multi (context ,mode ="Diagonal Stripes",width =w_val ,height =h_val ,px =px_val ,separation =sep_val ,t =t_val ,anchor =anc_val ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                elif "anillo"in modo_clean or "multi3"in modo_clean or "ring"in modo_clean :
                    shp_val =self .get_input_value (node ,0 ,context )
                    if not shp_val or str (shp_val ).strip ()=="":shp_val =str (_get_prop_value (props ,"shape","")).strip ()
                    shp_val =resolve_shape_value (shp_val ,context )
                    size_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"size","100.0"),context ,100.0 )
                    bord_val =self .get_input_value (node ,2 ,context )
                    if bord_val is None or str (bord_val ).strip ()=="":bord_val =_get_prop_value (props ,"bord","4")
                    sep_val =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"separation",_get_prop_value (props ,"sep","0.0")),context ,0.0 )
                    t_val =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    anc_val =self .get_input_value (node ,5 ,context )
                    if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")
                    res = shape_multi (context ,drawing =shp_val ,mode ="Concentric Rings",size =size_val ,bord =bord_val ,separation =sep_val ,t =t_val ,anchor =anc_val ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                elif "multi-forma"in modo_clean or "multiforma"in modo_clean or "multi-shape"in modo_clean or "multishape"in modo_clean or "multi5"in modo_clean :
                    shp_val =self .get_input_value (node ,0 ,context )
                    if not shp_val or str (shp_val ).strip ()=="":shp_val =str (_get_prop_value (props ,"shape","")).strip ()
                    w_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"width","60.0"),context ,60.0 )
                    h_val =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"height","50.0"),context ,50.0 )
                    dx_val =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"dx","0.0"),context ,0.0 )
                    dy_val =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"dy","0.0"),context ,0.0 )
                    t_val =_eval_num_expr (self .get_input_value (node ,5 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    anc_val =self .get_input_value (node ,6 ,context )
                    if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")

                    order_val = str(_get_prop_value(props, "order", "Normal")).strip()
                    for idx, inp in enumerate(node.get("inputs", [])):
                        if str(inp.get("name", "")).strip().lower() in ["order", "numpad order", "orden"]:
                            val = self.get_input_value(node, idx, context)
                            if val: order_val = str(val).strip()
                            break

                    res = shape_multi (context ,drawing =shp_val ,mode ="Multi-Shape Mosaic",width =w_val ,height =h_val ,dx =dx_val ,dy =dy_val ,t =t_val ,anchor =anc_val ,order =order_val ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                elif "poligon"in modo_clean or "mosaic"in modo_clean or "polygon"in modo_clean or "multi4"in modo_clean :
                    size_val =_eval_num_expr (self .get_input_value (node ,0 ,context )or _get_prop_value (props ,"size","64.0"),context ,64.0 )
                    sides_val =int (_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"sides","6"),context ,6 ))
                    rings_val =int (_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"rings","1"),context ,1 ))
                    n_val =int (_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"n_layers","25"),context ,25 ))
                    sep_val =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"separation",_get_prop_value (props ,"sep","0.0")),context ,0.0 )
                    t_val =_eval_num_expr (self .get_input_value (node ,5 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    anc_val =self .get_input_value (node ,6 ,context )
                    if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")
                    order_val = str(_get_prop_value(props, "order", "Normal")).strip()
                    for idx, inp in enumerate(node.get("inputs", [])):
                        if str(inp.get("name", "")).strip().lower() in ["order", "numpad order", "orden"]:
                            val = self.get_input_value(node, idx, context)
                            if val: order_val = str(val).strip()
                            break
                    res = shape_multi (context ,mode ="Polygonal Mosaic",size =size_val ,sides =sides_val ,rings =rings_val ,n_layers =n_val ,separation =sep_val ,t =t_val ,anchor =anc_val ,order =order_val ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                elif "segment"in modo_clean or "borde"in modo_clean or "border"in modo_clean or "multi6"in modo_clean :
                    num_inputs =len (node .get ("inputs",[]))
                    first_inp_name =str (node .get ("inputs",[])[0 ].get ("name","")).strip ().lower ()if num_inputs >0 else ""
                    if num_inputs >=8 or first_inp_name in ["shape","base shape","base_shape"]:
                        shp_val =self .get_input_value (node ,0 ,context )
                        if not shp_val or str (shp_val ).strip ()=="":shp_val =str (_get_prop_value (props ,"shape","")).strip ()
                        w_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"width","104.0"),context ,104.0 )
                        h_val =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"height","104.0"),context ,104.0 )
                        bord_val =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"bord","4.0"),context ,4.0 )
                        space_val =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"separation",_get_prop_value (props ,"space","0.0")),context ,0.0 )
                        len_val =_eval_num_expr (self .get_input_value (node ,5 ,context )or _get_prop_value (props ,"length","20.0"),context ,20.0 )
                        t_val =_eval_num_expr (self .get_input_value (node ,6 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                        anc_val =self .get_input_value (node ,7 ,context )
                        if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")
                    else :
                        shp_val =str (_get_prop_value (props ,"shape","")).strip ()
                        w_val =_eval_num_expr (self .get_input_value (node ,0 ,context )or _get_prop_value (props ,"width","104.0"),context ,104.0 )
                        h_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"height","104.0"),context ,104.0 )
                        bord_val =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"bord","4.0"),context ,4.0 )
                        space_val =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"separation",_get_prop_value (props ,"space","0.0")),context ,0.0 )
                        len_val =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"length","20.0"),context ,20.0 )
                        t_val =_eval_num_expr (self .get_input_value (node ,5 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                        anc_val =self .get_input_value (node ,6 ,context )
                        if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")
                    res = shape_multi (context ,drawing =shp_val ,mode ="Segmented Border",width =w_val ,height =h_val ,bord =bord_val ,space =space_val ,length =len_val ,separation =space_val ,t =t_val ,anchor =anc_val ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                elif "roseta"in modo_clean or "rosette"in modo_clean or "pastel"in modo_clean or "radial"in modo_clean or "multi7"in modo_clean :
                    parts_val =int (_eval_num_expr (self .get_input_value (node ,0 ,context )or _get_prop_value (props ,"parts","12"),context ,12 ))
                    r_out_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"r_out","50.0"),context ,50.0 )
                    r_in_val =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"r_in","0.0"),context ,0.0 )
                    sep_val =_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"separation",_get_prop_value (props ,"sep","0.0")),context ,0.0 )
                    t_val =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                    anc_val =self .get_input_value (node ,5 ,context )
                    if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")
                    res = shape_multi (context ,mode ="Radial Rosette",parts =parts_val ,r_out =r_out_val ,r_in =r_in_val ,separation =sep_val ,t =t_val ,anchor =anc_val ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                elif "tunel"in modo_clean or "cascada"in modo_clean or "multi8"in modo_clean or "tunnel"in modo_clean or "cascade"in modo_clean :
                    shp_val =self .get_input_value (node ,0 ,context )
                    if not shp_val or str (shp_val ).strip ()=="":shp_val =str (_get_prop_value (props ,"shape","")).strip ()
                    shp_val =resolve_shape_value (shp_val ,context )
                    s1_val =_eval_num_expr (self .get_input_value (node ,1 ,context )or _get_prop_value (props ,"size1","100.0"),context ,100.0 )
                    s2_val =_eval_num_expr (self .get_input_value (node ,2 ,context )or _get_prop_value (props ,"size2","10.0"),context ,10.0 )
                    loop_val =int (_eval_num_expr (self .get_input_value (node ,3 ,context )or _get_prop_value (props ,"loop","8"),context ,8 ))
                    sep_val =_eval_num_expr (self .get_input_value (node ,4 ,context )or _get_prop_value (props ,"separation",_get_prop_value (props ,"sep","0.0")),context ,0.0 )

                    num_inputs =len (node .get ("inputs",[]))
                    inp_5_name =str (node .get ("inputs",[])[5 ].get ("name","")).lower ()if num_inputs >5 else ""
                    if num_inputs >=8 or inp_5_name .startswith ("dir")or inp_5_name .startswith ("ang"):
                        ang_val =self .get_input_value (node ,5 ,context )
                        if ang_val is None or str (ang_val ).strip ()=="":ang_val =_get_prop_value (props ,"angle",_get_prop_value (props ,"direction","0.0"))
                        t_val =_eval_num_expr (self .get_input_value (node ,6 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                        anc_val =self .get_input_value (node ,7 ,context )
                        if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")
                    else :
                        ang_val =_get_prop_value (props ,"angle",_get_prop_value (props ,"direction","0.0"))
                        t_val =_eval_num_expr (self .get_input_value (node ,5 ,context )or _get_prop_value (props ,"t","1.0"),context ,1.0 )
                        anc_val =self .get_input_value (node ,6 ,context )
                        if anc_val is None or str (anc_val ).strip ()=="":anc_val =_get_prop_value (props ,"anchor","center")

                    res = shape_multi (context ,drawing =shp_val ,mode ="Tunnel / Cascade",size1 =s1_val ,size2 =s2_val ,loop =loop_val ,separation =sep_val ,angle =ang_val ,t =t_val ,anchor =anc_val ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                elif "banner" in modo_clean or "cartela" in modo_clean:
                    w_val = _eval_num_expr(self.get_input_value(node, 0, context) or _get_prop_value(props, "width", "200.0"), context, 200.0)
                    h_val = _eval_num_expr(self.get_input_value(node, 1, context) or _get_prop_value(props, "height", "50.0"), context, 50.0)
                    tip_val = self.get_input_value(node, 2, context)
                    if tip_val is None or str(tip_val).strip() == "": tip_val = _get_prop_value(props, "tip_style", _get_prop_value(props, "style", "Arrow"))
                    fold_val = _eval_num_expr(self.get_input_value(node, 3, context) or _get_prop_value(props, "fold_w", _get_prop_value(props, "fold_width", "0.0")), context, 0.0)
                    bord_val = _eval_num_expr(self.get_input_value(node, 4, context) or _get_prop_value(props, "bord", "0.0"), context, 0.0)
                    t_val = _eval_num_expr(self.get_input_value(node, 5, context) or _get_prop_value(props, "t", "1.0"), context, 1.0)
                    anc_val = self.get_input_value(node, 6, context)
                    if anc_val is None or str(anc_val).strip() == "": anc_val = _get_prop_value(props, "anchor", "center")
                    res = shape_multi(context, mode="Banner", width=w_val, height=h_val, tip_style=tip_val, fold_w=fold_val, bord=bord_val, t=t_val, anchor=anc_val, tags=tags_raw, out_mode=out_mode_val, loop_mode=loop_mode_val)

                elif "gear" in modo_clean or "engranaje" in modo_clean or "rueda" in modo_clean:
                    teeth_val = int(_eval_num_expr(self.get_input_value(node, 0, context) or _get_prop_value(props, "parts", _get_prop_value(props, "teeth", "8")), context, 8))
                    ro_val = _eval_num_expr(self.get_input_value(node, 1, context) or _get_prop_value(props, "r_out", _get_prop_value(props, "radius", "60.0")), context, 60.0)
                    ri_val = _eval_num_expr(self.get_input_value(node, 2, context) or _get_prop_value(props, "r_in", _get_prop_value(props, "root_radius", "45.0")), context, 45.0)
                    rh_val = _eval_num_expr(self.get_input_value(node, 3, context) or _get_prop_value(props, "r_hole", _get_prop_value(props, "hole_radius", "15.0")), context, 15.0)
                    slant_val = _eval_num_expr(self.get_input_value(node, 4, context) or _get_prop_value(props, "slant", _get_prop_value(props, "tooth_slant", "0.35")), context, 0.35)
                    t_val = _eval_num_expr(self.get_input_value(node, 5, context) or _get_prop_value(props, "t", "1.0"), context, 1.0)
                    anc_val = self.get_input_value(node, 6, context)
                    if anc_val is None or str(anc_val).strip() == "": anc_val = _get_prop_value(props, "anchor", "center")
                    res = shape_multi(context, mode="Gear", parts=teeth_val, r_out=ro_val, r_in=ri_val, r_hole=rh_val, slant=slant_val, t=t_val, anchor=anc_val, tags=tags_raw, out_mode=out_mode_val, loop_mode=loop_mode_val)

                else :
                    res = shape_multi (context ,mode =modo ,tags =tags_raw ,out_mode =out_mode_val ,loop_mode =loop_mode_val )

                if isinstance(res, (tuple, list)):
                    if output_slot_index < len(res):
                        return str(res[output_slot_index])
                    return str(res[0])
                return str(res)
            except Exception as e :
                return f"[Err Multi: {e}]"

        elif node_type in ["Functions/Polar to Cartesian","Polar to Cartesian"]:
            try :
                import math 
                x0_raw =self .get_input_value (node ,0 ,context )
                if x0_raw =="":x0_raw =_get_prop_value (props ,"x","0")
                y0_raw =self .get_input_value (node ,1 ,context )
                if y0_raw =="":y0_raw =_get_prop_value (props ,"y","0")
                ang_raw =self .get_input_value (node ,2 ,context )
                if ang_raw =="":ang_raw =_get_prop_value (props ,"angle","0")
                r_raw =self .get_input_value (node ,3 ,context )
                if r_raw =="":r_raw =_get_prop_value (props ,"radius","0")

                x0 =_eval_num_expr (x0_raw ,context ,0.0 )
                y0 =_eval_num_expr (y0_raw ,context ,0.0 )
                ang =_eval_num_expr (ang_raw ,context ,0.0 )
                r =_eval_num_expr (r_raw ,context ,0.0 )

                rad =math .radians (ang )
                dx =r *math .cos (rad )
                dy =r *math .sin (rad )
                res_x =x0 +dx 
                res_y =y0 +dy 

                fmt_x =int (res_x )if float (res_x ).is_integer ()else round (res_x ,2 )
                fmt_y =int (res_y )if float (res_y ).is_integer ()else round (res_y ,2 )
                fmt_dx =int (dx )if float (dx ).is_integer ()else round (dx ,2 )
                fmt_dy =int (dy )if float (dy ).is_integer ()else round (dy ,2 )

                if output_slot_index ==1 :return str (fmt_x )
                elif output_slot_index ==2 :return str (fmt_y )
                elif output_slot_index ==3 :return str (fmt_dx )
                elif output_slot_index ==4 :return str (fmt_dy )
                else :return f"\\pos({fmt_x },{fmt_y })"
            except Exception as e :
                return f"[Err Polars: {e }]"




        elif node_type in ["Functions/Bezier Curve", "Bezier Curve"]:
            try:
                import math

                def _get_val(name, default):
                    inputs = node.get('inputs', [])
                    for idx, inp in enumerate(inputs):
                        inp_name = str(inp.get('name', '')).strip().lower()
                        inp_prop = str(inp.get('property', '')).strip().lower()
                        target_name = name.strip().lower()
                        if inp_name == target_name or inp_prop == target_name:
                            v = self.get_input_value(node, idx, context)
                            if v != "":
                                return v
                    if name.lower() == "shape":
                        for idx, inp in enumerate(inputs):
                            inp_name = str(inp.get('name', '')).strip().lower()
                            if inp_name in ("shape", "path", "forma", "drawing", "forma base", "trazado"):
                                v = self.get_input_value(node, idx, context)
                                if v != "":
                                    return v
                    v = _get_prop_value(props, name.lower(), _get_prop_value(props, name, default))
                    return v if v != "" else default

                def _parse_pt(pt_val, default=(0.0, 0.0)):
                    if isinstance(pt_val, (list, tuple)) and len(pt_val) >= 2:
                        return float(_eval_num_expr(pt_val[0], context, default[0])), float(_eval_num_expr(pt_val[1], context, default[1]))
                    s = str(pt_val).strip()
                    depth = 0
                    split_idx = -1
                    for i, ch in enumerate(s):
                        if ch in '([{':
                            depth += 1
                        elif ch in ')]}':
                            depth -= 1
                        elif ch == ',' and depth == 0:
                            split_idx = i
                            break
                    if split_idx != -1:
                        part0 = s[:split_idx].strip()
                        part1 = s[split_idx + 1:].strip()
                        return float(_eval_num_expr(part0, context, default[0])), float(_eval_num_expr(part1, context, default[1]))
                    elif ' ' in s and depth == 0:
                        parts = s.split(None, 1)
                        return float(_eval_num_expr(parts[0], context, default[0])), float(_eval_num_expr(parts[1], context, default[1]))
                    try:
                        v = float(_eval_num_expr(s, context, default[0]))
                        return v, v
                    except Exception:
                        return default

                def _parse_pts_list(raw_val, default=None):
                    if default is None:
                        default = [(0.0, 0.0), (50.0, 100.0), (150.0, 100.0), (200.0, 0.0)]
                    if isinstance(raw_val, (list, tuple)):
                        pts = [_parse_pt(item, (0.0, 0.0)) for item in raw_val]
                        return pts if len(pts) > 0 else default
                    s = str(raw_val).strip()
                    if not s:
                        return default
                    import re
                    tokens = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', s)
                    if len(tokens) >= 2:
                        pts = []
                        for i in range(0, len(tokens) - 1, 2):
                            pts.append((float(tokens[i]), float(tokens[i + 1])))
                        return pts if len(pts) > 0 else default
                    return default

                def _eval_de_casteljau(pts, t_param):
                    if not pts:
                        return 0.0, 0.0
                    curr = [(float(p[0]), float(p[1])) for p in pts]
                    t = float(t_param)
                    u = 1.0 - t
                    while len(curr) > 1:
                        curr = [
                            (curr[i][0] * u + curr[i + 1][0] * t,
                             curr[i][1] * u + curr[i + 1][1] * t)
                            for i in range(len(curr) - 1)
                        ]
                    return curr[0]

                def _eval_bezier_derivative(pts, t_param):
                    if not pts or len(pts) < 2:
                        return 1.0, 0.0
                    n = len(pts) - 1
                    der_pts = [
                        (n * (pts[i + 1][0] - pts[i][0]),
                         n * (pts[i + 1][1] - pts[i][1]))
                        for i in range(n)
                    ]
                    return _eval_de_casteljau(der_pts, t_param)

                def _subdivide_bezier(pts, t_param):
                    if not pts:
                        return [], [], (0.0, 0.0)
                    curr = [(float(p[0]), float(p[1])) for p in pts]
                    t = float(t_param)
                    u = 1.0 - t
                    left = [curr[0]]
                    right = [curr[-1]]
                    while len(curr) > 1:
                        curr = [
                            (curr[i][0] * u + curr[i + 1][0] * t,
                             curr[i][1] * u + curr[i + 1][1] * t)
                            for i in range(len(curr) - 1)
                        ]
                        left.append(curr[0])
                        right.append(curr[-1])
                    right.reverse()
                    return left, right, curr[0]

                def _eval_bezier_arc_length(pts, t_param=1.0, n_intervals=16):
                    t = max(0.0, min(1.0, float(t_param)))
                    if t <= 1e-12:
                        return 0.0
                    m = max(4, n_intervals * 2)
                    h = t / float(m)
                    def _speed(s):
                        dx, dy = _eval_bezier_derivative(pts, s)
                        return math.hypot(dx, dy)
                    total = _speed(0.0) + _speed(t)
                    for i in range(1, m):
                        coeff = 4.0 if i % 2 == 1 else 2.0
                        total += coeff * _speed(i * h)
                    return (h / 3.0) * total

                def _bezier_length_to_t(pts, target_len, total_len=None, tol=1e-5, max_iter=24):
                    if total_len is None:
                        total_len = _eval_bezier_arc_length(pts, 1.0)
                    if total_len <= 1e-9 or target_len <= 0.0:
                        return 0.0
                    if target_len >= total_len:
                        return 1.0
                    low, high = 0.0, 1.0
                    cur_t = target_len / total_len
                    for _ in range(max_iter):
                        cur_len = _eval_bezier_arc_length(pts, cur_t)
                        err = cur_len - target_len
                        if abs(err) < tol:
                            break
                        if err < 0:
                            low = cur_t
                        else:
                            high = cur_t
                        cur_t = 0.5 * (low + high)
                    return max(0.0, min(1.0, cur_t))

                def _bezier_pts_to_assdraw(pts):
                    if not pts:
                        return ""
                    if len(pts) == 2:
                        return f"m {round(pts[0][0], 2)} {round(pts[0][1], 2)} l {round(pts[1][0], 2)} {round(pts[1][1], 2)}"
                    elif len(pts) == 3:
                        x0, y0 = pts[0]
                        x1, y1 = pts[1]
                        x2, y2 = pts[2]
                        cp1_x = x0 + (2.0 / 3.0) * (x1 - x0)
                        cp1_y = y0 + (2.0 / 3.0) * (y1 - y0)
                        cp2_x = x2 + (2.0 / 3.0) * (x1 - x2)
                        cp2_y = y2 + (2.0 / 3.0) * (y1 - y2)
                        return f"m {round(x0, 2)} {round(y0, 2)} b {round(cp1_x, 2)} {round(cp1_y, 2)} {round(cp2_x, 2)} {round(cp2_y, 2)} {round(x2, 2)} {round(y2, 2)}"
                    elif len(pts) == 4:
                        return f"m {round(pts[0][0], 2)} {round(pts[0][1], 2)} b {round(pts[1][0], 2)} {round(pts[1][1], 2)} {round(pts[2][0], 2)} {round(pts[2][1], 2)} {round(pts[3][0], 2)} {round(pts[3][1], 2)}"
                    else:
                        out = [f"m {round(pts[0][0], 2)} {round(pts[0][1], 2)}"]
                        steps = max(16, (len(pts) - 1) * 8)
                        for s_idx in range(1, steps + 1):
                            st = s_idx / float(steps)
                            sx, sy = _eval_de_casteljau(pts, st)
                            out.append(f"l {round(sx, 2)} {round(sy, 2)}")
                        return " ".join(out)

                def _generate_bezier_trajectory(loops=8, dmin=50.0, dmax=120.0, seed=None, origin=(0.0, 0.0), traj_mode="Free Wander"):
                    import random
                    rng = random.Random(seed) if seed is not None else random
                    ox, oy = float(origin[0]), float(origin[1])
                    dmin = abs(float(dmin))
                    dmax = abs(float(dmax))
                    if dmin > dmax:
                        dmin, dmax = dmax, dmin
                    loops = max(1, int(loops))
                    mode_str = str(traj_mode).strip().lower()

                    if "closed" in mode_str or "orbit" in mode_str or "bucle" in mode_str:
                        # Closed periodic loop around origin
                        n_pts = max(3, loops)
                        angles = [2.0 * math.pi * k / n_pts + rng.uniform(-0.3 / n_pts, 0.3 / n_pts) for k in range(n_pts)]
                        radii = [rng.uniform(dmin, dmax) for _ in range(n_pts)]
                        pts = [(ox + r * math.cos(a), oy + r * math.sin(a)) for a, r in zip(angles, radii)]

                        out_parts = [f"m {round(pts[0][0], 2)} {round(pts[0][1], 2)} b"]
                        for k in range(n_pts):
                            p_prev = pts[(k - 1) % n_pts]
                            p_curr = pts[k]
                            p_next = pts[(k + 1) % n_pts]
                            p_next2 = pts[(k + 2) % n_pts]

                            t1x = (p_next[0] - p_prev[0]) / 6.0
                            t1y = (p_next[1] - p_prev[1]) / 6.0
                            t2x = (p_next2[0] - p_curr[0]) / 6.0
                            t2y = (p_next2[1] - p_curr[1]) / 6.0

                            cp1 = (round(p_curr[0] + t1x, 2), round(p_curr[1] + t1y, 2))
                            cp2 = (round(p_next[0] - t2x, 2), round(p_next[1] - t2y, 2))
                            end_pt = (round(p_next[0], 2), round(p_next[1], 2))
                            out_parts.append(f"{cp1[0]} {cp1[1]} {cp2[0]} {cp2[1]} {end_pt[0]} {end_pt[1]}")
                        return " ".join(out_parts)

                    elif "bound" in mode_str or "acotad" in mode_str:
                        # Bounded wander around origin
                        curr_x, curr_y = ox, oy
                        out_parts = [f"m {round(ox, 2)} {round(oy, 2)} b"]
                        target_pts = [(ox, oy)]
                        for k in range(loops):
                            ang = rng.uniform(0, 2.0 * math.pi)
                            r = rng.uniform(dmin, dmax)
                            target_pts.append((ox + r * math.cos(ang), oy + r * math.sin(ang)))

                        for k in range(len(target_pts) - 1):
                            p_prev = target_pts[max(0, k - 1)]
                            p_curr = target_pts[k]
                            p_next = target_pts[k + 1]
                            p_next2 = target_pts[min(len(target_pts) - 1, k + 2)]

                            t1x = (p_next[0] - p_prev[0]) / 4.0
                            t1y = (p_next[1] - p_prev[1]) / 4.0
                            t2x = (p_next2[0] - p_curr[0]) / 4.0
                            t2y = (p_next2[1] - p_curr[1]) / 4.0

                            cp1 = (round(p_curr[0] + t1x, 2), round(p_curr[1] + t1y, 2))
                            cp2 = (round(p_next[0] - t2x, 2), round(p_next[1] - t2y, 2))
                            end_pt = (round(p_next[0], 2), round(p_next[1], 2))
                            out_parts.append(f"{cp1[0]} {cp1[1]} {cp2[0]} {cp2[1]} {end_pt[0]} {end_pt[1]}")
                        return " ".join(out_parts)

                    else:
                        # Free Wander (Cumulative random walk)
                        curr_x, curr_y = ox, oy
                        out_parts = [f"m {round(ox, 2)} {round(oy, 2)} b"]
                        for _ in range(loops):
                            dx1 = rng.uniform(dmin, dmax) * (1 if rng.random() > 0.5 else -1)
                            dy1 = rng.uniform(dmin, dmax) * (1 if rng.random() > 0.5 else -1)
                            dx2 = rng.uniform(dmin, dmax) * (1 if rng.random() > 0.5 else -1)
                            dy2 = rng.uniform(dmin, dmax) * (1 if rng.random() > 0.5 else -1)
                            dx3 = rng.uniform(dmin, dmax) * (1 if rng.random() > 0.5 else -1)
                            dy3 = rng.uniform(dmin, dmax) * (1 if rng.random() > 0.5 else -1)
                            cp1 = (round(curr_x + dx1, 2), round(curr_y + dy1, 2))
                            cp2 = (round(curr_x + dx1 + dx2, 2), round(curr_y + dy1 + dy2, 2))
                            curr_x += dx1 + dx2 + dx3
                            curr_y += dy1 + dy2 + dy3
                            end_pt = (round(curr_x, 2), round(curr_y, 2))
                            out_parts.append(f"{cp1[0]} {cp1[1]} {cp2[0]} {cp2[1]} {end_pt[0]} {end_pt[1]}")
                        return " ".join(out_parts)

                def _sample_polyline_arc_length(pts, progress_t):
                    if pts is None or len(pts) == 0:
                        return 0.0, 0.0, 1.0, 0.0
                    if len(pts) == 1:
                        return float(pts[0][0]), float(pts[0][1]), 1.0, 0.0
                    seg_lens = []
                    total_len = 0.0
                    for k in range(len(pts) - 1):
                        d = math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
                        seg_lens.append(d)
                        total_len += d
                    if total_len <= 1e-9:
                        return float(pts[0][0]), float(pts[0][1]), 1.0, 0.0
                    target_d = max(0.0, min(1.0, progress_t)) * total_len
                    accum = 0.0
                    chosen_idx = len(pts) - 2
                    frac = 0.0
                    for k, slen in enumerate(seg_lens):
                        if accum + slen >= target_d:
                            chosen_idx = k
                            frac = (target_d - accum) / max(1e-9, slen)
                            break
                        accum += slen
                    p_a = pts[chosen_idx]
                    p_b = pts[chosen_idx + 1]
                    cur_x = p_a[0] + (p_b[0] - p_a[0]) * frac
                    cur_y = p_a[1] + (p_b[1] - p_a[1]) * frac
                    der_x = p_b[0] - p_a[0]
                    der_y = p_b[1] - p_a[1]
                    return cur_x, cur_y, der_x, der_y

                mode = _get_prop_value(props, "mode", _get_prop_value(props, "modo", "Cubic 2D"))
                m_lower = str(mode).strip().lower()
                bx, by, dx, dy = 0.0, 0.0, 1.0, 0.0
                spline_str = ""
                spline_l_str = ""
                spline_r_str = ""

                origin_raw = _get_val("Origin", _get_val("origin", ""))
                ox, oy = _parse_pt(origin_raw, (0.0, 0.0))

                t_raw = _get_val("t", "0.5")
                ft = float(_eval_num_expr(t_raw, context, 0.5))
                ft = max(0.0, min(1.0, ft))

                subdivs_raw = _get_val("Subdivs", "100")
                subdivs = max(0, min(2000, int(float(_eval_num_expr(subdivs_raw, context, 100)))))

                if "quadratic" in m_lower or "cuadratica" in m_lower or "2d quadratic" in m_lower or "quad" in m_lower or "cuad" in m_lower:
                    x0, y0 = _parse_pt(_get_val("P0", "0,0"), (0.0, 0.0))
                    x1, y1 = _parse_pt(_get_val("P1", "50,100"), (50.0, 100.0))
                    x2, y2 = _parse_pt(_get_val("P2", "100,0"), (100.0, 0.0))
                    pts = [(x0 + ox, y0 + oy), (x1 + ox, y1 + oy), (x2 + ox, y2 + oy)]
                    spline_str = _bezier_pts_to_assdraw(pts)
                    bx, by = _eval_de_casteljau(pts, ft)
                    dx, dy = _eval_bezier_derivative(pts, ft)

                elif "n-degree" in m_lower or "n-grado" in m_lower or "polinomial" in m_lower or "multi" in m_lower or "grado n" in m_lower:
                    raw_pts = _get_val("Points", _get_val("puntos", ""))
                    if not raw_pts:
                        p0 = _parse_pt(_get_val("P0", "0,0"), (0.0, 0.0))
                        p1 = _parse_pt(_get_val("P1", "50,100"), (50.0, 100.0))
                        p2 = _parse_pt(_get_val("P2", "150,100"), (150.0, 100.0))
                        p3 = _parse_pt(_get_val("P3", "200,0"), (200.0, 0.0))
                        pts = [p0, p1, p2, p3]
                    else:
                        pts = _parse_pts_list(raw_pts)
                    if ox != 0.0 or oy != 0.0:
                        pts = [(p[0] + ox, p[1] + oy) for p in pts]
                    spline_str = _bezier_pts_to_assdraw(pts)
                    bx, by = _eval_de_casteljau(pts, ft)
                    dx, dy = _eval_bezier_derivative(pts, ft)

                elif "subdivide" in m_lower or "subdivision" in m_lower or "split" in m_lower or "cut" in m_lower:
                    p0 = _parse_pt(_get_val("P0", "0,0"), (0.0, 0.0))
                    p1 = _parse_pt(_get_val("P1", "50,100"), (50.0, 100.0))
                    p2 = _parse_pt(_get_val("P2", "150,100"), (150.0, 100.0))
                    p3 = _parse_pt(_get_val("P3", "200,0"), (200.0, 0.0))
                    pts = [(p0[0] + ox, p0[1] + oy), (p1[0] + ox, p1[1] + oy), (p2[0] + ox, p2[1] + oy), (p3[0] + ox, p3[1] + oy)]
                    left_pts, right_pts, split_pt = _subdivide_bezier(pts, ft)
                    spline_str = _bezier_pts_to_assdraw(pts)
                    spline_l_str = _bezier_pts_to_assdraw(left_pts)
                    spline_r_str = _bezier_pts_to_assdraw(right_pts)
                    bx, by = split_pt
                    dx, dy = _eval_bezier_derivative(pts, ft)

                elif "trajectory" in m_lower or "trayectoria" in m_lower:
                    traj_mode_raw = _get_val("Trajectory Mode", _get_prop_value(props, "traj_mode", _get_prop_value(props, "trajectory_mode", "Free Wander")))
                    dist_range_raw = _get_val("Dist Range", _get_val("dist_range", _get_val("Distance", _get_val("P0", "50,120"))))
                    seed_raw = _get_val("Seed", _get_val("seed", _get_val("P1", "1")))
                    loops_raw = _get_val("Loops", _get_val("loops", _get_val("Subdivs", "8")))
                    shape_raw = _get_val("Shape", "").strip()
                    raw_pts = _get_val("Points", _get_val("puntos", "")).strip()

                    if shape_raw != "":
                        if shape_raw.lower().startswith("shape."):
                            from nodes.shape_nodes import resolve_shape_value
                            shape_raw = resolve_shape_value(shape_raw, context)
                        shape_str = str(shape_raw).strip()
                        eff_subdivs = max(5, subdivs if subdivs >= 2 else 100)
                        from clipper_engine import ClipperEngine
                        contours = ClipperEngine.parse_assdraw(shape_str, bezier_steps=eff_subdivs) if shape_str else []
                        if contours and len(contours) > 0 and len(contours[0]) > 1:
                            pts = [(p[0] + ox, p[1] + oy) for c in contours for p in c]
                            bx, by, dx, dy = _sample_polyline_arc_length(pts, ft)
                            spline_str = shape_str
                        else:
                            dmin_val, dmax_val = _parse_pt(dist_range_raw, (50.0, 120.0))
                            seed_val = int(float(_eval_num_expr(seed_raw, context, 1)))
                            loops_val = max(1, min(64, int(float(_eval_num_expr(loops_raw, context, 8)))))
                            spline_str = _generate_bezier_trajectory(loops=loops_val, dmin=abs(dmin_val), dmax=abs(dmax_val), seed=seed_val, origin=(ox, oy), traj_mode=traj_mode_raw)
                            from clipper_engine import ClipperEngine
                            contours = ClipperEngine.parse_assdraw(spline_str, bezier_steps=max(5, subdivs if subdivs >= 2 else 50))
                            pts = [p for c in contours for p in c] if contours else [(ox, oy)]
                            bx, by, dx, dy = _sample_polyline_arc_length(pts, ft)
                    elif raw_pts != "":
                        pts = _parse_pts_list(raw_pts)
                        if ox != 0.0 or oy != 0.0:
                            pts = [(p[0] + ox, p[1] + oy) for p in pts]
                        if len(pts) >= 4 and len(pts) % 3 == 1:
                            spline_str = _bezier_pts_to_assdraw(pts)
                        else:
                            spline_str = "m " + " ".join(f"{round(p[0],2)} {round(p[1],2)}" for p in pts)
                        from clipper_engine import ClipperEngine
                        contours = ClipperEngine.parse_assdraw(spline_str, bezier_steps=max(5, subdivs if subdivs >= 2 else 50))
                        pts_sampled = [p for c in contours for p in c] if contours else pts
                        bx, by, dx, dy = _sample_polyline_arc_length(pts_sampled, ft)
                    else:
                        dmin_val, dmax_val = _parse_pt(dist_range_raw, (50.0, 120.0))
                        seed_val = int(float(_eval_num_expr(seed_raw, context, 1)))
                        loops_val = max(1, min(64, int(float(_eval_num_expr(loops_raw, context, 8)))))
                        spline_str = _generate_bezier_trajectory(loops=loops_val, dmin=abs(dmin_val), dmax=abs(dmax_val), seed=seed_val, origin=(ox, oy), traj_mode=traj_mode_raw)
                        from clipper_engine import ClipperEngine
                        contours = ClipperEngine.parse_assdraw(spline_str, bezier_steps=max(5, subdivs if subdivs >= 2 else 50))
                        pts = [p for c in contours for p in c] if contours else [(ox, oy)]
                        bx, by, dx, dy = _sample_polyline_arc_length(pts, ft)

                elif any(k in m_lower for k in ("shape", "path", "contour", "trazado", "assdraw", "tangent", "normal", "constant", "speed", "velocidad")) or _get_val("Shape", "").strip() != "":
                    shape_raw = _get_val("Shape", "")
                    if str(shape_raw).strip().lower().startswith("shape."):
                        from nodes.shape_nodes import resolve_shape_value
                        shape_raw = resolve_shape_value(shape_raw, context)
                    shape_str = str(shape_raw).strip()
                    eff_subdivs = max(5, subdivs if subdivs >= 2 else 100)
                    from clipper_engine import ClipperEngine
                    contours = ClipperEngine.parse_assdraw(shape_str, bezier_steps=eff_subdivs) if shape_str else []
                    if contours and len(contours) > 0 and len(contours[0]) > 1:
                        pts = [(p[0] + ox, p[1] + oy) for c in contours for p in c]
                        bx, by, dx, dy = _sample_polyline_arc_length(pts, ft)
                        spline_str = shape_str
                    else:
                        p0 = _parse_pt(_get_val("P0", "0,0"), (0.0, 0.0))
                        p1 = _parse_pt(_get_val("P1", "50,100"), (50.0, 100.0))
                        p2 = _parse_pt(_get_val("P2", "150,100"), (150.0, 100.0))
                        p3 = _parse_pt(_get_val("P3", "200,0"), (200.0, 0.0))
                        pts = [(p0[0] + ox, p0[1] + oy), (p1[0] + ox, p1[1] + oy), (p2[0] + ox, p2[1] + oy), (p3[0] + ox, p3[1] + oy)]
                        spline_str = _bezier_pts_to_assdraw(pts)
                        if "constant" in m_lower or "speed" in m_lower or "velocidad" in m_lower:
                            t_mapped = _bezier_length_to_t(pts, ft * _eval_bezier_arc_length(pts, 1.0))
                            bx, by = _eval_de_casteljau(pts, t_mapped)
                            dx, dy = _eval_bezier_derivative(pts, t_mapped)
                        else:
                            bx, by = _eval_de_casteljau(pts, ft)
                            dx, dy = _eval_bezier_derivative(pts, ft)

                else:
                    # Cubic 2D (Default)
                    p0 = _parse_pt(_get_val("P0", "0,0"), (0.0, 0.0))
                    p1 = _parse_pt(_get_val("P1", "50,100"), (50.0, 100.0))
                    p2 = _parse_pt(_get_val("P2", "150,100"), (150.0, 100.0))
                    p3 = _parse_pt(_get_val("P3", "200,0"), (200.0, 0.0))
                    pts = [(p0[0] + ox, p0[1] + oy), (p1[0] + ox, p1[1] + oy), (p2[0] + ox, p2[1] + oy), (p3[0] + ox, p3[1] + oy)]
                    spline_str = _bezier_pts_to_assdraw(pts)
                    bx, by = _eval_de_casteljau(pts, ft)
                    dx, dy = _eval_bezier_derivative(pts, ft)

                speed = math.sqrt(dx * dx + dy * dy)
                tan_rad = math.atan2(dy, dx)
                tan_deg = (math.degrees(tan_rad) + 360.0) % 360.0
                norm_deg = (tan_deg + 90.0) % 360.0

                fbx = round(float(bx), 2)
                fby = round(float(by), 2)
                fmt_x = int(fbx) if fbx.is_integer() else fbx
                fmt_y = int(fby) if fby.is_integer() else fby

                if not spline_l_str:
                    spline_l_str = spline_str
                if not spline_r_str:
                    spline_r_str = spline_str

                if output_slot_index == 0: return f"\\pos({fmt_x},{fmt_y})"
                elif output_slot_index == 1: return str(fmt_x)
                elif output_slot_index == 2: return str(fmt_y)
                elif output_slot_index == 3: return str(round(tan_deg, 2))
                elif output_slot_index == 4: return str(round(norm_deg, 2))
                elif output_slot_index == 5: return spline_str
                elif output_slot_index == 6: return spline_l_str
                elif output_slot_index == 7: return spline_r_str
                else:
                    return f"\\pos({fmt_x},{fmt_y})"
            except Exception as e:
                return f"[Err Bezier Curve: {e}]"




        elif node_type in ["Functions/Text to Shape","Text to Shape"]:
            try :
                txt =self .get_input_value (node ,0 ,context )
                if txt =="":txt =_get_prop_value (props ,"text","")

                font_name =self .get_input_value (node ,1 ,context )
                if font_name =="":
                    font_name =_get_prop_value (props ,"font_name","")

                font_size_raw =self .get_input_value (node ,2 ,context )
                if font_size_raw =="":
                    font_size_raw =_get_prop_value (props ,"font_size","")
                font_size =int (_eval_num_expr (font_size_raw ,context ,100.0 ))if font_size_raw !=""else None 

                scale_raw =self .get_input_value (node ,3 ,context )
                if scale_raw =="":scale_raw =_get_prop_value (props ,"scale","")
                if scale_raw =="":scale_raw ="1.0"
                scale =float (_eval_num_expr (scale_raw ,context ,1.0 ))

                bold_raw =_get_prop_value (props ,"bold","")
                bold =str (bold_raw ).lower ()in ["true","1","yes"]if bold_raw !=""else None 
                italic_raw =_get_prop_value (props ,"italic","")
                italic =str (italic_raw ).lower ()in ["true","1","yes"]if italic_raw !=""else None 

                from font_vector_engine import FontVectorEngine 
                from clipper_engine import ClipperEngine 
                shape_str =FontVectorEngine .from_context (
                text =str (txt )if txt else None ,
                context =context ,
                font_name =str (font_name )if font_name else None ,
                font_size =font_size ,
                bold =bold ,
                italic =italic ,
                scale =scale 
                )
                contours =ClipperEngine .parse_assdraw (shape_str )
                _ ,_ ,_ ,_ ,_ ,_ ,w ,h =ClipperEngine .get_bbox (contours )

                if output_slot_index ==1 :return str (round (w ,2 ))
                elif output_slot_index ==2 :return str (round (h ,2 ))
                return shape_str 
            except Exception as e :
                return f"[Err Text to Shape: {e }]"




        elif node_type in ["Shape/IMG to Shape","IMG to Shape"]:
            try :
                img_path =self .get_input_value (node ,0 ,context )
                if not img_path or str (img_path ).strip ()=="":
                    img_path =str (_get_prop_value (props ,"image_path","")).strip ()

                frame_raw =self .get_input_value (node ,1 ,context )
                if not frame_raw or str (frame_raw ).strip ()=="":
                    frame_raw =_get_prop_value (props ,"frame_idx","1")

                from img_tracer_engine import _is_animated_gif 
                if _is_animated_gif (img_path )and str (frame_raw ).strip ()in ["1",""]:
                    frame_raw ="ish_i"

                if isinstance (context ,dict ):
                    if 'ish_i'not in context :
                        context ['ish_i']=int (context .get ('j',1 ))

                frame_index =int (_eval_num_expr (frame_raw ,context ,1.0 ))
                if isinstance (context ,dict ):
                    context ['ish_i']=frame_index 

                threshold_raw =self .get_input_value (node ,2 ,context )
                if not threshold_raw or str (threshold_raw ).strip ()=="":
                    threshold_raw =_get_prop_value (props ,"threshold","128")
                threshold =int (_eval_num_expr (threshold_raw ,context ,128.0 ))

                tolerance_raw =self .get_input_value (node ,3 ,context )
                if not tolerance_raw or str (tolerance_raw ).strip ()=="":
                    tolerance_raw =_get_prop_value (props ,"tolerance","1.0")
                tolerance =float (_eval_num_expr (tolerance_raw ,context ,1.0 ))

                alphamax_raw =self .get_input_value (node ,4 ,context )
                if not alphamax_raw or str (alphamax_raw ).strip ()=="":
                    alphamax_raw =_get_prop_value (props ,"alphamax","1.0")
                alphamax =float (_eval_num_expr (alphamax_raw ,context ,1.0 ))

                opttoler_raw =self .get_input_value (node ,5 ,context )
                if not opttoler_raw or str (opttoler_raw ).strip ()=="":
                    opttoler_raw =_get_prop_value (props ,"opttoler","0.2")
                opttoler =float (_eval_num_expr (opttoler_raw ,context ,0.2 ))

                out_scale_raw =self .get_input_value (node ,6 ,context )
                if not out_scale_raw or str (out_scale_raw ).strip ()=="":
                    out_scale_raw =_get_prop_value (props ,"out_scale","1.0")
                out_scale =float (_eval_num_expr (out_scale_raw ,context ,1.0 ))
                if out_scale <=0 :out_scale =1.0 

                out_w_raw =self .get_input_value (node ,7 ,context )
                if not out_w_raw or str (out_w_raw ).strip ()=="":
                    out_w_raw =_get_prop_value (props ,"out_w","0.0")
                out_w =float (_eval_num_expr (out_w_raw ,context ,0.0 ))

                out_h_raw =self .get_input_value (node ,8 ,context )
                if not out_h_raw or str (out_h_raw ).strip ()=="":
                    out_h_raw =_get_prop_value (props ,"out_h","0.0")
                out_h =float (_eval_num_expr (out_h_raw ,context ,0.0 ))

                offset_x_raw =self .get_input_value (node ,9 ,context )
                if not offset_x_raw or str (offset_x_raw ).strip ()=="":
                    offset_x_raw =_get_prop_value (props ,"offset_x","0.0")
                offset_x =float (_eval_num_expr (offset_x_raw ,context ,0.0 ))

                offset_y_raw =self .get_input_value (node ,10 ,context )
                if not offset_y_raw or str (offset_y_raw ).strip ()=="":
                    offset_y_raw =_get_prop_value (props ,"offset_y","0.0")
                offset_y =float (_eval_num_expr (offset_y_raw ,context ,0.0 ))

                img_scale_raw =self .get_input_value (node ,11 ,context )
                if not img_scale_raw or str (img_scale_raw ).strip ()=="":
                    img_scale_raw =_get_prop_value (props ,"img_scale","1.0")
                img_scale =float (_eval_num_expr (img_scale_raw ,context ,1.0 ))

                bin_mode =self .get_input_value (node ,12 ,context )
                if not bin_mode or str (bin_mode ).strip ()=="":
                    bin_mode =str (_get_prop_value (props ,"bin_mode","Luminance")).strip ()

                mode = str(_get_prop_value(props, "mode", "potrace")).strip()
                anchor = str(_get_prop_value(props, "anchor", "center")).strip().lower()
                if anchor in ("absolute", "absoluto", "zero", "pantalla"):
                    unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit') if isinstance(context, dict) else None
                    pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0))))) if isinstance(context, dict) else 0.0
                    pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0))))) if isinstance(context, dict) else 0.0
                    offset_x += pos_x
                    offset_y += pos_y

                invert_str = str(_get_prop_value(props, "invert", "normal")).strip()
                invert = invert_str.lower() in ("inverted", "invert")

                invert_img_str = str(_get_prop_value(props, "invert_img", "normal")).strip()
                use_inverted_img = invert_img_str.lower() in ("inverted", "invert")

                from img_tracer_engine import trace_image 
                traced =trace_image (
                image_path =img_path ,
                mode =mode ,
                threshold =threshold ,
                invert =invert ,
                tolerance =tolerance ,
                out_scale =out_scale ,
                out_w =out_w ,
                out_h =out_h ,
                anchor =anchor ,
                offset_x =offset_x ,
                offset_y =offset_y ,
                img_scale =img_scale ,
                bin_mode =bin_mode ,
                alphamax =alphamax ,
                opttoler =opttoler ,
                frame_index =frame_index ,
                invert_img =use_inverted_img 
                )

                tot_fr =traced .get ("total_frames",1 )
                if isinstance (context ,dict ):
                    context ['ish_n']=tot_fr 
                    context ['ish_max']=tot_fr 
                    context ['total_frames']=tot_fr 

                if output_slot_index ==1 :return str (traced .get ("width",0.0 ))
                elif output_slot_index ==2 :return str (traced .get ("height",0.0 ))
                elif output_slot_index ==3 :return str (traced .get ("points",0 ))
                elif output_slot_index ==4 :return str (traced .get ("shapes_array",""))
                elif output_slot_index ==5 :return str (tot_fr )
                return traced .get ("shape","")
            except Exception as e :
                return f"[Err IMG to Shape: {e }]"





        elif node_type in ["Time/Synced", "Synced"]:
            try :
                line =None 
                if isinstance (context ,dict ):
                    line =context .get ('line')or context .get ('active_line')
                    if not line and context .get ('active_unit'):
                        line =getattr (context ['active_unit'],'line',None )

                inputs_list = node.get('inputs', [])
                def _get_synced_input(prop_names, default_val, fallback_idx):
                    for idx, inp in enumerate(inputs_list):
                        if isinstance(inp, dict):
                            inp_p = str(inp.get('property') or '').lower()
                            inp_n = str(inp.get('name') or '').lower()
                            if any(p.lower() in (inp_p, inp_n) for p in prop_names):
                                if self.is_port_connected(node, idx):
                                    return self.get_input_value(node, idx, context)
                                val = _get_prop_value(props, inp.get('property') or inp.get('name'), "")
                                if val != "": return str(val)
                    for p in prop_names:
                        val = _get_prop_value(props, p, "")
                        if val != "": return str(val)
                    if fallback_idx < len(inputs_list) and self.is_port_connected(node, fallback_idx):
                        return self.get_input_value(node, fallback_idx, context)
                    return str(default_val)

                p_const_raw = _get_synced_input(["progression_const", "constant", "p_const"], "0", 0)
                p_const = _eval_num_expr(p_const_raw, context, 0.0)

                fade_raw = _get_synced_input(["fade_dur", "fade", "fade_ms"], "300", 1)
                fade_dur = _eval_num_expr(fade_raw, context, 300.0)

                max_add_raw = _get_synced_input(["max_added_time", "max_extra", "max extra"], "2000", 2)
                max_add = _eval_num_expr(max_add_raw, context, 2000.0)

                delay_raw = _get_synced_input(["delay_ms", "delay", "delay_line", "delay line"], "250", 3)
                delay = _eval_num_expr(delay_raw, context, 250.0)

                thresh_raw = _get_synced_input(["max_gap_threshold", "threshold", "max_gap"], "3000", 4)
                max_gap = _eval_num_expr(thresh_raw, context, 3000.0)

                mode = str(_get_prop_value(props, "mode", "order")).strip().lower()

                from nodes .time_nodes import time_synchronized_extra_node 
                final_extra =time_synchronized_extra_node (
                context ,
                progression_const =p_const ,
                fade_dur =fade_dur ,
                max_added_time =max_add ,
                delay_ms =delay ,
                max_gap_threshold =max_gap ,
                mode =mode 
                )

                line_end =getattr (line ,'end_time',getattr (line ,'end',0 ))if line else 0 
                sync_end =line_end +final_extra 

                if output_slot_index ==1 :return str (round (sync_end ,2 ))
                return str (round (final_extra ,2 ))
            except Exception as e :
                return f"[Err Synced: {e}]"




        elif node_type in ["Shape/Concentric Borders","Concentric Borders"]:
            try :
                shp_raw =self .get_input_value (node ,0 ,context )
                if shp_raw =="":shp_raw =str (_get_prop_value (props ,"shape","")).strip ()

                mode_raw =self .get_input_value (node ,1 ,context )
                if mode_raw =="":mode_raw =str (_get_prop_value (props ,"mode",_get_prop_value (props ,"modo","hollow"))).strip ()

                loops_raw =self .get_input_value (node ,2 ,context )
                if loops_raw =="":loops_raw =str (_get_prop_value (props ,"loop_count",_get_prop_value (props ,"max_rings","5"))).strip ()

                sep_raw =self .get_input_value (node ,3 ,context )
                if sep_raw =="":sep_raw =str (_get_prop_value (props ,"separation","5")).strip ()

                ov_raw =self .get_input_value (node ,4 ,context )
                if ov_raw =="":ov_raw =str (_get_prop_value (props ,"overlap","0.5")).strip ()

                anchor_raw =self .get_input_value (node ,5 ,context )
                if anchor_raw =="":anchor_raw =str (_get_prop_value (props ,"anchor","relative")).strip ()

                out_mode_raw =str (_get_prop_value (props ,"out_mode","shape")).strip ()

                from nodes .shape_nodes import shape_concentric_borders_node 
                ring_shp ,pos_str ,idx_ring ,total_rings =shape_concentric_borders_node (
                context ,
                shape =shp_raw ,
                separation =sep_raw ,
                overlap =ov_raw ,
                mode =mode_raw ,
                loop_count =loops_raw ,
                out_mode =out_mode_raw ,
                anchor =anchor_raw 
                )

                if output_slot_index ==1 :
                    parent_x =float (getattr (context .get ('active_unit'),'center',getattr (context .get ('line'),'center',0.0 )))if context else 0.0 
                    parent_y =float (getattr (context .get ('active_unit'),'middle',getattr (context .get ('line'),'middle',0.0 )))if context else 0.0 
                    return f"\\pos({round (parent_x ,2 )},{round (parent_y ,2 )})"if (parent_x !=0 or parent_y !=0 )else pos_str 
                elif output_slot_index ==2 :
                    return str (idx_ring )
                elif output_slot_index ==3 :
                    return str (total_rings )
                return ring_shp 
            except Exception as e :
                return f"[Err Concentric Borders: {e }]"




        elif node_type in ["Shape/Walker", "Walker"]:
            try :
                shp_raw =self .get_input_value (node ,0 ,context )
                if shp_raw =="":shp_raw =str (_get_prop_value (props ,"shape","")).strip ()

                prog_raw =self .get_input_value (node ,1 ,context )
                if prog_raw =="":prog_raw =str (_get_prop_value (props ,"progress",_get_prop_value (props ,"progreso","1.0"))).strip ()

                start_raw =self .get_input_value (node ,2 ,context )
                if start_raw =="":start_raw =str (_get_prop_value (props ,"start_t",_get_prop_value (props ,"inicio","0.0"))).strip ()

                sub_raw =self .get_input_value (node ,3 ,context )
                if sub_raw =="":sub_raw =str (_get_prop_value (props ,"subdivs",_get_prop_value (props ,"subdivisiones","30"))).strip ()

                mode_raw =str (_get_prop_value (props ,"mode",_get_prop_value (props ,"modo","global"))).strip ()
                inv_raw =str (_get_prop_value (props ,"invert",_get_prop_value (props ,"invertir","normal"))).strip ()

                from nodes .shape_nodes import shape_walker_node 
                cut_shp ,pos_str ,angle_deg ,cut_len ,tip_x ,tip_y =shape_walker_node (
                context ,
                shape =shp_raw ,
                progress =prog_raw ,
                start_t =start_raw ,
                mode =mode_raw ,
                invert =inv_raw ,
                subdivs =sub_raw 
                )

                if output_slot_index ==1 :
                    return pos_str 
                elif output_slot_index ==2 :
                    frz_val =f"{angle_deg :.2f}".rstrip ('0').rstrip ('.')
                    if not frz_val or frz_val =="-0"or frz_val .endswith ('.'):
                        frz_val ="0"
                    return f"\\frz{frz_val }"
                elif output_slot_index ==3 :
                    return str (cut_len )
                elif output_slot_index ==4 :
                    return str (tip_x )
                elif output_slot_index ==5 :
                    return str (tip_y )
                return cut_shp 
            except Exception as e :
                return f"[Err Walker: {e}]"




        elif node_type in ["Shape/Stroke", "Stroke"]:
            try :
                is_connected =self .is_port_connected (node ,0 )
                shp_raw =self .get_input_value (node ,0 ,context )
                if not is_connected and shp_raw =="":
                    shp_raw =str (_get_prop_value (props ,"shape","")).strip ()

                w_raw =self .get_input_value (node ,1 ,context )
                if w_raw =="":w_raw =str (_get_prop_value (props ,"width",_get_prop_value (props ,"grosor",_get_prop_value (props ,"ancho","4.0")))).strip ()

                cap_raw =self .get_input_value (node ,2 ,context )
                if cap_raw =="":cap_raw =str (_get_prop_value (props ,"cap_mode",_get_prop_value (props ,"cap","bezier"))).strip ()

                join_raw =str (_get_prop_value (props ,"join_mode",_get_prop_value (props ,"join","round"))).strip ()
                miter_raw =str (_get_prop_value (props ,"miter_limit","2.0")).strip ()

                if output_slot_index ==1 :
                    return str (w_raw )


                if is_connected and not shp_raw :
                    return ""

                from nodes .shape_nodes import shape_stroke_node 
                return shape_stroke_node (
                context ,
                shape =shp_raw ,
                width =w_raw ,
                cap_mode =cap_raw ,
                join_mode =join_raw ,
                miter_limit =miter_raw 
                )
            except Exception as e :
                return f"[Err Stroke: {e}]"




        elif node_type in ["Shape/Union & Divide", "Union & Divide"]:
            try :
                modo_raw =str (_get_prop_value (props ,"mode",_get_prop_value (props ,"modo","divide"))).strip ()
                bbox_mode_raw =str (_get_prop_value (props ,"bbox_mode","marco")).strip ()
                fill_type_raw =str (_get_prop_value (props ,"fill_type",_get_prop_value (props ,"fill_rule","evenodd"))).strip ()
                clean_raw =str (_get_prop_value (props ,"clean_self_intersect","1")).strip ()
                tags_raw =str (props .get ("tags","")).strip ()
                tagmode_raw =str (props .get ("tagmode","ipol")).strip ()
                order_raw =str (props .get ("order","79")).strip ()

                is_conn_0 =self .is_port_connected (node ,0 )
                shp_raw =self .get_input_value (node ,0 ,context )
                if not is_conn_0 and (shp_raw ==""or shp_raw is None ):
                    shp_raw =str (_get_prop_value (props ,"shape",_get_prop_value (props ,"shape_in",""))).strip ()
                if not shp_raw or str (shp_raw ).strip ()=="":
                    unit =context .get ('active_unit')if isinstance (context ,dict )else (context .get ('syl')if isinstance (context ,dict )else None )
                    line =context .get ('active_line')if isinstance (context ,dict )else (context .get ('line')if isinstance (context ,dict )else None )
                    if unit :
                        shp_raw =getattr (unit ,'text_stripped',getattr (unit ,'text',''))
                    elif line :
                        shp_raw =getattr (line ,'text_stripped',getattr (line ,'text',''))

                mode_clean =modo_raw .lower ()
                is_union ="unir"in mode_clean or "union"in mode_clean or "merge"in mode_clean 
                is_fusion ="fusi"in mode_clean or "fusion"in mode_clean 
                is_subpaths ="sub-ruta"in mode_clean or "subruta"in mode_clean or "subpath"in mode_clean or "naive"in mode_clean 

                anchor_raw ="piezas"
                if is_union :
                    is_conn_1 =self .is_port_connected (node ,1 )
                    shp_b_raw =self .get_input_value (node ,1 ,context )
                    if not is_conn_1 and shp_b_raw =="":
                        shp_b_raw =str (_get_prop_value (props ,"shape_b",_get_prop_value (props ,"shape_2",""))).strip ()
                    p2_val =self .get_input_value (node ,2 ,context )
                    if p2_val !="":fill_type_raw =str (p2_val ).strip ()
                    p3_val =self .get_input_value (node ,3 ,context )
                    if p3_val !="":clean_raw =str (p3_val ).strip ()
                    p4_val =self .get_input_value (node ,4 ,context )
                    if p4_val !="":anchor_raw =str (p4_val ).strip ()
                    else :anchor_raw =str (_get_prop_value (props ,"anchor","piezas")).strip ()
                elif is_fusion :
                    shp_b_raw =""
                    p1_val =self .get_input_value (node ,1 ,context )
                    if p1_val !="":tagmode_raw =str (p1_val ).strip ()
                    else :tagmode_raw =str (props .get ("tagmode","ipol")).strip ()
                    p2_val =self .get_input_value (node ,2 ,context )
                    if p2_val !="":tags_raw =str (p2_val ).strip ()
                    else :tags_raw =str (props .get ("tags","")).strip ()
                    p3_val =self .get_input_value (node ,3 ,context )
                    if p3_val !="":anchor_raw =str (p3_val ).strip ()
                    else :anchor_raw =str (props .get ("anchor","piezas")).strip ()
                    p4_val =self .get_input_value (node ,4 ,context )
                    if p4_val !="":order_raw =str (p4_val ).strip ()
                    else :order_raw =str (props .get ("order","79")).strip ()

                    if tagmode_raw .lower ()not in ("ipol","line","interpolado","lineal")and (any (c in tagmode_raw for c in ['\\','#','&',',','{'])or len (tagmode_raw )>10 ):
                        if not tags_raw :
                            tags_raw =tagmode_raw 
                            tagmode_raw =str (props .get ("tagmode","ipol")).strip ()
                elif is_subpaths :
                    shp_b_raw =""
                    p1_val =self .get_input_value (node ,1 ,context )
                    if p1_val !="":anchor_raw =str (p1_val ).strip ()
                    else :anchor_raw =str (_get_prop_value (props ,"anchor","piezas")).strip ()
                    p2_val =self .get_input_value (node ,2 ,context )
                    if p2_val !="":order_raw =str (p2_val ).strip ()
                    else :order_raw =str (_get_prop_value (props ,"order","79")).strip ()
                else :
                    shp_b_raw =""
                    p1_val =self .get_input_value (node ,1 ,context )
                    if p1_val !="":fill_type_raw =str (p1_val ).strip ()
                    p2_val =self .get_input_value (node ,2 ,context )
                    if p2_val !="":clean_raw =str (p2_val ).strip ()
                    p3_val =self .get_input_value (node ,3 ,context )
                    if p3_val !="":anchor_raw =str (p3_val ).strip ()
                    else :anchor_raw =str (_get_prop_value (props ,"anchor","piezas")).strip ()
                    p4_val =self .get_input_value (node ,4 ,context )
                    if p4_val !="":order_raw =str (p4_val ).strip ()
                    else :order_raw =str (_get_prop_value (props ,"order","79")).strip ()

                d_val =int (float (context .get ('d_i',context .get ('fx_i',1 ))))if isinstance (context ,dict )else 1 

                from nodes .shape_nodes import shape_union_divide_node ,get_drawing_bbox 
                from clipper_engine import ClipperEngine 

                memo_key =f"_sud_eval_{node_id }_{hash (str (shp_raw ))}_{hash (str (shp_b_raw ))}_{hash (str (tags_raw ))}_{hash (str (tagmode_raw ))}_{hash (str (order_raw ))}_{modo_raw }_{anchor_raw }_{fill_type_raw }_{clean_raw }"
                cached_res =context .get (memo_key )if isinstance (context ,dict )else None 

                if cached_res is None :
                    pieces =shape_union_divide_node (
                    context =context ,
                    drawing =shp_raw ,
                    shape_b =shp_b_raw ,
                    mode =modo_raw ,
                    anchor =anchor_raw ,
                    fill_type =fill_type_raw ,
                    clean_self_intersect =clean_raw ,
                    index_j =d_val ,
                    tags =tags_raw ,
                    tagmode =tagmode_raw ,
                    order =order_raw ,
                    return_all_pieces =True 
                    )
                    if isinstance (pieces ,list ):
                        all_pieces =pieces 
                    else :
                        all_pieces =[pieces ]if pieces else []

                    bbox_str =""
                    shapes_for_bbox =[]
                    if isinstance (shp_raw ,list ):
                        shapes_for_bbox .extend (shp_raw )
                    elif shp_raw :
                        shapes_for_bbox .append (shp_raw )

                    if is_union :
                        if isinstance (shp_b_raw ,list ):
                            shapes_for_bbox .extend (shp_b_raw )
                        elif shp_b_raw :
                            shapes_for_bbox .append (shp_b_raw )

                    if shapes_for_bbox :
                        g_bbox =get_drawing_bbox (shapes_for_bbox )
                        if g_bbox :
                            w =max (0.001 ,g_bbox [2 ]-g_bbox [0 ])
                            h =max (0.001 ,g_bbox [3 ]-g_bbox [1 ])
                            cx =g_bbox [0 ]+w *0.5 
                            cy =g_bbox [1 ]+h *0.5 
                            bbox_str =f"{g_bbox [0 ]},{g_bbox [1 ]},{g_bbox [2 ]},{g_bbox [3 ]},{cx },{cy },{w },{h }"

                    piece_offsets =[]
                    if not is_union and not is_fusion and shapes_for_bbox :
                        raw_islands =ClipperEngine .decompose_shape_islands (shp_raw ,fill_rule =fill_type_raw ,bbox_mode ="marco",clean_self_intersect =bool (clean_raw ))if not is_subpaths else ClipperEngine .decompose_shape_subpaths (shp_raw ,bbox_mode ="marco")
                        g_bx =get_drawing_bbox (shapes_for_bbox )
                        if g_bx :
                            g_mid_x =(g_bx [0 ]+g_bx [2 ])*0.5 
                            g_mid_y =(g_bx [1 ]+g_bx [3 ])*0.5 
                            for p_raw in raw_islands :
                                p_bx =get_drawing_bbox (p_raw )
                                if p_bx :
                                    p_mid_x =(p_bx [0 ]+p_bx [2 ])*0.5 
                                    p_mid_y =(p_bx [1 ]+p_bx [3 ])*0.5 
                                    piece_offsets .append ((p_mid_x -g_mid_x ,p_mid_y -g_mid_y ))
                                else :
                                    piece_offsets .append ((0.0 ,0.0 ))

                    cached_res =(all_pieces ,bbox_str ,piece_offsets )
                    if isinstance (context ,dict ):
                        context [memo_key ]=cached_res 

                all_pieces ,bbox_str ,piece_offsets =cached_res 
                total_count =len (all_pieces )

                if isinstance (context ,dict ):
                    context ['d_i']=d_val 
                    context ['d_n']=total_count 
                    context ['d_max']=total_count 
                    if not is_union and not is_fusion :
                        context ['maxloop']=total_count 

                if output_slot_index ==1 :
                    import json 
                    return json .dumps (all_pieces ,ensure_ascii =False )
                elif output_slot_index ==2 :
                    return bbox_str 
                else :
                    if not all_pieces :
                        return ""
                    if is_union or is_fusion :
                        return all_pieces [0 ]
                    target_idx =max (1 ,min (total_count ,d_val ))-1 

                    if isinstance (context ,dict )and not is_union and not is_fusion :
                        anchor_clean =str (anchor_raw ).strip ().lower ()
                        parent_x =float (context .get ('x',context .get ('fx_pos_x',640.0 )))
                        parent_y =float (context .get ('y',context .get ('fx_pos_y',360.0 )))
                        if target_idx <len (piece_offsets ):
                            off_x ,off_y =piece_offsets [target_idx ]
                            abs_x =parent_x +off_x 
                            abs_y =parent_y +off_y 
                        else :
                            abs_x ,abs_y =parent_x ,parent_y 

                        if anchor_clean == "pieces":
                            context ['x']=round (abs_x ,3 )
                            context ['y']=round (abs_y ,3 )
                            context ['fx_pos_x']=round (abs_x ,3 )
                            context ['fx_pos_y']=round (abs_y ,3 )
                            context ['pos_x']=round (abs_x ,3 )
                            context ['pos_y']=round (abs_y ,3 )
                            context ['pos_overridden']=True 
                            context ['has_org']=True 
                            context ['org_x']=round (abs_x ,3 )
                            context ['org_y']=round (abs_y ,3 )
                        elif anchor_clean == "org_padre":
                            context ['x']=round (abs_x ,3 )
                            context ['y']=round (abs_y ,3 )
                            context ['fx_pos_x']=round (abs_x ,3 )
                            context ['fx_pos_y']=round (abs_y ,3 )
                            context ['pos_x']=round (abs_x ,3 )
                            context ['pos_y']=round (abs_y ,3 )
                            context ['pos_overridden']=True 
                            context ['has_org']=True 
                            context ['org_x']=round (parent_x ,3 )
                            context ['org_y']=round (parent_y ,3 )
                        elif anchor_clean == "pos":
                            context ['x']=round (abs_x ,3 )
                            context ['y']=round (abs_y ,3 )
                            context ['fx_pos_x']=round (abs_x ,3 )
                            context ['fx_pos_y']=round (abs_y ,3 )
                            context ['pos_x']=round (abs_x ,3 )
                            context ['pos_y']=round (abs_y ,3 )
                            context ['pos_overridden']=True 
                            context ['has_org']=False 

                    return all_pieces [target_idx ]
            except Exception as e :
                import traceback 
                print(f"[Pyxis Node Error] Exception in 'Union & Divide': {e}")
                traceback .print_exc ()
                return f"[Err Union & Divide: {e}]"




        elif node_type in ["Shape/Array", "Array"]:
            try :

                memo_key =f"_sa_eval_{node_id }_{context .get ('a_i',1 )if isinstance (context ,dict )else 1 }"
                cached_res =context .get (memo_key )if isinstance (context ,dict )else None 

                if cached_res is None :
                    modo_raw = str(props.get("mode", props.get("modo", "grid"))).strip()
                    out_mode_raw = str(props.get("out_mode", "loops")).strip()
                    mode_norm = modo_raw.lower()

                    particle_raw = self.get_input_value(node, 0, context)
                    if particle_raw == "": particle_raw = str(props.get("particle", "")).strip()

                    formation_raw = str(props.get("formation", "")).strip()
                    cols_raw = str(props.get("cols", "5")).strip()
                    rows_raw = str(props.get("rows", "3")).strip()
                    sp_x_raw = str(props.get("spacing_x", "0")).strip()
                    sp_y_raw = str(props.get("spacing_y", "0")).strip()
                    sp_raw = str(props.get("spacing", "0")).strip()
                    rings_raw = str(props.get("rings", "3")).strip()
                    c_per_ring_raw = str(props.get("count_per_ring", "")).strip()
                    rad_raw = str(props.get("radius", "50")).strip()
                    dr_raw = str(props.get("radius_step", "30")).strip()
                    rot_step_raw = str(props.get("rotate_step", "0")).strip()
                    count_raw = str(props.get("count", "20")).strip()
                    turns_raw = str(props.get("turns", "2.0")).strip()
                    max_rad_raw = str(props.get("max_radius", "100")).strip()
                    a_step_raw = str(props.get("angle_step", "0")).strip()
                    w_area_raw = str(props.get("area_width", "150")).strip()
                    h_area_raw = str(props.get("area_height", "100")).strip()
                    seed_raw = str(props.get("seed", "1")).strip()
                    sc_raw = str(props.get("scale", "1.0")).strip()
                    anchor_raw = str(props.get("anchor", "pieces")).strip()
                    order_raw = str(props.get("order", "79")).strip()
                    w_target_raw = str(props.get("width", "0")).strip()
                    h_target_raw = str(props.get("height", "0")).strip()

                    t_raw =str (props .get ("t",props .get ("progress",props .get ("factor_t","1.0")))).strip ()
                    num_inputs =len (node .get ("inputs",[]))

                    if "form"in mode_norm :
                        in_f =self .get_input_value (node ,1 ,context )
                        if in_f !="":formation_raw =in_f 
                        in_sp =self .get_input_value (node ,2 ,context )
                        if in_sp !="":sp_raw =in_sp 
                        in_sc =self .get_input_value (node ,3 ,context )
                        if in_sc !="":sc_raw =in_sc 
                        if num_inputs >=7 :
                            in_t =self .get_input_value (node ,4 ,context )
                            if in_t !="":t_raw =in_t 
                            in_anc =self .get_input_value (node ,5 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,6 ,context )
                            if in_ord !="":order_raw =in_ord 
                        else :
                            in_anc =self .get_input_value (node ,4 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,5 ,context )
                            if in_ord !="":order_raw =in_ord 
                    elif "ring"in mode_norm or "anillo"in mode_norm :
                        in_rng =self .get_input_value (node ,1 ,context )
                        if in_rng !="":rings_raw =in_rng 
                        in_cr =self .get_input_value (node ,2 ,context )
                        if in_cr !="":c_per_ring_raw =in_cr 
                        in_rad =self .get_input_value (node ,3 ,context )
                        if in_rad !="":rad_raw =in_rad 
                        in_dr =self .get_input_value (node ,4 ,context )
                        if in_dr !="":dr_raw =in_dr 
                        in_rot =self .get_input_value (node ,5 ,context )
                        if in_rot !="":rot_step_raw =in_rot 
                        in_sc =self .get_input_value (node ,6 ,context )
                        if in_sc !="":sc_raw =in_sc 
                        if num_inputs >=10 :
                            in_t =self .get_input_value (node ,7 ,context )
                            if in_t !="":t_raw =in_t 
                            in_anc =self .get_input_value (node ,8 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,9 ,context )
                            if in_ord !="":order_raw =in_ord 
                        else :
                            in_anc =self .get_input_value (node ,7 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,8 ,context )
                            if in_ord !="":order_raw =in_ord 
                    elif "spiral"in mode_norm or "espiral"in mode_norm :
                        in_cnt =self .get_input_value (node ,1 ,context )
                        if in_cnt !="":count_raw =in_cnt 
                        in_tr =self .get_input_value (node ,2 ,context )
                        if in_tr !="":turns_raw =in_tr 
                        in_mr =self .get_input_value (node ,3 ,context )
                        if in_mr !="":max_rad_raw =in_mr 
                        in_as =self .get_input_value (node ,4 ,context )
                        if in_as !="":a_step_raw =in_as 
                        in_sc =self .get_input_value (node ,5 ,context )
                        if in_sc !="":sc_raw =in_sc 
                        if num_inputs >=9 :
                            in_t =self .get_input_value (node ,6 ,context )
                            if in_t !="":t_raw =in_t 
                            in_anc =self .get_input_value (node ,7 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,8 ,context )
                            if in_ord !="":order_raw =in_ord 
                        else :
                            in_anc =self .get_input_value (node ,6 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,7 ,context )
                            if in_ord !="":order_raw =in_ord 
                    elif "scatter"in mode_norm or "dispers"in mode_norm :
                        in_cnt =self .get_input_value (node ,1 ,context )
                        if in_cnt !="":count_raw =in_cnt 
                        in_w =self .get_input_value (node ,2 ,context )
                        if in_w !="":w_area_raw =in_w 
                        in_h =self .get_input_value (node ,3 ,context )
                        if in_h !="":h_area_raw =in_h 
                        in_sd =self .get_input_value (node ,4 ,context )
                        if in_sd !="":seed_raw =in_sd 
                        in_sc =self .get_input_value (node ,5 ,context )
                        if in_sc !="":sc_raw =in_sc 
                        if num_inputs >=9 :
                            in_t =self .get_input_value (node ,6 ,context )
                            if in_t !="":t_raw =in_t 
                            in_anc =self .get_input_value (node ,7 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,8 ,context )
                            if in_ord !="":order_raw =in_ord 
                        else :
                            in_anc =self .get_input_value (node ,6 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,7 ,context )
                            if in_ord !="":order_raw =in_ord 
                    elif "hex"in mode_norm or "panal"in mode_norm :
                        in_c =self .get_input_value (node ,1 ,context )
                        if in_c !="":cols_raw =in_c 
                        in_r =self .get_input_value (node ,2 ,context )
                        if in_r !="":rows_raw =in_r 
                        in_sp =self .get_input_value (node ,3 ,context )
                        if in_sp !="":sp_raw =in_sp 
                        in_sc =self .get_input_value (node ,4 ,context )
                        if in_sc !="":sc_raw =in_sc 
                        if num_inputs >=8 :
                            in_t =self .get_input_value (node ,5 ,context )
                            if in_t !="":t_raw =in_t 
                            in_anc =self .get_input_value (node ,6 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,7 ,context )
                            if in_ord !="":order_raw =in_ord 
                        else :
                            in_anc =self .get_input_value (node ,5 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,6 ,context )
                            if in_ord !="":order_raw =in_ord 
                    else :
                        in_c =self .get_input_value (node ,1 ,context )
                        if in_c !="":cols_raw =in_c 
                        in_r =self .get_input_value (node ,2 ,context )
                        if in_r !="":rows_raw =in_r 
                        in_sx =self .get_input_value (node ,3 ,context )
                        if in_sx !="":sp_x_raw =in_sx 
                        in_sy =self .get_input_value (node ,4 ,context )
                        if in_sy !="":sp_y_raw =in_sy 
                        in_sc =self .get_input_value (node ,5 ,context )
                        if in_sc !="":sc_raw =in_sc 
                        if num_inputs >=9 :
                            in_t =self .get_input_value (node ,6 ,context )
                            if in_t !="":t_raw =in_t 
                            in_anc =self .get_input_value (node ,7 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,8 ,context )
                            if in_ord !="":order_raw =in_ord 
                        else :
                            in_anc =self .get_input_value (node ,6 ,context )
                            if in_anc !="":anchor_raw =in_anc 
                            in_ord =self .get_input_value (node ,7 ,context )
                            if in_ord !="":order_raw =in_ord 

                    t_val =_eval_num_expr (t_raw ,context ,default =1.0 )

                    tags_raw =None 
                    for idx ,inp in enumerate (node .get ("inputs",[])):
                        if str (inp .get ("name","")).strip ().lower ()in ["tags","tag","etiquetas"]:
                            tags_raw =self .get_input_value (node ,idx ,context )
                            break 
                    if tags_raw is None or str (tags_raw ).strip ()=="":
                        tags_raw =str (_get_prop_value (props ,"tags",_get_prop_value (props ,"tag",""))).strip ()

                    from nodes .shape_nodes import shape_array_node 
                    cached_res =shape_array_node (
                    context =context ,
                    particle =particle_raw ,
                    formation =formation_raw ,
                    width =w_target_raw ,
                    height =h_target_raw ,
                    scale =sc_raw ,
                    t =t_val ,
                    anchor =anchor_raw ,
                    order =order_raw ,
                    mode =modo_raw ,
                    out_mode =out_mode_raw ,
                    cols =cols_raw ,
                    rows =rows_raw ,
                    spacing_x =sp_x_raw ,
                    spacing_y =sp_y_raw ,
                    spacing =sp_raw ,
                    rings =rings_raw ,
                    count_per_ring =c_per_ring_raw ,
                    radius =rad_raw ,
                    radius_step =dr_raw ,
                    rotate_step =rot_step_raw ,
                    count =count_raw ,
                    turns =turns_raw ,
                    max_radius =max_rad_raw ,
                    angle_step =a_step_raw ,
                    area_width =w_area_raw ,
                    area_height =h_area_raw ,
                    seed =seed_raw ,
                    tags =tags_raw 
                    )
                    if isinstance (context ,dict ):
                        context [memo_key ]=cached_res 

                res_shp ,res_pos ,res_x ,res_y ,res_ang ,res_ai ,res_an ,res_col ,res_row =cached_res 

                if output_slot_index ==1 :
                    return res_pos 
                elif output_slot_index ==2 :
                    return str (res_x )
                elif output_slot_index ==3 :
                    return str (res_y )
                elif output_slot_index ==4 :
                    frz_val =f"{res_ang :.2f}".rstrip ('0').rstrip ('.')
                    if not frz_val or frz_val =="-0"or frz_val .endswith ('.'):
                        frz_val ="0"
                    return f"\\frz{frz_val }"
                elif output_slot_index ==5 :
                    return str (res_ai )
                elif output_slot_index ==6 :
                    return str (res_an )
                elif output_slot_index ==7 :
                    return str (res_col )
                elif output_slot_index ==8 :
                    return str (res_row )
                return res_shp 
            except Exception as e :
                import traceback 
                traceback .print_exc ()
                return f"[Err Array: {e}]"




        elif node_type in ["Functions/Text on Path","Text on Path","Text/Text on Path"]:
            try :
                shp_raw =self .get_input_value (node ,0 ,context )
                if shp_raw =="":shp_raw =str (_get_prop_value (props ,"shape","")).strip ()

                offset_raw =self .get_input_value (node ,1 ,context )
                if offset_raw =="":offset_raw =str (_get_prop_value (props ,"offset",_get_prop_value (props ,"desfase","0"))).strip ()

                extra_ang_raw =self .get_input_value (node ,2 ,context )
                if extra_ang_raw =="":extra_ang_raw =str (_get_prop_value (props ,"extra_angle",_get_prop_value (props ,"angulo_extra","0"))).strip ()

                sub_raw =self .get_input_value (node ,3 ,context )
                if sub_raw =="":sub_raw =str (_get_prop_value (props ,"subdivs",_get_prop_value (props ,"subdivisiones","30"))).strip ()

                mode_raw =str (_get_prop_value (props ,"mode","Center")).strip ()

                from nodes .text_nodes import text_on_path_node 
                tag_out ,pos_str ,frz_str ,x_val ,y_val ,total_len =text_on_path_node (
                context ,
                shape =shp_raw ,
                mode =mode_raw ,
                offset =offset_raw ,
                extra_angle =extra_ang_raw ,
                subdivs =sub_raw 
                )

                if output_slot_index ==1 :
                    return pos_str 
                elif output_slot_index ==2 :
                    return frz_str 
                elif output_slot_index ==3 :
                    return str (x_val )
                elif output_slot_index ==4 :
                    return str (y_val )
                elif output_slot_index ==5 :
                    return str (total_len )
                return tag_out 
            except Exception as e :
                return f"[Err Text on Path: {e }]"




        elif node_type in ["Functions/Clip Gradient","Shape/Clip Gradient","Clip Gradient"]:
            try :
                num_clips_raw =self .get_input_value (node ,0 ,context )
                if num_clips_raw =="":num_clips_raw =str (_get_prop_value (props ,"num_clips",_get_prop_value (props ,"franjas","5"))).strip ()

                angle_raw =self .get_input_value (node ,1 ,context )
                if angle_raw =="":angle_raw =str (_get_prop_value (props ,"angle",_get_prop_value (props ,"angulo","0"))).strip ()

                pad_raw =self .get_input_value (node ,2 ,context )
                if pad_raw =="":pad_raw =str (_get_prop_value (props ,"padding","4")).strip ()

                ov_raw =self .get_input_value (node ,3 ,context )
                if ov_raw =="":ov_raw =str (_get_prop_value (props ,"overlap",_get_prop_value (props ,"solape","0.5"))).strip ()

                order_raw =self .get_input_value (node ,4 ,context )
                if order_raw =="":order_raw =str (_get_prop_value (props ,"order",_get_prop_value (props ,"orden","normal"))).strip ()

                out_mode_raw =str (_get_prop_value (props ,"out_mode",_get_prop_value (props ,"salida","clip"))).strip ()

                from nodes .shape_nodes import clip_gradient_node 
                clip_tag ,progress_val ,idx_clip ,total_clips =clip_gradient_node (
                context ,
                num_clips =num_clips_raw ,
                angle =angle_raw ,
                padding =pad_raw ,
                overlap =ov_raw ,
                order =order_raw ,
                out_mode =out_mode_raw 
                )

                if output_slot_index ==1 :
                    return str (progress_val )
                elif output_slot_index ==2 :
                    return str (idx_clip )
                elif output_slot_index ==3 :
                    return str (total_clips )
                return clip_tag 
            except Exception as e :
                return f"[Err Clip Gradient: {e }]"




        elif node_type in ["Audio/Modulator", "Modulator"]:
            try :
                inputs_list =node .get ("inputs",[])
                def get_val (port_name_or_aliases ,default_val =""):
                    if isinstance (port_name_or_aliases ,str ):
                        aliases =[port_name_or_aliases ]
                    else :
                        aliases =list (port_name_or_aliases )
                    for alias in aliases :
                        clean_alias =_clean_key (alias )
                        for i ,inp_obj in enumerate (inputs_list ):
                            inp_name =inp_obj .get ("name","")
                            if _clean_key (inp_name )==clean_alias :
                                val =self .get_input_value (node ,i ,context )
                                if val !="":return val 
                                if "value"in inp_obj and inp_obj ["value"]is not None and str (inp_obj ["value"]).strip ()!="":
                                    return str (inp_obj ["value"])
                    for alias in aliases :
                        clean_alias =_clean_key (alias )
                        prop_val =_get_prop_value (props ,clean_alias ,"")
                        if prop_val !="":
                            return str (prop_val )
                    return str (default_val )

                audio_path_raw =get_val (["Audio Path","audio_path"],"")
                tag_raw =get_val (["Tag","tag_name"],"fscy")
                min_raw =get_val (["Min Val","min_val"],"100")
                max_raw =get_val (["Max Val","max_val"],"160")
                gain_raw =get_val (["Gain","gain"],"1.0")
                step_raw =get_val (["Step ms","step_ms"],"41.7")
                smooth_raw =get_val (["Smoothing","smoothing"],"0.2")
                min_hz_raw =get_val (["Min Hz","min_hz"],"20")
                max_hz_raw =get_val (["Max Hz","max_hz"],"250")
                start_time_raw =get_val (["Start Time","start_time"],"")
                end_time_raw =get_val (["End Time","end_time"],"")
                modo_raw =str (_get_prop_value (props ,"mode","rms")).strip ().lower ()

                from nodes .audio_nodes import audio_modulator_master 
                res =audio_modulator_master (
                context =context ,
                audio_path =audio_path_raw ,
                tag_name =tag_raw ,
                min_val =min_raw ,
                max_val =max_raw ,
                gain =gain_raw ,
                step_ms =step_raw ,
                smoothing =smooth_raw ,
                mode =modo_raw ,
                min_hz =min_hz_raw ,
                max_hz =max_hz_raw ,
                start_time =start_time_raw ,
                end_time =end_time_raw ,
                output_slot_index =output_slot_index 
                )
                if output_slot_index ==2 and isinstance (res ,list ):
                    return res 
                return str (res )
            except Exception as e :
                return f"[Err Modulator: {e}]"




        elif node_type in ["Audio/Waveform", "Waveform"]:
            try :
                inputs_list =node .get ("inputs",[])
                def get_val (port_name_or_aliases ,default_val =""):
                    if isinstance (port_name_or_aliases ,str ):
                        aliases =[port_name_or_aliases ]
                    else :
                        aliases =list (port_name_or_aliases )
                    for alias in aliases :
                        clean_alias =_clean_key (alias )
                        for i ,inp_obj in enumerate (inputs_list ):
                            inp_name =inp_obj .get ("name","")
                            if _clean_key (inp_name )==clean_alias :
                                val =self .get_input_value (node ,i ,context )
                                if val !="":return val 
                                if "value"in inp_obj and inp_obj ["value"]is not None and str (inp_obj ["value"]).strip ()!="":
                                    return str (inp_obj ["value"])
                    for alias in aliases :
                        clean_alias =_clean_key (alias )
                        prop_val =_get_prop_value (props ,clean_alias ,"")
                        if prop_val !="":
                            return str (prop_val )
                    return str (default_val )

                audio_path_raw =get_val (["Audio Path","audio_path"],"")
                ancho_raw =get_val (["Width","width"],"400")
                alto_raw =get_val (["Height","height"],"60")
                muestras_raw =get_val (["Samples","samples"],"32")
                gain_raw =get_val (["Gain","gain"],"1.0")
                grosor_raw =get_val (["Thickness","thickness"],"2")
                escala_raw =get_val (["Scale","scale"],"1.0")
                min_hz_raw =get_val (["Min Hz","min_hz","f_min"],"20")
                max_hz_raw =get_val (["Max Hz","max_hz","f_max"],"16000")
                start_time_raw =get_val (["Start Time","start_time","st"],"")
                end_time_raw =get_val (["End Time","end_time","et"],"")
                modo_raw =str (_get_prop_value (props ,"mode",_get_prop_value (props ,"modo","oscilloscope"))).strip ().lower ()

                from nodes .audio_nodes import audio_waveform_master 
                res =audio_waveform_master (
                context =context ,
                audio_path =audio_path_raw ,
                mode =modo_raw ,
                width =ancho_raw ,
                height =alto_raw ,
                samples =muestras_raw ,
                gain =gain_raw ,
                thickness =grosor_raw ,
                min_hz =min_hz_raw ,
                max_hz =max_hz_raw ,
                scale =escala_raw ,
                start_time =start_time_raw ,
                end_time =end_time_raw ,
                output_slot_index =output_slot_index 
                )
                if output_slot_index in (2 ,3 ,4 )and isinstance (res ,list ):
                    return res 
                return str (res )
            except Exception as e :
                return f"[Err Waveform: {e}]"




        elif node_type in ["Functions/Tag Oscillator","Tag Oscillator"]:
            try :
                inputs_list =node .get ("inputs",[])

                def get_val_by_name_or_prop (port_name ,prop_key ,default_val =""):
                    clean_target =_clean_key (port_name )
                    clean_prop =_clean_key (prop_key )


                    for i ,inp_obj in enumerate (inputs_list ):
                        inp_name =inp_obj .get ("name","")
                        inp_prop =inp_obj .get ("property","")

                        if _clean_key (inp_name )==clean_target or _clean_key (inp_prop )==clean_prop or clean_prop ==_clean_key (inp_name ):
                            val =self .get_input_value (node ,i ,context )
                            if val is not None and str (val ).strip ()!="":
                                return val 
                            if "value"in inp_obj and inp_obj ["value"]is not None and str (inp_obj ["value"]).strip ()!="":
                                return str (inp_obj ["value"])


                    prop_val =_get_prop_value (props ,prop_key ,"")
                    if prop_val is not None and str (prop_val ).strip ()!="":
                        return str (prop_val )

                    return default_val 

                st_val =get_val_by_name_or_prop ("Start Time","start_time","")
                et_val =get_val_by_name_or_prop ("End Time","end_time","")
                step_val =get_val_by_name_or_prop ("Step (ms)","step_ms","200.0")
                trans_val =get_val_by_name_or_prop ("Trans (ms)","trans_ms","50.0")
                dc_val =get_val_by_name_or_prop ("Duty Cycle","duty_cycle","")
                tags_val =get_val_by_name_or_prop ("Tags","tags",r"\fscx140\fscy140,\fscx100\fscy100")
                accel_val =get_val_by_name_or_prop ("Accel","accel","1.0")
                dilat_step_val =get_val_by_name_or_prop ("Dilate Step","dilat_step_ms","0.0")
                dilat_trans_val =get_val_by_name_or_prop ("Dilate Trans","dilat_trans_ms","0.0")
                offset_seq_val =get_val_by_name_or_prop ("Seq Offset","offset_seq_ms","0.0")
                rhythm_val =get_val_by_name_or_prop ("Rhythm Pattern","rhythm_pattern","")

                mode_osc =str (_get_prop_value (props ,"mode","wave")).strip ()
                mode_ord =str (_get_prop_value (props ,"order_mode","sequential")).strip ()

                from nodes .tag_nodes import tag_oscillator_node 
                res =tag_oscillator_node (
                context =context ,
                start_time =st_val ,
                end_time =et_val ,
                step_ms =step_val ,
                trans_ms =trans_val ,
                duty_cycle =dc_val ,
                tags =tags_val ,
                accel =accel_val ,
                dilat_step_ms =dilat_step_val ,
                dilat_trans_ms =dilat_trans_val ,
                offset_seq_ms =offset_seq_val ,
                rhythm_pattern =rhythm_val ,
                modo_oscilacion =mode_osc ,
                mode =mode_osc ,
                modo_orden =mode_ord ,
                order_mode =mode_ord ,
                output_slot_index =output_slot_index 
                )
                if output_slot_index in (2 ,3 )and isinstance (res ,list ):
                    return res 
                return str (res )
            except Exception as e :
                import traceback 
                print (f"[Err Tag Oscillator]: {e }")
                traceback .print_exc ()
                return f"[Err Tag Oscillator: {e }]"




        elif node_type in ["Functions/Glitter","Glitter"]:
            try :
                inputs_list =node .get ("inputs",[])

                st_val =_get_prop_value (props ,"start_time","0")
                et_val =_get_prop_value (props ,"end_time","fx.dur")
                density_val =_get_prop_value (props ,"density","1.0")
                seed_val =_get_prop_value (props ,"seed","0")
                mode_osc =str (_get_prop_value (props ,"mode","flashes")).strip ()

                props_clean =dict (props )
                props_clean .pop ("start_time",None )
                props_clean .pop ("end_time",None )
                props_clean .pop ("density",None )
                props_clean .pop ("densidad",None )
                props_clean .pop ("modo_oscilacion",None )
                props_clean .pop ("seed",None )

                has_named_special =any (k in (inp .get ("name")or "").lower ()for inp in inputs_list for k in ("start","end","dens"))
                num_special =sum (1 for inp in inputs_list if any (k in (inp .get ("name")or "").lower ()for k in ("start","end","dens")))

                for i ,inp_obj in enumerate (inputs_list ):
                    inp_name =(inp_obj .get ("name")or "").lower ()
                    if "start"in inp_name :
                        st_in =self .get_input_value (node ,i ,context )
                        if st_in is not None and str (st_in ).strip ()!="":st_val =st_in 
                    elif "end"in inp_name :
                        et_in =self .get_input_value (node ,i ,context )
                        if et_in is not None and str (et_in ).strip ()!="":et_val =et_in 
                    elif "dens"in inp_name :
                        d_in =self .get_input_value (node ,i ,context )
                        if d_in is not None and str (d_in ).strip ()!="":density_val =d_in 
                    else :
                        row_idx =(i -num_special )if has_named_special and i >=num_special else i 
                        row_val =self .get_input_value (node ,i ,context )
                        if row_val is not None and str (row_val ).strip ()!="":
                            row_s =str (row_val ).strip ()
                            if row_s .startswith ("\\"):
                                m_tag =re .match (r"^(\\[a-zA-Z0-9_]+)(.*)$",row_s )
                                if m_tag :
                                    t_part =m_tag .group (1 )
                                    v_part =m_tag .group (2 ).strip ()
                                    props_clean [f"tag_{row_idx }"]=t_part 
                                    if v_part and (f"min_{row_idx }"not in props_clean or not props_clean [f"min_{row_idx }"]):
                                        props_clean [f"min_{row_idx }"]=v_part 
                                else :
                                    props_clean [f"tag_{row_idx }"]=row_s 
                            elif ","in row_s :
                                parts =row_s .split (",")
                                props_clean [f"min_{row_idx }"]=parts [0 ].strip ()
                                if len (parts )>1 :
                                    props_clean [f"max_{row_idx }"]=parts [1 ].strip ()
                            else :
                                props_clean [f"min_{row_idx }"]=row_s 


                unit =context .get ("active_unit")if isinstance (context ,dict )else None 
                unit_i =getattr (unit ,"i",context .get ("fx_i",context .get ("j",context .get ("i",0 ))))if isinstance (context ,dict )else 0 
                memo_key =f"_glitter_{node .get ('id',0 )}_{unit_i }_{st_val }_{et_val }_{density_val }_{mode_osc }_{seed_val }"
                cached_data =context .get (memo_key )if isinstance (context ,dict )else None 

                if cached_data is None :
                    from nodes .tag_nodes import glitter_node 
                    cached_data =glitter_node (
                    context =context ,
                    start_time =st_val ,
                    end_time =et_val ,
                    density =density_val ,
                    modo_oscilacion =mode_osc ,
                    seed =seed_val ,
                    output_slot_index =-1 ,
                    **props_clean 
                    )
                    if isinstance (context ,dict ):
                        context [memo_key ]=cached_data 

                if isinstance (cached_data ,tuple ):
                    comb_res ,rows_res =cached_data 
                    try :
                        slot_idx =int (output_slot_index )if output_slot_index is not None else 0 
                    except Exception :
                        slot_idx =0 
                    if slot_idx ==0 :
                        return comb_res 
                    else :
                        target_r =slot_idx -1 
                        if 0 <=target_r <len (rows_res ):
                            return rows_res [target_r ]
                        return ""
                return str (cached_data )if cached_data is not None else ""
            except Exception as e :
                import traceback 
                print (f"[Err Glitter]: {e }")
                traceback .print_exc ()
                return f"[Err Glitter: {e }]"




        elif node_type in ["Functions/Once","Once","Basics/Once"]or name =="Once":
            try :
                modo =str (_get_prop_value (props ,"mode","line")).strip ().lower ()
                iter_var =str (_get_prop_value (props ,"iterator","j")).strip ()or "j"


                l =context .get ('line')if isinstance (context ,dict )else None 
                l_id =getattr (l ,'i',getattr (l ,'idx',id (l )if l else 0 ))

                if modo =="global":
                    scope_key ="global"
                elif modo =="line":
                    scope_key =f"line_{l_id }"
                elif modo =="word":
                    w =context .get ('word')if isinstance (context ,dict )else None 
                    w_id =getattr (w ,'i',getattr (w ,'idx',id (w )if w else 0 ))
                    scope_key =f"line_{l_id }_word_{w_id }"
                elif modo =="syl":
                    s =context .get ('syl')if isinstance (context ,dict )else None 
                    s_id =getattr (s ,'i',getattr (s ,'idx',id (s )if s else 0 ))
                    scope_key =f"line_{l_id }_syl_{s_id }"
                elif modo =="char":
                    c =context .get ('char')if isinstance (context ,dict )else None 
                    c_id =getattr (c ,'i',getattr (c ,'idx',id (c )if c else 0 ))
                    scope_key =f"line_{l_id }_char_{c_id }"
                elif modo in ("loop","bucle"):
                    iter_val =context .get (iter_var ,0 )if isinstance (context ,dict )else 0 
                    scope_key =f"line_{l_id }_bucle_{iter_var }_{iter_val }"
                else :
                    scope_key =f"line_{l_id }"

                cache_key =f"_once_{node .get ('id',0 )}_{scope_key }"
                if not hasattr (self ,"_once_cache")or self ._once_cache is None :
                    self ._once_cache ={}

                if cache_key in self ._once_cache :
                    return self ._once_cache [cache_key ]

                val =self .get_input_value (node ,0 ,context )
                self ._once_cache [cache_key ]=val 
                return val 
            except Exception as e :
                import traceback 
                print (f"[Err Once]: {e }")
                traceback .print_exc ()
                return f"[Err Once: {e }]"




        elif node_type in ["Functions/Only","Only","Basics/Only"]or name =="Only":
            try :
                cond_raw =_get_prop_value (props ,"condition","True")
                modo =str (_get_prop_value (props ,"mode","select")).lower ().strip ()
                try :
                    from nodes .tag_nodes import eval_condition_bool 
                except (ImportError ,ModuleNotFoundError ):
                    import importlib .util 
                    _tn_path =os .path .join (os .path .dirname (os .path .abspath (__file__ )),"nodes","tag_nodes.py")
                    if os .path .exists (_tn_path ):
                        _spec =importlib .util .spec_from_file_location ("_tag_nodes_engine",_tn_path )
                        _mod =importlib .util .module_from_spec (_spec )
                        _spec .loader .exec_module (_mod )
                        eval_condition_bool =_mod .eval_condition_bool 
                    else :
                        eval_condition_bool =lambda c ,ctx =None :bool (c )
                is_true =eval_condition_bool (cond_raw ,context )

                inputs_len =len (node .get ("inputs",[]))if isinstance (node .get ("inputs"),list )else 1 
                outputs_len =len (node .get ("outputs",[]))if isinstance (node .get ("outputs"),list )else 1 
                is_selector =(modo in ["select","selector","ternario","ternary"])or (inputs_len >=2 and outputs_len <=1 )

                if is_selector :

                    if is_true :
                        return self .get_input_value (node ,0 ,context )
                    else :
                        return self .get_input_value (node ,1 ,context )
                else :

                    slot_idx =0 if output_slot_index is None else output_slot_index 
                    if slot_idx ==0 :
                        return self .get_input_value (node ,0 ,context )if is_true else ""
                    elif slot_idx ==1 :
                        return self .get_input_value (node ,0 ,context )if not is_true else ""
                    return self .get_input_value (node ,0 ,context )if is_true else ""
            except Exception as e :
                import traceback 
                print (f"[Err Only]: {e }")
                traceback .print_exc ()
                return ""




        elif node_type in ["System/Benchmark Math","Benchmark Math"]:
            try :
                inputs = node.get('inputs', [])
                val_in = ""
                iter_raw = ""
                if inputs and len(inputs) == 1:
                    iter_raw = self.get_input_value(node, 0, context)
                else:
                    val_in = self.get_input_value(node, 0, context)
                    iter_raw = self.get_input_value(node, 1, context)

                if val_in == "": val_in = str(_get_prop_value(props, "val_in", _get_prop_value(props, "value", "")))
                if iter_raw == "": iter_raw = _get_prop_value(props, "iterations", "10000")
                iterations = max(1, int(_eval_num_expr(iter_raw, context, 10000.0)))

                complexity = str(_get_prop_value(props, "complexity", "Heavy Math (Trig + Sqrt)"))

                import math ,time 
                t0 =time .perf_counter ()
                acc =1.0 

                if "Prime"in complexity :
                    count =0 
                    for n in range (2 ,iterations +500 ):
                        is_prime =True 
                        for i in range (2 ,int (math .isqrt (n ))+1 ):
                            if n %i ==0 :
                                is_prime =False 
                                break 
                        if is_prime :count +=1 
                    acc =count 
                elif "Matrix"in complexity :
                    dim =25 
                    A =[[(i +j *0.1 )for j in range (dim )]for i in range (dim )]
                    B =[[(i *0.2 -j )for j in range (dim )]for i in range (dim )]
                    for _ in range (max (1 ,iterations //200 )):
                        C =[[sum (A [i ][k ]*B [k ][j ]for k in range (dim ))for j in range (dim )]for i in range (dim )]
                        acc +=C [0 ][0 ]
                else :
                    for i in range (1 ,iterations +1 ):
                        acc +=math .sin (i )*math .cos (i )+math .sqrt (i )

                elapsed_ms =(time .perf_counter ()-t0 )*1000.0 

                if output_slot_index ==1 :return f"{elapsed_ms :.2f}"
                return str (val_in )if val_in !=""else f"[Bench: {elapsed_ms :.2f}ms]"
            except Exception as e :
                return f"[Err Bench: {e }]"




        elif node_type in ["Functions/Particles","Particles"]:
            try :
                shp =self .get_input_value (node ,0 ,context )
                if shp =="":shp =str (_get_prop_value (props ,"shape","")).strip ()

                p_shp =self .get_input_value (node ,1 ,context )
                if p_shp =="":p_shp =str (_get_prop_value (props ,"particle_shape","")).strip ()

                density =self .get_input_value (node ,2 ,context )
                if density =="":density =str (_get_prop_value (props ,"density","5.0")).strip ()

                redraw =self .get_input_value (node ,3 ,context )
                if redraw =="":redraw =str (_get_prop_value (props ,"redraw_dist","0")).strip ()

                seed =self .get_input_value (node ,4 ,context )
                if seed =="":seed =str (_get_prop_value (props ,"seed","1")).strip ()

                scale =self .get_input_value (node ,5 ,context )
                if scale =="":scale =str (_get_prop_value (props ,"scale","1.0")).strip ()

                order =self .get_input_value (node ,6 ,context )
                if order =="":order =str (_get_prop_value (props ,"order","79")).strip ()

                modo = str(_get_prop_value(props, "mode", "outline_v2")).strip()

                from particle_nodes import particle_text_node 
                abs_x ,abs_y ,particle_ass_shape ,total_pts =particle_text_node (
                context ,shape =shp ,particle_shape =p_shp ,density =density ,redraw_dist =redraw ,seed =seed ,scale =scale ,mode =modo ,order =order 
                )

                if output_slot_index ==1 :return f"\\pos({abs_x },{abs_y })"
                elif output_slot_index ==2 :return str (abs_x )
                elif output_slot_index ==3 :return str (abs_y )
                elif output_slot_index ==4 :return str (total_pts )

                return f"{{\\pos({abs_x },{abs_y })}}{particle_ass_shape }"
            except Exception as e :
                return f"[Err Particles: {e }]"




        elif node_type in ["Functions/IMG to pixels", "Functions/IMG to Pixels", "IMG to pixels", "IMG to Pixels"]:
            try :
                img_path =self .get_input_value (node ,0 ,context )
                if img_path =="":img_path =str (_get_prop_value (props ,"image_path","")).strip ()

                p_shp =self .get_input_value (node ,1 ,context )
                if p_shp =="":p_shp =str (_get_prop_value (props ,"particle_shape","")).strip ()

                frame =self .get_input_value (node ,2 ,context )
                if frame =="":frame =str (_get_prop_value (props ,"frame_idx","j")).strip ()

                step =self .get_input_value (node ,3 ,context )
                if step =="":step =str (_get_prop_value (props ,"step","2")).strip ()

                alpha_th =self .get_input_value (node ,4 ,context )
                if alpha_th =="":alpha_th =str (_get_prop_value (props ,"alpha_threshold","128")).strip ()

                scale =self .get_input_value (node ,5 ,context )
                if scale =="":scale =str (_get_prop_value (props ,"scale","1.0")).strip ()

                anchor =self .get_input_value (node ,6 ,context )
                if anchor =="":anchor =str (_get_prop_value (props ,"anchor","center")).strip ()

                order =self .get_input_value (node ,7 ,context )
                if order =="":order =str (_get_prop_value (props ,"order","79")).strip ()

                from particle_nodes import particle_image_node 
                abs_x ,abs_y ,col_ass ,alpha_ass ,p_shape ,total_px =particle_image_node (
                context ,image_path =img_path ,particle_shape =p_shp ,frame =frame ,step =step ,alpha_threshold =alpha_th ,scale =scale ,anchor =anchor ,order =order 
                )

                if output_slot_index ==1 :return col_ass 
                elif output_slot_index ==2 :return f"\\pos({abs_x },{abs_y })"
                elif output_slot_index ==3 :return str (abs_x )
                elif output_slot_index ==4 :return str (abs_y )
                elif output_slot_index ==5 :return str (total_px )
                elif output_slot_index ==6 :
                    return f"{{\\pos({abs_x },{abs_y })\\1c{col_ass }\\1a{alpha_ass }}}{p_shape }"

                return f"{{\\pos({abs_x },{abs_y })\\1c{col_ass }\\1a{alpha_ass }}}{p_shape }"
            except Exception as e :
                return f"[Err Image Particles: {e }]"

        if node_type in ["Loops/Module","Module"]:
            in_i =self .get_input_value (node ,0 ,context )
            in_n =self .get_input_value (node ,1 ,context )
            in_m =self .get_input_value (node ,2 ,context )

            raw_i =in_i if (in_i is not None and str (in_i ).strip ()!="")else _get_prop_value (props ,"iter","i")
            raw_n =in_n if (in_n is not None and str (in_n ).strip ()!="")else _get_prop_value (props ,"total","N")
            raw_m =in_m if (in_m is not None and str (in_m ).strip ()!="")else _get_prop_value (props ,"sub_m","0")

            val_i =float (_eval_num_expr (raw_i ,context ,1.0 ))
            val_n =float (_eval_num_expr (raw_n ,context ,1.0 ))
            val_m =float (_eval_num_expr (raw_m ,context ,0.0 ))

            denom =val_n +val_m -1.0 
            res =(val_i -1.0 +val_m )/denom if (denom !=0 and val_n >1.0 )else val_m 
            res_rounded =round (res ,4 )
            if res_rounded ==int (res_rounded ):
                return str (int (res_rounded ))
            return f"{res_rounded :.4f}".rstrip ('0').rstrip ('.')

        if node_type in ["Variables/Sys Var","Sys Var"]:
            v_name =str (_get_prop_value (props ,"var_name","syl.text")).strip ()
            clean_v =v_name .lower ().replace ("fx.","")

            if clean_v in ["module","m"]:
                mod_val =round (float (context .get ("module",0.0 )),4 )
                if mod_val ==int (mod_val ):
                    return str (int (mod_val ))
                return f"{mod_val :.4f}".rstrip ('0').rstrip ('.')

            return str (_eval_sys_var (v_name ,context ))

        if node_type in ["Basics/String", "String"] or name == "String":
            return str(_get_prop_value(props, "value", ""))

        if node_type in ["Basics/Number", "Number"] or name == "Number":
            raw_val =_get_prop_value (props ,"value",0 )
            res =_eval_num_expr (raw_val ,context ,default =0.0 )
            if isinstance (res ,float )and res .is_integer ():
                return str (int (res ))
            return f"{res :.4f}".rstrip ('0').rstrip ('.')

        if node_type in ["Variables/Get Var", "Get Var"]:
            return context .get (props .get ("var_name",""),"")

        elif node_type in ["Variables/Memory","Memory"]:
            mode =str (props .get ("mode","remember")).strip ().lower ()
            key_val =self .get_input_value (node ,0 ,context )
            if key_val =="":key_val =str (props .get ("key","ref")).strip ()

            input_val =self .get_input_value (node ,1 ,context )
            if input_val =="":input_val =str (props .get ("value",props .get ("default",""))).strip ()

            if "remember" in mode or mode == "save":
                return str (self .remember (key_val ,input_val ))
            else :
                return str (self .recall (key_val ,input_val ))

        elif node_type in ["Loops/Main Loop","Main Loop"]or (isinstance (node_type ,str )and node_type .endswith ("Main Loop")):
            unit =context .get ('active_unit')
            if output_slot_index ==1 :
                return str (getattr (unit ,'i',1 )if unit else 1 )
            elif output_slot_index ==2 :
                return str (getattr (unit ,'n',1 )if unit else 1 )
            return ""

        elif node_type in ["Loops/MaxLoop","MaxLoop"]or (isinstance (node_type ,str )and node_type .endswith ("MaxLoop")):
            props =node .get ("properties",{})
            var_name =str (props .get ("var_name","j")).strip ()or "j"
            if output_slot_index ==1 :
                return str (context .get (var_name ,context .get ('j',context .get ('fx_i',1 ))))
            elif output_slot_index ==2 :
                return str (context .get (var_name +'_max',context .get ('maxj',context .get ('fx_n',1 ))))
            return ""

        elif node_type in ["Basics/Color Picker", "Color Picker"] or name == "Color Picker":
            try :
                from utils import parse_color_to_rgb ,rgb_to_ass_color ,rgb_to_hex_color 
                colors =props .get ("colors")
                if not isinstance (colors ,list )or len (colors )==0 :
                    colors =[]
                    idx =0 
                    while f"color_{idx }"in props :
                        colors .append (props [f"color_{idx }"])
                        idx +=1 
                    if not colors :
                        colors =[props .get ("color","#FFFFFF")]

                formats =props .get ("formats")
                if not isinstance (formats ,list )or len (formats )==0 :
                    formats =[]
                    idx =0 
                    while f"format_{idx }"in props :
                        formats .append (props [f"format_{idx }"])
                        idx +=1 
                    if not formats :
                        formats =["ASS"]*len (colors )

                def _format_color (i ):
                    c_hex =str (colors [i ]if i <len (colors )else "#FFFFFF").strip ()
                    r ,g ,b =parse_color_to_rgb (c_hex )
                    fmt =str (formats [i ]if i <len (formats )else "ASS").upper ()
                    if fmt in ["HEX","HTML","#"]:
                        return rgb_to_hex_color (r ,g ,b )
                    else :
                        return rgb_to_ass_color (r ,g ,b )


                if output_slot_index ==0 :
                    palette =[_format_color (i )for i in range (len (colors ))]
                    return ", ".join (palette )

                elif output_slot_index is not None and output_slot_index >0 :
                    swatch_idx =min (len (colors )-1 ,output_slot_index -1 )
                    return _format_color (swatch_idx )
                else :
                    return _format_color (0 )
            except Exception as e :
                import traceback 
                print (f"[Pyxis Engine Error] Color Picker evaluation failed: {e }")
                traceback .print_exc ()
                return "&HFFFFFF&"

        elif node_type in ["Functions/Color Gradient","Color Gradient"]:
            try :
                from nodes .tag_nodes import node_color_gradient 
                prog_raw =self .get_input_value (node ,0 ,context )
                if prog_raw =="":prog_raw =str (_get_prop_value (props ,"prog","char.i / char.n")).strip ()

                colors_raw =self .get_input_value (node ,1 ,context )
                if colors_raw =="":colors_raw =str (_get_prop_value (props ,"colors_str","#95E648,#3E750C,#ED38CA")).strip ()

                total_raw =self .get_input_value (node ,2 ,context )
                if total_raw =="":total_raw =str (_get_prop_value (props ,"total","1")).strip ()

                accel_raw =self .get_input_value (node ,3 ,context )
                if accel_raw =="":accel_raw =str (_get_prop_value (props ,"accel","1.0")).strip ()

                tag_type_raw =str (_get_prop_value (props ,"tag_type","\\1c")).strip ()

                return node_color_gradient (
                context =context ,
                prog =prog_raw ,
                colors_str =colors_raw ,
                total =total_raw ,
                accel =accel_raw ,
                tag_type =tag_type_raw ,
                output_slot_index =output_slot_index 
                )
            except Exception as e :
                return f"[Err Color Gradient: {e }]"

        elif node_type in ["Basics/Concatenate", "Concatenate", "Functions/Concatenate", "Text/Concatenate"] or name == "Concatenate":
            inputs_count =len (node .get ('inputs',[]))
            sep =str (_get_prop_value (props ,"separator","nil")).strip ().lower ()

            if sep in ("zip",):
                input_lists =[]
                for i in range (inputs_count ):
                    inp_def =node .get ('inputs',[])[i ]if i <len (node .get ('inputs',[]))else {}
                    has_link =inp_def .get ('link')is not None 

                    wire_val =self .get_input_value (node ,i ,context )if has_link else None 
                    box_prop =props .get (f"In{i +1 }",props .get (f"in{i +1 }",""))
                    box_tag =str (box_prop ).strip ()if box_prop is not None else ""

                    if has_link and wire_val is not None and str (wire_val ).strip ()!="":
                        if isinstance (wire_val ,(list ,tuple )):
                            raw_items =[x for x in wire_val if x is not None and str (x ).strip ()!=""]
                        else :
                            raw_items =_split_tokens_respecting_delimiters (str (wire_val ))

                        if box_tag !="":
                            items =[_format_tagged_item (box_tag ,x )for x in raw_items ]
                        else :
                            items =[str (x ).strip ()for x in raw_items if str (x ).strip ()!=""]
                        input_lists .append (items )
                    else :
                        if box_tag !="":
                            raw_items =_split_tokens_respecting_delimiters (box_tag )
                            input_lists .append ([str (x ).strip ()for x in raw_items if str (x ).strip ()!=""])
                        else :
                            input_lists .append ([])

                active_lists =[l for l in input_lists if len (l )>0 ]
                if not active_lists :
                    return ""

                multi_lens =[len (l )for l in active_lists if len (l )>1 ]
                num_kfs =min (multi_lens )if multi_lens else 1 

                keyframes =[]
                for k in range (num_kfs ):
                    kf_parts =[]
                    for l in active_lists :
                        item =l [k ]if len (l )>1 else l [0 ]
                        if item :
                            kf_parts .append (item )
                    keyframes .append ("".join (kf_parts ))

                return ", ".join (keyframes )

            else :
                values =[]
                for i in range (inputs_count ):
                    val =self .get_input_value (node ,i ,context )
                    if val =="":
                        val =props .get (f"In{i +1 }",props .get (f"in{i +1 }",""))
                    if val !="":
                        values .append (str (val ))
                if sep in ("nil","","none"):
                    sep_char =""
                elif sep in ("space","espacio"," "):
                    sep_char =" "
                elif sep in ("comma","coma",","):
                    sep_char =","
                elif sep in ("semicolon","punto_coma","punto y coma",";"):
                    sep_char =";"
                elif sep in ("newline","salto","\\n","\n","enter"):
                    sep_char ="\n"
                else :
                    sep_char =sep 
                return sep_char .join (values )

        elif node_type in ["Functions/Interpolator","Interpolator"]:
            try :
                raw_i =self .get_input_value (node ,0 ,context )
                if raw_i =="":raw_i =_get_prop_value (props ,"iterator","i")
                str_i =str (raw_i ).strip ().lower ()
                if str_i in ["i","iterador","iterator"]:
                    val_i =float (context .get ("i",context .get ("fx_i",1.0 )))if isinstance (context ,dict )else 1.0 
                elif str_i in ["j","loop"]:
                    val_i =float (context .get ("j",context .get ("fx_i",1.0 )))if isinstance (context ,dict )else 1.0 
                else :
                    val_i =float (_eval_num_expr (raw_i ,context ,1.0 ))

                raw_n =self .get_input_value (node ,1 ,context )
                if raw_n =="":raw_n =_get_prop_value (props ,"total","N")
                str_n =str (raw_n ).strip ().lower ()
                if str_n in ["n","total","max"]:
                    val_n =float (context .get ("n",context .get ("fx_n",context .get ("maxloop",1.0 ))))if isinstance (context ,dict )else 1.0 
                elif str_n in ["maxj","max_j","maxloop"]:
                    val_n =float (context .get ("maxj",context .get ("maxloop",1.0 )))if isinstance (context ,dict )else 1.0 
                else :
                    val_n =float (_eval_num_expr (raw_n ,context ,1.0 ))

                raw_accel =self .get_input_value (node ,2 ,context )
                if raw_accel =="":raw_accel =_get_prop_value (props ,"accel","1.0")
                accel_val =max (0.001 ,float (_eval_num_expr (raw_accel ,context ,1.0 )))

                raw_v1 = self.get_input_value(node, 3, context)
                if raw_v1 == "":
                    raw_v1 = _get_prop_value(props, "v1", "")

                raw_v2 = self.get_input_value(node, 4, context)
                if raw_v2 == "":
                    raw_v2 = _get_prop_value(props, "v2", "")

                raw_val_list = []
                if raw_v1 != "":
                    raw_val_list.append(raw_v1)
                if raw_v2 != "":
                    raw_val_list.append(raw_v2)

                if len(raw_val_list) < 2 and not any(isinstance(v, (list, tuple)) or (isinstance(v, str) and (',' in v or ';' in v)) for v in raw_val_list):
                    p_v1 = str(_get_prop_value(props, "v1", "0")).strip()
                    p_v2 = str(_get_prop_value(props, "v2", "1")).strip()
                    raw_val_list = [p_v1 if p_v1 != "" else "0", p_v2 if p_v2 != "" else "1"]

                val_list =[]
                for item in raw_val_list :
                    if isinstance (item ,(list ,tuple )):
                        val_list .extend ([str (x ).strip ()for x in item if str (x ).strip ()!=""])
                    elif isinstance (item ,str ):
                        s_item =item .strip ()
                        if s_item .startswith ("[")and s_item .endswith ("]"):
                            try :
                                import json 
                                parsed =json .loads (s_item )
                                if isinstance (parsed ,list ):
                                    val_list .extend ([str (x ).strip ()for x in parsed if str (x ).strip ()!=""])
                                    continue 
                            except Exception :
                                pass 
                        tokens =_split_tokens_respecting_delimiters (s_item )
                        if len (tokens )>1 :
                            val_list .extend (tokens )
                        elif s_item !="":
                            val_list .append (s_item )
                    elif item is not None and str (item ).strip ()!="":
                        val_list .append (str (item ).strip ())

                def _interpolate_single (t_norm ):
                    t_clamped =max (0.0 ,min (1.0 ,float (t_norm )))
                    if not val_list :
                        return ""
                    if len (val_list )==1 :
                        return str (val_list [0 ])

                    n_segments =len (val_list )-1 
                    scaled_t =t_clamped *n_segments 
                    seg_idx =int (scaled_t )
                    if seg_idx >=n_segments :
                        seg_idx =n_segments -1 
                        local_t =1.0 
                    else :
                        local_t =scaled_t -seg_idx 

                    v1 ,v2 =val_list [seg_idx ],val_list [seg_idx +1 ]
                    str1 ,str2 =str (v1 ).strip (),str (v2 ).strip ()


                    if re .search (r'\bm\s+-?\d+',str1 )and re .search (r'\bm\s+-?\d+',str2 ):
                        try :
                            from clipper_engine import ClipperEngine 
                            import numpy as np 
                            cnts1 =ClipperEngine .parse_assdraw (str1 )
                            cnts2 =ClipperEngine .parse_assdraw (str2 )
                            if cnts1 and cnts2 :
                                all_pts1 =np .vstack (cnts1 )
                                all_pts2 =np .vstack (cnts2 )
                                target_count =max (len (all_pts1 ),len (all_pts2 ),30 )

                                def _resample (pts ,count ):
                                    if len (pts )<2 :
                                        return np .repeat (pts ,count ,axis =0 )
                                    diffs =np .diff (pts ,axis =0 )
                                    dists =np .hypot (diffs [:,0 ],diffs [:,1 ])
                                    cum =np .insert (np .cumsum (dists ),0 ,0.0 )
                                    tot =cum [-1 ]
                                    if tot <=1e-6 :
                                        return np .repeat (pts [:1 ],count ,axis =0 )
                                    sdists =np .linspace (0.0 ,tot ,count )
                                    rx =np .interp (sdists ,cum ,pts [:,0 ])
                                    ry =np .interp (sdists ,cum ,pts [:,1 ])
                                    return np .column_stack ((rx ,ry ))

                                r1 =_resample (all_pts1 ,target_count )
                                r2 =_resample (all_pts2 ,target_count )
                                morphed =(1.0 -local_t )*r1 +local_t *r2 
                                parts =[f"m {round (morphed [0 ,0 ],2 )} {round (morphed [0 ,1 ],2 )}"]
                                for p in morphed [1 :]:
                                    parts .append (f"l {round (p [0 ],2 )} {round (p [1 ],2 )}")
                                return " ".join (parts )
                        except Exception :
                            pass 


                    if str1 .startswith ('\\')or str2 .startswith ('\\')or str1 .startswith ('{')or str2 .startswith ('{'):
                        try :
                            from clipper_engine import ClipperEngine 
                            kf1 =ClipperEngine ._parse_tag_keyframe (str1 )
                            kf2 =ClipperEngine ._parse_tag_keyframe (str2 )
                            if kf1 or kf2 :
                                return ClipperEngine ._interpolate_tag_keyframes ([kf1 ,kf2 ],local_t ,is_first_piece =True )
                        except Exception :
                            pass 


                    if str1 .startswith ("&H")and str1 .endswith ("&")and len (str1 )<=6 and str2 .startswith ("&H")and str2 .endswith ("&")and len (str2 )<=6 :
                        try :
                            a1 =int (str1 [2 :-1 ],16 )
                            a2 =int (str2 [2 :-1 ],16 )
                            a =max (0 ,min (255 ,int (round (a1 +(a2 -a1 )*local_t ))))
                            return f"&H{a :02X}&"
                        except Exception :
                            pass 


                    if (str1 .startswith ("&H")or str1 .startswith ("#"))and (str2 .startswith ("&H")or str2 .startswith ("#")):
                        try :
                            from utils import parse_color_to_rgb ,rgb_to_ass_color ,rgb_to_hex_color 
                            r1 ,g1 ,b1 =parse_color_to_rgb (str1 )
                            r2 ,g2 ,b2 =parse_color_to_rgb (str2 )
                            r =int (round (r1 +(r2 -r1 )*local_t ))
                            g =int (round (g1 +(g2 -g1 )*local_t ))
                            b =int (round (b1 +(b2 -b1 )*local_t ))
                            if str1 .startswith ("#"):
                                return rgb_to_hex_color (r ,g ,b )
                            else :
                                return rgb_to_ass_color (r ,g ,b )
                        except Exception :
                            pass 


                    try :
                        def _to_num (val_raw ):
                            try :
                                return float (val_raw )
                            except (ValueError ,TypeError ):
                                pass 
                            res =_eval_num_expr (val_raw ,context ,default =None )
                            if res is not None :
                                try :
                                    return float (res )
                                except (ValueError ,TypeError ):
                                    pass 
                            return None 

                        n1 =_to_num (v1 )
                        n2 =_to_num (v2 )
                        if n1 is not None and n2 is not None :
                            res =n1 +(n2 -n1 )*local_t 
                            if float (n1 ).is_integer ()and float (n2 ).is_integer ()and float (res ).is_integer ():
                                return str (int (res ))
                            return f"{res :.2f}".rstrip ('0').rstrip ('.')
                    except Exception :
                        pass 

                    return str (v1 if local_t <0.5 else v2 )


                def _apply_easing (raw_progress ):
                    t_val =max (0.0 ,min (1.0 ,float (raw_progress )))
                    if accel_val !=1.0 and 0.0 <t_val <1.0 :
                        if accel_val >1.0 :
                            return t_val **accel_val 
                        elif accel_val >0.0 :
                            p =1.0 /accel_val 
                            return 1.0 -((1.0 -t_val )**p )
                    return t_val 


                if output_slot_index ==1 :
                    n_steps =max (1 ,int (round (val_n )))
                    batch_vals =[]
                    for k in range (1 ,n_steps +1 ):
                        tk =(k -1.0 )/(n_steps -1.0 )if n_steps >1 else 0.0 
                        tk_eased =_apply_easing (tk )
                        batch_vals .append (_interpolate_single (tk_eased ))
                    return ", ".join (batch_vals )


                if 0.0 <=val_i <=1.0 and (raw_n ==""or val_n ==1.0 ):
                    t_val =val_i 
                else :
                    if val_n >1.0 :
                        t_val =(val_i -1.0 )/(val_n -1.0 )
                    else :
                        t_val =0.0 

                t_eased =_apply_easing (t_val )
                return _interpolate_single (t_eased )
            except Exception as e :
                return f"[Err Interpolator: {e }]"

        elif node_type in ["Functions/Animation", "Animation"]:
            try:
                raw_frames = self.get_input_value(node, 0, context)
                if raw_frames == "":
                    raw_frames = _get_prop_value(props, "frames", "")

                raw_step = self.get_input_value(node, 1, context)
                if raw_step == "":
                    raw_step = _get_prop_value(props, "step_ms", 41.7)

                raw_st = self.get_input_value(node, 2, context)
                if raw_st == "":
                    raw_st = _get_prop_value(props, "start_time", "")

                raw_et = self.get_input_value(node, 3, context)
                if raw_et == "":
                    raw_et = _get_prop_value(props, "end_time", "")

                mode_val = _get_prop_value(props, "mode", "fbf")
                alpha_tag_val = _get_prop_value(props, "alpha_tag", r"\alpha")
                order_val = _get_prop_value(props, "order", "sequential")
                var_name_val = _get_prop_value(props, "var_name", "an")

                from nodes.tag_nodes import node_animation
                return node_animation(
                    context=context,
                    frames=raw_frames,
                    step_ms=raw_step,
                    start_time=raw_st,
                    end_time=raw_et,
                    mode=mode_val,
                    alpha_tag=alpha_tag_val,
                    order=order_val,
                    var_name=var_name_val,
                    output_slot_index=output_slot_index
                )
            except Exception as e:
                import traceback
                print(f"[Pyxis Node Error] Exception in 'Animation': {e}")
                traceback.print_exc()
                return f"[Err Animation: {e}]"

        if node_type in NODE_REGISTRY :
            func =NODE_REGISTRY [node_type ]
            expected_inputs =PYXIS_DB .get (category ,{}).get (name ,[])
            args =[]
            dynamic_kwargs ={}
            if expected_inputs:
                for i ,input_name in enumerate (expected_inputs ):
                    val =self .get_input_value (node ,i ,context )
                    if val =="":
                        val_str =str (_get_prop_value (props ,input_name ,"")).strip ()
                        if val_str in context :val =str (context [val_str ])
                        else :
                            try :
                                if '.'in val_str :
                                    obj_name ,attr =val_str .split ('.')
                                    if obj_name in context and hasattr (context [obj_name ],attr ):val =str (getattr (context [obj_name ],attr ))
                                    else :val =val_str 
                                else :val =val_str 
                            except Exception :val =val_str 
                    args .append (val )
            else:
                inputs_list = node.get("inputs", [])
                for i, inp_obj in enumerate(inputs_list):
                    inp_name = inp_obj.get("name", "")
                    inp_prop = inp_obj.get("property") or inp_name
                    val = self.get_input_value(node, i, context)
                    if val == "":
                        prop_val = str(_get_prop_value(props, inp_prop, _get_prop_value(props, inp_name, ""))).strip()
                        if prop_val == "" and "value" in inp_obj and inp_obj["value"] is not None:
                            prop_val = str(inp_obj["value"]).strip()
                        val = prop_val
                    if val != "":
                        if inp_name:
                            dynamic_kwargs[str(inp_name)] = val
                        if inp_prop:
                            dynamic_kwargs[str(inp_prop)] = val

            try :
                import inspect 
                sig =inspect .signature (func )
                kwargs =dict(dynamic_kwargs)
                param_names = list(sig.parameters.keys())
                bound_positional = set(param_names[:len(args) + 1])
                if "output_slot_index" in sig.parameters or any (p .kind ==inspect .Parameter .VAR_KEYWORD for p in sig .parameters .values ()):
                    kwargs ["output_slot_index"]=output_slot_index 
                for k ,v in props .items ():
                    if k not in kwargs and k not in bound_positional:
                        kwargs [k ]=v 
                return str (func (context ,*args ,**kwargs ))
            except Exception as e :
                import traceback 
                print (f"[Pyxis Node Error] Exception in '{node_type }': {e }")
                traceback .print_exc ()
                return f"[Err {name }]"

        return ""

    def _update_progress (self ,progress_tracker ,progress_callback ):
        if not progress_tracker or not callable (progress_callback ):
            return 
        progress_tracker ['current']+=1 
        curr =progress_tracker ['current']
        total =max (1 ,progress_tracker .get ('total',1 ))

        has_audio =getattr (self ,'_has_audio_nodes',False )
        base_min_pct =25 if has_audio else 5 
        pct =min (89 ,base_min_pct +int ((curr /total )*(89 -base_min_pct )))

        now =time .time ()
        last_pct =progress_tracker .get ('last_pct',0 )
        last_time =progress_tracker .get ('last_time',0.0 )
        t_start =progress_tracker .get ('start_time')
        if not t_start :
            progress_tracker ['start_time']=now 
            t_start =now 

        current_lines =len (self .all_generated_lines )
        if (pct >last_pct and (now -last_time >=0.02 or pct -last_pct >=1 ))or (now -last_time >=0.05 )or (current_lines >0 and current_lines %25 ==0 )or total <=30 :
            progress_tracker ['last_pct']=pct 
            progress_tracker ['last_time']=now 
            elapsed =max (0.001 ,now -t_start )
            speed =int (current_lines /elapsed )if elapsed >0.05 else 0 
            progress_callback ({
            "percent":max (base_min_pct ,pct ),
            "lines_generated":current_lines ,
            "total_units":total ,
            "current_unit":curr ,
            "speed":speed ,
            "phase":f"Generating... {current_lines :,} lines ({speed } l/s)"if speed >0 else f"Generating... {current_lines :,} lines"
            })

    def execute_loops_recursive (self ,chain ,context ,output_node ,active_unit =None ,check_cancel =None ,progress_tracker =None ,progress_callback =None ):
        if self .is_cancelled :
            return 
        if getattr (self ,'shared_cancel_flag',None )is not None and getattr (self .shared_cancel_flag ,'value',False ):
            self .is_cancelled =True 
            return 

        if not chain :
            props =output_node .get ('properties',{})
            origin_align =5 
            try :
                origin_align =int (props .get ('origin_align',5 ))
                if origin_align <1 or origin_align >9 :
                    origin_align =5 
            except Exception :
                origin_align =5 
            context ['origin_align']=origin_align 
            context ['fx_align']=5 

            u_left =float (context .get ('val_left',getattr (active_unit ,'left',getattr (active_unit ,'center',0.0 ))if active_unit else 0.0 ))
            u_center =float (context .get ('val_center',getattr (active_unit ,'center',0.0 )if active_unit else 0.0 ))
            u_right =float (context .get ('val_right',getattr (active_unit ,'right',getattr (active_unit ,'center',0.0 ))if active_unit else 0.0 ))
            u_top =float (context .get ('val_top',getattr (active_unit ,'top',getattr (active_unit ,'middle',0.0 ))if active_unit else 0.0 ))
            u_middle =float (context .get ('val_middle',getattr (active_unit ,'middle',0.0 )if active_unit else 0.0 ))
            u_bottom =float (context .get ('val_bottom',getattr (active_unit ,'bottom',getattr (active_unit ,'middle',0.0 ))if active_unit else 0.0 ))

            if origin_align in (7 ,4 ,1 ):
                orig_x =u_left 
            elif origin_align in (9 ,6 ,3 ):
                orig_x =u_right 
            else :
                orig_x =u_center 

            if origin_align in (7 ,8 ,9 ):
                orig_y =u_top 
            elif origin_align in (1 ,2 ,3 ):
                orig_y =u_bottom 
            else :
                orig_y =u_middle 

            context ['fx_pos_x']=round (orig_x ,3 )
            context ['fx_pos_y']=round (orig_y ,3 )

            layer_in =self .get_input_value (output_node ,1 ,context )
            st_in =self .get_input_value (output_node ,2 ,context )
            et_in =self .get_input_value (output_node ,3 ,context )


            _ ,st_tmp ,et_tmp ,_ ,_ =self ._apply_defaults (
            active_unit ,layer_in ,st_in ,et_in ,"","",context =context 
            )
            eff_dur =max (1.0 ,float (et_tmp )-float (st_tmp ))
            context ["effect_st"]=float (st_tmp )
            context ["effect_et"]=float (et_tmp )
            context ["effect_dur"]=eff_dur 
            context ["fx_st"]=float (st_tmp )
            context ["fx_et"]=float (et_tmp )
            context ["fx_dur"]=eff_dur 
            context ["fx_start_time"]=float (st_tmp )
            context ["fx_end_time"]=float (et_tmp )
            context ["fx"]=FxContext (context )

            if not context .get ('in_auto_slicer_loop'):
                dummy_ctx =context .copy ()
                dummy_ctx ['in_auto_slicer_loop']=True 
                dummy_ctx ['fx']=FxContext (dummy_ctx )
                self .get_input_value (output_node ,4 ,dummy_ctx )
                self .get_input_value (output_node ,5 ,dummy_ctx )
                auto_n =dummy_ctx .get ('maxloop',1 )
                anim_step =dummy_ctx .get ('anim_step_ms')
                if auto_n >1 :
                    for auto_j in range (1 ,auto_n +1 ):
                        if self .is_cancelled :break 
                        loop_ctx =context .copy ()
                        loop_ctx ['in_auto_slicer_loop']=True 
                        loop_ctx ['d_i']=auto_j 
                        loop_ctx ['d_n']=auto_n 
                        loop_ctx ['d_max']=auto_n 
                        loop_ctx ['divide_i']=auto_j 
                        loop_ctx ['divide_n']=auto_n 
                        loop_ctx ['divide_max']=auto_n 
                        loop_ctx ['s_i']=auto_j 
                        loop_ctx ['s_n']=auto_n 
                        loop_ctx ['s_max']=auto_n 
                        loop_ctx ['slice_i']=auto_j 
                        loop_ctx ['slice_n']=auto_n 
                        loop_ctx ['slice_max']=auto_n 
                        loop_ctx ['tp_i']=auto_j 
                        loop_ctx ['tp_n']=auto_n 
                        loop_ctx ['tp_max']=auto_n 
                        loop_ctx ['m_i']=auto_j 
                        loop_ctx ['m_n']=auto_n 
                        loop_ctx ['m_max']=auto_n 
                        loop_ctx ['multi_i']=auto_j 
                        loop_ctx ['multi_n']=auto_n 
                        loop_ctx ['multi_max']=auto_n 
                        loop_ctx ['text_p_i']=auto_j 
                        loop_ctx ['text_p_n']=auto_n 
                        loop_ctx ['text_p_max']=auto_n 
                        loop_ctx ['p_i']=auto_j 
                        loop_ctx ['p_n']=auto_n 
                        loop_ctx ['p_max']=auto_n 
                        loop_ctx ['particle_i']=auto_j 
                        loop_ctx ['particle_n']=auto_n 
                        loop_ctx ['particle_max']=auto_n 
                        loop_ctx ['total_pixels']=auto_n 
                        loop_ctx ['a_i']=auto_j 
                        loop_ctx ['a_n']=auto_n 
                        loop_ctx ['a_max']=auto_n 
                        loop_ctx ['array_i']=auto_j 
                        loop_ctx ['array_n']=auto_n 
                        loop_ctx ['array_max']=auto_n 
                        loop_ctx ['b_i']=auto_j 
                        loop_ctx ['b_n']=auto_n 
                        loop_ctx ['b_max']=auto_n 
                        loop_ctx ['ring_i']=auto_j 
                        loop_ctx ['ring_n']=auto_n 
                        loop_ctx ['ring_max']=auto_n 
                        loop_ctx ['c_i']=auto_j 
                        loop_ctx ['c_n']=auto_n 
                        loop_ctx ['c_max']=auto_n 
                        loop_ctx ['clip_i']=auto_j 
                        loop_ctx ['clip_n']=auto_n 
                        loop_ctx ['clip_max']=auto_n 
                        loop_ctx ['an_i']=auto_j 
                        loop_ctx ['an_n']=auto_n 
                        loop_ctx ['an_max']=auto_n 
                        loop_ctx ['anim_i']=auto_j 
                        loop_ctx ['anim_n']=auto_n 
                        loop_ctx ['anim_max']=auto_n 
                        if anim_step :
                            base_st = float(dummy_ctx.get('anim_base_st', context.get('start_time', getattr(active_unit, 'start_time', 0.0))))
                            frame_st = base_st + (auto_j - 1) * anim_step
                            frame_et = frame_st + anim_step 
                            loop_ctx ['st']=frame_st 
                            loop_ctx ['et']=frame_et 
                            loop_ctx ['start_time']=frame_st 
                            loop_ctx ['end_time']=frame_et 
                            loop_ctx ['frame_start_time']=frame_st 
                            loop_ctx ['frame_end_time']=frame_et 
                            loop_ctx ['frame_dur']=anim_step 
                            loop_ctx ['fd']=anim_step 
                            loop_ctx ['fx_start_time']=frame_st 
                            loop_ctx ['fx_end_time']=frame_et 
                            loop_ctx ['fx_dur']=anim_step 
                        if 'j'not in context :
                            loop_ctx ['j']=auto_j 
                            loop_ctx ['maxj']=auto_n 
                        loop_ctx ['fx_i']=auto_j 
                        loop_ctx ['fx_n']=auto_n 
                        loop_ctx ['fx']=FxContext (loop_ctx )
                        self .execute_loops_recursive ([],loop_ctx ,output_node ,active_unit ,check_cancel ,progress_tracker ,progress_callback )
                    return 

            for n_id ,n_obj in self .nodes .items ():
                node_type =n_obj .get ('type','')
                if node_type in ['Variables/Memory','Memory']:
                    mode =str (n_obj .get ('properties',{}).get ('mode','')).strip ()
                    if 'Remember'in mode :
                        self .evaluate_data_node (n_id ,context )
                elif node_type in ['System/Script Code','Script Code']:
                    self .evaluate_data_node (n_id ,context )

            is_ret_conn =self .is_port_connected (output_node ,5 )
            context ['_return_port_connected']=is_ret_conn 
            if is_ret_conn :
                inp_5 =output_node .get ('inputs',[])[5 ]if len (output_node .get ('inputs',[]))>5 else None 
                link_id =inp_5 .get ('link')if isinstance (inp_5 ,dict )else None 
                link_obj =next ((l for l in self .links if l [0 ]==link_id ),None )if link_id else None 
                src_node =self .nodes .get (link_obj [1 ])if link_obj else None 
                src_type =str (src_node .get ('type','')).lower ()if src_node else ''
                context ['_return_node_is_shape']=any (kw in src_type for kw in ['shape','stroke','walker','slicer','border','drawing','particle','pixel','curva','bezier','animation'])
                retorno_str =self .get_input_value (output_node ,5 ,context )
            else :
                context ['_return_node_is_shape']=False 
                retorno_str =getattr (active_unit ,'text_stripped','')

            context ['return_raw']=retorno_str 
            context ['retorno_str']=retorno_str 

            tags_str =self .get_input_value (output_node ,4 ,context )
            loop_tags = str(context.get('loop_tags') or context.get('script_tags') or '').strip()
            if loop_tags:
                tags_str = merge_ass_tags(tags_str, loop_tags) if tags_str else loop_tags

            queue_id =self .get_input_value (output_node ,6 ,context )
            if _is_empty_value (queue_id ):
                for k in ['queue_id','actor','Queue ID','Queue_ID','queue']:
                    if k in props and not _is_empty_value (props [k ]):
                        queue_id =str (props [k ]).strip ()
                        break 

            queue_order =self .get_input_value (output_node ,7 ,context )
            if _is_empty_value (queue_order ):
                for k in ['queue_order','orden_cola','orden','order','Queue Order','Queue_Order']:
                    if k in props and not _is_empty_value (props [k ]):
                        queue_order =props [k ]
                        break 

            layer ,st ,et ,tags_str ,retorno_str =self ._apply_defaults (
            active_unit ,layer_in ,st_in ,et_in ,tags_str ,retorno_str ,context =context 
            )

            if not _final_text_has_content (retorno_str )and not str (tags_str ).strip ():return 



            if (r'\p1'in tags_str or (is_ret_conn and context .get ('_return_node_is_shape')))and not str (retorno_str ).strip ():
                return 

            queue_id =queue_id .strip ()if queue_id else "default"
            queue_order =_to_int_or_default (queue_order ,0 ,context =context )

            pyxis_line =context ['line']
            line_idx = getattr(pyxis_line, 'i', 0) if pyxis_line else 0
            from string_evaluator import evaluate_ass_line_tag_blocks
            evaluated_text = evaluate_ass_line_tag_blocks(f"{{{tags_str }}}{retorno_str }", context)

            ass_line ={
            'line_idx':line_idx ,
            'layer':layer ,
            'start_time':st ,
            'end_time':et ,
            'style_name':pyxis_line .style_name ,
            'actor':queue_id ,
            'margin_l':pyxis_line .margin_l ,
            'margin_r':pyxis_line .margin_r ,
            'margin_v':pyxis_line .margin_v ,
            'effect':'pyxis_fx',
            'text':evaluated_text ,
            'queue_id':queue_id ,
            'queue_order':queue_order 
            }
            self .all_generated_lines .append (ass_line )


            self ._local_line_batch =getattr (self ,'_local_line_batch',0 )+1 
            if self ._local_line_batch >=25 :
                if getattr (self ,'shared_line_counter',None )is not None :
                    try :
                        with self .shared_line_counter .get_lock ():
                            self .shared_line_counter .value +=self ._local_line_batch 
                    except Exception :
                        pass 
                self ._local_line_batch =0 
                if progress_tracker and callable (progress_callback ):
                    self ._update_progress (progress_tracker ,progress_callback )


            if len (self .all_generated_lines )%10 ==0 :
                cancel_signal =False 
                if getattr (self ,'shared_cancel_flag',None )is not None and getattr (self .shared_cancel_flag ,'value',False ):
                    cancel_signal =True 
                elif callable (check_cancel )and check_cancel ():
                    cancel_signal =True 
                if cancel_signal :
                    self .is_cancelled =True 
            return 

        current_loop =chain [0 ]
        rest_chain =chain [1 :]

        _nb_str = str(
        current_loop .get ('noblank')or 
        current_loop .get ('properties',{}).get ('noblank')or 
        output_node .get ('properties',{}).get ('noblank','No Blank')
        )
        is_noblank = "Con Blanks" not in _nb_str and "With" not in _nb_str

        if current_loop ['type']=='base':
            base_type ,pyxis_line =current_loop ['val'],context ['line']
            if base_type =="line":
                self .bind_active_unit (context ,pyxis_line ,is_noblank =is_noblank ,output_node =output_node )
                self .execute_loops_recursive (rest_chain ,context ,output_node ,pyxis_line ,check_cancel ,progress_tracker ,progress_callback )
                self ._update_progress (progress_tracker ,progress_callback )
            elif base_type in ["syl","word","char"]:
                for unit in getattr (pyxis_line ,base_type +"s",[]):
                    if self .is_cancelled :break 
                    if is_noblank and (getattr (unit ,'is_blank',False )or not _has_visible_content (unit )):continue 
                    if not _has_visible_content (unit ):continue 
                    ctx =context .copy ()
                    ctx [base_type ]=unit 
                    if base_type =='char':
                        if getattr (unit ,'syl',None ):ctx ['syl']=unit .syl 
                        if getattr (unit ,'word',None ):
                            ctx ['word']=unit .word 
                        elif getattr (unit ,'syl',None )and getattr (unit .syl ,'word',None ):
                            ctx ['word']=unit .syl .word 
                    elif base_type =='syl':
                        if getattr (unit ,'word',None ):
                            ctx ['word']=unit .word 
                        elif getattr (unit ,'chars',None )and len (unit .chars )>0 and getattr (unit .chars [0 ],'word',None ):
                            ctx ['word']=unit .chars [0 ].word 
                    elif base_type =='word':
                        if getattr (unit ,'chars',None )and len (unit .chars )>0 and getattr (unit .chars [0 ],'syl',None ):
                            ctx ['syl']=unit .chars [0 ].syl 
                    self .bind_active_unit (ctx ,unit ,is_noblank =is_noblank ,output_node =output_node )
                    self .execute_loops_recursive (rest_chain ,ctx ,output_node ,unit ,check_cancel ,progress_tracker ,progress_callback )
                    self ._update_progress (progress_tracker ,progress_callback )

        elif current_loop ['type']=='maxloop':
            modo =str (current_loop .get ('modo',current_loop .get ('mode','Normal'))).strip ().lower ()
            var_name =current_loop .get ('var_name','j')

            is_fbf =("fbf"in modo )or ("frame"in modo )

            if is_fbf :
                maxloop_node =current_loop .get ('node')

                step_val =current_loop .get ('step_ms')or current_loop .get ('val')or 41.7 
                try :
                    step_ms =max (1.0 ,float (_eval_num_expr (step_val ,context ,default =41.7 )))
                except Exception :
                    step_ms =41.7 

                default_st =float (getattr (active_unit ,'start_time',context .get ('start_time',0.0 )))
                default_et =float (getattr (active_unit ,'end_time',context .get ('end_time',0.0 )))

                raw_st =""
                if maxloop_node :
                    raw_st =self .get_input_value (maxloop_node ,1 ,context )
                if not raw_st :
                    raw_st =str (current_loop .get ('start_time')or '').strip ()

                if raw_st and raw_st .lower ()not in ["start_time","st",""]:
                    try :
                        unit_st =float (_eval_num_expr (raw_st ,context ,default =default_st ))
                    except Exception :
                        unit_st =default_st 
                else :
                    unit_st =default_st 

                raw_et =""
                if maxloop_node :
                    raw_et =self .get_input_value (maxloop_node ,2 ,context )
                if not raw_et :
                    raw_et =str (current_loop .get ('end_time')or '').strip ()

                if raw_et and raw_et .lower ()not in ["end_time","et",""]:
                    try :
                        unit_et =float (_eval_num_expr (raw_et ,context ,default =default_et ))
                    except Exception :
                        unit_et =default_et 
                else :
                    unit_et =default_et 

                unit_dur =max (1.0 ,unit_et -unit_st )
                veces =max (1 ,int (math .ceil (unit_dur /step_ms )))

                for i in range (1 ,veces +1 ):
                    if self .is_cancelled :break 
                    ctx =context .copy ()
                    ctx [var_name ],ctx [var_name +'_max']=i ,veces 
                    ctx ['fx_i'],ctx ['fx_n']=i ,veces 
                    if var_name =='j'or 'maxj'not in ctx :
                        ctx ['maxj']=veces 
                    if var_name =='j'or 'j'not in ctx :
                        ctx ['j']=i 

                    frame_st =unit_st +(i -1 )*step_ms 
                    frame_et =frame_st +step_ms 

                    ctx ['st']=frame_st 
                    ctx ['et']=frame_et 
                    ctx ['start_time']=frame_st 
                    ctx ['end_time']=frame_et 
                    ctx ['frame_start_time']=frame_st 
                    ctx ['frame_end_time']=frame_et 
                    ctx ['frame_dur']=step_ms 
                    ctx ['fd']=step_ms 
                    ctx ['fx_start_time']=frame_st 
                    ctx ['fx_end_time']=frame_et 
                    ctx ['fx_dur']=step_ms 

                    self .bind_active_unit (ctx ,active_unit ,output_node =output_node )

                    ctx ['start_time']=frame_st 
                    ctx ['end_time']=frame_et 
                    ctx ['st']=frame_st 
                    ctx ['et']=frame_et 
                    ctx ['frame_start_time']=frame_st 
                    ctx ['frame_end_time']=frame_et 

                    self .execute_loops_recursive (rest_chain ,ctx ,output_node ,active_unit ,check_cancel ,progress_tracker ,progress_callback )
            else :
                try :
                    veces =int (float (_eval_num_expr (current_loop ['val'],context ,1 )))
                except Exception :
                    veces =1 
                for i in range (1 ,veces +1 ):
                    if self .is_cancelled :break 
                    ctx =context .copy ()
                    ctx [var_name ],ctx [var_name +'_max']=i ,veces 
                    ctx ['fx_i'],ctx ['fx_n']=i ,veces 
                    if var_name =='j'or 'maxj'not in ctx :
                        ctx ['maxj']=veces 
                    if var_name =='j'or 'j'not in ctx :
                        ctx ['j']=i 
                    self .bind_active_unit (ctx ,active_unit ,output_node =output_node )
                    self .execute_loops_recursive (rest_chain ,ctx ,output_node ,active_unit ,check_cancel ,progress_tracker ,progress_callback )

        elif current_loop ['type']=='set_vars':
            if self .is_cancelled :return 
            ctx =context .copy ()
            vars_str =str (current_loop .get ('val')or '')

            from nodes .code_nodes import execute_python_script ,_propagate_alias_changes 
            line_obj =ctx .get ('line')or ctx .get ('l')

            for part in vars_str .replace (';','\n').split ('\n'):
                part_clean =part .strip ()
                if not part_clean or part_clean .startswith ('#')or part_clean .startswith ('--'):
                    continue 
                if '='in part_clean :
                    key ,val_expr =part_clean .split ('=',1 )
                    key =key .strip ()
                    val_expr =val_expr .strip ()
                    if key and val_expr :
                        eval_res =execute_python_script (ctx ,val_expr ,{})
                        if not str (eval_res ).startswith ("[Err Python Script:"):
                            try :
                                res_str =str (eval_res ).strip ()
                                if res_str .replace ('.','',1 ).replace ('-','',1 ).isdigit ():
                                    val_typed =float (res_str )if '.'in res_str else int (res_str )
                                else :
                                    val_typed =eval_res 
                            except Exception :
                                val_typed =eval_res 
                        else :
                            val_typed =val_expr 

                        if key .startswith ("fx."):
                            fx_field =key [3 :].strip ()
                            _apply_fx_setting (fx_field ,val_typed ,ctx )
                            _propagate_alias_changes (ctx ,[fx_field ,f"fx_{fx_field}"],active_unit ,line_obj )
                        elif key .startswith (("syl.","char.","word.")):
                            unit_prefix ,unit_attr =key .split (".",1 )
                            unit_prefix =unit_prefix .strip ()
                            unit_attr =unit_attr .strip ()
                            u_target =ctx .get (unit_prefix )or (active_unit if unit_prefix =="syl"else None )
                            if u_target and hasattr (u_target ,unit_attr ):
                                try :setattr (u_target ,unit_attr ,val_typed )
                                except Exception :pass 
                            ctx [f"{unit_prefix}_{unit_attr}"]=val_typed 
                            ctx [unit_attr ]=val_typed 
                            _propagate_alias_changes (ctx ,[unit_attr ,f"{unit_prefix}_{unit_attr}"],active_unit ,line_obj )
                        elif key .startswith (("line.","l.","L.")):
                            l_attr =key .split (".",1 )[1 ].strip ()
                            if line_obj and hasattr (line_obj ,l_attr ):
                                try :setattr (line_obj ,l_attr ,val_typed )
                                except Exception :pass 
                            ctx [f"line_{l_attr}"]=val_typed 
                            ctx [l_attr ]=val_typed 
                            _propagate_alias_changes (ctx ,[l_attr ,f"line_{l_attr}"],active_unit ,line_obj )
                        else :
                            ctx [key ]=val_typed 
                            _apply_fx_setting (key ,val_typed ,ctx )
                            _propagate_alias_changes (ctx ,[key ],active_unit ,line_obj )
                else :
                    execute_python_script (ctx ,part_clean ,{})

            self .execute_loops_recursive (rest_chain ,ctx ,output_node ,active_unit ,check_cancel ,progress_tracker ,progress_callback )

        elif current_loop ['type']=='code_script':
            if self .is_cancelled :return 
            ctx =context .copy ()
            code_node =current_loop .get ('node',{})
            if code_node and 'id'in code_node :
                res =self .evaluate_data_node (code_node ['id'],ctx )
                ctx ['script_result']=res 
                if res and str (res ).strip ()and not str (res ).startswith ("[Err"):
                    existing_tags =str (ctx .get ('loop_tags')or ctx .get ('tags')or '')
                    ctx ['loop_tags']=merge_ass_tags (existing_tags ,str (res ))
                    ctx ['tags']=ctx ['loop_tags']
            self .execute_loops_recursive (rest_chain ,ctx ,output_node ,active_unit ,check_cancel ,progress_tracker ,progress_callback )

    def estimate_workload (self ,dialogue_items ,styles ,allow_fallback_select_all =True ,global_selected_styles =None ):
        """Calculates a high-speed mathematical estimation (< 1ms) of total FX lines that the current graph will generate over subtitles, as well as the complexity level."""
        from ass_parser import KaraokeProcessor 
        processor =KaraokeProcessor (self .rx ,self .ry ,self .fd )

        parsed_lines =[]
        selected_styles =set (global_selected_styles )if global_selected_styles is not None else set ()

        for item in dialogue_items :
            if hasattr (item ,'raw_text')and hasattr (item ,'syls'):
                pyxis_line =item 
            else :
                raw_line =item ['raw']if isinstance (item ,dict )else getattr (item ,'raw','')
                metrics =item .get ('metrics')if isinstance (item ,dict )else getattr (item ,'metrics',None )
                style_name =raw_line .split (',')[3 ]if ','in raw_line else ''
                pyxis_line =processor .process_line (raw_line ,styles .get (style_name ,{}),metrics )
            if pyxis_line :
                parsed_lines .append (pyxis_line )
                if not getattr(pyxis_line, 'is_comment', False) and pyxis_line .is_selected :
                    selected_styles .add (pyxis_line .style_name )

        selected_lines_list =[l for l in parsed_lines if l .is_selected and not getattr(l, 'is_comment', False)]
        if not selected_lines_list and allow_fallback_select_all :
            for l in parsed_lines :
                if not getattr(l, 'is_comment', False):
                    l .is_selected =True 
                    selected_styles .add (l .style_name )
            selected_lines_list =[l for l in parsed_lines if not getattr(l, 'is_comment', False)]

        output_nodes =[n for n in self .nodes .values ()if 'salida'in str (n .get ('type','')).lower ()or 'output'in str (n .get ('type','')).lower ()]

        total_estimated_lines =0 
        total_base_units =0 
        has_particles =False 
        has_scripts =False 
        has_potrace =False 
        has_audio =False 

        for n in self .nodes .values ():
            nt =str (n .get ('type',''))
            if 'Audio'in nt or 'audio'in nt .lower ()or 'Waveform'in nt or 'Modulador'in nt :
                has_audio =True 
            if 'IMG to pixels'in nt or 'Particles'in nt or 'pixels'in nt .lower ():
                has_particles =True 
            if 'Script Code'in nt or 'Code'in nt :
                has_scripts =True 
            if 'IMG to Shape'in nt or 'Potrace'in nt :
                has_potrace =True 

        for out_node in output_nodes :
            props =out_node .get ('properties',{})
            apply_to =props .get ('apply_to','Selected Lines')
            loop_chain =self .trace_loop_chain (out_node )
            if not loop_chain :continue 

            base_loop =next ((l for l in loop_chain if l ['type']=='base'),None )
            base_type =base_loop ['val']if base_loop else 'line'
            _nb_str2 = str(
            (base_loop .get ('noblank')if base_loop else '')or 
            (base_loop .get ('properties',{}).get ('noblank')if base_loop else '')or 
            props .get ('noblank','No Blank')
            )
            is_noblank = "Con Blanks" not in _nb_str2 and "With" not in _nb_str2


            has_explicit_maxloop =any (l .get ('type')in ['maxloop','auto_slicer_loop']for l in loop_chain )
            particle_auto_multiplier =1 
            if not has_explicit_maxloop :
                dummy_ctx ={'in_auto_slicer_loop':False }
                try :
                    for slot_idx in range (len (out_node .get ('inputs',[]))):
                        self .get_input_value (out_node ,slot_idx ,dummy_ctx )
                    auto_n =dummy_ctx .get ('maxloop',1 )
                    if auto_n >1 :
                        particle_auto_multiplier =int (auto_n )
                except Exception :
                    pass 

            for pyxis_line in parsed_lines :
                if getattr(pyxis_line, 'is_comment', False): continue
                if apply_to in ["Selected Lines","Sel. Lines"]and not pyxis_line .is_selected :continue 
                if apply_to =="Style Lines"and pyxis_line .style_name not in selected_styles :continue 

                if base_type in ['syl','char','word']:
                    units =getattr (pyxis_line ,base_type +"s",[])
                    if is_noblank :
                        active_units =[u for u in units if not getattr (u ,'is_blank',False )]
                    else :
                        active_units =list (units )

                    total_base_units +=len (active_units )

                    for unit in active_units :
                        unit_mult =particle_auto_multiplier 
                        for loop in loop_chain :
                            l_type =loop .get ('type')
                            if l_type =='maxloop':
                                modo =str (loop .get ('mode','Normal')).strip ().lower ()
                                if 'fbf'in modo or 'frame'in modo :
                                    step_val =loop .get ('step_ms')or loop .get ('val')or 41.7 
                                    try :step_ms =max (1.0 ,float (step_val ))
                                    except Exception :step_ms =41.7 
                                    u_st =float (getattr (unit ,'start_time',getattr (pyxis_line ,'start_time',0.0 )))
                                    u_et =float (getattr (unit ,'end_time',getattr (pyxis_line ,'end_time',0.0 )))
                                    u_dur =max (1.0 ,u_et -u_st )
                                    unit_mult *=max (1 ,int (math .ceil (u_dur /step_ms )))
                                else :
                                    val_raw =loop .get ('iterations')or loop .get ('count')or loop .get ('val')or 1 
                                    try :veces =max (1 ,int (float (val_raw )))
                                    except Exception :veces =1 
                                    unit_mult *=veces 
                            elif l_type =='auto_slicer_loop':
                                auto_n =loop .get ('slices')or 5 
                                unit_mult *=max (1 ,int (auto_n ))
                        total_estimated_lines +=unit_mult 
                else :
                    total_base_units +=1 
                    unit_mult =particle_auto_multiplier 
                    for loop in loop_chain :
                        l_type =loop .get ('type')
                        if l_type =='maxloop':
                            modo =str (loop .get ('mode','Normal')).strip ().lower ()
                            if 'fbf'in modo or 'frame'in modo :
                                step_val =loop .get ('step_ms')or loop .get ('val')or 41.7 
                                try :step_ms =max (1.0 ,float (step_val ))
                                except Exception :step_ms =41.7 
                                l_st =float (getattr (pyxis_line ,'start_time',0.0 ))
                                l_et =float (getattr (pyxis_line ,'end_time',0.0 ))
                                l_dur =max (1.0 ,l_et -l_st )
                                unit_mult *=max (1 ,int (math .ceil (l_dur /step_ms )))
                            else :
                                val_raw =loop .get ('iterations')or loop .get ('count')or loop .get ('val')or 1 
                                try :veces =max (1 ,int (float (val_raw )))
                                except Exception :veces =1 
                                unit_mult *=veces 
                        elif l_type =='auto_slicer_loop':
                            auto_n =loop .get ('slices')or 5 
                            unit_mult *=max (1 ,int (auto_n ))
                    total_estimated_lines +=unit_mult 

        if total_estimated_lines <2000 :
            complexity ="Baja"
            complexity_key ="low"
            complexity_color ="#34d399"
        elif total_estimated_lines <15000 :
            complexity ="Normal"
            complexity_key ="normal"
            complexity_color ="#60a5fa"
        elif total_estimated_lines <50000 :
            complexity ="Alta"
            complexity_key ="high"
            complexity_color ="#fbbf24"
        else :
            complexity ="Extrema"
            complexity_key ="extreme"
            complexity_color ="#f87171"

        return {
        "estimated_lines":total_estimated_lines ,
        "input_lines":len (selected_lines_list ),
        "base_units":total_base_units ,
        "output_nodes_count":len (output_nodes ),
        "has_particles":has_particles ,
        "has_scripts":has_scripts ,
        "has_audio":has_audio ,
        "complexity":complexity ,
        "complexity_key":complexity_key ,
        "complexity_color":complexity_color ,
        "is_heavy":total_estimated_lines >=30000 
        }

    def process_single (self ,dialogue_items ,styles ,progress_callback =None ,check_cancel_callback =None ,allow_fallback_select_all =True ,global_selected_styles =None ,chunk_indices =None ):
        """Ejecución secuencial en un solo proceso/hilo para un bloque de líneas."""
        self .all_generated_lines =[]
        self .is_cancelled =False 
        from particle_nodes import clear_particle_caches 
        from nodes .shape_nodes import clear_shape_array_caches, clear_multi_caches 
        clear_shape_array_caches ()
        clear_multi_caches ()

        if hasattr (self ,'target_output_id')and self .target_output_id is not None :
            if isinstance (self .target_output_id ,(list ,tuple ,set )):
                raw_list =[]
                for item in self .target_output_id :
                    if item is not None :
                        for s in str (item ).split (','):
                            s_clean =s .strip ()
                            if s_clean :
                                raw_list .append (s_clean )
                target_ids =set (raw_list )
            else :
                raw_list =[s .strip ()for s in str (self .target_output_id ).split (',')if s .strip ()]
                target_ids =set (raw_list )

            all_salida_nodes =[node for node in self .nodes .values ()if 'salida'in str (node .get ('type','')).lower ()or 'output'in str (node .get ('type','')).lower ()]

            numeric_targets =set ()
            for t in target_ids :
                try :
                    numeric_targets .add (int (t ))
                except (ValueError ,TypeError ):
                    pass 

            def _matches_output (n ):
                n_type =str (n .get ('type','')).lower ()
                if 'salida'not in n_type and 'output'not in n_type :
                    return False 

                nid_str =str (n .get ('id',''))
                nid_int =n .get ('id')
                node_title =str (n .get ('title')or '').strip ()
                props =n .get ('properties',{})or {}
                out_id =str (props .get ('output_id')or props .get ('salida_id')or '').strip ()
                queue_id =str (props .get ('queue_id')or '').strip ()

                if any (x .lower ()in ('all','*','todos','all_outputs','todas')for x in target_ids ):
                    return True 

                if nid_str in target_ids :
                    return True 
                if nid_int is not None and nid_int in numeric_targets :
                    return True 
                if node_title and node_title in target_ids :
                    return True 

                if out_id and (out_id in target_ids or (_to_int_or_default (out_id ,None )in numeric_targets )):
                    return True 
                if queue_id and (queue_id in target_ids or (_to_int_or_default (queue_id ,None )in numeric_targets )):
                    return True 

                if n in all_salida_nodes :
                    idx_1based =all_salida_nodes .index (n )+1 
                    if (str (idx_1based )in target_ids or 
                    idx_1based in numeric_targets or 
                    f"Salida {idx_1based }"in target_ids or 
                    f"Salida_{idx_1based }"in target_ids or 
                    f"Salida {idx_1based }".lower ()in (x .lower ()for x in target_ids )or 
                    f"Salida_{idx_1based }".lower ()in (x .lower ()for x in target_ids )or 
                    f"Output {idx_1based }"in target_ids or 
                    f"Output_{idx_1based }"in target_ids or 
                    f"Output {idx_1based }".lower ()in (x .lower ()for x in target_ids )or 
                    f"Output_{idx_1based }".lower ()in (x .lower ()for x in target_ids )):
                        return True 

                if 'default'in target_ids and (not out_id or out_id =='default'):
                    return True 

                return False 

            output_nodes =[n for n in self .nodes .values ()if _matches_output (n )]
        else :
            output_nodes =[n for n in self .nodes .values ()if 'salida'in str (n .get ('type','')).lower ()or 'output'in str (n .get ('type','')).lower ()]

        def _get_node_sort_key (node ):
            props =node .get ('properties',{})
            q_ord =None 
            for k in ['queue_order','orden_cola','orden','order','Queue Order','Queue_Order']:
                if k in props and not _is_empty_value (props [k ]):
                    q_ord =props [k ]
                    break 
            return (_to_int_or_default (q_ord ,0 ),_to_int_or_default (node .get ('id',0 ),0 ))

        output_nodes =sorted (output_nodes ,key =_get_node_sort_key )
        self ._once_cache ={}

        from ass_parser import KaraokeProcessor 
        processor =KaraokeProcessor (self .rx ,self .ry ,self .fd )

        parsed_lines =[]
        selected_styles =set (global_selected_styles )if global_selected_styles is not None else set ()

        for idx ,item in enumerate (dialogue_items ,1 ):
            raw_line =item ['raw']if isinstance (item ,dict )else getattr (item ,'raw','')
            metrics =item .get ('metrics')if isinstance (item ,dict )else getattr (item ,'metrics',None )
            style_name =raw_line .split (',')[3 ]if ','in raw_line else ''
            pyxis_line =processor .process_line (raw_line ,styles .get (style_name ,{}),metrics )
            if pyxis_line :
                if isinstance (item ,dict )and 'i'in item :
                    pyxis_line .i =item ['i']
                elif hasattr (item ,'i')and not isinstance (item ,dict ):
                    pyxis_line .i =item .i 
                else :
                    pyxis_line .i =idx 
                
                is_item_selected = bool(
                    (isinstance(item, dict) and (item.get('is_selected') or (isinstance(item.get('metrics'), dict) and item['metrics'].get('sel'))))
                    or getattr(item, 'is_selected', False)
                    or getattr(pyxis_line, 'is_selected', False)
                )
                pyxis_line.is_selected = is_item_selected

                parsed_lines .append (pyxis_line )
                if not getattr(pyxis_line, 'is_comment', False) and pyxis_line .is_selected :
                    selected_styles .add (pyxis_line .style_name )

        selected_lines_list =[l for l in parsed_lines if l .is_selected and not getattr(l, 'is_comment', False)]
        if not selected_lines_list and allow_fallback_select_all :
            for l in parsed_lines :
                if not getattr(l, 'is_comment', False):
                    l .is_selected =True 
            selected_lines_list =[l for l in parsed_lines if not getattr(l, 'is_comment', False)]




        total_work_units =0 
        for out_node in output_nodes :
            props =out_node .get ('properties',{})
            apply_to =props .get ('apply_to','Selected Lines')
            loop_chain =self .trace_loop_chain (out_node )
            if not loop_chain :continue 

            base_loop =next ((l for l in loop_chain if l ['type']=='base'),None )
            base_type =base_loop ['val']if base_loop else 'line'
            _nb_str3 = str(
            (base_loop .get ('noblank')if base_loop else '')or 
            (base_loop .get ('properties',{}).get ('noblank')if base_loop else '')or 
            props .get ('noblank','No Blank')
            )
            is_noblank = "Con Blanks" not in _nb_str3 and "With" not in _nb_str3

            for pyxis_line in parsed_lines :
                if getattr(pyxis_line, 'is_comment', False): continue
                if chunk_indices is not None and getattr(pyxis_line, 'i', None) not in chunk_indices: continue
                if apply_to in ["Selected Lines","Sel. Lines"]and not pyxis_line .is_selected :continue 
                if apply_to =="Style Lines"and pyxis_line .style_name not in selected_styles :continue 

                if base_type in ['syl','char','word']:
                    units =getattr (pyxis_line ,base_type +"s",[])
                    if is_noblank :
                        cnt =sum (1 for u in units if not getattr (u ,'is_blank',False )and _has_visible_content (u ))
                    else :
                        cnt =sum (1 for u in units if _has_visible_content (u ))
                    total_work_units +=max (1 ,cnt )
                else :
                    total_work_units +=1 

        if total_work_units <1 :
            total_work_units =1 

        progress_tracker ={'current':0 ,'total':total_work_units ,'last_pct':0 ,'last_time':0.0 }

        for out_node in output_nodes :
            if self .is_cancelled :break 
            props =out_node .get ('properties',{})
            apply_to =props .get ('apply_to','Selected Lines')
            loop_chain =self .trace_loop_chain (out_node )
            if not loop_chain :continue 

            if apply_to in ["Selected Lines", "Sel. Lines"]:
                target_lines_list = selected_lines_list
            elif apply_to == "Style Lines":
                target_lines_list = [l for l in parsed_lines if not getattr(l, 'is_comment', False) and l.style_name in selected_styles]
            else:
                target_lines_list = [l for l in parsed_lines if not getattr(l, 'is_comment', False)]

            for pyxis_line in parsed_lines :
                if self .is_cancelled :break 
                if getattr(pyxis_line, 'is_comment', False): continue
                if chunk_indices is not None and getattr(pyxis_line, 'i', None) not in chunk_indices: continue
                if apply_to in ["Selected Lines","Sel. Lines"]and not pyxis_line .is_selected :continue 
                if apply_to =="Style Lines"and pyxis_line .style_name not in selected_styles :continue 
                self .execute_loops_recursive (
                loop_chain ,
                {'line':pyxis_line ,'processor':processor ,'all_lines':parsed_lines ,'selected_lines':selected_lines_list ,'target_lines':target_lines_list },
                out_node ,
                None ,
                check_cancel_callback ,
                progress_tracker ,
                progress_callback 
                )


        if getattr (self ,'_local_line_batch',0 )>0 :
            if getattr (self ,'shared_line_counter',None )is not None :
                try :
                    with self .shared_line_counter .get_lock ():
                        self .shared_line_counter .value +=self ._local_line_batch 
                except Exception :
                    pass 
            self ._local_line_batch =0 
        return self .all_generated_lines 

    def process (self ,dialogue_items ,styles ,progress_callback =None ,check_cancel_callback =None ,use_multiprocessing =True ):
        self .all_generated_lines =[]
        self .is_cancelled =False 

        cpu_cores =os .cpu_count ()or 1 
        num_items =len (dialogue_items )


        from particle_nodes import _GLOBAL_PARTICLE_PTS_CACHE ,_GLOBAL_PARTICLE_IMG_CACHE 
        for n_id ,n_obj in self .nodes .items ():
            n_type =n_obj .get ('type','')
            if any (k in n_type for k in ['IMG to pixels','Imagen a Partículas','Particles','Contorno']):
                try :
                    self .evaluate_data_node (n_id ,{'j':1 ,'i':1 })
                except Exception :
                    pass 

        cached_particle_data =(_GLOBAL_PARTICLE_PTS_CACHE .copy (),_GLOBAL_PARTICLE_IMG_CACHE .copy ())


        has_any_selection =any (
        bool (
        (isinstance (d ,dict )and (d .get ('is_selected')or (isinstance (d .get ('metrics'),dict )and d ['metrics'].get ('sel'))))
        or getattr (d ,'is_selected',False )
        )
        for d in dialogue_items 
        if not (
            (isinstance (d ,dict )and (str (d .get ('raw','')).strip ().startswith ('Comment:')or str (d .get ('raw','')).strip ().startswith ('Comment :')))
            or getattr (d ,'is_comment',False )
        )
        )
        allow_fallback_select_all =not has_any_selection 

        global_selected_styles =set ()
        for item in dialogue_items :
            raw_line =item ['raw']if isinstance (item ,dict )else getattr (item ,'raw','')
            if str (raw_line ).strip ().startswith ('Comment:')or str (raw_line ).strip ().startswith ('Comment :')or getattr (item ,'is_comment',False ):
                continue 
            style_name =raw_line .split (',')[3 ]if ','in raw_line else ''
            is_sel =bool (
            (isinstance (item ,dict )and (item .get ('is_selected')or (isinstance (item .get ('metrics'),dict )and item ['metrics'].get ('sel'))))
            or getattr (item ,'is_selected',False )
            )
            if (is_sel or allow_fallback_select_all )and style_name :
                global_selected_styles .add (style_name )

        for idx, item in enumerate(dialogue_items, 1):
            if isinstance(item, dict):
                if 'i' not in item:
                    item['i'] = idx
            else:
                if not hasattr(item, 'i'):
                    setattr(item, 'i', idx)

        if use_multiprocessing and num_items >1 and cpu_cores >1 :
            stop_monitor =threading .Event ()
            monitor_th =None 
            try :
                max_workers =min (cpu_cores ,num_items )
                chunk_size =max (1 ,math .ceil (num_items /max_workers ))

                shared_line_counter =multiprocessing .Value ('i',0 )
                shared_cancel_flag =multiprocessing .Value ('b',False )
                self .shared_line_counter =shared_line_counter 
                self .shared_cancel_flag =shared_cancel_flag 

                target_out =getattr (self ,'target_output_id',None )
                payloads =[]
                for i in range (0 ,num_items ,chunk_size ):
                    chunk_slice =dialogue_items [i :i +chunk_size ]
                    chunk_indices =set (
                        (item ['i']if isinstance (item ,dict )and 'i'in item else getattr (item ,'i',idx_fallback ))
                        for idx_fallback ,item in enumerate (chunk_slice ,i +1 )
                    )
                    payloads .append ((
                        getattr (self ,'raw_graph',{}),
                        self .rx ,
                        self .ry ,
                        self .fd ,
                        self .default_audio_source ,
                        dialogue_items ,
                        styles ,
                        cached_particle_data ,
                        target_out ,
                        allow_fallback_select_all ,
                        list (global_selected_styles ),
                        chunk_indices 
                    ))


                est_info =self .estimate_workload (dialogue_items ,styles ,allow_fallback_select_all =allow_fallback_select_all ,global_selected_styles =global_selected_styles )
                est_lines =max (10 ,est_info .get ('estimated_lines',100 ))

                t_loop_start =time .perf_counter ()

                def _monitor_progress_loop ():
                    last_c =0 
                    while not stop_monitor .is_set ():
                        stop_monitor .wait (0.033 )
                        if check_cancel_callback and check_cancel_callback ():
                            shared_cancel_flag .value =True 
                            self .is_cancelled =True 
                        if self .is_cancelled :
                            shared_cancel_flag .value =True 

                        c_lines =shared_line_counter .value 
                        t_now =time .perf_counter ()
                        elapsed =max (0.001 ,t_now -t_loop_start )
                        spd =int (c_lines /elapsed )if elapsed >0.05 else 0 
                        has_audio =getattr (self ,'_has_audio_nodes',False )
                        base_p =25 if has_audio else 5 
                        pct =min (89 ,base_p +int ((89 -base_p )*(c_lines /est_lines )))
                        if callable (progress_callback )and (c_lines !=last_c or c_lines >0 ):
                            last_c =c_lines 
                            progress_callback ({
                            "percent":max (base_p ,pct ),
                            "lines_generated":c_lines ,
                            "speed":spd ,
                            "phase":f"Generating... {c_lines :,} lines ({spd } l/s)"if spd >0 else f"Generating... {c_lines :,} lines"
                            })

                monitor_th =threading .Thread (target =_monitor_progress_loop ,daemon =True )
                monitor_th .start ()

                completed_chunks =0 
                total_chunks =len (payloads )

                prof =None 
                if _PROFILER_ENABLED :
                    try :
                        from pyxis_profiler import PyxisProfiler 
                        prof =PyxisProfiler .get_active ()
                    except Exception :
                        prof =None 

                with concurrent .futures .ProcessPoolExecutor (
                max_workers =max_workers ,
                initializer =_worker_init ,
                initargs =(shared_line_counter ,shared_cancel_flag )
                )as pool :
                    global _GLOBAL_ACTIVE_EXECUTOR 
                    _GLOBAL_ACTIVE_EXECUTOR =pool 

                    future_map ={
                    pool .submit (_process_line_chunk_worker ,p ):(i +1 ,len (p [11 ])if len (p )>=12 and p [11 ]is not None else len (p [5 ]),time .perf_counter ())
                    for i ,p in enumerate (payloads )
                    }

                    for future in concurrent .futures .as_completed (future_map ):
                        if self .is_cancelled or (shared_cancel_flag and shared_cancel_flag .value ):
                            break 
                        w_id ,line_cnt ,t_start =future_map [future ]
                        t_end =time .perf_counter ()
                        if prof :
                            prof .record_worker_chunk (w_id ,line_cnt ,t_end -t_start ,t_start ,t_end )
                        try :
                            lines_chunk =future .result ()
                            if lines_chunk :
                                self .all_generated_lines .extend (lines_chunk )
                        except Exception as fe :
                            if not self .is_cancelled :
                                print (f"[Pyxis Worker Exception] {fe }",flush =True )
                        completed_chunks +=1 

            except Exception as mp_err :
                print (f"[Pyxis Multiprocessing Warning] Falling back to sequential mode: {mp_err }",flush =True )
                self .process_single (
                dialogue_items ,
                styles ,
                progress_callback ,
                check_cancel_callback ,
                allow_fallback_select_all =allow_fallback_select_all ,
                global_selected_styles =global_selected_styles 
                )
            finally :
                stop_monitor .set ()
                if monitor_th and monitor_th .is_alive ():
                    monitor_th .join (timeout =0.1 )
                _GLOBAL_ACTIVE_EXECUTOR =None 
        else :
            self .process_single (
            dialogue_items ,
            styles ,
            progress_callback ,
            check_cancel_callback ,
            allow_fallback_select_all =allow_fallback_select_all ,
            global_selected_styles =global_selected_styles 
            )

        total_final_lines =len (self .all_generated_lines )
        if callable (progress_callback ):
            progress_callback ({
            "percent":90 ,
            "lines_generated":total_final_lines ,
            "phase":f"Sorting {total_final_lines } deterministic layers..."
            })

        prof =None 
        if _PROFILER_ENABLED :
            try :
                from pyxis_profiler import PyxisProfiler 
                prof =PyxisProfiler .get_active ()
            except Exception :
                prof =None 

        if prof :
            prof .start_phase ('post_process_sort')


        queues ={}
        for line in self .all_generated_lines :
            qid =line ['queue_id']
            if qid not in queues :queues [qid ]=[]
            queues [qid ].append (line )

        final_lines =[]
        if prof :
            prof .end_phase ('post_process_sort')
            prof .start_phase ('format_ass_lines')

        if callable (progress_callback ):
            progress_callback ({
            "percent":95 ,
            "lines_generated":total_final_lines ,
            "phase":f"Assembling ASS text ({total_final_lines } lines)..."
            })

        for qid in sorted (queues .keys ()):
            queue =sorted (queues [qid ],key =lambda x :(x ['queue_order'],x .get ('line_idx',0 )))
            for line in queue :
                st_val =format_time (int (round (line ['start_time'])))
                et_val =format_time (int (round (line ['end_time'])))
                ass_line =f"Dialogue: {line ['layer']},{st_val },{et_val },{line ['style_name']},{line ['actor']},{line ['margin_l']},{line ['margin_r']},{line ['margin_v']},{line ['effect']},{line ['text']}\n"
                final_lines .append (ass_line )

        if prof :
            prof .end_phase ('format_ass_lines')

        if callable (progress_callback ):
            progress_callback ({
            "percent":100 ,
            "lines_generated":len (final_lines ),
            "phase":"Completed. Transferring to Aegisub..."
            })

        self .used_line_indices = {line ['line_idx'] for line in self .all_generated_lines if line .get ('line_idx')}
        return final_lines 


def _process_line_chunk_worker (payload ):
    """Module-level worker entrypoint for ProcessPoolExecutor parallel workers.
Returns: list of generated line dictionaries for this chunk.
"""
    try :
        target_output_id =None 
        allow_fallback_select_all =True 
        global_selected_styles =None 
        chunk_indices =None 

        if len (payload )>=12 :
            graph_data ,rx ,ry ,fd ,default_audio_source ,all_dialogue_items ,styles ,particle_caches ,target_output_id ,allow_fallback_select_all ,global_selected_styles ,chunk_indices =payload [:12 ]
        elif len (payload )>=11 :
            graph_data ,rx ,ry ,fd ,default_audio_source ,all_dialogue_items ,styles ,particle_caches ,target_output_id ,allow_fallback_select_all ,global_selected_styles =payload [:11 ]
        elif len (payload )>=9 :
            graph_data ,rx ,ry ,fd ,default_audio_source ,all_dialogue_items ,styles ,particle_caches ,target_output_id =payload [:9 ]
        elif len (payload )>=8 :
            graph_data ,rx ,ry ,fd ,default_audio_source ,all_dialogue_items ,styles ,particle_caches =payload [:8 ]
        else :
            graph_data ,rx ,ry ,fd ,default_audio_source ,all_dialogue_items ,styles =payload [:7 ]

        if particle_caches :
            from particle_nodes import _GLOBAL_PARTICLE_PTS_CACHE ,_GLOBAL_PARTICLE_IMG_CACHE 
            _GLOBAL_PARTICLE_PTS_CACHE .update (particle_caches [0 ])
            _GLOBAL_PARTICLE_IMG_CACHE .update (particle_caches [1 ])

        worker_engine =GraphEngine (graph_data ,rx ,ry ,fd ,default_audio_source =default_audio_source )
        worker_engine .shared_line_counter =_WORKER_LINE_COUNTER 
        worker_engine .shared_cancel_flag =_WORKER_CANCEL_FLAG 
        if target_output_id is not None :
            worker_engine .target_output_id =target_output_id 

        def check_worker_cancelled ():
            return bool (_WORKER_CANCEL_FLAG and _WORKER_CANCEL_FLAG .value )

        worker_engine .process_single (
        all_dialogue_items ,
        styles ,
        check_cancel_callback =check_worker_cancelled ,
        allow_fallback_select_all =allow_fallback_select_all ,
        global_selected_styles =global_selected_styles ,
        chunk_indices =chunk_indices 
        )
        return worker_engine .all_generated_lines 
    except Exception as e :
        import traceback 
        print (f"[Pyxis Worker Exception] {traceback .format_exc ()}",flush =True )
        return []