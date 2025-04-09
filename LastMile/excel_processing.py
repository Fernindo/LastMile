import win32com.client
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

    excel = win32com.client.Dispatch("Excel.Application")
    excel.ScreenUpdating = False
    excel.DisplayAlerts = False
    excel.Visible = False

    try:
        wb = excel.Workbooks.Open(new_file)
        sheet = wb.Sheets(1)

        TEMPLATE_ROW = 18
        insert_position = TEMPLATE_ROW
        counter = 1

        for item in selected_items:
            produkt = item[1]
            jednotky = item[2]
            dodavatel = item[3]
            odkaz = item[4]
            koeficient = float(item[5])
            nakup_materialu = float(item[6])
            cena_prace = float(item[7])
            pocet = int(item[8])

            # Insert and format row from template
            sheet.Rows(insert_position).Insert()
            sheet.Rows(TEMPLATE_ROW + 1).Copy()
            sheet.Rows(insert_position).PasteSpecial(Paste=-4163)  # xlPasteFormats

            # Fill values
            sheet.Cells(insert_position, 2).Value = counter
            sheet.Cells(insert_position, 3).Value = produkt
            sheet.Cells(insert_position, 4).Value = jednotky
            sheet.Cells(insert_position, 5).Value = pocet
            sheet.Cells(insert_position, 6).Formula = f"=N{insert_position}*M{insert_position}"
            sheet.Cells(insert_position, 7).Formula = f"=F{insert_position}*E{insert_position}"
            sheet.Cells(insert_position, 8).Formula = f"=E{insert_position}"
            sheet.Cells(insert_position, 9).Value = cena_prace
            sheet.Cells(insert_position, 10).Formula = f"=I{insert_position}*H{insert_position}"
            sheet.Cells(insert_position, 11).Formula = f"=G{insert_position}+J{insert_position}"
            sheet.Cells(insert_position, 13).Value = koeficient
            sheet.Cells(insert_position, 14).Value = nakup_materialu
            sheet.Cells(insert_position, 15).Formula = f"=N{insert_position}*E{insert_position}"
            sheet.Cells(insert_position, 16).Formula = f"=G{insert_position}-O{insert_position}"
            sheet.Cells(insert_position, 17).Formula = f"=P{insert_position}/G{insert_position}"

            if odkaz and dodavatel:
                try:
                    sheet.Hyperlinks.Add(
                        Anchor=sheet.Cells(insert_position, 19),
                        Address=str(odkaz),
                        TextToDisplay=str(dodavatel)
                    )
                except Exception as link_error:
                    print(f"⚠ Could not add hyperlink at row {insert_position}: {link_error}")

            insert_position += 1
            counter += 1

        # ➕ Add notes if provided
        if notes_text.strip():
            try:
                notes_sheet = wb.Sheets.Add(After=wb.Sheets(wb.Sheets.Count))
                notes_sheet.Name = "Poznámky"
                for i, line in enumerate(notes_text.splitlines(), start=1):
                    notes_sheet.Cells(i, 1).Value = line
            except Exception as e:
                print("⚠ Failed to add notes sheet:", e)

        excel.ScreenUpdating = True
        wb.Save()
        wb.Close(False)
        print(f"✅ Successfully exported to: {new_file}")

    except Exception as e:
        print("❌ Failed during Excel export.")
        print(f"🔍 Error: {e}")
