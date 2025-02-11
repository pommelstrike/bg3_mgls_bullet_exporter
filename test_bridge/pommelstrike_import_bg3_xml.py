bl_info = {
    "name": "pommelstrike BG3 Physics XML Importer",
    "blender": (3, 0, 0),
    "category": "Import-Export",
    "author": "pommelstrike",
    "description": "Imports BG3 physics XML files and generates geometry in Blender.",
    "location": "File > Import > BG3 Physics XML",
    "version": (1, 4, 0),
}

import bpy
import os  # Needed to work with file paths
import xml.etree.ElementTree as ET
from mathutils import Vector, Quaternion
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator, Panel
import math
import bmesh

# Function to parse XML and extract physics shapes
def parse_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
        return []  # Return an empty list so Blender doesn't crash

    # Extract the default name from the XML filename (without extension)
    default_name = os.path.splitext(os.path.basename(file_path))[0]

    shapes = []
    for shape in root.findall(".//Shape"):
        try:
            # Retrieve the name; if missing or empty, use the filename
            name_elem = shape.find("Name")
            name = name_elem.text if (name_elem is not None and name_elem.text is not None) else default_name

            # Parse the local pose position and rotation
            pos_elem = shape.find("LocalPose/Position")
            rot_elem = shape.find("LocalPose/Rotation")
            if pos_elem is None or rot_elem is None:
                raise AttributeError("Missing LocalPose position or rotation")
            position = Vector((
                float(pos_elem.find("X").text),
                float(pos_elem.find("Y").text),
                float(pos_elem.find("Z").text),
            ))
            rotation = Quaternion((
                float(rot_elem.find("W").text),  # Note: Blender uses (w, x, y, z)
                float(rot_elem.find("X").text),
                float(rot_elem.find("Y").text),
                float(rot_elem.find("Z").text),
            ))

            # Get the Geometry element
            geom = shape.find("Geometry")
            if geom is None:
                raise AttributeError("Missing Geometry element")
            geom_type_elem = geom.find("Type")
            if geom_type_elem is None:
                raise AttributeError("Missing Geometry Type element")
            geom_type = geom_type_elem.text.strip()

            # Build a common shape data dictionary
            shape_data = {
                "name": name,
                "position": position,
                "rotation": rotation,
                "geometry_type": geom_type,
            }

            if geom_type == "ConvexMesh":
                # Process ConvexMesh geometry
                convex = geom.find("ConvexMesh")
                if convex is None:
                    raise AttributeError("Missing ConvexMesh element")
                vertices = []
                for polygon in convex.findall("Polygon"):
                    for vertex in polygon.findall("Vertex"):
                        x = float(vertex.find("X").text)
                        y = float(vertex.find("Y").text)
                        z = float(vertex.find("Z").text)
                        vertices.append(Vector((x, y, z)))
                # Check for optional local scale/rotation under Geometry/Scale
                scale_elem = geom.find("Scale/Scale")
                rot_scale_elem = geom.find("Scale/Rotation")
                if scale_elem is not None:
                    scale_vec = Vector((
                        float(scale_elem.find("X").text),
                        float(scale_elem.find("Y").text),
                        float(scale_elem.find("Z").text)
                    ))
                else:
                    scale_vec = Vector((1, 1, 1))
                if rot_scale_elem is not None:
                    scale_rot = Quaternion((
                        float(rot_scale_elem.find("W").text),
                        float(rot_scale_elem.find("X").text),
                        float(rot_scale_elem.find("Y").text),
                        float(rot_scale_elem.find("Z").text)
                    ))
                else:
                    scale_rot = Quaternion((1, 0, 0, 0))  # Identity quaternion
                transformed_vertices = [scale_rot @ (v * scale_vec) for v in vertices]
                shape_data["vertices"] = transformed_vertices

            elif geom_type == "Capsule":
                # Process Capsule geometry
                radius_elem = geom.find("Radius")
                half_height_elem = geom.find("HalfHeight")
                if radius_elem is None or half_height_elem is None:
                    raise AttributeError("Missing Radius or HalfHeight element for Capsule geometry")
                radius = float(radius_elem.text)
                half_height = float(half_height_elem.text)
                shape_data["radius"] = radius
                shape_data["half_height"] = half_height

            else:
                # Assume a "box" geometry that uses HalfExtents
                extents = geom.find("HalfExtents")
                if extents is None:
                    raise AttributeError("Missing HalfExtents element for Box geometry")
                half_extents = Vector((
                    float(extents.find("X").text),
                    float(extents.find("Y").text),
                    float(extents.find("Z").text),
                ))
                shape_data["half_extents"] = half_extents

            shapes.append(shape_data)
        except AttributeError as e:
            print(f"Skipping malformed shape in XML '{name}': {e}")

    return shapes

# Function to create a box in Blender (using HalfExtents)
def create_box(name, position, rotation, half_extents, parent_empty):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = half_extents
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = rotation
    obj.parent = parent_empty
    return obj

# Function to create a convex mesh in Blender (using vertices from ConvexMesh)
def create_convex_mesh(name, position, rotation, vertices, parent_empty):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for v in vertices:
        bm.verts.new(v)
    bm.verts.ensure_lookup_table()
    try:
        bmesh.ops.convex_hull(bm, input=bm.verts)
    except Exception as e:
        print(f"Error creating convex hull for '{name}': {e}")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = rotation
    obj.parent = parent_empty
    return obj

# Function to create a capsule in Blender (using Capsule geometry)
def create_capsule(name, position, rotation, radius, half_height, parent_empty):
    # Try using Blender's built-in capsule operator if available.
    try:
        bpy.ops.mesh.primitive_capsule_add(
            radius=radius,
            depth=2 * half_height,
            location=position
        )
        obj = bpy.context.object
    except Exception as e:
        print(f"Capsule operator not available for '{name}', using fallback: {e}")
        # Fallback: create a UV sphere and scale it in Z to approximate a capsule shape.
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16,
            ring_count=16,
            radius=radius,
            location=position
        )
        obj = bpy.context.object
        # Scale in Z so the sphere becomes elongated (note: this is an approximation)
        obj.scale[2] = half_height / radius
    obj.name = name
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = rotation
    obj.parent = parent_empty
    return obj

# Clear existing objects in the scene
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

# Main function to import physics data into Blender
def import_physics_shapes(xml_file):
    clear_scene()

    # Create an empty at world origin to act as the parent
    parent_empty = bpy.data.objects.new("BG3_Physics_Origin", None)
    bpy.context.collection.objects.link(parent_empty)
    parent_empty.location = (0, 0, 0)

    shapes = parse_xml(xml_file)

    for shape in shapes:
        geom_type = shape.get("geometry_type")
        if geom_type == "ConvexMesh":
            create_convex_mesh(
                shape["name"],
                shape["position"],
                shape["rotation"],
                shape["vertices"],
                parent_empty
            )
        elif geom_type == "Capsule":
            create_capsule(
                shape["name"],
                shape["position"],
                shape["rotation"],
                shape["radius"],
                shape["half_height"],
                parent_empty
            )
        else:
            create_box(
                shape["name"],
                shape["position"],
                shape["rotation"],
                shape["half_extents"],
                parent_empty
            )

    # Rotate the parent empty to convert Y-Up to Z-Up (90° rotation around X)
    parent_empty.rotation_euler[0] = math.radians(90)

# Operator for file import
class IMPORT_OT_bg3_physics(Operator, ImportHelper):
    bl_idname = "import.bg3_physics"
    bl_label = "Import BG3 Physics XML"
    bl_description = "Import BG3 physics XML file and create geometry"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".xml"
    filter_glob: StringProperty(default="*.xml", options={'HIDDEN'})

    def execute(self, context):
        import_physics_shapes(self.filepath)
        self.report({'INFO'}, "BG3 Physics XML Imported Successfully")
        return {'FINISHED'}

# Panel in the 3D Viewport N-Panel
class VIEW3D_PT_bg3_physics_import(Panel):
    bl_label = "BG3 Physics Importer"
    bl_category = "BG3 Physics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        layout.operator("import.bg3_physics", text="Import BG3 Physics XML")

# Register the addon
def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_bg3_physics.bl_idname, text="BG3 Physics XML (.xml)")

def register():
    bpy.utils.register_class(IMPORT_OT_bg3_physics)
    bpy.utils.register_class(VIEW3D_PT_bg3_physics_import)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(IMPORT_OT_bg3_physics)
    bpy.utils.unregister_class(VIEW3D_PT_bg3_physics_import)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
