#!/usr/bin/env python3

# -> imports
import pstats

from numpy import isin
import creatures as _creatures
from pygame.locals import * 
import pygame
import random
import math
import sys


def main():
    # -> pygame setup
    win = pygame.display.set_mode((600, 600))
    pygame.display.set_caption('Predator vs Prey')

    preyReproductionInterval = 60 * 10

    # -> func to draw the bg
    def drawBackground():
        win.fill((173, 173, 173))
        for y in range(6):
            for x in range(6):
                pygame.draw.rect(win, (156, 156, 156), (x * 100, y * 100, 100, 100), 2)

    # -> simulation set up
    creatures = [_creatures.Prey(random.randint(1, 600), random.randint(1, 600))
                for _ in range(1)]
    for _ in range(0):
        creatures.append(_creatures.Predator(random.randint(1, 600), random.randint(1, 600)))
    preys = [creature for creature in creatures if isinstance(creature, _creatures.Prey)]
    predators = [creature for creature in creatures if isinstance(creature, _creatures.Predator)]

    # -> game loop
    selectedCreature = None
    clock = pygame.time.Clock()
    bestPreyPerformer = _creatures.Prey(-69, -69) # template Prey
    bestPredPerformer = _creatures.Predator(-69, -69) # template Predator
    while True:
        # -> event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not selectedCreature:
                        for creature in creatures:
                            if creature.rect.collidepoint(pygame.mouse.get_pos()):
                                selectedCreature = creature
                                creature.selected = True
                    else:
                        selectedCreature.selected = False
                        selectedCreature = None
        
        # -> handling creature deaths
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
        reproductionPool = []
        for idx, creature in sorted(enumerate(creatures), reverse=True):
            creature.update(creatures)
            # -> handling reproductions
            if isinstance(creature, _creatures.Prey) and creature.reproduceTimer > preyReproductionInterval:
                reproductionPool.append(creature.reproduce())
                creature.reproduceTimer = 0
            elif isinstance(creature, _creatures.Predator) and creature.reproduceKills >= creature.killsToReproduce:
                reproductionPool.append(creature.reproduce())
                creature.reproduceKills = 0    
            creature.lifetime += 1
            if isinstance(creature, _creatures.Prey):
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

        # checking for best performers
        for prey in preys:
            if prey.lifetime >= bestPreyPerformer.lifetime:
                bestPreyPerformer = prey
        for pred in predators:
            if pred.kills / (pred.lifetime + 1) >= bestPredPerformer.kills / (bestPredPerformer.lifetime + 1):
                bestPredPerformer = pred

        # -> creature spawning
        if not preys:
            for _ in range(3):
                spawned = bestPreyPerformer.clone()
                preys.append(spawned)
                creatures.append(spawned)
        if not predators:
            for _ in range(3):
                spawned = bestPredPerformer.clone()
                predators.append(spawned)
                creatures.append(spawned)

        if len(preys) > 50:
            for prey in random.sample(preys, 5):
                prey.dead = True
        
        # -> render
        drawBackground()
        for creature in creatures:
            if not creature.dead:
                creature.draw(win)
        if selectedCreature:
            pygame.draw.rect(win, (255, 0, 0), selectedCreature.rect, 3)

        pygame.display.update()
        clock.tick(60)

main()

# import cProfile
# import pstats

# with cProfile.Profile() as pr:
#     main()

# stats = pstats.Stats(pr)
# stats.sort_stats(pstats.SortKey.TIME)
# stats.print_stats()