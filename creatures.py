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
    def __init__(self, x, y, screenDimensions):
        # -> basic setup
        self.screenDimensions = screenDimensions
        self.lifetime = 0
        self.maxEnergy = 100
        self.dead = False
        self.energy = self.maxEnergy
        self.topSpeed = 4
        self.topAngle = 40
        self.speed = 0
        self.pos = pygame.math.Vector2(x, y)
        self.size = 25
        self.image = pygame.Surface((self.size, self.size))
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))
        self.angle = random.randint(0, 360)

        # -> neural network set up
        self.network = network.Network()
        self.network.add(network.FCLayer(10, 6))
        self.network.add(network.FCLayer(6, 4))
        self.network.add(network.FCLayer(4, 2))
        self.network.add(network.ActivationLayer(network.sigmoid))

        # -> misc 
        self.selected = False
        self.remoteControlled = False
    
    # -> move function for remote controlled creatures
    def move(self):
        keys = pygame.key.get_pressed()
        if keys[K_w]:
            self.speed = 2
        elif not keys[K_w]:
            self.speed = 0
        if keys[K_a]:
            self.angle += 2
        if keys[K_d]:
            self.angle -= 2
    
    # -> primative render call
    def draw(self, win):
        if self.selected: # -> only draw rays if the creature is selected
            for ray in self.sensor.rays:
                pygame.draw.line(win, ray[2], ray[0], ray[1], 2)
        pygame.draw.circle(win, self.colour, self.rect.center, self.size / 2)
    
    # -> returns instructions from the neural network
    def parseNetwork(self, intersects):
        angularChange, speed = self.network.predict([np.array(intersects)])[0]
        angularChange = (0 - (0.5 - angularChange) * 2) * self.topAngle
        speed = self.topSpeed * speed
        return angularChange, speed
    
    # -> clamp the creature into the screen
    def clampInScreen(self):
        if self.pos.x < 0:
            self.pos.x = self.screenDimensions[0] - 1 # - self.size
        elif self.pos.x > self.screenDimensions[0]:
            self.pos.x = 0
        if self.pos.y < 0:
            self.pos.y = self.screenDimensions[1]
        elif self.pos.y > self.screenDimensions[1]:
            self.pos.y = 0

    def clone(self, mutate=True):
        if self.type == "PREY":
            clone = Prey(random.randint(1, 600), random.randint(1, 600), self.screenDimensions)
        else:
            clone = Predator(random.randint(1, 600), random.randint(1, 600), self.screenDimensions)
        clone.network = self.network
        if mutate:return self.mutate(clone)
        return clone

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
    
    def log(self):
        print('Energy:', str(self.energy))
        print('Angle:', str(self.angle))
        print('Speed:', str(self.speed))
        print('LifeTime:', str(self.lifetime))
        

class Prey(Creature):
    def __init__(self, x, y, screenDimensions):
        self.fov = math.pi * 2
        self.reproduceTimer = 0
        self.sensor = Sensor(self, 80)
        self.colour = (252, 186, 3)
        self.type = "PREY"
        super().__init__(x, y, screenDimensions)
        self.image.fill((0, 255, 0))
    
    def update(self, creatures):
        self.intersects = self.sensor.update(creatures)
        self.intersects.reverse()
        if not self.remoteControlled:
            # -> getting movement from neural network
            angularChange, speed = self.parseNetwork(self.intersects)
            self.angle += angularChange
            self.speed = speed 
        else:
            self.move() # -> player control
            self.speed = self.speed if self.energy > 0 else 0

        if self.speed == 0: # -> when creature is idle, give it dose of energy
            self.energy += 0.25 if self.energy < self.maxEnergy else 0
        elif self.energy - 0.2 * self.speed > 0: # -> has energy and wants to move
            radians = math.radians(self.angle)
            self.pos.x -= math.sin(radians) * self.speed
            self.pos.y -= math.cos(radians) * self.speed
            self.energy -= 0.2 * self.speed
            self.clampInScreen()
            self.rect.center = self.pos
    
    def reproduce(self):
        child = Prey(self.rect.centerx + random.randint(-20, 20), self.rect.centery + random.randint(-20, 20), self.screenDimensions)
        child.network = self.network
        return self.mutate(child)

class Predator(Creature):
    def __init__(self, x, y, screenDimensions):
        self.type = "PREDATOR"
        self.kills = 0
        self.reproduceKills = 0
        self.killsToReproduce = 3
        self.fov = math.pi / 4
        self.sensor = Sensor(self, 150)
        self.energy = 100
        self.colour = (179, 18, 77)
        super().__init__(x, y, screenDimensions)
        self.image.fill((150, 0, 0))
    
    def update(self, creatures):
        self.intersects = self.sensor.update(creatures)
        self.intersects.reverse()
        if self.energy <= 0:
            self.selected = False
            self.remoteControlled = False
            self.dead = True
            return

        if not self.remoteControlled:
            # -> get instructions from the neural network
            angularChange, self.speed = self.parseNetwork(self.intersects)
            self.angle += angularChange
        else:
            self.move()

        self.radians = math.radians(self.angle)
        self.pos.x -= math.sin(self.radians) * self.speed
        self.pos.y -= math.cos(self.radians) * self.speed
        self.clampInScreen()
        self.rect.center = self.pos
        self.energy -= max(self.speed * 0.2, 0.1) # -> energy usage must be at least 0.2 so they dont live forever

    def reproduce(self):
        child = Predator(self.rect.centerx + random.randint(-20, 20), self.rect.centery + random.randint(-20, 20), self.screenDimensions)
        child.network = self.network # -> copy network over
        return child