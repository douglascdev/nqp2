import math

import pygame


class Projectile:
    def __init__(self, game, owner, target):
        self.game = game
        self.owner = owner
        self.target = target
        self.angle = self.owner.angle(target)
        self.img = owner.projectile_data["img"]
        self.speed = owner.projectile_data["speed"]
        self.pos = self.owner.pos.copy()

        # move base firing position towards center of entity
        self.pos[1] -= 5

        self.damage = self.owner.attack

    def update(self, dt):
        remaining_dis = self.speed * dt
        while remaining_dis > 0:
            dis = min(remaining_dis, 4)
            remaining_dis -= dis

            self.pos[0] += math.cos(self.angle) * dis
            self.pos[1] += math.sin(self.angle) * dis
            r = pygame.Rect(self.pos[0] - 4, self.pos[1] - 4, 8, 8)

            if not self.game.combat.terrain.check_tile_hoverable(self.pos):
                return False

            for entity in self.game.combat.all_entities:
                if entity.team != self.owner.team:
                    if r.collidepoint(entity.pos):
                        entity.deal_damage(self.damage, self.owner)
                        return False

        return True

    def render(self, surf, offset=(0, 0)):
        img = self.game.assets.projectiles[self.img]
        rotated_img = pygame.transform.rotate(img, -math.degrees(self.angle))
        surf.blit(
            rotated_img,
            (
                self.pos[0] - rotated_img.get_width() // 2 + offset[0],
                self.pos[1] - rotated_img.get_height() // 2 + offset[1],
            ),
        )
