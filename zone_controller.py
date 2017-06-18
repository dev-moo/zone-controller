#!/usr/bin/env python

""""

Service to provide a UDP interface to a A/C zone controller

UDP service <==> Raspberry PI <==>
USB Connection <==> Arduino <==> Zone Controller

"""

#Import modules

import serial
import socket
import select
import json
import os
import sys
import logging
import time
from time import sleep, strftime

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)

import get_config
import button_press_function


#GLOBALS

CONFIG_FILE_NAME = 'zone_controller.conf'

CONFIG = get_config.get_config(CONFIG_FILE_NAME)

LOGFILE = CONFIG.get('General', 'logfile')
SERVER_IP = CONFIG.get('General', 'serverIP')
SERVER_PORT = int(CONFIG.get('General', 'serverPort'))
ARDUINO_ADDRESS = CONFIG.get('General', 'arduinoAddress')


#Enable debugging
DBG_ON = False
logging.basicConfig(level=logging.DEBUG, filename=LOGFILE)


#Commands for ZC
ZC_CMD_GET = 'G'
ZC_CMD_SET = 'S'
ZC_CMD_CHECK = 'C'

ZC_ALIVE_RESPONSE = 'OK'

LASTGET_TTL = 10 #30 seconds CurrentStatus Time To Live
LASTSET_TTL = 20 #Time for ZC to change state in seconds


#Conversion Maps
START_SEQUENCE = '2521'
ZONE_NAMES = ({'Zone1': 'Living', 'Zone2': 'Kitchen', 'Zone3': 'Bedroom 1',
               'Zone4': 'Bedroom 2', 'Zone5': 'Office'})

#Map zone code from zc to a name
ZONE_CODES = ({'31': 'Zone1', '32': 'Zone2', '33': 'Zone3', '34': 'Zone4',
               '35': 'Zone5', '36': 'Zone6'})


#39 = Off changing to low
#33 = low changing to high
#34 = high changing to off
#38 = ?
#41 = ?
#31 = ?

#map setting code from zc to a name
SETTING_CODES = {'32': 'Off', '35': 'Off', '34': 'Off', '41': 'Low',
                 '42': 'Low', '38': 'Low', '39': 'Low', '30': 'High',
                 '31': 'High', '33': 'High'}

#STATUS_CODES = {'30': 'Set', '34': 'Changing'}

#Used to determine number of pulses required to get to a desired state
PULSE_TABLE = {'Off': {'Off': 0, 'Low': 1, 'High': 2},
               'Low': {'Off': 2, 'Low': 0, 'High': 1},
               'High': {'Off': 1, 'Low': 2, 'High': 0}}


#Place to store current settings of zone controller
STATUS_CONTAINER = {'Zone1': '', 'Zone2': '', 'Zone3': '', 'Zone4': '',
                    'Zone5': '', 'Zone6': '', 'LastGet': '', 'LastSet': ''}

CURRENT_STATUS = STATUS_CONTAINER #Place to store current zc status



#Output to log file
def log_event(event):

    """Write to log file"""

    tstamp = strftime("%Y%m%d%H%M%S")

    dbg(event)

    log_file = open(LOGFILE, 'a')
    log_file.write('"' + str(tstamp) + '","' + str(event) + '"\r\n')
    log_file.close()


#Output to console
def dbg(event):

    """Write to console"""

    if DBG_ON:
        tstamp = strftime("%Y%m%d%H%M%S")
        print str(tstamp) + ',' + str(event)




def parse_input(serial_data):

    """Convert data returned from zone controller into Dictionary"""

    global CURRENT_STATUS

    status = STATUS_CONTAINER

    zone_bytes = serial_data.split(START_SEQUENCE)

    for zone in zone_bytes:
        if zone != "":

            dbg(zone)

            zone_name = ''
            zone_setting = ''

            if zone[:2] in ZONE_CODES:
                zone_name = ZONE_CODES[zone[:2]]

            if zone[2:4] in SETTING_CODES:
                zone_setting = SETTING_CODES[zone[2:4]]

            if zone_name != '':
                status[zone_name] = zone_setting


    status['LastGet'] = time.time()
    CURRENT_STATUS = status

    dbg("ZC Data parsed to:")
    dbg(status)

    return status



def get_settings():

    """Query zone controller for current status"""

    #Reuse previously collected data if its recent
    if CURRENT_STATUS['LastSet'] != '':
        if time.time() - CURRENT_STATUS['LastSet'] < LASTSET_TTL:
            dbg('LAST_SET has not expired. Not querying ZC, Sending cached data')
            return CURRENT_STATUS

    #Reuse previously collected data if its recent
    if CURRENT_STATUS['LastGet'] != '':
        if time.time() - CURRENT_STATUS['LastGet'] < LASTGET_TTL:
            dbg('LAST_GET has not expired. Not querying ZC, Sending cached data')
            return CURRENT_STATUS


    #Send get status command to ZC
    USB.flush()
    USB.write(ZC_CMD_GET)

    sleep(1)

    #Read in response
    usb_data = USB.readline()

    #Throw some kind of error
    if usb_data == 'FAILED':
        log_event("Unable to query zone controller")
        return CURRENT_STATUS

    usb_data = usb_data.strip('\r''\n')

    dbg("Zone Controller Replied with: " + usb_data)

    return parse_input(usb_data)



def calculate_pulses(current_setting, desired_setting):

    """Return number of pulses required to get from the current state to a desired state """

    pulses = PULSE_TABLE[current_setting]
    return pulses[desired_setting]



def operate_zone_controller(zone, setting, c_status):

    """Parse a command and send it to zone controller"""

    #Check if a change is actually required
    if setting == c_status[zone]:
        dbg('o_z_c: Function called when no change is required')
        return False

    #Sanity check the zone argument
    if zone not in ZONE_NAMES:
        dbg('o_z_c: Function called with a zone that doesnt exist: ' + zone)
        return False

    #Check we know the current setting of the zone
    if c_status[zone] == '':
        dbg('o_z_c: Unable to determine current setting for ' + zone)
        return False


    #Command string
    output = ZC_CMD_SET

    #Loop through each Code - ZoneName in dict
    for code, name in ZONE_CODES.items():
        if name == zone:

            #Get number of pulses to send on output
            pulses = calculate_pulses(c_status[zone], setting)

            #Generate command string
            for i in range(0, pulses):
                output += code.decode("hex")

            dbg(zone + " is currently set to " + c_status[zone] +
                " and needs to be changed to " + setting)


    dbg("Output to ZC: " + output)

    #Write command string to output
    USB.write(output)

    return True



def set_settings(cmd):

    """Take a command from network, convert it and send to zone controller"""

    global CURRENT_STATUS

    cs = None

    if CURRENT_STATUS['LastSet'] != '' and time.time() - CURRENT_STATUS['LastSet'] < LASTSET_TTL:
        cs = CURRENT_STATUS
    else:
        cs = get_settings()

    r = operate_zone_controller(cmd['Zone'], cmd['Value'], cs)

    if r:
        CURRENT_STATUS[cmd['Zone']] = cmd['Value']
        CURRENT_STATUS['LastSet'] = time.time()



def read_usb():

    """Read data on USB serial"""

    usbdata = USB.readline()
    usbdata = usbdata.strip('\r''\n')

    if usbdata == 'ButtonPressed':
        dbg("Button has been pressed")
        button_press_function.button_pressed()


        
def check_serial(arduino):
    
    """Check Arduino is responsive"""
    
    arduino.flush()
    arduino.write(ZC_CMD_CHECK)
    
    sleep(1)

    #Read in response
    usb_data = arduino.readline()
    usb_data = usb_data.strip('\r''\n')
    
    if usb_data == ZC_ALIVE_RESPONSE:
        dbg("Serial check passed")
        return True
    
    dbg("Serial check failed")
    
    return False

    
    
def setup_udp_socket(s_ip, s_port):

    """Create UDP socket to communicate on the network"""

    sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sck.setblocking(0)
    server_address = (s_ip, s_port)

    dbg('starting up on %s port %s' % server_address)

    # Bind the socket to the port
    while True:
        try:
            sck.bind(server_address)
            break
        except:
            logging.exception("Exception Occured:")
            sleep(5)

    return sck



def connect_arduino(address):
    
    """Create usb serial connection to Arduino"""
    
    arduino = False
    
    logging.info("Connecting to Arduino")
    
    #Serial connection to Arduino (zone controller)
    for x in xrange(6):
        try:
            arduino = serial.Serial(address, 9600, timeout=1)
            if check_serial(arduino):
                break
        except serial.SerialException:
            logging.exception("Exception Occurred:")
            log_event('Error connecting to Arduino')
            sleep(5)
            
    if not arduino:
        logging.exception("Unable to connect to Arduino")
        log_event('Unable to connect to Arduino, stopping service')
        exit()
    
    if not check_serial(arduino):
        logging.warning("Arduino is connected but not responding")
        log_event('Arduino is connected but not responding, stopping service')
        exit()    
        
    logging.info("Arduino is connected")
        
    return arduino
    
    
log_event("Starting Zone-Controller service")

SOCK = setup_udp_socket(SERVER_IP, SERVER_PORT)

USB = connect_arduino(ARDUINO_ADDRESS)


#Inputs to monitor
inputs = [SOCK, USB]


#Main Loop
try:
    while inputs:

        # Wait for at least one of the sockets to be ready for processing
        readable, writable, exceptional = select.select(inputs, [], inputs)

        # Handle inputs
        for s in readable:

            #UPD Socket
            if s is SOCK:

                data, address = SOCK.recvfrom(4096)

                #print >>sys.stderr, 'received %s bytes from %s' % (len(data), address)
                dbg('%s received from %s' % (data, address))


                if data:
                    try:
                        command = json.loads(data)

                        if command['Operation'] == "GET":

                            dbg("")
                            dbg("GET command received")

                            #Get settings and encode to JSON
                            json_str = json.dumps(get_settings())

                            sent = SOCK.sendto(json_str, address)

                            dbg('sent %s bytes back to %s' % (sent, address))
                            dbg("")

                        if command['Operation'] == "SET":

                            dbg("")
                            dbg("SET command received")

                            set_settings(command)

                            dbg("")

                    except:
                        logging.exception("Exception Occurred:")
                        dbg('Error receiving UPD JSON data')
                        log_event("An Exception Occured")

            #USB Serial
            elif s is USB:
                try:
                    read_usb()
                except serial.SerialException:
                    logging.exception("Exception Occurred:")
                    log_event("Serial Exception Occured")
                    if USB in inputs: inputs.remove(USB)
                    USB = connect_arduino(ARDUINO_ADDRESS)
                    inputs.append(USB)

        
        if not check_serial(USB):
            pass
            #USB = connect_arduino(ARDUINO_ADDRESS)
        
except:
    logging.exception("Fail:")
