import win32com.client
import os

def update_excel(selected_items, new_file):
    if not selected_items:
        print("⚠ No items selected for Excel.")
        return

    if not new_file:
        print("❌ No export path provided.")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    old_file = os.path.join(base_dir, "Vzorova_CP3.xlsx")

    excel = win32com.client.Dispatch("Excel.Application")
    excel.DisplayAlerts = False
    excel.Visible = False

    try:
        template_wb = excel.Workbooks.Open(old_file)
        new_wb = excel.Workbooks.Add()

        template_sheet = template_wb.Sheets(1)
        new_sheet = new_wb.Sheets(1)

        template_sheet.UsedRange.Copy(Destination=new_sheet.Range("A1"))

        used_columns = template_sheet.UsedRange.Columns.Count
        for col in range(1, used_columns + 1):
            try:
                new_sheet.Columns(col).ColumnWidth = template_sheet.Columns(col).ColumnWidth
            except Exception as e:
                print(f"⚠ Failed to set column width for column {col}: {e}")

        used_rows = template_sheet.UsedRange.Rows.Count
        for r in range(1, used_rows + 1):
            try:
                new_sheet.Rows(r).RowHeight = template_sheet.Rows(r).RowHeight
            except Exception as e:
                print(f"⚠ Failed to set row height for row {r}: {e}")

        template_wb.Close(False)
    except Exception as e:
        print(f"❌ Failed to copy template to new workbook")
        print(f"🔍 Error: {e}")
        return

    sheet = new_wb.Sheets(1)
    row = 18  # Data starts BELOW row 17

    for item in selected_items:
        produkt = item[0]             # Produkt
        jednotky = item[1]            # Jednotky
        dodavatel = item[2]           # Dodavatel (display text)
        odkaz = item[3]               # Odkaz (hyperlink)
        koeficient = item[4]          # Koeficient
        nakup_materialu = item[5]     # Nakup_materialu
        cena_prace = item[6]          # Cena_prace
        pocet = item[7]               # Pocet


        try:
            sheet.Rows(row).Insert()
        except Exception as e:
            print(f"⚠ Couldn't insert row at {row}: {e}")
            continue

        # Insert data exactly matching the desired structure
        sheet.Cells(row, 3).Value = produkt                         # C - produkt
        sheet.Cells(row, 4).Value = jednotky                           # D - jednotky
        sheet.Cells(row, 5).Value = pocet                           # E - pocet
        sheet.Cells(row, 6).Formula = f"=N{row}*M{row}"             # F - vzorec
        sheet.Cells(row, 7).Formula = f"=F{row}*E{row}"             # G - vzorec
        sheet.Cells(row, 8).Formula = f"=E{row}"                    # H - pocet vzorec je ze sa to rovna E
        sheet.Cells(row, 9).Value = cena_prace                           # I - pocet
        sheet.Cells(row,10).Formula = f"=I{row}*H{row}"                     # J - koeficient
        sheet.Cells(row,11).Formula = f"=G{row}+J{row}"                 # K - nakup material
        # ❌ DO NOT WRITE TO COLUMN L
        # sheet.Cells(row, 12).Formula = f"=J{row}*I{row}"          # ⛔ Removed
        sheet.Cells(row,13).Value = koeficient            # M - vzorec
        sheet.Cells(row,14).Value = nakup_materialu             # N - vzorec
        sheet.Cells(row,15).Formula = f"=N{row}*E{row}"         #O - vzorec
        sheet.Cells(row,16).Formula = f"= G{row}-O{row}"        #P - vzorec
        sheet.Cells(row,17).Formula = f"= P{row}/G{row}"        #Q - vzorec
        sheet.Cells(row,19).Value = dodavatel                    # S - text placeholder

        row += 1

    try:
        new_wb.SaveAs(new_file)
        new_wb.Close(False)
        print(f"✅ Successfully saved to: {new_file}")
    except Exception as e:
        print(f"❌ Could not save to {new_file}")
        print(f"🔍 Error: {e}")
