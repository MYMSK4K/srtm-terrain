
import events, random, uuid

class Script(events.EventCallback):
	def __init__(self, mediator):
		super(Script, self).__init__(mediator)

		mediator.AddListener("gamestart", self)
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
	
		self.enemyId = None
		self.enemyFaction = uuid.uuid4()
		self.friendlyFaction = uuid.uuid4()

	def ProcessEvent(self, event):
		print event.type

		if event.type == "gamestart":

			#Add friendlies
			addFaction = events.Event("addfactioncolour")
			addFaction.faction = self.friendlyFaction
			addFaction.colour = (1., 0., 0.)
			self.mediator.Send(addFaction)

			event = events.Event("addunit")
			event.faction = self.friendlyFaction
			event.pos = (53.93015, 27.37785, 0.)
			self.mediator.Send(event)[0]

			event = events.Event("addunit")
			event.faction = self.friendlyFaction
			event.pos = (53.93015+0.0001, 27.37785+0.00005, 0.)
			self.mediator.Send(event)[0]

			#Add enemies
			addFaction = events.Event("addfactioncolour")
			addFaction.faction = self.enemyFaction
			addFaction.colour = (0., 0., 1.)
			self.mediator.Send(addFaction)

			event = events.Event("addunit")
			event.pos = (53.93025, 27.3777)
			event.faction = self.enemyFaction
			self.enemyId = self.mediator.Send(event)[0]

			au = events.Event("setmission")
			au.text = "Destroy unit at "+str(event.pos)
			self.mediator.Send(au)

			event = events.Event("addarea")
			event.pos = (53.930185, 27.3782)
			self.mediator.Send(event)

		if event.type == "targetdestroyed":
			print "by playerId", event.playerId
			if self.enemyId == event.objId:
				au = events.Event("addunit")
				au.pos = (random.random() * 30. - 15., random.random() * 30. - 15.)
				au.faction = self.enemyFaction
				self.enemyId = self.mediator.Send(au)[0]

				au2 = events.Event("setmission")
				au2.text = "Destroy unit at "+str(au.pos)
				self.mediator.Send(au2)

