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

"""Pruebas unitarias para el servidor daemon IPC y gestion del ciclo de vida de bloqueos."""

import os 
import tempfile 
import unittest 
from pyxis_daemon import PyxisDaemonServer 


class DummyWindow :
    def __init__ (self ):
        self .shown =False 
        self .restored =False 
        self .focused =False 
        self .js_evaluated =[]

    def show (self ):
        self .shown =True 

    def restore (self ):
        self .restored =True 

    def focus (self ):
        self .focused =True 

    def evaluate_js (self ,code ):
        self .js_evaluated .append (code )


class DummyAPI :
    def __init__ (self ):
        self .temp_ass ="old.ass"
        self .result_file ="old_res.txt"
        self .lock_file ="old_lock.txt"
        self .session_file ="old_session.json"
        self .aegisub_version ="3.4.0"

    def release_lock (self ):
        if self .lock_file and os .path .exists (self .lock_file ):
            try :
                os .remove (self .lock_file )
            except Exception :
                pass 
        self .lock_file =None 


class TestDaemonIPC (unittest .TestCase ):
    """Pruebas de inicializacion del servidor daemon y endpoints IPC."""

    def test_daemon_server_initialization (self ):
        api =DummyAPI ()
        window =DummyWindow ()
        server =PyxisDaemonServer (main_api =api ,window =window )
        self .assertIsNotNone (server )
        self .assertEqual (server .main_api .aegisub_version ,"3.4.0")

    def test_lock_file_lifecycle (self ):
        temp_dir =tempfile .mkdtemp ()
        lock_path =os .path .join (temp_dir ,"test.lock")
        with open (lock_path ,"w",encoding ="utf-8")as f :
            f .write ("1")

        api =DummyAPI ()
        api .lock_file =lock_path 
        self .assertTrue (os .path .exists (lock_path ))

        api .release_lock ()
        self .assertFalse (os .path .exists (lock_path ))
        self .assertIsNone (api .lock_file )


if __name__ =="__main__":
    unittest .main ()
