from gui_functions import remove_accents

def test_remove_accents():
    text = "Pôvodný názov"
    assert remove_accents(text) == "Povodny nazov"
