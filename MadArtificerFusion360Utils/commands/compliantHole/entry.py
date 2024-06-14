import adsk.core
import os

import adsk.fusion
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.ADDIN_NAME}_compliantHole'
CMD_NAME = 'Compliant Hole Generator'
CMD_Description = 'Auto create reliefs for holes to allow better friction fits in 3d printing'

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

    # Axis of print
    axis_selection = inputs.addSelectionInput('axisSelection', "Axis (Construction Only)", "Select axis of print orientation")
    axis_selection.setSelectionLimits(1,1)
    axis_selection.addSelectionFilter('ConstructionLines')

    # Teardrop extent
    extent_selection = inputs.addSelectionInput('extentSelection', "End face", "Select ")
    extent_selection.setSelectionLimits(1,1)
    extent_selection.addSelectionFilter('Faces')

    flip_selection = inputs.addDirectionCommandInput('flipSelection', 'Flip')

    flexture_input = inputs.addValueInput('flextureValue', 'Size of flexture', 'mm', adsk.core.ValueInput.createByString("1.5mm"))
    gap_input = inputs.addValueInput('gapValue', "Size of gap", 'mm', adsk.core.ValueInput.createByString("1mm"))

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

    axisInput = inputs.itemById('axisSelection')
    orientation_axis = axisInput.selection(0).entity

    extentInput = inputs.itemById('extentSelection')
    extent = extentInput.selection(0).entity

    flipInput = inputs.itemById('flipSelection')

    flextureInput = inputs.itemById('flextureValue')
    gapInput = inputs.itemById('gapValue')

    create_relief(circle, orientation_axis, extent, flipInput.isDirectionFlipped, flextureInput.expression, gapInput.expression)


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
    edgeInput = inputs.itemById('edgeSelection')
    circle = edgeInput.selection(0).entity
    circleFace = futil.get_circle_face(circle)

    extentInput = inputs.itemById('extentSelection')
    extent = extentInput.selection(0).entity
    
    args.areInputsValid = True

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []

def create_relief(circle: adsk.fusion.BRepEdge, orientation_axis: adsk.fusion.ConstructionAxis, end_plane: adsk.fusion.BRepFace, flip: bool, flexture_size, gap_size):
    circle_face = futil.get_circle_face(circle)
    component = circle_face.body.parentComponent
    sketches = component.sketches
    sketch: adsk.fusion.Sketch = sketches.add(circle_face)

    sketch.isComputeDeferred = True
    sketch.project(circle)
    sketch.project(orientation_axis)

    sketch.isComputeDeferred = False
    sketch.isComputeDeferred = True

    hole_circle = sketch.sketchCurves.sketchCircles[0]
    s_axis = sketch.sketchCurves.sketchLines[0]
    center = hole_circle.centerSketchPoint
    if flip:
        diff = -hole_circle.radius*2
    else:
        diff = hole_circle.radius*2

    # center line
    next_point = adsk.core.Point3D.create(center.geometry.x + diff, center.geometry.y + diff, 0)
    center_line = sketch.sketchCurves.sketchLines.addByTwoPoints(center, next_point)
    center_line.isConstruction = True

    sketch.geometricConstraints.addParallel(s_axis, center_line)
    sketch.geometricConstraints.addCoincident(center_line.endSketchPoint, hole_circle)

    # add flexture
    flexture_circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(center.geometry.x + hole_circle.radius*2,center.geometry.y + hole_circle.radius*2,0), 1)
    flexture_circle_dim = sketch.sketchDimensions.addDiameterDimension(flexture_circle, adsk.core.Point3D.create(1,1,1), True)
    flexture_circle_dim.parameter.expression = flexture_size

    sketch.geometricConstraints.addTangent(hole_circle, flexture_circle)

    sketch.isComputeDeferred = False
    sketch.isComputeDeferred = True

    flexture_line = sketch.sketchCurves.sketchLines.addByTwoPoints(center, flexture_circle.centerSketchPoint)
    flexture_line.isConstruction = True
    flexture_line_dim = sketch.sketchDimensions.addAngularDimension(center_line, flexture_line, adsk.core.Point3D.create(1,1,1))
    flexture_line_dim.parameter.expression = '10 deg'
    
    sketch.isComputeDeferred = False
    sketch.isComputeDeferred = True

    # add gap
    gap_frame_circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(center, hole_circle.radius * 2 + flexture_circle.radius*2)
    sketch.geometricConstraints.addTangent(gap_frame_circle, flexture_circle)

    sketch.isComputeDeferred = False
    sketch.isComputeDeferred = True

    gap_circle

    # add constraints

    sketch.isComputeDeferred = False

    # # add extrude through extent
    # profile_bounds = [s_circle, teardrop1, teardrop2]
    # extrude_profile = futil.get_profile_from_sketch_bounds(sketch, profile_bounds)

    # if extrude_profile is not None:
    #     extrude_input = component.features.extrudeFeatures.createInput(extrude_profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
    #     extrude_input.setOneSideExtent(adsk.fusion.ToEntityExtentDefinition.create(end_plane, False), adsk.fusion.ExtentDirections.NegativeExtentDirection)
    #     component.features.extrudeFeatures.add(extrude_input)
