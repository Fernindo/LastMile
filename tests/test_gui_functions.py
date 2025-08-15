import sys
import types
from pathlib import Path

# Stub external dependencies before importing application modules
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

# Add application directory to path
ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / 'one folder to rule them all' / 'Hlavna aplikacia'
sys.path.append(str(APP_DIR))

from gui_functions import remove_accents


def test_remove_accents():
    text = "Pôvodný názov"
    assert remove_accents(text) == "Povodny nazov"


def test_remove_accents_handles_non_string():
    assert remove_accents(None) == ""
    assert remove_accents(123) == "123"
