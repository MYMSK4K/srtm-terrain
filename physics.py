
import events, time
import ode, uuid

class Physics(events.EventCallback):
	def __init__(self, mediator):
		super(Physics, self).__init__(mediator)

		self.world = ode.World()
		self.world.setGravity( (0,-9.81,0) )
		self.world.setERP(0.8)
		self.world.setCFM(1E-5)

		# Create a space object
		self.space = ode.Space()

		self.objs = {}

		# A joint group for the contact joints that are generated whenever
		# two bodies collide
		self.contactgroup = ode.JointGroup()

		# Create a plane geom which prevent the objects from falling forever
		self.floor = ode.GeomPlane(self.space, (0,1,0), 0)

	def AddSphere(self, pos):

		bodyId = uuid.uuid4()
		radius = 1.
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

		# Detect collisions and create contact joints
		self.space.collide(self, self.NearCallback)

		# Simulation step
		self.world.step(timeElapsed)

		# Remove all contact joints
		self.contactgroup.empty()

		for obj in self.objs:
			print timeElapsed, self.objs[obj][0].getPosition()

		if len(self.objs)==0:
			self.AddSphere((0.,2.,0.))

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

	while(1):
		p.Update(0.01,0.)
		time.sleep(0.01)


