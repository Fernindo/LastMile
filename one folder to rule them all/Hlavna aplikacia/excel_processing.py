import xlwings as xw
import os
import shutil
import sys
import tkinter as tk
from tkinter import messagebox

# Inicializácia tkinter root pre messageboxy
root = tk.Tk()
root.withdraw()

def update_excel(selected_items, new_file, notes_text=""):
    if not selected_items:
        messagebox.showwarning("Export neúspešný", "⚠ Žiadne položky na export.")
        return False
    if not new_file:
        messagebox.showerror("Export neúspešný", "❌ Nie je zadaná cesta pre export.")
        return False

    # Zistenie cesty k šablóne
    base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(base_dir, "Vzorova_CP3.xlsx")
    if not os.path.exists(template_file):
        messagebox.showerror("Export neúspešný", f"❌ Šablóna nenájdená: {template_file}")
        return False

    try:
        shutil.copy(template_file, new_file)
    except Exception as e:
        messagebox.showerror("Export neúspešný", f"❌ Chyba pri kopírovaní šablóny: {e}")
        return False

    try:
        app = xw.App(visible=False)
        wb = xw.Book(new_file)
        sheet = wb.sheets[0]

        TEMPLATE_ROW = 18
        insert_position = TEMPLATE_ROW
        counter = 1
        prev_section = None
        section_start = None

        def draw_full_border(xl_rng):
            for edge in (7, 8, 9, 10, 12, 13):  # edges + interior
                b = xl_rng.api.Borders(edge)
                b.LineStyle = 1  # xlContinuous
                b.Weight = 2     # xlThin

        for item in selected_items:
            section = item[0]

            if section != prev_section:
                if prev_section is not None:
                    sheet.range(f"{insert_position}:{insert_position}").insert('down')
                    r = insert_position
                    lbl_rng = sheet.range(sheet.cells(r,2), sheet.cells(r,5))
                    lbl_rng.api.Merge()
                    sheet.cells(r,2).value = f"{prev_section} SPOLU:"
                    sheet.cells(r,2).api.Font.Bold = True
                    sheet.cells(r,2).api.HorizontalAlignment = -4131
                    sheet.cells(r,6).value = "Materiál:"
                    sheet.cells(r,6).api.Interior.Color = 0xD9E1F2
                    sheet.cells(r,7).value = f"=SUM(G{section_start}:G{r-1})"
                    sheet.cells(r,9).value = "Práca:"
                    sheet.cells(r,9).api.Interior.Color = 0xD9E1F2
                    sheet.cells(r,10).value = f"=SUM(J{section_start}:J{r-1})"
                    sheet.cells(r,11).value = f"=ROUNDUP(SUM(K{section_start}:K{r-1}),0)"
                    draw_full_border(sheet.range(sheet.cells(r,2), sheet.cells(r,11)))
                    insert_position += 1

                # Sekčný nadpis
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                header_range = sheet.range(sheet.cells(insert_position,2), sheet.cells(insert_position,11))
                header_range.api.Merge()
                sheet.cells(insert_position,2).value = section
                sheet.cells(insert_position,2).api.Font.Bold = True
                sheet.cells(insert_position,2).api.Font.Size = 14
                sheet.cells(insert_position,2).api.HorizontalAlignment = -4131
                draw_full_border(header_range)

                section_start = insert_position + 1
                prev_section = section
                insert_position += 1

            produkt         = item[1]
            jednotky        = item[2]
            dodavatel       = item[3]
            odkaz           = item[4]
            koeficient      = float(item[5])
            nakup_materialu = float(item[6])
            cena_prace      = float(item[7])
            pocet           = int(item[8])

            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            source_range = sheet.range(f"{TEMPLATE_ROW + 1}:{TEMPLATE_ROW + 1}")
            dest_range = sheet.range(f"{insert_position}:{insert_position}")
            source_range.api.Copy()
            dest_range.api.PasteSpecial(Paste=-4163)

            row_cells = sheet.range(sheet.cells(insert_position,2), sheet.cells(insert_position,11))
            row_cells.api.Font.Bold = False

            sheet.cells(insert_position,2).value = counter
            sheet.cells(insert_position,3).value = produkt
            sheet.cells(insert_position,4).value = jednotky
            sheet.cells(insert_position,5).value = pocet
            sheet.cells(insert_position,6).value = f"=N{insert_position}*M{insert_position}"
            sheet.cells(insert_position,7).value = f"=F{insert_position}*E{insert_position}"
            sheet.cells(insert_position,8).value = f"=E{insert_position}"
            sheet.cells(insert_position,9).value = cena_prace
            sheet.cells(insert_position,10).value = f"=I{insert_position}*H{insert_position}"
            sheet.cells(insert_position,11).value = f"=G{insert_position}+J{insert_position}"

            sheet.cells(insert_position,13).value = koeficient
            sheet.cells(insert_position,14).value = nakup_materialu
            sheet.cells(insert_position,15).value = f"=N{insert_position}*E{insert_position}"
            sheet.cells(insert_position,16).value = f"=G{insert_position}-O{insert_position}"
            sheet.cells(insert_position,17).value = f"=P{insert_position}/G{insert_position}"

            draw_full_border(row_cells)

            if odkaz and dodavatel:
                try:
                    cell = sheet.cells(insert_position, 19)
                    cell.value = dodavatel
                    cell.api.Hyperlinks.Add(Anchor=cell.api, Address=str(odkaz), TextToDisplay=str(dodavatel))
                except Exception as e:
                    print(f"⚠ Hyperlink error: {e}")

            insert_position += 1
            counter += 1

        # Záverečný súčet pre poslednú sekciu
        if prev_section:
            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            r = insert_position
            lbl_rng = sheet.range(sheet.cells(r,2), sheet.cells(r,5))
            lbl_rng.api.Merge()
            sheet.cells(r,2).value = f"{prev_section} SPOLU:"
            sheet.cells(r,2).api.Font.Bold = True
            sheet.cells(r,2).api.HorizontalAlignment = -4131
            sheet.cells(r,6).value = "Materiál:"
            sheet.cells(r,6).api.Interior.Color = 0xD9E1F2
            sheet.cells(r,7).value = f"=SUM(G{section_start}:G{r-1})"
            sheet.cells(r,9).value = "Práca:"
            sheet.cells(r,9).api.Interior.Color = 0xD9E1F2
            sheet.cells(r,10).value = f"=SUM(J{section_start}:J{r-1})"
            sheet.cells(r,11).value = f"=ROUNDUP(SUM(K{section_start}:K{r-1}),0)"
            draw_full_border(sheet.range(sheet.cells(r,2), sheet.cells(r,11)))

        if notes_text.strip():
            try:
                notes_sheet = wb.sheets.add(after=wb.sheets[-1])
                notes_sheet.name = "Poznámky"
                for i, line in enumerate(notes_text.splitlines(), start=1):
                    notes_sheet.cells(i, 1).value = line
            except Exception as e:
                messagebox.showwarning("Poznámky", f"⚠ Nepodarilo sa pridať poznámky: {e}")

        wb.save()
        wb.close()
        app.quit()

        messagebox.showinfo("Export hotový", f"✅ Súbor bol uložený: {new_file}")
        return True

    except Exception as e:
        messagebox.showerror("Export zlyhal", f"❌ Chyba: {e}")
        return False
