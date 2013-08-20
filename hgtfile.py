import struct, zipfile
import numpy as np
import matplotlib.pyplot as plt

def OpenHgt(fina):

	z = zipfile.ZipFile(fina, "r")
	fili = z.namelist()
	fi = z.read(fili[0])
	l = struct.calcsize("<h")
	assert len(fi) % l == 0
	numPts = len(fi) / l
	sideLen = int(numPts ** 0.5)
	assert sideLen * sideLen == numPts

	data = np.empty((sideLen, sideLen), dtype=np.int16)
	for count in range(len(fi)/l):
		v = struct.unpack_from(">h", fi, count * l)[0]
		#print off / l, len(fi) / l, v
		data[count / sideLen, count % sideLen] = v

	print data.min(), data.max()

	imgplot = plt.imshow(data)
	plt.show()

if __name__=="__main__":

	OpenHgt("N51E001.hgt.zip")

