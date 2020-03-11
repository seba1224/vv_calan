import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
from math import trunc
import time
import ipdb


class plot_data():
         
    def __init__(self, fpga, plots, chann=6069, freqs=[0, 67.5], bw=67.5):
        """ Plots an animation of the real time values (at the network speed refresh)
        plots_type is a list which may contain the following options:
            -spect0 : gives the full spectrum of ZDOK0 ADC
            -spect1 : gives the full spectrum of ZDOK1 ADC
            -re_full: gives the real part of the correlation of both ADC
            -im_full: gives the imaginary part of the correlation of both ADC
            -phase  : gives the phase in degrees between the two ADC
            -chann_pow : gives the relative power between the two input
                        in the channel given in chann
            -chann_corr_re: gives the real part of the correlation
                             of the channel given in chann
            -chann_corr_im: gives the imaginary part of the correlation
                            if the channel given in chann 
            -chann_phase: gives the relative phase between the two inputs
                    in the given in chann 
        
        chann: Its the channel that you want to look at.
        freqs:  A two value list [freq_init, freq_end], the first one is
                the begining of the interval that you want to look at, the
                second one is the end.
        bw: is the complete bandwith of the FFT.
        """

        self.fpga = fpga
        self.fpga.write_int('cnt_rst',0) #just in case
        self.plots = plots
        self.nplots = len(self.plots)
        self.chann = chann
        self.freq = freqs
        self.bw = bw
        self.fft_freq = np.linspace(0, bw, 2**13,endpoint=False)
        self.plot_map = {1:'11', 2:'12', 3:'22', 4:'22', 5:'23',
                         6:'23', 7: '33', 8:'33', 9:'33'}
        self.fig = plt.figure()
        self.axes = []
        self.data = [] 
        
        #generate a dict for the specification of each plot
        #the info is encoded in [title, y_label, x_label,(y_init, y_end), (x_init, x_end), [brams], data_type]
        self.plot_info = {'spect0':['Spectrum ZDOK0', '[dB]', '[MHz]',
                            (30, 180), (self.freq), ['1_A2'], '>8192Q'],
                          'spect1':['Spectrum ZDOK1', '[dB]', '[MHz]',
                            (30, 180), (self.freq), ['1_B2'], '>8192Q'],
                            're_full':['Real correlation', '', '[MHz]',
                                      (30,180), (self.freq), ['AB_re'], '>8192q'],
                            'im_full':['Imag correlation', '', '[MHz]',
                                      (30,180), (self.freq), ['AB_im'], '>8192q'],
                            'phase':['Relative Phase', ('['+u'\xb0'+']'), '[MHz]',
                                     (-180,180), (self.freq), ['AB_im', 'AB_re'], '>8192q'],
                            'chann_pow':['Relative Power at'+str(self.fft_freq[self.chann]),
                                         '[dB]','[MHz]',(-180,180), self.freq,
                                         ['PowA', 'PowB'], '>8192Q'],
                            'chann_phase':['Relative phase at'+str(self.fft_freq[self.chann]),
                                        ('['+u'\xb0'+']'), '[MHz]',(-180,180), (0,8191),
                                        ['phase'], '>16384q']}

        
        self.create_plots()
        anim = animation.FuncAnimation(self.fig, self.animate, blit=True)
        plt.show()
        

        
    def create_plots(self):
        self.data_type = []
        self.brams = []
        for i in range(self.nplots):

                axis = self.fig.add_subplot(self.plot_map[self.nplots]+str(i+1))
                info = self.plot_info[self.plots[i]]
                axis.grid()
                axis.set_title(info[0])
                axis.set_ylabel(info[1])
                axis.set_xlabel(info[2])
                axis.set_ylim(info[3])
                axis.set_xlim(info[4])
        
                self.axes.append(axis)
                ax_data, = axis.plot([],[], lw=2)
                self.data.append(ax_data)
                self.brams.append(info[-2])
                self.data_type.append(info[-1])
                

    def get_data(self):
        output = []
        for i in range(self.nplots):
            if(self.data_type[i]=='>8192Q'):
                if(len(self.brams[i])==2):
                    data1 = struct.unpack('>8192Q', self.fpga.read(self.brams[i][0], 8192*8))
                    data2 = struct.unpack('>8192Q', self.fpga.read(self.brams[i][1], 8192*8)) 
                    data = 10*(np.log10(np.array(data1+1.))-np.log10(np.array(data2+1.)))
                else:
                    data = struct.unpack('>8192Q', self.fpga.read(self.brams[i][0], 8192*8))
                    data = 10*np.log10(np.array(data)+1)
            if(self.data_type[i]=='>8192q'):
                if(len(self.brams[i])==2):
                    im = struct.unpack('>8192q', self.fpga.read(self.brams[i][0], 8192*8))
                    re = struct.unpack('>8192q', self.fpga.read(self.brams[i][1], 8192*8))
                    data = np.rad2deg(np.arctan2(im, re))
                else:
                    data = struct.unpack('>8192q', self.fpga.read(self.brams[i][0], 8192*8))

            if(self.data_type[i]=='>16384q'):
                phase = struct.unpack('>16384q',self.fpga.read(self.brams[i][0]),16384*8)
                re = phase[::2]
                im = phase[1::2]
                data = np.rad2deg(np.arctan2(im, re)) 
            output.append(data)
        return output

    
    def animate(self, i):
        dat = self.get_data()
        #ipdb.set_trace()
        for i in range(len(dat)):
            self.data[i].set_data(self.fft_freq, dat[i])
        return self.data










            
                            




        




















        
        

