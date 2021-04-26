import time

import pygame
from pygame.locals import *

class Window:
    def __init__(self, game):
        self.game = game

        pygame.init()

        self.base_resolution = [640, 360]
        self.scaled_resolution = [1280, 720]

        self.window = pygame.display.set_mode(self.scaled_resolution, 0, 32)
        pygame.display.set_caption("NQP2?")

        self.display = pygame.Surface(self.base_resolution)

        self.dt = 0.1
        self.frame_start = time.time()

    def render_frame(self):
        self.window.blit(pygame.transform.scale(self.display, self.window.get_size()), (0, 0))
        pygame.display.update()
        self.display.fill((0, 0, 0))

        self.dt = time.time() - self.frame_start
        self.frame_start = time.time()