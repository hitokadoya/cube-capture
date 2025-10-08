"""Helpers for configuring Eevee renders and orthographic cameras."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Tuple

import bpy
from mathutils import Matrix, Vector

from .bounding_box import Bounds

_VIEW_DIRECTIONS: Dict[str, Tuple[Vector, Vector, int, Tuple[int, int]]] = {
    "FRONT": (Vector((0.0, -1.0, 0.0)), Vector((0.0, 0.0, 1.0)), 1, (0, 2)),
    "BACK": (Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0)), 1, (0, 2)),
    "RIGHT": (Vector((-1.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)), 0, (1, 2)),
    "LEFT": (Vector((1.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)), 0, (1, 2)),
    "TOP": (Vector((0.0, 0.0, -1.0)), Vector((0.0, 1.0, 0.0)), 2, (0, 1)),
    "BOTTOM": (Vector((0.0, 0.0, 1.0)), Vector((0.0, 1.0, 0.0)), 2, (0, 1)),
}

_TEMP_WORLD_BASENAME = "CubeCaptureFlatWorld"
_TEMP_WORLD_ASSIGNMENTS: Dict[int, str] = {}


@dataclass(frozen=True)
class RenderSettingsBackup:
    engine: str
    filepath: str
    resolution_x: int
    resolution_y: int
    resolution_percentage: int
    film_transparent: bool
    image_settings: Tuple[str, str, str]
    camera_name: str | None
    use_nodes: bool
    background_color: Tuple[float, float, float]
    background_strength: float
    world_name: str | None


def backup_scene_settings(scene: bpy.types.Scene) -> RenderSettingsBackup:
    world = scene.world
    background_color = (0.0, 0.0, 0.0)
    background_strength = 1.0
    use_nodes = False
    world_name = world.name if world else None
    if world is not None:
        use_nodes = world.use_nodes
        if use_nodes and world.node_tree:
            background = world.node_tree.nodes.get("Background")
            if background:
                background_color = tuple(background.inputs[0].default_value[:3])
                background_strength = background.inputs[1].default_value
    return RenderSettingsBackup(
        engine=scene.render.engine,
        filepath=scene.render.filepath,
        resolution_x=scene.render.resolution_x,
        resolution_y=scene.render.resolution_y,
        resolution_percentage=scene.render.resolution_percentage,
        film_transparent=scene.render.film_transparent,
        image_settings=(
            scene.render.image_settings.file_format,
            scene.render.image_settings.color_mode,
            scene.render.image_settings.color_depth,
        ),
        camera_name=scene.camera.name if scene.camera else None,
        use_nodes=use_nodes,
        background_color=background_color,
        background_strength=background_strength,
        world_name=world_name,
    )


def restore_scene_settings(scene: bpy.types.Scene, backup: RenderSettingsBackup) -> None:
    scene.render.engine = backup.engine
    scene.render.filepath = backup.filepath
    scene.render.resolution_x = backup.resolution_x
    scene.render.resolution_y = backup.resolution_y
    scene.render.resolution_percentage = backup.resolution_percentage
    scene.render.film_transparent = backup.film_transparent
    scene.render.image_settings.file_format = backup.image_settings[0]
    scene.render.image_settings.color_mode = backup.image_settings[1]
    scene.render.image_settings.color_depth = backup.image_settings[2]
    if backup.camera_name and backup.camera_name in bpy.data.objects:
        scene.camera = bpy.data.objects[backup.camera_name]
    original_world = bpy.data.worlds.get(backup.world_name) if backup.world_name else None
    scene.world = original_world
    scene_key = scene.as_pointer()
    temp_world_name = _TEMP_WORLD_ASSIGNMENTS.pop(scene_key, None)
    world = scene.world
    if world and world.use_nodes and world.node_tree:
        background = world.node_tree.nodes.get("Background")
        if background:
            background.inputs[0].default_value = (*backup.background_color, 1.0)
            background.inputs[1].default_value = backup.background_strength
    elif world and not backup.use_nodes:
        world.use_nodes = False
    if temp_world_name:
        temp_world = bpy.data.worlds.get(temp_world_name)
        if temp_world and temp_world.users == 0:
            bpy.data.worlds.remove(temp_world, do_unlink=True)


def _select_eevee_engine() -> str | None:
    """Return the preferred Eevee engine identifier available in this build."""
    engine_prop = bpy.types.RenderSettings.bl_rna.properties.get("engine")
    if engine_prop is None:
        return None
    identifiers = {item.identifier for item in engine_prop.enum_items}
    if "BLENDER_EEVEE_NEXT" in identifiers:
        return "BLENDER_EEVEE_NEXT"
    if "BLENDER_EEVEE" in identifiers:
        return "BLENDER_EEVEE"
    return None


def _get_eevee_settings(scene: bpy.types.Scene):
    """Return Eevee settings struct compatible with current engine, if any."""
    return getattr(scene, "eevee_next", None) or getattr(scene, "eevee", None)


def ensure_flat_lighting(scene: bpy.types.Scene) -> None:
    engine_id = _select_eevee_engine()
    if engine_id is not None:
        scene.render.engine = engine_id
    scene.render.film_transparent = True

    eevee_settings = _get_eevee_settings(scene)
    if eevee_settings is not None:
        eevee_settings.use_gtao = False
        if hasattr(eevee_settings, "use_ssr"):
            eevee_settings.use_ssr = False
        if hasattr(eevee_settings, "use_screen_space_reflections"):
            eevee_settings.use_screen_space_reflections = False
        if hasattr(eevee_settings, "use_soft_shadows"):
            eevee_settings.use_soft_shadows = False

    temp_world = bpy.data.worlds.new(_TEMP_WORLD_BASENAME)
    temp_world.use_nodes = True
    node_tree = temp_world.node_tree
    node_tree.nodes.clear()
    background = node_tree.nodes.new(type="ShaderNodeBackground")
    background.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    background.inputs[1].default_value = 1.0
    output = node_tree.nodes.new(type="ShaderNodeOutputWorld")
    node_tree.links.new(background.outputs[0], output.inputs[0])

    scene.world = temp_world
    _TEMP_WORLD_ASSIGNMENTS[scene.as_pointer()] = temp_world.name


def _orthographic_camera_matrix(location: Vector, direction: Vector, up: Vector) -> Matrix:
    direction = direction.normalized()
    up = up.normalized()
    z_axis = -direction
    x_axis = up.cross(z_axis).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    rotation = Matrix((x_axis, y_axis, z_axis)).transposed()
    return Matrix.Translation(location) @ rotation.to_4x4()


def create_temporary_camera(scene: bpy.types.Scene) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new("CubeCaptureTempCamera")
    camera_data.type = "ORTHO"
    camera_obj = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera_obj)
    return camera_obj


def configure_camera_for_view(
    camera: bpy.types.Object,
    bounds: Bounds,
    view_key: str,
    padding: float,
) -> None:
    direction, up, depth_axis, plane_axes = _VIEW_DIRECTIONS[view_key]
    size = bounds.size
    center = bounds.center
    max_dimension = max(size.x, size.y, size.z, 1.0)
    padding_distance = max_dimension * padding

    axis_size = size[depth_axis]
    distance = axis_size * 0.5 + padding_distance
    if distance < 0.5:
        distance = 0.5 + padding_distance

    plane_width = size[plane_axes[0]]
    plane_height = size[plane_axes[1]]
    ortho_scale = max(plane_width, plane_height, 0.01) * (1.0 + padding * 2.0)

    location = center - direction.normalized() * distance
    camera.matrix_world = _orthographic_camera_matrix(location, direction, up)

    camera_data = camera.data
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = ortho_scale
    camera_data.clip_start = max(distance * 0.1, 0.1)
    camera_data.clip_end = distance + max_dimension * 4.0 + padding_distance


def prepare_output_path(base_directory: str, filename: str) -> str:
    absolute_dir = bpy.path.abspath(base_directory)
    os.makedirs(absolute_dir, exist_ok=True)
    return os.path.join(absolute_dir, filename)


def apply_render_resolution(scene: bpy.types.Scene, width: int, height: int) -> None:
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
