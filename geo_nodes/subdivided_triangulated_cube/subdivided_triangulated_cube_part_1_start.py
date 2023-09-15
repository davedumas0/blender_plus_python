"""
See YouTube tutorial here: https://youtu.be/Is8Qu7onvzM
"""
import random
import time

import bpy


################################################################
# helper functions BEGIN
################################################################


def purge_orphans():
    """
    Remove all orphan data blocks

    see this from more info:
    https://youtu.be/3rNqVPtbhzc?t=149
    """
    if bpy.app.version >= (3, 0, 0):
        # run this only for Blender versions 3.0 and higher
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    else:
        # run this only for Blender versions lower than 3.0
        # call purge_orphans() recursively until there are no more orphan data blocks to purge
        result = bpy.ops.outliner.orphans_purge()
        if result.pop() != "CANCELLED":
            purge_orphans()


def clean_scene():
    """
    Removing all of the objects, collection, materials, particles,
    textures, images, curves, meshes, actions, nodes, and worlds from the scene

    Checkout this video explanation with example

    "How to clean the scene with Python in Blender (with examples)"
    https://youtu.be/3rNqVPtbhzc
    """
    # make sure the active object is not in Edit Mode
    if bpy.context.active_object and bpy.context.active_object.mode == "EDIT":
        bpy.ops.object.editmode_toggle()

    # make sure non of the objects are hidden from the viewport, selection, or disabled
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_select = False
        obj.hide_viewport = False

    # select all the object and delete them (just like pressing A + X + D in the viewport)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # find all the collections and remove them
    collection_names = [col.name for col in bpy.data.collections]
    for name in collection_names:
        bpy.data.collections.remove(bpy.data.collections[name])

    # in the case when you modify the world shader
    # delete and recreate the world object
    world_names = [world.name for world in bpy.data.worlds]
    for name in world_names:
        bpy.data.worlds.remove(bpy.data.worlds[name])
    # create a new world data block
    bpy.ops.world.new()
    bpy.context.scene.world = bpy.data.worlds["World"]

    purge_orphans()


def active_object():
    """
    returns the currently active object
    """
    return bpy.context.active_object


def time_seed():
    """
    Sets the random seed based on the time
    and copies the seed into the clipboard
    """
    seed = time.time()
    print(f"seed: {seed}")
    random.seed(seed)

    # add the seed value to your clipboard
    bpy.context.window_manager.clipboard = str(seed)

    return seed


def set_fcurve_extrapolation_to_linear():
    for fc in bpy.context.active_object.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"


def create_data_animation_loop(obj, data_path, start_value, mid_value, start_frame, loop_length, linear_extrapolation=True):
    """
    To make a data property loop we need to:
    1. set the property to an initial value and add a keyframe in the beginning of the loop
    2. set the property to a middle value and add a keyframe in the middle of the loop
    3. set the property the initial value and add a keyframe at the end of the loop
    """
    # set the start value
    setattr(obj, data_path, start_value)
    # add a keyframe at the start
    obj.keyframe_insert(data_path, frame=start_frame)

    # set the middle value
    setattr(obj, data_path, mid_value)
    # add a keyframe in the middle
    mid_frame = start_frame + (loop_length) / 2
    obj.keyframe_insert(data_path, frame=mid_frame)

    # set the end value
    setattr(obj, data_path, start_value)
    # add a keyframe in the end
    end_frame = start_frame + loop_length
    obj.keyframe_insert(data_path, frame=end_frame)

    if linear_extrapolation:
        set_fcurve_extrapolation_to_linear()


def set_scene_props(fps, frame_count):
    """
    Set scene properties
    """
    scene = bpy.context.scene
    scene.frame_end = frame_count

    # set the world background to black
    world = bpy.data.worlds["World"]
    if "Background" in world.node_tree.nodes:
        world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

    scene.render.fps = fps

    scene.frame_current = 1
    scene.frame_start = 1


def scene_setup():
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()

    clean_scene()

    set_scene_props(fps, frame_count)

def create_node(node_tree, type_name):
    node_obj = node_tree.nodes.new(type=type_name)   
    return node_obj

def move_node(type_name, gx=0, gy=0):
    """
    Move a node by the specified amount in the x and y directions.

    Parameters:
    - node: The node to be moved.
    - dx: The amount to move the node in the x direction.
    - dy: The amount to move the node in the y direction.
    """
    type_name.location.x += gx
    type_name.location.y += gy

def create_link(node_tree, from_node, output_socket_name, to_node, input_socket_name):
    """
    Create a link between two nodes using the specified output and input socket names.

    Parameters:
    - node_tree: The node tree in which the nodes reside.
    - from_node: The source node from which the connection originates.
    - output_socket_name: The name of the output socket on the source node.
    - to_node: The destination node to which the connection leads.
    - input_socket_name: The name of the input socket on the destination node.
    """
    node_tree.links.new(from_node.outputs[output_socket_name], to_node.inputs[input_socket_name])
    
    
def add_geo_nodes_modifier(obj):
    """
    Adds a Geometry Nodes modifier to the given object and sets it as the active object.

    Parameters:
    - obj: The object to which the modifier should be added.
    """
    # Ensure the object is selected and active
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Add the Geometry Nodes modifier
    bpy.ops.node.new_geometry_nodes_modifier()
    node_tree = obj.modifiers["GeometryNodes"].node_group
    return node_tree

def clear_nodes(node_tree):
    """
    Clears all nodes from the specified node tree.

    Parameters:
    - node_tree: The node tree from which nodes should be removed.
    """
    for node in list(node_tree.nodes):  # Use list() to avoid issues during iteration
        node_tree.nodes.remove(node)
        
        
   
def create_mesh(mesh_type='PLANE', location=(0, 0, 0)):
    """
    Create a mesh of the specified type.

    Parameters:
    - mesh_type: Type of the mesh to be created ('PLANE', 'CUBE', 'SPHERE', etc.)
    - location: Location where the mesh should be created
    """
    if mesh_type == 'PLANE':
        bpy.ops.mesh.primitive_plane_add(location=location)
    elif mesh_type == 'CUBE':
        bpy.ops.mesh.primitive_cube_add(location=location)
    elif mesh_type == 'SPHERE':
        bpy.ops.mesh.primitive_uv_sphere_add(location=location)
    # ... Add more mesh types as needed
    return active_object()

# Usage:
# plane = create_mesh('PLANE', location=(0, 0, 0))
# cube = create_mesh('CUBE', location=(1, 1, 1))
# sphere = create_mesh('SPHERE', location=(2, 2, 2))

def move_object(obj, translation_vector=(0, 0, 0)):
    """
    Translates an object by the specified vector.

    Parameters:
    - obj: The object to be moved.
    - translation_vector: A tuple (dx, dy, dz) specifying the translation in each axis.
    """
    obj.location += bpy.Vector(translation_vector)
    
# Usage (commented out for reference):
# move_object(my_object, (1, 0, 0))  # Move the object 1 unit in the x-axis


def scale_object(obj, scale_factor=(1, 1, 1)):
    """
    Scales an object by the specified factor.

    Parameters:
    - obj: The object to be scaled.
    - scale_factor: A tuple (sx, sy, sz) specifying the scaling in each axis.
    """
    obj.scale *= bpy.Vector(scale_factor)

# Usage (commented out for reference):
# scale_object(my_object, (2, 2, 2))  # Double the object's size in all axes
 

def enter_edit_mode(obj):
    """
    Switches the given object to edit mode.

    Parameters:
    - obj: The object to be switched to edit mode.
    """
    # Ensure the object is selected
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Switch to edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    
# Usage (commented out for reference):
# enter_edit_mode(my_object)  # Switch the object to edit mode

def exit_edit_mode(obj):
    """
    Switches the given object back to object mode.

    Parameters:
    - obj: The object to be switched back to object mode.
    """
    # Ensure the object is selected
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Switch to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

# Usage (commented out for reference):
# exit_edit_mode(my_object)   # Switch the object back to object mode


def set_selection_mode(obj, mode='FACE'):
    """
    Set the selection mode in Edit Mode (VERTEX, EDGE, FACE).

    Parameters:
    - obj: The object to set the selection mode for.
    - mode: The selection mode ('VERTEX', 'EDGE', 'FACE').
    """
    # Check if the object is in edit mode, if not, switch to edit mode
    if obj.mode != 'EDIT':
        enter_edit_mode(obj)
    
    # Set the selection mode
    if mode == 'VERTEX':
        bpy.ops.mesh.select_mode(type='VERT')
    elif mode == 'EDGE':
        bpy.ops.mesh.select_mode(type='EDGE')
    elif mode == 'FACE':
        bpy.ops.mesh.select_mode(type='FACE')
    else:
        print(f"Unsupported mode: {mode}. Supported modes are VERTEX, EDGE, and FACE.")

# Usage (commented out for reference):
# set_selection_mode(my_object, mode='FACE')  # Set the object's selection mode to face selection

def duplicate_mesh(obj):
    """
    Duplicates a mesh object and returns the duplicate.

    Parameters:
    - obj: The mesh object to be duplicated.
    """
    # Ensure the object is selected and active
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # Duplicate the object
    bpy.ops.object.duplicate_move()
    
    # The duplicated object will be the active object after the operation
    duplicate_obj = bpy.context.active_object
    
    return duplicate_obj


def duplicate_node(node_tree, node):
    """
    Duplicates a node within a node tree and returns the duplicate.

    Parameters:
    - node_tree: The node tree in which the node resides.
    - node: The node to be duplicated.
    """
    # Ensure the node tree is active
    bpy.context.space_data.node_tree = node_tree
    
    # Make sure only the desired node is selected
    for n in node_tree.nodes:
        n.select = False
    node.select = True
    node_tree.nodes.active = node
    
    # Duplicate the node
    bpy.ops.node.duplicate()
    
    # The duplicated node will be the active node after the operation
    duplicate_node = node_tree.nodes.active
    
    return duplicate_node

def get_socket_names(node):
    """
    Returns the names of input and output sockets (pins) of a node.

    Parameters:
    - node: The node whose socket names are to be retrieved.

    Returns:
    - A dictionary with 'inputs' and 'outputs' keys.
    """
    socket_info = {
        'inputs': [socket.name for socket in node.inputs],
        'outputs': [socket.name for socket in node.outputs]
    }
    
    return socket_info

def get_active_geo_nodes_viewport_area():
    """
    Returns the active VIEW_3D area in the Geometry Nodes tab if Blender is in Object Mode.
    
    Returns:
    - The active VIEW_3D area in the Geometry Nodes tab, or None if there isn't one.
    """
    if bpy.context.mode != 'OBJECT':
        print("Not in Object Mode!")
        return None

    # Check if we're in the Geometry Nodes tab
    if bpy.context.screen.name != 'Geometry Nodes':
        print("Not in the Geometry Nodes tab!")
        return None

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            return area

    return None

def set_active_3d_view_to_wireframe():
    """
    Sets the shading mode of the active 3D Viewport in the Geometry Nodes tab/workspace to wireframe.
    """
    # Get the active 3D Viewport in the Geometry Nodes workspace
    active_3d_view = get_active_geo_nodes_viewport_area()

    if active_3d_view:
        # Set shading mode to wireframe
        active_3d_view.spaces[0].shading.type = 'WIREFRAME'
    else:
        print("No active 3D Viewport found in the Geometry Nodes workspace.")


################################################################
# helper functions END
################################################################
nodeList = {
    "GeometryNodeInstanceOnPoints",
    "NodeGroupInput",
    "NodeGroupOutput",
    "GeometryNodeDistributePointsOnFaces",
    "GeometryNodePointScale",
    "GeometryNodeAttributeTransfer",
    "GeometryNodeVectorMath",
    "GeometryNodeAttributeMath",
    "GeometryNodeAttributeProximity",
    "GeometryNodePointSeparate",
    "GeometryNodePointCombine",
    "GeometryNodeAttributeCombine",
    "GeometryNodeAttributeFill",
    "GeometryNodeAttributeRandomize",
    "GeometryNodeAttributeCurve",
    "GeometryNodeAttributeColorRamp",
    "GeometryNodeAttributeClamp",
    "GeometryNodeAttributeMix",
    "GeometryNodePointTranslate",
    "GeometryNodePointRotate",
    "GeometryNodePointScale",
    "GeometryNodeAttributeNormal",
    "GeometryNodeAttributeTangent",
    "GeometryNodeAttributeUVMap",
    "GeometryNodeAttributePosition",
    "GeometryNodeAttributeBounds",
    "GeometryNodeAttributeProximity",
    "GeometryNodePointInstance",
    "GeometryNodeMeshPrimitive",
    "GeometryNodeAttributeBoolean",
    "GeometryNodeSubdivideMesh",
    # Add more nodes as needed
}


################################################################
# workspace BEGIN
################################################################





def create_centerpiece():
    pass
################################################################
# workspace END
################################################################



def main():
    """
    Python code to generate an animated geo nodes node tree
    that consists of a subdivided & triangulated cube with animated faces
    """
    scene_setup()
    create_centerpiece()


if __name__ == "__main__":
    main()


#[ONLY MAKE CHANGES IN THE WORKING AREA]
