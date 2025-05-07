import ttkbootstrap as tb

def create_main_window():
    """
    Vytvorí hlavné okno s modernou Bootstrap témou.
    Dostupné témy: 'flatly', 'darkly', 'minty', 'journal', 'solar', ...
    """
    return tb.Window(themename="flatly")

def apply_custom_styles(window):
    """
    Aplikuje vlastné štýly na widgety, ako sú veľkosť fontu v tabuľkách a tlačidlách.
    """
    style = window.style

    # Zvýšenie veľkosti písma v hlavnej tabuľke (Treeview)
    style.configure("Treeview", font=("Segoe UI", 12))
    style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))

    # Zvýšenie veľkosti písma tlačidiel
    style.configure("TButton", font=("Segoe UI", 11, "bold"))

    # Prípadne môžeš upraviť aj ostatné widgety (Label, Entry, atď.)
    style.configure("TLabel", font=("Segoe UI", 11))
    style.configure("TEntry", font=("Segoe UI", 11))
