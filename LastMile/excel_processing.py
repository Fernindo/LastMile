import xlwings as xw
import os
import shutil

def update_excel(selected_items, new_file, notes_text=""):
    if not selected_items:
        print("⚠ No items selected for Excel.")
        return

    if not new_file:
        print("❌ No export path provided.")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(base_dir, "Vzorova_CP3.xlsx")

    # Check if the Excel template file exists
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
        # Start an instance of Excel via xlwings
        app = xw.App(visible=False)
        # Optionally, you can turn off screen updating: app.screen_updating = False

        wb = xw.Book(new_file)
        sheet = wb.sheets[0]  # get the first sheet

        TEMPLATE_ROW = 18
        insert_position = TEMPLATE_ROW
        counter = 1

        for item in selected_items:
            # Unpack the item values according to their positions
            produkt = item[1]
            jednotky = item[2]
            dodavatel = item[3]
            odkaz = item[4]
            koeficient = float(item[5])
            nakup_materialu = float(item[6])
            cena_prace = float(item[7])
            pocet = int(item[8])

            # Insert new row at the desired position.
            # Using the range() method with the complete row reference
            sheet.range(f"{insert_position}:{insert_position}").insert('down')

            # Copy formatting from the template row (TEMPLATE_ROW + 1)
            source_range = sheet.range(f"{TEMPLATE_ROW + 1}:{TEMPLATE_ROW + 1}")
            dest_range = sheet.range(f"{insert_position}:{insert_position}")
            # The underlying API is used here for paste special formatting.
            source_range.api.Copy()
            dest_range.api.PasteSpecial(Paste=-4163)  # -4163 corresponds to xlPasteFormats

            # Fill in the cell values and formulas.
            sheet.cells(insert_position, 2).value = counter
            sheet.cells(insert_position, 3).value = produkt
            sheet.cells(insert_position, 4).value = jednotky
            sheet.cells(insert_position, 5).value = pocet
            # Assign formulas as strings (they will appear in Excel as formulas)
            sheet.cells(insert_position, 6).value = f"=N{insert_position}*M{insert_position}"
            sheet.cells(insert_position, 7).value = f"=F{insert_position}*E{insert_position}"
            sheet.cells(insert_position, 8).value = f"=E{insert_position}"
            sheet.cells(insert_position, 9).value = cena_prace
            sheet.cells(insert_position, 10).value = f"=I{insert_position}*H{insert_position}"
            sheet.cells(insert_position, 11).value = f"=G{insert_position}+J{insert_position}"
            sheet.cells(insert_position, 13).value = koeficient
            sheet.cells(insert_position, 14).value = nakup_materialu
            sheet.cells(insert_position, 15).value = f"=N{insert_position}*E{insert_position}"
            sheet.cells(insert_position, 16).value = f"=G{insert_position}-O{insert_position}"
            sheet.cells(insert_position, 17).value = f"=P{insert_position}/G{insert_position}"

            # Add a hyperlink to the cell in column 19 if provided.
            if odkaz and dodavatel:
                try:
                    cell = sheet.cells(insert_position, 19)
                    cell.value = dodavatel  # Set the displayed text
                    # Use the API to add a hyperlink.
                    cell.api.Hyperlinks.Add(Anchor=cell.api, Address=str(odkaz), TextToDisplay=str(dodavatel))
                except Exception as link_error:
                    print(f"⚠ Could not add hyperlink at row {insert_position}: {link_error}")

            insert_position += 1
            counter += 1

        # Add a separate sheet for notes if any notes are provided.
        if notes_text.strip():
            try:
                notes_sheet = wb.sheets.add(after=wb.sheets[-1])
                notes_sheet.name = "Poznámky"
                for i, line in enumerate(notes_text.splitlines(), start=1):
                    notes_sheet.cells(i, 1).value = line
            except Exception as e:
                print("⚠ Failed to add notes sheet:", e)

        # Save and clean up
        wb.save()
        wb.close()
        app.quit()
        print(f"✅ Successfully exported to: {new_file}")

    except Exception as e:
        print("❌ Failed during Excel export.")
        print(f"🔍 Error: {e}")
