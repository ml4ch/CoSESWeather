# Welcome to CoSESWeather

In this project a Weather-Data Acquisition and Management System has been developed. In this system a Arduino-based microcontorller (client) interfaces different kinds of sensors and forms the core entity of the weather-station developed throughout this project. 
Acquired data is then forwarded to a RaspberryPi-based device (server), where data is processed and permanently stored in MySQL databases.
A GUI-Application (CoSESWeatherApp) has been developed to enable users to conveniently interact with the system (waether-data export, account management, system commands etc.).

<p align="center">
  <img src="https://github.com/ml4ch/CoSESWeather/blob/master/CoSESWeatherApp/logo.png?raw=true">
</p>


## Development environment and file-structure

This section gives a brief overview on the required third-party modules and libraries as well as the utilized file-structure of this repository.


### Required modules (Python on server-side)

- Python 2.7 (Python language and interpreter): [Link: Python 2.7](https://www.python.org/download/releases/2.7/)
- PyQt4 and QtWebKit (GUI development): [Link: PyQt4: GUI toolkit](https://pypi.org/project/PyQt4/)
- requests (Sending HTTP/1.1 requests): [Link: Requests: HTTP for Humans](https://pypi.org/project/requests/)
- configparser (Configuration-file management): [Link: ConfigParser](https://pypi.org/project/configparser/)
- xlsxwriter (Excel-file creation): [Link: XlsxWriter](https://pypi.org/project/XlsxWriter/)
- PyInstaller (Bundles project): [Link: PyInstaller](https://pypi.org/project/PyInstaller/)


### Required libaries (Arduino, C, C++ on client side)

- Arduino (IDE and standard modules): [Link: Arduino IDE](https://www.arduino.cc/en/Main/Software)
- Controllino (Microcontroller library): [Link: Controllino Lib](https://github.com/CONTROLLINO-PLC/CONTROLLINO_Library)
- MAX31865 (PT100 amplifier library): [Link: MAX31865 Lib](https://github.com/adafruit/Adafruit_MAX31865)
- PT100 (PT100 look-up table): [Link: PT100 LookUp](https://github.com/drhaney/pt100rtd)


```markdown
Syntax highlighted code block

# Header 1
## Header 2
### Header 3

- Bulleted
- List

1. Numbered
2. List

**Bold** and _Italic_ and `Code` text

[Link](url) and ![Image](src)
```
