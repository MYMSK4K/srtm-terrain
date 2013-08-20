SCREEN_SIZE = (800, 600)

from math import radians 

from OpenGL.GL import *
from OpenGL.GLU import *

import pygame
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


def run():
	
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE, HWSURFACE|OPENGL|DOUBLEBUF)
	
	resize(*SCREEN_SIZE)
	init()
	
	clock = pygame.time.Clock()	
	
	glMaterial(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))	
	glMaterial(GL_FRONT, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

	movement_speed = 5.0	

	while True:
		
		for event in pygame.event.get():
			if event.type == QUIT:
				return
			if event.type == KEYUP and event.key == K_ESCAPE:
				return				
			
		# Clear the screen, and z-buffer
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
						
		time_passed = clock.tick()
		time_passed_seconds = time_passed / 1000.
		
		pressed = pygame.key.get_pressed()
		
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		gluLookAt(0, 0, 10, # look from camera XYZ
			0, 0, 0, # look at the origin
			0, 1, 0); # up

		glBegin(GL_QUADS);
		glColor4f(1.0, 0., 0., 1.)
		glVertex(-1.0, 1.0, 0.0)
		glVertex(1.0, 1.0, 0.0)
		glVertex(1.0, -1.0, 0.0)
		glVertex(-1.0, -1.0, 0.0)
		glEnd();

		# Show the screen
		pygame.display.flip()

if __name__ == "__main__":
	run()

