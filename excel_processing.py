import win32com.client
import os

def update_excel(selected_items):
    if not selected_items:
        print("⚠ No items selected for Excel.")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))  # project root
    original_file = os.path.join(base_dir, "excel_templates", "Vzorova_CP.xlsx")
    new_file = os.path.join(base_dir, "excel_templates", "Vzorova_CP_copy.xlsx")

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = True

    workbook = excel.Workbooks.Open(original_file)
    workbook.SaveAs(new_file)
    workbook = excel.Workbooks.Open(new_file)

    sheet = workbook.Sheets(1)

    row = 17  # Start writing from row 17

    for item in selected_items.values():
        sheet.Rows(row).Insert()

        produkt = item[0]              # product name
        nakup_materialu = item[1]      # purchase price
        koeficient = item[2]           # coefficient
        pocet = item[3]                # quantity

        # Set the Excel values according to your new table layout
        sheet.Cells(row, 3).Value = produkt           # Column C: produkt
        sheet.Cells(row, 4).Value = "ks"              # Column D: jednotky
        sheet.Cells(row, 5).Value = pocet             # Column E: počet
        sheet.Cells(row, 6).Formula = f"=N{row}*M{row}"   # Column F: formula
        sheet.Cells(row, 7).Value = ""                # Column G: cena práce — blank, formula might go here
        sheet.Cells(row, 8).Formula = f"=F{row}*E{row}"   # Column H: formula
        sheet.Cells(row, 9).Formula = f"=E{row}"          # Column I: formula = E
        sheet.Cells(row,10).Value = koeficient            # Column J: koeficient
        sheet.Cells(row,11).Value = nakup_materialu       # Column K: nákup materiálu
        sheet.Cells(row,12).Formula = f"=J{row}*I{row}"    # Column L: koeficient * množstvo
        sheet.Cells(row,13).Formula = f"=G{row}+L{row}"    # Column M: G + L
        sheet.Cells(row,14).Formula = f"=K{row}*E{row}"    # Column N: nákup * počet

        row += 1

    excel.CutCopyMode = False
    workbook.Save()

    print(f"✅ Excel updated: {len(selected_items)} row(s) inserted under row 16.")
