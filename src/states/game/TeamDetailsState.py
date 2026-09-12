"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class TeamDetailsState: displays a status screen
with individual panels for each party member showing their level, experience,
HP, and magic stats.
"""

from typing import Any
import pygame
from gale.state import BaseState
import settings
from src.gui.Panel import Panel


class TeamDetailsState(BaseState):
    """
    Displays team member status in separate panels when invoked from the pause menu.
    """

    def enter(self, play_state: Any) -> None:
        self.play_state = play_state
        self.party = play_state.world.party

        # Create a main container panel covering most of the screen
        self.panel = Panel(
            16,
            16,
            settings.VIRTUAL_WIDTH - 32,
            settings.VIRTUAL_HEIGHT - 32,
        )

    def close(self) -> None:
        """Closes the team details state and returns to the previous state."""
        self.state_machine.pop()

    def update(self, dt: float) -> None:
        pass

    def on_input(self, input_id: str, input_data: Any) -> None:
        """Closes the menu on enter or cancel input."""
        if not input_data.pressed:
            return

        if input_id in ("enter", "escape", "cancel", "space"):
            self.close()

    def render(self, surface: pygame.Surface) -> None:
        """Renders the main panel and individual stat boxes for each party member."""
        self.panel.render(surface)

        font_medium = settings.FONTS["medium"]
        font_small = settings.FONTS["small"]

        # Title
        title_surf = font_medium.render("Estado del Equipo", True, (255, 255, 255))
        surface.blit(
            title_surf,
            (settings.VIRTUAL_WIDTH / 2 - title_surf.get_width() / 2, 24),
        )

        # Render individual boxes for each character in the party
        characters = list(self.party.characters.values())
        box_width = settings.VIRTUAL_WIDTH - 64
        box_height = 36
        start_y = 56

        for i, char in enumerate(characters):
            bx = 32
            by = start_y + i * (box_height + 8)

            # Draw individual panel for character
            char_panel = Panel(bx, by, box_width, box_height)
            char_panel.render(surface)

            # Character stats text
            status_text = (
                f"{char.name} (Nv. {char.level}) | "
                f"HP: {int(char.current_hp)}/{int(char.hp)} | "
                f"MP/Mag: {int(char.magic)} | "
                f"EXP: {int(char.current_exp)}/{int(char.exp_to_level)}"
            )

            color = (180, 50, 50) if char.dead else (255, 255, 255)
            text_surf = font_small.render(status_text, True, color)
            surface.blit(
                text_surf,
                (bx + 12, by + box_height / 2 - text_surf.get_height() / 2),
            )
