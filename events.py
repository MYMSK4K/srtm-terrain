
import uuid

class Event:
	def __init__(self):
		self.type = "undefined"
		self.dest = None
		self.src = None

class EventCallback:
	def __init__(self):
		self.callbackId = uuid.uuid4()

	def ProcessEvent(self, event):
		pass

class EventMediator:
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
		self.listeners[ty][callbackObj.callbackId] = callbackId


