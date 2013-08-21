
import uuid

class Event(object):
	def __init__(self):
		self.type = "undefined"
		self.dest = None
		self.src = None

class EventCallback(object):
	def __init__(self, mediator):
		self.callbackId = uuid.uuid4()
		self.mediator = mediator

	def ProcessEvent(self, event):
		pass

class EventMediator(object):
	def __init__(self):
		self.listeners = {}

	def SendMessage(self, msg):

		if msg.type not in self.listeners:
			#raise Exception("Unknown message type")
			return
		tyListeners = self.listeners[msg.type]

		if msg.dest is not None:
			#Message is addressed to specific receiver
			if msg.dest not in tyListeners:
				raise Exception("Unknown message destination")
			tyListeners[msg.dest].ProcessEvent(msg)
		else:
			#Message is a broadcast
			for li in tyListeners:
				li.ProcessEvent(msg)

	def AddListener(self, ty, callbackObj):

		if ty not in self.listeners:
			self.listeners[ty] = {}
		self.listeners[ty][callbackObj.callbackId] = callbackObj


