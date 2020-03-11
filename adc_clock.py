#!/usr/bin/env python

import argparse
from valon_synth import *
from collections import OrderedDict

# SYNTH_A = 0, SYNTH_B = 8
synth = {"A" : SYNTH_A, "B" : SYNTH_B}
lev_dict = OrderedDict()
lev_dict[-4] = 0; lev_dict[-1] = 3; lev_dict[2] = 6; lev_dict[5] = 8;

parser = argparse.ArgumentParser(description='Get and set Valon 5007 Syntheziser parameters (power, frequency, reference).')
parser.add_argument("-u", "--usb", dest="usb",
                   default="/dev/ttyUSB0", help="USB path (/dev/ttyUSBX).")
parser.add_argument("-s", "--synth", type=str, dest="synth", choices=["A",  "B"],
                   default = "B", help="Chosen synthesizer (A or B).")
parser.add_argument("-f", "--freq", type=int, dest="freq",
                   default=None, help="Set frequency (137.5-4400MHz).")
parser.add_argument("-l", "--lev", type=int, dest="level", choices=lev_dict.keys(),
                   default=None, help="Set power level. Valid levels {key : dBm}: " + 
                       ''.join(str(k) + ': ' + str(v) + 'dBm, ' for k,v in lev_dict.items()))
parser.add_argument("-i", "--int_ref", dest="int_ref", action="store_true",
                   help="set internal reference")
parser.add_argument("-e", "--ext_ref", dest="ext_ref", action="store_true",
                   help="set external reference")
args = parser.parse_args()

s = Synthesizer(args.usb)
try:
    synth_num = synth[args.synth]
except:
    print "Synth name error."
    exit()

synth_freq = s.get_frequency(synth_num)
synth_levl = s.get_rf_level(synth_num)
print "Frequency SYNTH_" + str(args.synth) + ": " + str(synth_freq) + "[MHz]"
print "RF level SYNTH_"  + str(args.synth) + ": " + str(synth_levl) + " (" + str(lev_dict[synth_levl]) + "dBm)"
# False = internal, True = external
print "Reference : " + ("external" if s.get_ref_select() else "internal")

if args.freq is not None:
    s.set_frequency(synth[args.synth], args.freq)
    synth_freq = s.get_frequency(synth_num)
    print "Updated frequency SYNTH_" + str(args.synth) + ": " + str(synth_freq) + "[MHz]"
    
if args.level is not None:
    s.set_rf_level(synth[args.synth], args.level)
    synth_levl = s.get_rf_level(synth_num)
    print "Updated power level SYNTH_" + str(args.synth) + ": " + str(synth_levl) + " (" + str(lev_dict[synth_levl]) + "dBm)"

if args.int_ref:
    s.set_ref_select(False)
    print "Updated reference to internal"
if args.ext_ref:
    s.set_ref_select(True)
    print "Updated reference to external"

s.flash()
