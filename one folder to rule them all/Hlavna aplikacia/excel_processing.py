import xlwings as xw
import os
import shutil
import sys
import tkinter as tk
from tkinter import messagebox

# Create and hide the Tkinter root for messageboxes
root = tk.Tk()
root.withdraw()

def update_excel(selected_items, new_file, notes_text=""):
    # 1) Early sanity checks
    if not selected_items:
        messagebox.showwarning("Export neúspešný", "⚠ Žiadne položky na export.")
        return False
    if not new_file:
        messagebox.showerror("Export neúspešný", "❌ Nie je zadaná cesta pre export.")
        return False

    # 2) Locate & copy the template
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(base_dir, "Vzorova_CP3.xlsx")
    if not os.path.exists(template_file):
        messagebox.showerror("Export neúspešný", f"❌ Šablóna nenájdená: {template_file}")
        return False
    try:
        shutil.copy(template_file, new_file)
    except Exception as e:
        messagebox.showerror("Export neúspešný", f"❌ Chyba pri kopírovaní šablóny: {e}")
        return False

    # 3) Begin Excel operations
    try:
        app   = xw.App(visible=False)
        wb    = xw.Book(new_file)
        sheet = wb.sheets[0]

        TEMPLATE_ROW    = 18
        insert_position = TEMPLATE_ROW
        counter         = 1
        prev_section    = None
        section_start   = None

        def draw_full_border(xl_rng):
            for edge in (7, 8, 9, 10, 12, 13):
                b = xl_rng.api.Borders(edge)
                b.LineStyle = 1
                b.Weight    = 2

        for item in selected_items:
            section = item[0]
            # Close out previous section totals...
            if section != prev_section:
                if prev_section is not None:
                    # SPOLU row
                    sheet.range(f"{insert_position}:{insert_position}").insert('down')
                    r = insert_position
                    lbl_rng = sheet.range(sheet.cells(r,2), sheet.cells(r,5))
                    lbl_rng.api.Merge()
                    lbl = sheet.cells(r,2)
                    lbl.value = f"{prev_section} SPOLU:"
                    lbl.api.Font.Bold = True
                    lbl.api.HorizontalAlignment = -4131
                    mat = sheet.cells(r,6)
                    mat.value = "Materiál:"
                    mat.api.Interior.Color = 0xD9E1F2
                    sheet.cells(r,7).value = f"=SUM(G{section_start}:G{r-1})"
                    pr = sheet.cells(r,9)
                    pr.value = "Práca:"
                    pr.api.Interior.Color = 0xD9E1F2
                    sheet.cells(r,10).value = f"=SUM(J{section_start}:J{r-1})"
                    sheet.cells(r,11).value = f"=ROUNDUP(SUM(K{section_start}:K{r-1}),0)"
                    rng_sp = sheet.range(sheet.cells(r,2), sheet.cells(r,11))
                    draw_full_border(rng_sp)
                    insert_position += 1
                # Section header row
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                hdr = sheet.range(sheet.cells(insert_position,2), sheet.cells(insert_position,11))
                hdr.api.Merge()
                cell_hdr = sheet.cells(insert_position,2)
                cell_hdr.value = section
                cell_hdr.api.Font.Bold = True
                cell_hdr.api.Font.Size = 14
                cell_hdr.api.HorizontalAlignment = -4131
                draw_full_border(hdr)
                section_start = insert_position + 1
                prev_section = section
                insert_position += 1
            # Item row
            _, produkt, jednotky, dodavatel, odkaz, koef_mat, nakup_mat, cena_prace, pocet = item[:9]
            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            src = sheet.range(f"{TEMPLATE_ROW+1}:{TEMPLATE_ROW+1}")
            dst = sheet.range(f"{insert_position}:{insert_position}")
            src.api.Copy(); dst.api.PasteSpecial(Paste=-4163)
            rng_item = sheet.range(sheet.cells(insert_position,2), sheet.cells(insert_position,11))
            rng_item.api.Font.Bold = False
            sheet.cells(insert_position,2).value  = counter
            sheet.cells(insert_position,3).value  = produkt
            sheet.cells(insert_position,4).value  = jednotky
            sheet.cells(insert_position,5).value  = int(pocet)
            sheet.cells(insert_position,6).value  = f"=N{insert_position}*M{insert_position}"  # JC materiál
            sheet.cells(insert_position,7).value  = f"=F{insert_position}*E{insert_position}"  # Spolu materiál
            sheet.cells(insert_position,8).value  = f"=E{insert_position}"
            sheet.cells(insert_position,9).value  = cena_prace
            sheet.cells(insert_position,10).value = f"=I{insert_position}*H{insert_position}"  # Spolu práca
            sheet.cells(insert_position,11).value = f"=G{insert_position}+J{insert_position}"  # Spolu celkom
            draw_full_border(rng_item)
            if odkaz and dodavatel:
                try:
                    link = sheet.cells(insert_position,19)
                    link.value = dodavatel
                    link.api.Hyperlinks.Add(Anchor=link.api, Address=str(odkaz), TextToDisplay=str(dodavatel))
                except:
                    pass
            counter += 1
            insert_position += 1
        # Final SPOLU of last section
        if prev_section is not None:
            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            r = insert_position
            lbl_rng = sheet.range(sheet.cells(r,2), sheet.cells(r,5))
            lbl_rng.api.Merge()
            lbl = sheet.cells(r,2)
            lbl.value = f"{prev_section} SPOLU:"
            lbl.api.Font.Bold = True
            lbl.api.HorizontalAlignment = -4131
            mat = sheet.cells(r,6)
            mat.value = "Materiál:"
            mat.api.Interior.Color = 0xD9E1F2
            sheet.cells(r,7).value  = f"=SUM(G{section_start}:G{r-1})"
            pr  = sheet.cells(r,9)
            pr.value = "Práca:"
            pr.api.Interior.Color = 0xD9E1F2
            sheet.cells(r,10).value = f"=SUM(J{section_start}:J{r-1})"
            sheet.cells(r,11).value = f"=ROUNDUP(SUM(K{section_start}:K{r-1}),0)"
            sp_rng = sheet.range(sheet.cells(r,2), sheet.cells(r,11))
            draw_full_border(sp_rng)
        # Optional notes sheet
        if notes_text.strip():
            notes = wb.sheets.add(after=wb.sheets[-1])
            notes.name = "Poznámky"
            for i, line in enumerate(notes_text.splitlines(), start=1):
                notes.cells(i,1).value = line
        # Save & cleanup
        wb.save()
        wb.close()
        app.quit()
        # Notify user on success
        messagebox.showinfo("Export hotový", f"✅ Súbor bol uložený: {new_file}")
        return True
    except Exception as e:
        messagebox.showerror("Export zlyhal", f"❌ Chyba: {e}")
        return False
