
import bz2, json

class KothicFile:
	def __init__(self, fi):
		#Parse JOSNP
		fiStr = fi.read()
		jsonStart = fiStr.find("{")
		jsonEnd = fiStr[::-1].find("}")
		data = json.loads(fiStr[jsonStart:-jsonEnd])

		self.granuality = float(data['granularity'])
		self.bbox = data['bbox']
		self.bboxRange = (self.bbox[2] - self.bbox[0], self.bbox[3] - self.bbox[1])
		self.points = []
		self.lineStrings = []
		self.multiLineStrings = []
		self.polygons = []
		self.multiPolygon = []

		for feature in data['features']:
			reprpoint = None
			if 'reprpoint' in feature: reprpoint = feature['reprpoint']
			ftype = feature['type']
			properties = feature['properties']
			coordinates = feature['coordinates']

			latlon = self.ConvertCoord(coordinates)
			#print ftype, coordinates, latlon
			if ftype == "Point":
				self.points.append((properties, latlon, reprpoint))
			if ftype == "LineString":
				self.lineStrings.append((properties, latlon, reprpoint))
			if ftype == "MultiLineString":
				self.multiLineStrings.append((properties, latlon, reprpoint))
			if ftype == "Polygon":
				self.polygons.append((properties, latlon, reprpoint))
			if ftype == "MultiPolygon":
				self.multiPolygon.append((properties, latlon, reprpoint))

	def ConvertCoord(self, pt):
		
		if hasattr(pt[0], '__iter__'):
			out = []
			for p in pt:
				out.append(self.ConvertCoord(p))
			return out
		else:
			return ((pt[1] / self.granuality) * self.bboxRange[0] + self.bbox[0], 
				(pt[0] / self.granuality) * self.bboxRange[1] + self.bbox[1])
		
def KothicMatplotlib(kf):
	import matplotlib.pyplot as plt
	import numpy as np

	print len(kf.points)
	print len(kf.lineStrings)
	print len(kf.multiLineStrings)
	print len(kf.polygons)
	print len(kf.multiPolygon)

	for poly in kf.polygons:
		for line in poly[1]:
			plt.plot(np.array(line)[:,1], np.array(line)[:,0])

	for line in kf.lineStrings:
		plt.plot(np.array(line[1])[:,1], np.array(line[1])[:,0])
	plt.show()	

if __name__=="__main__":

	fi = bz2.BZ2File("kothic-12-2359-1316.js.bz2","r")
		
	kf = KothicFile(fi)
	print kf.bbox
	print kf.granuality
	KothicMatplotlib(kf)
