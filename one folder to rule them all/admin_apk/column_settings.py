import tkinter as tk
import json
import os

# Všetky dostupné stĺpce
ALL_COLUMNS = [
    "produkt", "jednotky", "dodavatel", "odkaz",
    "koeficient", "nakup_materialu", "cena_prace", "class_id"
]

# Súbor na ukladanie nastavení
SETTINGS_FILE = "user_column_settings.json"

def load_user_settings(user_id="default"):
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
            return settings.get(user_id, ALL_COLUMNS)
    return ALL_COLUMNS

def save_user_settings(selected_columns, user_id="default"):
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    else:
        settings = {}
    settings[user_id] = selected_columns
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def column_selector_ui(frame, on_change_callback, user_id="default"):
    selected_columns = load_user_settings(user_id)
    check_vars = {}

    for i, col in enumerate(ALL_COLUMNS):
        var = tk.BooleanVar(value=col in selected_columns)
        check_vars[col] = var
        chk = tk.Checkbutton(frame, text=col, variable=var,
                             command=lambda: on_change_callback(get_selected_columns(check_vars, user_id)))
        chk.grid(row=0, column=i, sticky="w")
        check_vars[col] = var

    return check_vars

def get_selected_columns(check_vars, user_id="default"):
    selected = [col for col, var in check_vars.items() if var.get()]
    save_user_settings(selected, user_id)
    return selected
