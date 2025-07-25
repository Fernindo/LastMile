import os
import sys
import types
from pathlib import Path

# Add application directory so modules can be imported
APP_DIR = Path(__file__).resolve().parent.parent / "one folder to rule them all" / "Hlavna aplikacia"
sys.path.insert(0, str(APP_DIR))

# Stub heavy dependencies used by gui_functions
sys.modules.setdefault('psycopg2', types.ModuleType('psycopg2'))

ttk_stub = types.ModuleType('ttkbootstrap')
ttk_stub.Button = object
sys.modules.setdefault('ttkbootstrap', ttk_stub)

xl_stub = types.ModuleType('xlwings')
xl_stub.App = object
xl_stub.Book = object
xl_stub.constants = types.SimpleNamespace(
    BordersIndex=None,
    BorderWeight=None,
    LineStyle=None,
    HAlign=None,
)
sys.modules.setdefault('xlwings', xl_stub)
sys.modules.setdefault('xlwings.constants', xl_stub.constants)
