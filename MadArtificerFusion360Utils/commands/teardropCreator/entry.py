import adsk.core
import os

import adsk.fusion
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.ADDIN_NAME}_teardropCreator'
CMD_NAME = 'Teardrop Hole Generator'
CMD_Description = 'Auto create teardrop holes for better 3d printing'

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
    start_selection = inputs.addSelectionInput('edgeSelection', "Teardrop Start", "Select edge of hole")
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

    create_teardrop(circle, orientation_axis, extent, flipInput.isDirectionFlipped)


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
    circleFace = get_circle_face(circle)

    extentInput = inputs.itemById('extentSelection')
    extent = extentInput.selection(0).entity
    
    # args.areInputsValid = are_faces_parallel(circleFace, extent)
    args.areInputsValid = True

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []

def get_circle_face(circle: adsk.fusion.BRepEdge) -> adsk.fusion.BRepFace | None:
    faces = circle.faces
    plane = None
    for i in range(faces.count):
        face: adsk.fusion.BRepFace = faces.item(i)
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            plane = face

    return plane

def are_faces_parallel(face1, face2):
    # Get the normals of the faces
    normal1 = face1.geometry.normal
    normal2 = face2.geometry.normal
    
    # Compute the dot product of the normals
    dot_product = normal1.dotProduct(normal2)
    
    # Check if the dot product is close to 1 or -1
    # If it is close to 1, the faces are parallel; if it is close to -1, they are antiparallel
    return abs(dot_product) > 0.99

def create_teardrop(circle: adsk.fusion.BRepEdge, orientation_axis: adsk.fusion.ConstructionAxis, end_plane: adsk.fusion.BRepFace, flip: bool):
    circle_face = get_circle_face(circle)
    component = circle_face.body.parentComponent
    sketches = component.sketches
    sketch = sketches.add(circle_face)

    sketch.isComputeDeferred = True
    sketch.project(circle)
    sketch.project(orientation_axis)

    s_circle = sketch.sketchCurves.sketchCircles.item(0)
    s_axis = sketch.sketchCurves.sketchLines.item(0)
    center = s_circle.centerSketchPoint
    if flip:
        diff = -s_circle.radius*2
    else:
        diff = s_circle.radius*2
    next_point = adsk.core.Point3D.create(center.geometry.x + diff, center.geometry.y + diff, 0)
    anchor_line = sketch.sketchCurves.sketchLines.addByTwoPoints(center, next_point)
    anchor_line.isConstruction = True
    anchor_point = anchor_line.endSketchPoint

    teardrop1 = sketch.sketchCurves.sketchLines.addByTwoPoints(anchor_point, adsk.core.Point3D.create(anchor_point.geometry.x+1, anchor_point.geometry.y+1,0))
    teardrop2 = sketch.sketchCurves.sketchLines.addByTwoPoints(anchor_point, adsk.core.Point3D.create(anchor_point.geometry.x+1, anchor_point.geometry.y+1,0))
    
    # add constraints
    sketch.geometricConstraints.addParallel(s_axis, anchor_line)
    sketch.geometricConstraints.addCoincident(teardrop1.endSketchPoint, s_circle)
    sketch.geometricConstraints.addCoincident(teardrop2.endSketchPoint, s_circle)
    sketch.geometricConstraints.addTangent(teardrop1, s_circle)
    sketch.geometricConstraints.addTangent(teardrop2, s_circle)
    sketch.geometricConstraints.addPerpendicular(teardrop1, teardrop2)

    sketch.isComputeDeferred = False

    # add extrude through extent
    extrude_profile = None
    for i in range(sketch.profiles.count):
        profile = sketch.profiles.item(i)
        
        if profile.face.edges.count == 3:
            num_line = 0
            num_arc = 0
            for j in range(3):
                geo_type = profile.face.edges.item(j)
                if isinstance(geo_type.geometry, adsk.core.Line3D):
                    num_line += 1
                elif isinstance(geo_type.geometry, adsk.core.Arc3D):
                    num_arc += 1
            if num_line == 2 and num_arc == 1:
                extrude_profile = profile

    if extrude_profile is not None:
        extrude_input = component.features.extrudeFeatures.createInput(extrude_profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        extrude_input.setOneSideExtent(adsk.fusion.ToEntityExtentDefinition.create(end_plane, False), adsk.fusion.ExtentDirections.NegativeExtentDirection)
        component.features.extrudeFeatures.add(extrude_input)
