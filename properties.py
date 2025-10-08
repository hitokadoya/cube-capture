"""Property group definitions for Cube Capture."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup

PROPERTY_NAME = "cube_capture_settings"


VIEW_ITEMS = (
    ("FRONT", "Front", "Render the front orthographic view"),
    ("BACK", "Back", "Render the back orthographic view"),
    ("RIGHT", "Right", "Render the right orthographic view"),
    ("LEFT", "Left", "Render the left orthographic view"),
    ("TOP", "Top", "Render the top orthographic view"),
    ("BOTTOM", "Bottom", "Render the bottom orthographic view"),
)


IMAGE_FORMAT_ITEMS = (
    ("PNG", "PNG", "Lossless 8-bit RGBA PNG"),
    ("OPEN_EXR", "OpenEXR", "High dynamic range OpenEXR"),
)


class CubeCaptureSettings(PropertyGroup):
    output_directory: StringProperty(
        name="Output Folder",
        description="Directory where rendered views are saved",
        subtype="DIR_PATH",
        default="//renders",
    )

    base_filename: StringProperty(
        name="Filename Prefix",
        description="Base name for generated images",
        default="cube_capture",
    )

    resolution_x: IntProperty(
        name="Width",
        description="Render width in pixels",
        default=2048,
        min=64,
        soft_max=8192,
    )

    resolution_y: IntProperty(
        name="Height",
        description="Render height in pixels",
        default=2048,
        min=64,
        soft_max=8192,
    )

    view_direction: EnumProperty(
        name="View",
        description="Choose the orthographic view to render",
        items=VIEW_ITEMS,
        default="FRONT",
    )

    image_format: EnumProperty(
        name="Format",
        description="Image file format for outputs",
        items=IMAGE_FORMAT_ITEMS,
        default="PNG",
    )

    padding_ratio: FloatProperty(
        name="Padding",
        description="Extra framing around the collection as a fraction of the largest dimension",
        min=0.0,
        max=1.0,
        default=0.05,
        subtype="FACTOR",
    )

    use_scene_lighting: BoolProperty(
        name="Use Scene Lighting",
        description="Render with the scene's existing lights and world instead of the add-on's flat setup",
        default=False,
    )


def register_properties() -> None:
    bpy.utils.register_class(CubeCaptureSettings)
    setattr(
        bpy.types.Scene,
        PROPERTY_NAME,
        bpy.props.PointerProperty(
            type=CubeCaptureSettings,
            name="Cube Capture Settings",
        ),
    )


def unregister_properties() -> None:
    delattr(bpy.types.Scene, PROPERTY_NAME)
    bpy.utils.unregister_class(CubeCaptureSettings)
