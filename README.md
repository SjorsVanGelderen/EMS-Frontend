# EMS Front-end
GTK3 front-end for [EMS flasher](https://github.com/mikeryan/ems-flasher) 

[![Packagist](https://img.shields.io/badge/status-alpha-orange.svg)]()
[![Packagist](https://img.shields.io/badge/license-GPLv3-blue.svg)]()  

![](screenshot.png) 

Written in Python 3.  
Uses PyGObject bindings.  

***

##Notes  
- This utility hasn't been tested extensively
- The utility might appear to lock up when flashing
- Sometimes an error actually freezes the utility
- This utility doesn't wait for the cartridge to become available properly
  - Unfortunately, this causes many errors

***

##Todo  
- Implement search functionality
- Test flashing large ROMs
- Bundle with EMS flasher
- Build deb / rpm / etc packages
- Log errors(possibly with verbose messages from EMS flasher)
