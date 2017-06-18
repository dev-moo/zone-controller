#!/usr/bin/env python

"""
<<<<<<< HEAD
Process config file
=======
Function/s that run when button is pressed on console
>>>>>>> refs/remotes/origin/master
"""

import os


#MAC address of PC to wake up
<<<<<<< HEAD
MAC = "74:D4:35:B6:7A:7B"
=======
MAC = "00:DE:AD:BE:EF:00"
>>>>>>> refs/remotes/origin/master

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
>>>>>>> refs/remotes/origin/master
