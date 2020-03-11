#!/usr/bin/env python
# coding: utf-8

# In[1]:


import visa
import sys
import time;
from pyvisa.resources import MessageBasedResource
import numpy as np;



# connect
def connect(address='192.168.1.30'):
    '''
    address: the instruments address;
    function used to build communication with instrumentations.
    '''
    addr='TCPIP0::'+address+'::hpib7,16::INSTR'
    rm = visa.ResourceManager();
    print('the list of the instrumentations:',rm.list_resources());
    print('connect to the instruments');
    instr= rm.open_resource(addr);
    instr.write('*RST; *CLS;');
    instr.write('*IDN?')
    print('instrment information:',instr.read());
    print('initialize VNA...');
    instr.write('SYST:FPReset;');
    time.sleep(0.5)
    print('ready');
    instr.write('DISPlay:WINDow1:STATE ON;');
    instr.write('format:data ascii');
    instr.write('initiate:continuous off');
    instr.write('output:state off');
    
    
    return instr,rm;

def correlator(instr,f0,RBW,N_average=1,R='ab'):
    
    print(f0,RBW);
    
    instr.write("calculate1:parameter:define 'ch1_a', "+R); 
    
    instr.write("DISP:WIND:TRAC1:FEED 'ch1_a'");
    instr.write("sense1:sweep:mode continuous");
    
    instr.write('sense1:sweep:points 1');
    instr.write('sense1:frequency:center '+str(f0));    
    instr.write('sense1:bandwidth:resolution '+str(RBW));
    
    # average points
    instr.write('sense1:average:mode point');
    instr.write('sense1:average:count '+str(N_average));
    instr.write('sense1:average:state on');
    
    # sweep time
    instr.write('sense1:sweep:time:auto on');
    #instr.write('sense1:sweep:time 0.0001');
    instr.write('sense1:sweep:time?');
    print(instr.read())
    
    
# make a measurements;
def measure(instr):
    instr.write('initiate1;*wai');
    instr.write('*OPC?')
    instr.timeout=10000
    state=instr.read_ascii_values();
    instr.timeout=2000;
    instr.write('CALCulate1:DATA? SDATA');
    VALUE=instr.read_ascii_values()
    print(VALUE)
    return VALUE;




# In[2]:



    
if __name__ == "__main__":    
    #ratio(VNA,f0,RBW,Num);
    #a=sys.argv[1];
    #b=sys.argv[2];
    #c=sys.argv[3];
    address='192.168.1.30'
    f0=60*10**6;
    RBW=10*10**3
    Num=100;
    VNA,rm=connect(address);
    correlator(VNA,f0,RBW,Num);
    DATA=measure(VNA);
    #VNA.close();
    #rm.close()
    


# In[ ]:





# In[ ]:




