
import hgtfile, random
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import numpy as np

class SimplifyMesh:
	def __init__(self, tile):
		self.pts = []
		self.val = []
		self.protect = []
		self.tile = tile
		print self.tile.shape
		for i in range(tile.shape[0]):
			for j in range(tile.shape[1]):
				self.pts.append((i, j))
				self.val.append((tile[i, j]))
	
				prot = False
				if (i==0 or i==tile.shape[0]-1) and (j==0 or j==tile.shape[1]-1):
					prot = True
				self.protect.append(prot)
			
	def EvalTris(self, points, vals):
		de = Delaunay(points)

		#Map values to dict
		valMap = {}
		for pt, v in zip(points, vals):
			valMap[tuple(pt)] = v

		#Perform linear regression to form piecewise surface
		triSol = []
		for tri in de.simplices:
			triPts = de.points[tri]
			#print triPts
			triVals = [valMap[tuple(p)] for p in triPts]
			#print triVals
			triPtsHom = [(p[0],p[1],1.) for p in triPts]

			sol, res, rank, s = np.linalg.lstsq(triPtsHom, triVals)
			triSol.append(sol)

		#For each point in the original surface, calc error
		err = []
		for i in range(self.tile.shape[0]):
			for j in range(self.tile.shape[1]):
				he = self.EstimateHeightAtPoint((i, j), de, triSol)
				err.append(abs(he - self.tile[i, j]))
		return max(err)

	def EstimateHeightAtPoint(self, pt, de, triSol):
		simp = de.find_simplex(pt)
		#print simp, de.simplices[simp], triSol[simp]
		return np.dot((pt[0], pt[1], 1.), triSol[simp])

	def FindBestPointToRemove(self):
		res = []
		for testPtNum, protected in enumerate(self.protect):
			if protected: continue
			testPts = []
			testVals = []
			for count, (pt, v) in enumerate(zip(self.pts, self.val)):
				if count == testPtNum: continue
				testPts.append(pt)
				testVals.append(v)
			err = self.EvalTris(testPts, testVals)
			#print self.pts[testPtNum], err
			res.append((err, testPtNum, self.pts[testPtNum]))
		res.sort()
		return res[0]

	def RemovePointsLessThanErr(self, errThresh = 1.):

		cursor = 0
		while cursor < len(self.protect):
			if self.protect[cursor]:
				cursor += 1
				continue
			testPts = []
			testVals = []
			for count, (pt, v) in enumerate(zip(self.pts, self.val)):
				if count == cursor: continue
				testPts.append(pt)
				testVals.append(v)
			err = self.EvalTris(testPts, testVals)
			print cursor, self.pts[cursor], err, len(self.protect)
			if err < errThresh:
				del self.pts[cursor]
				del self.val[cursor]
				del self.protect[cursor]
			else:
				cursor += 1

	def Calc(self, errThresh = 1.):
		running = True
		while running:
			err, ptNum, ptPos = self.FindBestPointToRemove()
			print err, ptNum, ptPos
			if err < errThresh:
				del self.pts[ptNum]
				del self.val[ptNum]
				del self.protect[ptNum]
			else:
				running = False
		
	def VisTris(self):
		de = Delaunay(self.pts)
		print de
		points = np.array(self.pts)
		plt.triplot(points[:,0], points[:,1], de.simplices.copy())
		plt.plot(points[:,0], points[:,1], 'o')
		plt.show()

	def GetCurrentMesh(self):
		return self.pts

if __name__=="__main__":
	
	tile = hgtfile.OpenHgt("N51E001.hgt.zip")

	simplify = SimplifyMesh(tile[:,:])
	simplify.RemovePointsLessThanErr(1.)
	simplify.VisTris()
	print simplify.GetCurrentMesh()

