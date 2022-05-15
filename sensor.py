import math
import pygame

def lerp(a, b, t):
    return a + (a - b) * t

class Sensor:

    def __init__(self, creature, raylength):
        self.creature = creature
        self.rayCount = 10
        self.rayLength = raylength
        self.fov = self.creature.fov

        self.rays = []
    
    def intersects(self, angle, creatures):
        for dist in range(1, self.rayLength, 4):
            pos = (self.creature.pos.x - math.sin(angle) * dist,
                   self.creature.pos.y - math.cos(angle) * dist)
            for creature in creatures:
                # if creature.type == self.creature.type:
                #     continue
                if creature == self.creature:
                    continue
                if creature.rect.collidepoint(pos):
                    return round(1 - dist / self.rayLength, 2)
        return 0

    def update(self, creatures):
        intersects = []
        self.rays = []
        angles = []
        for i in range(self.rayCount):
            angle = lerp(self.fov / 2, - self.fov / 2, i / (self.rayCount - 1)) + self.creature.angle
            start = [self.creature.pos.x, self.creature.pos.y]
            angles.append(angle)
            end = [self.creature.pos.x - math.sin(angle) * self.rayLength,
                   self.creature.pos.y - math.cos(angle) * self.rayLength]
            self.rays.append([start, end])
        
        for i in range(len(angles)): # -> in parallel with rays[] 
            intersect = self.intersects(angles[i], creatures)
            intersects.append(intersect)
            deltaX = self.rays[i][1][0] - self.rays[i][0][0]
            deltaY = self.rays[i][1][1] - self.rays[i][0][1]
            self.rays[i][1][0] = self.rays[i][1][0] - deltaX + (deltaX * (1 - intersect))
            self.rays[i][1][1] = self.rays[i][1][1] - deltaY + (deltaY * (1 - intersect))
            # -> red: not intersected, green: interesected
            if intersect != 0:
                self.rays[i].append((255, 0, 0))
            else:
                self.rays[i].append((0, 255, 0))

        return intersects