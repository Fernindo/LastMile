import os
import shutil
import sys
import subprocess
from tkinter import filedialog
from urllib.parse import urlparse
from typing import Optional

import xlwings as xw
from xlwings.constants import BordersIndex as BI, BorderWeight as BW, LineStyle, HAlign


def _normalize_url(url: str) -> Optional[str]:
    """Return a normalized URL or None if invalid."""
    if not url:
        return None
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "http://" + url
        parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return url
    return None


def update_excel(selected_items, project_name, notes_text="", definicia_text="", praca_data=None):
    """Generate an Excel report from selected basket items."""
    if not selected_items:
        print("⚠ No items selected for Excel.")
        return

    filetypes = [("Excel files", "*.xlsx"), ("All files", "*.*")]
    new_file = filedialog.asksaveasfilename(
        title="Exportovať do Excelu",
        defaultextension=".xlsx",
        filetypes=filetypes,
        initialfile=f"{project_name}.xlsx",
    )
    if not new_file:
        print("❌ Export zrušený používateľom.")
        return

    base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(base_dir, "CPINT.xlsx")
    if not os.path.exists(template_file):
        print(f"❌ Template file not found at: {template_file}")
        return

    try:
        shutil.copy(template_file, new_file)
    except Exception as e:
        print("❌ Failed to copy template.")
        print(f"🔍 Error: {e}")
        return

    app = xw.App(visible=False)
    wb = None
    original_display_alerts = app.display_alerts
    original_screen_updating = app.screen_updating
    original_calculation = app.calculation
    app.display_alerts = False
    app.screen_updating = False
    app.calculation = "manual"

    try:
        wb = xw.Book(new_file)
        sheet = wb.sheets[0]

        sheet.range("B9:K9").value = [[project_name] * 10]
        sheet.range("B10:K10").value = [[definicia_text] * 10]

        TEMPLATE_ROW = 18
        insert_position = TEMPLATE_ROW
        counter = 1
        prev_section = None
        section_start_row = None
        header_row = None

        for idx, item in enumerate(selected_items):
            section = item[0]
            if section != prev_section:
                if prev_section is not None:
                    sheet.range(f"{insert_position}:{insert_position}").insert('down')
                    insert_position += 1
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                sheet.cells(insert_position, 2).value = section
                row_range = sheet.range(f"{insert_position}:{insert_position}")
                row_range.api.Font.Bold = True
                row_range.api.Font.Size = 12
                row_range.api.HorizontalAlignment = HAlign.xlHAlignLeft
                header_row = insert_position
                insert_position += 1
                section_start_row = insert_position
                prev_section = section

            produkt = item[1]
            jednotky = item[2]
            dodavatel = item[3]
            odkaz = _normalize_url(item[4])
            koef_material = float(item[5])
            nakup_materialu = float(item[7])
            pocet_materialu = int(item[9]) if len(item) > 9 else 1

            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            src = sheet.range(f"{TEMPLATE_ROW+1}:{TEMPLATE_ROW+1}")
            dst = sheet.range(f"{insert_position}:{insert_position}")
            src.api.Copy()
            dst.api.PasteSpecial(Paste=-4163)
            sheet.range(f"{insert_position}:{insert_position}").api.Font.Bold = False

            row_values = [
                counter,
                produkt,
                jednotky,
                pocet_materialu,
                f"=N{insert_position}*M{insert_position}",
                f"=F{insert_position}*E{insert_position}",
                pocet_materialu,
                nakup_materialu,
                f"=I{insert_position}*H{insert_position}",
                f"=G{insert_position}+J{insert_position}",
                None,
                koef_material,
                nakup_materialu,
                f"=N{insert_position}*E{insert_position}",
                f"=G{insert_position}-O{insert_position}",
                f"=P{insert_position}+G{insert_position}",
                None,
                dodavatel,
            ]
            sheet.range((insert_position, 2), (insert_position, 19)).value = row_values
            row_rng = sheet.range((insert_position, 2), (insert_position, 19))
            row_rng.api.Font.Size = 9
            sheet.cells(insert_position, 2).api.HorizontalAlignment = HAlign.xlHAlignLeft
            if odkaz:
                sheet.cells(insert_position, 19).api.Hyperlinks.Add(
                    Anchor=sheet.cells(insert_position, 19).api,
                    Address=odkaz,
                    TextToDisplay="Link",
                )

            counter += 1
            insert_position += 1

            next_section = selected_items[idx + 1][0] if idx + 1 < len(selected_items) else None
            if next_section != section:
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                sum_values = [
                    section + "spolu",
                    None,
                    None,
                    None,
                    "Materiál",
                    f"=SUM(G{section_start_row}:G{insert_position - 1})",
                    None,
                    "Práca",
                    f"=SUM(J{section_start_row}:J{insert_position - 1})",
                    f"=ROUNDUP(SUM(K{section_start_row}:K{insert_position - 1}),0)",
                ]
                sheet.range((insert_position, 2), (insert_position, 11)).value = sum_values
                row_range = sheet.range(f"{insert_position}:{insert_position}")
                row_range.api.Font.Bold = True
                row_range.api.Font.Size = 12
                row_range.api.HorizontalAlignment = HAlign.xlHAlignLeft

                insert_position += 1
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                src.api.Copy()
                dst = sheet.range(f"{insert_position}:{insert_position}")
                dst.api.PasteSpecial(Paste=-4122)
                sheet.range(f"{insert_position}:{insert_position}").api.Font.Bold = False
                insert_position += 1

                section_end_row = insert_position - 2
                rng = sheet.range(f"B{header_row}:K{section_end_row}")
                for edge in (BI.xlEdgeLeft, BI.xlEdgeTop, BI.xlEdgeBottom, BI.xlEdgeRight):
                    br = rng.api.Borders(edge)
                    br.LineStyle = LineStyle.xlContinuous
                    br.Weight = BW.xlMedium
                for inner in (BI.xlInsideVertical, BI.xlInsideHorizontal):
                    br = rng.api.Borders(inner)
                    br.LineStyle = LineStyle.xlContinuous
                    br.Weight = BW.xlThin

        if notes_text:
            try:
                notes_sheet = wb.sheets.add(after=sheet)
                notes_sheet.name = "Poznámky"
                lines = notes_text.splitlines()
                notes_sheet.range((1, 1), (len(lines), 1)).value = [[line] for line in lines]
            except Exception as e:
                print("⚠ Failed to add notes sheet:", e)

        if praca_data:
            start_row = 44
            start_col = 10  # Column J
            headers = ["Rola", "Počet osôb", "Hodiny", "Plat/h", "Spolu", "Koef.", "Predaj"]
            sheet.range((start_row, start_col), (start_row, start_col + len(headers) - 1)).value = [headers]
            sheet.range(
                (start_row + 1, start_col),
                (start_row + len(praca_data), start_col + len(headers) - 1),
            ).value = praca_data

        wb.save()
        print(f"✅ Successfully exported to: {new_file}")
        try:
            if sys.platform.startswith("darwin"):
                subprocess.Popen(["open", new_file])
            elif os.name == "nt":
                os.startfile(new_file)
            else:
                subprocess.Popen(["xdg-open", new_file])
        except Exception as e:
            print(f"⚠ Unable to open the file: {e}")

    except Exception as e:
        print("❌ Failed during Excel export.")
        print(f"🔍 Error: {e}")
    finally:
        if wb:
            wb.save()
            wb.close()
        app.display_alerts = original_display_alerts
        app.screen_updating = original_screen_updating
        app.calculation = original_calculation
        app.quit()
