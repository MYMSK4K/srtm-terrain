
import hgtfile, random
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import numpy as np

class SimplifyMesh:
	def __init__(self, tile):
		self.pts = []
		self.val = []
		self.tile = tile
		print self.tile.shape
		for i in range(tile.shape[0]):
			for j in range(tile.shape[1]):
				self.pts.append((i, j))
				self.val.append((tile[i, j]))

	def EvalTris(self, points, vals):
		de = Delaunay(points)

		#For each point in the original surface
		for i in range(self.tile.shape[0]):
			for j in range(self.tile.shape[1]):
				self.EstimateHeightAtPoint((i, j), de)

	def EstimateHeightAtPoint(self, pt, de):
		simp = de.find_simplex(pt)
		print simp, de.simplices[simp]

		
	def VisTris(self, de):
		print de
		points = np.array(self.pts)
		plt.triplot(points[:,0], points[:,1], de.simplices.copy())
		plt.plot(points[:,0], points[:,1], 'o')
		plt.show()

if __name__=="__main__":

	tile = hgtfile.OpenHgt("N51E001.hgt.zip")

	simplify = SimplifyMesh(tile[:19,:19])
	simplify.EvalTris(simplify.pts, simplify.val)


