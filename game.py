
SCREEN_SIZE = (800, 600)

import math, uuid, events, script

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

### Person

class GameObj(object):
	def __init__(self, mediator):
		self.mediator = mediator
		self.objId = uuid.uuid4()
		self.playerId = None
		self.faction = 0
		self.pos = np.array((0., 0.))

	def Draw(self):
		pass

	def Update(self, timeElapsed):
		pass

	def GetHealth(self):
		return None

	def CollidesWithPoint(self, pos):
		return False

	def GetAttackTarget(self):
		return None

	def MoveTo(self, pos):
		pass

	def Attack(self, uuid):
		pass

class Person(GameObj):
	def __init__(self, mediator):
		super(Person, self).__init__(mediator)

		self.heading = 0. #Radians
		self.moveOrder = None
		self.attackOrder = None
		self.speed = 5.
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
					fireEvent.playerId = self.playerId
					fireEvent.firerPos = self.pos.copy()
					fireEvent.speed = 100.
					self.mediator.Send(fireEvent)

	def CollidesWithPoint(self, pos):
		direction = np.array(pos) - self.pos
		dist = np.linalg.norm(direction, ord=2)
		return dist < self.radius

	def GetHealth(self):
		return self.health

	def GetAttackTarget(self):
		return self.attackOrder

class Shell(GameObj):
	def __init__(self, mediator):
		super(Shell, self).__init__(mediator)

		self.targetPos = None
		self.targetId = None
		self.firerId = None
		self.firerPos = None
		self.speed = 100.
		self.radius = 0.05
		self.mediator = mediator
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
			detonateEvent.playerId = self.playerId
			self.mediator.Send(detonateEvent)
		else:
			self.pos += direction * timeElapsed * self.speed

	def GetHealth(self):
		return 1.

class AreaObjective(GameObj):
	def __init__(self, mediator):
		super(AreaObjective, self).__init__(mediator)
		self.radius = 10.

	def Draw(self):

		if self.faction == 0:
			glColor3f(1., 0., 0.)
		if self.faction == 1:
			glColor3f(0., 1., 0.)
		if self.faction == 2:
			glColor3f(0., 0., 1.)

		glPushMatrix()
		glTranslatef(self.pos[0], self.pos[1], 0.)

		glBegin(GL_LINE_LOOP)
		for i in range(50):
			glVertex3f(self.radius * math.sin(i * 2. * math.pi / 50.), self.radius * math.cos(i * 2. * math.pi / 50.), 0.)
		glEnd()

		glPopMatrix()

	def Update(self, timeElapsed):
		pass

	def CollidesWithPoint(self, pos):
		direction = np.array(pos) - self.pos
		dist = np.linalg.norm(direction, ord=2)
		return dist < self.radius

###Object Manager

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
		mediator.AddListener("enterarea", self)
		mediator.AddListener("exitarea", self)
		mediator.AddListener("addunit", self)
		mediator.AddListener("addarea", self)
		mediator.AddListener("setmission", self)

		self.objs = {}
		self.newObjs = [] #Add these to main object dict after iteration
		self.objsToRemove = [] #Remove these after current iteration
		self.areaContents = {}
		self.verbose = 0
		self.playerId = None

	def Add(self, obj):
		self.objs[obj.objId] = obj

	def ProcessEvent(self, event):
		if event.type == "getpos":
			if event.objId not in self.objs:
				raise Exception("Unknown object id")
			return self.objs[event.objId].pos

		if event.type == "fireshell":
			if self.verbose: print event.type

			shot = Shell(self.mediator)
			shot.targetPos = event.targetPos
			shot.targetId = event.targetId
			shot.firerId = event.firerId
			shot.playerId = event.playerId
			shot.pos = event.firerPos
			shot.speed = event.speed
			self.newObjs.append(shot)

		if event.type == "detonate":
			if self.verbose: print event.type
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
						destroyEvent.playerId = event.playerId
						self.mediator.Send(destroyEvent)
			
			if hitCount == 0:
				hitEvent = events.Event("shellmiss")
				hitEvent.firerId = event.firerId
				self.mediator.Send(hitEvent)

		if event.type == "targetdestroyed":
			if self.verbose: print event.type

			#Stop attacking targets that are dead
			for objId in self.objs:
				obj = self.objs[objId]
				if obj.GetAttackTarget() == event.objId:
					obj.Attack(None)

		if event.type == "targethit":
			if self.verbose: print event.type

		if event.type == "shellmiss":
			if self.verbose: print event.type

		if event.type == "attackorder":
			if self.verbose: print event.type

		if event.type == "moveorder":
			if self.verbose: print event.type

		if event.type == "stoporder":
			if self.verbose: print event.type

		if event.type == "enterarea":
			if self.verbose: print event.type

		if event.type == "exitarea":
			if self.verbose: print event.type

		if event.type == "addunit":			
			if self.verbose: print event.type
			enemy = Person(self.mediator)
			enemy.faction = event.faction
			enemy.pos = np.array(event.pos)
			self.newObjs.append(enemy)
			return enemy.objId

		if event.type == "addarea":
			if self.verbose: print event.type
			area = AreaObjective(self.mediator)
			area.pos = np.array(event.pos)
			self.newObjs.append(area)
			return area.objId

		if event.type == "setmission":
			print event.text

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

		#Update list of areas
		areas = set()
		for objId in self.objs:
			obj = self.objs[objId]
			if isinstance(obj, AreaObjective):
				areas.add(objId)
				if objId not in self.areaContents:
					self.areaContents[objId] = []

		#Remove unused areas
		areasToRemove = []
		for areaId in self.areaContents:
			if areaId not in areas:		
				areasToRemove.append(areaId)
		for areaId in areasToRemove:
			del self.areaContents[areaId]

		#Check the contents of areas
		for areaId in self.areaContents:
			area = self.objs[areaId]
			contents = self.areaContents[areaId]
			
			for objId in self.objs:
				obj = self.objs[objId]
				if isinstance(obj, AreaObjective): continue
				contains = area.CollidesWithPoint(obj.pos)
				if contains and objId not in contents:
					areaEvent = events.Event("enterarea")
					areaEvent.objId = objId
					areaEvent.areaId = areaId
					self.mediator.Send(areaEvent)

					contents.append(objId)
					
				if not contains and objId in contents:
					areaEvent = events.Event("exitarea")
					areaEvent.objId = objId
					areaEvent.areaId = areaId
					self.mediator.Send(areaEvent)

					contents.remove(objId)			

	def Draw(self):
		for objId in self.objs:
			self.objs[objId].Draw()

	def ObjNearPos(self, pos, notFaction = None):
		bestDist, bestUuid = None, None
		pos = np.array(pos)
		for objId in self.objs:
			obj = self.objs[objId]
			if notFaction is not None and obj.faction == notFaction: continue #Ignore friendlies
			health = obj.GetHealth()
			if health is None: continue
			if health == 0.: continue #Ignore dead targets
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
				if obj.playerId != self.playerId: continue
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
					if obj.playerId != self.playerId: continue
					obj.Attack(bestUuid)

					if bestUuid is not None:
						attackOrder = events.Event("attackorder")
						attackOrder.attackerId = obj.objId
						attackOrder.targetId = bestUuid
						self.mediator.Send(attackOrder)

			if bestUuid is None or bestDist >= clickTolerance:
				for objId in self.objs:
					obj = self.objs[objId]
					if obj.playerId != self.playerId: continue
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

	scriptObj = script.Script(eventMediator)
	gameObjects = GameObjects(eventMediator)

	player = Person(eventMediator)
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

