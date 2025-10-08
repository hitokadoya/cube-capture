"""Cube Capture Blender add-on."""

from __future__ import annotations

import importlib
from typing import Sequence

import bpy

from . import operators, properties, ui

bl_info = {
    "name": "Cube Capture",
    "author": "cube-capture Contributors",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Render",
    "description": "Captures six orthographic views of the Blender scene.",
    "category": "Render",
}


_modules: Sequence[object] = (properties, operators.render_views, ui.panel)  # type: ignore[attr-defined]


def _reload_modules() -> None:
    for module in _modules:
        importlib.reload(module)


classes = (
    operators.render_views.CUBECAPTURE_OT_render,
    ui.panel.CUBECAPTURE_PT_panel,
)


def register() -> None:
    if bpy.app.background:  # pragma: no cover - defensive guard when running tests
        pass
    _reload_modules()
    properties.register_properties()
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    properties.unregister_properties()


__all__ = ["register", "unregister", "bl_info"]
