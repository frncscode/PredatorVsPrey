# -> imports
import pygame
import random
import network
from sensor import Sensor
import math
import numpy as np
from pygame.locals import *

# -> convert degrees to radians
def convAngle(angle):
    return (angle + -45) * (math.pi / 180)

# Creature primative
class Creature:
    def __init__(self, x, y):
        # basic setup
        self.lifetime = 0
        self.maxEnergy = 100
        self.dead = False
        self.energy = self.maxEnergy
        self.topSpeed = 2
        self.topAngle = 40
        self.speed = 0
        self.pos = pygame.math.Vector2(x, y)
        self.size = 15
        self.image = pygame.Surface((self.size, self.size))
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))
        self.angle = 0

        # neural network set up
        self.network = network.Network()
        self.network.add(network.FCLayer(10, 6))
        self.network.add(network.FCLayer(6, 4))
        self.network.add(network.FCLayer(4, 2))
        self.network.add(network.ActivationLayer(network.sigmoid))

        # misc 
        self.selected = False
    
    def move(self):
        keys = pygame.key.get_pressed()
        if keys[K_w]:
            self.rect.y -= 3
        if keys[K_s]:
            self.rect.y += 3
        if keys[K_a]:
            self.rect.x -= 3
        if keys[K_d]:
            self.rect.x += 3
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery
    
    # -> returns instructions from the neural network
    def parseNetwork(self, intersects):
        angularChange, speed = self.network.predict([np.array(intersects)])[0]
        angularChange = (0 - (0.5 - angularChange) * 2) * self.topAngle
        speed = self.topSpeed * speed
        return angularChange, speed
    
    # -> clamp the creature into the screen
    def clampInScreen(self):
        # if self.rect.x < 0:
        #     self.rect.x = 0
        # elif self.rect.x + self.size> 600:
        #     self.rect.x = 600 - self.size
        # if self.rect.y < 0:
        #     self.rect.y = 0
        # elif self.rect.y + self.size> 600:
        #     self.rect.y = 600 - self.size
        if self.rect.x < 0:
            self.rect.x = 600 - self.size
        elif self.rect.x + self.size > 600:
            self.rect.x = 0
        if self.rect.y < 0:
            self.rect.y = 600 - self.size
        elif self.rect.y + self.size> 600:
            self.rect.y = 0

    def clone(self):
        if isinstance(self, Prey):
            clone = Prey(random.randint(1, 600), random.randint(1, 600))
        else:
            clone = Predator(random.randint(1, 600), random.randint(1, 600))
        clone.network = self.network
        return self.mutate(clone)

    def mutate(self, child):
        childNetwork = child.network
        
        for layer in [layer for layer in childNetwork.layers if not(isinstance(layer, network.ActivationLayer))]:
            # -> mutating weights
            for weights in layer.weights:
                for idx, weight in enumerate(weights):
                    if random.random() < 0.04:
                        layer.weights[idx] = weight + random.random() - 0.5
                    elif random.random() < 0.02:
                        layer.weights[idx] *= -1
            # -> mutating biases
            for idx, bias in enumerate(layer.bias[0]):
                if random.random() < 0.04:
                    layer.bias[0][idx] + random.random() - 0.5
                if random.random() < 0.02:
                    layer.bias[0][idx] *= -1
        return child
        

class Prey(Creature):
    def __init__(self, x, y):
        self.fov = math.pi * 2
        self.reproduceTimer = 0
        self.sensor = Sensor(self, 80)
        self.type = "PREY"
        super().__init__(x, y)
        self.image.fill((0, 255, 0))
    
    def update(self, creatures):
        intersects = self.sensor.update(creatures)
        intersects.reverse()
        if not self.selected:
            # -> getting movement from neural network
            angularChange, speed = self.parseNetwork(intersects)
            self.angle += angularChange
            self.radians = math.radians(self.angle)
            self.speed = speed if self.energy > 0 else 0
            if self.speed == 0:
                self.energy += 0.25
            elif self.energy > 0: # -> has energy and wants to move
                self.speed = speed
                self.rect.centerx -= math.sin(self.radians) * self.speed
                self.rect.centery -= math.cos(self.radians) * self.speed
                self.energy -= 0.2 * self.speed
                self.clampInScreen()
                self.pos = pygame.math.Vector2(self.rect.center)
            else: # -> out of energy
                self.speed = 0
        else:
            self.move()
            self.clampInScreen()
            self.pos = pygame.math.Vector2(self.rect.center)

    def draw(self, win):
        # for ray in self.sensor.rays:
        #     pygame.draw.line(win, ray[2], ray[0], ray[1])
        #win.blit(self.image, self.rect)
        pygame.draw.circle(win, (252, 186, 3), self.rect.center, self.size / 2)
    
    def reproduce(self):
        child = Prey(self.rect.centerx + random.randint(-20, 20), self.rect.centery + random.randint(-20, 20))
        child.network = self.network
        return self.mutate(child)

class Predator(Creature):
    def __init__(self, x, y):
        self.topSpeed = 3
        self.type = "PRED"
        self.kills = 0
        self.reproduceKills = 0
        self.killsToReproduce = 3
        self.fov = math.pi / 4
        self.sensor = Sensor(self, 150)
        self.energy = 100
        super().__init__(x, y)
        self.image.fill((150, 0, 0))
    
    def update(self, creatures):
        intersects = self.sensor.update(creatures)
        intersects.reverse()
        if not self.selected:
            if self.energy > 0:
                # -> get instructions from the neural network
                angularChange, speed = self.parseNetwork(intersects)
                self.speed = speed
                self.angle += angularChange
                self.radians = math.radians(self.angle) - math.radians(45)
                self.rect.centerx -= math.sin(self.radians) * self.speed
                self.rect.centery -= math.cos(self.radians) * self.speed
                self.clampInScreen()
                self.pos = pygame.math.Vector2(self.rect.center)
                self.energy -= self.speed * 0.2
            else:
                self.dead = True
        else:
            # -> when selected a creature can be manually moved
            self.move()
            self.clampInScreen()
            self.pos = pygame.math.Vector2(self.rect.center)
    
    def draw(self, win):
        for ray in self.sensor.rays:
            pygame.draw.line(win, ray[2], ray[0], ray[1])
        #win.blit(self.image, self.rect)
        pygame.draw.circle(win, (179, 18, 77), self.rect.center, self.size / 2)
        # #pygame.draw.line(win, (0, 0, 0), self.rect.center, (
        #     self.rect.centerx - math.sin(math.radians(self.angle)) * 50,
        #     self.rect.centery - math.cos(math.radians(self.angle)) * 50
        # ))


    def reproduce(self):
        child = Predator(self.rect.centerx + random.randint(-20, 20), self.rect.centery + random.randint(-20, 20))
        child.network = self.network
        return child