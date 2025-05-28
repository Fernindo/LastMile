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
        # app.screen_updating = False  # optionally speed it up
        wb = xw.Book(new_file)
        sheet = wb.sheets[0]

        TEMPLATE_ROW = 18
        insert_position = TEMPLATE_ROW
        counter = 1

        # ← NEW: track last section to know when to insert a header
        prev_section = None

        for idx, item in enumerate(selected_items):
            # ← NEW: extract section name from item[0]
            section = item[0]
            if section != prev_section:
                # — if we're finishing a section (i.e. not the very first), add one blank row
                if prev_section is not None:
                    sheet.range(f"{insert_position}:{insert_position}").insert('down')
                    insert_position += 1

                # — now insert the header row for the new section
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                sheet.cells(insert_position, 3).value = section
                sheet.range(f"{insert_position}:{insert_position}").api.Font.Bold = True
                insert_position += 1
                prev_section = section

            # ─── Unpack your item tuple as before ───────────────────────────
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

            # ─── Insert the item row ────────────────────────────────────────
            sheet.range(f"{insert_position}:{insert_position}").insert('down')

            # Copy formatting from the template row
            source = sheet.range(f"{TEMPLATE_ROW + 1}:{TEMPLATE_ROW + 1}")
            dest   = sheet.range(f"{insert_position}:{insert_position}")
            source.api.Copy()
            dest.api.PasteSpecial(Paste=-4163)  # xlPasteFormats

            # Fill in values & formulas (adjust columns as in your template)
            sheet.cells(insert_position, 2).value = counter
            sheet.cells(insert_position, 3).value = produkt
            sheet.cells(insert_position, 4).value = jednotky
            sheet.cells(insert_position, 5).value = pocet_materialu
            sheet.cells(insert_position, 6).value = f"=N{insert_position}*M{insert_position}"
            sheet.cells(insert_position, 7).value = f"=F{insert_position}*E{insert_position}"
            sheet.cells(insert_position, 8).value = f"=E{insert_position}"
            sheet.cells(insert_position, 9).value = nakup_materialu
            sheet.cells(insert_position, 10).value = f"=I{insert_position}*H{insert_position}"
            sheet.cells(insert_position, 11).value = f"=G{insert_position}+J{insert_position}"

            sheet.cells(insert_position, 13).value = koef_material
            sheet.cells(insert_position, 14).value = nakup_materialu
            sheet.cells(insert_position, 15).value = f"=N{insert_position}*E{insert_position}"
            sheet.cells(insert_position, 16).value = f"=G{insert_position}-O{insert_position}"
            sheet.cells(insert_position, 17).value = f"=P{insert_position}+G{insert_position}"
            sheet.cells(insert_position, 19).value = dodavatel
            # add hyperlink if present
            if odkaz:
                sheet.cells(insert_position, 19).api.Hyperlinks.Add(
                    Anchor=sheet.cells(insert_position, 19).api,
                    Address=odkaz,
                    TextToDisplay="Link"
                )

            counter += 1
            insert_position += 1

            next_section = selected_items[idx+1][0] if idx+1 < len(selected_items) else None
            if next_section != item[0]:
                # 1) plain blank spacer
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                sheet.cells(insert_position, 6).value = "Material"
                insert_position += 1

                # 2) formatted info row (you can type into this)
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                # copy formatting from your template row
                src = sheet.range(f"{TEMPLATE_ROW+1}:{TEMPLATE_ROW+1}")
                dst = sheet.range(f"{insert_position}:{insert_position}")
                src.api.Copy()
                dst.api.PasteSpecial(Paste=-4122)  # xlPasteFormats
                insert_position += 1
            """
            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            insert_position += 1
            """
            
           

        # ─── Append notes sheet if requested ─────────────────────────────
        if notes_text:
            try:
                notes_sheet = wb.sheets.add(after=sheet)
                notes_sheet.name = "Poznámky"
                for i, line in enumerate(notes_text.splitlines(), start=1):
                    notes_sheet.cells(i, 1).value = line
            except Exception as e:
                print("⚠ Failed to add notes sheet:", e)

        # ─── Save & clean up ─────────────────────────────────────────────
        wb.save()
        wb.close()
        app.quit()
        print(f"✅ Successfully exported to: {new_file}")

    except Exception as e:
        print("❌ Failed during Excel export.")
        print(f"🔍 Error: {e}")
