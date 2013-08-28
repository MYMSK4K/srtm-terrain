
import uuid, math, events
import numpy as np
import OpenGL.GL as GL

### Person

class GameObj(object):
	def __init__(self, mediator):
		self.mediator = mediator
		self.objId = uuid.uuid4()
		self.playerId = None
		self.faction = None
		self.pos = np.array((0., 0., 0.))

	def Draw(self, objmgr):
		pass

	def Update(self, timeElapsed, timeNow, objmgr):
		pass

	def GetHealth(self):
		return None

	def CollidesWithPoint(self, pos, objmgr):
		return False

	def GetAttackTarget(self):
		return None

	def MoveTo(self, pos, proj):
		pass

	def Attack(self, uuid):
		pass

	def SetPos(self, posIn, proj):
		assert(len(posIn)==3)
		self.pos = np.array(posIn)

	def UpdatePos(self, posIn):
		assert(len(posIn)==3)
		self.pos = np.array(posIn)

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

		createBodyEv = events.Event("physicscreateperson")
		createBodyEv.objId = self.objId
		mediator.Send(createBodyEv)

	def SetPos(self, posIn, proj):
		assert(len(posIn)==3)
		self.pos = np.array(posIn)

		setPosEv = events.Event("physicssetpos")
		setPosEv.objId = self.objId
		setPosEv.pos = proj.ProjDeg(*posIn)
		self.mediator.Send(setPosEv)

	def Draw(self, objmgr):

		if self.health > 0.:
			if self.faction in objmgr.factionColours:
				GL.glColor3f(*objmgr.factionColours[self.faction])
			else:
				GL.glColor3f(1., 1., 1.)
		else:
			GL.glColor3f(0.2, 0.2, 0.2)

		glRadius = objmgr.proj.ScaleDistance(self.radius)
		GL.glPushMatrix()

		objmgr.proj.TransformToLocalCoords(self.pos[0], self.pos[1], 0.)
		
		GL.glBegin(GL.GL_POLYGON)
		for i in range(10):
			GL.glVertex3f(glRadius * math.sin(i * 2. * math.pi / 10.), glRadius * math.cos(i * 2. * math.pi / 10.), 0.)
		GL.glEnd()

		GL.glColor3f(0., 0., 0.)
		GL.glBegin(GL.GL_POLYGON)
		GL.glVertex3f(glRadius * math.sin(self.heading), glRadius * math.cos(self.heading), 0.)
		GL.glVertex3f(0.1 * glRadius * math.sin(self.heading + math.pi / 2), 0.1 * glRadius * math.cos(self.heading + math.pi / 2), 0.)
		GL.glVertex3f(0.1 * glRadius * math.sin(self.heading - math.pi / 2), 0.1 * glRadius * math.cos(self.heading - math.pi / 2), 0.)
		GL.glEnd()

		GL.glPopMatrix()

	def MoveTo(self, pos, proj):
		self.moveOrder = np.array(pos)
		self.attackOrder = None
		posEv = events.Event("physicssettargetpos")
		posEv.pos = proj.ProjDeg(*pos)
		posEv.objId = self.objId
		self.mediator.Send(posEv)

	def Attack(self, uuid):
		self.attackOrder = uuid
		self.moveOrder = None

	def Update(self, timeElapsed, timeNow, objmgr):
		
		moveTowards = self.moveOrder

		if moveTowards is not None:
			dirMag = objmgr.proj.DistanceBetween(self.pos[0], self.pos[1], self.pos[2], 
				moveTowards[0], moveTowards[1], moveTowards[2])

		if self.attackOrder is not None:
			event = events.Event("getpos")
			event.objId = self.attackOrder
			getEnemyPosRet = self.mediator.Send(event)
			getEnemyPos = getEnemyPosRet[0]
			dirMag = objmgr.proj.DistanceBetween(self.pos[0], self.pos[1], self.pos[2], 
				getEnemyPos[0], getEnemyPos[1], getEnemyPos[2])

			if dirMag > self.attackRange * 0.95:
				moveTowards = getEnemyPos

		if moveTowards is not None:
			pass

		if self.attackOrder is not None:			
			if dirMag <= self.attackRange:
				#Check if we can fire
				durationSinceFiring = None
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
					fireEvent.speed = 10.
					self.mediator.Send(fireEvent)

	def CollidesWithPoint(self, pos, objmgr):
		assert len(self.pos) == 3
		dist = objmgr.proj.DistanceBetween(pos[0], pos[1], pos[2], 
			self.pos[0], self.pos[1], self.pos[2])
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
		self.speed = 10.
		self.radius = 0.05
		self.mediator = mediator
		self.attackOrder = None

	def Draw(self, objmgr):

		glRadius = objmgr.proj.ScaleDistance(self.radius)
		GL.glPushMatrix()
		objmgr.proj.TransformToLocalCoords(self.pos[0], self.pos[1], 0.)
		GL.glColor3f(0.5, 0.5, 0.5)

		GL.glBegin(GL.GL_POLYGON)
		for i in range(10):
			GL.glVertex3f(glRadius * math.sin(i * 2. * math.pi / 10.), glRadius * math.cos(i * 2. * math.pi / 10.), 0.)
		GL.glEnd()

		GL.glPopMatrix()

	def Update(self, timeElapsed, timeNow, objmgr):
		dirMag = objmgr.proj.DistanceBetween(self.pos[0], self.pos[1], self.pos[2], 
			self.targetPos[0], self.targetPos[1], self.targetPos[2])

		if dirMag < timeElapsed * self.speed:
			self.SetPos(self.targetPos.copy(), objmgr.proj)
			detonateEvent = events.Event("detonate")
			detonateEvent.pos = self.pos.copy()
			detonateEvent.objId = self.objId
			detonateEvent.firerId = self.firerId
			detonateEvent.playerId = self.playerId
			detonateEvent.proj = objmgr.proj
			self.mediator.Send(detonateEvent)
		else:
			newPos = objmgr.proj.OffsetTowardsPoint(self.pos, self.targetPos, self.speed * timeElapsed)
			newPos[2] = 0. #Fix items to surface of world
			self.SetPos(newPos, objmgr.proj)

	def GetHealth(self):
		return 1.

class AreaObjective(GameObj):
	def __init__(self, mediator):
		super(AreaObjective, self).__init__(mediator)
		self.radius = 10.

	def Draw(self, objmgr):
		glRadius = objmgr.proj.ScaleDistance(self.radius)

		if self.faction in objmgr.factionColours:
			GL.glColor3f(*objmgr.factionColours[self.faction])
		else:
			GL.glColor3f(1., 1., 1.)

		GL.glPushMatrix()
		objmgr.proj.TransformToLocalCoords(self.pos[0], self.pos[1], 0.)

		GL.glBegin(GL.GL_LINE_LOOP)
		for i in range(50):
			GL.glVertex3f(glRadius * math.sin(i * 2. * math.pi / 50.), glRadius * math.cos(i * 2. * math.pi / 50.), 0.)
		GL.glEnd()

		GL.glPopMatrix()

	def Update(self, timeElapsed, timeNow, objmgr):
		pass

	def CollidesWithPoint(self, pos, objmgr):
		dist = objmgr.proj.DistanceBetween(pos[0], pos[1], pos[2], 
			self.pos[0], self.pos[1], self.pos[2])
		return dist < self.radius

