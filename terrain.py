
import events, terrain, kothicfile, bz2, math, hgtfile
import OpenGL.GL as GL
import numpy as np
import scipy.misc

class TerrainTexture(object):
	def __init__(self, heightMap, bbox):
		self.dl = None

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
	
	def GenDisplayList(self, proj):
		self.dl = GL.glGenLists(1)
		GL.glNewList(self.dl, GL.GL_COMPILE)

		GL.glEnable(GL.GL_TEXTURE_2D)
		GL.glBindTexture(GL.GL_TEXTURE_2D, self.num)
		GL.glColor3f(0.98, 0.96, 0.95)

		res = 10
		for x in range(res):
			for y in range(res):

				bboxD = [float(x) * self.lonRange / res + self.bbox[0], 
					float(y) * self.latRange / res + self.bbox[1],
					float(x+1) * self.lonRange / res + self.bbox[0], 
					float(y+1) * self.latRange / res + self.bbox[1]]
				bboxR = map(math.radians, bboxD)

				GL.glBegin(GL.GL_POLYGON)

				GL.glTexCoord2f(*self.Project(bboxD[1], bboxD[0]))
				GL.glVertex3f(*proj.Proj(bboxR[1],bboxR[0],0.))

				GL.glTexCoord2f(*self.Project(bboxD[3], bboxD[0]))
				GL.glVertex3f(*proj.Proj(bboxR[3],bboxR[0],0.))

				GL.glTexCoord2f(*self.Project(bboxD[3], bboxD[2]))
				GL.glVertex3f(*proj.Proj(bboxR[3],bboxR[2],0.))

				GL.glTexCoord2f(*self.Project(bboxD[1], bboxD[2]))
				GL.glVertex3f(*proj.Proj(bboxR[1],bboxR[2],0.))
		
				GL.glEnd()

		GL.glEndList()	

	def Draw(self, proj):
		if self.dl is None:
			self.GenDisplayList(proj)
		GL.glCallList(self.dl)
		

class Terrain(events.EventCallback):
	def __init__(self, mediator):
		super(Terrain, self).__init__(mediator)
		mediator.AddListener("drawTerrain", self)

		fi = bz2.BZ2File("kothic-12-2359-1316.js.bz2","r")
		self.kf = kothicfile.KothicFile(fi)
		self.proj = None

		heightMap = hgtfile.OpenHgt("N53E027.hgt.zip")
		self.heightTex = TerrainTexture(heightMap, [27., 53., 28., 54.])

		heightMap2 = hgtfile.OpenHgt("N53E028.hgt.zip")
		self.heightTex2 = TerrainTexture(heightMap2, [28., 53., 29., 54.])
		
	def ProcessEvent(self, event):
		if event.type == "drawTerrain":
			self.Draw(event.proj)

	def Draw(self, proj):

		#Draw the ground
		self.heightTex.Draw(proj)
		self.heightTex2.Draw(proj)


		#Rivers and streams
		GL.glColor3f(0.0, 0.0, 0.9)
		for line in self.kf.lineStrings:
			attribs = line[0]
			if "waterway" not in attribs: continue
			#if attribs["waterway"] != "river" and  attribs["waterway"] != "stream": continue
			GL.glBegin(GL.GL_LINE_STRIP)
			for pt in line[1]:
				GL.glVertex3f(*proj.Proj(math.radians(pt[1]),math.radians(pt[0]),0.))
			GL.glEnd()


		#Buildings
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

