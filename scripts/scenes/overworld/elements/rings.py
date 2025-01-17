from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

import pygame
import pytweening

from scripts.core import utility
from scripts.core.base_classes.node_container import NodeContainer
from scripts.core.constants import DEFAULT_IMAGE_SIZE, Direction, NodeType, OverworldState, SceneType
from scripts.scenes.overworld.elements.node import Node

if TYPE_CHECKING:
    from typing import Dict, List, Optional, Tuple

    from scripts.core.game import Game

__all__ = ["Rings"]


class Rings(NodeContainer):
    def __init__(self, game: Game, centre: Tuple[int, int], outer_radius: float, num_rings: int):
        super().__init__(game)
        self.outer_radius: float = outer_radius
        self.centre: Tuple[int, int] = centre
        self.num_rings: int = num_rings

        self.rings: Dict[int, List[Node]] = {}  # N.B. the key starts from 1
        self.current_ring: int = 0

        self._frame_timer: float = 0

    def update(self, delta_time: float):
        for nodes in self.rings.values():
            for node in nodes:
                node.update(delta_time)

        # process change between nodes
        if self.is_travel_paused:
            # transition to next state
            if self.game.memory.days_until_boss <= 0:

                self.game.overworld.state = OverworldState.BOSS_APPROACHING
            else:
                # update to allow input again
                self.game.overworld.state = OverworldState.READY
        else:
            self._transition_to_new_node(delta_time)

        # tick frame
        self._frame_timer += delta_time
        # FIXME - temporary looping frame logic
        while self._frame_timer > 0.66:
            self._frame_timer -= 0.66

    def render(self, surface: pygame.surface):
        # draw the nodes on top of the ring
        gap_between_rings = self.outer_radius / self.num_rings
        for ring_count, ring in enumerate(self.rings.values()):
            # draw ring
            pygame.draw.circle(surface, (255, 255, 255), self.centre, gap_between_rings * ring_count, 1)

            # draw nodes
            for node in ring:

                # draw connections
                if node.connected_outer_node is not None:
                    # adjust to align with centre of node images
                    outer_node_pos = node.connected_outer_node.pos
                    adjusted_node_pos = node.pos[0] + (DEFAULT_IMAGE_SIZE / 2), node.pos[1] + (DEFAULT_IMAGE_SIZE / 2)
                    adjusted_outer_node_pos = outer_node_pos[0] + (DEFAULT_IMAGE_SIZE / 2), outer_node_pos[1] + (
                        DEFAULT_IMAGE_SIZE / 2
                    )
                    pygame.draw.line(surface, (255, 255, 255), adjusted_node_pos, adjusted_outer_node_pos)

                # handle hidden type
                if node.is_type_hidden:
                    hidden_image = self.game.assets.get_image("nodes", "unknown")
                    surface.blit(hidden_image, node.pos)
                else:
                    node.render(surface)

        # draw selection
        node = self.selected_node
        radius = (node.icon.get_width() / 2) + 2
        selection_x = self.selection_pos[0] + (DEFAULT_IMAGE_SIZE / 2)
        selection_y = self.selection_pos[1] + (DEFAULT_IMAGE_SIZE / 2)
        pygame.draw.circle(surface, (230, 180, 16), (selection_x, selection_y), radius, width=1)

        # draw commander
        commander_type = self.game.memory.commander.type
        if self.target_node is None:
            frame = 0
        else:
            frame = int(self._frame_timer * 6)
        commander_image = self.game.assets.commander_animations[commander_type]["move"][frame]
        surface.blit(commander_image, (self.selection_pos[0], self.selection_pos[1]))

    def generate_nodes(self):
        logging.info(f"Generating overworld...")
        gap_between_rings = self.outer_radius / self.num_rings
        base_num_nodes = 2  # starting number of nodes
        total_nodes = 0  # for logging
        blank_nodes = 0  # for logging
        chance_node_type_hidden = self.game.data.config["overworld"]["chance_node_type_hidden"]
        window_width = self.game.window.width
        window_height = self.game.window.height

        # generate rings
        num_nodes = base_num_nodes
        for ring_count in range(0, self.num_rings + 1):

            # add boss fight as innermost ring
            if ring_count == 0:
                boss_x = (window_width // 2) - (DEFAULT_IMAGE_SIZE // 2)
                boss_y = (window_height // 2) - (DEFAULT_IMAGE_SIZE // 2)
                node_icon = self._get_node_icon(NodeType.BOSS_COMBAT)
                node = Node(NodeType.BOSS_COMBAT, False, (boss_x, boss_y), node_icon)
                self.rings[ring_count] = [node]

                self.boss_pos = (boss_x, boss_y)

                continue

            # add random number of nodes
            num_nodes += self.game.rng.randint(1, ring_count)

            logging_message = f"-> Ring {ring_count} has {num_nodes} nodes; "

            self.rings[ring_count] = []
            angle_between_nodes = 360 / num_nodes
            current_radius = gap_between_rings * ring_count
            current_angle = 0
            logging_node_types = []

            # generate nodes for each ring
            for node_count in range(num_nodes):

                # randomise angle to make positions uneven
                angle_offset = self.game.rng.randint(-5, 5)

                # get new position on circle
                current_angle += angle_offset + angle_between_nodes

                # exit if we've looped the circle
                if current_angle >= 360:
                    break

                # rotate to new angle
                vec = pygame.math.Vector2(0, -current_radius).rotate(current_angle)
                x = self.centre[0] + vec.x - (DEFAULT_IMAGE_SIZE / 2)  # adjust to align with centre of node images
                y = self.centre[1] + vec.y - (DEFAULT_IMAGE_SIZE / 2)

                # generate node type
                node_type = self._get_random_node_type()
                logging_node_types.append(node_type.name)

                # roll to see if we should hide the type
                if self.game.rng.roll() < chance_node_type_hidden:
                    is_type_hidden = True
                else:
                    is_type_hidden = False

                # get node icon
                node_icon = self._get_node_icon(node_type)

                # init node and save
                node = Node(node_type, is_type_hidden, (x, y), node_icon)
                self.rings[ring_count].append(node)

                # for logging
                total_nodes += 1
                if node_type == NodeType.BLANK:
                    blank_nodes += 1

            logging_message += f"{logging_node_types}."
            logging.debug(logging_message)

        base_num_connections = 2
        total_connections = 0  # for logging
        num_connections = base_num_connections

        # generate connections between nodes
        for ring_num, ring in self.rings.items():
            num_connections += self.game.rng.randint(0, ring_num)

            # choose random nodes
            nodes_to_connect = self.game.rng.choices(ring, k=num_connections)
            for node in nodes_to_connect:

                # find nearest node in next ring
                try:
                    smallest_distance = 999
                    nearest_node = None
                    for outer_node in self.rings[ring_num + 1]:  # +1 for next outermost ring

                        # get distance between nodes
                        x2 = (node.pos[0] - outer_node.pos[0]) ** 2
                        y2 = (node.pos[1] - outer_node.pos[1]) ** 2
                        distance = math.sqrt(x2 + y2)

                        if distance < smallest_distance:
                            smallest_distance = distance
                            nearest_node = outer_node

                    # connect nodes
                    if nearest_node is not None and nearest_node.connected_inner_node is None:
                        node.connected_outer_node = nearest_node
                        nearest_node.connected_inner_node = node
                        total_connections += 1  # for logging

                except KeyError:
                    pass

        # pick a random node in outer ring as starting position
        nodes = self.rings[len(self.rings) - 1]
        node = self.game.rng.choice(nodes)
        self.selected_node = node
        self.selection_pos = node.pos

        # make blank
        self.selected_node.type = NodeType.BLANK
        self.selected_node.icon = self._get_node_icon(NodeType.BLANK)
        total_nodes -= 1

        # set current ring
        self.current_ring = len(self.rings) - 1

        # log summary
        logging.info(
            f"-> Map generated. Rings: {len(self.rings)} | Nodes: filled:{total_nodes}, blank:{blank_nodes}"
            f" | Connections: {total_connections}"
        )

    def lr_node(self, direction: Direction):
        nodes = self.rings[self.current_ring]
        current_index = nodes.index(self.selected_node)
        if direction == Direction.LEFT:
            # handle index looping
            if current_index + 1 >= len(nodes):
                current_index = 0
            else:
                current_index += 1
        if direction == Direction.RIGHT:
            # handle index looping
            if current_index - 1 < 0:
                current_index = len(nodes) - 1
            else:
                current_index -= 1
        return nodes[current_index]

    def select_next_node(self, direction: Direction):
        nodes = self.rings[self.current_ring]
        current_index = nodes.index(self.selected_node)

        # change state to limit input
        self.game.overworld.state = OverworldState.TRAVELLING

        # start animations and movement
        self.is_travel_paused = False

        # handle in ring movement
        if direction in (Direction.LEFT, Direction.RIGHT):
            # move clockwise
            if direction == Direction.LEFT:
                # handle index looping
                if current_index + 1 >= len(nodes):
                    current_index = 0
                else:
                    current_index += 1

            # move counter clockwise
            elif direction == Direction.RIGHT:
                # handle index looping
                if current_index - 1 < 0:
                    current_index = len(nodes) - 1
                else:
                    current_index -= 1

            # update selected node
            self.target_node = nodes[current_index]

        # handle cross ring movement
        elif direction in (Direction.UP, Direction.DOWN):
            # move inwards
            if direction == Direction.DOWN:
                # check for an inner connection
                if self.selected_node.connected_inner_node is not None:
                    self.target_node = self.selected_node.connected_inner_node
                    self.current_ring -= 1

            elif direction == Direction.UP:
                # check for an outer connection
                if self.selected_node.connected_outer_node is not None:
                    self.target_node = self.selected_node.connected_outer_node
                    self.current_ring += 1
