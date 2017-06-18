#!/usr/bin/env python

"""
Process config file
"""

import os


#MAC address of PC to wake up
MAC = "74:D4:35:B6:7A:7B"

def button_pressed():

    """
    This function is called when a button press is
    detected
    """
    
    os.system("wakeonlan -i 192.168.1.255 " + MAC)
