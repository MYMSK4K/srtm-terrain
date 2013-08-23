
SCREEN_SIZE = (800, 600)

import math, uuid, events, script, gameobjs, objmanager, terrain

from OpenGL.GL import *
from OpenGL.GLU import *

import pygame, events
from pygame.locals import *
import numpy as np

### OpenGL Utility Functions

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
	glEnable(GL_BLEND)

class ProjFunc:
	def __init__(self):
		pass

	def Proj(self, lat, lon, alt):

		R = 6371. + alt / 1000.
		x = R * math.cos(lat) * math.cos(lon)
		y = R * math.cos(lat) * math.sin(lon)
		z = R * math.sin(lat)
		return (x, y, z)

	def TransformToLocalCoords(self, lat, lon, alt):
		pos = self.Proj(math.radians(lat), math.radians(lon), alt)
		posUp = self.Proj(math.radians(lat), math.radians(lon), alt + 1000.)
		posNth = self.Proj(math.radians(lat+0.5), math.radians(lon), alt)
		posEst = self.Proj(math.radians(lat), math.radians(lon+0.5), alt)

		up = np.array(posUp) - np.array(pos)
		upMag = np.linalg.norm(up, ord=2)
		if upMag > 0.:
			up /= upMag

		nth = np.array(posNth) - np.array(pos)
		nthMag = np.linalg.norm(nth, ord=2)
		if nthMag > 0.:
			nth /= nthMag

		est = np.array(posEst) - np.array(pos)
		estMag = np.linalg.norm(est, ord=2)
		if estMag > 0.:
			est /= estMag

		m = np.concatenate((est, [0.], nth, [0.], up, [0., 0., 0., 0., 1.]))

		glTranslated(*pos)
		glMultMatrixd(m)

### Main Program

def run():
	
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE, HWSURFACE|OPENGL|DOUBLEBUF)
	
	resize(*SCREEN_SIZE)
	init()
	
	clock = pygame.time.Clock()	
	proj = ProjFunc()
	
	glMaterial(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))	
	glMaterial(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

	movement_speed = 5.0
	camLatLon, camAlt = [0.5*(53.9043+53.9560), 0.5*(27.3339+27.4218)], 30.

	eventMediator = events.EventMediator()

	scriptObj = script.Script(eventMediator)
	gameObjects = objmanager.GameObjects(eventMediator)
	terrainMgr = terrain.Terrain(eventMediator)
	terrainMgr.proj = proj

	player = gameobjs.Person(eventMediator)
	player.playerId = uuid.uuid4()
	player.faction = 1
	player.pos = camLatLon[:]
	gameObjects.Add(player)
	gameObjects.playerId = player.playerId

	addPlayerEvent = events.Event("addplayer")
	addPlayerEvent.playerId = player.playerId
	eventMediator.Send(addPlayerEvent)

	startEvent = events.Event("gamestart")
	eventMediator.Send(startEvent)

	while True:
		
		time_passed = clock.tick()
		time_passed_seconds = time_passed / 1000.

		for event in pygame.event.get():
			if event.type == QUIT:
				return
			if event.type == KEYUP and event.key == K_ESCAPE:
				return
			if event.type == MOUSEBUTTONDOWN:
				worldPos = gluUnProject(event.pos[0], SCREEN_SIZE[1] - event.pos[1], 1.)
				rayVec = np.array(worldPos) - np.array(camPos)
				rayVecMag = np.linalg.norm(rayVec, ord=2)
				if rayVecMag > 0.:
					rayVec /= rayVecMag

				#Scale ray based on altitude
				scaleFac = -camPos[2] / rayVec[2]
				clickWorld = scaleFac * rayVec + np.array(camPos)
				#print "clickWorld", clickWorld

				gameObjects.WorldClick((clickWorld[0], clickWorld[1]), event.button)

		pressed = pygame.key.get_pressed()

		if pressed[K_LEFT]:
			camLatLon[1] -= 0.001 * time_passed_seconds
		if pressed[K_RIGHT]:
			camLatLon[1] += 0.001 * time_passed_seconds
		if pressed[K_UP]:
			camLatLon[0] += 0.001 * time_passed_seconds
		if pressed[K_DOWN]:
			camLatLon[0] -= 0.001 * time_passed_seconds
		if pressed[K_a]:
			camAlt -= 100. * time_passed_seconds
		if pressed[K_z]:
			camAlt += 100. * time_passed_seconds
		
		#print camLatLon, camAlt
		camPos = proj.Proj(math.radians(camLatLon[0]), math.radians(camLatLon[1]), camAlt)
		camTarg = proj.Proj(math.radians(camLatLon[0]), math.radians(camLatLon[1]), 0.)
		camOffNth = proj.Proj(math.radians(camLatLon[0]+0.5), math.radians(camLatLon[1]), 0.)
		camUp = np.array(camOffNth) - np.array(camTarg)
		camUpMag = np.linalg.norm(camUp, ord=2)
		camUp /= camUpMag
		
		gameObjects.Update(time_passed_seconds, pygame.time.get_ticks() / 1000., proj)

		# Clear the screen, and z-buffer
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
						
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		gluLookAt(camPos[0], camPos[1], camPos[2], # look from camera XYZ
			camTarg[0], camTarg[1], camTarg[2], # look at the origin
			camUp[0], camUp[1], camUp[2]); # up

		drawTerrainEv = events.Event("drawTerrain")
		drawTerrainEv.proj = proj
		eventMediator.Send(drawTerrainEv)

		drawObjectsEv = events.Event("drawObjects")
		drawObjectsEv.proj = proj
		eventMediator.Send(drawObjectsEv)

		# Show the screen
		pygame.display.flip()

if __name__ == "__main__":
	run()

