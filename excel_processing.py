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
    # Close Excel's default blank workbook if it exists
    if excel.Workbooks.Count > 0:
        for wb in excel.Workbooks:
            if wb.Name == "Book1" or not wb.Saved:
                try:
                    wb.Close(SaveChanges=False)
                except:
                    pass

    excel.DisplayAlerts = False
    excel.Visible = False

    try:
        # Close default workbook if Excel launched it
        if excel.Workbooks.Count > 0:
            for wb in excel.Workbooks:
                if wb.Name == "Book1" or not wb.Saved:
                    try:
                        wb.Close(SaveChanges=False)
                    except:
                        pass

        # Open template and create new workbook
        template_wb = excel.Workbooks.Open(old_file)
        new_wb = excel.Workbooks.Add()
        template_sheet = template_wb.Sheets(1)
        new_sheet = new_wb.Sheets(1)

        # Copy entire template contents
        template_sheet.UsedRange.Copy(Destination=new_sheet.Range("A1"))

        # Copy column widths
        used_columns = template_sheet.UsedRange.Columns.Count
        for col in range(1, used_columns + 1):
            new_sheet.Columns(col).ColumnWidth = template_sheet.Columns(col).ColumnWidth

        # Copy row heights
        used_rows = template_sheet.UsedRange.Rows.Count
        for r in range(1, used_rows + 1):
            new_sheet.Rows(r).RowHeight = template_sheet.Rows(r).RowHeight

        template_wb.Close(False)
    except Exception as e:
        print("❌ Failed to prepare workbook.")
        print(f"🔍 Error: {e}")
        return

    sheet = new_wb.Sheets(1)
    row = 18
    counter = 1

    for item in selected_items:
        produkt = item[0]
        jednotky = item[1]
        dodavatel = item[2]
        odkaz = item[3]
        koeficient = float(item[4])
        nakup_materialu = float(item[5])
        cena_prace = float(item[6])
        pocet = int(item[7])

        try:
            sheet.Rows(row).Insert()
        except Exception as e:
            print(f"⚠ Couldn't insert row {row}: {e}")
            continue

        # Fill Excel cells
        sheet.Cells(row, 2).Value = counter                      # B - P.Č.
        sheet.Cells(row, 3).Value = produkt                     # C - Produkt
        sheet.Cells(row, 4).Value = jednotky                    # D - Jednotky
        sheet.Cells(row, 5).Value = pocet                       # E - Počet
        sheet.Cells(row, 6).Formula = f"=N{row}*M{row}"         # F - JC mat * Koef
        sheet.Cells(row, 7).Formula = f"=F{row}*E{row}"                  # G - JC práca
        sheet.Cells(row, 8).Formula = f"=E{row}"         # H - Spolu materiál
        sheet.Cells(row, 9).Value = cena_prace                # I - Počet (again)
        sheet.Cells(row,10).Formula = f"=I{row}*H{row}"         # J - Spolu práca
        sheet.Cells(row,11).Formula = f"=G{row}+J{row}"         # K - Spolu
        sheet.Cells(row,13).Value = koeficient                  # M - Koeficient
        sheet.Cells(row,14).Value = nakup_materialu             # N - Nákup materiál
        sheet.Cells(row,15).Formula = f"=N{row}*E{row}"         # O - Nákup spolu
        sheet.Cells(row,16).Formula = f"=G{row}-O{row}"         # P - Zisk
        sheet.Cells(row,17).Formula = f"=P{row}/G{row}"         # Q - Marža

        # Add hyperlink in column S
        if odkaz:
            sheet.Hyperlinks.Add(Anchor=sheet.Cells(row, 19), Address=odkaz, TextToDisplay=dodavatel)

        # Apply borders to B–S, skip L (col 12)
        for col in range(2, 20):
            if col == 12:
                continue
            cell = sheet.Cells(row, col)
            for border_id in [7, 8, 9, 10]:  # Left, Top, Bottom, Right
                border = cell.Borders(border_id)
                border.LineStyle = 1  # xlContinuous
                # Thicker on the leftmost and rightmost columns
                if (col == 2 and border_id == 7) or (col == 11 and border_id == 10):
                    border.Weight = 3  # xlMedium
                else:
                    border.Weight = 2  # xlThin

        row += 1
        counter += 1

    try:
        new_wb.SaveAs(new_file)
        new_wb.Close(False)
        print(f"✅ Successfully saved to: {new_file}")
    except Exception as e:
        print(f"❌ Could not save to {new_file}")
        print(f"🔍 Error: {e}")
        print("💡 Tip: Make sure the file isn't open in Excel or named the same as your template.")
