
import events

class Gui(events.EventCallback):
	def __init__(self, mediator):
		super(Gui, self).__init__(mediator)
		mediator.AddListener("mousebuttondown", self)
		mediator.AddListener("mousebuttonup", self)
		mediator.AddListener("mousemotion", self)
		mediator.AddListener("mousedowntimeout", self)
		self.playerId = None
		self.faction = None
		self.mousePressEvents = {}
		#self.multiClickDriftTol = 5. #px
		self.multiClickTimeout = .2 #sec

	def ProcessEvent(self, ev):
		#print event.type
		if ev.type == "mousebuttondown":
			if ev.button not in self.mousePressEvents:
				self.mousePressEvents[ev.button] = []
			self.mousePressEvents[ev.button].append(ev)
			
			timeOutEvent = events.Event("mousedowntimeout")
			timeOutEvent.button = ev.button
			timeOutEvent.triggerTime = ev.time
			timeOutEvent.deliverAtTime = self.multiClickTimeout + ev.time
			self.mediator.Send(timeOutEvent)

		if ev.type == "mousedowntimeout":
			
			#Check if later clicks will be performing the time out
			prevClick = self.mousePressEvents[ev.button][-1]
			if ev.triggerTime != prevClick.time:
				return

			#Dispatch clicks
			if ev.button == 1 and len(self.mousePressEvents[ev.button])==1:
				self.SingleLeftClick(prevClick.screenPos, prevClick.worldPos)

			if ev.button == 3 and len(self.mousePressEvents[ev.button])==1:
				self.SingleRightClick(prevClick.screenPos, prevClick.worldPos)

			#Clear click time log
			self.mousePressEvents[ev.button] = []

		if ev.type == "mousebuttonup":
			print ev.type
	
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
		if bestDist > 5.: return

		attackOrder = events.Event("attackorder")
		attackOrder.targetId = bestUuid
		attackOrder.playerId = self.playerId
		self.mediator.Send(attackOrder)

