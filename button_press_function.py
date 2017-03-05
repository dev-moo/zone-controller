#!/usr/bin/env python

"""
Function/s that run when button is pressed on console
"""

import os


#MAC address of PC to wake up
MAC = "00:DE:AD:BE:EF:00"

def button_pressed():

    """
    This function is called when a button press is
    detected
	
	Send a magic packet to wake up a PC (WOL)
    """
    
    os.system("wakeonlan -i 10.1.1.255 " + MAC)
