import visa, socket

class Generator():
    """
    Generic class to control signal generators.
    """
    def __init__(self, instr, instr_info): 
        self.instr = instr
        self.sleep_time = 0.1
        try:
            self.def_freq = instr_info['def_freq']
        except KeyError:
            self.def_freq = 10
        try:
            self.def_power = instr_info['def_power']
        except KeyError:
            self.def_power = -100

        # set default parameters
        self.set_freq_mhz()
        self.set_power_dbm()
        
    def close_connection(self):
        self.instr.close()

def create_generator(instr_info):
    """
    Create the appropiate generator object given the instr_info
    dictionary.
    :param instr_info: generator instrument info dictionary.
        The instr_info format is:
        {'instr_type' : type of generator, defined by the 
            command keywords.
         'connection' : type of connection in Visa format.
            See https://pyvisa.readthedocs.io/en/stable/names.html
         'def_freq'   : Default frequency to use when not specified 
            (in MHz).
         'def_power'  : Default power level to use when not specified
            (in dBm).
        }
    :param print_msgs: True: print command messages. False: do not.
    :return: Generator object.
    """
    from visa_generator import VisaGenerator
    from anritsu_generator import AnritsuGenerator
    
    # check if instrument is proper or simulated
    if instr_info['type'] == 'sim':
        rm = visa.ResourceManager('@sim')
    else:
        rm = visa.ResourceManager('@py')
    
    # try to connect to instrument
    try:
        instr = rm.open_resource(instr_info['connection'])
    except socket.error:
        print("Unable to connect to instrument " + instr_info['connection'])
        exit()

    # create the proper generator object with the correct inctruction keywords
    if instr_info['type'] == 'visa':
        return VisaGenerator(instr, instr_info)
    elif instr_info['type'] == 'anritsu':
        return AnritsuGenerator(instr, instr_info)
    else: # default to visa
        return VisaGenerator(instr, instr_info)
        
