import adsk.core
import os

import adsk.fusion
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.ADDIN_NAME}_unsupportedHole'
CMD_NAME = 'Unsupported Hole Supporter'
CMD_Description = 'Auto support unsupported holes for better 3d printing'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # Where to start teardrop (sketch will be on the plane of this circular edge)
    start_selection = inputs.addSelectionInput('edgeSelection', "Hole Start", "Select edge of hole")
    start_selection.setSelectionLimits(1, 1)
    start_selection.addSelectionFilter('CircularEdges')

    # Number of support layers
    # num_layers_input = inputs.addValueInput('numLayersValue', "Number of support layers", "int", "2")
    num_layers_input = inputs.addIntegerSpinnerCommandInput('numLayersValue', "Number of support layers", 1, 10, 1, 2)

    # Support layer thickness
    thickness_input = inputs.addValueInput('thicknessValue', "Layer thickness", "mm", adsk.core.ValueInput.createByString("0.2mm"))


    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    
    edgeInput = inputs.itemById('edgeSelection')
    circle = edgeInput.selection(0).entity

    num_layers_input = inputs.itemById('numLayersValue')
    num_layers = num_layers_input.value

    layerThicknessInput = inputs.itemById('thicknessValue')
    layer_thickness = layerThicknessInput.value

    # create_teardrop(circle, orientation_axis, extent, flipInput.isDirectionFlipped)
    create_supports(circle, num_layers, layer_thickness)


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')

    

# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    layerThicknessInput = inputs.itemById('thicknessValue')
    args.areInputsValid = layerThicknessInput.value > 0.0

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []

# Via ChatGPT
def is_point_on_same_side(point, line, ref_line):
    # Get the start and end points of the SketchLine
    start_point = line.startSketchPoint.geometry
    end_point = line.endSketchPoint.geometry

    # Define vectors along the SketchLine and from the SketchLine to the point
    line_vector = adsk.core.Vector3D.create(end_point.x - start_point.x, end_point.y - start_point.y, 0)
    point_vector = adsk.core.Vector3D.create(point.x - start_point.x, point.y - start_point.y, 0)

    # Get a point on the reference line (use the start point of the reference line)
    ref_point = ref_line.startSketchPoint.geometry
    ref_vector = adsk.core.Vector3D.create(ref_point.x - start_point.x, ref_point.y - start_point.y, 0)

    # Calculate the cross product of line_vector with point_vector and ref_vector
    cross_product_point = line_vector.crossProduct(point_vector)
    cross_product_ref = line_vector.crossProduct(ref_vector)

    # Determine if the point is on the same side as the reference line
    same_side = (cross_product_point.z * cross_product_ref.z) >= 0

    return same_side


def create_supports(circle: adsk.fusion.BRepEdge, num_layers: int, layer_thickness: float):
    circle_face = futil.get_circle_face(circle)
    component = circle_face.body.parentComponent
    sketches = component.sketches
    sketch: adsk.fusion.Sketch = sketches.add(circle_face)

    sketch.isComputeDeferred = True

    for edge in circle_face.edges:
        sketch.project(edge)

    assert len(sketch.sketchCurves.sketchCircles) == 2

    if sketch.sketchCurves.sketchCircles[0].geometry.radius < sketch.sketchCurves.sketchCircles[1].geometry.radius:
        hole_circle = sketch.sketchCurves.sketchCircles[0]
        outer_circle = sketch.sketchCurves.sketchCircles[1]
    else:
        hole_circle = sketch.sketchCurves.sketchCircles[1]
        outer_circle = sketch.sketchCurves.sketchCircles[0]

    center = hole_circle.centerSketchPoint

    num_sides = num_layers*2
    pattern = sketch.sketchCurves.sketchLines.addScribedPolygon(center, num_sides, 0, 1.0, False)

    sketch.geometricConstraints.addHorizontal(pattern[0])

    lines = list()
    for i, line in enumerate(pattern):
        line.isConstruction = True

        # add line which extends all the way to outer_circle
        new_line = sketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(1,0,0))
        sketch.geometricConstraints.addCollinear(line, new_line)
        sketch.geometricConstraints.addCoincident(new_line.startSketchPoint, outer_circle)
        sketch.geometricConstraints.addCoincident(new_line.endSketchPoint, outer_circle)

        lines.append(new_line)

        if i > 2:
            # adding constraint to all lines over constrains
            continue
        sketch.geometricConstraints.addTangent(line, hole_circle)

    parallel_lines = list()
    for i in range(num_sides//2):
        parallel_lines.append((lines[i], lines[num_sides//2+i]))

    sketch.isComputeDeferred = False

    # For each set of parallel lines, get all of the outside profiles and
    # extrude them the correct distance depending on their layer
    for i, (line1, line2) in enumerate(parallel_lines):
        extrude_profiles = adsk.core.ObjectCollection.create()
        for profile in sketch.profiles:
            centroid = profile.areaProperties().centroid
            if not is_point_on_same_side(centroid, line1, line2) or not is_point_on_same_side(centroid, line2, line1):
                extrude_profiles.add(profile)

        component.features.extrudeFeatures.addSimple(extrude_profiles, adsk.core.ValueInput.createByReal(layer_thickness * (i+1)), adsk.fusion.FeatureOperations.JoinFeatureOperation)
