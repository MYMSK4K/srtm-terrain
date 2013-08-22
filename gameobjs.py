
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
		self.pos = np.array((0., 0.))

	def Draw(self):
		pass

	def Update(self, timeElapsed, timeNow):
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
			GL.glColor3f(1., 0., 0.)
		if self.faction == 1:
			GL.glColor3f(0., 1., 0.)
		if self.faction == 2:
			GL.glColor3f(0., 0., 1.)
		if self.health == 0.:
			GL.glColor3f(0.3, 0.3, 0.3)

		GL.glPushMatrix()
		GL.glTranslatef(self.pos[0], self.pos[1], 0.)
		
		GL.glBegin(GL.GL_POLYGON)
		for i in range(10):
			GL.glVertex3f(self.radius * math.sin(i * 2. * math.pi / 10.), self.radius * math.cos(i * 2. * math.pi / 10.), 0.)
		GL.glEnd()

		GL.glColor3f(0., 0., 0.)
		GL.glBegin(GL.GL_POLYGON)
		GL.glVertex3f(self.radius * math.sin(self.heading), self.radius * math.cos(self.heading), 0.)
		GL.glVertex3f(0.1 * self.radius * math.sin(self.heading + math.pi / 2), 0.1 * self.radius * math.cos(self.heading + math.pi / 2), 0.)
		GL.glVertex3f(0.1 * self.radius * math.sin(self.heading - math.pi / 2), 0.1 * self.radius * math.cos(self.heading - math.pi / 2), 0.)
		GL.glEnd()

		GL.glPopMatrix()

	def MoveTo(self, pos):
		self.moveOrder = np.array(pos)
		self.attackOrder = None

	def Attack(self, uuid):
		self.attackOrder = uuid
		self.moveOrder = None

	def Update(self, timeElapsed, timeNow):
		
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
		GL.glPushMatrix()
		GL.glTranslatef(self.pos[0], self.pos[1], 0.)
		GL.glColor3f(0.5, 0.5, 0.5)

		GL.glBegin(GL.GL_POLYGON)
		for i in range(10):
			GL.glVertex3f(self.radius * math.sin(i * 2. * math.pi / 10.), self.radius * math.cos(i * 2. * math.pi / 10.), 0.)
		GL.glEnd()

		GL.glPopMatrix()

	def Update(self, timeElapsed, timeNow):
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
			GL.glColor3f(1., 0., 0.)
		if self.faction == 1:
			GL.glColor3f(0., 1., 0.)
		if self.faction == 2:
			GL.glColor3f(0., 0., 1.)

		GL.glPushMatrix()
		GL.glTranslatef(self.pos[0], self.pos[1], 0.)

		GL.glBegin(GL.GL_LINE_LOOP)
		for i in range(50):
			GL.glVertex3f(self.radius * math.sin(i * 2. * math.pi / 50.), self.radius * math.cos(i * 2. * math.pi / 50.), 0.)
		GL.glEnd()

		GL.glPopMatrix()

	def Update(self, timeElapsed, timeNow):
		pass

	def CollidesWithPoint(self, pos):
		direction = np.array(pos) - self.pos
		dist = np.linalg.norm(direction, ord=2)
		return dist < self.radius

