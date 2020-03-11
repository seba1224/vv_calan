import time
from generator import Generator

class AnritsuGenerator(Generator):
    """
    Controls a signal generator source that uses Anritsu commands.
    """
    def __init__(self, instr, instr_info):
        Generator.__init__(self, instr, instr_info)
        
    def turn_output_on(self):
        """
        Turn on the output of the generator.
        """
        self.instr.write('RF1')
        time.sleep(self.sleep_time)

    def turn_output_off(self):
        """
        Turn off the output of the generator.
        """
        self.instr.write('RF0')
        time.sleep(self.sleep_time)

    def set_freq_hz(self, freq=None):
        """
        Set the generator output frequency. 
        :param freq: frequency to set in Hz.
        """
        if freq is None:
            freq = 1000000 * self.def_freq
        self.instr.write('F1 ' + str(freq) + ' H')
        time.sleep(self.sleep_time)

    def set_freq_mhz(self, freq=None):
        """
        Set the generator output frequency. 
        :param freq: frequency to set in MHz.
        """
        if freq is None:
            freq = self.def_freq
            return
        self.instr.write('F1 ' + str(freq) + ' MH')

    def set_power_dbm(self, power=None):
        """
        Set the generator output power. 
        :param power: power level to set in dBm.
        """
        if power is None:
            power = self.def_power
        self.instr.write('L1 ' + str(power + ' DM'))
        time.sleep(self.sleep_time)
