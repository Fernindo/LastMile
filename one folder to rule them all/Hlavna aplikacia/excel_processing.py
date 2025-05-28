import xlwings as xw
import os
import shutil
import sys

def update_excel(selected_items, new_file, notes_text=""):
    # 1) Early sanity checks
    if not selected_items:
        print("⚠ No items selected for Excel.")
        return
    if not new_file:
        print("❌ No export path provided.")
        return

    # 2) Locate & copy the template
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(base_dir, "Vzorova_CP3.xlsx")
    if not os.path.exists(template_file):
        print(f"❌ Template file not found at: {template_file}")
        return
    try:
        shutil.copy(template_file, new_file)
    except Exception as e:
        print("❌ Failed to copy template:", e)
        return

    # 3) Open Excel
    try:
        app   = xw.App(visible=False)
        wb    = xw.Book(new_file)
        sheet = wb.sheets[0]

        # 4) Init pointers & counters
        TEMPLATE_ROW    = 18
        insert_position = TEMPLATE_ROW
        counter         = 1
        prev_section    = None
        section_start   = None

        # Helper to draw full grid border on a given range
        def draw_full_border(xl_rng):
            # Edges: left(7), top(8), bottom(9), right(10)
            # Interiors: inside vertical(12), inside horizontal(13)
            for edge in (7, 8, 9, 10, 12, 13):
                b = xl_rng.api.Borders(edge)
                b.LineStyle = 1  # xlContinuous
                b.Weight    = 2  # xlThin

        # 5) Loop through each selected item
        for item in selected_items:
            section = item[0]

            # 5a) When we hit a new section, close out the previous one
            if section != prev_section:
                if prev_section is not None:
                    # --- SPOLU total row for prev_section ---
                    sheet.range(f"{insert_position}:{insert_position}").insert('down')
                    r = insert_position

                    # Merge B:E for the SPOLU label
                    lbl_rng = sheet.range(sheet.cells(r,2), sheet.cells(r,5))
                    lbl_rng.api.Merge()
                    lbl = sheet.cells(r,2)
                    lbl.value = f"{prev_section} SPOLU:"
                    lbl.api.Font.Bold = True
                    lbl.api.HorizontalAlignment = -4131  # xlLeft

                    # Materiál: label + blue fill
                    mat = sheet.cells(r,6)
                    mat.value = "Materiál:"
                    mat.api.Interior.Color = 0xD9E1F2
                    sheet.cells(r,7).value = f"=SUM(G{section_start}:G{r-1})"

                    # Práca: label + blue fill
                    pr = sheet.cells(r,9)
                    pr.value = "Práca:"
                    pr.api.Interior.Color = 0xD9E1F2
                    sheet.cells(r,10).value = f"=SUM(J{section_start}:J{r-1})"

                    # Rounded total in K
                    sheet.cells(r,11).value = f"=ROUNDUP(SUM(K{section_start}:K{r-1}),0)"

                    # Draw full grid border B→K
                    rng_sp = sheet.range(sheet.cells(r,2), sheet.cells(r,11))
                    draw_full_border(rng_sp)

                    insert_position += 1

                # --- Section header row ---
                sheet.range(f"{insert_position}:{insert_position}").insert('down')
                hdr = sheet.range(sheet.cells(insert_position,2),
                                  sheet.cells(insert_position,11))
                hdr.api.Merge()
                cell_hdr = sheet.cells(insert_position,2)
                cell_hdr.value = section
                cell_hdr.api.Font.Bold = True
                cell_hdr.api.Font.Size = 14
                cell_hdr.api.HorizontalAlignment = -4131  # xlLeft
                draw_full_border(hdr)

                section_start   = insert_position + 1
                prev_section    = section
                insert_position += 1

            # 5b) Insert the item row
            produkt, jednotky, dodavatel, odkaz = item[1], item[2], item[3], item[4]
            koeficient      = float(item[5])
            nakup_materialu = float(item[6])
            cena_prace      = float(item[7])
            pocet           = int(item[8])

            sheet.range(f"{insert_position}:{insert_position}").insert('down')
            src = sheet.range(f"{TEMPLATE_ROW+1}:{TEMPLATE_ROW+1}")
            dst = sheet.range(f"{insert_position}:{insert_position}")
            src.api.Copy()
            dst.api.PasteSpecial(Paste=-4163)

            # Clear any bold from this new row (cols B→K)
            rng_item = sheet.range(sheet.cells(insert_position,2),
                                   sheet.cells(insert_position,11))
            rng_item.api.Font.Bold = False

            # Fill columns B→K
            sheet.cells(insert_position,2).value  = counter
            sheet.cells(insert_position,3).value  = produkt
            sheet.cells(insert_position,4).value  = jednotky
            sheet.cells(insert_position,5).value  = pocet
            sheet.cells(insert_position,6).value  = f"=N{insert_position}*M{insert_position}"  # JC materiál
            sheet.cells(insert_position,7).value  = f"=F{insert_position}*E{insert_position}"  # Spolu materiál
            sheet.cells(insert_position,8).value  = f"=E{insert_position}"                 # Počet prác
            sheet.cells(insert_position,9).value  = cena_prace                              # JC práca
            sheet.cells(insert_position,10).value = f"=I{insert_position}*H{insert_position}"  # Spolu práca
            sheet.cells(insert_position,11).value = f"=G{insert_position}+J{insert_position}"  # Celkom

            # Extras: coefficient, purchase, profit, margin, test
            sheet.cells(insert_position,13).value = koeficient
            sheet.cells(insert_position,14).value = nakup_materialu
            sheet.cells(insert_position,15).value = f"=N{insert_position}*E{insert_position}"
            sheet.cells(insert_position,16).value = f"=G{insert_position}-O{insert_position}"
            sheet.cells(insert_position,17).value = f"=P{insert_position}/G{insert_position}"

            # Draw full grid border B→K for this item
            draw_full_border(rng_item)

            # Hyperlink in column S
            if odkaz and dodavatel:
                try:
                    link_cell = sheet.cells(insert_position,19)
                    link_cell.value = dodavatel
                    link_cell.api.Hyperlinks.Add(
                        Anchor=link_cell.api,
                        Address=str(odkaz),
                        TextToDisplay=str(dodavatel)
                    )
                except:
                    pass

            counter         += 1
            insert_position += 1

        # 6) Final SPOLU row after last section
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

        # 7) Optional notes sheet
        if notes_text.strip():
            notes = wb.sheets.add(after=wb.sheets[-1])
            notes.name = "Poznámky"
            for i, line in enumerate(notes_text.splitlines(), start=1):
                notes.cells(i,1).value = line

        # 8) Save & cleanup
        wb.save()
        wb.close()
        app.quit()
        print(f"✅ Successfully exported to: {new_file}")

    except Exception as e:
        print("❌ Excel export failed:", e)
