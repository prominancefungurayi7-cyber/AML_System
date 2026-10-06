"""Invoke with isolated interpreter -I -B; explicit one-shot local API only."""
from pathlib import Path
import runpy
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
runpy.run_module('ml_v4.frozen_inference.cli',run_name='__main__')
