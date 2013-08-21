
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
		self.health = 1.
		self.radius = 1.

	def Draw(self):
		if self.faction == 0:
			glColor3f(1., 0., 0.)
		if self.faction == 1:
			glColor3f(0., 1., 0.)
		if self.faction == 2:
			glColor3f(0., 0., 1.)
		if self.health == 0.:
			glColor3f(0.3, 0.3, 0.3)

		glPushMatrix()
		glTranslatef(self.pos[0], self.pos[1], 0.)
		
		glBegin(GL_POLYGON)
		for i in range(10):
			glVertex3f(self.radius * math.sin(i * 2. * math.pi / 10.), self.radius * math.cos(i * 2. * math.pi / 10.), 0.)
		glEnd()

		glColor3f(0., 0., 0.)
		glBegin(GL_POLYGON)
		glVertex3f(self.radius * math.sin(self.heading), self.radius * math.cos(self.heading), 0.)
		glVertex3f(0.1 * self.radius * math.sin(self.heading + math.pi / 2), 0.1 * self.radius * math.cos(self.heading + math.pi / 2), 0.)
		glVertex3f(0.1 * self.radius * math.sin(self.heading - math.pi / 2), 0.1 * self.radius * math.cos(self.heading - math.pi / 2), 0.)
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
					fireEvent = events.Event("fireshell")
					fireEvent.targetPos = getEnemyPos.copy()
					fireEvent.targetId = self.attackOrder
					fireEvent.firerId = self.objId
					fireEvent.firerPos = self.pos.copy()
					fireEvent.speed = 100.
					self.mediator.Send(fireEvent)

	def CollidesWithPoint(self, pos):
		direction = np.array(pos) - self.pos
		dist = np.linalg.norm(direction, ord=2)
		return dist < self.radius

class Shell(object):
	def __init__(self, mediator):
		self.pos = np.array((0., 0.))
		self.targetPos = None
		self.targetId = None
		self.firerId = None
		self.firerPos = None
		self.speed = 100.
		self.radius = 0.05
		self.objId = uuid.uuid4()
		self.player = None
		self.health = 1.
		self.mediator = mediator
		self.faction = None
		self.attackOrder = None

	def Draw(self):
		glPushMatrix()
		glTranslatef(self.pos[0], self.pos[1], 0.)
		glColor3f(0.5, 0.5, 0.5)

		glBegin(GL_POLYGON)
		for i in range(10):
			glVertex3f(self.radius * math.sin(i * 2. * math.pi / 10.), self.radius * math.cos(i * 2. * math.pi / 10.), 0.)
		glEnd()

		glPopMatrix()

	def Update(self, timeElapsed):
		direction = np.array(self.targetPos) - np.array(self.pos)
		dirMag = np.linalg.norm(direction, ord=2)
		if dirMag > 0.:
			direction /= dirMag

		if dirMag < timeElapsed * self.speed:
			self.pos = self.targetPos
			detonateEvent = events.Event("detonate")
			detonateEvent.pos = self.pos.copy()
			detonateEvent.objId = self.objId
			detonateEvent.firerId = self.firerId
			self.mediator.Send(detonateEvent)
		else:
			self.pos += direction * timeElapsed * self.speed

	def CollidesWithPoint(self, pos):
		return False

class GameObjects(events.EventCallback):
	def __init__(self, mediator):
		super(GameObjects, self).__init__(mediator)
		mediator.AddListener("getpos", self)
		mediator.AddListener("fireshell", self)
		mediator.AddListener("detonate", self)
		mediator.AddListener("targetdestroyed", self)
		mediator.AddListener("targethit", self)
		mediator.AddListener("shellmiss", self)
		mediator.AddListener("attackorder", self)
		mediator.AddListener("moveorder", self)
		mediator.AddListener("stoporder", self)

		self.objs = {}
		self.newObjs = [] #Add these to main object dict after iteration
		self.objsToRemove = [] #Remove these after current iteration

	def Add(self, obj):
		self.objs[obj.objId] = obj

	def ProcessEvent(self, event):
		if event.type == "getpos":
			if event.objId not in self.objs:
				raise Exception("Unknown object id")
			return self.objs[event.objId].pos

		if event.type == "fireshell":
			print event.type

			shot = Shell(self.mediator)
			shot.targetPos = event.targetPos
			shot.targetId = event.targetId
			shot.firerId = event.firerId
			shot.pos = event.firerPos
			shot.speed = event.speed
			self.newObjs.append(shot)

		if event.type == "detonate":
			print event.type
			self.objsToRemove.append(event.objId)

			#Check if it hit
			hitCount = 0
			for objId in self.objs:
				obj = self.objs[objId]
				hit = obj.CollidesWithPoint(event.pos)

				if hit and obj.health > 0.:
					hitCount += 1
					obj.health -= 0.1

					hitEvent = events.Event("targethit")
					hitEvent.objId = obj.objId
					hitEvent.firerId = event.firerId
					self.mediator.Send(hitEvent)

					if obj.health < 0.: obj.health = 0.
					if obj.health == 0:
						destroyEvent = events.Event("targetdestroyed")
						destroyEvent.objId = obj.objId
						destroyEvent.firerId = event.firerId
						self.mediator.Send(destroyEvent)
			
			if hitCount == 0:
				hitEvent = events.Event("shellmiss")
				hitEvent.firerId = event.firerId
				self.mediator.Send(hitEvent)

		if event.type == "targetdestroyed":
			print event.type

			#Stop attacking targets that are dead
			for objId in self.objs:
				obj = self.objs[objId]
				if obj.attackOrder == event.objId:
					obj.Attack(None)

		if event.type == "targethit":
			print event.type

		if event.type == "shellmiss":
			print event.type

		if event.type == "attackorder":
			print event.type

		if event.type == "moveorder":
			print event.type

		if event.type == "stoporder":
			print event.type

	def Update(self, timeElapsed):
		for objId in self.objs:
			self.objs[objId].Update(timeElapsed)

		#Update list of objects with new items
		for obj in self.newObjs:
			self.objs[obj.objId] = obj
		self.newObjs = []

		#Remove objects that are due to be deleted
		for objId in self.objsToRemove:
			del self.objs[objId]
		self.objsToRemove = []

	def Draw(self):
		for objId in self.objs:
			self.objs[objId].Draw()

	def ObjNearPos(self, pos, notFaction = None):
		bestDist, bestUuid = None, None
		pos = np.array(pos)
		for objId in self.objs:
			obj = self.objs[objId]
			if notFaction is not None and obj.faction == notFaction: continue #Ignore friendlies
			if obj.health == 0.: continue #Ignore dead targets
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

				moveOrder = events.Event("moveorder")
				moveOrder.objId = obj.objId
				moveOrder.pos = worldPos
				self.mediator.Send(moveOrder)

		if button == 3:
			bestUuid, bestDist = self.ObjNearPos(worldPos, 1)
			clickTolerance = 5.

			if bestUuid is not None and bestDist < clickTolerance:
				for objId in self.objs:
					obj = self.objs[objId]
					if obj.player != 1: continue
					obj.Attack(bestUuid)

					if bestUuid is not None:
						attackOrder = events.Event("attackorder")
						attackOrder.attackerId = obj.objId
						attackOrder.targetId = bestUuid
						self.mediator.Send(attackOrder)

			if bestUuid is None or bestDist >= clickTolerance:
				for objId in self.objs:
					obj = self.objs[objId]
					if obj.player != 1: continue
					#Stop attack
					obj.Attack(None)

					stopOrder = events.Event("stoporder")
					stopOrder.objId = obj.objId
					self.mediator.Send(stopOrder)

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

