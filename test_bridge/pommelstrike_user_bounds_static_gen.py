bl_info = {
    "name": "pommelstrike BG3 Collision Bound Creator",
    "blender": (3, 0, 0),
    "category": "Object",
    "author": "pommelstrike",
    "description": "Creates collision box bounds (for BG3 Physics XML export) using presets, vertex selections, tiling, and mirroring.",
    "location": "View3D > N-Panel > BG3 Bound",
    "version": (2, 0, 6),
}

import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector, Matrix, Quaternion

### PRESET DEFINITIONS ###
# Each preset is defined as a tuple: (identifier, display name, description, (width, height, depth))
PRESETS = [
    ("DOOR", "Door Shape", "Door shape (2.09 x 0.16 x 2.88 m)", (2.09, 0.16, 2.88)),
    ("HORZ_LUMBER", "Horizontal Lumber", "Horizontal lumber (4 x 0.41 x 0.405 m)", (4.0, 0.41, 0.405)),
    ("VERT_LUMBER", "Vertical Lumber", "Vertical lumber (0.408 x 2.64 x 0.426 m)", (0.408, 2.64, 0.426)),
    ("LEGO_BRICK", "Lego Brick", "Lego brick (0.807 x 0.377 x 0.395 m)", (0.807, 0.377, 0.395)),
    ("LONG_LEGO_BRICK", "Long Lego Brick", "Long lego brick (2 x 0.6 x 0.3 m)", (2.0, 0.6, 0.3)),
    ("CUSTOM", "Custom", "Custom: use Add Cube tool", None),
]

def preset_items(self, context):
    items = []
    for preset in PRESETS:
        identifier, name, description, dims = preset
        items.append((identifier, name, description))
    return items

### PROPERTY REGISTRATION ###
def register_properties():
    # Remove existing properties if they exist
    if "bg3_collision_preset" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["bg3_collision_preset"]
    bpy.types.Scene.bg3_collision_preset = bpy.props.EnumProperty(
        name="Preset",
        description="Select a collision bound preset",
        items=preset_items,
        default=0,  # default index 0 -> "DOOR"
    )
    if "tile_rows" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["tile_rows"]
    bpy.types.Scene.tile_rows = bpy.props.IntProperty(name="Rows", default=2, min=1)
    if "tile_columns" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["tile_columns"]
    bpy.types.Scene.tile_columns = bpy.props.IntProperty(name="Columns", default=2, min=1)
    if "tile_spacing" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["tile_spacing"]
    bpy.types.Scene.tile_spacing = bpy.props.FloatProperty(name="Spacing", default=2.0, min=0.0)
    if "mirror_offset" in bpy.types.Scene.__annotations__:
        del bpy.types.Scene.__annotations__["mirror_offset"]
    bpy.types.Scene.mirror_offset = bpy.props.FloatProperty(name="Mirror Offset", default=2.0, min=0.0)

### UTILITY: Compute Oriented Bounding Box (OBB) from vertices ###
def compute_obb(vertices):
    """
    Compute an oriented bounding box (OBB) for a list of mathutils.Vector vertices.
    Returns:
      - world_center: Vector of the computed center in world space.
      - R: 3x3 rotation Matrix (principal axes).
      - extents: Vector of full dimensions along each principal axis.
    """
    if not vertices:
        return Vector((0,0,0)), Matrix.Identity(3), Vector((0,0,0))
    arr = np.array([v[:] for v in vertices])
    mean = np.mean(arr, axis=0)
    centered = arr - mean
    cov = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eig(cov)
    order = eigenvalues.argsort()[::-1]
    eigenvectors = eigenvectors[:, order]
    R = Matrix(eigenvectors.tolist())
    local_coords = [R.inverted() @ Vector(v) for v in centered]
    local_arr = np.array([v[:] for v in local_coords])
    local_min = local_arr.min(axis=0)
    local_max = local_arr.max(axis=0)
    extents = local_max - local_min  # full dimensions
    local_center = (local_min + local_max) / 2.0
    world_center = Vector(mean) + R @ Vector(local_center)
    return world_center, R, extents

### OPERATOR: Create Collision Bound from Preset ###
class BG3COLLISION_OT_create_bound(bpy.types.Operator):
    """Create a collision bound from a preset.
    The new bound will be created at the 3D cursor location,
    then its Z coordinate is raised by 1.44 m (to align with the floor)."""
    bl_idname = "bg3collision.create_bound"
    bl_label = "Create Collision Bound"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        preset_id = scene.bg3_collision_preset  # This returns the identifier string
        dims = None
        for preset in PRESETS:
            if preset[0] == preset_id:
                dims = preset[3]
                break

        if preset_id == "CUSTOM" or dims is None:
            bpy.ops.wm.tool_set_by_id(name="builtin.primitive_cube_add")
            self.report({'INFO'}, "Custom: Use the Add Cube tool.")
            return {'FINISHED'}

        # Place the new bound at the 3D cursor location with an offset in Z.
        cursor_loc = scene.cursor.location.copy()
        cursor_loc.z += 1.44  # Raise by 1.44 m

        bpy.ops.mesh.primitive_cube_add(size=2, location=cursor_loc)
        obj = context.active_object
        obj.name = f"{preset_id}_Bound"  # Temporary name; will be renamed later
        scale_factors = Vector((dims[0] / 2, dims[1] / 2, dims[2] / 2))
        obj.scale = scale_factors
        obj["bg3_collision_bound"] = True
        self.report({'INFO'}, f"Collision bound created with dimensions: {dims}")
        return {'FINISHED'}

### OPERATOR: Add Cube (Custom Option) with Toggle ###
class BG3COLLISION_OT_add_cube(bpy.types.Operator):
    """Switch to the built-in Add Cube tool for custom collision bounds,
    then automatically return to the selection tool after a delay."""
    bl_idname = "bg3collision.add_cube"
    bl_label = "Add Cube (Custom)"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            self.cancel(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name="builtin.primitive_cube_add")
        wm = context.window_manager
        self._timer = wm.event_timer_add(2.0, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
            self._timer = None

### OPERATOR: Create Collision Bound from Selected Vertices ###
class BG3COLLISION_OT_create_bound_from_selection(bpy.types.Operator):
    """Generate a collision bound (box) from selected vertices (in Edit Mode)"""
    bl_idname = "bg3collision.create_bound_from_selection"
    bl_label = "Create Bound from Selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh.")
            return {'CANCELLED'}
        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "Must be in Edit Mode with vertices selected.")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        selected_verts = [v.co.copy() for v in bm.verts if v.select]
        if len(selected_verts) < 3:
            self.report({'ERROR'}, "Please select at least 3 vertices.")
            return {'CANCELLED'}

        world_center, R, extents = compute_obb(selected_verts)
        # Raise the computed center by 1.44 m on Z
        world_center.z += 1.44

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_cube_add(size=2, location=world_center)
        bound_obj = context.active_object
        bound_obj.name = "CollisionBound_FromSelection"
        bound_obj.scale = Vector(extents) / 2

        R4 = R.to_4x4()
        T = Matrix.Translation(world_center)
        S = Matrix.Diagonal(Vector(extents) / 2).to_4x4()
        bound_obj.matrix_world = T @ R4 @ S

        bound_obj["bg3_collision_bound"] = True
        self.report({'INFO'}, "Collision bound created from selection.")
        return {'FINISHED'}

### OPERATOR: Tile Collision Bound ###
class BG3COLLISION_OT_tile_bound(bpy.types.Operator):
    """Duplicate selected collision bounds in a grid (2x2 with spacing 2)"""
    bl_idname = "bg3collision.tile_bound"
    bl_label = "Tile Collision Bound"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        rows = scene.tile_rows
        cols = scene.tile_columns
        spacing = scene.tile_spacing

        selected = [obj for obj in context.selected_objects if obj.get("bg3_collision_bound", False)]
        if not selected:
            self.report({'ERROR'}, "No collision bound objects selected.")
            return {'CANCELLED'}

        new_objs = []
        for obj in selected:
            base_loc = obj.location.copy()
            for i in range(rows):
                for j in range(cols):
                    if i == 0 and j == 0:
                        continue
                    offset = Vector((j * spacing, i * spacing, 0))
                    dup = obj.copy()
                    dup.data = obj.data.copy()
                    dup.location = base_loc + offset
                    context.collection.objects.link(dup)
                    dup["bg3_collision_bound"] = True
                    new_objs.append(dup)
        self.report({'INFO'}, f"Tiled {len(new_objs)} collision bound duplicates.")
        return {'FINISHED'}

### OPERATOR: Mirror Collision Bound ###
class BG3COLLISION_OT_mirror_bound(bpy.types.Operator):
    """Duplicate selected collision bounds mirrored along the Y axis with an offset of 2"""
    bl_idname = "bg3collision.mirror_bound"
    bl_label = "Mirror Collision Bound"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        offset_val = context.scene.mirror_offset
        selected = [obj for obj in context.selected_objects if obj.get("bg3_collision_bound", False)]
        if not selected:
            self.report({'ERROR'}, "No collision bound objects selected.")
            return {'CANCELLED'}

        new_objs = []
        for obj in selected:
            dup = obj.copy()
            dup.data = obj.data.copy()
            dup.scale.y *= -1
            dup.location.y = -obj.location.y + offset_val
            context.collection.objects.link(dup)
            dup["bg3_collision_bound"] = True
            new_objs.append(dup)
        self.report({'INFO'}, f"Created {len(new_objs)} mirrored collision bound duplicates.")
        return {'FINISHED'}

### OPERATOR: Rename Collision Bounds Sequentially with Prefix Prompt ###
class BG3COLLISION_OT_rename_bounds(bpy.types.Operator):
    """Rename all collision bound objects sequentially (_Phys#) based on their Y coordinate, with a user-provided prefix."""
    bl_idname = "bg3collision.rename_bounds"
    bl_label = "Rename Collision Bounds"
    bl_options = {'REGISTER', 'UNDO'}

    prefix: bpy.props.StringProperty(
        name="Prefix",
        description="Prefix for renaming collision bounds (the sequential number _Phys# will be appended)",
        default="CollisionBound"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        collision_objs = [obj for obj in bpy.data.objects if obj.get("bg3_collision_bound", False)]
        if not collision_objs:
            self.report({'WARNING'}, "No collision bound objects found.")
            return {'CANCELLED'}
        collision_objs.sort(key=lambda o: o.location.y)
        for idx, obj in enumerate(collision_objs, start=1):
            new_name = f"{self.prefix}_Phys{idx}"
            obj.name = new_name
            if obj.type == 'MESH' and obj.data:
                obj.data.name = new_name + "_Mesh"
        self.report({'INFO'}, f"Renamed {len(collision_objs)} collision bound objects sequentially.")
        return {'FINISHED'}

### UI PANEL ###
class BG3COLLISION_PT_panel(bpy.types.Panel):
    bl_label = "BG3 Collision Bound Creator"
    bl_idname = "BG3COLLISION_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BG3 Bound"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Preset Selection:")
        layout.prop(scene, "bg3_collision_preset", text="")

        row = layout.row(align=True)
        row.operator("bg3collision.create_bound", text="Create Collision Bound", icon="CUBE")
        row.operator("bg3collision.add_cube", text="Add Cube", icon="MESH_CUBE")

        layout.separator()
        layout.label(text="From Vertex Selection:")
        layout.operator("bg3collision.create_bound_from_selection", text="Create Bound from Selection", icon="MESH_CUBE")

        layout.separator()
        layout.label(text="Duplication Tools:")
        row = layout.row(align=True)
        row.operator("bg3collision.tile_bound", text="Tile Bound", icon="GRID")
        row.operator("bg3collision.mirror_bound", text="Mirror Bound", icon="MOD_MIRROR")

        layout.separator()
        layout.operator("bg3collision.rename_bounds", text="Rename Collision Bounds", icon="SORTSIZE")

### OPTIONAL: Add to Object Menu ###
def menu_func(self, context):
    self.layout.operator(BG3COLLISION_OT_create_bound.bl_idname, text="Create BG3 Collision Bound")

### REGISTRATION ###
classes = [
    BG3COLLISION_OT_create_bound,
    BG3COLLISION_OT_add_cube,
    BG3COLLISION_OT_tile_bound,
    BG3COLLISION_OT_mirror_bound,
    BG3COLLISION_OT_rename_bounds,
    BG3COLLISION_OT_create_bound_from_selection,
    BG3COLLISION_PT_panel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    for prop in ["bg3_collision_preset", "tile_rows", "tile_columns", "tile_spacing", "mirror_offset"]:
        if prop in bpy.types.Scene.__annotations__:
            del bpy.types.Scene.__annotations__[prop]
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
