
SCREEN_SIZE = (800, 600)

import math, uuid, events, script, gameobjs, objmanager

from OpenGL.GL import *
from OpenGL.GLU import *

import pygame, events
from pygame.locals import *
import numpy as np

### OpenGL Utility Functions

def resize(width, height):
	
	glViewport(0, 0, width, height)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(60.0, float(width)/height, .001, 1000.)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()

def init():
	
	glDisable(GL_DEPTH_TEST)
	glClearColor(1.0, 1.0, 1.0, 0.0)
	glEnable(GL_BLEND)

### Main Program

def run():
	
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE, HWSURFACE|OPENGL|DOUBLEBUF)
	
	resize(*SCREEN_SIZE)
	init()
	
	clock = pygame.time.Clock()	
	
	glMaterial(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))	
	glMaterial(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

	movement_speed = 5.0
	camPos = [0., 0., 30.]

	eventMediator = events.EventMediator()

	scriptObj = script.Script(eventMediator)
	gameObjects = objmanager.GameObjects(eventMediator)

	player = gameobjs.Person(eventMediator)
	player.playerId = uuid.uuid4()
	player.faction = 1
	gameObjects.Add(player)
	gameObjects.playerId = player.playerId

	addPlayerEvent = events.Event("addplayer")
	addPlayerEvent.playerId = player.playerId
	eventMediator.Send(addPlayerEvent)

	startEvent = events.Event("gamestart")
	eventMediator.Send(startEvent)

	while True:
		
		time_passed = clock.tick()
		time_passed_seconds = time_passed / 1000.

		for event in pygame.event.get():
			if event.type == QUIT:
				return
			if event.type == KEYUP and event.key == K_ESCAPE:
				return
			if event.type == MOUSEBUTTONDOWN:
				worldPos = gluUnProject(event.pos[0], SCREEN_SIZE[1] - event.pos[1], 1.)
				rayVec = np.array(worldPos) - np.array(camPos)
				rayVecMag = np.linalg.norm(rayVec, ord=2)
				if rayVecMag > 0.:
					rayVec /= rayVecMag

				#Scale ray based on altitude
				scaleFac = -camPos[2] / rayVec[2]
				clickWorld = scaleFac * rayVec + np.array(camPos)
				#print "clickWorld", clickWorld

				gameObjects.WorldClick((clickWorld[0], clickWorld[1]), event.button)

		pressed = pygame.key.get_pressed()

		if pressed[K_LEFT]:
			camPos[0] -= 1. * time_passed_seconds * camPos[2]
		if pressed[K_RIGHT]:
			camPos[0] += 1. * time_passed_seconds * camPos[2]
		if pressed[K_UP]:
			camPos[1] += 1. * time_passed_seconds * camPos[2]
		if pressed[K_DOWN]:
			camPos[1] -= 1. * time_passed_seconds * camPos[2]
		if pressed[K_a]:
			camPos[2] -= 20. * time_passed_seconds
		if pressed[K_z]:
			camPos[2] += 20. * time_passed_seconds
		
		gameObjects.Update(time_passed_seconds, pygame.time.get_ticks() / 1000.)

		# Clear the screen, and z-buffer
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
						
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		gluLookAt(camPos[0], camPos[1], camPos[2], # look from camera XYZ
			camPos[0], camPos[1], 0., # look at the ground plane
			0., 1., 0.); # up

		gameObjects.Draw()

		# Show the screen
		pygame.display.flip()

if __name__ == "__main__":
	run()

