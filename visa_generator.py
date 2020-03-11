import time
from generator import Generator

class VisaGenerator(Generator):
    """
    Controls a signal generator source that complies to Visa command
    standards.
    """
    def __init__(self, instr, instr_info):
        Generator.__init__(self, instr, instr_info)
        
    def turn_output_on(self):
        """
        Turn on the output of the generator.
        """
        self.instr.write('outp on')
        time.sleep(self.sleep_time)

    def turn_output_off(self):
        """
        Turn off the output of the generator.
        """
        self.instr.write('outp off')
        time.sleep(self.sleep_time)

    def set_freq_hz(self, freq=None):
        """
        Set the generator output frequency. 
        :param freq: frequency to set in Hz.
        """
        if freq is None:
            freq = 1000000 * self.def_freq
        self.instr.write('freq ' + str(freq))
        time.sleep(self.sleep_time)

    def set_freq_mhz(self, freq=None):
        """
        Set the generator output frequency. 
        :param freq: frequency to set in MHz.
        """
        if freq is None:
            self.set_freq_hz()
            return
        self.set_freq_hz(1000000 * freq)

    def set_power_dbm(self, power=None):
        """
        Set the generator output power. 
        :param power: power level to set in dBm.
        """
        if power is None:
            power = self.def_power
        self.instr.write('power ' + str(power))
        time.sleep(self.sleep_time)
