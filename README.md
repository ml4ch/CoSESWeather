## Welcome to CoSESWeather

In this project a Weather-Data Acquisition and Management System has been developed. In this system a Arduino-based microcontorller (client) interfaces different kinds of sensors and forms the core entity of the weather-station developed throughout this project. 
Acquired data is then forwarded to a RaspberryPi-based device (server), where data is processed and permanently stored in MySQL databases.
A GUI-Application (CoSESWeatherApp) has been developed to enable users to conveniently interact with the system (waether-data export, account management, system commands etc.).

![CoSESWeather Logo](https://github.com/ml4ch/CoSESWeather/blob/master/CoSESWeatherApp/logo.png?raw=true)

### Development environment and file-structure

This section gives a brief overview on the required modules and libraries as well as the utilized file-structure of this repository.

```markdown
# Required modules (Python)

- Python 2.7 (Python language and interpreter)
- PyQt4 and QtWebKit (GUI development)
```


```markdown
# Required libaries (Arduino)

```

```markdown
# Required software (server)

- PHP (required by various utilized packages)
- MySQL (database management system)
- phpMyAdmin (web-based user interface to databases)
- Apache2 (HTTP web-server)
- sSMTP and Mailutils (Mail handling tools)
```




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

For more details see [GitHub Flavored Markdown](https://guides.github.com/features/mastering-markdown/).

### Jekyll Themes

Your Pages site will use the layout and styles from the Jekyll theme you have selected in your [repository settings](https://github.com/ml4ch/CoSESWeather/settings). The name of this theme is saved in the Jekyll `_config.yml` configuration file.
