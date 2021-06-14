from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

    from scripts.core.game import Game


__all__ = ["UI"]

#### To Do List######
# TODO - add an overlay method to draw standardised info such as gold
# TODO - add option selection and looping selection to update
# TODO - amend selection approach to work on a grid, so we can move across columns and rows.


class UI(ABC):
    """
    Represent the UI of a scene
    """

    def __init__(self, game: Game):
        self.game: Game = game

    def update(self):
        pass

    def render(self, surface: pygame.surface):
        pass