"""UI panels for the Cube Capture add-on."""

from __future__ import annotations

import bpy

from ..properties import CubeCaptureSettings, PROPERTY_NAME


class CUBECAPTURE_PT_panel(bpy.types.Panel):
    bl_idname = "CUBECAPTURE_PT_main"
    bl_label = "Cube Capture"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Render"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene and getattr(context.scene, PROPERTY_NAME, None))

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        settings: CubeCaptureSettings = getattr(scene, PROPERTY_NAME)

        layer_collection = context.view_layer.active_layer_collection if context.view_layer else None
        collection_name = layer_collection.collection.name if layer_collection else "<None>"

        col = layout.column()
        col.label(text=f"Active Collection: {collection_name}")
        col.prop(settings, "view_direction")
        col.prop(settings, "resolution_x")
        col.prop(settings, "resolution_y")
        col.prop(settings, "padding_ratio")
        col.prop(settings, "use_scene_lighting")

        col.separator()
        col.prop(settings, "output_directory")
        col.prop(settings, "base_filename")
        col.prop(settings, "image_format")

        col.separator()
        col.operator("cube_capture.render", icon="RENDER_STILL")
