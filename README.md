# Welcome to CoSESWeather

In this project a Weather-Data Acquisition and Management System has been developed. In this system an Arduino-based microcontorller (client) interfaces different kinds of sensors and forms the core entity of the weather-station developed throughout this project. 
Acquired data is then forwarded to a RaspberryPi-based device (server) where data is processed and permanently stored in MySQL databases.
A GUI-Application (CoSESWeatherApp) has been developed to enable users to conveniently interact with the system (weather-data export, account management, system commands etc.).

<p align="center">
  <img src="https://github.com/ml4ch/CoSESWeather/blob/master/CoSESWeatherApp/logo.png?raw=true">
</p>


## File-structure of repository

The utilized structure of this project-repository is listed below. As the list shows, this project is split into four sub-directories. Important files are also listed and briefly discussed respectively.

- [**Client**](https://github.com/ml4ch/CoSESWeather/tree/master/Client): Source-code for the microcontroller
  - **CoSESClient.ino**: To be flashed onto the microcontroller
  
- [**CoSESWeatherApp**](https://github.com/ml4ch/CoSESWeather/tree/master/CoSESWeatherApp): App-Development (GUI)
  - **CoSESWeatherApp.py**: Main source-file of the app (logic and functionality)
  - **CoSESWeatherApp_ui.ui**: Main source-file of GUI in QtDesigner-format (visual appearance)
  - **CoSESWeatherApp_ui.py**: Main source-file of GUI converted to python-format
  - **convert_ui_to_py_MyApp.bat**: Batch-file to convert QtDesigner-format (.ui-files) to python-code (.py-files)
  - **CoSESWeatherApp.spec**: Specification-file (spec-file) tells PyInstaller how to bundle the app
  - **BuildApp.bat**: Batch-file to start PyInstaller and bundle the app according to the spec-file
  
- [**Server**](https://github.com/ml4ch/CoSESWeather/tree/master/Server): Source-code for the server
  - **CoSESServer.py**: Main server-process (opens socket to acquire raw data forwarded by microcontroller)
  - **CoSESDriver.py**: WeeWx-driver (interface between server-process, databases and WeeWx-framework)
  - **db_manager.php**: Database API-script (functionality and queries)
  - **db_config.php**: Database API-script (authentication data)
  - **CoSESWeather.ini**: Path-file (contains URLs and file-paths utilized in the project)
  - **CoSESServerManager.sh**: Helper-script (monitoring and restarting of system-processes)
  - **MySQLBackUp.sh**: Helper-script (backup creation of MySQL databases)
  - **WatchDogResetter.sh**: Reset of watchdog-timer (on server-side)
  - **localhost.sql**: Initial database-structure (can be imported to create required database-tables)

- [**WeeWx**](https://github.com/ml4ch/CoSESWeather/tree/master/WeeWx): Modified WeeWx-framework installation
  - **weewx-3.9.1(CoSESWeather_mod).tar.gz**: WeeWx weather-station framework (modified installation package)


## Development environment

This section gives a brief overview on the required third-party modules and libraries utilized in this project.


### Required modules (Python on server-side)

- **Python 2.7** (Python language and interpreter): [Python 2.7](https://www.python.org/download/releases/2.7/)
- **PyQt4 and QtWebKit** (GUI development): [PyQt4 GUI toolkit](https://pypi.org/project/PyQt4/)
- **requests** (Sending HTTP/1.1 requests): [HTTP for Humans](https://pypi.org/project/requests/)
- **configparser** (Configuration-file management): [ConfigParser](https://pypi.org/project/configparser/)
- **xlsxwriter** (Excel-file creation): [XlsxWriter](https://pypi.org/project/XlsxWriter/)
- **PyInstaller** (Bundles project): [PyInstaller](https://pypi.org/project/PyInstaller/)


### Required libaries (Arduino, C, C++ on client side)

- **Arduino** (IDE and standard modules): [Arduino IDE](https://www.arduino.cc/en/Main/Software)
- **Controllino** (Microcontroller library): [Controllino Lib](https://github.com/CONTROLLINO-PLC/CONTROLLINO_Library)
- **MAX31865** (PT100 amplifier library): [MAX31865 Lib](https://github.com/adafruit/Adafruit_MAX31865)
- **PT100** (PT100 look-up table): [PT100 LookUp](https://github.com/drhaney/pt100rtd)
 
 
 ## Required installation on server

The commands needed in order to install required packages are listed below. Administrative privileges on the target devicve are required for installation.


 - **Apache2** (HTTP web-server)
```markdown
sudo apt install apache2
```
 - **MySQL** (database management system)
 ```markdown
sudo apt install mariadb-server
```
 - **phpMyAdmin** (web-based tool for database management)
 ```markdown
sudo apt install phpmyadmin
```
 - **PHP** (programming language required by phpMyAdmin and Apache)
 ```markdown
 sudo apt install php libapache2-mod-php 
```
 - Connector between **PHP** and **MySQL**
 ```markdown
 sudo apt install php-mysql
```


## WeeWx weather-station framework

The popular open-source weather-station framework **WeeWx** is used in this project. For detailed information on functionality and customization the extensive documentation on the WeeWx-website is to be considered.


**Website**: [WeeWx Framework](http://weewx.com/)
