import os
import shutil
import sys
from tkinter import filedialog

import xlwings as xw
from xlwings.constants import BordersIndex as BI, BorderWeight as BW, LineStyle, HAlign


def export_vv(selected_items, project_name, notes_text="", definicia_text="", praca_data=None):
    """Generate a simple Výkaz výmer (VV) Excel report without any prices."""
    if not selected_items:
        print("⚠ No items selected for export.")
        return

    filetypes = [("Excel files", "*.xlsx"), ("All files", "*.*")]
    new_file = filedialog.asksaveasfilename(
        title="Exportovať Výkaz výmer",
        defaultextension=".xlsx",
        filetypes=filetypes,
        initialfile=f"{project_name}_VV.xlsx",
    )
    if not new_file:
        print("❌ Export zrušený používateľom.")
        return

    base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(base_dir, "VV_Template.xlsx") 
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
            pocet_materialu = int(item[9]) if len(item) > 9 else 1

            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            src = sheet.range(f"{TEMPLATE_ROW+1}:{TEMPLATE_ROW+1}")
            dst = sheet.range(f"{insert_position}:{insert_position}")
            src.api.Copy()
            dst.api.PasteSpecial(Paste=-4163)
            sheet.range(f"{insert_position}:{insert_position}").api.Font.Bold = False

            sheet.cells(insert_position, 2).value = counter
            sheet.cells(insert_position, 2).api.HorizontalAlignment = HAlign.xlHAlignLeft
            sheet.cells(insert_position, 2).api.Font.Size = 9

            sheet.cells(insert_position, 3).value = produkt
            sheet.cells(insert_position, 3).api.Font.Size = 9

            sheet.cells(insert_position, 4).value = jednotky
            sheet.cells(insert_position, 4).api.Font.Size = 9

            sheet.cells(insert_position, 5).value = pocet_materialu
            sheet.cells(insert_position, 5).api.Font.Size = 9

            # Namiesto všetkých cien vkladáme nuly
            sheet.cells(insert_position, 6).value = 0
            sheet.cells(insert_position, 7).value = 0
            sheet.cells(insert_position, 8).value = pocet_materialu  # prípadne 0 ak netreba
            sheet.cells(insert_position, 9).value = 0
            sheet.cells(insert_position, 10).value = 0
            sheet.cells(insert_position, 11).value = 0
            sheet.cells(insert_position, 13).value = 0
            sheet.cells(insert_position, 14).value = 0
            sheet.cells(insert_position, 15).value = 0
            sheet.cells(insert_position, 16).value = 0
            sheet.cells(insert_position, 17).value = 0

            sheet.cells(insert_position, 19).value = dodavatel
            sheet.cells(insert_position, 19).api.Font.Size = 9

            counter += 1
            insert_position += 1

            next_section = selected_items[idx + 1][0] if idx + 1 < len(selected_items) else None
            if next_section != section:
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                sheet.cells(insert_position, 2).value = section + "spolu"
                sheet.cells(insert_position, 6).value = "Spolu ks"
                last_item_row = insert_position - 1
                sheet.cells(insert_position, 7).value = f"=SUM(E{section_start_row}:E{last_item_row})"

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

        wb.save()
        wb.close()
        app.quit()
        print(f"✅ Výkaz výmer exportovaný do: {new_file}")

    except Exception as e:
        print("❌ Chyba počas exportu VV.")
        print(f"🔍 Error: {e}")
