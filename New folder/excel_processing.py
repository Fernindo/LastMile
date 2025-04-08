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

    try:
        shutil.copy(template_file, new_file)
    except Exception as e:
        print("❌ Failed to copy template.")
        print(f"🔍 Error: {e}")
        return

    app = xw.App(visible=False)
    try:
        wb = app.books.open(new_file)
        sheet = wb.sheets[0]

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

            # Instead of copying rows with .api (dangerous), just insert a new row and use the format from row 18
            sheet.range(f"{insert_position}:{insert_position}").insert(shift="down")
            sheet.range(f"{TEMPLATE_ROW}:{TEMPLATE_ROW}").copy(sheet.range(f"{insert_position}:{insert_position}"))

            # Fill in values
            sheet.cells(insert_position, 2).value = counter
            sheet.cells(insert_position, 3).value = produkt
            sheet.cells(insert_position, 4).value = jednotky
            sheet.cells(insert_position, 5).value = pocet
            sheet.cells(insert_position, 6).formula = f"=N{insert_position}*M{insert_position}"
            sheet.cells(insert_position, 7).formula = f"=F{insert_position}*E{insert_position}"
            sheet.cells(insert_position, 8).formula = f"=E{insert_position}"
            sheet.cells(insert_position, 9).value = cena_prace
            sheet.cells(insert_position,10).formula = f"=I{insert_position}*H{insert_position}"
            sheet.cells(insert_position,11).formula = f"=G{insert_position}+J{insert_position}"
            sheet.cells(insert_position,13).value = koeficient
            sheet.cells(insert_position,14).value = nakup_materialu
            sheet.cells(insert_position,15).formula = f"=N{insert_position}*E{insert_position}"
            sheet.cells(insert_position,16).formula = f"=G{insert_position}-O{insert_position}"
            sheet.cells(insert_position,17).formula = f"=P{insert_position}/G{insert_position}"

            # Skipping hyperlink for now
            # if odkaz and dodavatel:
            #     sheet.hyperlinks.add(sheet.cells(insert_position, 19), address=str(odkaz), text_to_display=str(dodavatel))

            insert_position += 1
            counter += 1

        if notes_text.strip():
            try:
                notes_sheet = wb.sheets.add(name="Poznámky", after=wb.sheets[-1])
                for i, line in enumerate(notes_text.splitlines(), start=1):
                    notes_sheet.cells(i, 1).value = line
            except Exception as e:
                print("⚠ Failed to add notes sheet:", e)

        wb.save()
        print(f"✅ Successfully exported to: {new_file}")

    except Exception as e:
        print("❌ Failed during Excel export.")
        print(f"🔍 Error: {e}")
    finally:
        wb.close()
        app.quit()
