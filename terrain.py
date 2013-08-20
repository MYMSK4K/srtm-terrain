SCREEN_SIZE = (800, 600)

from math import radians 

from OpenGL.GL import *
from OpenGL.GLU import *

import pygame
import hgtfile
from pygame.locals import *

def resize(width, height):
	
	glViewport(0, 0, width, height)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(60.0, float(width)/height, .1, 1000.)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()


def init():
	
	glEnable(GL_DEPTH_TEST)
	glClearColor(1.0, 1.0, 1.0, 0.0)

class QuadTile():
	def __init__(self, tile, xinds, yinds, vmin, vmax, depth = 0):

		self.tile = tile
		self.max = vmax
		self.min = vmin
		self.xinds = xinds
		self.yinds = yinds
		self.childTiles = []
		self.depth = depth

		if xinds[1]-xinds[0] > 10 or yinds[1]-yinds[0] > 10:
			self.Split()

	def Draw(self):

		x1 = float(self.xinds[0]) / self.tile.shape[0]
		x2 = float(self.xinds[1]) / self.tile.shape[0]
		y1 = float(self.yinds[0]) / self.tile.shape[1]
		y2 = float(self.yinds[1]) / self.tile.shape[1]
		c11 = self.tile[self.xinds[0], self.yinds[0]] 
		c12 = self.tile[self.xinds[0], self.yinds[1]]
		c21 = self.tile[self.xinds[1], self.yinds[0]]
		c22 = self.tile[self.xinds[1], self.yinds[1]]

		if len(self.childTiles) == 0:
			if 0:
				glBegin(GL_QUADS)
				glColor4f(c11, c11, c11, 1.)
				glVertex(x1, y1, 0.)
				glColor4f(c21, c21, c21, 1.)
				glVertex(x2, y1, 0.)
				glColor4f(c22, c22, c22, 1.)
				glVertex(x2, y2, 0.)
				glColor4f(c12, c12, c12, 1.)
				glVertex(x1, y2, 0.)
				glEnd()
			else:
				glColor4f(0., 0., 0., 1.)
				glBegin(GL_LINE_LOOP)
				glVertex(x1, y1, 0.)
				glVertex(x2, y1, 0.)
				glVertex(x2, y2, 0.)
				glVertex(x1, y2, 0.)
				glEnd()
		else:
			for t in self.childTiles:
				t.Draw()

	def Split(self):
		xsp = int(round((self.xinds[0] + self.xinds[1]) * 0.5))
		ysp = int(round((self.yinds[0] + self.yinds[1]) * 0.5))

		self.childTiles = []
		self.childTiles.append(QuadTile(self.tile, (self.xinds[0], xsp), (self.yinds[0], ysp), self.min, self.max, self.depth + 1))
		self.childTiles.append(QuadTile(self.tile, (xsp, self.xinds[1]), (self.yinds[0], ysp), self.min, self.max, self.depth + 1))
		self.childTiles.append(QuadTile(self.tile, (self.xinds[0], xsp), (ysp, self.yinds[1]), self.min, self.max, self.depth + 1))
		self.childTiles.append(QuadTile(self.tile, (xsp, self.xinds[1]), (ysp, self.yinds[1]), self.min, self.max, self.depth + 1))

class SrtmTile():
	def __init__(self):
		self.tile = hgtfile.OpenHgt("N51E001.hgt.zip")
		self.max = self.tile.max()
		self.min = self.tile.min()
		self.tileNorm = (self.tile.astype(float) - self.min) / (self.max - self.min)
		print self.tile.shape

		xsp = self.tile.shape[0] / 2
		ysp = self.tile.shape[1] / 2
		self.childTiles = []
		self.childTiles.append(QuadTile(self.tileNorm, (0, xsp), (0, ysp), self.min, self.max))
		self.childTiles.append(QuadTile(self.tileNorm, (xsp, self.tile.shape[0]-1), (0, ysp), self.min, self.max))
		self.childTiles.append(QuadTile(self.tileNorm, (0, xsp), (ysp, self.tile.shape[1]-1), self.min, self.max))
		self.childTiles.append(QuadTile(self.tileNorm, (xsp, self.tile.shape[0]-1), (ysp, self.tile.shape[1]-1), self.min, self.max))

	def Draw(self):

		self.childTiles[0].Draw()
		self.childTiles[1].Draw()
		self.childTiles[2].Draw()
		self.childTiles[3].Draw()

def run():
	
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE, HWSURFACE|OPENGL|DOUBLEBUF)
	
	resize(*SCREEN_SIZE)
	init()
	
	clock = pygame.time.Clock()	
	
	glMaterial(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))	
	glMaterial(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

	movement_speed = 5.0
	camPos = [0., 0., 2.]

	srtmTile = SrtmTile()

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
			camPos[0] -= 1. * time_passed_seconds
		if pressed[K_RIGHT]:
			camPos[0] += 1. * time_passed_seconds
		if pressed[K_UP]:
			camPos[1] += 1. * time_passed_seconds
		if pressed[K_DOWN]:
			camPos[1] -= 1. * time_passed_seconds
		if pressed[K_a]:
			camPos[2] -= 1. * time_passed_seconds
		if pressed[K_z]:
			camPos[2] += 1. * time_passed_seconds
		
		# Clear the screen, and z-buffer
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
						
		time_passed = clock.tick()
		time_passed_seconds = time_passed / 1000.
		
		pressed = pygame.key.get_pressed()
		
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		gluLookAt(camPos[0], camPos[1], camPos[2], # look from camera XYZ
			camPos[0], camPos[1], 0., # look at the origin
			0, 1, 0); # up

		srtmTile.Draw()

		# Show the screen
		pygame.display.flip()

if __name__ == "__main__":
	run()

