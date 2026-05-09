# pommelstrike BG3 Physics

> **All-in-one Blender addon for Baldur's Gate 3 physics authoring.**  
> Import, edit, and export collision (`BLD_*.xml`) and spring chain (`HAIR_*_Spring.xml`) physics data, then cook to binary `.bin` via `pomphysicstool.exe`.

---

## Documentation

Full user guide is available in the [GitHub Wiki](../../wiki).

---
## Features

- **Collision Physics** — Create and edit collision bodies (Box, Capsule, Sphere, ConvexMesh, TriangleMesh) for level geometry and props
- **Spring Chain Physics** — Build and edit hair/cloth physics chains with D6 joints and spring drives
- **One-Click Collider Generation** — Generate collision shapes from mesh selections with auto-fit bounding boxes
- **Chain from Bones** — Auto-generate spring chains from selected armature bones
- **Import & Export** — Full round-trip support for `BLD_*.xml` and `HAIR_*_Spring*.xml` files
- **Cook to .bin** — Integrated `pomphysicstool.exe` pipeline for XML → binary conversion
- ( `pomphysicstool.exe` requires NVIDIA.PhysX libraries dll)
one of these for example: the Tools folder of Lslib / Moonglasses / Vanilla toolkit folder 
```
...\ExportTool-v1.20.x\Packed\Tools

PhysXCommon_64.dll
PhysXCooking_64.dll
PhysXFoundation_64.dll
PhysX_64.dll
```
- 
- **Viewport Armature Linking** — Spring chain segments follow your rig in the viewport via Child Of constraints

---

## Requirements

- **Blender 4.1+**
- **Windows 10/11**
- **pomphysicstool.exe** *(required — for `.bin` cooking)*

---

## Installation

1. Download the addon zip (https://github.com/pommelstrike/bg3_physx_xml_io/releases/tag/v2.2.0)
2. Open Blender → **Edit → Preferences → Add-ons → Install…**
3. Select the zip file and enable **Import-Export: pommelstrike BG3 Physics**
4. Expand the addon preferences and set the path to `pomphysicstool.exe`
5. You must install CoACD and restart Blender prior to using new CoACD features
 (Edit ▸ Preferences ▸ Add-ons ▸ pommelstrike BG3 Physics ▸ Install CoACD).

---

## Quick Start

### Collision Physics

1. Press **N** in the 3D viewport → open the **POM Collision** sidebar tab
2. Select a mesh and click **Generate Collider**
3. Choose shape type (Box, Capsule, Sphere, Convex) and click OK
4. Adjust properties in the sidebar (actor name, dimensions, material, dynamics)
5. Click **Export Collision XML / .bin**

### Spring Chain Physics

1. Press **N** in the 3D viewport → open the **POM Chain** sidebar tab
2. Set the **Spring Armature** picker to your character's armature
3. Import an existing spring XML, or build a chain:
   - **Chain from Selected Bones** — auto-generate from armature
   - **New Chain Root** + **Add Segment** — build manually
4. Configure segment properties (mass, damping, swing limits, drive springs)
5. Select the chain root and click **Export Spring XML / .bin**

---

## Where to Find Things

| Location | What |
|----------|------|
| **Edit → Preferences → Add-ons** | `pomphysicstool.exe` path, debug logging toggle |
| **File → Import** | BG3 Collision XML, BG3 Spring XML |
| **File → Export** | BG3 Collision XML, BG3 Spring XML |
| **3D Viewport Sidebar (N) → POM Collision** | Collider generation, properties, export |
| **3D Viewport Sidebar (N) → POM Chain** | Chain creation, segment/joint editing, export |

---

## File Naming

| Type | Pattern | Example |
|------|---------|---------|
| Collision | `BLD_<name>.xml` → `BLD_<name>.bin` | `BLD_Gondian_Pump_A.xml` |
| Spring | `HAIR_<name>_Spring.xml` → `.bin` | `HAIR_HUM_M_Wavy_Short_E_Spring.xml` |
| Spring Base | `HAIR_<name>_Spring_Base.xml` → `.bin` | `HAIR_HUM_M_Wavy_Short_E_Spring_Base.xml` |

---

## Support

If this tool helps your BG3 modding work, consider supporting development:

- **[Patreon](https://www.patreon.com/pommelstrike)**
- **[Ko-fi](https://ko-fi.com/pommelstrike/)**

---

## License

This project is provided as-is for BG3 modding purposes.
