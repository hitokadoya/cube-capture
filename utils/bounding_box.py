"""Bounding box utilities for fitting cameras around Blender collections."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional

import bpy
from bpy.types import Depsgraph, ViewLayer
from mathutils import Vector


@dataclass(frozen=True)
class Bounds:
    """Axis-aligned bounding box in world space."""

    minimum: Vector
    maximum: Vector

    @property
    def size(self) -> Vector:
        return self.maximum - self.minimum

    @property
    def center(self) -> Vector:
        return (self.minimum + self.maximum) * 0.5


def _iter_world_corners(obj: bpy.types.Object) -> Iterable[Vector]:
    matrix = obj.matrix_world
    for corner in obj.bound_box:
        yield matrix @ Vector(corner)


def compute_collection_bounds(
    collection: bpy.types.Collection,
    depsgraph: Depsgraph | None = None,
    view_layer: ViewLayer | None = None,
) -> Optional[Bounds]:
    """Compute tight world-space bounds for visible, renderable objects in a collection."""

    minimum = Vector((math.inf, math.inf, math.inf))
    maximum = Vector((-math.inf, -math.inf, -math.inf))
    found_geometry = False

    for obj in collection.all_objects:  # type: ignore[attr-defined]
        if obj.hide_render:
            continue
        if view_layer is not None and not obj.visible_get(view_layer=view_layer):
            continue

        source_obj = obj.evaluated_get(depsgraph) if depsgraph is not None else obj
        if source_obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT", "VOLUME", "GPENCIL"}:
            for world_corner in _iter_world_corners(source_obj):
                minimum.x = min(minimum.x, world_corner.x)
                minimum.y = min(minimum.y, world_corner.y)
                minimum.z = min(minimum.z, world_corner.z)

                maximum.x = max(maximum.x, world_corner.x)
                maximum.y = max(maximum.y, world_corner.y)
                maximum.z = max(maximum.z, world_corner.z)

                found_geometry = True

    if not found_geometry:
        return None

    return Bounds(minimum=minimum, maximum=maximum)
