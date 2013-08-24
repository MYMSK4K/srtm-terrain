
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
	
	glEnable(GL_DEPTH_TEST)
	glDepthFunc(GL_LEQUAL)
	glClearColor(1.0, 1.0, 1.0, 0.0)
	glEnable(GL_BLEND)

class ProjFunc:
	def __init__(self):
		self.radius = 6371.
		self.glOrigin = (0., 0., 0.)
		self.glOrigin = self.Proj(math.radians(54.0), math.radians(27.0), 0.)

	def Proj(self, lat, lon, alt):

		R = self.radius + alt / 1000.
		x = R * math.cos(lat) * math.cos(lon)
		y = R * math.cos(lat) * math.sin(lon)
		z = R * math.sin(lat)
		out = np.array((x,y,z)) - self.glOrigin
		return out

	def UnProj(self, x, y, z):
		pos = np.array([x,y,z])+self.glOrigin
		R = np.linalg.norm(pos, ord=2)
		lat = math.asin(pos[2] / R)
		lon = math.atan2(pos[1], pos[0])
		alt = R - self.radius
		return lat, lon, alt * 1000.

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
				#Convert from screen to world coordinates
				glDepth = glReadPixels(event.pos[0], SCREEN_SIZE[1] - event.pos[1], 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT);
				clickWorld = gluUnProject(event.pos[0], SCREEN_SIZE[1] - event.pos[1], glDepth)
				print clickWorld				

				#Convert from world to lat lon
				latLonR = proj.UnProj(*clickWorld)
				clickLat = math.degrees(latLonR[0])
				clickLon = math.degrees(latLonR[1])
				print clickLat, clickLon, latLonR[2]

				#Emit event
				gameObjects.WorldClick((clickLat, clickLon, latLonR[2]), event.button)

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

