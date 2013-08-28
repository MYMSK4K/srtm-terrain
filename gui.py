
import events, math
import OpenGL.GLU as GLU
import OpenGL.GL as GL
import numpy as np

class Gui(events.EventCallback):
	def __init__(self, mediator):
		super(Gui, self).__init__(mediator)
		mediator.AddListener("mousebuttondown", self)
		mediator.AddListener("mousebuttonup", self)
		mediator.AddListener("mousemotion", self)
		mediator.AddListener("mousedowntimeout", self)
		mediator.AddListener("drawselection", self)

		self.playerId = None
		self.faction = None
		self.mouseDownEvents = {}
		self.mouseDownStart = {}
		self.mouseDragBounds = {}
		#self.multiClickDriftTol = 5. #px
		self.multiClickTimeout = .2 #sec
		self.selectTolerance = 30. #px
		self.selection = []

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
			#print ev.type
			self.mouseDownStart[ev.button] = None

			#Detect if this was a valid click and drag
			if ev.button in self.mouseDragBounds:
				selectBox = self.mouseDragBounds[ev.button]
				if selectBox is not None and selectBox[1] is not None:
					dragDist = np.linalg.norm(np.array(selectBox[0].screenPos) - np.array(selectBox[1].screenPos), ord=2)
					if dragDist >= self.selectTolerance:
						self.ClickDragEnd(selectBox[0], selectBox[1])

			self.mouseDragBounds[ev.button] = None

		if ev.type == "mousemotion":
			pressed = False
			for button in self.mouseDownStart:
				if self.mouseDownStart[button] is not None: 
					pressed = True
					self.mouseDragBounds[button] = [self.mouseDownStart[button], ev]

		if ev.type == "drawselection":
			self.DrawSelection(ev.proj)

			self.DrawDragBox(ev.proj)

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
			cartPos = proj.ProjDeg(*nearestUnitWorldPos)
			#print "cartPos", cartPos

			#Get screen coordinates of nearest unit
			unitScreenPos = GLU.gluProject(*cartPos)
			#print "at screenPos", unitScreenPos
			unitScreenPos2D = np.array((unitScreenPos[0], unitScreenPos[1]))
			glScreenPos = (screenPos[0], screenSize[1] - screenPos[1])
			screenDist = np.linalg.norm(unitScreenPos2D - glScreenPos, ord=2)

		return bestUuid, bestDist, screenDist

	def SingleLeftClick(self, screenPos, worldPos, screenSize, proj):

		nearUnitId, nearUnitDistW, nearUnitDistS = self.ClickUnitCheck(screenPos, worldPos, proj, screenSize)

		if nearUnitDistS < self.selectTolerance:
			#Select unit
			self.selection = []
			self.selection.append(nearUnitId)

		else:
			#Order move
			pos, nth, est, up = proj.GetLocalDirectionVecs(*worldPos)
			count = 0

			for obj in self.selection:
				factionReq = events.Event("getfaction") 
				factionReq.objId = obj
				faction = self.mediator.Send(factionReq)[0]
				if faction != self.faction: continue

				offsetDestCart = pos + est * proj.ScaleDistance(5.) * count
				offsetWorld = list(proj.UnProjDeg(*offsetDestCart))
				offsetWorld[2] = 0. #Force to ground level

				moveOrder = events.Event("moveorder")
				moveOrder.pos = offsetWorld
				moveOrder.selection = [obj]
				moveOrder.playerId = self.playerId
				self.mediator.Send(moveOrder)

				count += 1

	def SingleRightClick(self, screenPos, worldPos, screenSize, proj):

		nearUnitId, nearUnitDistW, nearUnitDistS = self.ClickUnitCheck(screenPos, worldPos, proj, screenSize)

		if nearUnitDistS < self.selectTolerance:
			attackOrder = events.Event("attackorder")
			attackOrder.targetId = nearUnitId
			attackOrder.playerId = self.playerId
			playerSpecificSelection = []
			for obj in self.selection:
				factionReq = events.Event("getfaction") 
				factionReq.objId = obj
				if self.mediator.Send(factionReq)[0] != self.faction: continue
				playerSpecificSelection.append(obj)
			attackOrder.selection = playerSpecificSelection
			self.mediator.Send(attackOrder)

	def ClickDragEnd(self, startEv, endEv):
		getReq = events.Event("getUnitsInBbox")
		getReq.pos1 = startEv.worldPos
		getReq.pos2 = endEv.worldPos
		getResult = self.mediator.Send(getReq)
		self.selection = getResult[0]

	def DrawSelection(self, proj):

		for objId in self.selection:
			
			getPos = events.Event("getpos")
			getPos.objId = objId
			getPosRet = self.mediator.Send(getPos)
			assert len(getPosRet) == 1
			unitPos = getPosRet[0]
			
			#print "selection", objId, unitPos

			boxHalfWidth = proj.ScaleDistance(1.5)
			boxTick = proj.ScaleDistance(.3)

			GL.glDisable(GL.GL_DEPTH_TEST)
			GL.glPushMatrix()
			GL.glColor3f(0.1,0.8,0.1)

			proj.TransformToLocalCoords(*unitPos)

			GL.glBegin(GL.GL_LINE_STRIP)
			GL.glVertex(boxHalfWidth-boxTick, boxHalfWidth, 0.)
			GL.glVertex(boxHalfWidth, boxHalfWidth, 0.)
			GL.glVertex(boxHalfWidth, boxHalfWidth-boxTick, 0.)
			GL.glEnd()

			GL.glBegin(GL.GL_LINE_STRIP)
			GL.glVertex(-boxHalfWidth+boxTick, -boxHalfWidth, 0.)
			GL.glVertex(-boxHalfWidth, -boxHalfWidth, 0.)
			GL.glVertex(-boxHalfWidth, -boxHalfWidth+boxTick, 0.)
			GL.glEnd()

			GL.glBegin(GL.GL_LINE_STRIP)
			GL.glVertex(boxHalfWidth-boxTick, -boxHalfWidth, 0.)
			GL.glVertex(boxHalfWidth, -boxHalfWidth, 0.)
			GL.glVertex(boxHalfWidth, -boxHalfWidth+boxTick, 0.)
			GL.glEnd()

			GL.glBegin(GL.GL_LINE_STRIP)
			GL.glVertex(-boxHalfWidth+boxTick, boxHalfWidth, 0.)
			GL.glVertex(-boxHalfWidth, boxHalfWidth, 0.)
			GL.glVertex(-boxHalfWidth, boxHalfWidth-boxTick, 0.)
			GL.glEnd()

			GL.glPopMatrix()
			GL.glEnable(GL.GL_DEPTH_TEST)

	def DrawDragBox(self, proj):
		for button in self.mouseDragBounds:
			if button is None: continue
			boxEv = self.mouseDragBounds[button]
			if boxEv is None: continue
			pt1w = boxEv[0].worldPos
			pt2w = boxEv[1].worldPos
			pt1 = proj.ProjDeg(pt1w[0], pt1w[1], pt1w[2])
			pt2 = proj.ProjDeg(pt1w[0], pt2w[1], pt1w[2])
			pt3 = proj.ProjDeg(pt2w[0], pt2w[1], pt2w[2])
			pt4 = proj.ProjDeg(pt2w[0], pt1w[1], pt2w[2])

			GL.glDisable(GL.GL_DEPTH_TEST)
			GL.glColor3f(0.1,0.8,0.1)

			GL.glBegin(GL.GL_LINE_LOOP)
			GL.glVertex(*pt1)
			GL.glVertex(*pt2)
			GL.glVertex(*pt3)
			GL.glVertex(*pt4)
			GL.glEnd()

			GL.glEnable(GL.GL_DEPTH_TEST)


