
import events, gameobjs, math
import numpy as np

###Object Manager

class GameObjects(events.EventCallback):
	def __init__(self, mediator):
		super(GameObjects, self).__init__(mediator)
		mediator.AddListener("getpos", self)
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
		mediator.AddListener("addunit", self)
		mediator.AddListener("addarea", self)
		mediator.AddListener("setmission", self)
		mediator.AddListener("drawObjects", self)

		self.objs = {}
		self.newObjs = [] #Add these to main object dict after iteration
		self.objsToRemove = [] #Remove these after current iteration
		self.areaContents = {}
		self.verbose = 0
		self.playerId = None

	def Add(self, obj):
		self.objs[obj.objId] = obj

	def ProcessEvent(self, event):
		if event.type == "getpos":
			if event.objId not in self.objs:
				raise Exception("Unknown object id")
			return self.objs[event.objId].pos

		if event.type == "fireshell":
			if self.verbose: print event.type

			shot = gameobjs.Shell(self.mediator)
			shot.targetPos = event.targetPos
			shot.targetId = event.targetId
			shot.firerId = event.firerId
			shot.playerId = event.playerId
			shot.SetPos(event.firerPos)
			shot.speed = event.speed
			self.newObjs.append(shot)

		if event.type == "detonate":
			if self.verbose: print event.type
			self.objsToRemove.append(event.objId)

			#Check if it hit
			hitCount = 0
			for objId in self.objs:
				obj = self.objs[objId]
				hit = obj.CollidesWithPoint((event.pos[0], event.pos[1], 0.), event.proj)

				if hit and obj.health > 0.:
					hitCount += 1
					obj.health -= 0.1

					hitEvent = events.Event("targethit")
					hitEvent.objId = obj.objId
					hitEvent.firerId = event.firerId
					self.mediator.Send(hitEvent)

					if obj.health < 0.: obj.health = 0.
					if obj.health == 0:
						destroyEvent = events.Event("targetdestroyed")
						destroyEvent.objId = obj.objId
						destroyEvent.firerId = event.firerId
						destroyEvent.playerId = event.playerId
						self.mediator.Send(destroyEvent)
			
			if hitCount == 0:
				hitEvent = events.Event("shellmiss")
				hitEvent.firerId = event.firerId
				self.mediator.Send(hitEvent)

		if event.type == "targetdestroyed":
			if self.verbose: print event.type

			#Stop attacking targets that are dead
			for objId in self.objs:
				obj = self.objs[objId]
				if obj.GetAttackTarget() == event.objId:
					obj.Attack(None)

		if event.type == "targethit":
			if self.verbose: print event.type

		if event.type == "shellmiss":
			if self.verbose: print event.type

		if event.type == "attackorder":
			if self.verbose: print event.type

		if event.type == "moveorder":
			if self.verbose: print event.type

		if event.type == "stoporder":
			if self.verbose: print event.type

		if event.type == "enterarea":
			if self.verbose: print event.type

		if event.type == "exitarea":
			if self.verbose: print event.type

		if event.type == "addunit":
			if self.verbose: print event.type
			enemy = gameobjs.Person(self.mediator)
			enemy.faction = event.faction
			enemy.SetPos(np.array((event.pos[0], event.pos[1], 0.)))
			self.newObjs.append(enemy)
			return enemy.objId

		if event.type == "addarea":
			if self.verbose: print event.type
			area = gameobjs.AreaObjective(self.mediator)
			area.SetPos(np.array((event.pos[0], event.pos[1], 0.)))
			self.newObjs.append(area)
			return area.objId

		if event.type == "setmission":
			print event.text

		if event.type == "drawObjects":
			self.Draw(event.proj)

	def Update(self, timeElapsed, timeNow, proj):
		for objId in self.objs:
			self.objs[objId].Update(timeElapsed, timeNow, proj)

		#Update list of objects with new items
		for obj in self.newObjs:
			self.objs[obj.objId] = obj
		self.newObjs = []

		#Remove objects that are due to be deleted
		for objId in self.objsToRemove:
			del self.objs[objId]
		self.objsToRemove = []

		#Update list of areas
		areas = set()
		for objId in self.objs:
			obj = self.objs[objId]
			if isinstance(obj, gameobjs.AreaObjective):
				areas.add(objId)
				if objId not in self.areaContents:
					self.areaContents[objId] = []

		#Remove unused areas
		areasToRemove = []
		for areaId in self.areaContents:
			if areaId not in areas:		
				areasToRemove.append(areaId)
		for areaId in areasToRemove:
			del self.areaContents[areaId]

		#Check the contents of areas
		for areaId in self.areaContents:
			area = self.objs[areaId]
			contents = self.areaContents[areaId]
			
			for objId in self.objs:
				obj = self.objs[objId]
				if isinstance(obj, gameobjs.AreaObjective): continue
				contains = area.CollidesWithPoint((obj.pos[0], obj.pos[1], 0.), proj)
				if contains and objId not in contents:
					areaEvent = events.Event("enterarea")
					areaEvent.objId = objId
					areaEvent.areaId = areaId
					self.mediator.Send(areaEvent)

					contents.append(objId)
					
				if not contains and objId in contents:
					areaEvent = events.Event("exitarea")
					areaEvent.objId = objId
					areaEvent.areaId = areaId
					self.mediator.Send(areaEvent)

					contents.remove(objId)			

	def Draw(self, proj):
		for objId in self.objs:
			self.objs[objId].Draw(proj)

	def ObjNearPos(self, pos, proj, notFaction = None):
		bestDist, bestUuid = None, None
		pos = np.array(pos)
		for objId in self.objs:
			obj = self.objs[objId]
			if notFaction is not None and obj.faction == notFaction: continue #Ignore friendlies
			health = obj.GetHealth()
			if health is None: continue
			if health == 0.: continue #Ignore dead targets
			mag = proj.DistanceBetween(obj.pos[0], obj.pos[1], 0., 
				pos[0], pos[1], 0.)
			if bestDist is None or mag < bestDist:
				bestDist = mag
				bestUuid = obj.objId

		return bestUuid, bestDist

	def WorldClick(self, worldPos, button, proj):
		if button == 1:
			for objId in self.objs:
				obj = self.objs[objId]
				if obj.playerId != self.playerId: continue

				worldPosFlat = (worldPos[0], worldPos[1], 0.)
				obj.MoveTo(worldPosFlat)

				moveOrder = events.Event("moveorder")
				moveOrder.objId = obj.objId
				moveOrder.pos = worldPosFlat
				self.mediator.Send(moveOrder)

		if button == 3:
			bestUuid, bestDist = self.ObjNearPos(worldPos, proj, 1)
			clickTolerance = 5.
			print bestUuid, bestDist

			if bestUuid is not None and bestDist < clickTolerance:
				for objId in self.objs:
					obj = self.objs[objId]
					if obj.playerId != self.playerId: continue
					obj.Attack(bestUuid)

					if bestUuid is not None:
						attackOrder = events.Event("attackorder")
						attackOrder.attackerId = obj.objId
						attackOrder.targetId = bestUuid
						self.mediator.Send(attackOrder)

			if bestUuid is None or bestDist >= clickTolerance:
				for objId in self.objs:
					obj = self.objs[objId]
					if obj.playerId != self.playerId: continue
					#Stop attack
					obj.Attack(None)

					stopOrder = events.Event("stoporder")
					stopOrder.objId = obj.objId
					self.mediator.Send(stopOrder)

