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
        # Open template
        template_wb = excel.Workbooks.Open(old_file)

        # Create new workbook
        new_wb = excel.Workbooks.Add()

        # Copy contents from template sheet to new workbook
        template_sheet = template_wb.Sheets(1)
        new_sheet = new_wb.Sheets(1)

        # Copy content
        template_sheet.UsedRange.Copy(Destination=new_sheet.Range("A1"))

        # Copy column widths
        used_columns = template_sheet.UsedRange.Columns.Count
        for col in range(1, used_columns + 1):
            try:
                new_sheet.Columns(col).ColumnWidth = template_sheet.Columns(col).ColumnWidth
            except Exception as e:
                print(f"⚠ Failed to set column width for column {col}: {e}")

        # Copy row heights
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
    row = 17  # starting row for data insertion

    for item in selected_items:
        produkt = item[0]
        nakup_materialu = item[1]
        koeficient = item[2]
        pocet = item[3]

        try:
            sheet.Rows(row).Insert()
            # Safely try to preserve row height from original template row (if it exists)
            try:
                sheet.Rows(row).RowHeight = template_sheet.Rows(row).RowHeight
            except Exception as e:
                print(f"⚠ Couldn't set height for row {row}: {e}")
        except Exception as e:
            print(f"⚠ Couldn't insert row at {row}: {e}")
            continue

        sheet.Cells(row, 3).Value = produkt
        sheet.Cells(row, 4).Value = "ks"
        sheet.Cells(row, 5).Value = pocet
        sheet.Cells(row, 6).Formula = f"=N{row}*M{row}"
        sheet.Cells(row, 7).Value = ""
        sheet.Cells(row, 8).Formula = f"=F{row}*E{row}"
        sheet.Cells(row, 9).Formula = f"=E{row}"
        sheet.Cells(row,10).Value = koeficient
        sheet.Cells(row,11).Value = nakup_materialu
        sheet.Cells(row,12).Formula = f"=J{row}*I{row}"
        sheet.Cells(row,13).Formula = f"=G{row}+L{row}"
        sheet.Cells(row,14).Formula = f"=K{row}*E{row}"

        row += 1

    try:
        new_wb.SaveAs(new_file)
        new_wb.Close(False)
        print(f"✅ Successfully saved to: {new_file}")
    except Exception as e:
        print(f"❌ Could not save to {new_file}")
        print(f"🔍 Error: {e}")
