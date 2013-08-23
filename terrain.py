
import events, terrain, kothicfile, bz2

class Terrain(events.EventCallback):
	def __init__(self, mediator):
		super(Terrain, self).__init__(mediator)
		mediator.AddListener("drawTerrain", self)

		fi = bz2.BZ2File("kothic-12-2359-1316.js.bz2","r")
		self.kf = kothicfile.KothicFile(fi)
		self.proj = None
		
	def ProcessEvent(self, event):
		if event.type == "drawTerrain":
			self.Draw()

	def Draw(self):
		for poly in self.kf.polygons:
			for line in poly[1]:
				#print line
				pass
