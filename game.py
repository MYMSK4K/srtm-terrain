
SCREEN_SIZE = (800, 600)

import math, uuid, events

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

class Person(object):
	def __init__(self, mediator):
		self.pos = np.array((0., 0.))
		self.heading = 0. #Radians
		self.player = None
		self.faction = 0
		self.moveOrder = None
		self.attackOrder = None
		self.speed = 5.
		self.objId = uuid.uuid4()
		self.mediator = mediator
		self.attackRange = 5.
		self.fireTime = None
		self.firePeriod = 1.

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
		self.moveOrder = np.array(pos)
		self.attackOrder = None

	def Attack(self, uuid):
		self.attackOrder = uuid
		self.moveOrder = None

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

		if self.attackOrder is not None:
			event = events.Event("getpos")
			event.objId = self.attackOrder
			getEnemyPosRet = self.mediator.Send(event)
			getEnemyPos = getEnemyPosRet[0]
			direction = getEnemyPos - np.array(self.pos)
			dirMag = np.linalg.norm(direction, ord=2)
			if dirMag > 0.:
				direction /= dirMag

			if dirMag > self.attackRange * 0.95:
				self.pos += direction * timeElapsed * self.speed

			if dirMag <= self.attackRange:
				#Check if we can fire
				durationSinceFiring = None
				timeNow = (pygame.time.get_ticks() / 1000.)
				if self.fireTime is not None:
					durationSinceFiring = timeNow - self.fireTime
				if durationSinceFiring is None or self.firePeriod < durationSinceFiring:
					self.fireTime = timeNow
				


class Shell(object):
	def __init__(self, mediator):
		pass

	def Draw(self):
		pass

	def Update(self, timeElapsed):
		pass

class GameObjects(events.EventCallback):
	def __init__(self, mediator):
		super(GameObjects, self).__init__(mediator)
		mediator.AddListener("getpos", self)
		self.objs = {}

	def Add(self, obj):
		self.objs[obj.objId] = obj

	def ProcessEvent(self, event):
		if event.type == "getpos":
			if event.objId not in self.objs:
				raise Exception("Unknown object id")
			return self.objs[event.objId].pos

	def Update(self, timeElapsed):
		for objId in self.objs:
			self.objs[objId].Update(timeElapsed)

	def Draw(self):
		for objId in self.objs:
			self.objs[objId].Draw()

	def ObjNearPos(self, pos, notFaction = None):
		bestDist = None
		pos = np.array(pos)
		for objId in self.objs:
			obj = self.objs[objId]
			if notFaction is not None and obj.faction == notFaction: continue
			direction = obj.pos - pos
			mag = np.linalg.norm(direction, ord=2)
			if bestDist is None or mag < bestDist:
				bestDist = mag
				bestUuid = obj.objId

		return bestUuid, bestDist

	def WorldClick(self, worldPos, button):
		if button == 1:
			for objId in self.objs:
				obj = self.objs[objId]
				if obj.player != 1: continue
				obj.MoveTo(worldPos)

		if button == 3:
			bestUuid, bestDist = self.ObjNearPos(worldPos, 1)
			print bestUuid, bestDist

			if bestDist < 5.:
				for objId in self.objs:
					obj = self.objs[objId]
					if obj.player != 1: continue
					obj.Attack(bestUuid)

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

	eventMediator = events.EventMediator()

	gameObjects = GameObjects(eventMediator)
	player = Person(eventMediator)
	player.player = 1
	player.faction = 1
	gameObjects.Add(player)
	enemy = Person(eventMediator)
	enemy.faction = 2
	enemy.pos = np.array((20., 10.))
	gameObjects.Add(enemy)

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

				gameObjects.WorldClick((clickWorld[0], clickWorld[1]), event.button)

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
		
		gameObjects.Update(time_passed_seconds)

		# Clear the screen, and z-buffer
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
						
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

