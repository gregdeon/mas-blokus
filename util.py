import numpy as np

#takes a uint8 and produces the first player ID that matches
#100 is an error value
def bitstoid(bits):
    if bits == 0:
        return -1
    else:
        for i in range(8):
            if bits & 1 != 0:
                return i
            bits = bits >> 1
    if VERBOSE:
        print('ERROR: bitstoid received an invalid bitstring')
    return 100
bitstoid = np.vectorize(bitstoid)


def idtobits(id):
	if(id != 0):
		return 1 << (id - 1)
	else:
		return 0
idtobits = np.vectorize(idtobits)



#nice formatting for number printing
def print_num(num):
    return str(int(100*np.round(num,2))/100.0)