"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Tile.
"""

import pygame

import settings


class Tile:
    def __init__(self, x: int, y: int, tile_id: int) -> None:
        self.x = x
        self.y = y
        self.id = tile_id

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        surface.blit(
            settings.TEXTURES["tiles"],
            (
                (self.x - 1 + offset_x) * settings.TILE_SIZE,
                (self.y - 1 + offset_y) * settings.TILE_SIZE,
            ),
            settings.frame("tiles", self.id),
        )
