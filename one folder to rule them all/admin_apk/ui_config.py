import ttkbootstrap as tb

def create_main_window():
    return tb.Window(themename="flatly")  # alebo 'darkly', 'minty', 'solar', 'journal', 'flatly'

def apply_custom_styles(window):
    style = window.style
    style.configure("Treeview", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10, "bold"))
    style.configure("TLabel", font=("Segoe UI", 10))
    style.configure("TEntry", font=("Segoe UI", 10))
