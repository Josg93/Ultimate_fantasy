"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class TileMap: a single width x height grid of
Tiles (tiles[y][x], row-major, both axes 1-based to match the entities'
own map_x/map_y). A Region composes three of these (base/fence/grass) to
simulate layering.
"""

from typing import List, Optional, Tuple

import pygame

from src.world.Tile import Tile


class TileMap:
    def __init__(
        self, width: int, height: int, offset: Optional[Tuple[int, int]] = None
    ) -> None:
        self.tiles: List[List[Tile]] = []
        self.width = width
        self.height = height
        self.offset_x, self.offset_y = offset if offset is not None else (0, 0)

    def render(self, surface: pygame.Surface) -> None:
        for y in range(1, self.height + 1):
            for x in range(1, self.width + 1):
                self.tiles[y - 1][x - 1].render(surface, self.offset_x, self.offset_y)
