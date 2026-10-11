"""Verify control-file throttling without requiring a Rhino process."""
import ast
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import time

class ControlUpdates(unittest.TestCase):
    def test_heartbeat_is_throttled_but_user_actions_write_immediately(self):
        source=ast.parse((Path(__file__).resolve().parents[1]/'rhino/TrackingPanel.py').read_text())
        method=next(n for n in ast.walk(source) if isinstance(n,ast.FunctionDef) and n.name=='write')
        with tempfile.TemporaryDirectory() as root:
            Path(root,'runtime').mkdir()
            scope=dict(ROOT=root,time=time,os=os,json=json)
            exec(compile(ast.Module(body=[method],type_ignores=[]),'<control-write>','exec'),scope)
            panel=types.SimpleNamespace(settings=dict(paused=False))
            clock=iter([10.,10.1,10.25,10.26])
            with patch.object(time,'monotonic',side_effect=lambda:next(clock)):
                scope['write'](panel,False)
                path=Path(root,'runtime/control.json');original=path.read_text()
                panel.settings['paused']=True
                scope['write'](panel,False)
                self.assertEqual(path.read_text(),original)
                scope['write'](panel,False)
                self.assertTrue(json.loads(path.read_text())['paused'])
                panel.settings['stop']=True
                scope['write'](panel)
                self.assertTrue(json.loads(path.read_text())['stop'])
                self.assertFalse(Path(root,'runtime/control.json.tmp').exists())

if __name__=='__main__':unittest.main()
