import maya.cmds as cmds
import maya.mel as mel

"""
cloth_buddy.py

This an a tool used to more efficiently and cleanly setup full wardrobes

Will nicely group and parent all cloth, in_mesh, ncloth nodes, nrigids, and constraints

By Chay

create_ui()

"""

def create_nCloth_simulation():
    selection = cmds.ls(selection=True, transforms=True)

    if not selection:
        cmds.warning("Please select at least one transform.")
        return
    
    # Check or create nucleus_grp
    if not cmds.objExists("nucleus_grp"):
        cmds.group(em=True, name="nucleus_grp")

    for obj in selection:
        # Clear the selection and select only the current object
        cmds.select(clear=True)
        cmds.select(obj)
    
        # Apply nCloth to the selected object
        cmds.nClothCreate()
    
        # Ensure we get the nCloth node correctly
        ncloth_shape_node = cmds.ls(type='nCloth', dag=True)
        if not ncloth_shape_node:
            cmds.warning(f"nCloth node not found for {obj}. Skipping...")
            continue
        ncloth_shape_node = ncloth_shape_node[-1]
        
        # Get the nCloth transform and rename it
        ncloth_transform = cmds.listRelatives(ncloth_shape_node, parent=True)
        if not ncloth_transform:
            cmds.warning(f"nCloth transform not found for {obj}. Skipping...")
            continue
        ncloth_transform = cmds.rename(ncloth_transform[0], obj + '_nCloth')
        
        # Get the nCloth shape node and rename it
        ncloth_shape_node = cmds.listRelatives(ncloth_transform, shapes=True)
        if not ncloth_shape_node:
            cmds.warning(f"nCloth shape node not found for {obj}. Skipping...")
            continue
        ncloth_shape_node = ncloth_shape_node[0]
        
        # Set nCloth-specific default attributes
        cmds.setAttr(f"{ncloth_shape_node}.thickness", 0.100)
        cmds.setAttr(f"{ncloth_shape_node}.selfCollideWidthScale", 0.15)
        cmds.setAttr(f"{ncloth_shape_node}.friction", 0.5)
        cmds.setAttr(f"{ncloth_shape_node}.damp", 0.1)
        cmds.setAttr(f"{ncloth_shape_node}.collideStrength", 0.5)
        cmds.setAttr(f"{ncloth_shape_node}.selfCollisionFlag", 4)
        cmds.setAttr(f"{ncloth_shape_node}.maxSelfCollisionIterations", 100)
        cmds.setAttr(f"{ncloth_shape_node}.pointMass", 2)
        cmds.setAttr(f"{ncloth_shape_node}.pushOutRadius", 0)
        cmds.setAttr(f"{ncloth_shape_node}.scalingRelation", 1)
        cmds.setAttr(f"{ncloth_shape_node}.stretchResistance", 100)
        cmds.setAttr(f"{ncloth_shape_node}.compressionResistance", 80)
        cmds.setAttr(f"{ncloth_shape_node}.bendResistance", 4)
        cmds.setAttr(f"{ncloth_shape_node}.bendAngleDropoff", 0.6)
        cmds.setAttr(f"{ncloth_shape_node}.collideLastThreshold", 1)
        cmds.setAttr(f"{ncloth_shape_node}.stretchDamp", 10)
        cmds.setAttr(f"{ncloth_shape_node}.selfTrappedCheck", 1)
        cmds.setAttr(f"{ncloth_shape_node}.lift", 0.1)
        cmds.setAttr(f"{ncloth_shape_node}.drag", 0.15)
        cmds.setAttr(f"{ncloth_shape_node}.tangentialDrag", 0.1)
        
        # Rename the original object and turn off intermediate object
        inMesh = cmds.rename(obj, obj + '_inMesh')
        new_shape_node = cmds.listRelatives(inMesh, shapes=True)
        if not new_shape_node:
            cmds.warning(f"Shape node not found for {obj}. Skipping...")
            continue
        new_shape_node = new_shape_node[0]
        cmds.setAttr(f"{new_shape_node}.intermediateObject", 0)
        
        # Hide the inMesh by default
        cmds.setAttr(f"{inMesh}.visibility", 0)
        
        # Find the newly generated output mesh from nCloth
        polysurface = cmds.listConnections(f"{ncloth_shape_node}.outputMesh", destination=True, shapes=True)
        if polysurface:
            polysurface_transform = cmds.listRelatives(polysurface[0], parent=True)[0]
            polysurface_transform = cmds.rename(polysurface_transform, obj + '_outMesh')
        else:
            polysurface_transform = None
    
        # Ensure all nodes are grouped properly before moving to the next object
        nodes_to_group = [inMesh, ncloth_transform]
        if polysurface_transform:
            nodes_to_group.append(polysurface_transform)
        
        cmds.select(clear=True)
        
        # Create the simulation group for this object
        sim_grp = cmds.group(nodes_to_group, name=obj + '_sim_grp')
        
        # Parent the simulation group under nucleus_grp
        cmds.parent(sim_grp, "nucleus_grp")
        
        # Check if a nucleus node was created and set default settings
        nucleus_nodes = cmds.ls(type="nucleus")
        if nucleus_nodes:
            latest_nucleus = nucleus_nodes[-1]
            # Set default nucleus settings if it's new
            if cmds.nodeType(latest_nucleus) == "nucleus":
                cmds.setAttr(f"{latest_nucleus}.subSteps", 60)
                cmds.setAttr(f"{latest_nucleus}.maxCollisionIterations", 60)
                cmds.setAttr(f"{latest_nucleus}.spaceScale", 0.01)
                cmds.setAttr(f"{latest_nucleus}.airDensity", 0.1)
                cmds.setAttr(f"{latest_nucleus}.collisionLayerRange", 10)


def create_collider():
    selection = cmds.ls(selection=True, transforms=True)

    if not selection:
        cmds.warning("Please select at least one transform.")
        return

    # Check or create nucleus_grp and nRigid_grp
    if not cmds.objExists("nucleus_grp"):
        cmds.group(em=True, name="nucleus_grp")

    if not cmds.objExists("nRigid_grp"):
        cmds.group(em=True, name="nRigid_grp", parent="nucleus_grp")

    for obj in selection:
        # Create a passive collider (nRigid)
        cmds.select(obj)
        nRigid = mel.eval('makeCollideNCloth')
        nRigidTransform = cmds.listRelatives(nRigid, parent=True)[0]
        nRigidFinal = cmds.rename(nRigidTransform, 'nRigid_' + obj)
        newRigidXform = cmds.rename(obj, obj + '_collider')

        # Set the specific collider attributes
        cmds.setAttr(f"{nRigidFinal}.thickness", 0.1)
        cmds.setAttr(f"{nRigidFinal}.friction", 0.5)
        cmds.setAttr(f"{nRigidFinal}.collideStrength", 0.5)
        cmds.setAttr(f"{nRigidFinal}.pushOutRadius", 0.1)
        cmds.setAttr(f"{nRigidFinal}.fieldDistance", 2)
        cmds.setAttr(f"{nRigidFinal}.fieldScale[1].fieldScale_Position", 0.5)

        # Group the collider under nRigid_grp
        cmds.parent(nRigidFinal, "nRigid_grp")
        cmds.parent(newRigidXform, "nucleus_grp")


def create_constraint():
    constraint_type = cmds.optionMenu('constraintMenu', query=True, value=True)

    if constraint_type == 'point to surface':
        create_point_to_surface_constraint()
    elif constraint_type == 'comp to comp':
        create_comp_to_comp_constraint()
    elif constraint_type == 'exclude collide pair':
        create_exclude_collide_pair_constraint()
    else:
        cmds.warning("Unknown constraint type.")


def create_point_to_surface_constraint():
    selected_verts = cmds.filterExpand(sm=31)  # Selected vertices
    selected_objs = cmds.ls(sl=True, o=True)  # Selected objects

    if len(selected_verts) < 1 or len(selected_objs) < 2:
        cmds.warning("Please select components and a target object.")
        return

    selected = selected_verts[0]
    selected_object_fullname = selected.split('_outMesh.vtx[')[0]

    target_obj = selected_objs[1]

    base_name = "p2s_" + selected_verts[0].split(".")[0] + "_TO_" + target_obj
    index = 1

    while cmds.objExists(base_name + "_" + str(index)):
        index += 1

    constraint_name = base_name + "_" + str(index)

    cmds.select(selected_verts + [target_obj])
    newly_created = mel.eval('createNConstraint pointToSurface 0;')

    constraint_transform = cmds.listRelatives(newly_created, parent=True)[0]
    cmds.rename(constraint_transform, constraint_name)

    constraint_group_name = 'nucleus_grp|' + selected_object_fullname + '_sim_grp' + '|constraints_grp'

    if not cmds.objExists(constraint_group_name):
        new_group = cmds.group(empty=True, name='constraints_grp', parent=selected_object_fullname + '_sim_grp')
        cmds.parent(constraint_name, new_group)
    else:
        cmds.parent(constraint_name, constraint_group_name)

    print('Point to Surface Constraint created and grouped.')

def create_comp_to_comp_constraint():
    selected_components = cmds.filterExpand(sm=(31, 32))  # Supports vertices and edges

    if not selected_components:
        cmds.warning("Please select vertices or edges.")
        return

    first_obj = selected_components[0].split('.')[0]  # Get the object name from the first component

    # Extract the base name (e.g., "poop" from "poop_outMesh")
    base_name = first_obj.split('_outMesh')[0]

    constraint_base_name = "p2p_" + base_name
    index = 1

    while cmds.objExists(constraint_base_name + "_" + str(index)):
        index += 1

    constraint_name = constraint_base_name + "_" + str(index)

    # Create the component-to-component constraint
    cmds.select(selected_components)
    newly_created = mel.eval('createNConstraint pointToPoint 0;')

    constraint_transform = cmds.listRelatives(newly_created, parent=True)[0]
    cmds.rename(constraint_transform, constraint_name)

    # Grouping based on the base name (e.g., "poop_sim_grp")
    constraint_group_name = 'nucleus_grp|' + base_name + '_sim_grp' + '|constraints_grp'

    if not cmds.objExists(constraint_group_name):
        new_group = cmds.group(empty=True, name='constraints_grp', parent=base_name + '_sim_grp')
        cmds.parent(constraint_name, new_group)
    else:
        cmds.parent(constraint_name, constraint_group_name)

    print('Component to Component Constraint created and grouped.')

def create_exclude_collide_pair_constraint():
    selection = cmds.ls(selection=True, transforms=True)

    if len(selection) < 2:
        cmds.warning("Please select two transforms for collision exclusion.")
        return

    first_obj = selection[0]
    second_obj = selection[1]

    base_name = f"{first_obj}_exclude_{second_obj}"
    index = 1

    while cmds.objExists(base_name + "_" + str(index)):
        index += 1

    constraint_name = base_name + "_" + str(index)

    cmds.select(first_obj, second_obj)
    newly_created = mel.eval('createNConstraint collisionExclusion 0;')

    constraint_transform = cmds.listRelatives(newly_created, parent=True)[0]
    cmds.rename(constraint_transform, constraint_name)

    # Grouping based on the base name (e.g., "poop_sim_grp")
    base_name = first_obj.split('_outMesh')[0]
    constraint_group_name = 'nucleus_grp|' + base_name + '_sim_grp' + '|constraints_grp'

    if not cmds.objExists(constraint_group_name):
        new_group = cmds.group(empty=True, name='constraints_grp', parent=base_name + '_sim_grp')
        cmds.parent(constraint_name, new_group)
    else:
        cmds.parent(constraint_name, constraint_group_name)

    print('Exclude Collide Pair Constraint created and grouped.')


def set_initial_pose():
    # Run the MEL commands to set initial pose
    mel.eval("setDynStartState;")
    mel.eval("SetNClothStartFromMesh;")

def create_ui():
    # Check if the window exists and delete if it does
    if cmds.window("nClothTool", exists=True):
        cmds.deleteUI("nClothTool")

    # Create the window
    window = cmds.window("nClothTool", title="Cloth Buddy", widthHeight=(300, 300))

    # Create a column layout
    cmds.columnLayout(adjustableColumn=True)

    # Section for nCloth and Collider creation
    cmds.frameLayout(label="Creation", collapsable=True, marginHeight=10, marginWidth=10)
    cmds.columnLayout(adjustableColumn=True)
    cmds.button(label="Make nCloth", command=lambda *args: create_nCloth_simulation(), height=40, bgc=[0.39, 0.58, 0.93])  # Cornflower blue
    cmds.separator(height=10, style="in")
    cmds.button(label="Make Collider", command=lambda *args: create_collider(), height=40, bgc=[1.0, 0.6, 0.4])  # Light warming orange/red
    cmds.setParent("..")
    cmds.setParent("..")

    # Section for Constraints
    cmds.frameLayout(label="Constraints", collapsable=True, marginHeight=10, marginWidth=10)
    cmds.columnLayout(adjustableColumn=True)
    cmds.optionMenu('constraintMenu', label='Constraint Type')
    cmds.menuItem(label='point to surface')
    cmds.menuItem(label='comp to comp')
    cmds.menuItem(label='exclude collide pair')
    cmds.separator(height=10, style="in")
    cmds.button(label="Create Constraint", command=lambda *args: create_constraint(), height=40)
    cmds.setParent("..")
    cmds.setParent("..")

    # Section for Setting Initial Pose
    cmds.frameLayout(label="Misc", collapsable=True, marginHeight=10, marginWidth=10)
    cmds.columnLayout(adjustableColumn=True)
    cmds.button(label="Set Initial Pose", command=lambda *args: set_initial_pose(), height=40)
    cmds.setParent("..")
    cmds.setParent("..")

    # Show the window
    cmds.showWindow(window)

# Execute the UI
#create_ui()
