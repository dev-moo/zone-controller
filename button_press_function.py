#!/usr/bin/env python

"""
<<<<<<< HEAD
Process config file
=======
Function/s that run when button is pressed on console
>>>>>>> 2400a58dca71bdf1e487847a5312917e7034e85c
"""

import os


#MAC address of PC to wake up
<<<<<<< HEAD
MAC = "74:D4:35:B6:7A:7B"
=======
MAC = "00:DE:AD:BE:EF:00"
>>>>>>> 2400a58dca71bdf1e487847a5312917e7034e85c

def button_pressed():

    """
    This function is called when a button press is
    detected
<<<<<<< HEAD
    """
    
    os.system("wakeonlan -i 192.168.1.255 " + MAC)
=======
	
	Send a magic packet to wake up a PC (WOL)
    """
    
    os.system("wakeonlan -i 10.1.1.255 " + MAC)
>>>>>>> 2400a58dca71bdf1e487847a5312917e7034e85c
