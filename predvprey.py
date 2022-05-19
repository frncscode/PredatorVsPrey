#!/usr/bin/env python3

# -> imports
import creatures as _creatures
from pygame.locals import * 
import threading
import pygame
import random
import multiprocessing
import math
import time
import sys

pygame.init()

def drawEye(creature, win):
    pos = creature.pos
    angle = math.radians(creature.angle)
    intersects = creature.intersects
    intersects.reverse()

    pupilMajorDirection = intersects.index(max(intersects)) if intersects != [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] else (len(intersects) - 1) / 2
    pupilDirectionScalar = pupilMajorDirection / (len(intersects) - 1)
    if creature.type == 'PREY':pupilDirectionScalar = 0.5
    pupilAngle = -math.degrees(creature.fov) / 2 + math.degrees(creature.fov) * pupilDirectionScalar
    pupilAngle += creature.angle + pupilAngle
    pupilAngle = math.radians(pupilAngle)

    startPos = (pos.x - math.sin(angle) * creature.size * 0.2, pos.y - math.cos(angle) * creature.size * 0.2)
    pygame.draw.circle(win, (255, 255, 255), startPos, creature.size / 3) # -> the iris
    pygame.draw.circle(win, (0, 0, 0), (startPos[0] - math.sin(pupilAngle) * creature.size / 6, startPos[1] - math.cos(pupilAngle) * creature.size / 6), creature.size / 5)

def generateCreaturePool(preyCount, predCount, screenDimensions):
    preys, preds = [], []
    for _ in range(preyCount):
        preys.append(_creatures.Prey(random.randint(0, screenDimensions[0]), random.randint(0, screenDimensions[1]), screenDimensions))
    for _ in range(predCount):
        preds.append(_creatures.Predator(random.randint(0, screenDimensions[0]), random.randint(0, screenDimensions[1]), screenDimensions))
    return preys, preds, preys + preds

# -> man in the middle function for threading
def updateCreatures(pool, creatures):
    for idx,creature in enumerate(pool):
        creature.update(creatures)


def main():
    # -> pygame setup
    win = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Predator vs Prey')
    pygame.display.set_icon(pygame.image.load('brain.png'))
    screenDimensions = win.get_size()

    # -> how long in ticks until a prey reproduces
    preyReproductionInterval = 60 * 10

    # -> func to draw the bg
    def drawBackground():
        win.fill((40, 42, 54))
        for y in range(screenDimensions[1] // 50):
            for x in range(screenDimensions[0] // 50):
                pygame.draw.rect(win, (68, 71, 90), (x * 50, y * 50, 50, 50), 2)

    # -> simulation set up
    preys, predators, creatures = generateCreaturePool(15, 15, screenDimensions)

    # -> initial set up
    selectedCreature = None
    clock = pygame.time.Clock()
    bestPreyPerformer = _creatures.Prey(-69, -69, screenDimensions) # -> template Prey
    bestPredPerformer = _creatures.Predator(-69, -69, screenDimensions) # -> template Predator
    sidebarOpenTimerMax = 20
    sidebarOpenTimer = 0

    while True: # -> game loop

        # -> stuff
        mousePos = pygame.mouse.get_pos()
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        clickedOnSideBar = False

        # -> event loop
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # -> left button down
                    if not selectedCreature:
                        for creature in creatures:
                            if creature.rect.collidepoint(pygame.mouse.get_pos()):
                                selectedCreature = creature
                                sidebarOpenTimer = 0
                                creature.selected = True
                                break
                    else:
                        if mousePos[0] > screenDimensions[0] * 0.3:
                            selectedCreature.selected = False
                            selectedCreature.remoteControlled = False
                            selectedCreature = None
                        else:
                            clickedOnSideBar = True

        # -> handling creature deaths
        start = time.perf_counter_ns()
        if creatures:
            for idx, creature in sorted(enumerate(creatures), reverse=True):
                if creature.dead:
                    creatures.pop(idx)
        if preys:
            for idx, prey in sorted(enumerate(preys), reverse=True):
                if prey.dead:
                    preys.pop(idx)
        if predators:
            for idx, pred in sorted(enumerate(predators), reverse=True):
                if pred.dead:
                    predators.pop(idx)

        # -> updates
        sidebarOpenTimer += 1 
        if sidebarOpenTimer > sidebarOpenTimerMax:
            sidebarOpenTimer = sidebarOpenTimerMax
        
        # threading test
        a = creatures[:len(creatures) // 2]
        b = creatures[len(creatures) // 2:]
        x = threading.Thread(target=updateCreatures, args=[a, creatures])
        y = threading.Thread(target=updateCreatures, args=[b, creatures])
        start = time.perf_counter_ns()
        x.start()
        y.start()
        x.join()
        y.join()

        
        # -> handling reproductions
        reproductionPool = []
        for creature in creatures:
            if creature.type == 'PREY' and creature.reproduceTimer > preyReproductionInterval:
                reproductionPool.append(creature.reproduce())
                creature.reproduceTimer = 0
            elif creature.type == 'PREDATOR' and creature.reproduceKills >= creature.killsToReproduce:
                reproductionPool.append(creature.reproduce())
                creature.reproduceKills = 0    
            creature.lifetime += 1
            if creature.type == 'PREY':
                creature.reproduceTimer += 1

        # -> handling predator killing
        for idx, prey in sorted(enumerate(preys), reverse=True):
            for predator in predators:
                if predator.rect.colliderect(prey.rect):
                    predator.energy = predator.maxEnergy
                    predator.kills += 1
                    predator.reproduceKills += 1
                    prey.dead = True
                    if selectedCreature == prey:
                        selectedCreature = None
        
        # -> seperate loop for inserting children into the creatures list
        for child in reproductionPool:
            creatures.append(child)
            if isinstance(child, _creatures.Prey):
                preys.append(child)
            elif isinstance(child, _creatures.Predator):
                predators.append(child)

        # -> checking for best performers
        for prey in preys:
            if prey.lifetime >= bestPreyPerformer.lifetime and not prey.remoteControlled:
                bestPreyPerformer = prey
        for pred in predators:
            if pred.kills * pred.lifetime >= bestPredPerformer.kills * bestPredPerformer.lifetime and not pred.remoteControlled:
                bestPredPerformer = pred

        # -> creature spawning
        if not preys:
            for _ in range(2):
                spawned = bestPreyPerformer.clone()
                preys.append(spawned)
                creatures.append(spawned)
            spawned = bestPreyPerformer.clone(mutate=False)
            preys.append(spawned)
            creatures.append(spawned)
            spawned = bestPreyPerformer.clone(mutate=False)
            preys.append(spawned)
            creatures.append(spawned)
            bestPreyPerformer = spawned

        if not predators:
            for _ in range(2):
                spawned = bestPredPerformer.clone()
                predators.append(spawned)
                creatures.append(spawned)
            spawned = bestPredPerformer.clone(mutate=False)
            predators.append(spawned)
            creatures.append(spawned)
            spawned = bestPredPerformer.clone(mutate=False)
            predators.append(spawned)
            creatures.append(spawned)
            spawned.kills += 1
            bestPredPerformer = spawned

        # -> killing off preys if they grow to much in numbers
        if True: # -> temporarily disabled
            if len(preys) > 50:
                for prey in random.sample(preys, len(preys) - 50):
                    # -> caps prey count at 50
                    prey.dead = True
        
        if selectedCreature:
            if selectedCreature.dead:
                selectedCreature.remoteControlled = False
                selectedCreature = None
        
        # -> render
        drawBackground()
        for creature in creatures:
            if not creature.dead:
                creature.draw(win)
        if selectedCreature:
            pygame.draw.circle(win, (255, 121, 198), selectedCreature.rect.center, selectedCreature.size // 2, 2)
            pygame.draw.polygon(win, (255, 121, 198), [
                (selectedCreature.pos.x, selectedCreature.pos.y - 0.8 * selectedCreature.size),
                (selectedCreature.pos.x - selectedCreature.size / 3, selectedCreature.pos.y - 1.2 * selectedCreature.size),
                (selectedCreature.pos.x + selectedCreature.size / 3, selectedCreature.pos.y - 1.2 * selectedCreature.size)
                ])
        for creature in creatures:
            drawEye(creature, win)
        
        # draw a crown on the best performer (if on screen)
        if bestPredPerformer in creatures:
            pred = bestPredPerformer
            if pred.selected:
                pygame.draw.polygon(win, (255, 230, 0),[
                (pred.pos.x - pred.size / 2, pred.pos.y - pred.size * 2.2),
                (pred.pos.x, pred.pos.y - 0.5 * (pred.size * 2.2 + 18)),
                (pred.pos.x + pred.size / 2, pred.pos.y - pred.size * 2.2),
                (pred.pos.x + pred.size / 2, pred.pos.y - pred.size * 2.2 + 10),
                (pred.pos.x - pred.size / 2, pred.pos.y - pred.size * 2.2 + 10)
                ])

            else:
                pygame.draw.polygon(win, (255, 230, 0),[
                (pred.pos.x - pred.size / 2, pred.pos.y - pred.size * 1.2),
                (pred.pos.x, pred.pos.y - 0.5 * (pred.size * 1.2 + 10)),
                (pred.pos.x + pred.size / 2, pred.pos.y - pred.size * 1.2),
                (pred.pos.x + pred.size / 2, pred.pos.y - pred.size * 1.2 + 10),
                (pred.pos.x - pred.size / 2, pred.pos.y - pred.size * 1.2 + 10)
                ])

        # -> render the inspect side bar
        if selectedCreature:win.blit(_creatures.generateCreatureSidebar(selectedCreature, screenDimensions, clickedOnSideBar, mousePos),
        (-screenDimensions[0] * 0.3 + (sidebarOpenTimer / sidebarOpenTimerMax) * screenDimensions[0] * 0.3, 0))

        pygame.display.update()
        clock.tick(60)

main()
sys.exit()

import cProfile
import pstats

with cProfile.Profile() as pr:
    main()

stats = pstats.Stats(pr)
stats.sort_stats(pstats.SortKey.TIME)
stats.print_stats()