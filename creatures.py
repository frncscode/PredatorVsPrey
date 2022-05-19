# -> imports
import pygame
import random
import network
from sensor import Sensor
import math
import numpy as np
import time
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
        self.size = 15
        self.image = pygame.Surface((self.size, self.size))
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))
        self.angle = random.randint(0, 360)
        self.intersects = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

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
            if random.random() < 0.6:
                print('mutating weights')
                # -> mutating weights
                for weights in layer.weights:
                    for idx, weight in enumerate(weights):
                        if random.random() < 0.02:
                            layer.weights[idx] = weight + random.random() - 0.5
                        if random.random() < 0.02:
                            layer.weights[idx] *= -1
                        if random.random() < 0.02:
                            layer.bias[0][idx] = random.random() - 0.5
            if random.random() < 0.6:
                print('mutating biases')
                # -> mutating biases
                for idx, bias in enumerate(layer.bias[0]):
                    if random.random() < 0.02:
                        layer.bias[0][idx] + random.random() - 0.5
                    if random.random() < 0.02:
                        layer.bias[0][idx] = random.random() - 0.5
                    if random.random() < 0.02:
                        layer.bias[0][idx] *= -1
        return child
        

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
        if not self.selected:self.remoteControlled = False
        self.intersects = self.sensor.update(creatures)
        self.intersects.reverse()
        if not self.remoteControlled:
            # -> getting movement from neural network
            angularChange, speed = self.parseNetwork(self.intersects)
            self.angle += angularChange
            self.speed = speed if self.energy - (0.25 * speed) > 0 else 0
        else:
            self.move() # -> player control
            self.speed = self.speed if self.energy > 0 else 0

        if self.speed == 0: # -> when creature is idle, give it dose of energy
            self.energy += 0.25 if self.energy < self.maxEnergy else 0
        elif self.energy - 0.25 * self.speed > 0: # -> has energy and wants to move
            radians = math.radians(self.angle)
            self.pos.x -= math.sin(radians) * self.speed
            self.pos.y -= math.cos(radians) * self.speed
            self.energy -= 0.2 * self.speed
            self.clampInScreen()
            self.rect.center = self.pos
    
    def reproduce(self):
        child = Prey(self.rect.centerx + random.randint(-20, 20), self.rect.centery + random.randint(-20, 20), self.screenDimensions)
        child.network = self.network
        return self.mutate(child) if random.random() < 0.5 else child

class Predator(Creature):
    def __init__(self, x, y, screenDimensions):
        self.type = "PREDATOR"
        self.kills = 0
        self.reproduceKills = 0
        self.killsToReproduce = 3
        self.fov = math.pi / 5
        self.sensor = Sensor(self, 200)
        self.energy = 100
        self.colour = (179, 18, 77)
        super().__init__(x, y, screenDimensions)
        self.image.fill((150, 0, 0))
    
    def update(self, creatures):
        if not self.selected:self.remoteControlled = False
        start = time.perf_counter_ns()
        self.intersects = self.sensor.update(creatures)
        # print('Sensor Update Took:', str(time.perf_counter_ns() - start))
        self.intersects.reverse()
        if self.energy <= 0:
            self.selected = False
            self.remoteControlled = False
            self.dead = True
            return

        if not self.remoteControlled:
            # -> get instructions from the neural network
            start = time.perf_counter_ns()
            angularChange, self.speed = self.parseNetwork(self.intersects)
            # print('Network Took:', str(time.perf_counter_ns() - start))
            self.angle += angularChange
        else:
            self.move()

        self.radians = math.radians(self.angle)
        self.pos.x -= math.sin(self.radians) * self.speed
        self.pos.y -= math.cos(self.radians) * self.speed
        self.clampInScreen()
        self.rect.center = self.pos
        self.energy -= max(self.speed * 0.2, 0.05) # -> energy usage must be at least 0.2 so they dont live forever

    def reproduce(self):
        child = Predator(self.rect.centerx + random.randint(-20, 20), self.rect.centery + random.randint(-20, 20), self.screenDimensions)
        child.network = self.network # -> copy network over
        return child



# -> Function that gets infomation from a selected creature and creates a sidebar object
# -> that can be drawn to the screen

def getFontObject(msg, fontSize=24, colour=(0, 0, 0)):
    # -> pygame wrapper to speed up text creation
    font = pygame.font.SysFont('Consolas', fontSize)
    fontSurface = font.render(msg, True, colour)
    return fontSurface

def generateCreatureSidebar(creature, winDimensions, clicked, mousePos):
    # -> returns a sidebar surface for infomation on creatures
    sidebarSize = (winDimensions[0] * 0.3, winDimensions[1])
    surface = pygame.Surface(sidebarSize, pygame.SRCALPHA)
    surface.fill((98, 114, 164, 200))

    # -> drawing the side bar title
    fontObject = getFontObject(creature.type, fontSize=36, colour=(189, 147, 249))
    surface.blit(fontObject, (sidebarSize[0] * 0.5 - fontObject.get_width() / 2, sidebarSize[1] * 0.01))

    if creature.type == 'PREDATOR': # -> display kills if creature is a predator
        surface.blit(getFontObject('Kills: '+str(creature.kills), colour=(189, 147, 249)), (0, sidebarSize[1] * 0.1))

    # -> drawing lifetime
    surface.blit(getFontObject('Lifetime: '+str(creature.lifetime), colour=(189, 147, 249)), (0, sidebarSize[1] * 0.15))

    # -> drawing the energy progress bar
    surface.blit(getFontObject('Energy:', colour=(189, 147, 249)), (0, sidebarSize[1] * 0.2))
    progressBarPos = (sidebarSize[0] * 0.1, sidebarSize[1] * 0.25)
    progressBarLength = sidebarSize[0] * 0.8
    pygame.draw.rect(surface, (68, 71, 90), (progressBarPos[0], progressBarPos[1], progressBarLength, sidebarSize[1] * 0.05))
    pygame.draw.rect(surface, (80, 250, 123), (progressBarPos[0], progressBarPos[1], progressBarLength * (creature.energy / creature.maxEnergy), sidebarSize[1] * 0.05))

    # -> drawing the speed progress bar
    surface.blit(getFontObject('Speed:', colour=(189, 147, 249)), (0, sidebarSize[1] * 0.35))
    progressBarPos = (sidebarSize[0] * 0.1, sidebarSize[1] * 0.4)
    progressBarLength = sidebarSize[0] * 0.8
    pygame.draw.rect(surface, (68, 71, 90), (progressBarPos[0], progressBarPos[1], progressBarLength, sidebarSize[1] * 0.05))
    pygame.draw.rect(surface, (80, 250, 123), (progressBarPos[0], progressBarPos[1], progressBarLength * (creature.speed / creature.topSpeed), sidebarSize[1] * 0.05))

    # -> drawing realtime neural network visualizer
    surface.blit(getFontObject('Network:', colour=(189, 147, 249)), (0, sidebarSize[1] * 0.5))
    intersects = creature.intersects
    intersects.reverse()
    connectionLength = sidebarSize[0] * 0.6
    lenBetweenNeuron = sidebarSize[0] // len(intersects)
    pos = (sidebarSize[0] * 0.2, winDimensions[1] * 0.55)
    topNeuronPos = (sidebarSize[0] * 0.8, pos[1] + (lenBetweenNeuron * len(intersects) * 0.5 - (lenBetweenNeuron * 0.5)))
    bottomNeuronPos = (sidebarSize[0] * 0.8, pos[1] + (lenBetweenNeuron * len(intersects) * 0.5 + (lenBetweenNeuron * 0.5)))
    line1TotalAlpha = 0
    line2TotalAlpha = 0
    for yMove in range(len(intersects)):
        pygame.draw.circle(surface, (255, 121, 198, (intersects[yMove] * 255)), (pos[0], pos[1] + yMove * lenBetweenNeuron), 5)
        line1Alpha = (intersects[yMove] * 255)
        line2Alpha = (intersects[yMove] * 255)
        pygame.draw.line(surface, (139, 233, 253, line1Alpha), (pos[0], pos[1] + yMove * lenBetweenNeuron), topNeuronPos, 2)
        pygame.draw.line(surface, (139, 233, 253, line2Alpha), (pos[0], pos[1] + yMove * lenBetweenNeuron), bottomNeuronPos, 2)
        line1TotalAlpha += line1Alpha
        line2TotalAlpha += line2Alpha
    
    pygame.draw.circle(surface, (255, 121, 198, (line1TotalAlpha / (len(intersects) * 255) * 255)), topNeuronPos, 7)
    pygame.draw.circle(surface, (255, 121, 198, (line2TotalAlpha / (len(intersects) * 255) * 255)), bottomNeuronPos, 7)

    # -> handling the remote control feature
    surface.blit(getFontObject('Control:', colour=(189, 147, 249)), (0, sidebarSize[1] * 0.95))
    pygame.draw.rect(surface, (68, 71, 90), 
    (sidebarSize[0] * 0.5, sidebarSize[1] * 0.95, sidebarSize[0] * 0.4, sidebarSize[1] * 0.04))
    
    if not creature.remoteControlled:
        rect = pygame.Rect(sidebarSize[0] * 0.5, sidebarSize[1] * 0.95, sidebarSize[0] * 0.4 * 0.5, sidebarSize[1] * 0.04)
        pygame.draw.rect(surface, (255, 85, 85), rect)
        if clicked and rect.collidepoint(mousePos):
            creature.remoteControlled = True
    else:
        rect = pygame.Rect(sidebarSize[0] * 0.5 + sidebarSize[0] * 0.4 * 0.5, sidebarSize[1] * 0.95, sidebarSize[0] * 0.4 * 0.5, sidebarSize[1] * 0.04)
        pygame.draw.rect(surface, (80, 250, 123), rect)
        if clicked and rect.collidepoint(mousePos):
            creature.remoteControlled = False

    return surface