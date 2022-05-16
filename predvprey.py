#!/usr/bin/env python3

# -> imports
import creatures as _creatures
from pygame.locals import * 
import pygame
import random
import sys

pygame.init()

def getFontObject(msg, fontSize=24, colour=(0, 0, 0)):
    font = pygame.font.SysFont('Consolas', fontSize)
    fontSurface = font.render(msg, True, colour)
    return fontSurface

def generateCreatureSidebar(creature, winDimensions):
    # -> returns a sidebar surface for infomation on creatures
    sidebarSize = (winDimensions[0] * 0.3, winDimensions[1])
    surface = pygame.Surface(sidebarSize, pygame.SRCALPHA)
    surface.fill((0, 0, 0, 100))

    # -> drawing the side bar title
    fontObject = getFontObject(creature.type, fontSize=36, colour=(255, 0, 0))
    surface.blit(fontObject, (sidebarSize[0] * 0.5 - fontObject.get_width() / 2, sidebarSize[1] * 0.01))

    if creature.type == 'PREDATOR': # -> display kills if creature is a predator
        surface.blit(getFontObject('Kills: '+str(creature.kills), colour=(255, 0, 0)), (0, sidebarSize[1] * 0.1))

    # -> drawing lifetime
    surface.blit(getFontObject('Lifetime: '+str(creature.lifetime), colour=(255, 0, 0)), (0, sidebarSize[1] * 0.15))

    # -> drawing the energy progress bar
    surface.blit(getFontObject('Energy:', colour=(255, 0, 0)), (0, sidebarSize[1] * 0.2))
    progressBarPos = (sidebarSize[0] * 0.1, sidebarSize[1] * 0.25)
    progressBarLength = sidebarSize[0] * 0.8
    pygame.draw.rect(surface, (0, 0, 0), (progressBarPos[0], progressBarPos[1], progressBarLength, sidebarSize[1] * 0.05))
    pygame.draw.rect(surface, (0, 255, 0), (progressBarPos[0], progressBarPos[1], progressBarLength * (creature.energy / creature.maxEnergy), sidebarSize[1] * 0.05))

    # -> drawing the speed progress bar
    surface.blit(getFontObject('Speed:', colour=(255, 0, 0)), (0, sidebarSize[1] * 0.35))
    progressBarPos = (sidebarSize[0] * 0.1, sidebarSize[1] * 0.4)
    progressBarLength = sidebarSize[0] * 0.8
    pygame.draw.rect(surface, (0, 0, 0), (progressBarPos[0], progressBarPos[1], progressBarLength, sidebarSize[1] * 0.05))
    pygame.draw.rect(surface, (0, 255, 0), (progressBarPos[0], progressBarPos[1], progressBarLength * (creature.speed / creature.topSpeed), sidebarSize[1] * 0.05))

    # -> drawing realtime neural network visualizer
    surface.blit(getFontObject('Network:', colour=(255, 0, 0)), (0, sidebarSize[1] * 0.5))
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
        pygame.draw.circle(surface, (0, 255, 0, (intersects[yMove] * 255)), (pos[0], pos[1] + yMove * lenBetweenNeuron), 5)
        line1Alpha = (intersects[yMove] * 255)
        line2Alpha = (intersects[yMove] * 255)
        pygame.draw.line(surface, (255, 0, 0, line1Alpha), (pos[0], pos[1] + yMove * lenBetweenNeuron), topNeuronPos, 2)
        pygame.draw.line(surface, (255, 0, 0, line2Alpha), (pos[0], pos[1] + yMove * lenBetweenNeuron), bottomNeuronPos, 2)
        line1TotalAlpha += line1Alpha
        line2TotalAlpha += line2Alpha
    
    pygame.draw.circle(surface, (0, 255, 0, (line1TotalAlpha / (len(intersects) * 255) * 255)), topNeuronPos, 7)
    pygame.draw.circle(surface, (0, 255, 0, (line2TotalAlpha / (len(intersects) * 255) * 255)), bottomNeuronPos, 7)


    return surface

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
        win.fill((173, 173, 173))
        for y in range(screenDimensions[1] // 50):
            for x in range(screenDimensions[0] // 50):
                pygame.draw.rect(win, (156, 156, 156), (x * 50, y * 50, 50, 50), 2)

    # -> simulation set up
    creatures = [_creatures.Prey(random.randint(1, 600), random.randint(1, 600), screenDimensions)
                for _ in range(1)]
    for _ in range(0):
        creatures.append(_creatures.Predator(random.randint(1, 600), random.randint(1, 600), screenDimensions))
    preys = [creature for creature in creatures if isinstance(creature, _creatures.Prey)]
    predators = [creature for creature in creatures if isinstance(creature, _creatures.Predator)]

    # -> game loop
    selectedCreature = None
    clock = pygame.time.Clock()
    bestPreyPerformer = _creatures.Prey(-69, -69, screenDimensions) # -> template Prey
    bestPredPerformer = _creatures.Predator(-69, -69, screenDimensions) # -> template Predator
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
                                break
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

        # -> checking for best performers
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
            spawned = bestPreyPerformer.clone(mutate=False)
            preys.append(spawned)
            creatures.append(spawned)
            bestPreyPerformer = spawned
            # -> reset the best prey performer to be one of the new spawning creatures
            # -> therefore the creature reproduction pool can vary more and more chance of a cool mutation occuring
        if not predators:
            for _ in range(3):
                spawned = bestPredPerformer.clone()
                predators.append(spawned)
                creatures.append(spawned)
            spawned = bestPredPerformer.clone(mutate=False)
            predators.append(spawned)
            creatures.append(spawned)
            bestPreyPerformer = spawned
            bestPredPerformer = spawned
            # -> same reasoning as above - with the preys reproduction

        # -> killing off preys if they grow to much in numbers
        if len(preys) > 50:
            for prey in random.sample(preys, len(preys) - 50):
                # -> caps prey count at 50
                prey.dead = True
        
        if selectedCreature:
            if selectedCreature.dead:
                selectedCreature = None
        
        # -> render
        drawBackground()
        for creature in creatures:
            if not creature.dead:
                creature.draw(win)
        if selectedCreature:
            pygame.draw.circle(win, (0, 0, 255), selectedCreature.rect.center, selectedCreature.size // 2, 2) 
        # -> render the inspect side bar
        if selectedCreature:win.blit(generateCreatureSidebar(selectedCreature, screenDimensions), (0, 0))

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