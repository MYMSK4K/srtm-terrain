
import events

class Gui(events.EventCallback):
	def __init__(self, mediator):
		super(Gui, self).__init__(mediator)
		mediator.AddListener("mousebuttondown", self)
		mediator.AddListener("mousebuttonup", self)
		mediator.AddListener("mousemotion", self)
		self.playerId = None
		self.faction = None

	def ProcessEvent(self, event):
		#print event.type
		if event.type == "mousebuttondown":
			if event.button == 1:
				moveOrder = events.Event("moveorder")
				moveOrder.pos = (event.worldPos[0], event.worldPos[1], 0.)
				moveOrder.playerId = self.playerId
				self.mediator.Send(moveOrder)

			if event.button == 3:
				getNearby = events.Event("getNearbyUnits")
				getNearby.pos = event.worldPos
				getNearby.proj = event.proj
				getNearby.notFaction = self.faction
				nearbyRet = self.mediator.Send(getNearby)
				bestUuid, bestDist = None, None
				for ret in nearbyRet:
					if ret is None: continue
					assert len(ret) == 2
					bestUuid, bestDist = ret
				if bestUuid is None: return

				attackOrder = events.Event("attackorder")
				attackOrder.targetId = bestUuid
				attackOrder.playerId = self.playerId
				self.mediator.Send(attackOrder)

		if event.type == "mousebuttonup":
			print event.type

