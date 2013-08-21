
SCREEN_SIZE = (800, 600)

import math 

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

### Person

class Person():
	def __init__(self):
		self.pos = np.array((0., 0.))
		self.heading = 0. #Radians
		self.player = None
		self.faction = 0
		self.moveOrder = None
		self.attackOrder = None
		self.speed = 5.

	def Draw(self):
		if self.faction == 0:
			glColor3f(1., 0., 0.)
		if self.faction == 1:
			glColor3f(0., 1., 0.)
		if self.faction == 2:
			glColor3f(0., 0., 1.)

		glPushMatrix()
		glTranslatef(self.pos[0], self.pos[1], 0.)
		
		glBegin(GL_POLYGON)
		radius = 1.
		for i in range(10):
			glVertex3f(radius * math.sin(i * 2. * math.pi / 10.), radius * math.cos(i * 2. * math.pi / 10.), 0.)
		glEnd()

		glColor3f(0., 0., 0.)
		glBegin(GL_POLYGON)
		glVertex3f(radius * math.sin(self.heading), radius * math.cos(self.heading), 0.)
		glVertex3f(0.1 * radius * math.sin(self.heading + math.pi / 2), 0.1 * radius * math.cos(self.heading + math.pi / 2), 0.)
		glVertex3f(0.1 * radius * math.sin(self.heading - math.pi / 2), 0.1 * radius * math.cos(self.heading - math.pi / 2), 0.)
		glEnd()

		glPopMatrix()

	def MoveTo(self, pos):
		self.moveOrder = np.array((pos[0], pos[1]))

	def Update(self, timeElapsed):
		
		if self.moveOrder is not None:
			direction = np.array(self.moveOrder) - np.array(self.pos)
			dirMag = np.linalg.norm(direction, ord=2)
			if dirMag > 0.:
				direction /= dirMag

			if dirMag < timeElapsed * self.speed:
				self.pos = self.moveOrder
				self.moveOrder = None
			else:
				self.pos += direction * timeElapsed * self.speed


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
	camPos = [0., 0., 10.]

	gameObjs = []
	player = Person()
	player.player = 1
	player.faction = 1
	gameObjs.append(player)
	enemy = Person()
	enemy.faction = 2
	enemy.pos = np.array((20., 10.))
	gameObjs.append(enemy)

	eventMediator = events.EventMediator()

	while True:
		
		time_passed = clock.tick()
		time_passed_seconds = time_passed / 1000.

		for event in pygame.event.get():
			if event.type == QUIT:
				return
			if event.type == KEYUP and event.key == K_ESCAPE:
				return
			if event.type == MOUSEBUTTONDOWN:
				print event
				worldPos = gluUnProject(event.pos[0], SCREEN_SIZE[1] - event.pos[1], 1.)
				rayVec = np.array(worldPos) - np.array(camPos)
				rayVecMag = np.linalg.norm(rayVec, ord=2)
				if rayVecMag > 0.:
					rayVec /= rayVecMag

				#Scale ray based on altitude
				scaleFac = -camPos[2] / rayVec[2]
				clickWorld = scaleFac * rayVec + np.array(camPos)
				print clickWorld

				if event.button == 1:
					for obj in gameObjs:
						if obj.player != 1: continue
						obj.MoveTo(clickWorld)

				if event.button == 3:
					for obj in gameObjs:
						if obj.player != 1: continue
						obj.attackOrder = clickWorld

		pressed = pygame.key.get_pressed()

		if pressed[K_LEFT]:
			camPos[0] -= 1. * time_passed_seconds * camAlt
		if pressed[K_RIGHT]:
			camPos[0] += 1. * time_passed_seconds * camAlt
		if pressed[K_UP]:
			camPos[1] += 1. * time_passed_seconds * camAlt
		if pressed[K_DOWN]:
			camPos[1] -= 1. * time_passed_seconds * camAlt
		if pressed[K_a]:
			camPos[2] -= 10. * time_passed_seconds
		if pressed[K_z]:
			camPos[2] += 10. * time_passed_seconds
		
		for obj in gameObjs:
			obj.Update(time_passed_seconds)

		# Clear the screen, and z-buffer
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
						
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		gluLookAt(camPos[0], camPos[1], camPos[2], # look from camera XYZ
			camPos[0], camPos[1], 0., # look at the ground plane
			0., 1., 0.); # up

		for obj in gameObjs:
			obj.Draw()

		# Show the screen
		pygame.display.flip()

if __name__ == "__main__":
	run()

