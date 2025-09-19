import os
import shutil
import sys
import subprocess
from tkinter import filedialog

import xlwings as xw
from xlwings.constants import BordersIndex as BI, BorderWeight as BW, LineStyle, HAlign

from doprava import load_doprava_data


def update_excel(selected_items, project_name, notes_text="", definicia_text="", praca_data=None):
    """Generate an Excel report from selected basket items + doprava + práca."""
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

    base_dir = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
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

    try:
        app = xw.App(visible=False)
        wb = xw.Book(new_file)
        sheet = wb.sheets[0]

        # ----- project header -----
        sheet.range("B9:K9").value = [[project_name] * 10]
        sheet.range("B10:K10").value = [[definicia_text] * 10]

        TEMPLATE_ROW = 15
        insert_position = TEMPLATE_ROW
        counter = 1
        prev_section = None
        section_start_row = None
        header_row = None
        try:
            default_row_height = sheet.range(f"{TEMPLATE_ROW+1}:{TEMPLATE_ROW+1}").row_height
        except Exception:
            default_row_height = None

        # ----- položky -----
        for idx, item in enumerate(selected_items):
            section = item[0]
            if section != prev_section:
                if prev_section is not None:
                    sheet.range(f"{insert_position}:{insert_position}").insert("down")
                    sheet.range(f"{insert_position}:{insert_position}").row_height = 9.75
                    insert_position += 1
                sheet.range(f"{insert_position}:{insert_position}").insert("down")
                if default_row_height:
                    sheet.range(f"{insert_position}:{insert_position}").row_height = default_row_height
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
            odkaz = item[4]
            koef_material = float(item[5])
            nakup_materialu = float(item[7])
            pocet_materialu = int(item[9]) if len(item) > 9 else 1

            sheet.range(f"{insert_position}:{insert_position}").insert("down")
            src = sheet.range(f"{TEMPLATE_ROW+1}:{TEMPLATE_ROW+1}")
            dst = sheet.range(f"{insert_position}:{insert_position}")
            src.api.Copy()
            dst.api.PasteSpecial(Paste=-4163)
            sheet.range(f"{insert_position}:{insert_position}").api.Font.Bold = False

            sheet.cells(insert_position, 2).value = counter
            sheet.cells(insert_position, 3).value = produkt
            sheet.cells(insert_position, 4).value = jednotky
            sheet.cells(insert_position, 5).value = pocet_materialu
            sheet.cells(insert_position, 6).value = f"=N{insert_position}*M{insert_position}"
            sheet.cells(insert_position, 7).value = f"=F{insert_position}*E{insert_position}"
            sheet.cells(insert_position, 8).value = pocet_materialu
            sheet.cells(insert_position, 9).value = nakup_materialu
            sheet.cells(insert_position, 10).value = f"=I{insert_position}*H{insert_position}"
            sheet.cells(insert_position, 11).value = f"=G{insert_position}+J{insert_position}"
            sheet.cells(insert_position, 13).value = koef_material
            sheet.cells(insert_position, 14).value = nakup_materialu
            sheet.cells(insert_position, 15).value = f"=N{insert_position}*E{insert_position}"
            sheet.cells(insert_position, 16).value = f"=G{insert_position}-O{insert_position}"
            sheet.cells(insert_position, 17).value = f"=P{insert_position}/G{insert_position}"
            sheet.cells(insert_position, 19).value = dodavatel
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
                sheet.range(f"{insert_position}:{insert_position}").insert("down")
                if default_row_height:
                    sheet.range(f"{insert_position}:{insert_position}").row_height = default_row_height
                sheet.cells(insert_position, 2).value = section + " spolu"
                row_range = sheet.range(f"{insert_position}:{insert_position}")
                row_range.api.Font.Bold = True
                row_range.api.Font.Size = 12
                row_range.api.HorizontalAlignment = HAlign.xlHAlignLeft

                last_item_row = insert_position - 1
                sheet.cells(insert_position, 6).value = "Materiál"
                sheet.cells(insert_position, 7).value = f"=SUM(G{section_start_row}:G{last_item_row})"
                sheet.cells(insert_position, 9).value = "Práca"
                sheet.cells(insert_position, 10).value = f"=SUM(J{section_start_row}:J{last_item_row})"
                sheet.cells(insert_position, 11).value = f"=ROUNDUP(SUM(K{section_start_row}:K{last_item_row}),0)"
                insert_position += 1

                section_end_row = insert_position - 1
                rng = sheet.range(f"B{header_row}:K{section_end_row}")
                for edge in (BI.xlEdgeLeft, BI.xlEdgeTop, BI.xlEdgeBottom, BI.xlEdgeRight):
                    br = rng.api.Borders(edge)
                    br.LineStyle = LineStyle.xlContinuous
                    br.Weight = BW.xlMedium
                for inner in (BI.xlInsideVertical, BI.xlInsideHorizontal):
                    br = rng.api.Borders(inner)
                    br.LineStyle = LineStyle.xlContinuous
                    br.Weight = BW.xlThin

        # ----- poznámky -----
        if notes_text:
            try:
                notes_sheet = wb.sheets.add(after=sheet)
                notes_sheet.name = "Poznámky"
                for i, line in enumerate(notes_text.splitlines(), start=1):
                    notes_sheet.cells(i, 1).value = line
            except Exception as e:
                print("⚠ Failed to add notes sheet:", e)

        # ----- práca -----
        if praca_data:
            start_row = 28
            start_col = 13  # Column J

            print("[DEBUG] praca_data:", praca_data)

            

            for r_idx, row in enumerate(praca_data, start=start_row + 1):
                filtered = [row[0], row[1], row[2], row[3], row[4], row[6]]  
                for c_idx, val in enumerate(filtered):
                    sheet.cells(r_idx, start_col + c_idx).value = val
           
        # ----- doprava -----
        doprava_data = load_doprava_data()
        if doprava_data:
            row = 25
            cena_vyjazd, pocet_vyjazdov, cena_ba, cena_km, cena_mimo = doprava_data
            sheet.cells(row, 13).value = cena_vyjazd     # M = 1 výjazd v BA
            sheet.cells(row, 14).value = pocet_vyjazdov  # N = počet výjazdov
            sheet.cells(row, 15).value = cena_ba         # O = celková cena BA
            sheet.cells(row, 16).value = cena_km         # P = €/km mimo BA
            sheet.cells(row, 17).value = cena_mimo       # Q = celková cena mimo BA

        wb.save()
        wb.close()
        app.quit()
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
