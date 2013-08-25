
import events, terrain, kothicfile, bz2, math, hgtfile
import OpenGL.GL as GL
import numpy as np
import scipy.misc

class TerrainTexture(object):
	def __init__(self, heightMap, bbox):
		heightMapRes = scipy.misc.imresize(heightMap, (1024, 1024), 'bilinear', "L")
		heightMapRes /= 2.
		heightMapRes += 128.
		rawData = heightMapRes.astype('uint8').tostring()

		self.num = GL.glGenTextures(1)
		GL.glBindTexture(GL.GL_TEXTURE_2D, self.num)
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
		GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
		GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_LUMINANCE, heightMapRes.shape[0], heightMapRes.shape[1], 0, GL.GL_LUMINANCE,
			GL.GL_UNSIGNED_BYTE, rawData)

		self.bbox = bbox #left,bottom,right,top	
		self.lonRange = bbox[2] - bbox[0]
		self.latRange = bbox[3] - bbox[1]
	
	def Project(self, lat, lon):
		x = (lon - self.bbox[0]) / self.lonRange
		y = (lat - self.bbox[1]) / self.latRange
		return x, y

class Terrain(events.EventCallback):
	def __init__(self, mediator):
		super(Terrain, self).__init__(mediator)
		mediator.AddListener("drawTerrain", self)

		fi = bz2.BZ2File("kothic-12-2359-1316.js.bz2","r")
		self.kf = kothicfile.KothicFile(fi)
		self.proj = None

		heightMap = hgtfile.OpenHgt("N53E027.hgt.zip")
		self.heightTex = TerrainTexture(heightMap, [27., 53., 28., 54.])
		
	def ProcessEvent(self, event):
		if event.type == "drawTerrain":
			self.Draw(event.proj)

	def Draw(self, proj):

		GL.glEnable(GL.GL_TEXTURE_2D)
		GL.glBindTexture(GL.GL_TEXTURE_2D, self.heightTex.num)

		#Draw the ground
		GL.glColor3f(0.98, 0.96, 0.95)
		GL.glBegin(GL.GL_POLYGON)
		bboxD = self.kf.bbox
		#bboxD = [27.3782, 53.930185, 27.3882, 53.940185]
		bbox = map(math.radians, bboxD)

		GL.glTexCoord2f(*self.heightTex.Project(bboxD[1], bboxD[0]))
		GL.glVertex3f(*proj.Proj(bbox[1],bbox[0],0.))

		GL.glTexCoord2f(*self.heightTex.Project(bboxD[3], bboxD[0]))
		GL.glVertex3f(*proj.Proj(bbox[3],bbox[0],0.))

		GL.glTexCoord2f(*self.heightTex.Project(bboxD[3], bboxD[2]))
		GL.glVertex3f(*proj.Proj(bbox[3],bbox[2],0.))

		GL.glTexCoord2f(*self.heightTex.Project(bboxD[1], bboxD[2]))
		GL.glVertex3f(*proj.Proj(bbox[1],bbox[2],0.))
		
		GL.glEnd()

		GL.glColor3f(0.0, 0.0, 0.5)
		for poly in self.kf.polygons:
			attribs = poly[0]
			if "building" not in attribs: continue
			GL.glBegin(GL.GL_POLYGON)
			for line in poly[1]:
				for pt in line:
					GL.glVertex3f(*proj.Proj(math.radians(pt[1]),math.radians(pt[0]),0.))
	
			GL.glEnd()

		GL.glDisable(GL.GL_TEXTURE_2D)

