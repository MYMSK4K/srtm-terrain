
import events, time, projfunc
import ode, uuid
import numpy as np

class Physics(events.EventCallback):
	def __init__(self, mediator):
		super(Physics, self).__init__(mediator)

		self.proj = None
		self.planetCentre = None

		self.world = ode.World()
		#self.world.setGravity( (0,-9.81,0) )
		self.world.setERP(0.8)
		self.world.setCFM(1E-5)

		# Create a space object
		self.space = ode.Space()

		self.objs = {}

		# A joint group for the contact joints that are generated whenever
		# two bodies collide
		self.contactgroup = ode.JointGroup()

		# Create a plane geom which prevent the objects from falling forever
		#self.floor = ode.GeomPlane(self.space, (0,1,0), 0)

	def AddPlanet(self):
		self.planetCentre = np.array(self.proj.Proj(0., 0., self.proj.UnscaleDistance(-self.proj.radius)))
		self.planet = ode.GeomSphere(self.space, self.proj.radius)
		self.planet.setPosition(self.planetCentre)

	def AddSphere(self, pos):

		bodyId = uuid.uuid4()
		radius = 0.001
		density = 1.

		# Create body
		body = ode.Body(self.world)
		M = ode.Mass()
		M.setSphere(density, radius)
		body.setMass(M)
		body.setPosition(pos)

		# Create a box geom for collision detection
		geom = ode.GeomSphere(self.space, radius)
		geom.setBody(body)

		self.objs[bodyId] = (body, geom)

		return bodyId

	def Update(self, timeElapsed, timeNow):

		# Calculate gravity
		for objId in self.objs:
			body, geom = self.objs[objId]
			pos = body.getPosition()
			
			vecFromCentre = self.planetCentre - pos
			dist = np.linalg.norm(vecFromCentre, ord=2)
			if dist > 0.:
				vecFromCentre /= dist

			body.addForce(vecFromCentre * body.getMass().mass * 0.00981)

		# Detect collisions and create contact joints
		self.space.collide(self, self.NearCallback)

		# Simulation step
		self.world.step(timeElapsed)

		# Remove all contact joints
		self.contactgroup.empty()

		for i, obj in enumerate(self.objs):
			print i, timeElapsed, self.objs[obj][0].getPosition()

		if len(self.objs)==0:
			pos = self.proj.ProjDeg(54., 27., 2.)
			self.AddSphere(pos)

			vecFromCentre = self.planetCentre - pos
			dist = np.linalg.norm(vecFromCentre, ord=2)

	def NearCallback(self, args, geom1, geom2):
		# Check if the objaects do collide
		contacts = ode.collide(geom1, geom2)

		# Create contact joints
		for c in contacts:
			c.setBounce(0.2)
			c.setMu(5000)
			j = ode.ContactJoint(self.world, self.contactgroup, c)
			j.attach(geom1.getBody(), geom2.getBody())


if __name__ == "__main__":
	p = Physics(None)
	p.proj = projfunc.ProjFunc()
	p.AddPlanet()

	while(1):
		p.Update(0.01,0.)
		time.sleep(0.01)


