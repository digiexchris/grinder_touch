
# SG CNC for linuxcnc

#### Surface Grinder CNC
Semi-automatic surface grinder interface similar to hydraulic grinders, but with extra functionality

Traverse, Infeed, and Downfeed axis are arbitrary so it's easy to make it move in a weird way.

A fork of https://github.com/turboss/sg_cnc.git


## Quick install

install linuxcnc 2.9pre using the debian 11

http://www.linuxcnc.org/

install python3-qtpy

qtpyvcp packages can be found here 
https://repository.qtpyvcp.com/apt/pool/main/stable/


https://www.qtpyvcp.com/install/prerequisites.html

install the .deb from this repo

### Dependencies

```
$ sudo apt install python3-pyqt5 python3-pyqt5.qtquick python3-dbus.mainloop.pyqt5 python3-pyqt5.qtopengl python3-pyqt5.qsci python3-pyqt5.qtmultimedia qml-module-qtquick-controls gstreamer1.0-plugins-bad libqt5multimedia5-plugins pyqt5-dev-tools python3-dev python3-setuptools python3-pip git
```

## Customize

install qtpyvcp
https://www.qtpyvcp.com/install/apt_install.html
https://repository.qtpyvcp.com/apt/pool/main/stable/

```
$ cd src/grinder_touch
$ editvcp config.yml
```

## Resources

* [Development](https://github.com/digiexchris/qtpyvcp-grinder-touch)
* [Documentation](https://qtpyvcp.com)


## Dependancies

* [LinuxCNC](https://linuxcnc.org) 2.9.1 or later
* Python 3.9
* PyQt5 or PySide2
* [QtPyVCP](https://qtpyvcp.com/)

grinder_touch is developed and tested using the LinuxCNC Debian 12, It should run on any system that can have PyQt5 installed, but Debian 12 is the only OS
that is officially supported.


## DISCLAIMER

THE AUTHORS OF THIS SOFTWARE ACCEPT ABSOLUTELY NO LIABILITY FOR
ANY HARM OR LOSS RESULTING FROM ITS USE.  IT IS _EXTREMELY_ UNWISE
TO RELY ON SOFTWARE ALONE FOR SAFETY.  Any machinery capable of
harming persons must have provisions for completely removing power
from all motors, etc, before persons enter any danger area.  All
machinery must be designed to comply with local and national safety
codes, and the authors of this software can not, and do not, take
any responsibility for such compliance.

## LICENSE

MIT License

Copyright (c) 2024 Christopher Chatelain

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.