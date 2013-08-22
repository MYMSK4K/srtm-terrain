
import events, random

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
		mediator.AddListener("addplayer", self)
	
		self.enemyId = None

	def ProcessEvent(self, event):
		print event.type

		if event.type == "gamestart":

			event = events.Event("addunit")
			event.pos = (20., 10.)
			event.faction = 2
			self.enemyId = self.mediator.Send(event)[0]

			au = events.Event("setmission")
			au.text = "Destroy unit at "+str(event.pos)
			self.mediator.Send(au)

			event = events.Event("addarea")
			event.pos = (-15., 20.)
			self.mediator.Send(event)

		if event.type == "targetdestroyed":
			if self.enemyId == event.objId:
				au = events.Event("addunit")
				au.pos = (random.random() * 30. - 15., random.random() * 30. - 15.)
				au.faction = 2
				self.enemyId = self.mediator.Send(au)[0]

				au2 = events.Event("setmission")
				au2.text = "Destroy unit at "+str(au.pos)
				self.mediator.Send(au2)

