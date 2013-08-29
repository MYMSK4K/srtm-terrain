
import events, time, projfunc
import math
import numpy as np

class PhysicsBody():
	def __init__(self):
		self.pos = np.array((0., 0., 0.))
		self.velocity = np.array((0., 0., 0.))
		self.targetPos = None
		self.accel = 0.01
		self.maxSpeed = 0.003
		self.mass = 1.
		self.radius = 0.001

class Physics(events.EventCallback):
	def __init__(self, mediator):
		super(Physics, self).__init__(mediator)

		mediator.AddListener("physicscreateperson", self)
		mediator.AddListener("physicssetpos", self)
		mediator.AddListener("physicssettargetpos", self)

		self.proj = None
		self.planetCentre = None
		self.reportedPos = {}

		self.objs = {}
		self.prevSpeed = {}

	def AddPlanet(self):
		self.planetRadius = self.proj.radius
		self.planetCentre = np.array(self.proj.Proj(0., 0., self.proj.UnscaleDistance(-self.proj.radius)))

	def AddSphere(self, pos, objId):
		body = PhysicsBody()
		body.pos = np.array(pos)
		self.objs[objId] = body

	def Update(self, timeElapsed, timeNow):

		movedObjs = set()
		currentForces = {}
		contacts = {}

		#Add motor forces
		for objId in self.objs:
			body = self.objs[objId]
			if body.targetPos is None: continue
			
			#Direction towards target
			targetVec = body.targetPos - body.pos
			dist = np.linalg.norm(targetVec, ord=2)
			targetVecNorm = targetVec.copy()
			if dist > 0.:
				targetVecNorm /= dist

			#Normalise velocity to get direction
			velVec = body.velocity
			speed = np.linalg.norm(velVec, ord=2)
			velVecNorm = velVec.copy()
			if speed > 0.:
				velVecNorm /= speed

			#Check if we are close enough to round to target pos
			distTol = body.accel * timeElapsed ** 2. / 2.
			speedTol = body.accel * timeElapsed
			if dist < distTol and speed < speedTol:
				body.velocity *= 0.
				body.pos = body.targetPos.copy()
				continue

			#Check if approaching target
			veldot = np.dot(velVec, targetVecNorm)
			approaching = (veldot >= 0.)
			speedTowardTarg = np.dot(velVec, targetVecNorm)			

			if approaching:
				#Check if braking is needed
				idealSpeedToward = (2. * dist * body.accel) ** 0.5
				safetyMargin = 0.95

				if speedTowardTarg >= idealSpeedToward * safetyMargin:
					braking = True
				else:
					braking = False
			else:
				braking = False

			#Calculate force to reduce missing the target
			offTargetVel = velVec - speedTowardTarg * targetVec
			offTargetVelMag = np.linalg.norm(offTargetVel, ord=2)
			offTargetVelNorm = offTargetVel.copy()
			if offTargetVelMag > 0.:
				offTargetVelNorm /= offTargetVelMag
			offTargetAccelReq = - offTargetVelNorm

			if braking:
				#Braking is required
				idealDecelMag = (speedTowardTarg ** 2.) / (2. * dist)
				idealAccel = 0.9 * offTargetAccelReq - targetVecNorm * idealDecelMag
			else:
				if speed <= body.maxSpeed:
					#Mix acceleration towards with anti-drift
					idealAccel = (0.9 * offTargetAccelReq + targetVecNorm) * body.accel
				else:
					idealAccel = offTargetAccelReq
			
			#Limit acceleration
			idealAccelMag = np.linalg.norm(idealAccel, ord=2)
			idealAccelScaled = idealAccel.copy()
			if idealAccelMag > body.accel:
				idealAccelScaled /= idealAccelMag
				idealAccelScaled *= body.accel

			currentForces[objId] = idealAccelScaled * body.mass

		#Add collisions
		for i, objId1 in enumerate(self.objs):
			for j, objId2 in enumerate(self.objs):
				if j <= i: continue #Cannot self collide
				obj1 = self.objs[objId1]
				obj2 = self.objs[objId2]

				sepVec = obj2.pos - obj1.pos
				dist = np.linalg.norm(sepVec, ord=2)
				penetrDist = obj1.radius + obj2.radius - dist
				if penetrDist >= 0.:
					sepVecNorm = sepVec.copy()
					sepVecNorm /= dist
					
					#Remove velocity component in contact
					#approachSpeed1 = np.dot(sepVecNorm, obj1.velocity)
					#approachSpeed2 = np.dot(-sepVecNorm, obj2.velocity)			

					#if approachSpeed1 > 0.:
					#	obj1.velocity -= approachSpeed1 * sepVecNorm
					#if approachSpeed2 > 0.:
					#	obj2.velocity -= approachSpeed2 * sepVecNorm
		
					#Apply separation force
					if objId1 not in currentForces: currentForces[objId1] = np.array((0.,0.,0.))
					if objId2 not in currentForces: currentForces[objId2] = np.array((0.,0.,0.))
					obj1Forces = currentForces[objId1]
					obj2Forces = currentForces[objId2]

					forceTowards1 = np.dot(sepVecNorm, obj1Forces)
					forceTowards2 = np.dot(sepVecNorm, obj2Forces)
					
					#Newton's 3rd law
					currentForces[objId1] -= forceTowards1 * sepVecNorm
					currentForces[objId2] += forceTowards1 * sepVecNorm
					currentForces[objId1] -= forceTowards2 * sepVecNorm
					currentForces[objId2] += forceTowards2 * sepVecNorm
					
					#Move objects apart
					obj1.pos -= 0.5 * penetrDist * sepVecNorm
					obj2.pos += 0.5 * penetrDist * sepVecNorm

				movedObjs.add(objId1)
				movedObjs.add(objId2)

		#Move objects to terrain surface
		for objId in self.objs:
			body = self.objs[objId]
			upVec = body.pos - self.planetCentre
			distFromPlanetCentre = np.linalg.norm(upVec, ord=2)
			gndAlt = distFromPlanetCentre - self.planetRadius
			upVecNorm = upVec.copy()
			if distFromPlanetCentre > 0.:
				upVecNorm /= distFromPlanetCentre

			body.pos -= upVecNorm * gndAlt

		#Add friction
		for objId in self.objs:
			body = self.objs[objId]
			speed = np.linalg.norm(body.velocity, ord=2)
			velDirNorm = body.velocity.copy()
			if speed > 0.:
				velDirNorm /= speed

				if objId not in currentForces: currentForces[objId] = np.array((0.,0.,0.))
				currentForces[objId] -= body.velocity * 0.5

		#Update velocity and position
		for objId in self.objs:
			body = self.objs[objId]
			if objId in currentForces: #Newton's first law
				bodyForces = currentForces[objId]
				body.velocity += timeElapsed * bodyForces / body.mass #Newton's second law

			body.pos += body.velocity * timeElapsed

			if np.linalg.norm(body.velocity, ord=2) > 0.:
				movedObjs.add(objId)

		#Generate events for anything moving
		for objId in movedObjs:
			body = self.objs[objId]

			posUpdateEv = events.Event("physicsposupdate")
			posUpdateEv.pos = body.pos
			posUpdateEv.objId = objId
			self.mediator.Send(posUpdateEv)

	def ProcessEvent(self, event):
		if event.type == "physicscreateperson":
			self.AddSphere(self.proj.ProjDeg(0.,0.,0.), event.objId)
			return

		if event.type == "physicssetpos":
			#print event.type, event.pos
			obj = self.objs[event.objId]
			obj.pos = np.array(event.pos).copy()
			return

		if event.type == "physicssettargetpos":
			obj = self.objs[event.objId]
			obj.targetPos = np.array(event.pos).copy()
			return

		print event.type

if __name__ == "__main__":
	p = Physics(None)
	p.proj = projfunc.ProjFunc()
	p.AddPlanet()

	while(1):
		p.Update(0.01,0.)
		time.sleep(0.01)


