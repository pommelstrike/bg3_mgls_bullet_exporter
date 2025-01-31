# Divinity Physics Exporter for Blender 3.X

This is a simple addon for Blender 3.x+ that allows you to export bullet/bin files for Moonglasses for BG3, without dependency of Blender Game Engine.

## Features:  
* Export Blender Game physics to .bullet, and optionally convert that .bullet to .bin, for use in Moonglasses.
* Automatically rotate the object for BG3's Y-Up world (Blender is Z-Up).
* Use the layer name or active object name when exporting.  
* _**\*New\***_ Export meshes with minimal setup necessary - The exporter will default to Static/Convex Mesh (or whatever you set it to) and automatically join meshes / parent them if enabled. This all happens to copies, so as to not modify your actual objects.

## Installing
Will need LSPakUtilityBulletToPhysX

## Credits
This is a modified version of LaughingLeader-DOS2-Mods/dos2de_bullet_exporter [https://github.com/LaughingLeader-DOS2-Mods/dos2de_bullet_exporter] &  V0idExp's original bullet exporter addon, located here: [https://github.com/V0idExp/blender-bullet-export](https://github.com/V0idExp/blender-bullet-export)
