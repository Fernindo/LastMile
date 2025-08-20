import sys
import os
import datetime
import argparse
import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar, Frame, Label, Button

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--meno", type=str, default="", help="Meno prihláseného používateľa")
    parser.add_argument("--priezvisko", type=str, default="", help="Priezvisko prihláseného používateľa")
    parser.add_argument("--open-latest", action="store_true", help="Pri štarte automaticky otvoriť najnovší projekt")
    # Ignoruj neznáme argumenty, aby to nepadalo pri balení do exe
    args, _ = parser.parse_known_args()
    return args

def main():
    args = parse_args()

    # Determine base directory (where launcher.py or launcher.exe lives)
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Look for the "projects" folder
    projects_dir = os.path.join(base_dir, "projects")
    if not os.path.isdir(projects_dir):
        messagebox.showerror("Chyba", "Chýba priečinok 'projects' pri launcheri.")
        sys.exit(1)

    # Build main window
    root = tk.Tk()
    root.title("📁 Archív projektov")
    root.geometry("460x520")
    root.configure(bg="#f0f4f8")

    # Title and description
    Label(root, text="Vyber projekt pre otvorenie", font=("Segoe UI", 14, "bold"), bg="#f0f4f8").pack(pady=(20, 6))
    if args.priezvisko or args.meno:
        Label(root,
              text=f"Prihlásený: {args.priezvisko} {args.meno[:1] + '.' if args.meno else ''}",
              font=("Segoe UI", 10),
              fg="#333",
              bg="#f0f4f8").pack(pady=(0, 6))

    # Frame for listbox + scrollbar
    list_frame = Frame(root, bg="#f0f4f8")
    list_frame.pack(fill="both", expand=True, padx=20, pady=10)

    lb = Listbox(
        list_frame,
        width=48,
        height=20,
        font=("Segoe UI", 10),
        bg="white",
        fg="black",
        highlightthickness=1,
        highlightcolor="#0078D7",
        selectbackground="#0078D7",
        selectforeground="white",
        activestyle="none"
    )
    lb.pack(side="left", fill="both", expand=True)

    sb = Scrollbar(list_frame, orient="vertical", command=lb.yview)
    sb.pack(side="right", fill="y")
    lb.config(yscrollcommand=sb.set)

    # Close button
    Button(root, text="Zavrieť", command=root.destroy, font=("Segoe UI", 10), bg="#e0e0e0", relief="flat").pack(pady=(5, 15))

    # On double click
    def on_open(evt=None, idx=None):
        sel = lb.curselection() if idx is None else (idx,)
        if not sel:
            return
        display = lb.get(sel[0]).strip()

        # odstráň prípadný podpis " — Priezvisko M."
        if " — " in display:
            core = display.split(" — ", 1)[0]
        else:
            core = display

        if " | " in core:
            date_part, base = [s.strip() for s in core.split("|", 1)]
            json_file = f"{base}_{date_part}.json"
        else:
            base = core
            json_file = f"{base}.json"

        json_path = os.path.join(projects_dir, json_file)
        root.destroy()
        import gui
        gui.start(base_dir, json_path)

    lb.bind("<Double-1>", on_open)

    # Load JSON files
    files = [f for f in os.listdir(projects_dir) if f.lower().endswith(".json")]

    def sort_key(fname: str) -> float:
        """Return a timestamp to sort project files by newest first."""
        name, _ = os.path.splitext(fname)
        if "_" in name:
            _, date_part = name.split("_", 1)
            try:
                dt = datetime.datetime.strptime(date_part, "%Y-%m-%d_%H-%M-%S")
                return dt.timestamp()
            except ValueError:
                pass
        return os.path.getmtime(os.path.join(projects_dir, fname))

    files.sort(key=sort_key, reverse=True)

    # Build display list; prvá (najnovšia) dostane podpis priezvisko + iniciála
    display_items = []
    for i, f in enumerate(files):
        name, _ = os.path.splitext(f)
        if "_" in name:
            base, date_part = name.split("_", 1)
            display = f"{date_part} | {base}"
        else:
            display = name

        if i == 0 and (args.priezvisko or args.meno):
            who = f"{args.priezvisko} {args.meno[:1] + '.' if args.meno else ''}".strip()
            display = f"{display} — {who}"
        display_items.append(display)
        lb.insert(tk.END, display)

    # Auto-open latest if requested
    if args.open_latest and display_items:
        root.after(100, lambda: on_open(idx=0))

    root.mainloop()

if __name__ == "__main__":
    main()
