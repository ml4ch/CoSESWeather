#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This software is part of the CoSESWeather project.
This WeeWx Driver for the CoSES-Weather Station (CoSESWeather) fetches datasets from the primary MySQL database so the
weather data can be archived and recorded in the secondary database (WeeWx) and finally be displayed in a generated
weather report.
"""

import sys
import os
import subprocess
import time
import traceback
import datetime
import requests
import ConfigParser
import syslog
import weewx.drivers


__author__ = "Miroslav Lach"
__copyright__ = "Copyright 2019, MSE"
__version__ = "1.0"
__maintainer__ = "Miroslav Lach"
__email__ = "miroslav.lach@tum.de"


DRIVER_NAME = 'CoSESDriver'
DRIVER_VERSION = 'v1.0'

# Path to the CoSESWeather.ini file
path_ini = r'/opt/CoSESWeather/CoSESWeather.ini'
# Path to the user_notification.txt file
path_contacts = r'/opt/CoSESWeather/user_notification.txt'


def loader(config_dict, _):  # Required and expected by WeeWx
    return CoSESDriver(**config_dict[DRIVER_NAME])

def logmsg(level, msg):
    syslog.syslog(level, '[CoSESDriver]: %s' % msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)


class CoSESDriver(weewx.drivers.AbstractDevice):
    def __init__(self, **stn_dict):
        self.t_last_fetch = time.time()
        self.model = stn_dict.get('model', 'CoSESDriver')
        self.fetch_interval = float(stn_dict.get('fetch_interval', 60))  # fetch datasets for accumulation from primary database once every minute
        self.record_interval = float(stn_dict.get('record_interval', 300))  # archive (accumulated datasets) in secondary database (WeeWx database) once every 5 minutes
        self.t_warn_no_fetch = float(stn_dict.get('t_warn_if_no_fetch', 900))  # timeout in 15 minutes
        self.php_path = self.read_ini('php_paths', 'link_db_api')
        loginf("Initiating WeeWx CoSESDriver for CoSESWeather ...")
        loginf('CoSESDriver %s started.' % DRIVER_VERSION)

    def closePort(self):
        """
        Called when Driver is shut down
        :param NONE: --
        :return: --
        """
        loginf("Shutting down WeeWx CoSESDriver for CoSESWeather ...")
        loginf('CoSESDriver %s shut down.' % DRIVER_VERSION)

    @property
    def hardware_name(self):
        """
        Required and expected by WeeWx.
        :param NONE: --
        :return: str - driver name
        """
        return self.model

    def genLoopPackets(self):
        """
        Required and expected by WeeWx.
        This function fetches newly acquired datasets from the primary database and forwards the data to WeeWx.
        This function requests data from the primary database via a PHP script.
        :param NONE: --
        :return: dictionary - Emits data packets parsed so WeeWx can process them and use it for weather report generation.
        """
        while True:
            # Requesting datasets from primary database
            data_php = {"p_mode": 2}
            php_response = requests.post(self.php_path, data=data_php)
            try:
                php_response = php_response.json()
            except Exception:
                php_response = php_response.text

            try:  # ok?
                if '__SUCCESS;' in php_response[0]:  # Valid datasets returned by primary MySQL database
                    del php_response[0]
                    self.t_last_fetch = time.time()
                    for dataset in php_response:
                        data = dict()
                        data['dateTime'] = int(dataset['t_unix'])  # Timestamp
                        data['usUnits'] = weewx.METRICWX  # use METRIC (for km/h windspeed) or METRICWX (for m/s windspeed)
                        # Anemometer
                        if dataset['wind']:  # if value available
                            data['windSpeed'] = float(dataset['wind'])
                        # PT100
                        if dataset['temp']:
                            data['outTemp'] = float(dataset['temp'])  # PT100
                        # SPN1 total radiation
                        if dataset['spn1_radTot']:
                            data['radiation'] = float(dataset['spn1_radTot'])
                        # SPN1 diffuse radiation
                        if dataset['spn1_radDiff']:
                            data['radiationDiff'] = float(dataset['spn1_radDiff'])
                        # SPN1 sunshine presence
                        if dataset['spn1_sun']:
                            data['sun'] = float(dataset['spn1_sun'])
                        # CMP3 1
                        if dataset['rad_cmp1']:
                            data['radiation1'] = float(dataset['rad_cmp1'])
                        # CMP3 2
                        if dataset['rad_cmp2']:
                            data['radiation2'] = float(dataset['rad_cmp2'])
                        # CMP3 3
                        if dataset['rad_cmp3']:
                            data['radiation3'] = float(dataset['rad_cmp3'])
                        yield data  # send data package including all acquired sensor data
                else:
                    if '__NO_ROWS_RETURNED;' in php_response:
                        # no new datasets available in primary database for WeeWx to fetch and record
                        if (time.time() - self.t_last_fetch) > self.t_warn_no_fetch:
                            msg = "[FATAL] Could not fetch any new datasets within specified timeout window! " \
                                  "Seems that no new datasets are saved into primary database. " \
                                  "Please check system as soon as possible!"
                            self.send_notification(msg)  # send email notification to admin
                            logerr(msg)  # log event
                            self.restart_system()  # reboot system
                    else:  # Error occurred in PHP script
                        msg = "[FATAL] Failed to fetch datasets from primary database! Reply: " + php_response
                        self.send_notification(msg)  # send email notification to admin
                        self.generate_status_file('Email notification sent by driver script')
                        logerr(msg)  # log event
            except Exception:  # unexpected crash
                crash_msg = "[FATAL] Unexpected crash occurred in CoSESDriver! Reply: " + \
                            str(traceback.format_exc() + str(php_response) + 'Database API db_manager.php accessible '
                                                            'with required permissions? Apache server up and running?')
                self.send_notification(crash_msg)  # send email notification to admin
                self.generate_status_file('Email notification sent by driver script')
                logerr(crash_msg)  # log event
            time.sleep(self.fetch_interval)

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
                    loginf('Notification sent to system administrators.')
            except Exception:  # database did not reply - get emails out of notification file directly
                try:
                    f = open(path_contacts, 'r')  # read notification.txt file
                    email_list = f.readlines()
                    f.close()
                    if email_list:  # if there are mail addresses in .txt file
                        for mail in email_list:
                            process = subprocess.Popen(['mail', '-s', str(mail_subject), str(mail)], stdin=subprocess.PIPE)  # Send email notification
                            process.communicate(str(mail_content))  # Using PIPE to inject message body into the unix-process
                        loginf('Notification sent to system administrators.')
                except Exception:
                    pass

        if not self.check_status_file():  # If no status file exists, send notification
            _send(self, msg)
        else:  # If status file exists, only send one notification per day (to prevent notification spamming)
            if self.check_status_file_date():
                _send(self, msg + ' This is a repeating message. The system is still not running properly. '
                                  'Please look into it as soon as possible.')

    def check_status_file(self):
        """
        This function checks if the status file exists. If there is one, the system has just been restarted
        due to errors. This function can e.g. be used to prevent notification spam or track system reboots
        :param NONE: --
        :return: --
        """
        file_path = self.read_ini('config', 'path_status_file')  # Get path from .ini file
        if os.path.isfile(file_path):  # If status file already exists return True
            return True
        else:  # if file does not exist return False
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

    def restart_system(self):
        """
        This function will restart the (hardware) Server (RevPi reboot)
        :param NONE: --
        :return: --
        """
        loginf('Initiating system reboot ...')
        # Create local file so system knows there just has been a restart in order to fix issues before
        self.generate_status_file('Restart triggered by driver')
        # wait and trigger restart
        time.sleep(5)
        subprocess.call(['shutdown', '-r', 'now'])  # Restart RevPi (call = blocking)

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
                message = '[FATAL] Database Error occurred while fetching contacts! ' \
                          'PHP Script returned: ' + str(php_response)
                logerr(message)
        except Exception:  # unexpected crash
            crash_msg = "[FATAL] Unexpected crash occurred in CoSESDriver! Reply: " + \
                        str(traceback.format_exc() + str(php_response) + 'Database API db_manager.php accessible with '
                                                                'required permissions? Apache server up and running?')
            logerr(crash_msg)  # log event

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
            logerr("[FATAL] CoSESWeather.ini file could not be found! Please make sure the file exists and is in "
                   "the specified location: %s." % path_ini)
            sys.exit(0)


if __name__ == '__main__':
    driver = CoSESDriver()
    for packet in driver.genLoopPackets():
        print packet







