import numpy as np
from generator import *
import os
import time
import matplotlib.pyplot as plt
import struct
import ipdb
import E8364C




class lab_measure():
    
    def __init__(self,_fpga, freqs, powers, npoints=1024, gen_ip=['192.168.1.33', '192.168.1.34'], bw=67.5, VNA_IP='192.168.1.30',VNA_args=[50,10*10**3, 100]):
        """n_points = number of points you which to save per meas
           gen_ips = 2-list with their corresponding IP's
           freq = a list of 2 arrays with the frequencies in each step
           powers = a list of 2 arrays with the powers in each step
    
           **The 2 arrays in powers and freqs must have the same lenghtS
        """
        self.fpga = _fpga
        self.fpga.write_int('cnt_rst',0)
        self.bw = bw
        self.n_points = npoints
        self.signal_ip = gen_ip[0]
        self.ref_ip = gen_ip[1]
        self.vna_ip = VNA_IP
        self.signal_freq = freqs[0]
        self.ref_freq = freqs[1]
        self.signal_pow = powers[0]
        self.ref_pow = powers[1]
        self.vna_args = VNA_args
        self.set_gen_connection()
        input_status = self.check_lengths()
        if (input_status):
            raise ValueError('The powers and frequencies arrays must have the same length')
        input_status = self.check_max()
        if(input_status):
            raise ValueError('The power at the inputs must be less than -3dBm')
        
        self.set_gen_connection()
        self.set_channel()
        beg = raw_input('Start the measurement?[y/n]')
        if(beg=='y'):
            self.meas_data = self.make_meas()




    
    def set_gen_connection(self):
        #ipdb.set_trace()
        self.gen_signal = {'type':'visa',
                           'connection':'TCPIP::'+str(self.signal_ip)+'::INSTR',
                            'def_freq':50,
                            'def_power':-5}
        self.gen_ref =    {'type':'visa',
                           'connection':'TCPIP::'+str(self.ref_ip)+'::INSTR',
                           'def_freq':50,
                           'def_power':-5 }
        
        self.source_signal = create_generator(self.gen_signal)
        self.source_ref = create_generator(self.gen_ref)
        self.vna, self.rm = E8364C.connect(self.vna_ip)
            
    


    
    def check_lengths(self):
        #ipdb.set_trace()
        if(len(self.signal_freq)==len(self.signal_pow)==len(self.ref_freq)==len(self.ref_pow)):
            return 0
        else:
            return 1

    def check_max(self):
        if(max(self.signal_pow)>-3 or max(self.ref_pow)> -3):
            ans = raw_input('One power value is above the -3dBm recommended as inputs \nYou must have some sort of attenuation.. continue?[y/n]')
            if(ans =='y'):
                return 0
            else:
                return 1
        else:
            return 0


    def set_channel(self):
        #ipdb.set_trace()
        self.source_signal.set_power_dbm(self.signal_pow[0])
        self.source_signal.set_freq_mhz(self.signal_freq[0])
        self.source_ref.set_power_dbm(self.ref_pow[0])
        self.source_ref.set_freq_mhz(self.ref_freq[0])
        self.source_signal.turn_output_on()
        self.source_ref.turn_output_on()
        spect_A = struct.unpack('>8192Q', self.fpga.read('1_A2', 8192*8))
        spect_B = struct.unpack('>8192Q', self.fpga.read('1_B2', 8192*8))
        spect_A = 10*np.log10(np.array(spect_A)+1.)
        spect_B = 10*np.log10(np.array(spect_B)+1.)
        fft_freq = np.linspace(0, self.bw, 8192, endpoint=False)
        fig = plt.figure()
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        ax1.grid(); ax2.grid()
        ax1.set_title('Spectrum ZDOK0'); ax2.set_title('Spectrum ZDOK1')
        ax1.set_xlabel('[MHz]'); ax2.set_xlabel('MHz')
        ax1.set_xlim(0, self.bw); ax2.set_xlim(0, self.bw)
        ax1.set_ylim(30, 150); ax2.set_ylim(30, 150)
        
        ax1.plot(fft_freq, spect_A); ax2.plot(fft_freq, spect_B)
        arg_A = np.argmax(spect_A); arg_B = np.argmax(spect_B)
        print("Maximum values are located in:\n ZDOK0: %i (%.4f) \t ZDOK1: %i (%.4f)"%(arg_A, fft_freq[arg_A], arg_B, fft_freq[arg_B]))
        print("close the figure to continue")
        plt.show()
        chann2save = input('Which channel do you want to save?')
        self.fpga.write_int('addr2catch', chann2save)
        E8364C.correlator(self.vna,self.vna_args[0]*10**6, self.vna_args[1], self.vna_args[2])
        
        
        

        
    def make_meas(self):
        #ipdb.set_trace()
        filename = 'data_'+time.asctime().replace(" ", "")
        os.mkdir(filename)
        os.chdir(filename)
        self.fpga.write_int('mux_sel',1)
        self.fpga.write_int('n_points', self.n_points)
        
        #open files to write in
        f_a = file('PowA', 'a')
        f_b = file('PowB', 'a')
        f_phase = file('phase', 'a')
        f_vna_re = file('vna_re', 'a')
        f_vna_im = file('vna_im', 'a')
        ##begin the iterations
        self.source_signal.turn_output_on()
        self.source_ref.turn_output_on()
        start = time.time()
        pow_mean = np.zeros(len(self.signal_freq))
        pow_std = np.zeros(len(self.signal_freq))
        ang_mean = np.zeros(len(self.signal_freq))
        ang_std = np.zeros(len(self.signal_freq))
        vna_re_meas = np.zeros((len(self.signal_freq)))
        vna_im_meas = np.zeros(len(self.signal_freq))
        vna_ang =  np.zeros(len(self.signal_freq))
        fig = plt.figure()
        ax1 = fig.add_subplot(121)        
        ax2 = fig.add_subplot(122)
        ax1.set_ylim(-180,180)
        ax2.set_ylim(-180,180)
        ax1.set_title('roach')
        ax2.set_title('vna')
        x_lim = np.arange(len(self.signal_freq))
        ax1.set_xlim(0, len(self.signal_freq))
        ax2.set_xlim(0, len(self.signal_freq))        
        roach_plot, = ax1.plot(x_lim, ang_mean)
        vna_plot, = ax2.plot(x_lim, vna_ang)
        plt.ion()
        plt.show()
        
        for i in range(len(self.signal_freq)):
            self.source_signal.set_power_dbm(self.signal_pow[i])
            self.source_ref.set_power_dbm(self.ref_pow[i])
            self.source_signal.set_freq_mhz(self.signal_freq[i])
            self.source_ref.set_freq_mhz(self.ref_freq[i])
            self.fpga.write_int('reading_data',1)
            self.fpga.write_int('reading_data',0)
            time.sleep(0.5)  #in the model we need to put a register to save the value!!
            """
            for j in range(20):
                time.sleep(0.5)
                if(not self.fpga.read_int('meas_rdy')):
                    break
            if(j==20):
                print("Error at iteration="+str(i))
                pass
            """
            vna_data = E8364C.measure(self.vna)
            raw_A = self.fpga.read('PowA', self.n_points*8)
            raw_B = self.fpga.read('PowB', self.n_points*8)
            raw_phase = self.fpga.read('phase', self.n_points*16)
            f_vna_re.write(str(vna_data[0])+',')
            f_vna_im.write(str(vna_data[1])+',')
            f_a.write(raw_A)
            f_b.write(raw_B)
            f_phase.write(raw_phase)
            powA = 10*np.log10(struct.unpack('>'+str(self.n_points)+'Q', raw_A))
            powB = 10*np.log10(struct.unpack('>'+str(self.n_points)+'Q', raw_B))
            phase = struct.unpack('>'+str(2*self.n_points)+'q', raw_phase)
            re = phase[::2]
            im = phase[1::2]
            ang = np.rad2deg(np.arctan2(im,re))
            pow_mean[i] =np.mean(powA)-np.mean(powB)
            pow_std[i] = np.std(powA)+np.std(powB)
            ang_mean[i] = np.mean(ang)
            ang_std[i] = np.std(ang)
            vna_re_meas[i] = vna_data[1]
            vna_im_meas[i] = vna_data[0]
            vna_ang[i] = np.rad2deg(np.arctan2(vna_im_meas[i],vna_re_meas[i]))
            roach_plot.set_ydata(ang_mean)
            vna_plot.set_ydata(vna_ang)
        f_a.close()
        f_b.close()
        f_phase.close()
        f_vna_re.closee()
        f_vna_im.close()
        self.meas_data = [pow_mean, pow_std, ang_mean, ang_std, vna_re_meas, vna_im_meas]
        os.chdir('..')
        return self.meas_data











            



        
        
        
        
        
