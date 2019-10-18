# sleeper-keeper
Further proof of my love for the commish

## Description

Uses the Sleeper API to generate a list of keepers for YAFL 2.0.

## Getting Started

### Dependencies

This script requires python 3.x. As with all python projects, I recommend using a virtual environment.

Required Packages: 
* sleeper_api_wrapper==1.0.7

### Installation

To install required packages: ```pip install -r requirements.txt```

### Executing program

```
python sleeper_keeper.py --user Andjita --refresh True
```

## Help

usage: sleeper_keeper.py [-h] --user USER [--refresh REFRESH] [--debug DEBUG]

Generates a list of eligible keepers for YAFL 2.0.

       For first time use, the --refresh flag must be True.
           Ex: 'python sleeper_keeper.py --user chilliah --refresh True

       Results are saved to final_keepers.txt.

       You must specify a user with '--user'
       To get new data from the Sleeper API, use the optional argument '--refresh True'
       To print all output to files, use the optional argument '--debug True'

optional arguments:
  * -h, --help&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Show this help message and exit
  * --user USER&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Username of owner in YAFL 2.0
  * --refresh REFRESH&nbsp;&nbsp;If True, get new player data from the Sleeper API
  * --debug DEBUG&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;If True, print everything to file for debug
