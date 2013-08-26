
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
				self.SingleLeftClick(event.screenPos, event.worldPos)

			if event.button == 3:
				self.SingleRightClick(event.screenPos, event.worldPos)

		if event.type == "mousebuttonup":
			print event.type
	
	def SingleLeftClick(self, screenPos, worldPos):
		moveOrder = events.Event("moveorder")
		moveOrder.pos = (worldPos[0], worldPos[1], 0.)
		moveOrder.playerId = self.playerId
		self.mediator.Send(moveOrder)

	def SingleRightClick(self, screenPos, worldPos):
		getNearby = events.Event("getNearbyUnits")
		getNearby.pos = worldPos
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

