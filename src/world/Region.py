"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Region: procedurally generates a single
screen's worth of overworld tiles (base grass, fence border with optional
gates, and a decoration layer of flowers/tall-grass/NPCs). There is no
Tiled/TMX map here -- everything is generated directly in code, exactly
like the original.
"""

import random
from typing import Any, Dict, Optional

import pygame

from gale.state import StateMachine

import settings
from src.definitions.entity import ENTITY_DEFS, ENTITY_HEIGHT, ENTITY_WIDTH
from src.entity.NPC import NPC
from src.states.entity.NPCIdleState import NPCIdleState
from src.world.Tile import Tile
from src.world.TileMap import TileMap

TILE_IDS = settings.TILE_IDS


class Region:
    def __init__(self, definition: Optional[Dict[str, Any]] = None) -> None:
        definition = definition or {}

        self.tile_width: int = definition.get("tile_width", settings.TILE_WIDTH)
        self.tile_height: int = definition.get("tile_height", settings.TILE_HEIGHT)

        self.is_town: bool = definition.get("is_town", False)
        self.num_npcs: int = random.randint(2, 4) if self.is_town else 0
        self.npcs = []

        self.base_layer = TileMap(self.tile_width, self.tile_height)
        self.fence_layer = TileMap(self.tile_width, self.tile_height)
        self.grass_layer = TileMap(self.tile_width, self.tile_height)

        self.gates = {
            "north": definition.get("north_gate", False),
            "south": definition.get("south_gate", False),
            "east": definition.get("east_gate", False),
            "west": definition.get("west_gate", False),
        }

        self._create_maps()

    def _create_maps(self) -> None:
        width, height = self.tile_width, self.tile_height

        # Step A: base layer (ground) -- every cell a random grass variant.
        for y in range(1, height + 1):
            row = []
            for x in range(1, width + 1):
                tile_id = random.choice(TILE_IDS["grass"])
                row.append(Tile(x, y, tile_id))
            self.base_layer.tiles.append(row)

        # Step B: fence layer (border wall).
        for y in range(1, height + 1):
            row = []
            for x in range(1, width + 1):
                if y == 1:
                    if x == 1:
                        tile_id = TILE_IDS["top-left-fence"]
                    elif x == width:
                        tile_id = TILE_IDS["top-right-fence"]
                    else:
                        tile_id = TILE_IDS["top-fence"]
                elif y == height:
                    if x == 1:
                        tile_id = TILE_IDS["bottom-left-fence"]
                    elif x == width:
                        tile_id = TILE_IDS["bottom-right-fence"]
                    else:
                        tile_id = TILE_IDS["bottom-fence"]
                elif x == 1:
                    tile_id = TILE_IDS["left-fence"]
                elif x == width:
                    tile_id = TILE_IDS["right-fence"]
                else:
                    tile_id = TILE_IDS["empty"]

                row.append(Tile(x, y, tile_id))
            self.fence_layer.tiles.append(row)

        # Step C: gate carving (up to 4 gates, 2-tile-wide openings flanked
        # by "border" fence-cap tiles). `_tile_at` takes 1-based tile
        # (x, y) grid coordinates, same convention as every Tile's own
        # .x/.y, and returns the Tile so its .id can be overwritten.
        def _tile_at(tx: int, ty: int) -> Tile:
            return self.fence_layer.tiles[ty - 1][tx - 1]

        if self.gates["north"]:
            x = width // 2
            _tile_at(x - 1, 1).id = TILE_IDS["border-left-fence"]
            _tile_at(x, 1).id = TILE_IDS["empty"]
            _tile_at(x + 1, 1).id = TILE_IDS["empty"]
            _tile_at(x + 2, 1).id = TILE_IDS["border-right-fence"]

        if self.gates["south"]:
            x = width // 2
            _tile_at(x - 1, height).id = TILE_IDS["border-left-fence"]
            _tile_at(x, height).id = TILE_IDS["empty"]
            _tile_at(x + 1, height).id = TILE_IDS["empty"]
            _tile_at(x + 2, height).id = TILE_IDS["border-right-fence"]

        if self.gates["west"]:
            y = height // 2
            _tile_at(1, y - 1).id = TILE_IDS["border-bottom-left-fence"]
            _tile_at(1, y).id = TILE_IDS["empty"]
            _tile_at(1, y + 1).id = TILE_IDS["empty"]
            _tile_at(1, y + 2).id = TILE_IDS["border-top-left-fence"]

        if self.gates["east"]:
            y = height // 2
            _tile_at(width, y - 1).id = TILE_IDS["border-bottom-right-fence"]
            _tile_at(width, y).id = TILE_IDS["empty"]
            _tile_at(width, y + 1).id = TILE_IDS["empty"]
            _tile_at(width, y + 2).id = TILE_IDS["border-top-right-fence"]

        # Step D: grass/flowers/NPC decoration layer.
        for y in range(1, height + 1):
            row = []
            for x in range(1, width + 1):
                if y == 1 or y == height or x == 1 or x == width:
                    tile_id = TILE_IDS["empty"]
                elif self.is_town:
                    if random.random() < 0.2:
                        tile_id = random.choice(TILE_IDS["flowers"])
                    else:
                        tile_id = TILE_IDS["empty"]
                        if (
                            len(self.npcs) < self.num_npcs
                            and random.random() < 0.05
                            and y != height // 2
                        ):
                            self._create_npc(x, y)
                else:
                    if random.random() < 0.3:
                        tile_id = TILE_IDS["tall-grass"]
                    else:
                        tile_id = TILE_IDS["empty"]

                row.append(Tile(x, y, tile_id))
            self.grass_layer.tiles.append(row)

    def _create_npc(self, x: int, y: int) -> None:
        width, height = self.tile_width, self.tile_height

        if x <= width / 2 and y <= height / 2:
            direction = "down" if random.random() < 0.6 else "right"
        elif x <= width / 2:
            direction = "up" if random.random() < 0.4 else "right"
        elif y <= height / 2:
            direction = "down" if random.random() < 0.6 else "left"
        else:
            direction = "up" if random.random() < 0.4 else "left"

        gender = "male" if random.random() < 0.5 else "female"

        names = ENTITY_DEFS["npcs"][gender]["names"]
        name = names.pop(random.randrange(len(names)))

        npc = NPC(
            {
                "name": name,
                "map_x": x,
                "map_y": y,
                "width": ENTITY_WIDTH,
                "height": ENTITY_HEIGHT,
                "direction": direction,
                "animations": ENTITY_DEFS["animations"],
                "texture": ENTITY_DEFS["npcs"][gender]["texture"],
            }
        )

        npc.state_machine = StateMachine({"idle": lambda sm: NPCIdleState(npc, sm)})
        npc.state_machine.change("idle")

        self.npcs.append(npc)

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        self.base_layer.render(surface)
        self.fence_layer.render(surface)
        self.grass_layer.render(surface)

        for npc in self.npcs:
            npc.render(surface)
