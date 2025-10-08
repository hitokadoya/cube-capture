"""Render operators for Cube Capture."""

from __future__ import annotations

import bpy

from ..properties import CubeCaptureSettings, PROPERTY_NAME
from ..utils.bounding_box import compute_collection_bounds
from ..utils.render_setup import (
    apply_render_resolution,
    backup_scene_settings,
    configure_camera_for_view,
    create_temporary_camera,
    ensure_flat_lighting,
    prepare_output_path,
    restore_scene_settings,
)

VIEW_ORDER = ("FRONT", "BACK", "RIGHT", "LEFT", "TOP", "BOTTOM")
EXTENSION_MAP = {
    "PNG": ".png",
    "OPEN_EXR": ".exr",
}


class CUBECAPTURE_OT_render(bpy.types.Operator):
    """Render orthographic views for the active collection."""

    bl_idname = "cube_capture.render"
    bl_label = "Cube Capture Views"
    bl_description = "Captures six orthographic views of the Blender scene."
    bl_options = {"REGISTER", "UNDO"}

    @staticmethod
    def _show_save_alert(context: bpy.types.Context, filepath: str) -> None:
        """Display a popup informing the user where the render was saved."""

        window_manager = context.window_manager if context else None
        if window_manager is None:
            return

        def draw(self, _context):  # type: ignore[override]
            self.layout.label(text=filepath)

        window_manager.popup_menu(draw, title="Render Saved", icon="FILE_TICK")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        scene = context.scene
        return bool(scene and getattr(scene, PROPERTY_NAME, None))

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        settings: CubeCaptureSettings = getattr(scene, PROPERTY_NAME)

        layer_collection = context.view_layer.active_layer_collection if context.view_layer else None
        target_collection = None
        if layer_collection:
            target_collection = layer_collection.collection
        elif context.collection:
            target_collection = context.collection

        if target_collection is None:
            self.report({"ERROR"}, "No active collection found.")
            return {"CANCELLED"}

        depsgraph = context.evaluated_depsgraph_get() if hasattr(context, "evaluated_depsgraph_get") else None
        bounds = compute_collection_bounds(target_collection, depsgraph=depsgraph, view_layer=context.view_layer)
        if bounds is None:
            self.report({"ERROR"}, "Active collection does not contain renderable geometry.")
            return {"CANCELLED"}

        view_key = settings.view_direction
        if view_key not in VIEW_ORDER:
            self.report({"ERROR"}, "Selected view is not supported.")
            return {"CANCELLED"}

        backup = backup_scene_settings(scene)
        camera = create_temporary_camera(scene)
        camera_data = camera.data
        padding = max(settings.padding_ratio, 0.0)

        output_filepath = ""

        try:
            if not settings.use_scene_lighting:
                ensure_flat_lighting(scene)
            apply_render_resolution(scene, settings.resolution_x, settings.resolution_y)
            scene.render.image_settings.file_format = settings.image_format
            scene.render.image_settings.color_mode = "RGBA"
            scene.render.image_settings.color_depth = "16" if settings.image_format == "OPEN_EXR" else "8"
            scene.camera = camera

            configure_camera_for_view(camera, bounds, view_key, padding)
            context.view_layer.update()

            filename = f"{settings.base_filename}_{view_key.lower()}"
            target_path = prepare_output_path(settings.output_directory, filename)
            extension = EXTENSION_MAP.get(settings.image_format, "")
            output_filepath = bpy.path.ensure_ext(target_path, extension)
            scene.render.filepath = output_filepath

            render_call = bpy.ops.render.render(animation=False, write_still=True, use_viewport=False)
            render_result = render_call if isinstance(render_call, set) else {render_call}
            if "CANCELLED" in render_result:
                self.report({"INFO"}, "Render cancelled.")
                return {"CANCELLED"}
        finally:
            restore_scene_settings(scene, backup)
            if camera.name in bpy.data.objects:
                bpy.data.objects.remove(camera, do_unlink=True)
            if camera_data and camera_data.name in bpy.data.cameras:
                bpy.data.cameras.remove(camera_data, do_unlink=True)

        self.report({"INFO"}, f"Render saved to {output_filepath}.")
        self._show_save_alert(context, output_filepath)
        return {"FINISHED"}
