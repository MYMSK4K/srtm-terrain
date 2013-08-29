
import events, time, projfunc
import ode, math
import numpy as np

class Physics(events.EventCallback):
	def __init__(self, mediator):
		super(Physics, self).__init__(mediator)

		mediator.AddListener("physicscreateperson", self)
		mediator.AddListener("physicssetpos", self)
		mediator.AddListener("physicssettargetpos", self)

		self.proj = None
		self.planetCentre = None
		self.reportedPos = {}

		self.world = ode.World()
		self.world.setERP(0.8)
		self.world.setCFM(1E-5)

		# Create a space object
		self.space = ode.Space()

		self.objs = {}
		self.prevSpeed = {}

		# A joint group for the contact joints that are generated whenever
		# two bodies collide
		self.contactgroup = ode.JointGroup()

	def AddPlanet(self):
		self.planetCentre = np.array(self.proj.Proj(0., 0., self.proj.UnscaleDistance(-self.proj.radius)))
		self.planet = ode.GeomSphere(self.space, self.proj.radius)
		self.planet.setPosition(self.planetCentre)

	def AddSphere(self, pos, objId):

		radius = 0.001
		density = 1.e9

		# Create body
		body = ode.Body(self.world)
		M = ode.Mass()
		M.setSphere(density, radius)
		body.setMass(M)
		body.setPosition(pos)

		# Create a box geom for collision detection
		geom = ode.GeomSphere(self.space, radius)
		geom.setBody(body)

		self.objs[objId] = [body, geom, None]

		return objId

	def Update(self, timeElapsed, timeNow):

		# Calculate gravity
		for objId in self.objs:
			body, geom, targetPos = self.objs[objId]
			pos = body.getPosition()
			
			vecFromCentre = self.planetCentre - pos
			dist = np.linalg.norm(vecFromCentre, ord=2)
			if dist > 0.:
				vecFromCentre /= dist

			body.addForce(vecFromCentre * body.getMass().mass * 0.00981)

		#Add motor forces
		for objId in self.objs:
			body, geom, targetPos = self.objs[objId]
			if targetPos is None: continue
			pos = body.getPosition()
			
			vec = targetPos - pos
			dist = np.linalg.norm(vec, ord=2)
			if dist > 0.:
				vec /= dist

			vel = body.getLinearVel()
			velMag = np.linalg.norm(vel, ord=2)
			if velMag > 0.:
				vel /= velMag

			accel = 0.008
			calcAccel = 0.005
			idealSpeed = math.pow(2. * calcAccel * dist, 0.5)
			
			if idealSpeed > velMag:
				print "accel", idealSpeed, velMag, timeElapsed
				fo = vec * body.getMass().mass * accel
				body.addForce(fo)
			else:
				print "braking", idealSpeed, velMag, timeElapsed
				fo = -vel * body.getMass().mass * accel
				body.addForce(fo)

			if objId in self.prevSpeed:
				print (velMag - self.prevSpeed[objId]) / timeElapsed

			self.prevSpeed[objId] = velMag

		# Detect collisions and create contact joints
		self.space.collide(self, self.NearCallback)

		# Simulation step
		self.world.step(timeElapsed)

		# Remove all contact joints
		self.contactgroup.empty()

		#FIXME remove unused data in self.prevPosLi?

		# Generate events if object has moved
		for objId in self.objs:
			body, geom, targetPos = self.objs[objId]
			pos = body.getPosition()
			if objId not in self.reportedPos:
				#Position not previously reported
				posUpdateEv = events.Event("physicsposupdate")
				posUpdateEv.pos = pos
				posUpdateEv.objId = objId
				self.mediator.Send(posUpdateEv)

				self.reportedPos[objId] = pos
			else:
				prevPos = self.reportedPos[objId]
				moveDist = np.linalg.norm(np.array(prevPos) - pos, ord=2)

				if moveDist > 0.00001:
					#Position has changed enough to report it
					posUpdateEv = events.Event("physicsposupdate")
					posUpdateEv.pos = pos
					posUpdateEv.objId = objId
					self.mediator.Send(posUpdateEv)

					self.reportedPos[objId] = pos
				
		#for i, obj in enumerate(self.objs):
		#	print i, timeElapsed, self.objs[obj][0].getPosition()

	def NearCallback(self, args, geom1, geom2):
		# Check if the objaects do collide
		contacts = ode.collide(geom1, geom2)

		# Create contact joints
		for c in contacts:
			#pos, normal, depth, geom1, geom2 = c.getContactGeomParams()
			#if depth == 0: continue
			
			c.setBounce(0.2)
			c.setMu(5000)
			j = ode.ContactJoint(self.world, self.contactgroup, c)
			j.attach(geom1.getBody(), geom2.getBody())

	def ProcessEvent(self, event):
		if event.type == "physicscreateperson":
			self.AddSphere(self.proj.ProjDeg(0.,0.,0.), event.objId)
			return

		if event.type == "physicssetpos":
			#print event.type, event.pos
			obj = self.objs[event.objId]
			obj[0].setPosition(event.pos)
			return

		if event.type == "physicssettargetpos":
			obj = self.objs[event.objId]
			obj[2] = np.array(event.pos)
			return

		print event.type

if __name__ == "__main__":
	p = Physics(None)
	p.proj = projfunc.ProjFunc()
	p.AddPlanet()

	while(1):
		p.Update(0.01,0.)
		time.sleep(0.01)


