"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class TransparentMenu: a panel and list view
where non-healing action items are rendered with transparency (alpha),
while healing actions are rendered fully opaque.
"""

from typing import List, Optional, Sequence, Tuple, Callable
import pygame
from gale.ui.cursor import Cursor
from gale.ui.theme import Theme
import settings
from src.gui.Panel import Panel

Item = Tuple[str, Callable[[], None]]

_MENU_THEME = Theme(
    background_color=pygame.Color(56, 56, 56),
    hover_color=pygame.Color(56, 56, 56),
    focus_color=pygame.Color(56, 56, 56),
    text_color=pygame.Color(255, 255, 255),
    border_width=0,
)


class TransparentMenu:
    """
    Menu implementation that applies transparency (alpha) to action items
    unless they are healing actions.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        items: Sequence[Item],
        show_cursor: bool = True,
        font: Optional[pygame.font.Font] = None,
    ) -> None:
        self.panel = Panel(x, y, width, height)
        self.items = list(items)
        self.selected_index = 0
        self.font = font or settings.FONTS["medium"]
        self.cursor = Cursor(settings.TEXTURES["cursor-right"]) if show_cursor else None
        self.width = width
        self.height = height
        self.x = x
        self.y = y

    def row_height(self) -> float:
        return self.height / len(self.items) if self.items else self.height

    def row_rect(self, index: int) -> pygame.Rect:
        row_height = self.row_height()
        return pygame.Rect(
            int(self.x + 4),
            int(self.y + 3 + index * row_height),
            int(self.width - 8),
            int(row_height),
        )

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        self.panel.render(surface)

        if not self.items:
            return

        for index, (label, _) in enumerate(self.items):
            row_rect = self.row_rect(index)

            # Highlight selected row background
            if index == self.selected_index:
                pygame.draw.rect(surface, _MENU_THEME.focus_color, row_rect)

            # Determine if this action is a healing action
            # Healing actions (e.g. Heal, Global Heal) are rendered without transparency (alpha = 255)
            # Other actions are rendered with partial transparency (alpha = 150)
            is_healing = "heal" in label.lower() or "curar" in label.lower()
            alpha = 255 if is_healing else 150

            # Render text surface and apply alpha transparency
            text_surf = self.font.render(label, True, _MENU_THEME.text_color)
            if alpha < 255:
                text_surf = text_surf.copy()
                text_surf.set_alpha(alpha)

            # Blit centered in row rect
            text_rect = text_surf.get_rect(
                centerx=row_rect.centerx, centery=row_rect.centery
            )
            surface.blit(text_surf, text_rect)

            # Render cursor on selected row
            if index == self.selected_index and self.cursor is not None:
                cursor_x = max(self.panel.width / 3, self.panel.x - 8)
                self.cursor.render(surface, (cursor_x, row_rect.centery))

    def navigate(self, direction: Tuple[int, int]) -> None:
        _, dy = direction
        if dy != 0 and self.items:
            self.selected_index = (self.selected_index + dy) % len(self.items)
            settings.SOUNDS["blip"].stop()
            settings.SOUNDS["blip"].play()

    def confirm(self) -> None:
        if self.items:
            settings.SOUNDS["blip"].stop()
            settings.SOUNDS["blip"].play()
            _, on_select = self.items[self.selected_index]
            on_select()
