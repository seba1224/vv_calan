import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
from math import trunc
import time
import ipdb


class plot_data():
    """Class to create an animation
    """
    
    def __init__(self,_fpga,plots_types, chann=6069, _freqs=[0,67.5], bw=67.5 ):
        """ Plots an animation of the real time values (at the network speed refresh)
        plots_type is a list which may contain the following options:
            -spect0 : gives the full spectrum of ZDOK0 ADC
            -spect1 : gives the full spectrum of ZDOK1 ADC
            -re_full: gives the real part of the correlation of both ADC
            -im_full: gives the imaginary part of the correlation of both ADC
            -phase  : gives the phase in degrees between the two ADC
            -chann_pow : gives the relative power between the two input
                        in the channel given in chann
            -chann_corr: gives the real part of the correlation
                             of the channel given in chann
            
            -chann_phase: gives the relative phase between the two inputs
                    in the given in chann 
        
        chann: Its the channel that you want to look at.
        freqs:  A two value list [freq_init, freq_end], the first one is
                the begining of the interval that you want to look at, the
                second one is the end.
        bw: is the complete bandwith of the FFT.
    """
        self.fpga = _fpga
        self.fpga.write_int('cnt_rst',0)
        self.nplots = len(plots_types)
        self.plots_types = plots_types
        self.chann = chann
        self.freq = _freqs
        self.bw = bw
        self.fft_freq = np.linspace(0, bw, 2**13,endpoint=False)
        self.plot_map = {1:'11', 2:'12', 3:'22', 4:'22', 5:'23',
                         6:'23', 7: '33', 8:'33', 9:'33'}
        self.fig = plt.figure()
        self.axes = []
        self.data = []
        self.title = {'spect0':'Spectrum ZDOK0', 'spect1': 'Spectrum ZDOK1', 're_full':'Real Correlation', 'im_full':'Imag Correlation', 
                      'phase': 'Relative Phase','chann_pow':'Relative Power at '+str(self.fft_freq[self.chann]),
                      'chann_corr':'Correlation at '+str(self.fft_freq[self.chann]),
                      'chann_phase':'Relative phase at '+str(self.fft_freq[self.chann])}
        self.label_y = {'spect0':'[dB]', 'spect1': '[dB]', 're_full':'', 'im_full':'',
                      'phase': '['+u'\xb0'+']','chann_pow':'[dB]',
                      'chann_corr':'','chann_phase':'['+u'\xb0'+']'}
        
        self.label_x = {'spect0':'[MHz]', 'spect1': '[MHz]', 're_full':'[MHz]', 'im_full':'[MHz]',
                      'phase': '[MHz]','chann_pow':'',
                      'chann_corr_re':'', 'chann_corr_im':'','chann_phase':''}
        self.brams = {'spect0':'1_A2', 'spect1': '1_B2', 're_full':'AB_re', 'im_full':'AB_im',
                      'phase': ['AB_re','AB_im'] ,'chann_pow':['PowA','PowB'],
                      'chann_corr_re':'phase', 'chann_corr_im':'phase','chann_phase':'phase'}
        self.data_type = {'spect0':'>8192Q', 'spect1': '>8192Q', 're_full':'>8192q', 'im_full':'>8192q',
                      'phase': '>16384q','chann_pow':'>8192',
                      'chann_corr':'>16384q','chann_phase':'>8192Q'}
        self.create_plots()
        
        anim = animation.FuncAnimation(self.fig, self.animate, blit=True)
        plt.show()
        

    def create_plots(self):
        ##for the correlation could be a problem....
        #ipdb.set_trace()
        for i in range(self.nplots):
            axis = self.fig.add_subplot(self.plot_map[self.nplots]+str(i+1))
            axis.set_title(self.title[self.plots_types[i]])
            axis.set_ylabel(self.label_y[self.plots_types[i]])
            axis.set_xlabel(self.label_x[self.plots_types[i]])
            axis.grid()     
            axis.set_xlim(0, self.bw)
            axis.set_ylim(30, 180)
            ###we have to modify the xlim and ylim
            self.axes.append(axis)
            ax_data, = axis.plot([],[], lw=2)            
            self.data.append(ax_data)


    def get_data(self):
        output = []
        for i in range(self.nplots):
            if(type(self.brams[self.plots_types[i]])==list):
                ##TODO handle this option 

                output.append(np.linspace(0,67.5,8192))
                pass
            else:
                value = struct.unpack(self.data_type[self.plots_types[i]], self.fpga.read(self.brams[self.plots_types[i]],8192*8 ))
            if(self.data_type[self.plots_types[i]]=='>8192Q'):
                value = 10*np.log10(np.array(value)+1)
            if(self.data_type[self.plots_types[i]]=='>16384q'):
                re = value[::2]; im = value[1::2]
                value = np.rad2deg(np.arctan2(im, re))
            output.append(value)
        return output
    


    def animate(self,i):
        dat = self.get_data()
        #ipdb.set_trace()
        for i in range(len(dat)):
            self.data[i].set_data(self.fft_freq, dat[i])
        return self.data











        
    










    
