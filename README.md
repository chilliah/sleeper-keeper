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
python sleeper_keeper.py Andjita --refresh
```

## Help

usage: sleeper_keeper.py [-h] [--refresh] [--debug] [--offline] [--pos POS]
                         user

Generates a list of eligible keepers for YAFL 2.0.

       For first time use, run with --refresh. Ex: 'python sleeper_keeper.py chilliah --refresh'

       Results are saved to final_keepers.txt.

       You must run with a username from YAFL 2.0.
       To get new data from the Sleeper API, use the optional argument '--refresh'.
       To print all output to files, use the optional argument '--debug'.
       To run in offline mode, use the options argument '--offline'.
       To get keeper values for a specific position, use the optional argument '--pos QB'.
           Valid positions are QB, WR, RB, TE, and DEF. Results are saved to position_keepers.txt.

positional arguments:
  * user        Username of owner in YAFL 2.0

optional arguments:
  * -h, --help Show this help message and exit
  * --refresh  Get new player data from the Sleeper API
  * --debug  If True, print everything to file for debug
  * --offline   Run in Offline Mode. Use saved data from previous run.
  * --pos POS   Get keeper values for specified position
