
import struct

if __name__=="__main__":

	fi = open("/home/tim/Downloads/Gb_england_surrey_europe_2.obf","rb")
	print map(hex, struct.unpack_from("BBBB", fi.read(), 0))

