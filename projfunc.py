
import math
import numpy as np
import OpenGL.GL as GL

class ProjFunc:
	def __init__(self):
		self.radius = 6371.
		self.scale = 1000.
		self.glOrigin = (0., 0., 0.)
		self.glOrigin = self.ProjDeg(54., 27., 0.)

	def Proj(self, lat, lon, alt):

		R = self.radius + alt / self.scale
		x = R * math.cos(lat) * math.cos(lon)
		y = R * math.cos(lat) * math.sin(lon)
		z = R * math.sin(lat)
		out = np.array((x,y,z)) - self.glOrigin
		return out

	def ProjDeg(self, latD, lonD, alt):
		return self.Proj(math.radians(latD), math.radians(lonD), alt)

	def UnProj(self, x, y, z):
		pos = np.array([x,y,z])+self.glOrigin
		R = np.linalg.norm(pos, ord=2)
		lat = math.asin(pos[2] / R)
		lon = math.atan2(pos[1], pos[0])
		alt = R - self.radius
		return lat, lon, alt * self.scale

	def UnProjDeg(self, x, y, z):
		radWorld = self.UnProj(x, y, z)
		return math.degrees(radWorld[0]), math.degrees(radWorld[1]), radWorld[2]

	def GetLocalDirectionVecs(self, lat, lon, alt):
		pos = self.ProjDeg(lat, lon, alt)
		posUp = self.ProjDeg(lat, lon, alt + 10000. / self.scale)
		posEst = self.ProjDeg(lat, lon+0.005, alt)

		up = np.array(posUp) - np.array(pos)
		upMag = np.linalg.norm(up, ord=2)
		if upMag > 0.:
			up /= upMag

		est = np.array(posEst) - np.array(pos)
		estMag = np.linalg.norm(est, ord=2)
		if estMag > 0.:
			est /= estMag

		nth = np.cross(up, est)
		return pos, nth, est, up

	def TransformToLocalCoords(self, lat, lon, alt):
		pos, nth, est, up = self.GetLocalDirectionVecs(lat, lon, alt)

		m = np.concatenate((est, [0.], nth, [0.], up, [0., 0., 0., 0., 1.]))

		GL.glTranslated(*pos)
		GL.glMultMatrixd(m)

	def DistanceBetween(self, lat1, lon1, alt1, lat2, lon2, alt2):
		pt1 = self.Proj(math.radians(lat1), math.radians(lon1), alt1)
		pt2 = self.Proj(math.radians(lat2), math.radians(lon2), alt2)

		return np.linalg.norm(pt1 - pt2, ord=2) * self.scale

	def ScaleDistance(self, dist):
		return dist / self.scale

	def UnscaleDistance(self, dist):
		return dist * self.scale

	def OffsetTowardsPoint(self, oriPt, towardPt, dist):
		pt1 = self.Proj(math.radians(oriPt[0]), math.radians(oriPt[1]), oriPt[2])
		pt2 = self.Proj(math.radians(towardPt[0]), math.radians(towardPt[1]), towardPt[2])
		direction = pt2 - pt1
		mag = np.linalg.norm(direction, ord=2)
		if mag > 0.:
			direction /= mag
		offsetCart = (direction * dist / self.scale) + pt1
		outRad = self.UnProj(offsetCart[0], offsetCart[1], offsetCart[2])
		return np.array((math.degrees(outRad[0]), math.degrees(outRad[1]), outRad[2]))

