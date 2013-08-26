
import uuid

class Event(object):
	def __init__(self, ty):
		self.type = ty
		self.dest = None
		self.src = None
		self.deliverAtTime = None

class EventCallback(object):
	def __init__(self, mediator):
		self.callbackId = uuid.uuid4()
		self.mediator = mediator

	def ProcessEvent(self, event):
		pass

class EventMediator(object):
	def __init__(self):
		self.listeners = {}
		self.delayedMessages = []

	def Send(self, msg):

		if msg.deliverAtTime is not None:
			self.delayedMessages.append(msg)
			return

		if msg.type not in self.listeners:
			#raise Exception("Unknown message type")
			return
		tyListeners = self.listeners[msg.type]

		if msg.dest is not None:
			#Message is addressed to specific receiver
			if msg.dest not in tyListeners:
				raise Exception("Unknown message destination")
			ret = tyListeners[msg.dest].ProcessEvent(msg)
			return [ret,]
		else:
			#Message is a broadcast
			ret = []
			for li in tyListeners:
				ret.append(tyListeners[li].ProcessEvent(msg))
			return ret

	def Update(self, gameTime):
		delivered = []
		for i, msg in enumerate(self.delayedMessages):
			if gameTime >= msg.deliverAtTime:
				msg.time = gameTime
				msg.deliverAtTime = None
				self.Send(msg)
				delivered.append(i)

		delayedMessagesOld = self.delayedMessages
		self.delayedMessages = []
		for i, msg in enumerate(delayedMessagesOld):
			if i in delivered: continue
			self.delayedMessages.append(msg)

	def AddListener(self, ty, callbackObj):

		if ty not in self.listeners:
			self.listeners[ty] = {}
		self.listeners[ty][callbackObj.callbackId] = callbackObj


