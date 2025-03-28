import win32com.client

def update_excel(selected_items):
    if not selected_items:
        print("⚠ No items selected for Excel.")
        return

    original_file = r"C:\Users\domko\Downloads\Vzorova_CP 3.xlsx"
    new_file = r"C:\Users\domko\Desktop\LM\excel\Vzorova_CP_copy 3.xlsx"

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = True  

    workbook = excel.Workbooks.Open(original_file)
    workbook.SaveAs(new_file)
    workbook = excel.Workbooks.Open(new_file)

    sheet = workbook.Sheets(1)  

    # **Start inserting items below row 16, ensuring each gets its own row**
    row = 17  # First empty row under row 16

    for item in selected_items:
        sheet.Rows(row).Insert()  # Insert a new empty row for each item

        material = item[1]       # Product Name
        pocet = item[2]          # User-defined Quantity
        cena_materialu = item[3] # Material Price

        # **Start writing data from column 3 (C)**
        sheet.Cells(row, 3).Value = material         # Column C - Product Name
        sheet.Cells(row, 4).Value = "Ks"             # Column D - Unit
        sheet.Cells(row, 5).Value = pocet            # Column E - Quantity
        sheet.Cells(row, 6).Formula = f"=N{row}*M{row}"  # Column F = N row * M row
        sheet.Cells(row, 7).Formula = f"=F{row}*E{row}"  # Column G = F row * E row
        sheet.Cells(row, 8).Formula = f"=E{row}"        # Column H = Column E (Quantity)
        sheet.Cells(row, 9).Value = ""               # Column I - Placeholder
        sheet.Cells(row,10).Formula = f"=I{row}*H{row}" # Column J = I * H
        sheet.Cells(row,11).Formula = f"=G{row}+J{row}" # Column K = G + J 

        row += 1  # Move to the next row for the next item

    excel.CutCopyMode = False
    workbook.Save()

    print(f"✅ Excel updated: {len(selected_items)} row(s) inserted under row 16 with formulas in columns F, G, H, J, and K.")
