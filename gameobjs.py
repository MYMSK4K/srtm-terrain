
import uuid, math, events
import numpy as np
import OpenGL.GL as GL

### Person

class GameObj(object):
	def __init__(self, mediator):
		self.mediator = mediator
		self.objId = uuid.uuid4()
		self.playerId = None
		self.faction = 0
		self.pos = np.array((0., 0., 0.))

	def Draw(self, proj):
		pass

	def Update(self, timeElapsed, timeNow, proj):
		pass

	def GetHealth(self):
		return None

	def CollidesWithPoint(self, pos, proj):
		return False

	def GetAttackTarget(self):
		return None

	def MoveTo(self, pos):
		pass

	def Attack(self, uuid):
		pass

	def SetPos(self, posIn):
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

	def Draw(self, proj):
		if self.faction == 0:
			GL.glColor3f(1., 0., 0.)
		if self.faction == 1:
			GL.glColor3f(0., 1., 0.)
		if self.faction == 2:
			GL.glColor3f(0., 0., 1.)
		if self.health == 0.:
			GL.glColor3f(0.3, 0.3, 0.3)

		glRadius = proj.ScaleDistance(self.radius)
		GL.glPushMatrix()

		proj.TransformToLocalCoords(self.pos[0], self.pos[1], 0.)
		
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

	def MoveTo(self, pos):
		self.moveOrder = np.array(pos)
		self.attackOrder = None

	def Attack(self, uuid):
		self.attackOrder = uuid
		self.moveOrder = None

	def Update(self, timeElapsed, timeNow, proj):
		
		moveTowards = self.moveOrder

		if moveTowards is not None:
			dirMag = proj.DistanceBetween(self.pos[0], self.pos[1], self.pos[2], 
				moveTowards[0], moveTowards[1], moveTowards[2])

		if self.attackOrder is not None:
			event = events.Event("getpos")
			event.objId = self.attackOrder
			getEnemyPosRet = self.mediator.Send(event)
			getEnemyPos = getEnemyPosRet[0]
			dirMag = proj.DistanceBetween(self.pos[0], self.pos[1], self.pos[2], 
				getEnemyPos[0], getEnemyPos[1], getEnemyPos[2])

			if dirMag > self.attackRange * 0.95:
				moveTowards = getEnemyPos

		if moveTowards is not None:
			if dirMag < timeElapsed * self.speed:
				self.SetPos(self.moveOrder.copy())
				self.moveOrder = None
			else:
				self.SetPos(proj.OffsetTowardsPoint(self.pos, moveTowards, self.speed * timeElapsed))

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

	def CollidesWithPoint(self, pos, proj):
		assert len(self.pos) == 3
		dist = proj.DistanceBetween(pos[0], pos[1], pos[2], 
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

	def Draw(self, proj):

		glRadius = proj.ScaleDistance(self.radius)
		GL.glPushMatrix()
		proj.TransformToLocalCoords(self.pos[0], self.pos[1], 0.)
		GL.glColor3f(0.5, 0.5, 0.5)

		GL.glBegin(GL.GL_POLYGON)
		for i in range(10):
			GL.glVertex3f(glRadius * math.sin(i * 2. * math.pi / 10.), glRadius * math.cos(i * 2. * math.pi / 10.), 0.)
		GL.glEnd()

		GL.glPopMatrix()

	def Update(self, timeElapsed, timeNow, proj):
		dirMag = proj.DistanceBetween(self.pos[0], self.pos[1], self.pos[2], 
			self.targetPos[0], self.targetPos[1], self.targetPos[2])

		if dirMag < timeElapsed * self.speed:
			self.SetPos(self.targetPos.copy())
			detonateEvent = events.Event("detonate")
			detonateEvent.pos = self.pos.copy()
			detonateEvent.objId = self.objId
			detonateEvent.firerId = self.firerId
			detonateEvent.playerId = self.playerId
			detonateEvent.proj = proj
			self.mediator.Send(detonateEvent)
		else:
			self.SetPos(proj.OffsetTowardsPoint(self.pos, self.targetPos, self.speed * timeElapsed))

	def GetHealth(self):
		return 1.

class AreaObjective(GameObj):
	def __init__(self, mediator):
		super(AreaObjective, self).__init__(mediator)
		self.radius = 10.

	def Draw(self, proj):
		glRadius = proj.ScaleDistance(self.radius)

		if self.faction == 0:
			GL.glColor3f(1., 0., 0.)
		if self.faction == 1:
			GL.glColor3f(0., 1., 0.)
		if self.faction == 2:
			GL.glColor3f(0., 0., 1.)

		GL.glPushMatrix()
		proj.TransformToLocalCoords(self.pos[0], self.pos[1], 0.)

		GL.glBegin(GL.GL_LINE_LOOP)
		for i in range(50):
			GL.glVertex3f(glRadius * math.sin(i * 2. * math.pi / 50.), glRadius * math.cos(i * 2. * math.pi / 50.), 0.)
		GL.glEnd()

		GL.glPopMatrix()

	def Update(self, timeElapsed, timeNow, proj):
		pass

	def CollidesWithPoint(self, pos, proj):
		dist = proj.DistanceBetween(pos[0], pos[1], pos[2], 
			self.pos[0], self.pos[1], self.pos[2])
		return dist < self.radius

