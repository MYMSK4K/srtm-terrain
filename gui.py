
import events, math
import OpenGL.GLU as GLU
import numpy as np

class Gui(events.EventCallback):
	def __init__(self, mediator):
		super(Gui, self).__init__(mediator)
		mediator.AddListener("mousebuttondown", self)
		mediator.AddListener("mousebuttonup", self)
		mediator.AddListener("mousemotion", self)
		mediator.AddListener("mousedowntimeout", self)
		self.playerId = None
		self.faction = None
		self.mouseDownEvents = {}
		self.mouseDownStart = {}
		#self.multiClickDriftTol = 5. #px
		self.multiClickTimeout = .2 #sec

	def ProcessEvent(self, ev):
		#print event.type
		if ev.type == "mousebuttondown":
			if ev.button not in self.mouseDownEvents:
				self.mouseDownEvents[ev.button] = []
			self.mouseDownEvents[ev.button].append(ev)

			self.mouseDownStart[ev.button] = ev
			
			timeOutEvent = events.Event("mousedowntimeout")
			timeOutEvent.button = ev.button
			timeOutEvent.triggerTime = ev.time
			timeOutEvent.deliverAtTime = self.multiClickTimeout + ev.time
			self.mediator.Send(timeOutEvent)

		if ev.type == "mousedowntimeout":
			
			#Check if later clicks will be performing the time out
			prevClick = self.mouseDownEvents[ev.button][-1]
			if ev.triggerTime != prevClick.time:
				return

			#Dispatch clicks
			if ev.button == 1 and len(self.mouseDownEvents[ev.button])==1 and self.mouseDownStart[ev.button] is None:
				self.SingleLeftClick(prevClick.screenPos, prevClick.worldPos, prevClick.screenSize, prevClick.proj)

			if ev.button == 3 and len(self.mouseDownEvents[ev.button])==1 and self.mouseDownStart[ev.button] is None:
				self.SingleRightClick(prevClick.screenPos, prevClick.worldPos, prevClick.screenSize, prevClick.proj)

			#Clear click time log
			self.mouseDownEvents[ev.button] = []

		if ev.type == "mousebuttonup":
			print ev.type
			self.mouseDownStart[ev.button] = None

		if ev.type == "mousemotion":
			pressed = False
			for button in self.mouseDownStart:
				if self.mouseDownStart[button] is not None: pressed = True

			if not pressed: return
			#Drag event


	def ClickUnitCheck(self, screenPos, worldPos, proj, screenSize):
		#print "clickScreenPos", screenPos
		#print "at worldPos", worldPos

		#Get unit nearest click position
		getNearby = events.Event("getNearbyUnits")
		getNearby.pos = worldPos
		getNearby.notFaction = None
		nearbyRet = self.mediator.Send(getNearby)
		bestUuid, bestDist = None, None
		for ret in nearbyRet:
			if ret is None: continue
			assert len(ret) == 2
			bestUuid, bestDist = ret
		#print "best unit", bestUuid, bestDist

		#Get position of unit
		screenDist = None
		if bestUuid:
			getPos = events.Event("getpos")
			getPos.objId = bestUuid
			getPosRet = self.mediator.Send(getPos)
			assert len(getPosRet) == 1
			nearestUnitWorldPos = getPosRet[0]

			#print "at worldPos", nearestUnitWorldPos

			#Get cartesian position
			cartPos = proj.Proj(math.radians(nearestUnitWorldPos[0]), math.radians(nearestUnitWorldPos[1]), nearestUnitWorldPos[2])
			#print "cartPos", cartPos

			#Get screen coordinates of nearest unit
			unitScreenPos = GLU.gluProject(*cartPos)
			#print "at screenPos", unitScreenPos
			unitScreenPos2D = np.array((unitScreenPos[0], unitScreenPos[1]))
			glScreenPos = (screenPos[0], screenSize[1] - screenPos[1])
			screenDist = np.linalg.norm(unitScreenPos2D - glScreenPos, ord=2)

		return bestUuid, bestDist, screenDist

			
	def SingleLeftClick(self, screenPos, worldPos, screenSize, proj):

		print self.ClickUnitCheck(screenPos, worldPos, proj, screenSize)

		moveOrder = events.Event("moveorder")
		moveOrder.pos = (worldPos[0], worldPos[1], 0.)
		moveOrder.playerId = self.playerId
		self.mediator.Send(moveOrder)

	def SingleRightClick(self, screenPos, worldPos, screenSize, proj):
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

