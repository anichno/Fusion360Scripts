import adsk.core
import adsk.fusion
import traceback

def is_part(component):
    return component.occurrences.count == 0

# def resolve_parents(component, parentList):
#     if component.assemblyContext is not None:
#         parentList.append(component.assemblyContext.component)

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

        # Get all components in the design
        components = design.allComponents

        default_material_components = list()
        # Iterate through each component and check if it has a material
        for component in components:
            if is_part(component):
                material = component.material
                if material.name == "Default":
                    default_material_components.append(component.name)
                    # parents = list()
                    # resolve_parents(component, parents)
                    # ui.messageBox(f"parents")
                # if material is not None:
                # ui.messageBox(f"component: {component.name} : material: {material.name}")

        if len(default_material_components) == 0:
            ui.messageBox('Material check completed.', 'Material Check Success')
        else:
            ui.messageBox("The following components have not been assigned a material:\n\t{}".format("\n\t".join(default_material_components)), "Material Check Failed")

    except:
        if ui:
            ui.messageBox('Error:\n{}'.format(traceback.format_exc()))

# Run the script
if __name__ == '__main__':
    run(None)