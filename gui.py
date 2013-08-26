
import events

class Gui(events.EventCallback):
	def __init__(self, mediator):
		super(Gui, self).__init__(mediator)
		mediator.AddListener("mousebuttondown", self)
		mediator.AddListener("mousebuttonup", self)
		mediator.AddListener("mousemotion", self)

	def ProcessEvent(self, event):
		#print event.type
		pass
