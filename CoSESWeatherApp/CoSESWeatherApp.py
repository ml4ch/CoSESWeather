#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This software is part of the CoSESWeather project.
CoSESWeatherApp is the GUI that enables the user to interact with the CoSESWeather System.
This software provides the possibility to view and export weather data, manage user accounts, send commands to the µC etc.
"""

import sys
import os.path
import traceback
import subprocess
import time
import datetime
import requests
import webbrowser
import ConfigParser
import csv
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from PyQt4 import QtGui, QtCore
import CoSESWeatherApp_ui
import CoSESWeatherApp_LOGIN_ui
import PasswordChange_ui
import TrendViewer_ui


__author__ = "Miroslav Lach"
__copyright__ = "Copyright 2019, MSE"
__version__ = "1.0"
__maintainer__ = "Miroslav Lach"
__email__ = "miroslav.lach@tum.de"


client_version = 'v1.0'
coses_website_address = r'https://www.mse.tum.de/en/coses/'

# Path to the CoSESWeather.ini file
path_ini = r'/opt/CoSESWeather/CoSESWeather.ini'

# Destination IP (static IP) of the RevPi that hosts the CoSESWeather-System
revpi_remote_address = r'https://miroslav-lach-8364.dataplicity.io'

# Local destination address of system
revpi_local_address = r'localhost'
# Linux superuser account name
LINUX_USER = "coses"


def resource_path(relative_path):
    """ Get absolute path to resource, needed for PyInstaller to include and bind all resource files """
    # Credits for function to max on stackoverflow.com:
    # Link: https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile/44352931
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def check_platform():
    """
    Checks if the machine on which the App is run is the RevPi
    :param : --
    :return: bool
    """
    platform_os = sys.platform
    if platform_os == "linux" or platform_os == "linux2":  # Linux
        if os.getenv('USER') == LINUX_USER:  # running system seems to be RevPi
            return True
        return False
    elif platform_os == "win32" or platform_os == "cygwin":  # Windows
        return False
    else:  # Other OS
        return False

def truncate_float(full_float, digits):
    """
    Truncate digits from a floating point number
    :param : full_float (string), digits (integer)
    :return: float
    """
    return float(full_float[:full_float.find('.') + digits + 1])

class ReloadTrendWorker(QtCore.QThread):
    """
    ReloadTrendWorker Thread. Refreshes the weather data trends in trend-viewer automatically (serves as a Timer)
    """
    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            time.sleep(240)  # run once every 4 minutes
            self.emit(QtCore.SIGNAL('signal_finish()'))


class WorkerINIT(QtCore.QThread):
    """
    WorkerINIT Thread. Performs checks whether the links to the RevPi System can be reached (on initialization)
    """
    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        try:  # connection can be established
            request_weewx = requests.get(MAIN_INSTANCE.system_address)
            request_php = requests.get(MAIN_INSTANCE.system_php_address)

            if request_weewx.status_code == 200 and request_php.status_code == 200:  # response ok
                MAIN_INSTANCE.link_valid = True
                MAIN_INSTANCE.execute_php_job(0)
            else:  # error
                MAIN_INSTANCE.link_valid = False
        except Exception:  # no connection possible - timeout
            MAIN_INSTANCE.link_valid = False
        finally:
            self.emit(QtCore.SIGNAL('signal_emit()'))
        return


class ExportWorkerThread(QtCore.QThread):
    """
    ExportWorker Thread. Creates the Export-File
    """
    def __init__(self, var_process):
        QtCore.QThread.__init__(self)
        self.process_arg = var_process

    def __del__(self):
        self.wait()

    def run(self):
        try:
            rows_selected = len(MAIN_INSTANCE.json_data_dict)

            if self.process_arg == 0:  # export from primary database
                file_name = 'CoSESWeather_DataExport_DB1'
            else:  # export from secondary database
                file_name = 'CoSESWeather_DataExport_DB2'

            if MAIN_INSTANCE.file_name_specified:  # if custom export path and filename have been specified
                custom_filename = MAIN_INSTANCE.file_name_specified.\
                    replace('.txt', '').\
                    replace('.csv', '').\
                    replace('.xlsx', '')
                MAIN_INSTANCE.file_name_export = custom_filename
            else:  # no custom export path and filename have been specified - save in standard path (root dir of app)
                MAIN_INSTANCE.file_name_export = file_name + time.strftime(
                    "__%d_%m_%Y__%H_%M_%S", time.localtime())
            header_list = MAIN_INSTANCE.sensor_select.split(', ')

            if '.txt' in MAIN_INSTANCE.comboBox_formatExport.currentText():  # .txt format chosen for export
                MAIN_INSTANCE.file_name_export += '.txt'
                space_padding = 25
                # create .txt-file
                with open(MAIN_INSTANCE.file_name_export, 'w') as txtfile:
                    # write header
                    header = 'timestamp'.ljust(space_padding)
                    for sensor in header_list:
                        header += sensor.ljust(space_padding)
                    txtfile.write(header + '\n')
                    # write values
                    for row in MAIN_INSTANCE.json_data_dict:
                        current_timestamp = row[0]  # get timestamp as first value
                        current_line = current_timestamp.ljust(space_padding)
                        for i, val in enumerate(row[1:]):  # get all values but skip timestamp
                            if val:  # if sensor value available
                                if i == 4:  # sun - treat as integer
                                    vdata = val
                                else:  # other sensor values - float
                                    vdata = str(truncate_float(val, 3))
                            else:  # if sensor value is NONE/NULL-Type
                                vdata = '-'
                            current_line += vdata.ljust(space_padding)
                        txtfile.write(current_line + '\n')

            elif '.csv' in MAIN_INSTANCE.comboBox_formatExport.currentText():  # .csv format chosen for export
                MAIN_INSTANCE.file_name_export += '.csv'
                # create .csv-file
                with open(MAIN_INSTANCE.file_name_export, 'wb') as csvfile:
                    filewriter = csv.writer(csvfile, delimiter=',',
                                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    # write header
                    header_list.insert(0, 'timestamp')
                    filewriter.writerow(header_list)
                    # write values
                    for row in MAIN_INSTANCE.json_data_dict:
                        filewriter.writerow(row)

            elif '.xlsx' in MAIN_INSTANCE.comboBox_formatExport.currentText():  # .xlsx format chosen for export
                MAIN_INSTANCE.file_name_export += '.xlsx'
                # create excel header
                if self.process_arg == 0:  # export from primary database
                    for i, item in enumerate(header_list):
                        if item == 'temp':
                            new_str = u'Temperature [\u00b0C]'
                        elif item == 'wind':
                            new_str = u'Wind Speed [m/s]'
                        elif item == 'spn1_radTot':
                            new_str = u'Total Radiation (SPN1) [W/m²]'
                        elif item == 'spn1_radDiff':
                            new_str = u'Diffuse Radiation (SPN1) [W/m²]'
                        elif item == 'spn1_sun':
                            new_str = u'Sunshine Presence (SPN1) [1/0]'
                        elif item == 'rad_cmp1':
                            new_str = u'CMP3 Radiation 1 (56°) [W/m²]'
                        elif item == 'rad_cmp2':
                            new_str = u'CMP3 Radiation 2 (43°) [W/m²]'
                        elif item == 'rad_cmp3':
                            new_str = u'CMP3 Radiation 3 (64°) [W/m²]'
                        else:
                            new_str = header_list[i]
                        header_list[i] = new_str
                    header_list.insert(0, u'Date | Time')
                else:  # export from secondary database
                    for i, item in enumerate(header_list):
                        if item == 'outTemp':
                            new_str = u'Temperature [\u00b0C]'
                        elif item == 'windSpeed':
                            new_str = u'Wind Speed [m/s]'
                        elif item == 'radiation':
                            new_str = u'Total Radiation (SPN1) [W/m²]'
                        elif item == 'radiationDiff':
                            new_str = u'Diffuse Radiation (SPN1) [W/m²]'
                        elif item == 'sun':
                            new_str = u'Sunshine Presence (SPN1) [1/0]'
                        elif item == 'radiation1':
                            new_str = u'CMP3 Radiation 1 (56°) [W/m²]'
                        elif item == 'radiation2':
                            new_str = u'CMP3 Radiation 2 (43°) [W/m²]'
                        elif item == 'radiation3':
                            new_str = u'CMP3 Radiation 3 (64°) [W/m²]'
                        else:
                            new_str = header_list[i]
                        header_list[i] = new_str
                    header_list.insert(0, u'Date | Time')

                # create .xlsx-file
                workbook = xlsxwriter.Workbook(MAIN_INSTANCE.file_name_export)
                initial_sheet_created = False
                previous_month = None

                # add sheet styles
                cell_format_merged_header = workbook.add_format(MAIN_INSTANCE.cell_format_merged_header_DICT)
                cell_format_merged_plot_header = workbook.add_format(MAIN_INSTANCE.cell_format_merged_plot_header_DICT)
                cell_format_filler_cell = workbook.add_format(MAIN_INSTANCE.cell_format_filler_cell_DICT)
                cell_format_merged_secondary_header = workbook.add_format(MAIN_INSTANCE.cell_format_merged_secondary_header_DICT)
                cell_format_header = workbook.add_format(MAIN_INSTANCE.cell_format_header_DICT)
                cell_format_timestamp = workbook.add_format(MAIN_INSTANCE.cell_format_timestamp_DICT)
                cell_format_timestamp_left = workbook.add_format(MAIN_INSTANCE.cell_format_timestamp_left_DICT)
                cell_format_data = workbook.add_format(MAIN_INSTANCE.cell_format_data_DICT)
                cell_format_merged_header_hilo = workbook.add_format(MAIN_INSTANCE.cell_format_merged_header_hilo_DICT)
                cell_format_hilo_data = workbook.add_format(MAIN_INSTANCE.cell_format_hilo_data_DICT)
                cell_format_hilo_data_blue = workbook.add_format(MAIN_INSTANCE.cell_format_hilo_data_blue_DICT)
                cell_format_filler_cell_hilo = workbook.add_format(MAIN_INSTANCE.cell_format_filler_cell_hilo_DICT)
                cell_format_hilo_MIN = workbook.add_format(MAIN_INSTANCE.cell_format_hilo_MIN_DICT)
                cell_format_hilo_MAX = workbook.add_format(MAIN_INSTANCE.cell_format_hilo_MAX_DICT)

                sheet_list = []
                def _write_header(inst, cur_time):
                    new_sheet = time.strftime("%B %Y", time.localtime(float(cur_time)))
                    ws = workbook.add_worksheet(new_sheet)
                    sheet_list.append(new_sheet)
                    # writer header
                    r = 0
                    ws.merge_range(r, 0, r + 1, len(header_list) - 1,
                                   'CoSESWeather Data Export', cell_format_merged_header)
                    r = 2
                    ws.set_row(r, 16)
                    ws.merge_range(r, 0, r, len(header_list) - 1,
                                   '| time range: ' + inst.userData_tmpList[2] + ' - ' +
                                   inst.userData_tmpList[3] + ' | rows exported total: ' + str(rows_selected) +
                                   ' | time step: ' + inst.time_step_str + ' |',
                                   cell_format_merged_secondary_header)
                    r = 3
                    ws.autofilter(r, 0, rows_selected, len(header_list) - 1)
                    for c, label in enumerate(header_list):
                        ws.write(r, c, label, cell_format_header)
                        ws.set_column(r, c, 35)
                    ws.set_row(r, 20)
                    ws.freeze_panes(4, 1)
                    r = 4
                    return ws, r

                # get and parse values
                rows_per_month = 0
                rows_per_month_list = []
                for current_row in MAIN_INSTANCE.json_data_dict:
                    current_timestamp = current_row[0]
                    current_month = time.strftime("%m", time.localtime(float(current_timestamp)))

                    # add sheet
                    if not initial_sheet_created:  # No sheet created yet (create first sheet)
                        worksheet, row = _write_header(MAIN_INSTANCE, float(current_timestamp))
                        initial_sheet_created = True

                    # new month -> create a new sheet
                    if not current_month == previous_month and previous_month:
                        worksheet, row = _write_header(MAIN_INSTANCE, float(current_timestamp))
                        rows_per_month_list.append(rows_per_month)
                        rows_per_month = 0
                    rows_per_month += 1

                    # write row to sheet
                    for i, item in enumerate(current_row):
                        if i == 0:  # timestamp column
                            worksheet.write(row, i, time.strftime("%a, %d.%m.%Y - %H:%M:%S",
                                                    time.localtime(float(current_timestamp))), cell_format_timestamp)
                        else:  # data columns
                            if item:  # if sensor value available
                                worksheet.write(row, i, truncate_float(item, 3), cell_format_data)
                            else:  # if sensor value is NONE/NULL-Type
                                worksheet.write_formula(row, i, 'na()', cell_format_data)
                    row += 1

                    previous_month = current_month
                rows_per_month_list.append(rows_per_month)
                del header_list[0]  # delete element with 'Date | Time' from header as not needed anymore

                if self.process_arg == 1:  # export from secondary database
                    # if checkbox for including hi/lo statistics has been checked
                    if MAIN_INSTANCE.checkBox_exportHiLo.isChecked():
                        hilo_header_list = ['Low', 'Low time', 'High', 'High time']

                        # function checks if provided column number is a mmultiple of 5
                        def _is_col_multiple_of_5(c):
                            if c == 0:
                                return False
                            else:
                                col_num = str(((float(c) / 5) % 1))
                                if col_num == '0.0':  # column is a multiple of 5
                                    return True
                                else:  # column is NOT a multiple of 5
                                    return False

                        # create hilo sheet
                        hilo_sheet_name = 'Hi|Lo Statistics'
                        worksheet = workbook.add_worksheet(hilo_sheet_name)
                        # set width of columns
                        for col_i in range((len(header_list) * 5) + 1):
                            if _is_col_multiple_of_5(col_i):
                                width = 1
                            else:
                                width = 25
                            worksheet.set_column(xl_rowcol_to_cell(0, col_i) + ':' + xl_rowcol_to_cell(0, col_i), width)

                        # write hilo-sheet header
                        row = 0
                        worksheet.merge_range(row, 0, row + 1, (len(header_list) * 5),
                                       'CoSESWeather Data Export [High | Low Statistics]'.rjust(115),
                                              cell_format_merged_header_hilo)
                        row = 2
                        worksheet.set_row(row, 20)

                        worksheet.write(row, 0, 'Date', cell_format_header)
                        for s_i, sensor_i in enumerate(header_list):
                            worksheet.merge_range(row, (s_i * 4) + s_i + 1, row, ((s_i * 4) + s_i + 4), sensor_i,
                                                  cell_format_header)
                            # fill empty cells with background/boarder color
                            worksheet.write(row, ((s_i * 4) + s_i + 4) + 1, '', cell_format_filler_cell_hilo)

                        # write secondary header
                        row = 3
                        col = 1
                        worksheet.set_row(row, 16)
                        worksheet.write(row, 0, 'Day | Date', cell_format_merged_secondary_header)
                        for header_str in header_list:
                            for h, hilo_str in enumerate(hilo_header_list):
                                if _is_col_multiple_of_5(col):
                                    # fill empty cells with background/boarder color
                                    worksheet.write(row, col, '', cell_format_filler_cell_hilo)
                                    col += 1
                                if h == 0 or h == 2:
                                    header_str_mod = header_str[:header_str.find('[') - 1]
                                    worksheet.write(row, col, hilo_str + ' ' + header_str_mod,
                                                    cell_format_merged_secondary_header)
                                else:
                                    worksheet.write(row, col, hilo_str, cell_format_merged_secondary_header)
                                col += 1
                        # fill empty cells with background/boarder color
                        worksheet.write(row, col, '', cell_format_filler_cell_hilo)
                        # freeze header cells
                        worksheet.freeze_panes(4, 1)

                        cur_month = 99
                        col_meta = 0
                        rows_meta = 0
                        header_structure_created = False
                        # define and initialize hilo variables
                        self.hilo_value_MIN = 9999
                        self.hilo_value_MAX = -9999
                        self.hilo_pos_MIN_tuple = (0, 0)
                        self.hilo_pos_MAX_tuple = (0, 0)

                        # function keeps track of monthly peak sensor values (hilo values)
                        def _check_hilo_values(inst, sensor_val, r, c):
                            if sensor_val > inst.hilo_value_MAX:
                                inst.hilo_value_MAX = sensor_val
                                inst.hilo_pos_MAX_tuple = (r, c)
                            if sensor_val < inst.hilo_value_MIN:
                                inst.hilo_value_MIN = sensor_val
                                inst.hilo_pos_MIN_tuple = (r, c)

                        # write data
                        for table_day_sets in MAIN_INSTANCE.json_data_hilo_dict:  # loop through all sensor archive tables
                            row = 5
                            # start looping through sensor values
                            for day_set in table_day_sets:  # loop through all daily sets in the current sensor archive table
                                col = col_meta
                                # create sheet seperator structure only once - in first run
                                new_month = time.strftime("%m", time.localtime(float(day_set['dateTime'])))
                                if not cur_month == new_month:  # mark/add header section for new month
                                    new_section = time.strftime("%B %Y", time.localtime(float(day_set['dateTime'])))
                                    if row == 5:  # first date entry
                                        # check if new month section/seperator has to be created
                                        if not header_structure_created:
                                            worksheet.merge_range(row - 1, 0, row - 1, (len(header_list) * 5),
                                                                  ' ' + new_section, cell_format_merged_plot_header)
                                            worksheet.set_row(row - 1, 16)
                                    else:
                                        # check if new month section/seperator has to be created
                                        if not header_structure_created:
                                            worksheet.merge_range(row, 0, row, (len(header_list) * 5),
                                                                  ' ' + new_section, cell_format_merged_plot_header)
                                            worksheet.set_row(row, 16)
                                        row += 1
                                        # mark hilo results with certain color in the hilo sheet
                                        if not self.hilo_value_MIN == 9999:  # if min value available
                                            worksheet.write(self.hilo_pos_MIN_tuple[0], self.hilo_pos_MIN_tuple[1],
                                                            truncate_float(str(self.hilo_value_MIN), 3), cell_format_hilo_MIN)
                                        if not self.hilo_value_MAX == -9999:  # if max value available
                                            worksheet.write(self.hilo_pos_MAX_tuple[0], self.hilo_pos_MAX_tuple[1],
                                                            truncate_float(str(self.hilo_value_MAX), 3), cell_format_hilo_MAX)

                                        # reset hilo variables
                                        self.hilo_value_MIN = 9999
                                        self.hilo_value_MAX = -9999
                                        self.hilo_pos_MIN_tuple = (0, 0)
                                        self.hilo_pos_MAX_tuple = (0, 0)
                                cur_month = new_month

                                # Write timestamp
                                if col == 0:  # write timestamp only once per row
                                    curr_time = float(day_set['dateTime'])
                                    day_timestamp = time.strftime("%a, %d.%m.%Y", time.localtime(curr_time))
                                    day_of_month = time.strftime("%d", time.localtime(curr_time))
                                    worksheet.write(row, col, day_of_month + ' | ' + day_timestamp,
                                                    cell_format_timestamp_left)
                                col += 1

                                # Fill out column 'Low value'
                                current_value_min = day_set['min']
                                if current_value_min:
                                    worksheet.write(row, col, truncate_float(current_value_min, 3),
                                                    cell_format_hilo_data_blue)
                                    _check_hilo_values(self, float(current_value_min), row, col)  # Update HiLo values
                                else:
                                    worksheet.write_formula(row, col, 'na()', cell_format_hilo_data_blue)
                                col += 1

                                # Fill out column 'Low time'
                                if day_set['mintime']:
                                    timestamp_min = time.strftime("%H:%M", time.localtime(float(day_set['mintime'])))
                                    worksheet.write(row, col, timestamp_min, cell_format_hilo_data)
                                else:
                                    worksheet.write_formula(row, col, 'na()', cell_format_hilo_data)
                                col += 1

                                # Fill out column 'High value'
                                current_value_max = day_set['max']
                                if current_value_max:
                                    worksheet.write(row, col, truncate_float(current_value_max, 3),
                                                    cell_format_hilo_data_blue)
                                    _check_hilo_values(self, float(current_value_max), row, col)  # Update HiLo values
                                else:
                                    worksheet.write_formula(row, col, 'na()', cell_format_hilo_data_blue)
                                col += 1

                                # Fill out column 'High time'
                                if day_set['maxtime']:
                                    timestamp_max = time.strftime("%H:%M", time.localtime(float(day_set['maxtime'])))
                                    worksheet.write(row, col, timestamp_max, cell_format_hilo_data)
                                else:
                                    worksheet.write_formula(row, col, 'na()', cell_format_hilo_data)

                                # Fill empty cells with background/border color
                                worksheet.write(row, col + 1, '', cell_format_filler_cell_hilo)
                                # increase row count as current dataset has been written
                                row += 1
                                if rows_meta < row:  # keep track of row count
                                    rows_meta = row
                            col_meta += 5
                            header_structure_created = True
                            # mark hilo results with certain color in the hilo sheet
                            if not self.hilo_value_MIN == 9999:  # if min value available
                                worksheet.write(self.hilo_pos_MIN_tuple[0], self.hilo_pos_MIN_tuple[1],
                                                truncate_float(str(self.hilo_value_MIN), 3), cell_format_hilo_MIN)
                            if not self.hilo_value_MAX == -9999:  # if max value available
                                worksheet.write(self.hilo_pos_MAX_tuple[0], self.hilo_pos_MAX_tuple[1],
                                                truncate_float(str(self.hilo_value_MAX), 3), cell_format_hilo_MAX)
                            # reset hilo variables
                            self.hilo_value_MIN = 9999
                            self.hilo_value_MAX = -9999
                            self.hilo_pos_MIN_tuple = (0, 0)
                            self.hilo_pos_MAX_tuple = (0, 0)

                        # create and add hilo charts
                        worksheet.merge_range(rows_meta, 0, rows_meta, (len(header_list) * 5),
                                              'HiLo Statistics Plot', cell_format_merged_header_hilo)
                        worksheet.set_row(rows_meta, 18)
                        rows_raw = rows_meta + 1
                        rows_meta += 2
                        col_data = 1
                        for char_i in range(len(header_list)):  # add one chart per sensor value
                            title_current_chart = header_list[char_i][:header_list[char_i].find('[') - 1]
                            # add line type plot and set chart properties
                            weather_hilo_plot = workbook.add_chart({'type': 'line'})
                            weather_hilo_plot.set_plotarea({
                                'gradient': {'colors': ['#e6e6e6', '#d9d9d9', '#b3b3b3']}
                            })
                            weather_hilo_plot.set_chartarea({
                                'border': {'none': True},
                                'fill': {'color': '#f2f2f2'}
                            })
                            # create one plot for every sensor with one high and one low series respectively
                            # low values series
                            col_shift_cols = char_i * 5
                            weather_hilo_plot.add_series({
                                'name': [hilo_sheet_name, 3, col_data + col_shift_cols],
                                'categories': [hilo_sheet_name, 5, 0, rows_raw - 2, 0],
                                'values': [hilo_sheet_name, 5, col_data + col_shift_cols, rows_raw - 2,
                                           col_data + col_shift_cols],
                                'line': {'color': '#7370ea'}
                            })
                            # high values series
                            weather_hilo_plot.add_series({
                                'name': [hilo_sheet_name, 3, col_data + col_shift_cols + 2],
                                'values': [hilo_sheet_name, 5, col_data + col_shift_cols + 2, rows_raw - 2,
                                           col_data + col_shift_cols + 2],
                                'line': {'color': '#ef2d47'}
                            })
                            # Finalize currents month sheet plot -> add a chart title and axi-labels
                            weather_hilo_plot.set_title({
                                'name': title_current_chart,
                                'name_font': {'color': '#0065BD'}
                            })
                            weather_hilo_plot.set_x_axis({
                                'name': 'Date'
                            })
                            weather_hilo_plot.set_y_axis({
                                'name': header_list[char_i][
                                        header_list[char_i].find('[') + 1:header_list[char_i].find(']')],
                                'name_font': {
                                    'color': '#0065BD',
                                    'bold': True,
                                    'size': 14
                                },
                                'num_font': {
                                    'bold': True
                                }
                            })
                            weather_hilo_plot.set_legend({'position': 'bottom'})  # or 'none' to turn legend off
                            # add chart on WeatherPlot sheet
                            worksheet.insert_chart(rows_meta, 1, weather_hilo_plot,
                                                   {'x_scale': 4, 'y_scale': 2})
                            rows_meta += 30
                        if len(header_list) >= 3:  # at least 3 sensors are being exported
                            header_export_lenght = (len(header_list) * 5) + 1
                        elif len(header_list) == 2:  # exactly two sensors are being exported
                            header_export_lenght = 19
                        else:  # only one sensor exported
                            header_export_lenght = 26
                        for row_fill in range(rows_raw, rows_meta):  # fill cells around plots with background color
                            for col_fill in range(header_export_lenght):
                                worksheet.write(row_fill, col_fill, '', cell_format_filler_cell)

                # if checkbox for plotting has been checked
                if MAIN_INSTANCE.checkBox_exportPlot.isChecked():
                    # create plot sheet
                    worksheet = workbook.add_worksheet('WeatherData Plots')
                    # fill empty cells with background color
                    approx_rows_sheet = (34 * (len(header_list)) * len(sheet_list))
                    for row_i in range(approx_rows_sheet):
                        for col_i in range(30 + 1):
                            worksheet.write(row_i, col_i, '', cell_format_filler_cell)
                    # write chart-sheet header
                    row = 0
                    worksheet.merge_range(row, 0, row + 1, 30,
                                          'CoSESWeather Data Export [Weather Data Charts]', cell_format_merged_header)
                    row = 2
                    worksheet.set_row(row, 16)
                    worksheet.merge_range(row, 0, row, 30,
                                          '| time range: ' + MAIN_INSTANCE.userData_tmpList[2] + ' - ' +
                                          MAIN_INSTANCE.userData_tmpList[3] + ' | rows exported total: ' + str(
                                              rows_selected) +
                                          ' | time step: ' + MAIN_INSTANCE.time_step_str + ' |',
                                          cell_format_merged_secondary_header)
                    worksheet.autofilter(row, 0, approx_rows_sheet, 0)
                    row = 3
                    worksheet.set_column(0, 0, 20)
                    worksheet.freeze_panes(3, 1)

                    # create and add charts
                    for s, sheet in enumerate(sheet_list):  # add chart for every month
                        # mark/add header section for new month
                        worksheet.merge_range(row, 0, row, 30,
                                              ' ' + sheet, cell_format_merged_plot_header)
                        worksheet.set_row(row, 16)
                        row += 2
                        for s_row in range(len(header_list)):  # add one chart per sensor value
                            for row_i in range(row - 1, row + 30):  # add month to filter cell
                                worksheet.write(row_i, 0, sheet, cell_format_filler_cell)
                            title_current_chart = header_list[s_row][:header_list[s_row].find('[') - 1]
                            # add line type plot and set chart properties
                            weather_plot = workbook.add_chart({'type': 'line'})
                            weather_plot.set_plotarea({
                                'gradient': {'colors': ['#e6e6e6', '#d9d9d9', '#b3b3b3']}
                            })
                            weather_plot.set_chartarea({
                                'border': {'none': True},
                                'fill': {'color': '#f2f2f2'}
                            })
                            # get data for plot from every monthly export sheet
                            weather_plot.add_series({
                                'name': title_current_chart,
                                'categories': [sheet, 4, 0, rows_per_month_list[s] + 4, 0],
                                'values': [sheet, 4, s_row + 1, rows_per_month_list[s] + 4, s_row + 1],
                                'line': {'color': '#0065BD'}
                            })
                            # Finalize currents month sheet plot -> add a chart title and axi-labels
                            weather_plot.set_title({
                                'name': title_current_chart,
                                'name_font': {'color': '#0065BD'}
                            })
                            weather_plot.set_x_axis({
                                'name': 'Date'
                            })
                            weather_plot.set_y_axis({
                                'name': header_list[s_row][
                                        header_list[s_row].find('[') + 1:header_list[s_row].find(']')],
                                'name_font': {
                                    'color': '#0065BD',
                                    'bold': True,
                                    'size': 14
                                },
                                'num_font': {
                                    'bold': True
                                }
                            })
                            weather_plot.set_legend({'position': 'bottom'})  # or 'none' to turn legend off
                            # add chart on WeatherPlot sheet
                            worksheet.insert_chart(row, 1, weather_plot,
                                                   {'x_scale': 4, 'y_scale': 2})
                            row += 30

                workbook.close()  # save and close the workbook

            self.emit(QtCore.SIGNAL('signal_export_done(QString)'), "ok;" + str(rows_selected))

        except Exception:  # error occurred
            self.emit(QtCore.SIGNAL('signal_export_done(QString)'), "666;" + str(traceback.format_exc()))
        return


class PHPWorker(QtCore.QThread):
    """
    PHPWorker Thread. Processes calls to the PHP database API script
    """
    def __init__(self, var_process):
        QtCore.QThread.__init__(self)
        self.process_arg = var_process

    def __del__(self):
        self.wait()

    def run(self):
        try:
            data = {}

            # Job0: Get latest sensor dataset
            if self.process_arg == 0:
                data.update({"p_mode": 4
                             })

            # Job1: User login
            elif self.process_arg == 1:
                data.update({"p_mode": 5,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass
                             })

            # Job2: User password change
            elif self.process_arg == 2:
                data.update({"p_mode": 6,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass,
                             "p_pass_new": MAIN_INSTANCE.p_pass_new
                             })

            # Job3: New user account
            elif self.process_arg == 3:
                data.update({"p_mode": 7,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass,
                             "acc_user": MAIN_INSTANCE.userData_tmpList[0],
                             "acc_pass": MAIN_INSTANCE.userData_tmpList[1],
                             "acc_email": MAIN_INSTANCE.userData_tmpList[2],
                             "acc_admin": MAIN_INSTANCE.userData_tmpList[3]
                             })

            # Job4: Delete user account
            elif self.process_arg == 4:
                data.update({"p_mode": 8,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass,
                             "acc_email": MAIN_INSTANCE.userData_tmpList[0],
                             "a_reason": MAIN_INSTANCE.userData_tmpList[1]
                             })

            # Job5: Change account password
            elif self.process_arg == 5:
                data.update({"p_mode": 9,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass,
                             "acc_pass": MAIN_INSTANCE.userData_tmpList[0],
                             "acc_email": MAIN_INSTANCE.userData_tmpList[1],
                             "a_reason": MAIN_INSTANCE.userData_tmpList[2]
                             })

            # Job6: Reset microcontroller
            elif self.process_arg == 6:
                data.update({"p_mode": 10,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass,
                             "a_reason": MAIN_INSTANCE.userData_tmpList[0]
                             })

            # Job7: Restart system
            elif self.process_arg == 7:
                data.update({"p_mode": 11,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass,
                             "a_reason": MAIN_INSTANCE.userData_tmpList[0]
                             })

            # Job8: Get admin log
            elif self.process_arg == 8:
                data.update({"p_mode": 12,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass,
                             "a_prios": MAIN_INSTANCE.userData_tmpList[0]
                             })

            # Job9: Get registered users
            elif self.process_arg == 9:
                data.update({"p_mode": 13,
                             "p_user": MAIN_INSTANCE.p_user,
                             "p_pass": MAIN_INSTANCE.p_pass
                             })

            # Job10: Data export
            elif self.process_arg == 10:
                # Job: export from primary database
                if MAIN_INSTANCE.userData_tmpList[0] == 0:
                    data.update({"p_mode": 15,
                                 "p_user": MAIN_INSTANCE.p_user,
                                 "p_pass": MAIN_INSTANCE.p_pass,
                                 "d_export_mode": MAIN_INSTANCE.userData_tmpList[0],
                                 "d_sensors": MAIN_INSTANCE.userData_tmpList[1],
                                 "d_start": MAIN_INSTANCE.userData_tmpList[2],
                                 "d_stop": MAIN_INSTANCE.userData_tmpList[3],
                                 "d_step": MAIN_INSTANCE.userData_tmpList[4]
                                 })
                # Job: export from secondary database
                elif MAIN_INSTANCE.userData_tmpList[0] == 1:
                    data.update({"p_mode": 15,
                                 "p_user": MAIN_INSTANCE.p_user,
                                 "p_pass": MAIN_INSTANCE.p_pass,
                                 "d_export_mode": MAIN_INSTANCE.userData_tmpList[0],
                                 "d_sensors": MAIN_INSTANCE.userData_tmpList[1],
                                 "d_start": MAIN_INSTANCE.userData_tmpList[2],
                                 "d_stop": MAIN_INSTANCE.userData_tmpList[3],
                                 "d_step": MAIN_INSTANCE.userData_tmpList[4],
                                 "d_hilo": MAIN_INSTANCE.userData_tmpList[5]
                                 })

            # Send query request to PHP script
            php_response = requests.post(MAIN_INSTANCE.system_php_address, data=data)
            try:
                php_response = php_response.json()
                MAIN_INSTANCE.json_data_dict = php_response
            except Exception:
                php_response = php_response.text
                sys.exc_clear()

            # Return results to callback function
            try:
                if '__SUCCESS;' in php_response or '__SUCCESS;' in php_response[0]:  # Valid response
                    self.emit(QtCore.SIGNAL('signal_php(QString)'), "jobID" +
                              str(self.process_arg) + ":" + str(php_response)[:64])
                else:  # error occurred
                    self.emit(QtCore.SIGNAL('signal_php(QString)'), "666;" +
                              str(php_response)[:64] + "_#_" + str(traceback.format_exc()))
            except Exception:  # no data returned
                self.emit(QtCore.SIGNAL('signal_php(QString)'), "666;" +
                          str(php_response)[:64] + "_#_" + str(traceback.format_exc()) + "\nPossibly exceeded maximum allowed PHP memory allocation (memory_limit)?")
        except Exception:  # Error occurred
            self.emit(QtCore.SIGNAL('signal_php(QString)'), "666;" + str(traceback.format_exc()))

        return


class MyApp(QtGui.QTabWidget, CoSESWeatherApp_ui.Ui_CoSESWeatherApp):
    """
    Main GUI Class
    """
    def __init__(self):
        QtGui.QTabWidget.__init__(self)
        CoSESWeatherApp_ui.Ui_CoSESWeatherApp.__init__(self)
        self.setupUi(self)

        self.onRevPi = False
        self.statusOk = False
        self.link_valid = False
        self.php_worker_available = True
        self.loggedIn = False
        self.userData_tmpList = []
        self.json_data_dict = {}
        self.json_data_hilo_dict = {}
        self.system_address = r'http://' + revpi_local_address + r'/weewx'
        self.system_php_address = r'http://' + revpi_local_address + '/db_manager.php'
        version_str = "CoSESWeatherApp " + client_version
        self.setWindowTitle(version_str)
        self.label_version.setText(version_str)
        self.setStyleSheet("""QToolTip {
                                   background-color: #e9f1f4;
                                   color: black;
                                   border: white solid 1px
                                   }""")

        # Logout Buttons
        for i in range(5):  # iterate over all logout buttons
            button = 'pushButton_login_' + str(i)
            getattr(self, button).clicked.connect(self.OnButtonClickedLoginLogout)

        # # # Connect Events and Buttons
        # # tab overview
        self.pushButton_GOTO_weewx.clicked.connect(self.OnButtonClickedTrendViewer)
        self.pushButton_refresh.clicked.connect(self.OnButtonClickedRefresh)
        # # tab data export
        self.interval_items_list_DB1 = ['    5 sec', '    1 min', '    5 min',
                                        '    30 min', '    1 hour', '    12 hours',
                                        '    1 day'
                                        ]

        self.interval_items_list_DB2 = ['    5 min', '    30 min', '    1 hour',
                                        '    12 hours', '    1 day'
                                        ]
        self.file_name_specified = ''
        self.label_savePath.setText('Export will be saved into the current directory of the App.')
        self.pushButton_fileBrowser.clicked.connect(self.OnButtonClickedSaveTo)
        self.export_mode = 0
        self.groupBox_exportADD.hide()
        self.groupBox_exportMain.setMinimumSize(525, 1348)
        self.groupBox_exportMain.setMaximumSize(525, 1348)
        self.groupBox_exportStart.setGeometry(10, 1380 - 112, 505, 71)
        self.groupBox_exportMain.setGeometry(9, 9, 525, 1460 - 112)
        self.checkBox_exportHiLo.hide()
        self.comboBox_formatExport.currentIndexChanged.connect(self.OnComboboxExportFormatChanged)
        self.label_anim.hide()
        self.OnButtonClickedSelectAll()
        self.pushButton_exportStart.clicked.connect(self.OnButtonClickedExportStart)
        self.pushButton_exportFolder.clicked.connect(self.OnButtonClickedExportOpenFolder)
        self.comboBox_DB.currentIndexChanged.connect(self.OnComboboxChanged_DB)
        self.pushButton_selectAll.clicked.connect(self.OnButtonClickedSelectAll)
        self.pushButton_deselectAll.clicked.connect(self.OnButtonClickedDeselectAll)
        self.calendarWidget_dateStart.clicked[QtCore.QDate].connect(self.OnCalendarClickedStartDate)
        self.calendarWidget_dateStop.clicked[QtCore.QDate].connect(self.OnCalendarClickedStopDate)
        self.OnCalendarClickedStartDate(self.calendarWidget_dateStart.selectedDate())
        self.OnCalendarClickedStopDate(self.calendarWidget_dateStop.selectedDate())
        # add cell formatting styles
        self.cell_format_merged_header_DICT = {
            'bold': True,
            'border': True,
            'font_size': '13',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#c6c6c6'
        }
        self.cell_format_merged_plot_header_DICT = {
            'bold': True,
            'border': True,
            'font_size': '11',
            'font_name': 'Arial',
            'align': 'left',
            'valign': 'vcenter',
            'font_color': '#f2f2f2',
            'bg_color': '#808080'
        }
        self.cell_format_filler_cell_DICT = {
            'bg_color': '#f2f2f2',
            'font_color': '#f2f2f2'
        }
        self.cell_format_merged_secondary_header_DICT = {
            'bold': True,
            'border': True,
            'font_size': '8',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#c6c6c6'
        }
        self.cell_format_header_DICT = {
            'bold': True,
            'border': True,
            'font_color': '#0065BD',
            'bg_color': '#efefef',
            'font_size': '11',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter'
        }
        self.cell_format_timestamp_DICT = {
            'bold': True,
            'border': True,
            'font_size': '11',
            'bg_color': '#efefef',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter'
        }
        self.cell_format_timestamp_left_DICT = {
            'bold': True,
            'border': True,
            'font_size': '11',
            'bg_color': '#efefef',
            'font_name': 'Arial',
            'align': 'left',
            'valign': 'vcenter'
        }
        self.cell_format_data_DICT = {
            'bold': False,
            'border': True,
            'font_size': '11',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter'
        }
        self.cell_format_merged_header_hilo_DICT = {
            'bold': True,
            'border': True,
            'font_size': '13',
            'font_name': 'Arial',
            'align': 'left',
            'valign': 'vcenter',
            'fg_color': '#c6c6c6'
        }
        self.cell_format_hilo_data_DICT = {
            'border': True,
            'font_size': '11',
            'bg_color': '#efefef',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter'
        }
        self.cell_format_hilo_data_blue_DICT = {
            'bold': True,
            'border': True,
            'font_size': '11',
            'bg_color': '#efefef',
            'font_color': '#0065BD',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter'
        }
        self.cell_format_filler_cell_hilo_DICT = {
            'bg_color': '#c6c6c6',
            'font_color': '#c6c6c6'
        }
        self.cell_format_hilo_MIN_DICT = {
            'bold': True,
            'border': True,
            'font_size': '11',
            'bg_color': '#efefef',
            'font_color': '#7370ea',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter'
        }
        self.cell_format_hilo_MAX_DICT = {
            'bold': True,
            'border': True,
            'font_size': '11',
            'bg_color': '#efefef',
            'font_color': '#ef2d47',
            'font_name': 'Arial',
            'align': 'center',
            'valign': 'vcenter'
        }
        # # tab account data
        QtGui.QTabWidget.setTabEnabled(self, 2, False)  # disable tab account data as only accessible for logged in users
        # tab account data - user data
        self.pushButton_changePass.clicked.connect(self.OnButtonClickedChangePassUser)
        # tab account data - administration
        self.tabWidget_acc.currentChanged.connect(self.OnTabChangedAccData)
        self.lineEdit_acmdReason.setEnabled(False)
        self.radioButton_AdminNo.setChecked(True)
        self.groupBox_adminLog.hide()
        self.tableWidget_adminLog.hide()
        self.groupBox_usersTotal.hide()
        self.comboBox_acmd.currentIndexChanged.connect(self.OnComboboxAdminCommandChanged_1)
        self.comboBox_uC_cmd.currentIndexChanged.connect(self.OnComboboxAdminCommandChanged_2)
        self.pushButton_acmdExecute.clicked.connect(self.OnButtonClickedACMD_Execute_1)
        self.pushButton_acmdExecute_2.clicked.connect(self.OnButtonClickedACMD_Execute_2)
        self.pushButton_adminLog.clicked.connect(self.OnButtonClickedAdminLog)
        self.checkBox_prio_1.stateChanged.connect(self.OnCheckboxStateChanged_ALogPrio)
        self.checkBox_prio_2.stateChanged.connect(self.OnCheckboxStateChanged_ALogPrio)
        self.checkBox_prio_3.stateChanged.connect(self.OnCheckboxStateChanged_ALogPrio)
        self.checkBox_prio_1.setChecked(True)
        self.checkBox_prio_2.setChecked(True)
        self.checkBox_prio_3.setChecked(True)
        self.checkBox_prio_1.hide()
        self.checkBox_prio_2.hide()
        self.checkBox_prio_3.hide()
        # Admin Log Widget
        self.tableWidget_adminLog.setColumnCount(5)
        self.tableWidget_adminLog.setColumnWidth(0, 160)
        self.tableWidget_adminLog.setColumnWidth(1, 150)
        self.tableWidget_adminLog.setColumnWidth(2, 120)
        self.tableWidget_adminLog.setColumnWidth(3, 110)
        self.tableWidget_adminLog.setColumnWidth(4, 130)
        self.tableWidget_adminLog.setHorizontalHeaderLabels(
            ['Username', 'Action', 'Reason', 'Priority', 'Time'])
        self.tableWidget_adminLog.horizontalHeader().setVisible(True)
        # Registered Users Log Widget
        self.tableWidget_regUsers.setColumnCount(4)
        self.tableWidget_regUsers.setColumnWidth(0, 135)
        self.tableWidget_regUsers.setColumnWidth(1, 50)
        self.tableWidget_regUsers.setColumnWidth(2, 190)
        self.tableWidget_regUsers.setColumnWidth(3, 130)
        self.tableWidget_regUsers.setHorizontalHeaderLabels(
            ['Username', 'Admin', 'Email', 'Last Login'])
        self.tableWidget_regUsers.horizontalHeader().setVisible(True)
        # # tab info
        self.pushButton_WEBISTE.clicked.connect(self.OnButtonClickedWebsite)

        self.check_system_status()  # check and startup main system
        return

    def closeEvent(self, event):
        """
        Gets called on closeEvent
        :param event
        :return: --
        """
        if self.loggedIn:  # if user logged in
            confirm_abort_final = QtGui.QMessageBox()
            confirm_abort_final.setIcon(QtGui.QMessageBox.Warning)
            confirm_abort_final.setWindowIcon(QtGui.QIcon(path_logo_box))
            confirm_abort_final.setText(u"You are currently logged in.\n"
                                        u"Are you sure you want to logout and close the Application?")
            confirm_abort_final.setWindowTitle(u'Exit')
            confirm_abort_final.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            button_yes = confirm_abort_final.button(QtGui.QMessageBox.Yes)
            button_yes.setText('Yes')
            button_no = confirm_abort_final.button(QtGui.QMessageBox.No)
            button_no.setText('No')
            confirm_abort_final.show()
            confirm_abort_final.exec_()
            if confirm_abort_final.clickedButton() == button_yes:
                self.CloseAllWidgets()
                event.accept()
            elif confirm_abort_final.clickedButton() == button_no:
                event.ignore()
        elif self.onRevPi and self.statusOk:  # if system running on RevPi
            confirm_abort_final = QtGui.QMessageBox()
            confirm_abort_final.setIcon(QtGui.QMessageBox.Warning)
            confirm_abort_final.setWindowIcon(QtGui.QIcon(path_logo_box))
            confirm_abort_final.setText(u"The Application should be kept running on RevPi!\n"
                                        u"Are you sure you want to exit?")
            confirm_abort_final.setWindowTitle(u'Confirm request')
            confirm_abort_final.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            button_yes = confirm_abort_final.button(QtGui.QMessageBox.Yes)
            button_yes.setText('Yes')
            button_no = confirm_abort_final.button(QtGui.QMessageBox.No)
            button_no.setText('No')
            confirm_abort_final.show()
            confirm_abort_final.exec_()
            if confirm_abort_final.clickedButton() == button_yes:
                self.CloseAllWidgets()
                event.accept()
            elif confirm_abort_final.clickedButton() == button_no:
                event.ignore()
        else:
            self.CloseAllWidgets()
            event.accept()
        return

    def keyPressEvent(self, event):
        """
        Gets called on keyPressEvent
        :param event
        :return: --
        """
        if self.php_worker_available:
            key = event.key()
            if key == QtCore.Qt.Key_Escape:  # When pressing ESC
                self.close()  # close app
            elif key == QtCore.Qt.Key_F1:  # When pressing F1
                self.OnButtonClickedLoginLogout()  # login/logout user
            elif key == QtCore.Qt.Key_Enter or key == QtCore.Qt.Key_Return:  # When pressing Enter
                if self.stab_2.isVisible() and not self.tableWidget_adminLog.isVisible():  # if administration tab is visible
                    if self.comboBox_uC_cmd.hasFocus() or self.lineEdit_uC_reason.hasFocus() or \
                            self.pushButton_acmdExecute_2.hasFocus():
                        self.OnButtonClickedACMD_Execute_2()  # send admin command to system
                    else:
                        self.OnButtonClickedACMD_Execute_1()  # modify user accounts
                elif self.tab.isVisible():  # if overview tab is visible
                    self.OnButtonClickedTrendViewer()  # open trend-viewer
                elif self.tab1.isVisible():  # if data export tab is visible
                    self.OnButtonClickedExportStart()  # start data export
            elif key == QtCore.Qt.Key_F11:  # When pressing F11
                try:
                    previous_index = self.currentIndex() - 1
                    if self.isTabEnabled(previous_index):
                        self.setCurrentIndex(previous_index)  # goto the previous tab
                    else:  # if the supposed tab is not enabled skip it
                        self.setCurrentIndex(previous_index - 1)  # goto the previous previous tab
                except Exception:
                    pass
            elif key == QtCore.Qt.Key_F12:  # When pressing F12
                try:
                    next_index = self.currentIndex() + 1
                    if self.isTabEnabled(next_index):
                        self.setCurrentIndex(next_index)  # goto the next tab
                    else:  # if the supposed tab is not enabled skip it
                        self.setCurrentIndex(next_index + 1)  # goto the next next tab
                except Exception:
                    pass
        return

    def CloseAllWidgets(self):
        """
        Closes all windows of CoSESWeather-App. Used onExit
        :param: --
        :return: --
        """
        MAIN_INSTANCE_LOGIN.close()
        MAIN_INSTANCE_PASS.close()
        MAIN_INSTANCE_TrendViewer.close()
        return

    def OnTabChangedAccData(self):
        """
        Called when the tab in the account data tab child tab changes
        :param: --
        :return: --
        """
        self.groupBox_usersTotal.hide()
        if self.stab_2.isVisible():  # if tab 'Administration' is visible: show 'Show Admin Log' button
            self.groupBox_adminLog.show()
            if self.tableWidget_adminLog.isVisible():
                self.OnCheckboxStateChanged_ALogPrio()  # update admin log
        else:
            self.groupBox_adminLog.hide()
            if self.stab_3.isVisible():
                self.groupBox_usersTotal.show()
                self.execute_php_job(9)  # get registered users list
        return

    def OnComboboxChanged_DB(self):
        """
        Called when first Combobox in 'Data Export' Tab is changed
        :param: --
        :return: --
        """
        if 'Primary Database' in self.comboBox_DB.currentText():  # primary database chosen
            self.export_mode = 0
            self.checkBox_exportHiLo.hide()
            self.lineEdit_DB.setText('Raw Weather Data')
            self.comboBox_intervalExport.clear()
            self.comboBox_intervalExport.addItems(self.interval_items_list_DB1)
        else:  # secondary database chosen
            self.export_mode = 1
            self.checkBox_exportHiLo.show()
            self.lineEdit_DB.setText('WeeWx Weather Data')
            self.comboBox_intervalExport.clear()
            self.comboBox_intervalExport.addItems(self.interval_items_list_DB2)
        return

    def OnComboboxExportFormatChanged(self):
        """
        Called when Combobox for Export-Format is changed in Tab 'Data Export'
        :param: --
        :return: --
        """
        if '.txt' in self.comboBox_formatExport.currentText():  # .txt format chosen for export
            self.groupBox_exportADD.hide()
            self.groupBox_exportMain.setMinimumSize(525, 1348)
            self.groupBox_exportMain.setMaximumSize(525, 1348)
            self.groupBox_exportStart.setGeometry(10, 1380 - 112, 505, 71)
            self.groupBox_exportMain.setGeometry(9, 9, 525, 1460 - 112)
        elif '.csv' in self.comboBox_formatExport.currentText():  # .csv format chosen for export
            self.groupBox_exportADD.hide()
            self.groupBox_exportMain.setMinimumSize(525, 1348)
            self.groupBox_exportMain.setMaximumSize(525, 1348)
            self.groupBox_exportStart.setGeometry(10, 1380 - 112, 505, 71)
            self.groupBox_exportMain.setGeometry(9, 9, 525, 1460 - 112)
        elif '.xlsx' in self.comboBox_formatExport.currentText():  # .xlsx format chosen for export
            self.groupBox_exportADD.show()
            self.groupBox_exportMain.setMinimumSize(525, 1460)
            self.groupBox_exportMain.setMaximumSize(525, 1460)
            self.groupBox_exportStart.setGeometry(10, 1380, 505, 71)
            self.groupBox_exportMain.setGeometry(9, 9, 525, 1460)
        return

    def OnCalendarClickedStartDate(self, date):
        """
        Gets the date from the CalendarWidget (1) in the Data Export Tab
        :param: --
        :return: --
        """
        date_selected = QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates).toString(date, "yyyy-MM-dd")
        self.lineEdit_chosenDate_start.setText(date_selected)
        return

    def OnCalendarClickedStopDate(self, date):
        """
        Gets the date from the CalendarWidget (2) in the Data Export Tab
        :param: --
        :return: --
        """
        date_selected = QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates).toString(date, "yyyy-MM-dd")
        self.lineEdit_chosenDate_stop.setText(date_selected)
        return

    def OnButtonClickedSelectAll(self):
        """
        Selects all sensor checkboxes in the Data Export Tab when 'select all' button is clicked
        :param: --
        :return: --
        """
        self.checkBox_temp.setChecked(True)
        self.checkBox_wind.setChecked(True)
        self.checkBox_radTot.setChecked(True)
        self.checkBox_radDiff.setChecked(True)
        self.checkBox_sun.setChecked(True)
        self.checkBox_rad1.setChecked(True)
        self.checkBox_rad2.setChecked(True)
        self.checkBox_rad3.setChecked(True)
        return

    def OnButtonClickedDeselectAll(self):
        """
        Deselects all sensor checkboxes in the Data Export Tab when 'deselect all' button is clicked
        :param: --
        :return: --
        """
        self.checkBox_temp.setChecked(False)
        self.checkBox_wind.setChecked(False)
        self.checkBox_radTot.setChecked(False)
        self.checkBox_radDiff.setChecked(False)
        self.checkBox_sun.setChecked(False)
        self.checkBox_rad1.setChecked(False)
        self.checkBox_rad2.setChecked(False)
        self.checkBox_rad3.setChecked(False)
        return

    def OnButtonClickedSaveTo(self):
        """
        Opens a file dialog window to change the export file path when 'Save to ...' button in Tab 'Data Export'
        is clicked
        :param: --
        :return: --
        """
        file_format = self.comboBox_formatExport.currentText()
        if '.txt' in file_format:  # .txt format chosen for export
            file_format_extension = '.txt'
        elif '.csv' in file_format:  # .csv format chosen for export
            file_format_extension = '.csv'
        elif '.xlsx' in file_format:  # .xlsx format chosen for export
            file_format_extension = '.xlsx'
        # open file dialog window
        file_name = str(QtGui.QFileDialog.getSaveFileName(self, 'Choose Export Path', '',
                                                  "CoSESWeather File-Export (*" + file_format_extension + ")"))
        if os.path.exists(file_name[:file_name.rfind('/')]):  # file exists
            self.label_savePath.setText('Save to: ' + file_name)
            self.file_name_specified = file_name
        else:  # file does not exist
            self.label_savePath.setText('Export will be saved into the current directory of the App.')
            self.file_name_specified = ''
        return

    def OnButtonClickedExportOpenFolder(self):
        """
        Opens the directory where the export has been save to when 'Open Folder' button in Tab 'Data Export' is clicked
        :param: --
        :return: --
        """
        try:
            export_path = os.path.join('.', os.path.normpath(self.file_name_export))

            # open exported file in explorer
            if self.check_os_windows():  # windows
                if os.path.isfile(export_path):  # file exists
                    subprocess.Popen(["explorer", "/select,", export_path])
                else:  # file does not exist
                    self.ShowMessageBox(u"File not found", u"The latest export-file could not be found!\n"
                                                           u"Has the file been moved or deleted?", 1)
            else:  # linux
                if os.path.isfile(export_path):  # file exists
                    self.ShowMessageBox(u"Feature not available", u"This feature is not available on the current "
                                                    u"system.\nPlease navigate to the specified path manually", 0)
                else:  # file does not exist
                    self.ShowMessageBox(u"File not found", u"The latest export-file could not be found!\n"
                                                           u"Has the file been moved or deleted?", 1)
        except Exception:
            self.ShowMessageBox(u"File not found", u"Could not find any export-file!\n"
                                                   u"Did you already start a file export in the current session?", 1)
        return

    def check_os_windows(self):
        """
        Checks whether the current OS is Windows or Unix. Returns True for WINDOWS and False for UNIX
        :param: --
        :return True/False: boolean
        """
        platform_os = sys.platform
        if platform_os == "win32" or platform_os == "cygwin":  # Windows
            return True
        else:  # Unix OS
            return False

    def OnExportStart(self):
        """
        Called when the Data Export in Tab 'Data Export' is started. Disables all buttons and starts animation
        :param: --
        :return: --
        """
        self.setEnabled(False)
        self.label_anim.show()
        self.movie_anim = QtGui.QMovie(resource_path("anim_processing.gif"))
        self.label_anim.setMovie(self.movie_anim)
        self.movie_anim.start()
        return

    def OnExportFinish(self):
        """
        Called when the Data Export in Tab 'Data Export' is finished. (re)enables all buttons and stops animation
        :param: --
        :return: --
        """
        self.movie_anim.stop()
        self.label_anim.hide()
        self.setEnabled(True)
        return

    def OnButtonClickedExportStart(self):
        """
        Starts the Data Export when 'Start Export' button in Tab 'Data Export' is clicked
        :param: --
        :return: --
        """
        if self.link_valid:  # connection to RevPi established
            if self.loggedIn:  # if user logged in
                del self.userData_tmpList[:]
                # at least one checkbox must be checked
                if not self.checkBox_temp.isChecked() and not self.checkBox_wind.isChecked() \
                        and not self.checkBox_radTot.isChecked() and not self.checkBox_radDiff.isChecked() \
                        and not self.checkBox_sun.isChecked() and not self.checkBox_rad1.isChecked() \
                        and not self.checkBox_rad2.isChecked() and not self.checkBox_rad3.isChecked():
                    self.ShowMessageBox(u"Error", u"Please select at least one data source (sensor) "
                                                  u"to be included in the export.", 1)
                else:  # start export
                    if self.export_mode == 0:  # Export from primary database (raw data)
                        confirm_job_final = QtGui.QMessageBox()
                        confirm_job_final.setIcon(QtGui.QMessageBox.Question)
                        confirm_job_final.setWindowIcon(QtGui.QIcon(path_logo_box))
                        confirm_job_final.setText(u"Do you want to start the specified data-export?")
                        confirm_job_final.setWindowTitle(u'Data Export')
                        confirm_job_final.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                        button_yes = confirm_job_final.button(QtGui.QMessageBox.Yes)
                        button_yes.setText('Yes')
                        button_no = confirm_job_final.button(QtGui.QMessageBox.No)
                        button_no.setText('No')
                        confirm_job_final.show()
                        confirm_job_final.exec_()
                        if confirm_job_final.clickedButton() == button_yes:
                            pass
                        elif confirm_job_final.clickedButton() == button_no:
                            return
                        self.OnExportStart()

                        # get required sensor values
                        sensor_select_string = ''
                        if self.checkBox_temp.isChecked():
                            sensor_select_string += 'temp, '
                        if self.checkBox_wind.isChecked():
                            sensor_select_string += 'wind, '
                        if self.checkBox_radTot.isChecked():
                            sensor_select_string += 'spn1_radTot, '
                        if self.checkBox_radDiff.isChecked():
                            sensor_select_string += 'spn1_radDiff, '
                        if self.checkBox_sun.isChecked():
                            sensor_select_string += 'spn1_sun, '
                        if self.checkBox_rad1.isChecked():
                            sensor_select_string += 'rad_cmp1, '
                        if self.checkBox_rad2.isChecked():
                            sensor_select_string += 'rad_cmp2, '
                        if self.checkBox_rad3.isChecked():
                            sensor_select_string += 'rad_cmp3, '

                        # get selected start/stop date and time
                        date_selected_start = self.lineEdit_chosenDate_start.text()
                        date_selected_stop = self.lineEdit_chosenDate_stop.text()
                        selected_time_start = self.timeEdit_startDate.time().toString()
                        selected_time_stop = self.timeEdit_stopDate.time().toString()
                        # append required job parameters to list
                        self.userData_tmpList.append(0)  # export mode
                        self.sensor_select = sensor_select_string.strip(', ')
                        self.userData_tmpList.append(self.sensor_select)
                        # date/time needs to have this format for MySQL query: '2010-10-01 12:00:00'
                        self.userData_tmpList.append(str(date_selected_start + ' ' + selected_time_start))
                        self.userData_tmpList.append(str(date_selected_stop + ' ' + selected_time_stop))

                        # get time step
                        if '5 sec' in self.comboBox_intervalExport.currentText():  # step size = 5 seconds
                            self.time_step_str = '5 seconds'
                            self.time_step_int = 5
                        elif '1 min' in self.comboBox_intervalExport.currentText():  # step size = 1 minute
                            self.time_step_str = '1 minute'
                            self.time_step_int = 60
                        elif '5 min' in self.comboBox_intervalExport.currentText():  # step size = 5 minutes
                            self.time_step_str = '5 minutes'
                            self.time_step_int = 300
                        elif '30 min' in self.comboBox_intervalExport.currentText():  # step size = 30 minutes
                            self.time_step_str = '30 minutes'
                            self.time_step_int = 1800
                        elif '1 hour' in self.comboBox_intervalExport.currentText():  # step size = 1 hour
                            self.time_step_str = '1 hour'
                            self.time_step_int = 3600
                        elif '12 hours' in self.comboBox_intervalExport.currentText():  # step size = 12 hours
                            self.time_step_str = '12 hours'
                            self.time_step_int = 43200
                        elif '1 day' in self.comboBox_intervalExport.currentText():  # step size = 1 day
                            self.time_step_str = '1 day'
                            self.time_step_int = 86400
                        else:  # step size = 5 seconds
                            self.time_step_str = '5 seconds'
                            self.time_step_int = 5
                        # set time step (integer in seconds)
                        self.userData_tmpList.append(self.time_step_int)

                    # Export from secondary database (weewx)
                    elif self.export_mode == 1:
                        confirm_job_final = QtGui.QMessageBox()
                        confirm_job_final.setIcon(QtGui.QMessageBox.Question)
                        confirm_job_final.setWindowIcon(QtGui.QIcon(path_logo_box))
                        confirm_job_final.setText(u"Do you want to start the specified data-export?")
                        confirm_job_final.setWindowTitle(u'Data Export')
                        confirm_job_final.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                        button_yes = confirm_job_final.button(QtGui.QMessageBox.Yes)
                        button_yes.setText('Yes')
                        button_no = confirm_job_final.button(QtGui.QMessageBox.No)
                        button_no.setText('No')
                        confirm_job_final.show()
                        confirm_job_final.exec_()
                        if confirm_job_final.clickedButton() == button_yes:
                            pass
                        elif confirm_job_final.clickedButton() == button_no:
                            return
                        self.OnExportStart()

                        # get required sensor values
                        sensor_select_string = ''
                        if self.checkBox_temp.isChecked():
                            sensor_select_string += 'outTemp, '
                        if self.checkBox_wind.isChecked():
                            sensor_select_string += 'windSpeed, '
                        if self.checkBox_radTot.isChecked():
                            sensor_select_string += 'radiation, '
                        if self.checkBox_radDiff.isChecked():
                            sensor_select_string += 'radiationDiff, '
                        if self.checkBox_sun.isChecked():
                            sensor_select_string += 'sun, '
                        if self.checkBox_rad1.isChecked():
                            sensor_select_string += 'radiation1, '
                        if self.checkBox_rad2.isChecked():
                            sensor_select_string += 'radiation2, '
                        if self.checkBox_rad3.isChecked():
                            sensor_select_string += 'radiation3, '

                        # get selected start/stop date and time
                        date_selected_start = self.lineEdit_chosenDate_start.text()
                        date_selected_stop = self.lineEdit_chosenDate_stop.text()
                        selected_time_start = self.timeEdit_startDate.time().toString()
                        selected_time_stop = self.timeEdit_stopDate.time().toString()
                        # append required job parameters to list
                        self.userData_tmpList.append(1)  # export mode
                        self.sensor_select = sensor_select_string.strip(', ')
                        self.userData_tmpList.append(self.sensor_select)
                        # date/time needs to have this format for MySQL query: '2010-10-01 12:00:00'
                        self.userData_tmpList.append(str(date_selected_start + ' ' + selected_time_start))
                        self.userData_tmpList.append(str(date_selected_stop + ' ' + selected_time_stop))

                        # get time step
                        if '5 min' in self.comboBox_intervalExport.currentText():  # step size = 5 minutes
                            self.time_step_str = '5 minutes'
                            self.time_step_int = 300
                        elif '30 min' in self.comboBox_intervalExport.currentText():  # step size = 30 minutes
                            self.time_step_str = '30 minutes'
                            self.time_step_int = 1800
                        elif '1 hour' in self.comboBox_intervalExport.currentText():  # step size = 1 hour
                            self.time_step_str = '1 hour'
                            self.time_step_int = 3600
                        elif '12 hours' in self.comboBox_intervalExport.currentText():  # step size = 12 hours
                            self.time_step_str = '12 hours'
                            self.time_step_int = 43200
                        elif '1 day' in self.comboBox_intervalExport.currentText():  # step size = 1 day
                            self.time_step_str = '1 day'
                            self.time_step_int = 86400
                        else:  # step size = 5 seconds
                            self.time_step_str = '5 minutes'
                            self.time_step_int = 300

                        # set time step (integer in seconds)
                        self.userData_tmpList.append(self.time_step_int)

                        if self.checkBox_exportHiLo.isChecked():  # include hi/lo statistic in export is checked
                            self.userData_tmpList.append(1)
                        else:  # not checked - do not include statistics
                            self.userData_tmpList.append(0)

                    # start export job
                    self.execute_php_job(10)

            else:  # user not logged in
                self.ShowMessageBox(u"Feature currently not available",
                                    u"You are currently not logged in!\n"
                                    u"This feature is only available for registered users.\n"
                                    u"Please contact the CoSES-Team in order to register an account.", 1)
        else:  # no connection
            self.ShowMessageBox(u"Feature currently not available",
                                u"Connection to destination system could not be established!\n"
                                u"Please check your connection and server reachability.\n"
                                u"Restart the App to attempt reconnecting to target server.\n"
                                u"Contact the CoSES-Team if the issue persists.", 1)
        return

    def OnButtonClickedRefresh(self):
        """
        Refreshes current conditions in GUI when 'Refresh' button is clicked in Tab 'Overview'
        :param: --
        :return: --
        """
        if self.link_valid:  # connection to RevPi established
            self.execute_php_job(0)
        else:  # no connection
            self.ShowMessageBox(u"Feature currently not available",
                                u"Connection to destination system could not be established!\n"
                                u"Please check your connection and server reachability.\n"
                                u"Restart the App to attempt reconnecting to target server.\n"
                                u"Contact the CoSES-Team if the issue persists.", 1)
        return

    def OnButtonClickedTrendViewer(self):
        """
        Opens the web-based WeeWx Trend-Viewer in a new window or in default web-browser when 'View Weather-Trends'
        button is clicked in Tab 'Overview'
        :param: --
        :return: --
        """
        if self.link_valid:  # links can be reached
            if 'Trend-Viewer' in self.comboBox_viewer.currentText():  # open in trend-viewer
                self.showMinimized()
                MAIN_INSTANCE_TrendViewer.show()
                MAIN_INSTANCE_TrendViewer.showMaximized()
            else:  # open in web-browser
                webbrowser.open(self.system_address)
        else:  # no connection to the RevPi system possible
            self.ShowMessageBox(u"Feature currently not available",
                                u"Connection to destination system could not be established!\n"
                                u"Please check your connection and server reachability.\n"
                                u"Restart the App to attempt reconnecting to target server.\n"
                                u"Contact the CoSES-Team if the issue persists.", 1)
        return

    def OnButtonClickedLoginLogout(self):
        """
        Opens the Login Dialog when 'Login' button is clicked (all Tabs)
        :param: --
        :return: --
        """
        if self.link_valid:  # connection ok
            MAIN_INSTANCE_LOGIN.reset_LoginWidget()
            if self.loggedIn:  # if user already logged in
                confirm_abort_final = QtGui.QMessageBox()
                confirm_abort_final.setIcon(QtGui.QMessageBox.Question)
                confirm_abort_final.setWindowIcon(QtGui.QIcon(path_logo_box))
                confirm_abort_final.setText(u"Are you sure you want to logout?")
                confirm_abort_final.setWindowTitle(u'Logout')
                confirm_abort_final.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                button_yes = confirm_abort_final.button(QtGui.QMessageBox.Yes)
                button_yes.setText('Yes')
                button_no = confirm_abort_final.button(QtGui.QMessageBox.No)
                button_no.setText('No')
                confirm_abort_final.show()
                confirm_abort_final.exec_()
                if confirm_abort_final.clickedButton() == button_yes:
                    self.OnUserLogout()  # logout user
                elif confirm_abort_final.clickedButton() == button_no:
                    pass
            else:  # user not logged in
                MAIN_INSTANCE_LOGIN.lineEdit_user.setFocus()
                MAIN_INSTANCE_LOGIN.show()  # show login dialog
        else:  # no connection
            self.ShowMessageBox(u"Feature currently not available",
                                u"Connection to destination system could not be established!\n"
                                u"Please check your connection and server reachability.\n"
                                u"Restart the App to attempt reconnecting to target server.\n"
                                u"Contact the CoSES-Team if the issue persists.", 1)
        return

    def OnUserLogout(self):
        """
        User logout when 'Logout' button is clicked
        :param: --
        :return: --
        """
        self.loggedIn = False
        QtGui.QTabWidget.setTabEnabled(self, 2, False)  # disable tab account data as only accessible for logged in users
        for i in range(5):  # iterate over all logout buttons and lineEdits
            button = 'pushButton_login_' + str(i)
            getattr(self, button).setText('Login')
            lineEdit = 'lineEdit_loggedin_user_' + str(i)
            getattr(self, lineEdit).setText('--')
            getattr(self, lineEdit).setStyleSheet("font-weight: bold;")
        try:  # if available
            self.movie_anim.stop()
            self.label_anim.hide()
        except Exception:
            pass
        return

    def OnButtonClickedWebsite(self):
        """
        Forwards the user to CoSES Project-Website when 'Goto Project-Website' button on the Info-Tab is clicked
        :param: --
        :return: --
        """
        webbrowser.open(coses_website_address)
        return

    def OnButtonClickedChangePassUser(self):
        """
        Opens the change password window for the user when 'Change Password' button on the account data 'User Data'
        tab is clicked
        :param: --
        :return: --
        """
        MAIN_INSTANCE_PASS.lineEdit_newPass1.clear()
        MAIN_INSTANCE_PASS.lineEdit_newPass2.clear()
        MAIN_INSTANCE_PASS.lineEdit_newPass1.setStyleSheet("font-weight: bold;")
        MAIN_INSTANCE_PASS.lineEdit_newPass2.setStyleSheet("font-weight: bold;")
        MAIN_INSTANCE_PASS.lineEdit_newPass1.setFocus()
        MAIN_INSTANCE_PASS.show()
        return

    def OnButtonClickedAdminLog(self):
        """
        Shows the admin's activity log when 'Show Admin Log' button on the account data 'Administration'
        tab is clicked
        :param: --
        :return: --
        """
        if self.tableWidget_adminLog.isVisible():  # if admin log is displayed
            self.tableWidget_adminLog.hide()  # hide log
            self.pushButton_adminLog.setText('Show Admin Log')
            self.checkBox_prio_1.hide()
            self.checkBox_prio_2.hide()
            self.checkBox_prio_3.hide()
        else:  # if admin log is not yet displayed
            self.OnCheckboxStateChanged_ALogPrio()  # get admin log
            self.tableWidget_adminLog.show()  # show log
            self.checkBox_prio_1.show()
            self.checkBox_prio_2.show()
            self.checkBox_prio_3.show()
            self.pushButton_adminLog.setText('Hide Admin Log')
        return

    def OnCheckboxStateChanged_ALogPrio(self):
        """
        Enables user to select only certain log messages with certain priority to be shown in admin log.
        Called when one of the three checkBoxes 'Info', 'Suspicious' or 'System Events' is (de)selected.
        :param: --
        :return: --
        """
        prio_string = ''
        del self.userData_tmpList[:]
        if self.checkBox_prio_1.isChecked():
            prio_string += '0,'
        if self.checkBox_prio_2.isChecked():
            prio_string += '1,'
        if self.checkBox_prio_3.isChecked():
            prio_string += '2,'
        if not self.checkBox_prio_1.isChecked() and not self.checkBox_prio_2.isChecked()\
                and not self.checkBox_prio_3.isChecked():  # no option checked
                    self.tableWidget_adminLog.setRowCount(0)
        else:
            self.userData_tmpList.append(prio_string.strip(','))
            self.execute_php_job(8)
        return

    def OnButtonClickedACMD_Execute_1(self):
        """
        Executes the specified admin command when 'Execute' (1) button on the account data 'Administration'
        tab is clicked
        :param: --
        :return: --
        """
        del self.userData_tmpList[:]
        if str(self.comboBox_acmd.currentText()).strip() == 'Add Account':
            cmd_text = u"(add user account)"
        elif str(self.comboBox_acmd.currentText()).strip() == 'Delete Account':
            cmd_text = u"(delete user account)"
        elif str(self.comboBox_acmd.currentText()).strip() == 'Change Password':
            cmd_text = u"(change account password)"

        action_text = u"Are you sure you want to execute the task " + cmd_text + u"?\n"
        confirm_job_final = QtGui.QMessageBox()
        confirm_job_final.setIcon(QtGui.QMessageBox.Warning)
        confirm_job_final.setWindowIcon(QtGui.QIcon(path_logo_box))
        confirm_job_final.setText(action_text)
        confirm_job_final.setWindowTitle(u'Execute Task')
        confirm_job_final.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        button_yes = confirm_job_final.button(QtGui.QMessageBox.Yes)
        button_yes.setText('Yes')
        button_no = confirm_job_final.button(QtGui.QMessageBox.No)
        button_no.setText('No')
        confirm_job_final.show()
        confirm_job_final.exec_()
        if confirm_job_final.clickedButton() == button_yes:
            pass
        elif confirm_job_final.clickedButton() == button_no:
            return

        self.lineEdit_acmdReason.setStyleSheet("font-weight: bold;")
        self.lineEdit_acmdUsername.setStyleSheet("font-weight: bold;")
        self.lineEdit_acmdPass.setStyleSheet("font-weight: bold;")
        self.lineEdit_acmdEmail.setStyleSheet("font-weight: bold;")
        # Job: add new user account
        if str(self.comboBox_acmd.currentText()).strip() == 'Add Account':  # Add Account selected
            if str(self.lineEdit_acmdUsername.text()) and str(self.lineEdit_acmdPass.text()) and \
                    str(self.lineEdit_acmdEmail.text()):
                self.lineEdit_acmdUsername.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                self.lineEdit_acmdPass.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                self.lineEdit_acmdEmail.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                self.userData_tmpList.append(str(self.lineEdit_acmdUsername.text()))
                self.userData_tmpList.append(str(self.lineEdit_acmdPass.text()))
                self.userData_tmpList.append(str(self.lineEdit_acmdEmail.text()))
                if self.radioButton_AdminYes.isChecked():  # new account is admin account
                    self.userData_tmpList.append('1')
                else:  # just user account
                    self.userData_tmpList.append('0')
                self.execute_php_job(3)
                self.set_AdminCP_disabled()

            else:  # missing data
                if not str(self.lineEdit_acmdUsername.text()):
                    self.lineEdit_acmdUsername.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                if not str(self.lineEdit_acmdPass.text()):
                    self.lineEdit_acmdPass.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                if not str(self.lineEdit_acmdEmail.text()):
                    self.lineEdit_acmdEmail.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                self.ShowMessageBox(u"Error",
                                    u"Please fill out the form completly!", 1)

        # Job: delete user account
        elif str(self.comboBox_acmd.currentText()).strip() == 'Delete Account':  # Delete Account selected
            if str(self.lineEdit_acmdReason.text()) and str(self.lineEdit_acmdEmail.text()):
                self.lineEdit_acmdReason.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                self.lineEdit_acmdEmail.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                self.userData_tmpList.append(str(self.lineEdit_acmdEmail.text()))
                self.userData_tmpList.append(str(self.lineEdit_acmdReason.text()))
                self.execute_php_job(4)
                self.set_AdminCP_disabled()

            else:  # missing data
                if not str(self.lineEdit_acmdReason.text()):
                    self.lineEdit_acmdReason.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                if not str(self.lineEdit_acmdEmail.text()):
                    self.lineEdit_acmdEmail.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                self.ShowMessageBox(u"Error",
                                    u"Please fill out the form completly!", 1)

        # Job: change password
        elif str(self.comboBox_acmd.currentText()).strip() == 'Change Password':  # Change Password selected
            if str(self.lineEdit_acmdReason.text()) and str(self.lineEdit_acmdPass.text()) and \
                    str(self.lineEdit_acmdEmail.text()):
                self.lineEdit_acmdReason.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                self.lineEdit_acmdPass.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                self.lineEdit_acmdEmail.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                self.userData_tmpList.append(str(self.lineEdit_acmdPass.text()))
                self.userData_tmpList.append(str(self.lineEdit_acmdEmail.text()))
                self.userData_tmpList.append(str(self.lineEdit_acmdReason.text()))
                self.execute_php_job(5)
                self.set_AdminCP_disabled()

            else:  # missing data
                if not str(self.lineEdit_acmdReason.text()):
                    self.lineEdit_acmdReason.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                if not str(self.lineEdit_acmdPass.text()):
                    self.lineEdit_acmdPass.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                if not str(self.lineEdit_acmdEmail.text()):
                    self.lineEdit_acmdEmail.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                self.ShowMessageBox(u"Error",
                                    u"Please fill out the form completly!", 1)
        return

    def OnButtonClickedACMD_Execute_2(self):
        """
        Executes the specified admin command when 'Execute' (2) button on the account data 'Administration'
        tab is clicked
        :param: --
        :return: --
        """
        del self.userData_tmpList[:]
        if str(self.comboBox_uC_cmd.currentText()).strip() == 'Reset Microcontroller':
            cmd_text = u"(microcontroller reset)"
            cmd_info = u"Sensor data acquisition will temporarily be disabled."
        elif str(self.comboBox_uC_cmd.currentText()).strip() == 'Restart System':
            cmd_text = u"(system restart)"
            cmd_info = u"Users will not be able to reach the server until the system is back up."
        action_text = u"Are you sure you want to execute the task " + cmd_text + u"?\n" \
                      u"Warning: This action will temporarily disable the system!\n" + cmd_info
        confirm_job_final = QtGui.QMessageBox()
        confirm_job_final.setIcon(QtGui.QMessageBox.Warning)
        confirm_job_final.setWindowIcon(QtGui.QIcon(path_logo_box))
        confirm_job_final.setText(action_text)
        confirm_job_final.setWindowTitle(u'Execute Task')
        confirm_job_final.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        button_yes = confirm_job_final.button(QtGui.QMessageBox.Yes)
        button_yes.setText('Yes')
        button_no = confirm_job_final.button(QtGui.QMessageBox.No)
        button_no.setText('No')
        confirm_job_final.show()
        confirm_job_final.exec_()
        if confirm_job_final.clickedButton() == button_yes:
            pass
        elif confirm_job_final.clickedButton() == button_no:
            return

        if str(self.lineEdit_uC_reason.text()):  # form filled out
            self.lineEdit_uC_reason.setStyleSheet(
                    "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")

            # Job Reset Microcontroller selected
            if str(self.comboBox_uC_cmd.currentText()).strip() == 'Reset Microcontroller':  # Reset Microcontroller selected
                self.userData_tmpList.append(str(self.lineEdit_uC_reason.text()))
                self.execute_php_job(6)
                self.set_AdminCP_disabled()

            # Job Restart System selected
            elif str(self.comboBox_uC_cmd.currentText()).strip() == 'Restart System':  # Restart System selected
                self.userData_tmpList.append(str(self.lineEdit_uC_reason.text()))
                self.execute_php_job(7)
                self.set_AdminCP_disabled()

        else:  # missing data
            self.lineEdit_uC_reason.setStyleSheet(
                "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
            self.ShowMessageBox(u"Error",
                                u"Please fill out the form completly!", 1)
        return

    def set_AdminCP_disabled(self):
        """
        Disables (greys out) all buttons and lineEdits in the account data 'Administration' Tab.
        :param: --
        :return: --
        """
        self.lineEdit_acmdReason.setEnabled(False)
        self.lineEdit_acmdUsername.setEnabled(False)
        self.lineEdit_acmdPass.setEnabled(False)
        self.lineEdit_acmdEmail.setEnabled(False)
        self.radioButton_AdminNo.setEnabled(False)
        self.radioButton_AdminYes.setEnabled(False)
        self.lineEdit_uC_reason.setEnabled(False)
        self.comboBox_acmd.setEnabled(False)
        self.comboBox_uC_cmd.setEnabled(False)
        self.pushButton_acmdExecute.setEnabled(False)
        self.pushButton_acmdExecute_2.setEnabled(False)
        return

    def set_AdminCP_enabled(self):
        """
        Disables (greys out) all buttons and lineEdits in the account data 'Administration' Tab.
        :param: --
        :return: --
        """
        self.lineEdit_acmdReason.setEnabled(True)
        self.lineEdit_acmdUsername.setEnabled(True)
        self.lineEdit_acmdPass.setEnabled(True)
        self.lineEdit_acmdEmail.setEnabled(True)
        self.radioButton_AdminNo.setEnabled(True)
        self.radioButton_AdminYes.setEnabled(True)
        self.lineEdit_uC_reason.setEnabled(True)
        self.comboBox_acmd.setEnabled(True)
        self.comboBox_uC_cmd.setEnabled(True)
        self.pushButton_acmdExecute.setEnabled(True)
        self.pushButton_acmdExecute_2.setEnabled(True)
        return

    def OnComboboxAdminCommandChanged_1(self, clear=True):
        """
        Called when the ComboBox_1 in the account data 'Administration' Tab is changed
        :param: --
        :return: --
        """
        if clear:
            self.lineEdit_acmdReason.setStyleSheet("font-weight: bold;")
            self.lineEdit_acmdUsername.setStyleSheet("font-weight: bold;")
            self.lineEdit_acmdPass.setStyleSheet("font-weight: bold;")
            self.lineEdit_acmdEmail.setStyleSheet("font-weight: bold;")
            self.lineEdit_acmdReason.clear()
            self.lineEdit_acmdUsername.clear()
            self.lineEdit_acmdPass.clear()
            self.lineEdit_acmdEmail.clear()

        if str(self.comboBox_acmd.currentText()).strip() == 'Add Account':  # Add Account selected
            self.label_acmdText.setText('Add a new user account to the database')
            self.lineEdit_acmdReason.setEnabled(False)
            self.lineEdit_acmdUsername.setEnabled(True)
            self.lineEdit_acmdPass.setEnabled(True)
            self.lineEdit_acmdEmail.setEnabled(True)
            self.radioButton_AdminNo.setEnabled(True)
            self.radioButton_AdminYes.setEnabled(True)
            self.radioButton_AdminNo.setChecked(True)
        elif str(self.comboBox_acmd.currentText()).strip() == 'Delete Account':  # Delete Account selected
            self.label_acmdText.setText('Delete an existing user account from the database')
            self.lineEdit_acmdReason.setEnabled(True)
            self.lineEdit_acmdUsername.setEnabled(False)
            self.lineEdit_acmdPass.setEnabled(False)
            self.lineEdit_acmdEmail.setEnabled(True)
            self.radioButton_AdminNo.setEnabled(False)
            self.radioButton_AdminYes.setEnabled(False)
        elif str(self.comboBox_acmd.currentText()).strip() == 'Change Password':  # Change Password selected
            self.label_acmdText.setText('Change the password of an existing user account')
            self.lineEdit_acmdReason.setEnabled(True)
            self.lineEdit_acmdUsername.setEnabled(False)
            self.lineEdit_acmdPass.setEnabled(True)
            self.lineEdit_acmdEmail.setEnabled(True)
            self.radioButton_AdminNo.setEnabled(False)
            self.radioButton_AdminYes.setEnabled(False)
        return

    def OnComboboxAdminCommandChanged_2(self, clear=True):
        """
        Called when the ComboBox_2 in the account data 'Administration' Tab is changed
        :param: --
        :return: --
        """
        if clear:
            self.lineEdit_uC_reason.setStyleSheet("font-weight: bold;")
            self.lineEdit_uC_reason.clear()
        if str(self.comboBox_uC_cmd.currentText()).strip() == 'Reset Microcontroller':  # Reset Microcontroller selected
            self.label_acmdText_2.setText('Send a reset command to the Microcontroller')
        elif str(self.comboBox_uC_cmd.currentText()).strip() == 'Restart System':  # Restart System selected
            self.label_acmdText_2.setText('Restart complete system including RevPi and Controllino')
        return

    def ShowMessageBox(self, title, message, mode):
        """
        Displays a message dialog box to the user
        :param title: string
        :param message: string
        :param mode: int (0 = Info | 1 = Warning | 2 = Error)
        :return: --
        """
        info_message = QtGui.QMessageBox()
        if mode == 0:  # info
            info_message.setIcon(QtGui.QMessageBox.Information)
        elif mode == 1:  # warning
            info_message.setIcon(QtGui.QMessageBox.Warning)
        else:  # error
            info_message.setIcon(QtGui.QMessageBox.Critical)
        info_message.setWindowIcon(QtGui.QIcon(path_logo_box))
        info_message.setText(message)
        info_message.setWindowTitle(title)
        info_message.show()
        info_message.exec_()
        return

    def check_system_status(self):
        """
        Checks if CoSESWeather-System is fully available and to what degree ready to run
        :param : --
        :return: --
        """
        if check_platform():  # System runs on RevPi
            self.onRevPi = True
            try:  # .ini file can be read
                fail_count = 0
                config = ConfigParser.ConfigParser()
                config.read(path_ini)
                self.lineEdit_status_ini.setStyleSheet("color: rgb(0, 170, 0);")
                self.lineEdit_status_ini.setText("ok")
                # check system status (if necessary files are available on system)
                data_ini = config.get('python_paths', 'path_revpiserver')
                if os.path.isfile(data_ini):
                    self.lineEdit_status_server.setStyleSheet("color: rgb(0, 170, 0);")
                    self.lineEdit_status_server.setText("ok")
                else:
                    fail_count += 1

                data_ini = config.get('php_paths', 'path_db_api')
                if os.path.isfile(data_ini) or os.path.isfile(data_ini.replace('/html', '')):
                    self.lineEdit_status_php.setStyleSheet("color: rgb(0, 170, 0);")
                    self.lineEdit_status_php.setText("ok")
                    self.system_php_address = config.get('php_paths', 'link_db_api')
                else:
                    fail_count += 1
                self.system_address = config.get('config', 'local_address')

                data_ini = config.get('bash_paths', 'path_serverstart')
                if os.path.isfile(data_ini):
                    self.lineEdit_status_bash_manager.setStyleSheet("color: rgb(0, 170, 0);")
                    self.lineEdit_status_bash_manager.setText("ok")
                else:
                    fail_count += 1

                data_ini = config.get('bash_paths', 'path_revpi_watchdog')
                if os.path.isfile(data_ini):
                    self.lineEdit_status_bash_watchdog.setStyleSheet("color: rgb(0, 170, 0);")
                    self.lineEdit_status_bash_watchdog.setText("ok")
                else:
                    fail_count += 1

                data_ini = config.get('bash_paths', 'path_mysql_backup')
                if os.path.isfile(data_ini):
                    self.lineEdit_status_bash_backup.setStyleSheet("color: rgb(0, 170, 0);")
                    self.lineEdit_status_bash_backup.setText("ok")
                else:
                    fail_count += 1

                data_ini = config.get('weewx_paths', 'path_weewx_root')
                if os.path.isdir(data_ini):
                    self.lineEdit_status_weewx_folder.setStyleSheet("color: rgb(0, 170, 0);")
                    self.lineEdit_status_weewx_folder.setText("ok")
                else:
                    fail_count += 1

                data_ini = config.get('weewx_paths', 'path_weewx_root')
                if os.path.isfile(data_ini + r'/weewx.conf'):
                    self.lineEdit_status_weewx_conf.setStyleSheet("color: rgb(0, 170, 0);")
                    self.lineEdit_status_weewx_conf.setText("ok")
                else:
                    fail_count += 1

                if fail_count == 0:  # all files have been found -> system status ok!
                    self.lineEdit_status_SYSTEM.setStyleSheet("color: rgb(0, 170, 0);")
                    self.lineEdit_status_SYSTEM.setText("ok")
                    self.statusOk = True

            except Exception:  # .ini file cannot be found
                self.statusOk = False
        else:  # System not launched on RevPi (checks not necessary)
            self.onRevPi = False
            self.statusOk = True
            self.comboBox_viewer.removeItem(0)  # remove trend-viewer from dropdown
            self.removeTab(3)  # remove tab system status as only important when running App on RevPi
            self.system_address = revpi_remote_address + r'/weewx'
            self.system_php_address = revpi_remote_address + r'/db_manager.php'
            self.lineEdit_status_ini.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_ini.setText("--")
            self.lineEdit_status_server.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_server.setText("--")
            self.lineEdit_status_php.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_php.setText("--")
            self.lineEdit_status_bash_manager.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_bash_manager.setText("--")
            self.lineEdit_status_bash_watchdog.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_bash_watchdog.setText("--")
            self.lineEdit_status_bash_backup.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_bash_backup.setText("--")
            self.lineEdit_status_weewx_folder.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_weewx_folder.setText("--")
            self.lineEdit_status_weewx_conf.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_weewx_conf.setText("--")
            self.lineEdit_status_SYSTEM.setStyleSheet("color: rgb(66, 66, 66);")
            self.lineEdit_status_SYSTEM.setText("--")
        # check if determined links can be reached
        self.WorkerINIT_thread = WorkerINIT()
        self.connect(self.WorkerINIT_thread, QtCore.SIGNAL("signal_emit()"), self.OnINITFinished)
        self.WorkerINIT_thread.start()
        return

    def execute_php_job(self, jobID):
        """
        This function starts the PHPWorker to trigger a certain task dependent on the provided jobID
        :param jobID: int
        :return: --
        """
        '''
        jobID 
        0   =   Get latest reading from primary database (for current conditions overview in GUI)
        1   =   Login user 
        2   =   Change user password
        3   =   Create new user account
        4   =   Delete user account
        5   =   Change password of user account
        6   =   Reset microcontroller
        7   =   Restart system
        8   =   Get admin log
        9   =   Get registered users
        10  =   Data export (primary and secondary database)
        '''
        if self.link_valid and self.php_worker_available:
            # start thread
            self.php_worker_available = False
            self.PHPWorker_thread = PHPWorker(var_process=jobID)
            self.connect(self.PHPWorker_thread, QtCore.SIGNAL("signal_php(QString)"), self.OnPHPWorkerFinished)
            self.PHPWorker_thread.start()
        else:
            pass
        return

    def OnPHPWorkerFinished(self, result_string):
        """
        This is the return function of the PHPWorker-Thread
        :param result_string: string
        :return: --
        """
        try:
            if '666;' in result_string:  # Error occurred
                result_string_list = result_string.replace('666;', '').split('_#_')
                error_text = u"Error occurred while querying Database!\n" \
                             u"Please restart the App and try again. If this issue persists, " \
                             u"please contact the CoSES-Team.\n" \
                             u"Error: "

                for error_msg in result_string_list:
                    if error_msg and not error_msg == '' and not 'None' in error_msg:
                        if 'Dataplicity' in error_msg:  # Dataplicity error message - device might be offline
                            error_text += u'Server cannot be reached. ' \
                                          u'CoSESWeather App is unable to connect to target device. ' \
                                          u'It may be offline.\n'
                        else:
                            error_text += error_msg + '\n'

                self.lineEdit_status_CONNECTION.setText('No Connection')
                self.lineEdit_status_CONNECTION.setStyleSheet("")
                self.ShowMessageBox(u"Error occurred", error_text, 2)
                self.OnUserLogout()  # logout user
                self.link_valid = False
                MAIN_INSTANCE_LOGIN.close()
                MAIN_INSTANCE_PASS.close()
            else:  # Success: valid response
                result_string = result_string.replace('__SUCCESS;', '')

                # php worker returned result for job 1 (get latest sensor dataset for GUI 'current conditions')
                if 'jobID0:' in result_string:
                    if '__NO_ROWS_RETURNED' in result_string:  # no sensor data yet in database
                        pass
                    else:  # update sensor values in GUI
                        del self.json_data_dict[0]
                        # temperature sensor
                        if self.json_data_dict[0]['temp']:
                            self.lineEdit_temp.setText(self.json_data_dict[0]['temp'])
                        else:
                            self.lineEdit_temp.setText('N/A')
                        # windsensor
                        if self.json_data_dict[0]['wind']:
                            self.lineEdit_wind.setText(self.json_data_dict[0]['wind'])
                        else:
                            self.lineEdit_wind.setText('N/A')
                        # spn1 total radiation
                        if self.json_data_dict[0]['spn1_radTot']:
                            self.lineEdit_totalRad.setText(self.json_data_dict[0]['spn1_radTot'])
                        else:
                            self.lineEdit_totalRad.setText('N/A')
                        # spn1 diffuse radiation
                        if self.json_data_dict[0]['spn1_radDiff']:
                            self.lineEdit_diffRad.setText(self.json_data_dict[0]['spn1_radDiff'])
                        else:
                            self.lineEdit_diffRad.setText('N/A')
                        # spn1 sun presence
                        if self.json_data_dict[0]['spn1_sun']:
                            if self.json_data_dict[0]['spn1_sun'] == '1':  # sun shining
                                self.lineEdit_sun.setText('Yes')
                            else:  # currently no sun
                                self.lineEdit_sun.setText('No')
                        else:
                            self.lineEdit_sun.setText('N/A')
                        # cmp3 radiation 1
                        if self.json_data_dict[0]['rad_cmp1']:
                            self.lineEdit_rad1.setText(self.json_data_dict[0]['rad_cmp1'])
                        else:
                            self.lineEdit_rad1.setText('N/A')
                        # cmp3 radiation 2
                        if self.json_data_dict[0]['rad_cmp2']:
                            self.lineEdit_rad2.setText(self.json_data_dict[0]['rad_cmp2'])
                        else:
                            self.lineEdit_rad2.setText('N/A')
                        # cmp3 radiation 3
                        if self.json_data_dict[0]['rad_cmp3']:
                            self.lineEdit_rad3.setText(self.json_data_dict[0]['rad_cmp3'])
                        else:
                            self.lineEdit_rad3.setText('N/A')
                        self.lineEdit_last_update.setText(time.strftime("%d.%m.%Y - %H:%M:%S",
                                                            time.localtime(float(self.json_data_dict[0]['t_unix']))))

                # php worker returned result for user login
                elif 'jobID1:' in result_string:
                    if 'ERROR_AUTH' in result_string:  # incorrect username or password
                        MAIN_INSTANCE_LOGIN.lineEdit_user.clear()
                        MAIN_INSTANCE_LOGIN.lineEdit_pass.clear()
                        MAIN_INSTANCE_LOGIN.lineEdit_user.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                        MAIN_INSTANCE_LOGIN.lineEdit_pass.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                        MAIN_INSTANCE_LOGIN.setEnabled(True)
                        MAIN_INSTANCE_LOGIN.label_wait.hide()
                        self.ShowMessageBox(u"Incorrect Login",
                                            u"Username or password incorrect!", 1)
                    else:  # login successful
                        del self.json_data_dict[0]
                        QtGui.QTabWidget.setTabEnabled(self, 2, True)  # Enable account data tab as user is logged in

                        # load user data
                        if int(self.json_data_dict[0]['admin']) > 0:  # user is admin
                            self.tabWidget_acc.addTab(self.stab_2, "Administration")  # add tab 'administration'
                            self.tabWidget_acc.addTab(self.stab_3, "Registered Users")  # add tab 'registered users'
                            self.lineEdit_acc_status.setText('Admin')
                        else:
                            self.tabWidget_acc.removeTab(1)  # remove tab 'administration' as only available for admins
                            self.tabWidget_acc.removeTab(1)  # remove tab 'registered users' as only available for admins
                            self.lineEdit_acc_status.setText('User')

                        self.p_username = self.json_data_dict[0]['user']
                        self.lineEdit_acc_username.setText(self.p_username)
                        self.lineEdit_acc_email.setText(self.json_data_dict[0]['email'])
                        try:  # timestamp already available
                            self.lineEdit_acc_lastLogin.setText(self.json_data_dict[0]['lastLogin'])
                        except Exception:  # timestamp not available yet as user not logged in yet
                            self.lineEdit_acc_lastLogin.setText('n.a.')
                        for i in range(5):  # iterate over all login buttons and lineEdits
                            button = 'pushButton_login_' + str(i)
                            getattr(self, button).setText('Logout')
                            lineEdit = 'lineEdit_loggedin_user_' + str(i)
                            getattr(self, lineEdit).setText(self.p_username)
                            getattr(self, lineEdit).setStyleSheet("color: rgb(0, 101, 189);")

                        MAIN_INSTANCE_LOGIN.lineEdit_user.setStyleSheet(
                            "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                        MAIN_INSTANCE_LOGIN.lineEdit_pass.setStyleSheet(
                            "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                        self.loggedIn = True
                        self.ShowMessageBox(u"Login successful",
                                            u"Welcome back " + self.p_username + u"!", 0)
                        self.lineEdit_welcome.setText(u"* * *   Welcome to CoSESWeather " + self.p_username + u"   * * *")
                        MAIN_INSTANCE_LOGIN.close()
                        self.setCurrentIndex(2)
                        self.tabWidget_acc.setCurrentIndex(0)

                # php worker returned result for user password change
                elif 'jobID2:' in result_string:  # password change successful
                    self.p_pass = self.p_pass_new
                    MAIN_INSTANCE_PASS.lineEdit_newPass1.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                    MAIN_INSTANCE_PASS.lineEdit_newPass2.setStyleSheet(
                        "background-color: rgb(193, 255, 193); font-weight: bold; border: 1px solid #a6a6a6;")
                    self.ShowMessageBox(u"Success",
                                        u"Password change successful.", 0)
                    MAIN_INSTANCE_PASS.close()

                # php worker returned result for new account
                elif 'jobID3:' in result_string:
                    result_string = str(result_string.replace('jobID3:', '').replace('\n', ''))
                    if 'ERROR_DUBLICATE' in result_string:  # email duplicate
                        self.lineEdit_acmdEmail.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                        self.ShowMessageBox(u"Error",
                                            u"This eMail is already in use!", 1)
                        self.set_AdminCP_enabled()
                        self.OnComboboxAdminCommandChanged_1(False)
                        self.OnComboboxAdminCommandChanged_2(False)
                    else:  # new account successfully created
                        self.ShowMessageBox(u"Success",
                                            u"New user account successfully created.", 0)
                        self.set_AdminCP_enabled()
                        self.OnComboboxAdminCommandChanged_1()
                        self.OnComboboxAdminCommandChanged_2()

                # php worker returned result for delete account
                elif 'jobID4:' in result_string:
                    result_string = str(result_string.replace('jobID4:', '').replace('\n', ''))
                    if 'ERROR_ACC_NOT_FOUND' in result_string:  # account not found
                        self.lineEdit_acmdEmail.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                        self.ShowMessageBox(u"Error",
                                            u"Specified account could not be found in database!", 1)
                        self.set_AdminCP_enabled()
                        self.OnComboboxAdminCommandChanged_1(False)
                        self.OnComboboxAdminCommandChanged_2(False)
                    else:  # account successfully deleted
                        self.ShowMessageBox(u"Success",
                                            u"User account has been successfully deleted from database.", 0)
                        self.set_AdminCP_enabled()
                        self.OnComboboxAdminCommandChanged_1()
                        self.OnComboboxAdminCommandChanged_2()

                # php worker returned result for account password change
                elif 'jobID5:' in result_string:
                    result_string = str(result_string.replace('jobID5:', '').replace('\n', ''))
                    if 'ERROR_ACC_NOT_FOUND' in result_string:  # account not found
                        self.lineEdit_acmdEmail.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                        self.ShowMessageBox(u"Error",
                                            u"Specified account could not be found in database!", 1)
                        self.set_AdminCP_enabled()
                        self.OnComboboxAdminCommandChanged_1(False)
                        self.OnComboboxAdminCommandChanged_2(False)
                    else:  # user account password successfully changed
                        if self.userData_tmpList[1] == self.p_user:  # If admin changed his own password
                            self.p_pass = self.userData_tmpList[0]
                            msg_string = u"Your admin account password has been successfully changed."
                        else:  # admin changed password of other user
                            msg_string = u"Password of specified user has been successfully changed."
                        self.ShowMessageBox(u"Success", msg_string, 0)
                        self.set_AdminCP_enabled()
                        self.OnComboboxAdminCommandChanged_1()
                        self.OnComboboxAdminCommandChanged_2()

                # php worker returned result for microcontroller reset
                elif 'jobID6:' in result_string:
                    self.ShowMessageBox(u"Reset Scheduler",
                                        u"Microcontroller reset has been triggered.\n"
                                        u"The action is scheduled and will be carried out soon.", 0)
                    self.set_AdminCP_enabled()
                    self.OnComboboxAdminCommandChanged_1()
                    self.OnComboboxAdminCommandChanged_2()

                # php worker returned result for system restart
                elif 'jobID7:' in result_string:
                    self.ShowMessageBox(u"Restart Scheduler",
                                        u"System restart has been triggered.\n"
                                        u"The action is scheduled and will be carried out soon.\n"
                                        u"Please note the server will not be available until the system is back up.", 0)
                    self.set_AdminCP_enabled()
                    self.OnComboboxAdminCommandChanged_1()
                    self.OnComboboxAdminCommandChanged_2()

                # php worker returned result for admin log
                elif 'jobID8:' in result_string:
                    del self.json_data_dict[0]
                    self.tableWidget_adminLog.setRowCount(len(self.json_data_dict))
                    for i, log in enumerate(self.json_data_dict):
                        self.tableWidget_adminLog.setItem(i, 0, QtGui.QTableWidgetItem(log['user']))
                        self.tableWidget_adminLog.setItem(i, 1, QtGui.QTableWidgetItem(log['action']))
                        self.tableWidget_adminLog.setItem(i, 2, QtGui.QTableWidgetItem(log['reason']))
                        self.tableWidget_adminLog.setItem(i, 3, QtGui.QTableWidgetItem(log['priority']))
                        self.tableWidget_adminLog.setItem(i, 4, QtGui.QTableWidgetItem(log['time']))

                # php worker returned result for registered users
                elif 'jobID9:' in result_string:
                    del self.json_data_dict[0]
                    _user_count = len(self.json_data_dict)
                    self.tableWidget_regUsers.setRowCount(_user_count)
                    self.lineEdit_usersTotal.setText(str(_user_count))
                    for i, user in enumerate(self.json_data_dict):
                        self.tableWidget_regUsers.setItem(i, 0, QtGui.QTableWidgetItem(user['user']))
                        if user['admin'] == '1':
                            self.tableWidget_regUsers.setItem(i, 1, QtGui.QTableWidgetItem('Yes'))
                        else:
                            self.tableWidget_regUsers.setItem(i, 1, QtGui.QTableWidgetItem('No'))
                        self.tableWidget_regUsers.setItem(i, 2, QtGui.QTableWidgetItem(user['email']))
                        if user['lastLogin']:
                            self.tableWidget_regUsers.setItem(i, 3, QtGui.QTableWidgetItem(user['lastLogin']))
                        else:
                            self.tableWidget_regUsers.setItem(i, 3, QtGui.QTableWidgetItem('n.a.'))

                # php worker returned result for data export
                elif 'jobID10:' in result_string:
                    result_string = str(result_string.replace('jobID10:', ''))

                    if '__db1;' in result_string:  # export job for primary database
                        result_string = str(result_string.replace('__db1;', ''))

                        if '_NO_RESULT;' in result_string:  # no data match for specified export
                            result_string = str(result_string.replace('_NO_RESULT;', ''))
                            date_first_record = datetime.datetime.fromtimestamp(float(result_string)).\
                                strftime('%d.%m.%Y at %H:%M:%S')
                            self.OnExportFinish()
                            self.ShowMessageBox(u"No Export possible",
                                                u"No data could be exported according to the request!\n"
                                                u"Hint: Did you specify a wrong time/date range?\n"
                                                u"The first record in the database has the following date:\n"
                                                u"-> " + unicode(date_first_record) + u".", 1)
                        else:  # export possible
                            del self.json_data_dict[0]
                            # start file-export thread
                            self.ExportWorker_thread = ExportWorkerThread(var_process=0)  # Export from primary database
                            self.connect(self.ExportWorker_thread, QtCore.SIGNAL("signal_export_done(QString)"),
                                         self.OnExportWorkerFinished)
                            self.ExportWorker_thread.start()

                    elif '__db2;' in result_string:  # export job for secondary database
                        result_string = str(result_string.replace('__db2;', ''))
                        if '_NO_RESULT;' in result_string:  # no data match for specified export
                            result_string = str(result_string.replace('_NO_RESULT;', ''))
                            date_first_record = datetime.datetime.fromtimestamp(float(result_string)). \
                                strftime('%d.%m.%Y at %H:%M:%S')
                            self.OnExportFinish()
                            self.ShowMessageBox(u"No Export possible",
                                                u"No data could be exported according to the request!\n"
                                                u"Hint: Did you specify a wrong time/date range?\n"
                                                u"The first record in the database has the following date:\n"
                                                u"-> " + unicode(date_first_record) + u".", 1)
                        else:  # export possible
                            del self.json_data_dict[0]
                            if self.checkBox_exportHiLo.isChecked():  # export hilo data is checked
                                self.json_data_hilo_dict = self.json_data_dict[0]['hilo']
                                self.json_data_dict = self.json_data_dict[0]['data']

                            # start file-export thread
                            self.ExportWorker_thread = ExportWorkerThread(var_process=1)  # Export from secondary database
                            self.connect(self.ExportWorker_thread, QtCore.SIGNAL("signal_export_done(QString)"),
                                         self.OnExportWorkerFinished)
                            self.ExportWorker_thread.start()

        except Exception:  # Error occurred
            self.lineEdit_status_CONNECTION.setText('No Connection')
            self.lineEdit_status_CONNECTION.setStyleSheet("")
            self.ShowMessageBox(u"Error",
                                u"Error occurred on receiving php-worker finish call.\n"
                                u"Please restart the App and try again. If this issue persists, "
                                u"please contact the CoSES-Team.\n"
                                u"Error: " + unicode(traceback.format_exc()), 2)
            self.OnUserLogout()  # logout user
            self.link_valid = False
            MAIN_INSTANCE_LOGIN.close()
            MAIN_INSTANCE_PASS.close()
        self.php_worker_available = True
        return

    def OnExportWorkerFinished(self, result_string):
        """
        This is the return function of the ExportWorker-Thread
        :param result_string: string
        :return: --
        """
        try:
            if '666;' in result_string:  # Error occurred
                result_string_list = result_string.replace('666;', '')
                self.lineEdit_status_CONNECTION.setText('No Connection')
                self.lineEdit_status_CONNECTION.setStyleSheet("")
                self.ShowMessageBox(u"Error",
                                    u"Error occurred while generating export-file!\n"
                                    u"Please restart the App and try again. If this issue persists, "
                                    u"please contact the CoSES-Team.\n"
                                    u"Error: " + unicode(result_string_list), 2)
                self.OnUserLogout()  # logout user
                self.link_valid = False
                MAIN_INSTANCE_LOGIN.close()
                MAIN_INSTANCE_PASS.close()

            else:  # Success: valid response
                rows_selected = result_string.replace('ok;', '')
                self.OnExportFinish()
                self.ShowMessageBox(u"Export Successful",
                                    u"Data export finished successfully (" +
                                    unicode(rows_selected) + u" rows selected).\n"
                                    u"The export file can be found in the root directory of this app.\n"
                                    u"Hint: Click on the 'Open Folder' button to open the directory of the export.", 0)

        except Exception:  # Error occurred
            self.lineEdit_status_CONNECTION.setText('No Connection')
            self.lineEdit_status_CONNECTION.setStyleSheet("")
            self.ShowMessageBox(u"Error",
                                u"Error occurred on receiving export-worker finish call.\n"
                                u"Please restart the App and try again. If this issue persists, "
                                u"please contact the CoSES-Team.\n"
                                u"Error: " + unicode(traceback.format_exc()), 2)
            self.OnUserLogout()  # logout user
            self.link_valid = False
            MAIN_INSTANCE_LOGIN.close()
            MAIN_INSTANCE_PASS.close()
        return

    def OnINITFinished(self):
        """
        This is the return function of the WorkerINIT-Thread
        :param result: string
        :return: --
        """
        if not check_platform():  # if not running on RevPi
            splash.finish(splash)  # hide splash screen (loading screen on startup)
        if self.link_valid:  # if connection to the CoSESWeather-Server could be established
            self.lineEdit_status_CONNECTION.setText('Connected')
            self.lineEdit_status_CONNECTION.setStyleSheet("color: rgb(0, 170, 0);")
            if check_platform():  # if running on RevPi
                self.OnButtonClickedTrendViewer()  # open trend-viewer
                # start reload thread (to update weewx view in trend-viewer)
                self.ReloadTrendWorker_thread = ReloadTrendWorker()
                self.connect(self.ReloadTrendWorker_thread, QtCore.SIGNAL("signal_finish()"),
                             self.ReloadTrendWorkerFinished)
                self.ReloadTrendWorker_thread.start()
        else:  # connection not possible
            self.ShowMessageBox(u"Connection Issues",
                                u"Connection to the server not possible!\n"
                                u"Please try again later or contact the CoSES-Team.", 1)
        self.show()  # show main GUI
        return

    def ReloadTrendWorkerFinished(self):
        """
        Reloads the weather-trend data in the thread-viewer to keep trend data up-to date (called by ReloadTrendWorker)
        :param: --
        :return: --
        """
        MAIN_INSTANCE_TrendViewer.webView_weewx.reload()
        return


class MyApp_LOGIN(QtGui.QDialog, CoSESWeatherApp_LOGIN_ui.Ui_LoginDialog):
    """
    MyApp_LOGIN Class. This class controls the CoSESWeather-App Login widget
    """
    def __init__(self):
        QtGui.QDialog.__init__(self)
        CoSESWeatherApp_LOGIN_ui.Ui_LoginDialog.__init__(self)
        self.setupUi(self)
        self.setStyleSheet("""QToolTip {
                                   background-color: #e9f1f4;
                                   color: black;
                                   border: white solid 1px
                                   }""")
        self.label_wait.hide()
        self.pushButton_login_MAIN.clicked.connect(self.OnButtonClickedLogin)
        self.pushButton_login_close.clicked.connect(self.OnButtonClickedClose)
        self.pushButton_addTUM.clicked.connect(self.OnButtonClickedTUM)
        self.lineEdit_user.textChanged.connect(self.OnLineEditsLoginTextChange)
        self.lineEdit_pass.textChanged.connect(self.OnLineEditsLoginTextChange)

    def closeEvent(self, event):
        """
        Gets called on closeEvent
        :param event
        :return: --
        """
        event.accept()
        return

    def keyPressEvent(self, event):
        """
        Gets called on keyPressEvent
        :param event
        :return: --
        """
        key = event.key()
        if key == QtCore.Qt.Key_Escape:  # When pressing ESC
            self.close()
        elif key == QtCore.Qt.Key_Enter or key == QtCore.Qt.Key_Return:
            self.OnButtonClickedLogin()  # login user
        elif key == QtCore.Qt.Key_F1:  # When pressing F1
            self.OnButtonClickedTUM()
        return

    def OnButtonClickedClose(self):
        """
        Closes the login dialog when 'Close' button is clicked
        :param: --
        :return: --
        """
        self.close()
        return

    def OnButtonClickedTUM(self):
        """
        Adds the TUM-email format (@tum.de) to the lineEdit when 'TUM' button is clicked
        :param: --
        :return: --
        """
        current_text = unicode(self.lineEdit_user.text()).replace(u"@tum.de", u"").strip()
        self.lineEdit_user.setText(current_text + u"@tum.de")
        self.lineEdit_user.setFocus()
        return

    def OnLineEditsLoginTextChange(self):
        """
        Called when text in main login window changes
        :param: --
        :return: --
        """
        self.lineEdit_user.setStyleSheet("font-weight: bold;")
        self.lineEdit_pass.setStyleSheet("font-weight: bold;")
        return

    def reset_LoginWidget(self):
        """
        Resets the stylesheet of the main login window
        :param: --
        :return: --
        """
        self.lineEdit_user.setStyleSheet("font-weight: bold;")
        self.lineEdit_pass.setStyleSheet("font-weight: bold;")
        self.lineEdit_user.clear()
        self.lineEdit_pass.clear()
        self.label_wait.hide()
        self.setEnabled(True)
        return

    def OnButtonClickedLogin(self):
        """
        Attempts to login user when 'Login' button is clicked
        :param: --
        :return: --
        """
        try:
            if str(self.lineEdit_user.text()) and str(self.lineEdit_pass.text()):  # data entered
                self.setEnabled(False)
                self.label_wait.show()
                MAIN_INSTANCE.p_user = str(self.lineEdit_user.text())
                MAIN_INSTANCE.p_pass = str(self.lineEdit_pass.text())
                MAIN_INSTANCE.execute_php_job(1)  # login user
            else:  # no data entered
                if not str(self.lineEdit_user.text()):
                    self.lineEdit_user.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                if not str(self.lineEdit_pass.text()):
                    self.lineEdit_pass.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                MAIN_INSTANCE.ShowMessageBox(u"Error", u"Please enter your user data!", 1)
        except Exception:
            self.lineEdit_user.setStyleSheet(
                "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
            self.lineEdit_pass.setStyleSheet(
                "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
            MAIN_INSTANCE.ShowMessageBox(u"Error", u"Invalid user data!", 1)
        return


class MyApp_PassChanger(QtGui.QDialog, PasswordChange_ui.Ui_PassChangerDialog):
    """
    MyApp_PassChanger Class. This class controls Password Changer Dialog
    """
    def __init__(self):
        QtGui.QDialog.__init__(self)
        PasswordChange_ui.Ui_PassChangerDialog.__init__(self)
        self.setupUi(self)
        self.setStyleSheet("""QToolTip {
                                   background-color: #e9f1f4;
                                   color: black;
                                   border: white solid 1px
                                   }""")

        self.pushButton_cancelPass.clicked.connect(self.OnButtonClickedClose)
        self.pushButton_changePass.clicked.connect(self.OnButtonClickedApply)
        self.lineEdit_newPass1.textChanged.connect(self.OnLineEditsPass1TextChange)
        self.lineEdit_newPass2.textChanged.connect(self.OnLineEditsPass2TextChange)

    def closeEvent(self, event):
        """
        Gets called on closeEvent
        :param event
        :return: --
        """
        event.accept()
        return

    def keyPressEvent(self, event):
        """
        Gets called on keyPressEvent
        :param event
        :return: --
        """
        key = event.key()
        if key == QtCore.Qt.Key_Escape:  # When pressing ESC
            self.close()
        elif key == QtCore.Qt.Key_Enter or key == QtCore.Qt.Key_Return:
            self.OnButtonClickedApply()  # apply password change
        return

    def OnButtonClickedClose(self):
        """
        Closes the password change dialog when 'Close' button is clicked
        :param: --
        :return: --
        """
        self.close()
        return

    def OnLineEditsPass1TextChange(self):
        """
        Called when text in first password lineEdit changes
        :param: --
        :return: --
        """
        self.lineEdit_newPass1.setStyleSheet("font-weight: bold;")
        self.lineEdit_newPass2.setStyleSheet("font-weight: bold;")
        return

    def OnLineEditsPass2TextChange(self):
        """
        Called when text in second password lineEdit changes
        :param: --
        :return: --
        """
        self.lineEdit_newPass1.setStyleSheet("font-weight: bold;")
        self.lineEdit_newPass2.setStyleSheet("font-weight: bold;")
        return

    def OnButtonClickedApply(self):
        """
        Attempts to change the user password when 'Apply' button is clicked
        :param: --
        :return: --
        """
        try:
            if str(self.lineEdit_newPass1.text()) and str(self.lineEdit_newPass2.text()):  # password entered into both lines
                if str(self.lineEdit_newPass1.text()) == str(self.lineEdit_newPass2.text()):  # passwords match
                    if len(str(self.lineEdit_newPass1.text())) > 5:  # if entered password at least 6 chars long
                        MAIN_INSTANCE.p_pass_new = str(self.lineEdit_newPass1.text())
                        MAIN_INSTANCE.execute_php_job(2)  # change password of user
                    else:  # password too short
                        self.lineEdit_newPass1.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                        self.lineEdit_newPass2.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                        MAIN_INSTANCE.ShowMessageBox(u"Error", u"The password must contain at least 6 characters!", 1)
                else:  # no data entered
                    if not str(self.lineEdit_newPass1.text()):
                        self.lineEdit_newPass1.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                    if not str(self.lineEdit_newPass2.text()):
                        self.lineEdit_newPass2.setStyleSheet(
                            "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                    MAIN_INSTANCE.ShowMessageBox(u"Error", u"Passwords do not match!", 1)
            else:  # no data entered
                if not str(self.lineEdit_newPass1.text()):
                    self.lineEdit_newPass1.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                if not str(self.lineEdit_newPass2.text()):
                    self.lineEdit_newPass2.setStyleSheet(
                        "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
                MAIN_INSTANCE.ShowMessageBox(u"Error", u"Please enter the password into both lines!", 1)
        except Exception:
            self.lineEdit_newPass1.setStyleSheet(
                "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
            self.lineEdit_newPass2.setStyleSheet(
                "background-color: rgb(255, 204, 204); font-weight: bold; border: 1px solid #a6a6a6;")
            MAIN_INSTANCE.ShowMessageBox(u"Error", u"Please enter a valid password!", 1)
        return


class MyApp_TrendViewer(QtGui.QWidget, TrendViewer_ui.Ui_TrendViewer):
    """
    TrendViewer Class. This class controls the CoSESWeather-App Trend-Viewer window
    """
    def __init__(self):
        QtGui.QWidget.__init__(self)
        TrendViewer_ui.Ui_TrendViewer.__init__(self)
        self.setupUi(self)
        self.setStyleSheet("""QToolTip {
                                   background-color: #e9f1f4;
                                   color: black;
                                   border: white solid 1px
                                   }""")

    def closeEvent(self, event):
        """
        Gets called on closeEvent
        :param event
        :return: --
        """
        event.accept()
        return

    def keyPressEvent(self, event):
        """
        Gets called on keyPressEvent
        :param event
        :return: --
        """
        key = event.key()
        if key == QtCore.Qt.Key_Escape:  # When pressing ESC
            self.close()
        return


if __name__ == "__main__":
    """
    Main Function - entry point
    """
    app = QtGui.QApplication(sys.argv)
    path_logo_box = resource_path("icon.ico")
    if not check_platform():  # show splash screen only on windows
        # Initiate and show SplashScreen
        splash_png = QtGui.QPixmap(resource_path("splash.png"))
        splash = QtGui.QSplashScreen(splash_png, QtCore.Qt.WindowStaysOnTopHint)
        splash.setMask(splash_png.mask())
        splash.setEnabled(False)
        splash.show()
    # Get Instances and startup GUI
    MAIN_INSTANCE = MyApp()
    MAIN_INSTANCE_LOGIN = MyApp_LOGIN()
    MAIN_INSTANCE_PASS = MyApp_PassChanger()
    MAIN_INSTANCE_TrendViewer = MyApp_TrendViewer()
    sys.exit(app.exec_())
