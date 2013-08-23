
import events, terrain, kothicfile, bz2, math
import OpenGL.GL as GL

class Terrain(events.EventCallback):
	def __init__(self, mediator):
		super(Terrain, self).__init__(mediator)
		mediator.AddListener("drawTerrain", self)

		fi = bz2.BZ2File("kothic-12-2359-1316.js.bz2","r")
		self.kf = kothicfile.KothicFile(fi)
		self.proj = None
		
	def ProcessEvent(self, event):
		if event.type == "drawTerrain":
			self.Draw(event.proj)

	def Draw(self, proj):

		#Draw the ground
		GL.glColor3f(0.98, 0.96, 0.95)
		GL.glBegin(GL.GL_POLYGON)
		bboxD = self.kf.bbox
		#bboxD = [27.3782, 53.930185, 27.3882, 53.940185]
		bbox = map(math.radians, bboxD)

		GL.glVertex3f(*proj.Proj(bbox[1],bbox[0],0.))
		GL.glVertex3f(*proj.Proj(bbox[3],bbox[0],0.))
		GL.glVertex3f(*proj.Proj(bbox[3],bbox[2],0.))
		GL.glVertex3f(*proj.Proj(bbox[1],bbox[2],0.))
		
		GL.glEnd()



		for poly in self.kf.polygons:
			for line in poly[1]:
				#print line
				pass
