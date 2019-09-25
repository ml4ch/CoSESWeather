#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This software is part of the CoSESWeather project.
CoSESServer.py runs the Server on the RevPi that communicates with the CONTROLLINO (µC) and collects the acquired sensor data.
This software interfaces the data acquisition unit and presents one of the core elements of the CoSESWeather Station.
"""

import sys
import os
import os.path
import errno
import subprocess
import socket
import time
import datetime
import threading
import traceback
import requests
import ConfigParser


__author__ = "Miroslav Lach"
__copyright__ = "Copyright 2019, MSE"
__version__ = "1.0"
__maintainer__ = "Miroslav Lach"
__email__ = "miroslav.lach@tum.de"


# Path to the CoSESWeather.ini file
path_ini = r'/opt/CoSESWeather/CoSESWeather.ini'
# Path to the user_notification.txt file
path_contacts = r'/opt/CoSESWeather/user_notification.txt'

# Define connection parameters
host = ''
port = 7785

# Define Controllino commands
CMD_HeartBeat_char = '#'
CMD_RESET_CONTROLLINO = 'a'
# CMD_RESTART_SYSTEM = 'b'  # currently not used

# Define HeartBeat and Timeout parameters
HeartBeatControllinoReply_char = '*'
t_HeartBeatRate = 7  # Send a HeartBeat e.g. 7 = one HeartBeat every 7 seconds
HeartBeats_missed_TIMEOUT = 2  # System recovery measures will be taken if more than 2 HeartBeats have been ignored
t_clientTimeout = 120  # Timeout for incoming connections in seconds (waiting for client to connect to the server)

# General
version = 'v1.0'
RevPiServerLaunched = False


def AliveCheckerThread(inst):
    """
    Revives the connection and restarts the server thread
    :param inst: Instance object
    :return: --
    """
    while True:
        if inst.ReviveConnection:
            inst.ReviveConnection = False
            inst.log_event('[CoSESServer] Reviving connection ...')
            time.sleep(5)
            inst.start_server()
        time.sleep(2)  # slow down loop to decrease CPU usage!


def UpdateNotificationFileThread(inst):
    """
    Updates the user_notification.txt file and delete status file once every 12 hours
    :param inst: Instance object
    :return: --
    """
    while True:
        inst.update_notification_file()
        time.sleep(43200)  # run every 12 hours
        inst.delete_status_file()


def AdminCommandCheckerThread(inst):
    """
    Checks for admin commands to be executed (submitted by CoSESWeather-App admin users)
    :param inst: Instance object
    :return: --
    """
    while True:
        if not inst.isServerRestarting:
            data_php = {"p_mode": 14}
            php_response = requests.post(inst.php_path, data=data_php)  # Requesting admin commands
            try:
                php_response = php_response.json()
            except Exception:
                php_response = php_response.text

            try:  # ok?
                if '__SUCCESS;' in php_response[0]:  # php response ok
                    del php_response[0]
                    msg = '[CoSESServer] Executing admin command: '
                    if 'Microcontroller reset' in php_response[0]['cmd']:  # reset Controllino
                        msg += 'Microcontroller reset ...'
                        inst.send_command(CMD_RESET_CONTROLLINO)
                    elif 'System restart' in php_response[0]['cmd']:  # restart system
                        msg += 'System restart ...'
                        inst.send_command(CMD_RESET_CONTROLLINO)  # reset Controllino
                        inst.restart_system()  # reboot RevPi
                    inst.log_event(msg)
                else:
                    if '_NO_COMMANDS;' in php_response:  # no admin commands waiting for execution
                        pass
                    else:
                        message = '[- Warning -] Database Error occurred! Admin Log could not be fetched! ' \
                                  'PHP Script returned: ' + str(php_response)
                        inst.log_event(message)
                        inst.send_notification(message)
                        inst.generate_status_file('Email notification sent by server script')
            except Exception:  # unexpected crash
                crash_msg = "[- Warning -] Unexpected crash occurred in CoSESServer! Reply: " + \
                            str(traceback.format_exc() + str(php_response) + 'Database API db_manager.php accessible '
                                                            'with required permissions? Apache server up and running?')
                inst.log_event(crash_msg)
                inst.send_notification(crash_msg)
                inst.generate_status_file('Email notification sent by server script')
        time.sleep(10)  # runs every 10 seconds


def RevPiServerThread(inst):
    """
    Main Server Thread. Binds socket and waits for incoming TCP packets
    :param inst: Instance object
    :return: --
    """
    while inst.threadRunning:
        try:
            if not inst.isConnected:  # In case no client is connected yet
                if(time.time() - inst.t_Timout_listening_client) > t_clientTimeout:  # If no client connected within 120 seconds
                    if not inst.isServerRestarting:  # If restart has not been triggered already
                        if inst.alreadyTimedOutClientConnect:  # Already experienced timeout before, now try system reboot
                            message = '[- Warning -] Timeout recurs. No client connected within ' + \
                                      str(t_clientTimeout) + ' seconds. Trying to reboot system. ' \
                                                             'Please make sure the reboot solved the issue.'
                            inst.log_event(message)
                            inst.send_notification(message)
                            inst.close_connection()  # stop the connection in a clean way
                            inst.restart_system()  # reboot RevPi
                        else:  # First time exception, try to just re-launch the connection
                            message = '[- Warning -] Timeout. No client connected within ' + \
                                      str(t_clientTimeout) + ' seconds. Trying to revive connection ...'
                            inst.log_event(message)
                            inst.close_connection()  # stop the connection in a clean way
                            inst.revive_connection()
                        inst.alreadyTimedOutClientConnect = True
                        break
                else:  # No Timeout occurred yet
                    try:
                        inst.conn, addr = inst.s.accept()
                        inst.conn.setblocking(False)  # Set as non-blocking socket
                        message = '[CoSESServer] Client connected to server: ' + str(addr)
                        inst.isServerRestarting = False
                        inst.log_event(message)
                        inst.delete_status_file()
                        time.sleep(2)  # Give the client some time to fully initialize the connection
                        inst.isConnected = True
                        inst.t_lastHeartBeat = time.time()
                        inst.isConnectionClosing = False
                    except Exception, e:
                        if e.args[0] == errno.EAGAIN:  # Exception is caused by non-blocking socket (no user connecting)
                            pass
                        else:  # Other exception, try to re-establish connection to Controllino after clean shutdown
                            message = '[Traceback_4] ' + str(traceback.format_exc())
                            inst.log_event(message, False)
                            if inst.alreadyExperiencedException_04:  # Already experienced this exception, now try system reboot
                                inst.log_event('[CoSESServer] Failed. Trying to reboot system ...')
                                inst.send_notification('[- Warning -] Exception re-occurred. Trying to reboot system. '
                                                       'Please make sure the reboot solved the issue.')
                                inst.close_connection()  # stop the connection in a clean way
                                inst.restart_system()  # reboot RevPi
                            else:  # First time exception, try to just re-launch the connection
                                inst.log_event('[CoSESServer] Failed. Trying to revive connection ...')
                                inst.close_connection()  # stop the connection in a clean way
                                inst.revive_connection()
                            inst.alreadyExperiencedException_04 = True
                            break
            else:  # Client is currently connected
                try:
                    # Receiving Data from Client
                    data = inst.conn.recv(1024)
                    if data:  # If data in input buffer
                        process_arriving_packet = True
                        data_tmp = data.split('\n')
                        for item in data_tmp:
                            # Collecting Sensor Data received over TCP Socket
                            if item and "|" in item:  # Sensor Data received
                                if process_arriving_packet:  # Accept only one sensor data packet per cycle (as multiple packets are caused by a timeout and contain duplicate timestamps)
                                    inst.parse_sensor_data(item)
                                    process_arriving_packet = False
                            elif item and HeartBeatControllinoReply_char in item:  # HeartBeat response detected
                                inst.HeartBeatValid = True
                except Exception, e:
                    if e.args[0] == errno.EWOULDBLOCK:  # Exception is caused by non-blocking socket (currently no data recv)
                        pass
                    else:  # Other exception, try to re-establish connection to Controllino after clean shutdown
                        message = '[Traceback_3] ' + str(traceback.format_exc())
                        inst.log_event(message, False)
                        if inst.alreadyExperiencedException_03:  # Already experienced this exception, now try system reboot
                            inst.log_event('[CoSESServer] Failed. Trying to reboot system ...')
                            inst.send_notification('[- Warning -] Exception re-occurred. Trying to reboot system. '
                                                   'Please make sure the reboot solved the issue.')
                            inst.send_command(CMD_RESET_CONTROLLINO)  # Try to send reset command to Cotrollino
                            time.sleep(2)
                            inst.close_connection()  # stop the connection in a clean way
                            inst.restart_system()  # reboot RevPi
                        else:  # First time exception, try to just re-launch the connection
                            inst.log_event('[CoSESServer] Failed. Trying to revive connection ...')
                            inst.close_connection()  # stop the connection in a clean way
                            inst.revive_connection()
                        inst.alreadyExperiencedException_03 = True
                        break
                if(time.time() - inst.t_lastHeartBeat) > t_HeartBeatRate:  # It's time to send a new HeartBeat
                    if inst.HeartBeatValid:  # Last HeartBeat has been acknowledged
                        inst.conn.send(CMD_HeartBeat_char)  # Send new HeartBeat signal to Cotrollino
                        inst.HeartBeatValid = False
                        inst.t_lastHeartBeat = time.time()
                        inst.alreadyRevivedConnection = False
                        inst.alreadyTimedOutClientConnect = False
                        inst.alreadyExperiencedException_01 = False
                        inst.alreadyExperiencedException_02 = False
                        inst.alreadyExperiencedException_03 = False
                        inst.alreadyExperiencedException_04 = False
                    else:  # No reply for last HeartBeat!
                        if inst.missedHeartBeats > HeartBeats_missed_TIMEOUT:  # Something is wrong, multiple HeartBeats not received!
                            if inst.alreadyRevivedConnection:  # If previously a connection revive has been tried but failed, now try to restart the whole system
                                message = '[- Warning -] Multiple HeartBeats left unanswered! Previous measures failed. ' \
                                          'Trying to reboot whole system. Please make sure the reboot solved the issue.'
                                inst.log_event(message)
                                inst.send_notification(message)
                                inst.send_command(CMD_RESET_CONTROLLINO)  # Try to send reset command to Cotrollino
                                time.sleep(2)
                                inst.close_connection()  # stop the connection in a clean way
                                inst.restart_system()  # reboot RevPi
                            else:  # This is the first time that multiple heartbeats have been missed, first try just a simple connection re-launch
                                inst.log_event('[- Warning -] Multiple HeartBeats left unanswered! '
                                               'Initiating reconnect ...')
                                inst.send_command(CMD_RESET_CONTROLLINO)  # Try to send reset command to Cotrollino
                                time.sleep(2)
                                inst.close_connection()  # stop the connection in a clean way
                                inst.revive_connection()
                            inst.alreadyRevivedConnection = True
                            break
                        else:  # HeartBeat missed!
                            if(t_HeartBeatRate * 5) < (time.time() - inst.t_temp):  # Reset counter if no HeartBeats missed for a while
                                inst.missedHeartBeats = 0
                            inst.missedHeartBeats += 1
                            inst.HeartBeatValid = True
                            inst.log_event('[- Warning -] HeartBeat not received in time by client. (Skipping a Beat)')
                            inst.t_temp = time.time()
        except Exception:
            message = '[Traceback_2] ' + str(traceback.format_exc())
            inst.log_event(message, False)
            if inst.alreadyExperiencedException_02:  # Already experienced this exception, now try system reboot
                inst.log_event('[CoSESServer] Failed. Trying to reboot system ...')
                inst.send_notification('[- Warning -] Exception re-occurred. Trying to reboot system. '
                                       'Please make sure the reboot solved the issue.')
                inst.send_command(CMD_RESET_CONTROLLINO)  # Try to send reset command to Cotrollino
                time.sleep(2)
                inst.close_connection()  # stop the connection in a clean way
                inst.restart_system()  # reboot RevPi
            else:  # First time exception, try to just re-launch the connection
                inst.log_event('[CoSESServer] Failed. Trying to revive connection ...')
                inst.close_connection()  # stop the connection in a clean way
                inst.revive_connection()
            inst.alreadyExperiencedException_02 = True
            break
        if(time.time() - inst.t_Watchdog) > 45:  # Hardware watchdog will be reset every 45 seconds
            inst.reset_watchdog_timer()  # reset watchdog timer
            inst.t_Watchdog = time.time()
        time.sleep(0.05)  # slow down loop to decrease CPU usage!


class RevPiServerClass:
    def __init__(self):
        self.log_path = self.read_ini('config', 'path_log')  # check if log file exists
        global RevPiServerLaunched
        if not RevPiServerLaunched:
            # General global Class VARs
            RevPiServerLaunched = True
            self.ReviveConnection = False
            self.isConnectionClosing = False
            self.isServerRestarting = False
            self.s = None
            self.conn = None
            self.isConnected = False
            self.threadRunning = False
            self.log_list = []
            self.t_Watchdog = time.time()
            self.SensorDataDict = {
                0: None,
                1: None,
                2: None,
                3: None,
                4: None,
                5: None,
                6: None,
                7: None,
            }
            self.php_path = self.read_ini('php_paths', 'link_db_api')
            # HeartBeat
            self.t_lastHeartBeat = time.time()
            self.t_temp = time.time()
            self.HeartBeatValid = True
            self.missedHeartBeats = 0
            # Advanced Exception Handling
            self.alreadyRevivedConnection = False
            self.alreadyTimedOutClientConnect = False
            self.alreadyExperiencedException_01 = False
            self.alreadyExperiencedException_02 = False
            self.alreadyExperiencedException_03 = False
            self.alreadyExperiencedException_04 = False
            self.notification_path = None
            self.update_notification_file()  # Create or update user_notification.txt
            self.reset_watchdog_timer()  # reset watchdog timer
            self.t_Timout_listening_client = time.time()
            # Start reviver thread
            alive_thread = threading.Thread(target=AliveCheckerThread, args=[self])
            alive_thread.start()
            # Start Thread that is checking the database for admin commands
            ACMD_thread = threading.Thread(target=AdminCommandCheckerThread, args=[self])
            ACMD_thread.start()
            # Start Thread that keeps the notification file up-to-date
            NotificationUpdater_thread = threading.Thread(target=UpdateNotificationFileThread, args=[self])
            NotificationUpdater_thread.start()
        else:
            self.log_event('[ERROR_1] CoSESServer already running! Only one instance at a time can be run.')

    def start_server(self):
        """
        Starts the CoSESServer so a client (CONTROLLINO) is able to connect
        :param NONE: --
        :return: --
        """
        self.log_path = self.read_ini('config', 'path_log')  # check if log file exists
        if not self.threadRunning:  # If server not running
            self.reset_watchdog_timer()  # reset watchdog timer
            self.t_Watchdog = time.time()
            self.log_event('------------------------------------------------------', False)
            message = 'CoSESServer ' + version + ' by Miroslav Lach [2019, MSE - CoSESWeather]'
            self.log_event(message, False)
            self.log_event('------------------------------------------------------', False)
            self.log_event('[CoSESServer] Launching server ...', False)
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create socket with IPv4 and TCP
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # make socket address re-usable without TIME_WAIT after shutdown
                self.s.setblocking(False)  # Set as non-blocking socket
                self.log_event('[CoSESServer] Created socket.', False)
                self.s.bind((host, port))  # Listen for incoming connections on the defined port
                message = '[CoSESServer] Bind on port: ' + str(port)
                self.log_event(message, False)
                self.s.listen(1)  # Accept only one client for created socket
                self.log_event('[CoSESServer] Server successfully launched.', False)
                self.log_event('[CoSESServer] Waiting for incoming connections ...')
                self.t_Timout_listening_client = time.time()
                # Start Server Thread that listens for incoming data and manages heartbeats
                self.threadRunning = True
                workerHandler = threading.Thread(target=RevPiServerThread, args=[self])
                workerHandler.start()
                self.isConnectionClosing = False
            except Exception:
                message = '[Traceback_1] ' + str(traceback.format_exc())
                self.log_event(message, False)
                if self.alreadyExperiencedException_01:  # Already experienced this exception, now try system reboot
                    self.log_event('[CoSESServer] Failed. Trying to reboot system ...')
                    self.send_notification('[- Warning -] Exception re-occurred. Trying to reboot system. '
                                           'Please make sure the reboot solved the issue.')
                    self.close_connection()  # stop the connection in a clean way
                    self.restart_system()  # reboot RevPi
                else:  # First time exception, try to just re-launch the connection
                    self.log_event('[CoSESServer] Failed. Trying to re-launch server ...')
                    self.close_connection()  # stop the connection in a clean way
                    time.sleep(5)
                    self.start_server()  # Try to establish connection again
                self.alreadyExperiencedException_01 = True
        else:
            self.log_event('[ERROR_2] CoSESServer already running! Only one instance at a time can be run.')

    def parse_sensor_data(self, rawDataString):
        """
        Parse the raw data received from the TCP socket acquired from various sensors
        :param rawDataString: string - containing values from all sensors. Values are separated with an '|'.
        :return: --
        """
        '''
            *** Contents of Dictionary SensorDataDict *** 
        0 = Anemometer          | Windspeed         | [m/s]
        1 = PT100               | Temperature       | [°C]
        2 = SPN1 Pyranometer    | Total Radiation   | [W/m²]
        3 = SPN1 Pyranometer    | Diffuse Radiation | [W/m²]
        4 = SPN1 Pyranometer    | Sunshine Presence | [0, 1]
        5 = CMP3  Pyranometer 1 | Solar Radiation   | [W/m²]
        6 = CMP3  Pyranometer 2 | Solar Radiation   | [W/m²]
        7 = CMP3  Pyranometer 3 | Solar Radiation   | [W/m²]
        '''
        index = 0
        rawSensorDataList = rawDataString.split("|")
        for sensor_i in rawSensorDataList:  # Loop through all sensor readings
            if sensor_i and not sensor_i == '':  # If exists and not empty
                if ',' in sensor_i or '_ERR_SPN1_' in sensor_i:  # SPN1 reading returns a comma separated string -> needs further parsing
                    if '_ERR_SPN1_' in sensor_i:  # SPN1 did not return a valid reading
                        spn1Readings = [None, None, None]  # invalid reading received
                        self.log_event('[- Warning -] SPN1 (over serial) returned an invalid reading! '
                                       'Please check if this is a repetitive misbehavior. Sensor properly connected?')
                    else:  # valid reading returned from SPN1
                        spn1Readings = sensor_i.split(",")
                        # In case SPN1 radiation values are negative, set to zero
                        if float(spn1Readings[0]) < 0:
                            spn1Readings[0] = '0.0'
                        if float(spn1Readings[1]) < 0:
                            spn1Readings[1] = '0.0'
                    self.SensorDataDict[index] = spn1Readings[0]
                    index += 1
                    self.SensorDataDict[index] = spn1Readings[1]
                    index += 1
                    self.SensorDataDict[index] = spn1Readings[2]
                    index += 1
                else:  # All other sensors
                    if '9999' in sensor_i:  # one of the sensor returned an invalid value or could not be read
                        if '9999.1' in sensor_i:  # PT100 RTD Amp-Board
                            self.log_event('[- Warning -] PT100 RTD Amp-Board (over SPI) returned invalid values! '
                                           'Please check if this is a repetitive misbehavior. Module properly connected?')
                        elif '9999.21' in sensor_i:  # CMP3 Amp-Board ADC - Channel 1
                            self.log_event('[- Warning -] CMP3 Amp-Board ADC (Channel 1 over I2C) returned invalid values! '
                                           'Please check if this is a repetitive misbehavior. Module properly connected?')
                        elif '9999.22' in sensor_i:  # CMP3 Amp-Board ADC - Channel 3
                            self.log_event('[- Warning -] CMP3 Amp-Board ADC (Channel 3 over I2C) returned invalid values! '
                                           'Please check if this is a repetitive misbehavior. Module properly connected?')
                        elif '9999.23' in sensor_i:  # CMP3 Amp-Board ADC - Channel 4
                            self.log_event('[- Warning -] CMP3 Amp-Board ADC (Channel 4 over I2C) returned invalid values! '
                                           'Please check if this is a repetitive misbehavior. Module properly connected?')
                        self.SensorDataDict[index] = None  # flag sensor reading as invalid
                    else:  # returned sensor values seem valid - save them
                        self.SensorDataDict[index] = sensor_i  # Save data into dictionary
                    index += 1
        # Save new dataset into primary database (forwarding data to PHP script)
        data = {
                "p_mode": 1,
                "p_temp": self.SensorDataDict[1],
                "p_wind": self.SensorDataDict[0],
                "p_spn1_radTot": self.SensorDataDict[2],
                "p_spn1_radDiff": self.SensorDataDict[3],
                "p_spn1_sun": self.SensorDataDict[4],
                "p_rad_cmp1": self.SensorDataDict[5],
                "p_rad_cmp2": self.SensorDataDict[6],
                "p_rad_cmp3": self.SensorDataDict[7]
               }
        resp_php = requests.post(self.php_path, data=data).text  # send POST request

        if '__SUCCESS;' not in resp_php:  # If error occurred while trying to save data to primary database
            message = '[- Warning -] Primary Database Error occurred! PHP Script returned: ' + str(resp_php)
            self.send_notification(message)
            self.generate_status_file('Email notification sent by server script')
            self.log_event(message)

    def send_command(self, cmd):
        """
        Sends a command to the client
        :param cmd: str - 'a' = reset microprocessor | '#' = HEARTBEAT
        :return: --
        """
        try:
            if self.threadRunning and self.isConnected:
                self.conn.send(cmd)
                print('[Info]: Command sent. (cmd: ' + cmd + ')')
            elif not self.isConnected and self.threadRunning:
                print('[CMD_WARNING]: No client currently connected!')
            else:
                print('[CMD_WARNING]: CoSESServer not running!')
        except Exception:
            pass

    def close_connection(self):
        """
        Closes a connection and the socket in a clean and controlled way
        :param NONE: --
        :return: --
        """
        if not self.isConnectionClosing:  # Avoid multiple execution
            self.isConnectionClosing = True
            self.threadRunning = False
            try:
                self.conn.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            if self.conn:
                self.conn.close()
            self.conn = None
            self.s = None
            self.isConnected = False
            # Reset variables and counters
            self.HeartBeatValid = True
            self.missedHeartBeats = 0
            self.log_event('[CoSESServer] Server closed the connection.')

    def revive_connection(self):
        """
        Sets the revive flag. This will cause the AliveCheckerThread to restart the (software) server
        :param NONE: --
        :return: --
        """
        self.ReviveConnection = True

    def restart_system(self):
        """
        This function will restart the (hardware) Server (RevPi reboot)
        :param NONE: --
        :return: --
        """
        self.isServerRestarting = True
        self.log_event('[CoSESServer] Initiating system reboot ...')
        # Create local file so system knows there just has been a restart in order to fix issues before
        self.generate_status_file('Restart triggered by system')
        # wait and trigger restart
        time.sleep(5)
        subprocess.call(['shutdown', '-r', 'now'])  # Restart RevPi (call = blocking)

    def generate_status_file(self, reason):
        """
        This function generates the status file. This file indicates that the system just has been restarted
        due to errors. This function can e.g. be used to prevent notification spam or track system reboots
        :param reason: string - reason for status file generation
        :return: --
        """
        def _update_or_create_file(inst):
            file_path = inst.read_ini('config', 'path_status_file')  # Get path from .ini file
            fi = open(file_path, 'a+')  # open file in append mode
            fi.write('[' + time.strftime("%d.%m.%Y|%H:%M:%S", time.localtime()) + ']' + reason + '\n')
            fi.close()

        if not self.check_status_file():  # no status file exists yet, create one
            _update_or_create_file(self)
        else:  # if status file already exists
            if self.check_status_file_date():  # Update it if last update is older than one day or created by bash
                _update_or_create_file(self)

    def delete_status_file(self):
        """
        This function deletes the status file. This file indicates that the system just has been restarted
        due to errors. This function can e.g. be used to prevent notification spam or track system reboots
        :param NONE: --
        :return: --
        """
        if self.check_status_file():
            file_path = self.read_ini('config', 'path_status_file')  # Get path from .ini file
            os.remove(file_path)

    def check_status_file(self):
        """
        This function checks if the status file exists. If there is one, the system has just been restarted
        due to errors. This function can e.g. be used to prevent notification spam or track system reboots
        :param NONE: --
        :return: --
        """
        file_path = self.read_ini('config', 'path_status_file')  # Get path from .ini file
        if os.path.isfile(file_path):  # If status file already exists return = 1
            return True
        else:  # if file does not exist return = 0
            return False

    def check_status_file_date(self):
        """
        This function checks the date of the status file. If the last entry in this file is older than one day
        this function returns = 1. This is used to schedule notification messages and prevent spam.
        :param NONE: --
        :return: --
        """
        try:
            file_path = self.read_ini('config', 'path_status_file')  # Get path from .ini file
            with open(file_path, 'r') as file_r:  # read status file and check the last line
                lastLine = list(file_r)[-1]
            date_log = lastLine[1:20]  # extract the timestamp of the log line
            day_of_month_CURRENT = int(time.strftime("%d", time.localtime()))
            day_of_month_LOG = int(datetime.datetime.strptime(date_log, "%d.%m.%Y|%H:%M:%S").day)
            if not day_of_month_CURRENT == day_of_month_LOG:  # match the days: no notification sent today
                return True
            else:  # already sent a notification today
                return False
        except Exception:
            return True

    def log_event(self, msg, push=True):
        """
        Appends an event into the logfile and prints to the server terminal
        :param msg: str - The message that has to be logged
        :param push: bool - If True, appended messages will be written to the logfile
        :return: --
        """
        def _write_to_file(inst):
            f = open(inst.log_path, 'a+')  # open file in append mode
            for log_i in inst.log_list:
                f.write(log_i + '\n')
                print(log_i)
            f.close()
            del inst.log_list[:]

        def _create_new_header(inst, msg_temp):
            inst.log_list.append('---------------------------------------------------------------------------')
            inst.log_list.append('--------------------- CoSESServer Log -------------------------------------')
            inst.log_list.append('---------------------------------------------------------------------------')
            inst.log_list.append(msg_temp)
            _write_to_file(inst)

        msg_tmp = '[' + time.strftime("%d.%m.%Y|%H:%M:%S", time.localtime()) + ']' + msg
        if push:  # If write mode TRUE: log list will be written into file
            self.log_path = self.read_ini('config', 'path_log')  # check log file path
            if not os.path.isfile(self.log_path):  # If no log file exists yet, create a header for log file (initial)
                _create_new_header(self, msg_tmp)
            else:  # log file already exists, just append new logs to old log file
                self.log_list.append(msg_tmp)
                _write_to_file(self)
        else:  # If write mode FLASE: only append to log list, but do not write to file
            if not os.path.isfile(self.log_path):  # If not log file exists yet
                _create_new_header(self, msg_tmp)
            else:  # If log file already exists
                self.log_list.append(msg_tmp)

    def reset_watchdog_timer(self):
        """
        Resets the timer of the hardware watchdog of the RevPi (that otherwise will reboot the system after 60 secs)
        :param NONE: --
        :return: --
        """
        script_path = self.read_ini('bash_paths', 'path_revpi_watchdog')  # Get script path from .ini file
        subprocess.Popen(["bash", script_path])  # reset watchdog timer (using the bash-script) (Popen = nonblocking)

    def getDB_user_emails(self):
        """
        Queries the user database and returns emails of registered users with admin status
        :param NONE: --
        :return: email_list - list
        """
        data_php = {"p_mode": 3}
        # Requesting emails from user database
        php_response = requests.post(self.php_path, data=data_php)
        try:
            php_response = php_response.json()
        except Exception:
            php_response = php_response.text

        try:  # ok?
            if '__SUCCESS;' in php_response[0]:  # valid php response returned by MySQL user database
                del php_response[0]
                return php_response
            else:
                message = '[- Warning -] User Database Error occurred while fetching contacts! ' \
                          'PHP Script returned: ' + str(php_response)
                self.log_event(message)
        except Exception:  # unexpected crash
            crash_msg = "[- Warning -] Unexpected crash occurred in CoSESServer! Reply: " + \
                        str(traceback.format_exc() + str(php_response) + 'Database API db_manager.php accessible with'
                                                                ' required permissions? Apache server up and running?')
            self.log_event(crash_msg)

    def send_notification(self, msg):
        """
        Send an email notification
        :param msg: str - The message to be sent via email
        :return: --
        """
        def _send(inst, message):
            email_list = inst.getDB_user_emails()
            mail_content = '[' + time.strftime("%d.%m.%Y|%H:%M:%S", time.localtime()) + ']' + message
            mail_subject = '[CoSESWeather]Warning: Faulty Behaviour detected!'
            try:  # database returned updated contact/email list
                if email_list[0]:  # if there are mail addresses in database
                    for mail in email_list:
                        process = subprocess.Popen(['mail', '-s', str(mail_subject), str(mail)], stdin=subprocess.PIPE) # Send email notification
                        process.communicate(str(mail_content))  # Using PIPE to inject message body into the unix-process
                    inst.log_event('[CoSESServer] Notification sent to system administrators.')
            except Exception:  # database did not reply - get emails out of notification file directly
                try:
                    f = open(path_contacts, 'r')  # read notification.txt file
                    email_list = f.readlines()
                    f.close()
                    if email_list:  # if there are mail addresses in .txt file
                        for mail in email_list:
                            process = subprocess.Popen(['mail', '-s', str(mail_subject), str(mail)], stdin=subprocess.PIPE)  # Send email notification
                            process.communicate(str(mail_content))  # Using PIPE to inject message body into the unix-process
                        inst.log_event('[CoSESServer] Notification sent to system administrators.')
                except Exception:
                    pass

        if not self.check_status_file():  # If no status file exists, send notification
            _send(self, msg)
        else:  # If status file exists, only send one notification per day (to prevent notification spamming)
            if self.check_status_file_date():
                _send(self, msg + ' This is a repeating message. The system is still not running properly. '
                                  'Please look into it as soon as possible.')

    def update_notification_file(self):
        """
        Update the path_notification.txt and keep the emails of system users/administrators up-to-date
        :param NONE: --
        :return: --
        """
        try:
            self.notification_path = self.read_ini('config', 'path_notification')  # get file path from .ini file
            email_list = self.getDB_user_emails()
            if email_list[0]:  # if there are mail addresses in database
                f = open(self.notification_path, 'w+')  # overwrites old file or creates new one if not exists
                for mail in email_list:
                    f.write(mail + '\n')
                f.close()
        except Exception:
            pass

    def read_ini(self, section, value):
        """
        Read the CoSESWeather.ini to extract paths to files
        :param section: str - Desired section that should be extracted from the .ini file
        :param value: str - Desired value that should be extracted from the .ini file
        :return data_out: str - requested value
        """
        try:
            config = ConfigParser.ConfigParser()
            config.read(path_ini)
            data_out = config.get(section, value)
            return data_out
        except Exception:
            message = 'Failed. CoSESWeather.ini file missing! Please make sure the file exists and is in the ' \
                      'specified location: ' + path_ini
            self.exit_gracefully(message)

    def exit_gracefully(self, message):
        """
        Will shut down the CoSESServer.py and write the provided message to the log.
        :param message: str - The message to be written to CoSESServer log
        :return --
        """
        msg = '[- ERROR -] ' + message
        self.log_event(msg)
        sys.exit(0)


if __name__ == '__main__':
    INSTANCE_MAIN = RevPiServerClass()
    INSTANCE_MAIN.start_server()














