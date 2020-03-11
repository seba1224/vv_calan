import corr 
import time
import os
from plot_snapshot import snapshot
import telnetlib
import ipdb
from meas import lab_measure
from plots import plot_data



class calan_vv(object):    
    def __init__(self, roachIP, bof_path, valon_freq):
        self.IP = roachIP
        self.bof = bof_path
        self.valon_freq = valon_freq/2
        self.fpga_clk = self.valon_freq/8
        self.bw = self.fpga_clk/2.
        self.fpga = corr.katcp_wrapper.FpgaClient(self.IP)
        self.fft_size = 2**14
        self.channels = 2**13
        self.n_acc = 10

    def upload_bof(self):
        """ upload the bof file to the ROACH
        """
        self.fpga.upload_program_bof(self.bof, 3000)
        time.sleep(1)
    


    def set_integ_time(self, integ_time=1.2*10**-3):
        """ set the integration time,
            integ_time = integration time in seconds
        """
        chann_period = 2.**14/(self.fpga_clk*10**6) #
        self.n_acc = int(integ_time/chann_period)+1
        if(self.n_acc>2**14-2):
            print("The accumulation could overflow, carefull look at the spectrum..")
        self.fpga.write_int('acc_len',self.n_acc)
        self.fpga.write_int('cnt_rst',1)
        self.fpga.write_int('cnt_rst',0)
        print("integration time set to: %.4f [ms]"%(self.n_acc*chann_period*10**3))
        
    

    def init_vv(self, integ_time=1.2*10**-3):
        """initialize the vector voltmeter registers
        """
        self.fpga.write_int('cnt_rst',1)
        self.set_integ_time(integ_time)
        self.fpga.write_int('cnt_rst',0)

        
        
    def init_timestamp(self, unlock_error=10**-4):
        """initialize the timestamp model
            unlock_error = the varition in seconds to rise a
            unlock flag
        """
        T = 10**-2 #bit time of IRIGB00
        sec_factor = 0.75                               #security factor (could be higher, but this value works..)
        irig_pos_id = 0.8*T*self.fpga_clk*10**6*sec_factor
        irig_1 = 0.5*T*self.fpga_clk*10**6*sec_factor
        irig_0 = 0.2*T*self.fpga_clk*10**6*sec_factor
        
        print('writing timestamp variables.....')
        
        #those are the durations of every symbol in IRIG
        self.fpga.write_int('IRIG_irig_pos_id', irig_pos_id)
        self.fpga.write_int('IRIG_irig_1', irig_1)
        self.fpga.write_int('IRIG_irig_0', irig_0)
    
        
        
        self.fpga.write_int('IRIG_sel_ind',0)           #1 only to debbugg the irig_read fsm
        
        #settings for the debouncer fsm
        self.fpga.write_int('IRIG_waiting_in_vain', 20) #cycles that the gpio values may vary until sets to one
        self.fpga.write_int('IRIG_threshold', 20)       #cycles that the gpio values may vary until sets to zero
        self.fpga.write_int('IRIG_top_count', 100)      #the number of symbols of the first data frame, for debbuging only
        self.fpga.write_int('IRIG_bott_count', 100)     #the number of symbols of the dataframe, for debbuging only
        
        
        #set upper and lower limit of seconds that the timestamp
        #could vary to rise the flag of unlocking
        self.fpga.write_int('IRIG_frec_uplim', int(self.fpga_clk*10**6*(1+unlock_error)))   
        self.fpga.write_int('IRIG_frec_downlim', int(self.fpga_clk*10**6*(1-unlock_error))) 
        
        ##with the previous registers set up, we obtain the time from the master clock
        self.calibrate_timestamp()
        

    def calibrate_timestamp(self):
        """Get the time from the master clock
        """
        #reset the fsm to a known state
        self.fpga.write_int('IRIG_hrd_rst', 1)
        time.sleep(1)
        self.fpga.write_int('IRIG_hrd_rst', 0)
            
        #start the calibration
        self.fpga.write_int('IRIG_cal',1)
        time.sleep(1)
        self.fpga.write_int('IRIG_cal',0)
            
        #wait until the first frame is detected and received
        print('waiting for the master clock data...')
        time.sleep(3)
        for i in range(5):
            time.sleep(1)
            aux = self.fpga.read_int('IRIG_terminate')
            if(aux == 1):
                break
            
        if(i==4):
            print('There might be a problem..its everything connected?')
            ans = raw_input('Do you want to try the connection again?(y/n)')
            if(ans=='y' or ans=='yes'):
                self.calibrate_timestamp()
            else:
                return
        else:
            #The first second is always over the upper lim, and the second its always below the lower lim because
                # the fraction counter initialize only when the calibration is over. 
                #From the third second the system is stable, so we rest the unlock flag.
            time.sleep(3)
            self.fpga.write_int('IRIG_try_again',1)
            self.fpga.write_int('IRIG_try_again',0)
                 
            print('Timestamp calibration finished :D')
            return 

        
    def get_hour(self):
        """Translate the time from seconds of a year
        to day/hour/minutes/seconds
        """
        toy = self.fpga.read_int('secs')
        days = int(toy/(24.*3600))
        hours =int((toy%(24.*3600))/3600)
        minutes = int((toy%(24.*3600)%3600)/60)
        secs = toy%(24.*3600)%3600%60
        out = str(days)+'day'+str(hours)+':'+str(minutes)+':'+str(secs)
        print(out)
        return out


    def get_unlock(self):
        """ return 1 if the timestamp is unlocked
            return 0 if the timestamp is locked
        """
        out = self.fpga.read_int('unlock')
        return out

    
    def adc_snapshot(self):
        """Plot animation of the ADC snapshot
        """
        snapshot(self.fpga)

    
    def ppc_upload(self, file_path='ppc_save'):
        """Upload the required files to the ppc in the ROACH
        """
        user = 'root'
        self.tn = telnetlib.Telnet(self.IP)         
        self.tn.read_until("login: ")
        self.tn.write(user + "\n")
        self.tn.read_very_eager()
        #ipdb.set_trace()
        time.sleep(1)
        self.tn.write('cd /var/tmp\n')
        self.tn.read_very_eager()
        for i in range(5):
            self.tn.write('nc -l -p 1234 > ppc_save \n')
            os.system('nc -w 3 '+str(self.IP)+' 1234 < '+file_path)
            time.sleep(1) 
            self.tn.read_very_eager()
            self.tn.write("ls\n")
            time.sleep(0.5)
            ans = self.tn.read_very_eager()
            if(ans.find("ppc_save")!=-1):
                break
        
        if(i==4):
            raise RuntimeError('The file couldnt get upload..')
        time.sleep(0.5)
        self.tn.read_very_eager()
        self.tn.write('chmod +x ppc_save \n')
        time.sleep(0.5)
        self.tn.read_very_eager()
        self.tn.write('touch save \n')
        self.tn.read_very_eager()
        self.tn.close()

    def ppc_meas(self, chann=6069 ,duration=30):
        """Measure and save the data in the PowerPC in the roach
           duration=time of the complete measure, in minutes 
        """
        ###TODO: check if some registers must be cleaned before...
        self.fpga.write_int('addr2catch', chann)                       #select the channel to save in the ppc
        bram_addr = 8192.
        bram_period = self.fft_size*bram_addr*self.n_acc/(self.fpga_clk*10**6)*2 #we have two banks
        read_cycles = int(duration*60./bram_period)
        user = 'root'
        self.tn = telnetlib.Telnet(self.IP)
        self.tn.read_until("login: ")
        self.tn.write(user + "\n")
        time.sleep(0.5)
        self.tn.read_very_eager()
        time.sleep(1)
        self.tn.write('cd /var/tmp\n')
        time.sleep(0.5)
        self.tn.read_very_eager()
        self.tn.write('./ppc_save '+str(read_cycles+1)+'\n') #TODO:check the time consistency, ie if it could run without the connection
        time.sleep(0.5)
        print(self.tn.read_very_eager())

    
    
    def ppc_download(self, pc_IP):
        """Download the saved data to a computer
        """
        user = 'root'
        self.tn = telnetlib.Telnet(self.IP)
        self.tn.read_until("login: ")
        self.tn.write(user + "\n")
        time.sleep(1)
        self.tn.read_very_eager()
        self.tn.write('cd /var/tmp\n')
        self.tn.read_very_eager()
        ipdb.set_trace()
        os.system('nc -l -p 1234 > data &') ##there is a bugg here, the terminal hangs up...REVIEW!!!
        self.tn.write('nc -w 3 '+str(pc_IP)+' 1234 < save')
    




    def calibration(self, load=0, man_gen=0, ip_gen='192.168.1.33', filename='cal'):
        """This function makes the calibration of the ROACH more 
        understandable; you have to had installed the package 
        calandigital (https://github.com/FrancoCalan/calandigital)
        if you only want to make mcmm set load at 1
        if you want to manually set the generator set man_gen=1
        ip_gen = generator IP, to use in this mode the generator must
                 support visa commands
        filename = if load=1 the load dir, if load=0 the saving dir


            -Sidenote: a common failure is to set bad the bw and it throws
            an error of representation
        """
        parameter = "calibrate_adc5g.py"
        parameter += " -i "+str(self.IP)
        if(man_gen==0):
            parameter += " -g "+str(ip_gen)
            parameter += " -gf "+str(10)
            parameter += " -gp "+str(-3)
        parameter += " -psn -psp"
        parameter += " -bw "+str(self.valon_freq)
        parameter += " -s0 adcsnap0"
        parameter += " -s1 adcsnap1"
        parameter += " -ns 1000"
        if(load==0):
            parameter += " -dm -di -do"
            parameter += " -cd "+str(filename)
        if(load==1):
            parameter += " -dm -li -lo"
            parameter += " -ld "+str(filename)
        print(parameter)    
        os.system(parameter)
        
    def synchronization(self):
        ##TODO...
        return
    
    


    def adc_freq(self, new_freq, port=1):
        """
            To use this function is necessary to be connected 
            to the USB port of the valon
            new freq: Its the sampling frequency of the ADC's
            port: which port we are programming, 0 means A and 1 means B
            **the actual clock that is programmed is the half of that value,
             beacause the ADC take a sample at the rising and falling edge
        """
        parameter = "python adc_clock.py -f" + str(int(new_freq/2))
        if(port):
            parameter += ' -s B'   #check if the B port is really the good one
            os.system(parameter)
            self.valon_freq = new_freq/2
            self.fpga_clk = self.valon_freq/8
            self.bw = self.fpga_clk/2
            #you should reset the registers and re calibrate the timestamp
        else:
            parameter += ' -s A'
            os.system(parameter)
            

    def adc_reference(self, ext=1):
        """To use this function is necessary to be connected 
            to the USB port of the valon
            Function to change the reference of the valon
            ext=1 --->external reference
            ext=0 --->internal reference
        """
        parameter = "python adc_clock.py "
        if(ext):
            parameter += '-e'   
        else:
            parameter += '-i'
        os.system(parameter)
        
    def plots(self, plots=['spect0','spect1'],chann=6069, freq=[0,67.5],bw=67.5):
        """
        Plot an animation of the real time values (at the network speed refresh)
        Parameters:
        plots is a list which may contain the following options:
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
        plot_data(self.fpga, plots, chann, freq, bw)
            





            
    
        




            


