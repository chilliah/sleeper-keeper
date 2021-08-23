import argparse
import csv
import json
import os
import sys
from pprint import pformat
from sleeper_wrapper import Players
from textwrap import dedent

# This is a helper script for sleeper_keeper.py.
# Take the kept_players.csv generated from the list Andrew sends and convert it to a json file kept_players.json.
# kept_players.csv needs to be in the following format:
#     PlayerName,Manager,Years Kept
#     Lamar Jackson,chilliah,1
#     Austin Ekeler,chilliah,1
# Takes the kept_players.json file and fills it with data from the dump_players.json file, which is the json dump
# of all the players sleeper contains. Saves that file as processed_kept_players.json. This is the json file that
# sleeper_keeper.py will use when determining eligible keepers.


def nice_print(args):
    """ Pretty print args

    Args:
        args: Thing to pretty print
    """
    print('{}'.format(pformat(args)))


def convert_csv_to_json(year):
    """ Converts CSV of kept players to json

    The csv file must be named: kept_players.csv and must be placed in the current year.
        For example the 2019 kept players should be placed in the 2020 folder with name 'kept_players.csv'

    kept_players.csv can be generated in google sheets with File>Downloads>CSV

    kept_players.csv needs to be in the following format:
    PlayerName,Manager,Years Kept
    Lamar Jackson,chilliah,1
    Austin Ekeler,chilliah,1

    kept_players.json will be the following format:
    {
        "Lamar Jackson": {
        "PlayerName": "Lamar Jackson",
        "Manager": "chilliah",
        "Years Kept": "1"
        },
    }

    Args:
        year (int): Year of the league to pull information from sleeper API
    """
    data = {}

    with open('data_files/{}/kept_players/kept_players.csv'.format(year), 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for rows in csvreader:
            key = rows['PlayerName']
            data[key] = rows

    with open('data_files/{}/kept_players/kept_players.json'.format(year), 'w') as jsonfile:
        jsonfile.write(json.dumps(data, indent=4))

    return


def add_sleeper_information(year):
    """ Adds information from the sleeper api to the new kept_players dictionary and generates a new dictionary with
    that information added.

    Loads the kept_players.json and dump_players.json files. Loops through the kept_players dictionary and attempts to
    match the kept_players name with the name from dump_players. From the dump_players dictionary obtain the player_id,
    team, and position. Combine all this into a new dictionary and save that dictionary to
    data_files/{year}/processed_kept_players.json

    processed_kept_players.json structured as:
        {'player_id': {'manager': 'manager name'
                       'player_name': 'name of player'
                       'position': 'position of player'
                       'team': 'team of player'
                       'years_kept': 'Years a player has been kept'}}

    Args:
        year (int): Year of the league to pull information from sleeper API

    Returns:
        player_dict (dict): Dictionary of kept players processed with sleeper information
    """
    with open('data_files/{}/kept_players/kept_players.json'.format(year), 'r') as f:
        kept_dict = json.load(f)

    # If dump_players.json doesn't exist, run the get_players function from sleeper_keeper to generate it.
    # This fixed a dependency bug with sleeper_keeper and
    if os.path.isfile('data_files/{}/dump_players.json'.format(year)):
        with open('data_files/{}/dump_players.json'.format(year), 'r') as f:
            players = json.load(f)
    else:
        print('Getting all players from Sleeper API...')
        players = Players().get_all_players()

        nice_print(players)

    # Empty dictionary to store processed kept players in
    player_dict = dict()

    # Loop through players in the dictionary of kept players to get their player id
    for player_name in kept_dict:
        # Go through all the players in the dump_players.json file. For each player get the id. Then compare
        # the player name in the kept_players dictionary to the player name in the dump_players dictionary.
        # If they match, add a new entry in the player_dict that starts with the player id. Also add additional
        # information (position and team) to determine if the player is correct. If there is not a match, then print
        # a warning and do not replace the player_name with player_id.
        #
        # The intent of this is that if a player name is not matched, go look up the player name and fix the player name
        # in the csv file.
        for player in players:
            player_id = players[player]['player_id']
            player_name_dump = '{} {}'.format(players[player]['first_name'], players[player]['last_name'])
            # nice_print(players[player])
            if player_name.lower() == player_name_dump.lower():
                print('{} has id {}'.format(player_name, player_id))
                player_dict[player_id] = dict()
                player_dict[player_id]['player_name'] = player_name
                player_dict[player_id]['years_kept'] = kept_dict[player_name]['Years Kept']
                player_dict[player_id]['team'] = players[player]['team']
                player_dict[player_id]['position'] = players[player]['position']
                player_dict[player_id]['manager'] = kept_dict[player_name]['Manager']
                break
        else:
            print('*** {} id not found. Add manually ***'.format(player_name))
            player_dict[player_name] = dict()
            player_dict[player_name]['player_name'] = player_name
            player_dict[player_name]['years_kept'] = kept_dict[player_name]['Years Kept']

    # Debug print statements
    # nice_print(player_name)
    # nice_print(kept_dict)
    # nice_print(player_dict)

    # Save as processed_kept_players.json to be used in sleeper_keeper.py
    with open('data_files/{}/kept_players/processed_kept_players.json'.format(year), 'w') as f:
        f.write(json.dumps(player_dict))

    print('Kept players saved to data_files/{}/kept_players/processed_kept_players.json'.format(year))
    return player_dict


def pretty_print_kept(player_dict, year, league_name):
    """ Sorts and saves the kept players to a file.

    Sorts the kept player dictionary alphabetically by manager name, so that all kept players by a manager will be
    listed together. Saves the sorted list of kept players to data_files/{year}/kept_players/processed_kept_players.txt.
    This file is intended to be served by the keepers website at the /kept/<year> endpoint.

    Args:
        player_dict (dict): Dictionary of kept players processed with sleeper information
        year (int): Year of the league to pull information from sleeper API
        league_name (str): Name of the league to pull information from sleeper API
    """
    # List to store keepers that will be sorted.
    keepers_list = []

    nice_print(player_dict)
    for owner_id in player_dict:
        # nice_print(player_dict[owner_id])
        player_name = player_dict[owner_id]['player_name']
        years_kept = player_dict[owner_id]['years_kept']
        manager = player_dict[owner_id]['manager']
        keepers_list.append('{}: {} - Years Kept {}'.format(manager, player_name, years_kept))

    with open('data_files/{}/kept_players/processed_kept_players.txt'.format(year), 'w') as f:
        print('The {} Kept Players for {}:\n\n'.format(league_name, year))
        f.write('The {} Kept Players for {}:\n\n'.format(league_name, year))
        for keeper in sorted(keepers_list):
            print('{}\n'.format(keeper))
            f.write('{}\n'.format(keeper))

    return


if __name__ == "__main__":
    main_help_text = dedent(
        ''' This is a helper script for Sleeper Keeper that will generate the kept_player file from kept_players.csv.
        
        kept_players.csv must be at:
            data_files/{year}/kept_players/kept_players.csv
        
        kept_players.csv must be in the following format:
            PlayerName,Manager,Years Kept
            Lamar Jackson,chilliah,1
            Austin Ekeler,chilliah,1
            
        You must run with a valid year for your league.
        You must run with a valid league name that exactly matches the league name from Sleeper.

        Ex: 'python process_kept_csv.py "YAFL 2.0" 2019' '''
    )
    parser = argparse.ArgumentParser(description=main_help_text, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('name', type=str, help='Name of league. Must exactly match Sleeper')
    parser.add_argument('year', type=int, help='Year to pull information from league')

    args = parser.parse_args()
    league_name = args.name
    year = args.year

    convert_csv_to_json(year)
    player_dict = add_sleeper_information(year)
    pretty_print_kept(player_dict, year, league_name)
    sys.exit(0)
