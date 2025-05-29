import xlwings as xw
import os
import shutil
import sys

def update_excel(selected_items, new_file, notes_text=""):
    if not selected_items:
        print("⚠ No items selected for Excel.")
        return

    if not new_file:
        print("❌ No export path provided.")
        return

    # ─── Locate template ─────────────────────────────────────────────────────
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    template_file = os.path.join(base_dir, "Vzorova_CP3.xlsx")
    if not os.path.exists(template_file):
        print(f"❌ Template file not found at: {template_file}")
        print("Make sure that 'Vzorova_CP3.xlsx' is in the same folder as your scripts.")
        return

    try:
        shutil.copy(template_file, new_file)
    except Exception as e:
        print("❌ Failed to copy template.")
        print(f"🔍 Error: {e}")
        return

    try:
        # ─── Open Excel ─────────────────────────────────────────────────────
        app = xw.App(visible=False)
        wb = xw.Book(new_file)
        sheet = wb.sheets[0]

        TEMPLATE_ROW      = 18
        insert_position   = TEMPLATE_ROW
        counter           = 1
        prev_section      = None
        section_start_row = None

        for idx, item in enumerate(selected_items):
            section = item[0]

            # ─── New section header? ───────────────────────────────────
            if section != prev_section:
                if prev_section is not None:
                    # spacer before new section
                    sheet.range(f"{insert_position}:{insert_position}").insert('down')
                    insert_position += 1

                # insert header row
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                sheet.cells(insert_position, 3).value = section
                sheet.range(f"{insert_position}:{insert_position}").api.Font.Bold = True
                insert_position += 1

                # mark first row of items in this section
                section_start_row = insert_position
                prev_section = section

            # ─── Unpack item tuple ─────────────────────────────────────
            produkt         = item[1]
            jednotky        = item[2]
            dodavatel       = item[3]
            odkaz           = item[4]
            koef_material   = float(item[5])
            koef_prace      = float(item[6])
            nakup_materialu = float(item[7])
            cena_prace      = float(item[8])
            pocet_materialu = int(item[9]) if len(item) > 9 else 1
            pocet_prace     = int(item[10]) if len(item) > 10 else 1

            # ─── Insert & format the item row ───────────────────────────
            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            src = sheet.range(f"{TEMPLATE_ROW+1}:{TEMPLATE_ROW+1}")
            dst = sheet.range(f"{insert_position}:{insert_position}")
            src.api.Copy()
            dst.api.PasteSpecial(Paste=-4163)  # xlPasteFormats

            # fill values & formulas (adjust as needed)
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
            sheet.cells(insert_position, 17).value = f"=P{insert_position}+G{insert_position}"
            sheet.cells(insert_position, 19).value = dodavatel
            if odkaz:
                sheet.cells(insert_position, 19).api.Hyperlinks.Add(
                    Anchor=sheet.cells(insert_position, 19).api,
                    Address=odkaz,
                    TextToDisplay="Link"
                )

            counter += 1
            insert_position += 1

            # ─── End-of-section subtotal? ───────────────────────────────
            next_section = selected_items[idx+1][0] if idx+1 < len(selected_items) else None
            if next_section != section:
                # blank spacer + label
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                sheet.cells(insert_position, 3).value = section + "spolu"
                sheet.cells(insert_position, 6).value = "Materiál"
                last_item_row = insert_position - 1
                sheet.cells(insert_position, 7).value = (
                    f"=SUM(G{section_start_row}:G{last_item_row})"
                )
                sheet.cells(insert_position, 9).value = "Práca"
                sheet.cells(insert_position, 10).value = (
                    f"=SUM(J{section_start_row}:J{last_item_row})"
                )
                sheet.cells(insert_position, 11).value = (
                    f"=ROUNDUP(SUM(K{section_start_row}:K{last_item_row}),0)"
                )
                insert_position += 1

                # optional “info” row with template formats
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                src.api.Copy()
                dst = sheet.range(f"{insert_position}:{insert_position}")
                dst.api.PasteSpecial(Paste=-4122)  # xlPasteFormats
                insert_position += 1

        # ─── Append notes sheet if requested ─────────────────────────
        if notes_text:
            try:
                notes_sheet = wb.sheets.add(after=sheet)
                notes_sheet.name = "Poznámky"
                for i, line in enumerate(notes_text.splitlines(), start=1):
                    notes_sheet.cells(i, 1).value = line
            except Exception as e:
                print("⚠ Failed to add notes sheet:", e)

        # ─── Save & clean up ─────────────────────────────────────────
        wb.save()
        wb.close()
        app.quit()
        print(f"✅ Successfully exported to: {new_file}")

    except Exception as e:
        print("❌ Failed during Excel export.")
        print(f"🔍 Error: {e}")
