import math
import pygame
import time 

def lerp(a, b, t):
    return a + (a - b) * t

# -> sensor class for ray casting
class Sensor:

    def __init__(self, creature, raylength):
        self.creature = creature
        self.rayCount = 10
        self.rayLength = raylength
        self.fov = self.creature.fov # -> radians
        self.rays = []
    
    def intersects(self, angle, creatures):
        for dist in range(1, self.rayLength, 5):
            pos = (self.creature.pos.x - math.sin(angle) * dist,
                   self.creature.pos.y - math.cos(angle) * dist)
            for creature in creatures:
                if creature.type == self.creature.type:
                    continue
                if creature.rect.collidepoint(pos):
                    return round(1 - dist / self.rayLength, 2)
        return 0

    def update(self, creatures):
        intersects = []
        self.rays = []
        angles = []
        startTime = time.perf_counter_ns()
        for i in range(self.rayCount):
            radians = math.radians(self.creature.angle) - math.radians(45)
            angle = lerp(self.fov / 2, - self.fov / 2, i / (self.rayCount - 1)) + radians
            start = [self.creature.pos.x, self.creature.pos.y]
            angles.append(angle)
            end = [self.creature.pos.x - math.sin(angle) * self.rayLength,
                   self.creature.pos.y - math.cos(angle) * self.rayLength]
            self.rays.append([start, end])
        #print('Calculating Rays Took:', str(time.perf_counter_ns() - startTime))
        
        startTime = time.perf_counter_ns()
        for i in range(len(angles)): # -> in parallel with rays[] 
            intersect = self.intersects(angles[i], creatures)
            intersects.append(intersect)
            deltaX = self.rays[i][1][0] - self.rays[i][0][0]
            deltaY = self.rays[i][1][1] - self.rays[i][0][1]
            self.rays[i][1][0] = self.rays[i][1][0] - deltaX + (deltaX * (1 - intersect))
            self.rays[i][1][1] = self.rays[i][1][1] - deltaY + (deltaY * (1 - intersect))
            # -> red: not intersected, green: interesected
            if intersect != 0:
                self.rays[i].append((255, 85, 85))
            else:
                self.rays[i].append((80, 250, 123))
        #print('Testing For Intersects Took:', str(time.perf_counter_ns() - startTime))
        return intersects
        
        '''
    possible optimization ->
        intersects = []
        self.rays = []
        angles = []
        for i in range(self.rayCount):
            added = False
            radians = math.radians(self.creature.angle) - math.radians(45)
            angle = lerp(self.fov / 2, - self.fov / 2, i / (self.rayCount - 1)) + radians
            start = [self.creature.pos.x, self.creature.pos.y]
            angles.append(angle)
            for dist in range(1, self.rayLength, 5):
                end = [self.creature.pos.x - math.sin(angle) * dist,
                       self.creature.pos.y - math.cos(angle)* dist ]
                for creature in creatures:
                    if not(creature.type == self.creature.type) and creature.rect.collidepoint(end):
                        intersects.append(round(1 - dist / self.rayLength, 2))
                        added = True
                        self.rays.append([start, end, (255, 0, 0)])
            if not added:
                intersects.append(0)
                self.rays.append([start, end, (0, 247, 70)])
        return intersects
        '''