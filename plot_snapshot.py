import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
import numpy as np
import ipdb

class snapshot():
    def __init__(self, _fpga):
        self.fpga = _fpga
        self.fpga.write_int('snap_trig',1)
        self.x_axis = range(2**14)
        self.data = []
        self.fig = plt.figure()
        ax0 = self.fig.add_subplot(121)
        ax1 = self.fig.add_subplot(122)
        ax0_data, = ax0.plot([],[], lw=2)
        ax1_data, = ax1.plot([],[], lw=2)
        self.data.append(ax0_data)
        self.data.append(ax1_data)
        ax0.grid()
        ax1.grid()
        ax0.set_title('ZDOK 0')
        ax1.set_title('ZDOK 1')
        ax0.set_xlim([0, 2**10])
        ax1.set_xlim([0, 2**10])
        ax0.set_ylim([-130, 130])
        ax1.set_ylim([-130, 130])
        ani = animation.FuncAnimation(self.fig, self.animate, blit=True)
        plt.show()
        
        
    def animate(self,i):
        snap_data0 = struct.unpack('>16384b',self.fpga.snapshot_get('adcsnap0', man_trig=True, man_valid=True)['data'])
        snap_data1 = struct.unpack('>16384b',self.fpga.snapshot_get('adcsnap1', man_trig=True,man_valid=True)['data'])
        #ipdb.set_trace() 
        self.data[0].set_data(self.x_axis, snap_data0)
        self.data[1].set_data(self.x_axis, snap_data1)
        return self.data

