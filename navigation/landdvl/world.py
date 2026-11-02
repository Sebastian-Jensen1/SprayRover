"""A simple garden: lawn area, trees and a house wall, and how they affect GNSS quality."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tree:
    x: float
    y: float
    canopy_radius: float


@dataclass(frozen=True)
class Garden:
    """Garden in a local ENU frame (metres). The house wall runs along y = 0."""

    width: float = 30.0
    height: float = 20.0
    trees: tuple[Tree, ...] = field(
        default_factory=lambda: (Tree(15.0, 10.0, 4.0), Tree(24.0, 15.0, 3.0))
    )
    wall_multipath_band: float = 4.0  # GNSS is degraded this close to the house wall
    tree_edge_band: float = 2.5  # ...and this close to a tree canopy edge

    def gnss_quality(self, x: float, y: float) -> str:
        """'none' under a canopy, 'float' near a canopy or the wall, otherwise 'fix'."""
        for tree in self.trees:
            d = math.hypot(x - tree.x, y - tree.y)
            if d < tree.canopy_radius:
                return "none"
        for tree in self.trees:
            d = math.hypot(x - tree.x, y - tree.y)
            if d < tree.canopy_radius + self.tree_edge_band:
                return "float"
        if y < self.wall_multipath_band:
            return "float"
        return "fix"
