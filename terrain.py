SCREEN_SIZE = (800, 600)

import math 

from OpenGL.GL import *
from OpenGL.GLU import *

import pygame
import hgtfile
from pygame.locals import *
import numpy as np

def resize(width, height):
	
	glViewport(0, 0, width, height)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(60.0, float(width)/height, .001, 1000.)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()


def init():
	
	glDisable(GL_DEPTH_TEST)
	glClearColor(1.0, 1.0, 1.0, 0.0)


class ProjFunc:
	def __init__(self):
		pass

	def Proj(self, lat, lon, alt):

		R = 6371. + alt / 1000.
		x = R * math.cos(lat) * math.cos(lon)
		y = R * math.cos(lat) * math.sin(lon)
		z = R * math.sin(lat)
		return (x, y, z)

class QuadTileData:
	def __init__(self, tile, lat1, lat2, lon1, lon2):
		self.tile = tile
		self.max = tile.max()
		self.min = tile.min()
		self.proj = ProjFunc()
		lats = (math.radians(lat1), math.radians(lat2))
		lons = (math.radians(lon1), math.radians(lon2))
		self.latLims = (min(lats), max(lats))
		self.lonLims = (min(lons), max(lons))
		self.latRange = self.latLims[1] - self.latLims[0]
		self.lonRange = self.lonLims[1] - self.lonLims[0]

class GeoMipMap():
	def __init__(self, data, xinds = None, yinds = None, depth = 0):
		
		self.data = data
		self.depth = depth
		if xinds is not None: self.xinds = xinds
		else: self.xinds = (0, data.tile.shape[0]-1)
		if yinds is not None: self.yinds = yinds
		else: self.yinds = (0, data.tile.shape[1]-1)

	def Draw(self):
		for i in range(self.xinds[0], self.xinds[1]):
			for j in range(self.yinds[0], self.yinds[1]):

				x1 = -float(i) * self.data.latRange / self.data.tile.shape[0] + self.data.latLims[1]
				x2 = -float(i+1) * self.data.latRange / self.data.tile.shape[0] + self.data.latLims[1]
				y1 = float(j) * self.data.lonRange / self.data.tile.shape[1] + self.data.lonLims[0]
				y2 = float(j+1) * self.data.lonRange / self.data.tile.shape[1] + self.data.lonLims[0]

				p11 = self.data.proj.Proj(x1, y1, 0.)
				p12 = self.data.proj.Proj(x1, y2, 0.)
				p21 = self.data.proj.Proj(x2, y1, 0.)
				p22 = self.data.proj.Proj(x2, y2, 0.)

				c11 = self.data.tile[i, j] 
				c12 = self.data.tile[i, j+1]
				c21 = self.data.tile[i+1, j]
				c22 = self.data.tile[i+1, j+1]


				if 1:
					glBegin(GL_QUADS)
					glColor4f(c11, c11, c11, 1.)
					glVertex(*p11)
					glColor4f(c21, c21, c21, 1.)
					glVertex(*p21)
					glColor4f(c22, c22, c22, 1.)
					glVertex(*p22)
					glColor4f(c12, c12, c12, 1.)
					glVertex(*p12)
					glEnd()

				if 0:
					glColor4f(1., 1., 0., 1.)
					glBegin(GL_LINE_LOOP)
					glVertex(*p11)
					glVertex(*p21)
					glVertex(*p22)
					glVertex(*p12)
					glEnd()


class QuadTile():
	def __init__(self, data, xinds = None, yinds = None, depth = 0):

		self.data = data
		self.childTiles = []
		self.depth = depth
		if xinds is not None: self.xinds = xinds
		else: self.xinds = (0, data.tile.shape[0]-1)
		if yinds is not None: self.yinds = yinds
		else: self.yinds = (0, data.tile.shape[1]-1)
		
		if self.xinds[1]-self.xinds[0] > 50 or self.yinds[1]-self.yinds[0] > 50:
			self.Split()


	def Draw(self):

		x1 = -float(self.xinds[0]) * self.data.latRange / self.data.tile.shape[0] + self.data.latLims[1]
		x2 = -float(self.xinds[1]) * self.data.latRange / self.data.tile.shape[0] + self.data.latLims[1]
		y1 = float(self.yinds[0]) * self.data.lonRange / self.data.tile.shape[1] + self.data.lonLims[0]
		y2 = float(self.yinds[1]) * self.data.lonRange / self.data.tile.shape[1] + self.data.lonLims[0]

		p11 = self.data.proj.Proj(x1, y1, 0.)
		p12 = self.data.proj.Proj(x1, y2, 0.)
		p21 = self.data.proj.Proj(x2, y1, 0.)
		p22 = self.data.proj.Proj(x2, y2, 0.)

		c11 = self.data.tile[self.xinds[0], self.yinds[0]] 
		c12 = self.data.tile[self.xinds[0], self.yinds[1]]
		c21 = self.data.tile[self.xinds[1], self.yinds[0]]
		c22 = self.data.tile[self.xinds[1], self.yinds[1]]

		if len(self.childTiles) == 0:
			if 1:
				glBegin(GL_QUADS)
				glColor4f(c11, c11, c11, 1.)
				glVertex(*p11)
				glColor4f(c21, c21, c21, 1.)
				glVertex(*p21)
				glColor4f(c22, c22, c22, 1.)
				glVertex(*p22)
				glColor4f(c12, c12, c12, 1.)
				glVertex(*p12)
				glEnd()
			if 0:
				glColor4f(1., 1., 0., 1.)
				glBegin(GL_LINE_LOOP)
				glVertex(*p11)
				glVertex(*p21)
				glVertex(*p22)
				glVertex(*p12)
				glEnd()
		else:
			for t in self.childTiles:
				t.Draw()

	def Split(self):
		xsp = int(round((self.xinds[0] + self.xinds[1]) * 0.5))
		ysp = int(round((self.yinds[0] + self.yinds[1]) * 0.5))

		self.childTiles = []
		self.childTiles.append(QuadTile(self.data, (self.xinds[0], xsp), (self.yinds[0], ysp), self.depth + 1))
		self.childTiles.append(QuadTile(self.data, (xsp, self.xinds[1]), (self.yinds[0], ysp), self.depth + 1))
		self.childTiles.append(QuadTile(self.data, (self.xinds[0], xsp), (ysp, self.yinds[1]), self.depth + 1))
		self.childTiles.append(QuadTile(self.data, (xsp, self.xinds[1]), (ysp, self.yinds[1]), self.depth + 1))

	def SplitToMipMap(self):
		xsp = int(round((self.xinds[0] + self.xinds[1]) * 0.5))
		ysp = int(round((self.yinds[0] + self.yinds[1]) * 0.5))

		self.childTiles = []
		self.childTiles.append(GeoMipMap(self.data, (self.xinds[0], xsp), (self.yinds[0], ysp), self.depth + 1))
		self.childTiles.append(GeoMipMap(self.data, (xsp, self.xinds[1]), (self.yinds[0], ysp), self.depth + 1))
		self.childTiles.append(GeoMipMap(self.data, (self.xinds[0], xsp), (ysp, self.yinds[1]), self.depth + 1))
		self.childTiles.append(GeoMipMap(self.data, (xsp, self.xinds[1]), (ysp, self.yinds[1]), self.depth + 1))

def run():
	
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE, HWSURFACE|OPENGL|DOUBLEBUF)
	
	resize(*SCREEN_SIZE)
	init()
	
	clock = pygame.time.Clock()	
	
	glMaterial(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))	
	glMaterial(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

	movement_speed = 5.0

	proj = ProjFunc()
	
	camLatLon = [51.5, 1.5]
	camAlt = 100000.

	tile = hgtfile.OpenHgt("N51E001.hgt.zip")
	tileNorm = (tile.astype(float) - tile.min()) / (tile.max() - tile.min())
	tileData = QuadTileData(tileNorm, 51., 52., 1., 2.)
	srtmTile = QuadTile(tileData)

	count = 0
	ti = srtmTile
	while len(ti.childTiles) > 0:
		ti = ti.childTiles[0]
	ti.SplitToMipMap()

	while True:
		
		time_passed = clock.tick()
		time_passed_seconds = time_passed / 1000.

		for event in pygame.event.get():
			if event.type == QUIT:
				return
			if event.type == KEYUP and event.key == K_ESCAPE:
				return

		pressed = pygame.key.get_pressed()

		if pressed[K_LEFT]:
			camLatLon[1] -= 0.1 * time_passed_seconds
		if pressed[K_RIGHT]:
			camLatLon[1] += 0.1 * time_passed_seconds
		if pressed[K_UP]:
			camLatLon[0] += 0.1 * time_passed_seconds
		if pressed[K_DOWN]:
			camLatLon[0] -= 0.1 * time_passed_seconds
		if pressed[K_a]:
			camAlt -= 100000. * time_passed_seconds
		if pressed[K_z]:
			camAlt += 100000. * time_passed_seconds
		
		camPos = proj.Proj(math.radians(camLatLon[0]), math.radians(camLatLon[1]), camAlt)
		camTarg = proj.Proj(math.radians(camLatLon[0]), math.radians(camLatLon[1]), 0.)
		camOffNth = proj.Proj(math.radians(camLatLon[0]+0.5), math.radians(camLatLon[1]), 0.)
		camUp = np.array(camOffNth) - np.array(camTarg)
		camUpMag = np.linalg.norm(camUp, ord=2)
		camUp /= camUpMag

		# Clear the screen, and z-buffer
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
						
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		gluLookAt(camPos[0], camPos[1], camPos[2], # look from camera XYZ
			camTarg[0], camTarg[1], camTarg[2], # look at the origin
			camUp[0], camUp[1], camUp[2]); # up

		srtmTile.Draw()

		# Show the screen
		pygame.display.flip()

if __name__ == "__main__":
	run()

