import adsk.core
import adsk.fusion
import traceback
import os
import time
from collections import defaultdict

def is_part(component):
    return component.occurrences.count == 0

def save_parts(folder, parts_by_material):
    folder_path = folder + f"/export_{time.time()}"
    os.makedirs(folder_path)
    for material in parts_by_material:
        material_folder = folder_path + material
        os.makedirs(material_folder)

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Get the active design
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            ui.messageBox('Active product is not a Fusion 360 design', 'Invalid Design')
            return
        
        root_comp = design.rootComponent
        
        folderDialog = ui.createFolderDialog()
        folderDialog.title = "Export Directory"
        result = folderDialog.showDialog()
        if result == adsk.core.DialogResults.DialogOK:
            # Get all components in the design
            components = design.allComponents

            parts_by_material = defaultdict(list)
            for component in components:
                if is_part(component):
                    material = component.material
                    parts_by_material[material.name].append(component)

            export_mgr = design.exportManager
            folder_path = folderDialog.folder + f"/export_{time.time()}"
            os.makedirs(folder_path)
            for material in parts_by_material:
                if "plastic" in material.lower():
                    material_folder = folder_path + "/" + material
                    os.makedirs(material_folder)
                    for part in parts_by_material[material]:
                        part_filename = f"{material_folder}/{part.name}_{part.id}_{root_comp.allOccurrencesByComponent(part).count}.stl"
                        export_opts = export_mgr.createSTLExportOptions(part, part_filename)
                        export_opts.meshRefinement = 0
                        export_mgr.execute(export_opts)


            ui.messageBox("Done exporting")
        else:
            return

    except:
        if ui:
            ui.messageBox('Error:\n{}'.format(traceback.format_exc()))

# Run the script
if __name__ == '__main__':
    run(None)