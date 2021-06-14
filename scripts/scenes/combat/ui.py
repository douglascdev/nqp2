from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from scripts.core.base_classes.ui import UI
from scripts.core.constants import CombatState, SceneType
from scripts.core.utility import offset

if TYPE_CHECKING:
    pass

__all__ = ["CombatUI"]

## TO DO LIST ##
# TODO -  Win state/ lose state; when all of one side is dead.
# TODO - show bar that is all of remaining health for both sides as a % of total. So when player is winning the bar
#  will progress to one side and if the opposite then it will progress to the other.
# TODO - dev tool - instant win button
# TODO - dont start combat until all units placed / units up to limit placed
# TODO -


class CombatUI(UI):
    def __init__(self, game):
        super().__init__(game)

        self.selected_card = 0  # card index

        # position relative to terrain
        self.place_target = [0, 0]

    def update(self):
        cards = self.game.combat.hand.cards

        if self.game.combat.state in [CombatState.UNIT_CHOOSE_CARD, CombatState.ACTION_CHOOSE_CARD]:
            if self.game.input.states["left"]:
                self.game.input.states["left"] = False
                self.selected_card -= 1

            if self.game.input.states["right"]:
                self.game.input.states["right"] = False
                self.selected_card += 1

            if self.game.input.states["select"]:

                # transition to appropriate mode
                if self.game.combat.state == CombatState.UNIT_CHOOSE_CARD:
                    # can only use a card if there are cards in your hand
                    if len(cards):
                        self.game.combat.state = CombatState.UNIT_SELECT_TARGET
                else:
                    self.game.combat.state = CombatState.ACTION_SELECT_TARGET

                self.place_target = [
                    self.game.combat.terrain.pixel_size[0] // 2,
                    self.game.combat.terrain.pixel_size[1] // 2,
                ]

            if self.game.input.states["cancel"]:
                if self.game.combat.state == CombatState.UNIT_CHOOSE_CARD:
                    pass

                self.game.combat.state = CombatState.WATCH

        elif self.game.combat.state in [CombatState.UNIT_SELECT_TARGET, CombatState.ACTION_SELECT_TARGET]:
            directions = {
                "right": (1, 0),
                "left": (-1, 0),
                "up": (0, -1),
                "down": (0, 1),
            }

            move_amount = [0, 0]

            # add up direction movement
            for direction in directions:
                if self.game.input.states["hold_" + direction]:
                    offset(move_amount, directions[direction], self.game.window.dt * 75)

            self.place_target = offset(self.place_target, move_amount)

            if self.game.input.states["select"]:
                # hand will contain the hand for whichever deck is in use
                if self.game.combat.state == CombatState.UNIT_SELECT_TARGET:
                    unit = cards[self.selected_card].unit
                    unit.pos = self.place_target.copy()
                    self.game.combat.units.add_unit(unit)

                    logging.info(f"Placed {unit.type}({unit.id}) at {unit.pos}.")
                else:
                    # TODO: handle action cards here
                    pass

                cards.pop(self.selected_card)

            if self.game.input.states["cancel"] or self.game.input.states["select"]:
                # transition to appropriate state
                if self.game.combat.state == CombatState.UNIT_SELECT_TARGET:
                    self.game.combat.state = CombatState.UNIT_CHOOSE_CARD
                else:
                    self.game.combat.state = CombatState.ACTION_CHOOSE_CARD

        elif self.game.combat.state == CombatState.WATCH:
            if self.game.input.states["cancel"]:
                self.game.combat.state = CombatState.ACTION_CHOOSE_CARD

        if self.game.input.states["view_troupe"]:
            self.game.input.states["view_troupe"] = False
            self.game.change_scene(SceneType.TROUPE)

        # correct card selection index for looping
        if self.selected_card < 0:
            self.selected_card = len(cards) - 1
        if self.selected_card >= len(cards):
            self.selected_card = 0

    def render(self, surface: pygame.Surface):
        # render status text
        if self.game.combat.state in [CombatState.UNIT_SELECT_TARGET, CombatState.ACTION_SELECT_TARGET]:
            status = "select a target location"
        if self.game.combat.state == CombatState.UNIT_CHOOSE_CARD:
            status = "select a unit or press X to end unit placement"
        if self.game.combat.state == CombatState.ACTION_CHOOSE_CARD:
            status = "select an action or press X to watch"
        if self.game.combat.state == CombatState.WATCH:
            status = "press X to use an action"
        self.game.assets.fonts["warning"].render(status, surface, (4, 4))

        cards = self.game.combat.hand.cards

        if self.game.combat.state in [CombatState.UNIT_SELECT_TARGET, CombatState.ACTION_SELECT_TARGET]:
            pygame.draw.circle(surface, (255, 255, 255), self.game.combat.camera.render_offset(self.place_target), 8, 1)

        if self.game.combat.state != CombatState.WATCH:
            start_pos = self.game.window.display.get_width() // 2 - (len(cards) - 1) * 30

            for i, card in enumerate(cards):
                height_offset = 0
                if self.selected_card == i:
                    height_offset = -12

                elif self.game.combat.state in [CombatState.UNIT_SELECT_TARGET, CombatState.ACTION_SELECT_TARGET]:
                    height_offset += 12

                card.render(surface, (start_pos + i * 60 - 25, 300 + height_offset))