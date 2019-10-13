# Strelok
Strelok was an open source intelligence tool I designed for a university project. It is/was capable of searching Facebook using a first name, last name and location - and find a corresponding LinkedIn profile that matches.

## Dependencies
* Python 3
* GTK+ 3.0
* Pickle
* Itertools
* ConfigParser
* Logging
* Selenium WebDriver
* BeautifulSoup4
* [Chromedriver](https://sites.google.com/a/chromium.org/chromedriver/)

Strelok was developed and designed for Elementary OS, which is a Linux distribution based on Ubuntu. Strelok has not been tested on any other operating system. The above dependecies are what you will need to install to run Strelok. Without these, it will not work.

## Setup
* Place strelok.py, strelok.glade and photo.jpg in a folder of your choosing.
* Place the downloaded Chromedriver in /usr/bin/
* Use pip/pip3 to install the above dependencies

### Note
I haven't actively developed this since leaving University - however, one day I will re-write it. There is "authentication" code currently, but it's easy enough to get around.
Also note that this probably no longer works.
