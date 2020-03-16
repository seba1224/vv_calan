import struct 
import numpy as np
import datetime
import h5py


def parse_raw(raw_file, n_readings):
	filename = str(datetime.datetime.now())	
	with h5py.File((filename+'.hdf5'), "w") as f:
		powA = f.create_dataset('PowA', (n_readings*8192,), dtype='Q')
		powB = f.create_dataset('PowB', (n_readings*8192,), dtype='Q')
		re = f.create_dataset('ABre', (n_readings*8192,), dtype='q')
		im = f.create_dataset('ABim', (n_readings*8192,), dtype='q')
		sec = f.create_dataset('seconds', (n_readings*8192,), dtype='I')
		frac_sec = f.create_dataset('frac_sec', (n_readings*8192,), dtype='I')
		raw_data = file(raw_file, 'r')
		for i in range(n_readings):
			A2_data = np.array(struct.unpack('>8192Q', raw_data.read(8192*8)))
			B2_data = np.array(struct.unpack('>8192Q', raw_data.read(8192*8)))
			phase = np.array(struct.unpack('>16384q', raw_data.read(8192*16)))
			re_data = phase[::2]
			im_data = phase[1::2]
			time = np.array(struct.unpack('>16384I', raw_data.read(8192*8)))
			sec_data = time[::2]
			frac_data = time[::2]
			powA[8192*i:8192*(i+1)] = A2_data
			powB[8192*i:8192*(i+1)] = B2_data
			re[8192*i:8192*(i+1)] = re_data
			im[8192*i:8192*(i+1)] = im_data
			sec[8192*i:8192*(i+1)] = sec_data
			frac_sec[8192*i:8192*(i+1)] = frac_data
		raw_data.close()
			
		


