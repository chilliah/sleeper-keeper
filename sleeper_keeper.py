import configparser
import math
import sys
import time
from google.cloud import storage
from itertools import chain
from pathlib import Path
from pprint import pformat

import numpy as np
import pandas as pd
import requests


# TODO the future begins now
# I want to convert this program to use Pandas and a PD dataframe (DF).
# This is the best season to start, cause I need to integrate auction support. Might as well start over.
# Goals for this rewrite:
#   Support a config file, so that multi-league support is built into the program
#   Draft board to show drafted picks (Graphical representation of traded draft picks would be so dope)
#   Maths on the DF
#   Discord integration - Would love to use webhooks for something.
#       Maybe making trade announcements?
#       Taunting winners/losers
#       Playoff stuff?
#   Rich Stats
#       How each team is doing at a certain position?
#       What about against an opponent? For the season? For the life time of a league?
#   History
#       Work with Andrew to import league history?
#   Downloads
#       Keep CSV support, cause MW is a little bitch
# Beginning of the future
# Since everything is saved as a dataframe now (keeper_df) I can add a filter category to the site to make it only show
# stuff like just someones keepers or all the RBs/Wrs/QBs that be be kept. Might be worth it in the future

#   Config File
#       League Name
#       this might not be needed

# Patching in app engine support on 10/15/22
# Just going to test doing this with a download and upload from cloud storage to local directory
# Start with doing a config option to keep support for local storage


# TODO Look into 'r' (I think restritced) strings. I vaguely remember these from Armada
class League:
    def __init__(self, name, current_year, current_id, eligible_years, first_year, draft_type, eligible_ids):
        """ Class that represents a League

        Args:
            name (str) = Name of the league
            current_year (int) = Year of league to get keeper results
            current_id (str) = Current League ID
            eligible_years (list) = Years the league as been in sleeper (int)
            first_year (int) = First year of league, for kept players
            draft_type (str) = String representing the draft type for the league
            eligible_ids (list) = List of all the League IDs in order of eligible_years
        """
        self.name = name
        self.current_year = current_year
        self.current_id = current_id
        self.eligible_years = eligible_years
        self.first_year = first_year
        self.draft_type = draft_type
        self.eligible_ids = eligible_ids

        # Generate a dictionary of {year:league_id} Should make life easier later on.
        year_to_id = dict(zip(eligible_years, eligible_ids))
        self.year_to_id = year_to_id


class Debug:
    def __init__(self, refresh, debug, player_refresh, save_run, filtered_results, cloud_storage):
        """ Class that represents the debug variables

        Args:
            refresh (bool): If True, Get fresh data from API and update saved files.
            debug (bool): If True, print debug information in terminal.
            player_refresh (bool): If True, get players from Sleeper API.
            save_run (bool): If True, open keeper_df from a save pickle and do not process anything.
            filtered_results (bool): If True, filter the dataframe for easier read.
            cloud_storage (bool): If True, download and upload to the cloud save for cloud run
        """
        self.refresh = refresh
        self.debug = debug
        self.player_refresh = player_refresh
        self.save_run = save_run
        self.filtered_results = filtered_results
        self.cloud_storage = cloud_storage


def nice_print(args):
    """ Pretty print args. Real talk, best function I've ever written.

    Args:
        args: Thing to pretty print
    """
    print(f'{pformat(args)}')


def open_pickle_catch(file_location, cloud_storage):
    """ Try to open the file and file_location, if it does not open assert

    Args:
        file_location (str): Directory of the pickle file to read
        cloud_storage (bool): Debug config setting. If true, download the file from cloud_storage first.

    Return:
        file_df (DataFrame): DataFrame read from the pickle file

    """
    try:

        # Add catch for cloud storage here:
        if cloud_storage:

            # App Engine file system is read only. Have do put this stuff in the /tmp folder.
            source_blob = file_location
            tmp = '/tmp/'
            file_location = tmp + file_location

            download_cloud(source_blob, file_location)

        with open(file_location):
            file_df = pd.read_pickle(file_location)
    except Exception as e:
        print(e)
        assert_string = f'Unable to open {file_location}. \n Set refresh to True in config.ini'
        assert False, assert_string

    return file_df


def save_pickle_catch(file_location, df, cloud_storage):
    """ Try to open the file and file_location, if it does not open assert

    Args:
        file_location (str): Directory of the pickle file to read
        df (DataFrame): DataFrame to pickle
        cloud_storage (bool): Debug config setting. If true, download the file from cloud_storage first.

    Return:
        file_df (DataFrame): DataFrame read from the pickle file

    """
    # If cloud_storage then use the /tmp directory
    if cloud_storage:
        source_blob = file_location
        tmp = '/tmp/'
        file_location = tmp + file_location
    # If data_files doesn't exist, create the directory
    # Since the function is called with the full pickle, strip out the file_name and only populate the directories.
    file = file_location.rsplit('/', 1)[-1]
    folder_string = file_location.rstrip(file)

    path = Path(folder_string)
    path.mkdir(parents=True, exist_ok=True)

    df.to_pickle(file_location)

    if cloud_storage:
        upload_cloud(source_blob, file_location)

    return


def open_html_catch(file_location, cloud_storage):
    """ Try to open the file and file_location, if it does not open assert

    Args:
        file_location (str): Directory of the html file to read
        cloud_storage (bool): Debug config setting. If true, download the file from cloud_storage first.

    Return:
        file_df (DataFrame): DataFrame read from the pickle file

    """
    try:

        # Add catch for cloud storage here:
        if cloud_storage:

            # App Engine file system is read only. Have do put this stuff in the /tmp folder.
            source_blob = file_location
            tmp = '/tmp/'
            file_location = tmp + file_location

            download_cloud(source_blob, file_location)

        print(f'Location to download html_file = {file_location}. Cloud S = {cloud_storage} type cs = {type(cloud_storage)}')

        with open(file_location):
            print(f'Opened filed from here {file_location}')
            file_html = open(file_location, 'r')
    except Exception as e:
        print(e)
        assert_string = f'Unable to open {file_location}. \n Set refresh to True in config.ini'
        assert False, assert_string

    return file_html


def save_html_catch(file_location, html, cloud_storage):
    """ Try to open the file and file_location, if it does not open assert

    Args:
        file_location (str): Directory of the pickle file to read
        html (HTML table): HTML File to be saved
        cloud_storage (bool): Debug config setting. If true, download the file from cloud_storage first

    Return:
        file_df (DataFrame): DataFrame read from the pickle file

    """
    # If cloud_storage then use the /tmp directory
    if cloud_storage:
        source_blob = file_location
        tmp = '/tmp/'
        file_location = tmp + file_location
    # If data_files doesn't exist, create the directory
    # Since the function is called with the full pickle, strip out the file_name and only populate the directories.
    file = file_location.rsplit('/', 1)[-1]
    folder_string = file_location.rstrip(file)

    path = Path(folder_string)
    path.mkdir(parents=True, exist_ok=True)

    with open(file_location, 'w') as f:
        f.write(html)

    if cloud_storage:
        upload_cloud(source_blob, file_location)

    return


def get_players(players_debug):
    """ Get all the players from Sleeper save in DataFrame

    Args:
        players_debug (Debug): Class representing the Debug information from the config file

    Returns:
        players_df (DataFrame): DateFrame of all the players
    """
    # Since the players API endpoint is so large, we don't need to call it every run.
    # Store a separate refresh variable
    refresh = players_debug.player_refresh
    cloud_storage = players_debug.cloud_storage
    # Save file location
    players_pkl_location = 'data_files/common/players_df.pkl'

    if refresh:
        print('Getting all players from Sleeper API...')
        players = get_sleeper_api('players', '', '')

        players_df = pd.DataFrame.from_dict(players)

        # Transpose the players_df raw API data, so that the index will be the player id
        # This is needed cause the columns are the player_ids and transpose will flip the dataframe
        players_t_df = players_df.T

        # Pickle and save the dataframe for offline use
        save_pickle_catch(players_pkl_location, players_t_df, cloud_storage)

    players_df = open_pickle_catch(players_pkl_location, cloud_storage)

    return players_df


# TODO This is the old RUN keeper webpage stuff remove when done
# This can be used to do the first year RUN stuff cause I need to keep the old sheet for the 2020 year stuff
# I can use this function to do just that. Move the location of this stuff to the first_year
def keeper_csv_to_table():
    """ Open the RUN kept player csv and convert it to html table. Generate webpage.

    Run this to convert the First Year RUN Kept Player CSV to a HTML table that will be served by the
    runkeeperwebpage.py site.
    """
    # Import RUN kept player data as Panda Dataframe
    kept_data = pd.read_csv('data_files/run_files/run_first_kept_player.csv')

    # Use a list to format the dataframe into how we want the table to be saved and generated.
    format_keeper_list = ['Manager', 'Player', 'Position', 'Years Kept', 'Cost 2020', 'Keeper Cost 2021']
    print(kept_data[format_keeper_list])

    # Save to pickle, so that we have the data backed up.
    kept_data[format_keeper_list].to_pickle('data_files/run_files/kept_pickle.pkl')
    read_data = pd.read_pickle('data_files/run_files/kept_pickle.pkl')

    # Generate a html table from the dataframe.
    # classes is used to allow the table to have unique css styling.
    # The css style sheet will reference .mystyle
    kept_html = read_data.to_html(index=False, classes='mystyle')
    with open('data_files/run_files/kept_table.html', 'w') as f:
        f.write(kept_html)

    print('\r\ndata_files/run_files/kept_table.html generated successfully\r\n')


def get_drafted_players(draft_debug, draft_league):
    """ Get the drafted players from sleeperAPI save to draft_df DataFrame

    Args:
        draft_debug (Debug): Class representing the Debug information from the config file
        draft_league (League): Class representing the League information from the config file.

    Returns:
        draft_df (DataFrame): DataFrame of drafted players
    """
    refresh = draft_debug.refresh
    cloud_storage = draft_debug.cloud_storage
    year = draft_league.current_year
    league_id = draft_league.current_id
    # Save file locations
    draft_pkl_location = f'data_files/{year}/{league_id}/draft_df.pkl'
    draft_base_pkl_location = f'data_files/{year}/{league_id}/draft_base_df.pkl'
    if refresh:
        print('Getting all draft picks from league...')
        # Get all the drafts for the league
        all_drafts = get_sleeper_api('league', str(league_id), 'drafts')

        # Sleeper will only have 1 draft, so we can access the first result from the list
        draft_id = all_drafts[0]['draft_id']

        # Create base draft object with draft_id
        draft_base = get_sleeper_api('draft', draft_id, '')

        # Create a base draft dataframe object. This will likely later be used for making the draft board
        # TODO This is being saved, but not used. Figure out if I need it and probably return it to main
        draft_base_df = pd.json_normalize(draft_base, max_level=0)
        save_pickle_catch(draft_base_pkl_location, draft_base_df, cloud_storage)
        nice_print(draft_base_df)

        # Get the picks for the draft at draft_id
        draft = get_sleeper_api('draft', draft_id, 'picks')
        # TODO draft_slot is the column that the player was drafted in. I suppose this can be used to build a draft
        # board later in the future.

        # These are the columns to keep in the draft dataframe
        draft_df = pd.DataFrame(draft)

        # Set player_id to the index, so loc can be called with player_id
        draft_df.set_index('player_id', inplace=True)

        # Pickle and save the dataframe for offline use
        save_pickle_catch(draft_pkl_location, draft_df, cloud_storage)

    draft_df = open_pickle_catch(draft_pkl_location, cloud_storage)
    nice_print(draft_df)

    return draft_df


def load_config(config_file):
    """ Open config file and get variables we need

    The config file, config.ini, should be in the root directory of the project with old_sleeper_keeper.py (main).
    Format for config file is:
         [league]
            name = YAFL 2.0
            current_year = 2021
            id = 726613533856428032
            eligible_years = 2019, 2020, 2021
            eligible_ids = 460518016728166400, 515555767692488704, 726613533856428032
            first_year = 2019
            draft_type = auction

        [debug]
            refresh = False
            debug = False
            player_refresh = False
            save_run = False (currently not used)
            filtered_results = True (currently not used)
            cloud_storage = True

    Args:
        config_file (str): Location of the config file to load from.

    Returns:
        league_1 (Debug): Class representing the Debug information from the config file
        draft_1 (League): Class representing the League information from the config file.
    """
    # TODO Clean up this function
    # TODO add config file catch? Python interpurt makes it so easy to debug these issues
    config = configparser.ConfigParser()
    config.read(config_file)

    # Get the info we want like year and league name
    league_current_year = config.getint('league', 'current_year')
    league_first_year = config.getint('league', 'first_year')
    league_eligible_years_string = config.get('league', 'eligible_years')
    league_eligible_years_string_list = league_eligible_years_string.split(',')
    # List comprehension to convert the string to int.
    league_eligible_years = [int(i) for i in league_eligible_years_string_list]
    league_name = config.get('league', 'name')
    league_id_config = config.get('league', 'id')
    league_draft_type = config.get('league', 'draft_type')
    league_eligible_ids_string_list = config.get('league', 'eligible_ids')
    league_eligible_ids = league_eligible_ids_string_list.split(',')

    # Declare a class with all the league info from the config file
    league_1 = League(league_name, league_current_year, league_id_config, league_eligible_years, league_first_year,
                      league_draft_type, league_eligible_ids)

    # Get debug variables. These will be supplied by keeper webpage. The values in the config are for shell run
    debug_refresh = config.getboolean('debug', 'refresh')
    debug_debug = config.getboolean('debug', 'debug')
    debug_player_refresh = config.getboolean('debug', 'player_refresh')
    debug_save_run = config.getboolean('debug', 'save_run')
    debug_filtered_results = config.getboolean('debug', 'filtered_results')
    debug_cloud_storage = config.getboolean('debug', 'cloud_storage')
    print(debug_debug)

    # Declare a class with all the debug info from the config file.
    debug_1 = Debug(debug_refresh, debug_debug, debug_player_refresh, debug_save_run, debug_filtered_results,
                    debug_cloud_storage)

    return league_1, debug_1


def get_rosters(roster_debug, roster_league):
    """ Get the current roster for each team.

    Gets the roster for every team from the league object. Maps the user_id to the display_name. Saves it to disk.

    Args:
        roster_debug (Debug): Class representing the Debug information from the config file
        roster_league (League): Class representing the League information from the config file.

    Returns:
        rosters_df (DataFrame): DataFrame of the roster Sleeper API call
    """
    refresh = roster_debug.refresh
    cloud_storage = roster_debug.cloud_storage
    year = roster_league.current_year
    league_id = roster_league.current_id
    # Save file location
    rosters_pkl_location = f'data_files/{year}/{league_id}/rosters_df.pkl'

    if refresh:
        # Get the users from the Sleeper API to get the display_name for the rosters_df
        print('Getting all users in league...')
        users = get_sleeper_api('league', league_id, 'users')

        # Create dataframe from users API call with display_name and user_id as columns
        # Sort the DF by the user_id, will use this to drop in the display_name to the rosters_df
        users_df = pd.DataFrame(users)
        users_df.sort_values(by=['user_id'], inplace=True)

        # Get the rosters from the Sleeper API
        print('Getting rosters from league...')
        rosters = get_sleeper_api('league', str(league_id), 'rosters')

        # Create rosters dataframe from rosters API call
        rosters_df = pd.DataFrame(rosters)

        # Sort by the owner_id this enables just dropping in the users_df user_id column correctly
        rosters_df.sort_values(by=['owner_id'], inplace=True)

        # Check if the users_id columns are sorted, then insert the display_name column
        # Compares if the columns are sorted
        if users_df['user_id'].reset_index(drop=True).equals(rosters_df['owner_id'].reset_index(drop=True)):
            # Declare a list that is to be converted into a column
            display_name = users_df['display_name'].tolist()
            rosters_df['display_name'] = display_name
        else:
            print(f'The roster_df and user_df have different user_id columns. Manual inspection required')
            exit()

        # Change the index to owner_id to allow for rosters_df.at[owner_id, 'display_name']
        rosters_df.set_index('owner_id', inplace=True, drop=False)

        # Pickle and save the dataframe for offline use
        save_pickle_catch(rosters_pkl_location, rosters_df, cloud_storage)

    rosters_df = open_pickle_catch(rosters_pkl_location, cloud_storage)

    nice_print(rosters_df)

    return rosters_df


def get_transactions(trans_debug, trans_league, trade_deadline):
    """ Get all the transactions and the trade deadline from the Sleeper API

    Get all the transactions from the Sleeper API after the trade deadline till the end of the season. Filter the
    completed transactions into a Dataframe, which will be used to determine the dropped players after the trade
    deadline.

    transactions_dataframe:
        transaction_id      creator              status     drops         draft_picks  consent_ids  status_updated
        769105866526982144  468535859126202368   complete   {'4972': 11}  []           [11]           1637741217895

    Args:
        trans_debug (Debug): Class representing the Debug information from the config file
        trans_league (League): Class representing the League information from the config file.
        trade_deadline (int): Trade deadline for YAFL

    Returns:
        final_transactions_df (Dataframe): Dataframe of completed transactions after trade deadline
    """
    refresh = trans_debug.refresh
    cloud_storage = trans_debug.cloud_storage
    year = trans_league.current_year
    league_id = trans_league.current_id
    # Save file location
    transactions_pkl_location = f'data_files/{year}/{league_id}/transactions_df.pkl'

    if refresh:
        print(f'Getting all transactions from Sleeper API after week {trade_deadline}...')
        week = 0

        # Initialize empty list to hold list of all transactions
        transactions_list = []

        # Get all the transactions since after the trade deadline and store them in list
        while week <= 18:

            print('Getting transactions for week {}'.format(week))
            transactions_week = get_sleeper_api('transactions', str(league_id), week)

            # Add the week to each transaction. This will be used to filter for trades and drops by week.
            # The Sleeper API logs each transactions in epoch time, but then logs the trade deadline as the week.
            for transaction in transactions_week:
                transaction["week"] = week

            transactions_list.append(transactions_week)

            week = week + 1

            time.sleep(0.1)

        # Just created a list of a list of dictionary. Need to flatten the list to convert it into a dataframe
        flat_transactions = list(chain.from_iterable(transactions_list))
        transactions_list_df = pd.DataFrame(flat_transactions)
        transactions_list_df.set_index('transaction_id', inplace=True)

        # When getting the transactions for a week, sleeper will also list the failed transactions.
        # Filter out only the completed transactions.
        # Note for future Jeff: This is how you filter a dataframe. This will filter the status column for any string
        # with 'complete'
        complete_filter = transactions_list_df['status'].isin(['complete'])

        # Get dataframe of only the completed transactions for each week and append to it
        completed_transactions_df = transactions_list_df[complete_filter]

        # Fields to keep from transactions API call.
        # TODO status_updated is a unix timestamp. Should I convert to datetime before I pickle?
        transactions_data = ['creator', 'status', 'adds', 'drops', 'draft_picks', 'status_updated', 'type', 'week']

        final_transactions_df = pd.DataFrame(completed_transactions_df, columns=transactions_data)

        nice_print(final_transactions_df)

        # Pickle and save the dataframe for offline use
        save_pickle_catch(transactions_pkl_location, final_transactions_df, cloud_storage)

    final_transactions_df = open_pickle_catch(transactions_pkl_location, cloud_storage)
    nice_print(final_transactions_df)

    return final_transactions_df


def get_traded_picks(picks_debug, picks_league, trade_trans_df, trade_roster_df):
    """ Get the traded draft picks from the transactions_df

    Args:
        picks_debug (Debug): Class representing the Debug information from the config file
        picks_league (League): Class representing the League information from the config file.
        trade_trans_df (DataFrame): Transactions DataFrame of every week
        trade_roster_df (DataFrame): Roster DataFrame used to populate the traded_picks_df

    Return:
        traded_picks_df (DataFrame): DataFrame of traded draft picks with info from sleeper API
    """
    refresh = picks_debug.refresh
    cloud_storage = picks_debug.cloud_storage
    year = picks_league.current_year
    league_id = picks_league.current_id
    # Save file location
    traded_picks_file_location = f'data_files/{year}/{league_id}/traded_picks_df.pkl'

    if refresh:
        # Draft picks are stored as a list of list.
        # Use a list comprehension to turn it into a flat list then put it in a DF.
        # Save it for future stuff like picturing the draft pick changes
        draft_picks_lol_df = trade_trans_df['draft_picks']
        draft_picks_lol = draft_picks_lol_df.to_list()
        draft_picks_list = [draft_pick for draft_picks_list in draft_picks_lol for draft_pick in draft_picks_list]
        draft_picks_df = pd.DataFrame(draft_picks_list)

        nice_print(draft_picks_df)

        # Add a catch for no traded draft picks.
        if not draft_picks_df.empty:
            # Move the process_traded_draft_picks to the refresh in order to limit writes to disk.
            process_traded_draft_picks(draft_picks_df, trade_roster_df)

        nice_print(f'Traded Draft Picks: {draft_picks_df}')

        # Save traded picks to pickle
        save_pickle_catch(traded_picks_file_location, draft_picks_df, cloud_storage)

    traded_picks_df = open_pickle_catch(traded_picks_file_location, cloud_storage)
    nice_print(traded_picks_df)

    return traded_picks_df


def process_transactions(trans_debug, trans_league, transactions_df, trade_deadline):
    """ Process the transactions_df to get the traded players, traded draft picks, and dropped players

    Create a list of the traded players for keeper reset tracking
    Create a list of the dropped players for keeper tracking
    Create a DataFrame of the trade draft picks for future processing.

    Args:
        trans_debug (Debug): Class representing the Debug information from the config file
        trans_league (League): Class representing the League information from the config file.
        transactions_df (DataFrame): Transactions from the Sleeper API in a DataFrame
        trade_deadline (int): Trade deadline for league

    Returns:
        traded_players (list): List of player_ids that have been traded
        dropped_players (list): List of player_ids that have been dropped after the trade deadline
        added_players (list): List of player_ids that have been added after the trade deadline
        draft_picks_df (DataFrame): DataFrame of the draft picks from the transactions DataFrame
    """
    # Get the trades from the transactions_df and put them in a added players list
    # This list will be used to mark a players keeper value as reset in YAFL.
    # Filter the transaction list for the trades and remove the None to avoid key errors
    # Make it a list, and flatten the list to just get the keys, which is the added players_ids
    trade_filter = transactions_df['type'].isin(['trade'])
    trades_df = pd.DataFrame(transactions_df[trade_filter])
    trade_clean_df = trades_df['adds'].dropna()
    print(trade_clean_df.values)  # DEBUG - Get the values of the Pandas series
    trade_list = trade_clean_df.to_list()
    traded_players = set().union(*(d.keys() for d in trade_list))

    #TODO Catch here for YAFL Business?
    # This is a list of players and IDs involved in MW and I's illegal trade. Going to exclude them for this year
    # Remove if MW ever makes a trade with these guys
    league_id = trans_league.current_id
    year = trans_league.current_year
    if league_id == "861678908091789312" and year == 2022:
        # Darren Waller = 2505
        traded_players.remove('2505')
        # Austin Ekeler = 4663
        traded_players.remove('4663')
        # Lamar Jackson = 4881
        traded_players.remove('4881')
        # Zach Ertz = 1339
        traded_players.remove('1339')
        # Rashod Bateman = 7571
        traded_players.remove('7571')
        # Rhamondre Stevenson = 7611
        traded_players.remove('7611')

    # Get the dropped players from the transactions_df after trade_deadline
    # Use a lambda function to get all the transactions past the trade_deadline and put them in a dropped players DF
    # Drop the Nan transactions to avoid key errors, then flatten the list and get the dropped players
    drops_filter = transactions_df['week'].apply(lambda x: x > trade_deadline)
    drops_df = transactions_df[drops_filter]
    drops_clean_df = drops_df['drops'].dropna()
    dropped_list = drops_clean_df.to_list()
    dropped_players = set().union(*(d.keys() for d in dropped_list))

    # Get the added players from the transactions_df after trade_deadline
    # Use a lambda function to get all the transactions past the trade_deadline and put them in a added players DF
    # Add the Nan transactions to avoid key errors, then flatten the list and get the added players
    adds_filter = transactions_df['week'].apply(lambda x: x > trade_deadline)
    adds_df = transactions_df[adds_filter]
    adds_clean_df = adds_df['adds'].dropna()
    added_list = adds_clean_df.to_list()
    added_players = set().union(*(d.keys() for d in added_list))

    print(f'dropped_players: {dropped_players}')
    print(f'added_players: {added_players}')
    print(f'traded_players: {traded_players}')

    return traded_players, dropped_players, added_players


def process_traded_draft_picks(draft_picks_df, roster_df):
    """ Processed the draft picks Dataframe and owner_name and owner_id

    Traded Draft picks from the sleeper API are all referenced from roster_id, which is an int tied to each roster
    Process the traded draft picks and add the owner_name and owner_id for all fields of the traded pick.

    Add the following fields to the draft_picks_df Dataframe:
        'new_owner_id' = new_owner_id_list - Owner_id of the new owner of the draft pick
        'new_owner_display' = new_owner_display_list - Owner name of the new owner of the draft pick
        'previous_owner_id' = previous_owner_id_list - Owner_id of the previous owner of the draft pick
        'previous_owner_display' = previous_owner_display_list - Owner name of previous owner the draft pick
        'original_owner_id' = original_owner_id_list - Owner_id of the original owner of the draft pick
        'original_owner_display' = Owner name of original owner the draft pick

    Args:
        draft_picks_df (DataFrame): Dataframe of the traded draft picks from the sleeper API
        roster_df (DataFrame): Dataframe of the rosters that has been processed with display_names

    Return:
        draft_picks_df (DataFrame): Dataframe of the traded draft picks processed with roster_df info
    """
    # roster_id = Original Owner
    # previous_owner_id = previous owner
    # owner_id = New owner
    new_owner_list = draft_picks_df['owner_id'].tolist()
    previous_owner_list = draft_picks_df['previous_owner_id'].tolist()
    original_owner_list = draft_picks_df['roster_id'].tolist()

    roster_id_df = roster_df.set_index('roster_id', drop=False)

    new_owner_id_list = []
    new_owner_display_list = []
    for owner in new_owner_list:
        # print(roster_id_df.at[owner, 'owner_id'])  # Debug statement
        # print(roster_id_df.at[owner, 'display_name'])  # Debug statement
        new_owner_id_list.append(roster_id_df.at[owner, 'owner_id'])
        new_owner_display_list.append(roster_id_df.at[owner, 'display_name'])

    previous_owner_id_list = []
    previous_owner_display_list = []
    for owner in previous_owner_list:
        # print(roster_id_df.at[owner, 'owner_id'])  # Debug statement
        # print(roster_id_df.at[owner, 'display_name'])  # Debug statement
        previous_owner_id_list.append(roster_id_df.at[owner, 'owner_id'])
        previous_owner_display_list.append(roster_id_df.at[owner, 'display_name'])

    original_owner_id_list = []
    original_owner_display_list = []
    for owner in original_owner_list:
        # print(roster_id_df.at[owner, 'owner_id'])  # Debug statement
        # print(roster_id_df.at[owner, 'display_name'])  # Debug statement
        original_owner_id_list.append(roster_id_df.at[owner, 'owner_id'])
        original_owner_display_list.append(roster_id_df.at[owner, 'display_name'])

    draft_picks_df['new_owner_id'] = new_owner_id_list
    draft_picks_df['new_owner_display'] = new_owner_display_list
    draft_picks_df['previous_owner_id'] = previous_owner_id_list
    draft_picks_df['previous_owner_display'] = previous_owner_display_list
    draft_picks_df['original_owner_id'] = original_owner_id_list
    draft_picks_df['original_owner_display'] = original_owner_display_list

    # Sort the draft_picks_df before saving to make processing draft picks easier down the line
    # Ignore_index resets the index, which makes everything easier down the line
    draft_picks_df.sort_values(by=['new_owner_display', 'season', 'round'], inplace=True, ignore_index=True)

    # Add strings to describe each dataframe row
    def pick_string(new_owner_string, previous_owner_string, original_owner_string, round_string, season_string,
                    pick_type):
        if pick_type == 'gained':
            traded_pick_string = f'{new_owner_string} has gained a {season_string} {round_string} round draft pick ' \
                    f'from {previous_owner_string}. The original owner of this draft pick was {original_owner_string}'
        elif pick_type == 'lost':
            traded_pick_string = f'{previous_owner_string} has lost a {season_string} {round_string} round draft pick' \
                    f'to {new_owner_string}. The original owner of this draft pick was {original_owner_string}'
        else:
            traded_pick_string = f'CHECK PROGRAM. TRADE STRING DID NOT PROCESS CORRECTLY'
            print(traded_pick_string)
            exit()

        return traded_pick_string

    # Gained Draft Pick Lambda function
    draft_picks_df['gained_draft_picks'] = draft_picks_df.apply(
        lambda x: pick_string(x['new_owner_display'], x['previous_owner_display'], x['original_owner_display'],
                              x['round'], x['season'], 'gained'), axis=1)

    # Lost draft pick lambda comment
    draft_picks_df['lost_draft_picks'] = draft_picks_df.apply(
        lambda x: pick_string(x['new_owner_display'], x['previous_owner_display'], x['original_owner_display'],
                              x['round'], x['season'], 'lost'), axis=1)

    nice_print(draft_picks_df)

    return draft_picks_df


def get_sleeper_api(base, base_id, endpoint):
    """ Function that calls the league API and returns the results json blob

    League URL for sleeper API: "https://api.sleeper.app/v1/league/{league_id}/{endpoint}"
    Draft URL for sleeper API: "https://api.sleeper.app/v1/draft/{draft_id}/{picks}"
    Transactions URL: 'https://api.sleeper.app/v1/league/{league_id}/transactions/{week}'
    Players URL: 'https://api.sleeper.app/v1/players/nfl'

    Args:
        base (string): Base object for sleeper API call. Example league, draft, players
        base_id (string): ID associated with the base sleeper API call
        endpoint (string): Endpoint to get from Sleeper API

    Returns:
        sleeper_json (json): Json blob from the sleeper API endpoint
    """
    # The base variable is the base call, which then sets the right URL
    # Most Sleeper API calls require a ID associated with it to get more detailed information. For example the draft
    # URL expected the draft_id. The league URL wants the league_id
    if base == 'league' or base == 'draft':
        sleeper_base_url = f'https://api.sleeper.app/v1/{base}/{base_id}/{endpoint}'
    elif base == 'transactions':
        sleeper_base_url = f'https://api.sleeper.app/v1/league/{base_id}/transactions/{endpoint}'
    elif base == 'players':
        sleeper_base_url = 'https://api.sleeper.app/v1/players/nfl'
    else:
        sleeper_base_url = 'https://api.sleeper.app/v1/'
        print(f'Not a correct filter')
        exit()

    # Send a GET request to the Sleeper API league endpoint, which holds all the relevant information we need for
    # this helper script. Convert that response to a json and return.
    # print(f'Getting {sleeper_base_url} from Sleeper API')  # Debug statement
    sleeper_json_string = requests.get(sleeper_base_url)
    sleeper_json = sleeper_json_string.json()
    # print(f'Response from Sleeper API: ')  # Debug statement
    # nice_print(sleeper_json)  # Debug statement

    return sleeper_json


def get_league(league_debug, league_league):
    """ Create a DataFrame from the league endpoint to get the league stats. Get the trade deadline from league DF

    Args:
        league_debug (Debug): Class representing the Debug information from the config file
        league_league (League): Class representing the League information from the config file.

    Returns:
        league_df (DataFrame): DataFrame of the league API
        trade_deadline (int): Week of the trade deadline
    """
    refresh = league_debug.refresh
    cloud_storage = league_debug.cloud_storage
    year = league_league.current_year
    league_id = league_league.current_id

    # Save file location
    league_pkl_location = f'data_files/{year}/{league_id}/league_df.pkl'

    if refresh:
        print('Getting league from Sleeper API...')
        league = get_sleeper_api('league', str(league_id), '')

        # The league json blob needs to be normalized, cause of the series  mix type error
        league_df = pd.json_normalize(league, max_level=0)

        # Pickle and save the dataframe for offline use
        save_pickle_catch(league_pkl_location, league_df, cloud_storage)

    league_df = open_pickle_catch(league_pkl_location, cloud_storage)
    trade_deadline = league_df['settings'][0]['trade_deadline']

    nice_print(league_df)
    print(f'Trade deadline is week: {trade_deadline}')

    return league_df, trade_deadline


def process_kept_players(kept_debug, kept_league, players_df):
    """ Open Kept player CSV from Andrew, populate Sleeper API data, then pickle and save

    Args:
        kept_debug (Debug): Class representing the Debug information from the config file
        kept_league (League): Class representing the League information from the config file.
        players_df (DataFrame): DataFrame of players Sleeper API Data

    Return:
        kept_df (dataframe): Dataframe of kept players with player_id
    """
    # TODO Date 1/12/2022 Add a save table of the kept players in order to display them in a link like before.
    refresh = kept_debug.refresh
    cloud_storage = kept_debug.cloud_storage
    year = kept_league.current_year
    first_year = kept_league.first_year
    league_id = kept_league.current_id
    kept_pkl_location = f'data_files/{year}/{league_id}/kept_players/kept_players.pkl'
    kept_players_csv = f'data_files/{year}/{league_id}/kept_players/kept_players.csv'

    if refresh:
        # TODO DATE 1/12/2022 Add a catch for no path to clarify error
        # TODO I don't need to do a path write, cause the league_id folder will be written. Maybe just write the
        # TODO kept_players folder?

        # TODO Add a first year catch
        # Make this a catch function in case kept_csv files change
        if year == first_year:
            kept_df = pd.DataFrame()
            return kept_df
        else:
            kept_df = pd.read_csv(kept_players_csv)

        # Get list of kept player names
        kept_player_list = kept_df['player_name'].tolist()
        print(kept_player_list)  # Debug statement
        nice_print(kept_df)

        # Empty list to store player ids
        player_id_list = []
        # For each player in the list, search the players dataframe to find their player ID
        for player in kept_player_list:
            # Search the player dataframe for the player id with the player name
            # A query has to be used here, because the players_df index is player_id, not player_name
            # TODO Make note that a catch may need to be added here. If a defense is ever kept, they won't have a full
            # TODO name in the sleeper API. Will need to do first+last like done in keeper_df
            query_string = 'full_name == @player'

            # TODO Need to think of a better way to process periods in names like DK Metkaf. Kill me.
            print(f'full_name == {player}')  # Debug. Helps with correcting the kept_players_csv file, so search works

            # TODO Stupid catch and continue for Bills cause of stupid people
            if player == "Buffalo Bills":
                player_id = 'BUF'
                player_id_list.append(player_id)
                nice_print(player_id_list)
                continue

            # TODO Add a catch here for the Mike Williams situation where their are multiple players of the same name
            player_id = players_df.query(query_string)['player_id'][0]

            # TODO Hard Code catches for multiple results?
            # This is here, cause there are 2 Mike Williams
            if player == "Mike Williams":
                player_id = '4068'

            player_id_list.append(player_id)
            nice_print(player_id_list)


        # nice_print(player_id_list)  # Debug statement
        kept_df['player_id'] = player_id_list

        # Set index to player_id, to enable the at function in process_keepers
        kept_df.set_index('player_id', inplace=True, drop=False)

        save_pickle_catch(kept_pkl_location, kept_df, cloud_storage)

    kept_df = open_pickle_catch(kept_pkl_location, cloud_storage)
    nice_print(kept_df)

    return kept_df


def calc_position_average(draft_df):
    """ Calculate the average draft cost at each position

    Args:
        draft_df (DataFrame): Dataframe of drafted players from Sleeper API

    Return:
        position_avg (dict): Dictionary of {position:avg_cost}
    """
    # The metadata contains the position and amount. It is stored as a Series (DF Column) of dictionaries.
    # Split that into a dataframe and use it for the calculation
    draft_metadata_df = draft_df['metadata'].apply(pd.Series)

    position_keys = ['QB', 'RB', 'WR', 'TE', 'DEF']
    position_avg = dict()

    # Loop through each position in the list and create a dataframe for each position. Then calculate the mean at
    # each position and put it in a dictionary that will be returned for np.select against position_amount_avg.
    for position in position_keys:
        pos_filter = draft_metadata_df['position'] == position
        pos_df = draft_metadata_df[pos_filter]
        pos_avg = math.ceil(pos_df['amount'].astype(float).mean())

        position_avg[position] = pos_avg

    return position_avg


def save_process_keepers(keep_debug, keep_league, roster_df, players_df, kept_df, draft_df, traded_players,
                         added_players, dropped_players):
    """ Generate a keeper Dataframe based on the rules of the league

    Args:
        keep_debug (Debug): Class representing the Debug information from the config file
        keep_league (League): Class representing the League information from the config file.
        roster_df (DataFrame): Dataframe with processed roster API information
        players_df (DataFrame): Dataframe of sleeper API players endpoint
        kept_df (DataFrame): Dataframe of kept players with sleeper API information
        draft_df (DataFrame): Dataframe of drafted players from API
        traded_players (List): List of traded players (str)
        added_players (List): List of players added after the trade deadline (str)
        dropped_players (List): List of players dropped after the trade deadline (str)

    Return:
        keeper_df (DataFrame):
    """
    refresh = keep_debug.refresh
    cloud_storage = keep_debug.cloud_storage
    year = keep_league.current_year
    league_id = keep_league.current_id
    draft_type = keep_league.draft_type
    # Save file location
    keeper_pkl_location = f'data_files/{year}/{league_id}/keeper_df.pkl'

    if refresh:

        # Generate owner_id list from roster df
        owner_list = roster_df['owner_id'].tolist()

        # Empty dictionary to hold the generated flat keeper to owner list
        keeper_dict = {}
        # Loop through owners
        for owner_id in owner_list:
            # print(owner_id)  # Debug statement
            players = roster_df.at[owner_id, 'players']
            # print(players)  # Debug statement

            # Loop through the players on the roster and add them to the keeper dict.
            for player_id in players:
                keeper_dict[player_id] = owner_id

        # print(keeper_dict)  # Debug statement
        keeper_df = pd.DataFrame.from_dict(keeper_dict, orient='index', columns=['owner_id'])

        # Get list of the player_ids from the dictionary we made above. Returns view python 3
        # Get list of owner_ids from the dictionary we made above. Returns view python 3
        list_of_player_ids = keeper_dict.keys()
        list_of_owner_ids = keeper_dict.values()

        # Create the column of player_ids for easier searching later
        keeper_df['player_id'] = list_of_player_ids

        # Create empty lists to hold the column data. These lists will be inserted into the keeper DF
        list_of_player_names = []
        list_of_player_positions = []
        list_of_player_years_kept = []
        list_of_player_draft_round = []
        list_of_player_traded_bool = []
        list_of_player_added_bool = []
        list_of_player_dropped_bool = []
        list_of_player_draft_amounts = []  # This will store the auction cost at draft, which is amount in the API
        for player_id in list_of_player_ids:
            # Get the name and position from the Player DataFrame
            # Defenses don't have full_name in the sleeper API. So need to combine first and last name to make full name
            # Get the position. Add them to the list of player names and positions
            first_name = players_df.at[player_id, 'first_name']
            last_name = players_df.at[player_id, 'last_name']
            position = players_df.at[player_id, 'position']
            player_name = first_name + ' ' + last_name
            list_of_player_names.append(player_name)
            list_of_player_positions.append(position)

            # Get years kept for each player set to 0 if not in the kept player list
            if kept_df.empty or kept_df[kept_df['player_id'].isin([player_id])].empty:
                years_kept = 0
            else:
                years_kept = kept_df.at[player_id, 'years_kept']
            list_of_player_years_kept.append(years_kept)

            # Here's how to get the draft round of a player based on their player_id
            # Also add the amount if it's they were drafted
            if draft_df[draft_df.index.isin([player_id])].empty:
                # This is kind of a hack, but should work unless there's something else I want to do later
                # Anyway UDFA keeper cost is round 8 per the YAFL constitution, so set the drafted round to 9, so I can
                # just subtract it by 1.
                # If a player wasn't drafted, set their draft_amount to 0
                draft_round = 9
                draft_amount = 0
            elif draft_type == 'auction':
                draft_round = draft_df.at[player_id, 'round']
                draft_amount = draft_df.at[player_id, 'metadata']['amount']
            else:
                draft_round = draft_df.at[player_id, 'round']
                draft_amount = 1000  # Going to do a small hack here and set a insane value, to sort for note.
            list_of_player_draft_round.append(draft_round)
            list_of_player_draft_amounts.append(draft_amount)

            # If the player was traded, then set Traded to True. Store in list to be added to keeper dataframe.
            if player_id in traded_players:
                list_of_player_traded_bool.append(True)
            else:
                list_of_player_traded_bool.append(False)

            # If the player was added after the trade deadline, then set added to True.
            # Store in list to be added to keeper dataframe.
            if player_id in added_players:
                list_of_player_added_bool.append(True)
            else:
                list_of_player_added_bool.append(False)

            # If the player was dropped after the trade deadline, then set dropped to True.
            # Store in list to be added to keeper dataframe.
            if player_id in dropped_players:
                list_of_player_dropped_bool.append(True)
            else:
                list_of_player_dropped_bool.append(False)

        # Generate list of owner names from owner_id
        list_of_owner_names = []
        for owner_id in list_of_owner_ids:
            owner_name = roster_df.at[owner_id, 'display_name']
            list_of_owner_names.append(owner_name)

        # Create the column of player_ids for easier searching later
        # This can be done all at once, but it is easier to read broken out, so I am leaving it broken out.
        keeper_df['player_name'] = list_of_player_names
        keeper_df['position'] = list_of_player_positions
        keeper_df['owner_name'] = list_of_owner_names
        keeper_df['years_kept'] = list_of_player_years_kept
        keeper_df['draft_round'] = list_of_player_draft_round
        keeper_df['traded'] = list_of_player_traded_bool
        keeper_df['added'] = list_of_player_added_bool
        keeper_df['dropped'] = list_of_player_dropped_bool
        keeper_df['draft_amount'] = list_of_player_draft_amounts

        # TODO Note that this is important for YAFL keepers - Round Cost reset on years served
        # Calculate keeper cost. Take into account if a player was traded.
        # Use a np.select and fill cost field based on the traded field
        # If the traded field is TRUE, then reset the keeper value with the following formula
        #   Draft Round + years kept - 1 = Cost
        #       Example with Dak: 4 + 2 - 1 = 5 Dak was originally drafted at round 6 and is 5 round keeper after reset
        # If the traded field is False, then just subtract 1 from draft round
        #       Example with A. Cooper: Drafted 4 - 1 = 3. Cooper is a 3rd round keeper.
        conditions = [keeper_df['traded'] == True, keeper_df['traded'] == False]
        outputs = [keeper_df['draft_round'] + keeper_df['years_kept'] - 1, keeper_df['draft_round'] - 1]
        res = np.select(conditions, outputs)
        keeper_df = keeper_df.assign(cost=pd.Series(res).values)

        # TODO Note that this is import for YAFL Keepers - Years served.
        # Reset years kept if the player was traded
        # Use a np.select and fill cost field based on the traded field
        # If the traded field is TRUE, then reset the years kept to 0
        # If the traded field is False, then just subtract 1 from draft round
        conditions = [keeper_df['traded'] == True, keeper_df['traded'] == False]
        outputs = ['0', keeper_df['years_kept']]
        res = np.select(conditions, outputs)
        keeper_df = keeper_df.assign(new_years_kept=pd.Series(res).values)

        # TODO This is important for RUN.
        # If the draft was an auction, then get the average draft amount for each position.
        # Use an apply to apply it correctly based on the position.
        if draft_type == 'auction':
            pos_avg_amount = calc_position_average(draft_df)
            # nice_print(pos_avg_amount)  # Debug statement
            keeper_df['pos_avg_amount'] = keeper_df.apply(lambda x: pos_avg_amount[x['position']], axis=1)
            # nice_print(keeper_df)  # Debug statement
        else:
            keeper_df['pos_avg_amount'] = 0

        # TODO This is important for RUN keepers.
        # Apply different functions based on amount and drafted.
        # If a player was drafted, then calculate their keep amount (cost). If not then need to average
        # Use a np.select and fill keep_amount field based if a player was drafted
        # If the draft_amount is 0, then set the keep_amount to the players position average amount
        # If the draft_amount is not 0, then apply the RUN keeper formula
        #   year_amount = draft_amount + 5 (Add 5 to draft amount)
        #   keep_amount = year_amount + 10%(year_amount) (Keep amount is new draft amount + 10% interest
        #   Round the keep_amount up
        conditions = [keeper_df['draft_amount'] == 0, keeper_df['draft_amount'] != 0]
        outputs = [keeper_df['pos_avg_amount'], ((keeper_df['draft_amount'].astype(int) + 5)*1.10).apply(np.ceil)]
        res = np.select(conditions, outputs)
        keeper_df = keeper_df.assign(keep_amount=pd.Series(res.astype(int)).values)

        # TODO Maybe change how this is being filtered, but for now if draft is not auction, then do this.
        if draft_type == 'auction':
            # Populate the Note field. This field will display if a player was traded and also the reason why a player
            # can not be kept
            # If a player was added after the trade deadline, then that is the reason they are ineligible
            # If a player was dropped after the trade deadline, then that is the reason they are ineligible
            # If a player years kept is 2, then that is the reason they are ineligible. Max years kept is 2.
            # Use the old years_kept, because RUN doesn't have a keeper reset
            conditions = [keeper_df['added'] == True, keeper_df['dropped'] == True,
                          keeper_df['years_kept'].astype(int) >= 2, keeper_df['draft_amount'] == 0]
            outputs = ['Ineligible. Added after trade deadline.', 'Ineligible. Dropped after trade deadline.',
                       'Ineligible. Reached years kept limit of 2',
                       'Player not drafted. Set keeper cost to positional average']
            res = np.select(conditions, outputs, default='')
            keeper_df = keeper_df.assign(note=pd.Series(res).values)

            # Small function to filter the eligible players. If a player was added or dropped after the trade deadline
            # or has been kept for 2 years, then the player is ineligible to be kept.
            # This function is used as the lambda function in the eligible apply.
            def process_eligible_run(added, dropped, new_years_kept):
                if added is True:
                    eligible = False
                elif dropped is True:
                    eligible = False
                elif int(new_years_kept) >= 2:
                    eligible = False
                else:
                    eligible = True
                return eligible

            # Apply process_eligible across the keeper_df. Axis=1 applies it across the columns of the dataframe
            keeper_df['eligible'] = keeper_df.apply(
                lambda x: process_eligible_run(x['added'], x['dropped'], x['years_kept']), axis=1)

        else:
            # TODO Note that this is for YAFL keepers note field.
            # Populate the Note field. This field will display if a player was traded and also the reason why a player
            # can not be kept
            # If a player was added after the trade deadline, then that is the reason they are ineligible
            # If a player was dropped after the trade deadline, then that is the reason they are ineligible
            # If a player cost is 0, then they were drafted in the first round. First round drafters can not be kept.
            # If a player years kept is 2, then that is the reason they are ineligible. Max years kept is 2.
            # If a player was traded, then their keeper value (years kept and cost) is reset.
            conditions = [keeper_df['added'] == True, keeper_df['dropped'] == True, keeper_df['cost'] == 0,
                          keeper_df['new_years_kept'].astype(int) >= 2, keeper_df['traded'] == True,
                          keeper_df['draft_amount'] == 0]
            outputs = ['Ineligible. Added after trade deadline.', 'Ineligible. Dropped after trade deadline.',
                       'Ineligible. Drafted in first round.', 'Ineligible. Reached years kept limit of 2',
                       'Player traded, keeper value reset.', 'Player not drafted. Set keeper cost to 8 round']
            res = np.select(conditions, outputs, default='')
            keeper_df = keeper_df.assign(note=pd.Series(res).values)

            # Small function to filter the eligible players. If a player was added or dropped after the trade deadline,
            # was drafted in the first round, or has been kept for 2 years, then the player is ineligible to be kept.
            # This function is used as teh lambda function in the eligible apply.
            def process_eligible_yafl(added, dropped, cost, new_years_kept):
                if added is True:
                    eligible = False
                elif dropped is True:
                    eligible = False
                elif cost == 0:
                    eligible = False
                elif int(new_years_kept) >= 2:
                    eligible = False
                else:
                    eligible = True
                return eligible

            # Apply process_eligible across the keeper_df. Axis=1 applies it across the columns of the dataframe
            keeper_df['eligible'] = keeper_df.apply(
                lambda x: process_eligible_yafl(x['added'], x['dropped'], x['cost'], x['new_years_kept']), axis=1)

        save_pickle_catch(keeper_pkl_location, keeper_df, cloud_storage)

    keeper_df = open_pickle_catch(keeper_pkl_location, cloud_storage)
    nice_print(keeper_df)

    return keeper_df


def save_keeper_table(table_debug, table_league, keeper_df):
    """ Generate 2 html tables from the keeper Dataframe. Also save a CSV file.

    Args:
        table_debug (Debug): Class representing the Debug information from the config file
        table_league (League): Class representing the League information from the config file.
        keeper_df (DataFrame): DataFrame of keepers
    """
    refresh = table_debug.refresh
    cloud_storage = table_debug.cloud_storage
    year = table_league.current_year
    league_id = table_league.current_id
    draft_type = table_league.draft_type
    # Save location for keeper html tables
    keeper_table_location = f'data_files/{year}/{league_id}/keeper_table.html'
    keeper_table_human_full_location = f'data_files/{year}/{league_id}/keeper_human_table.html'
    keeper_table_csv = f'data_files/{year}/{league_id}/keeper_table.csv'
    keeper_filtered_table_location = f'data_files/{year}/{league_id}/keeper_table_filtered.html'

    if refresh:
        # TODO DATE 1/13/2022 . Here is where I should filter out the results and also rename the headers of the table
        #  to something that is easier for someone to read and follow. I can build a new DF and chang the columns
        #  titles and drop.
        # Generate a html table from the dataframe.
        # classes is used to allow the table to have unique css styling.
        # The css style sheet will reference .mystyle
        # TODO Note this is the full keeper_df converted to a html table. This can be useful with a debug interface
        #   to remotely debug issue with the keeper dataframe.
        keeper_html = keeper_df.to_html(index=False, classes='mystyle')
        save_html_catch(keeper_table_location, keeper_html, cloud_storage)

        # TODO Note this is the full human-readable keeper_df. Going to offer it as a check-box, link, or some form
        #   for the nerds like Andrew, MW, and I.
        if draft_type == 'auction':
            keeper_human_full_filter_list = ['owner_name', 'player_name', 'position', 'years_kept', 'draft_amount',
                                             'keep_amount', 'eligible', 'note']
            keeper_human_full_df = keeper_df[keeper_human_full_filter_list]
            human_full_column_list = ['Owner', 'Player', 'Position', 'Years Kept', f'Draft Cost($) {year}',
                                      f'Keeper Cost($) {int(year)+1}', 'Eligible', 'Note']
            keeper_human_full_df.columns = human_full_column_list
        else:
            keeper_human_full_filter_list = ['owner_name', 'player_name', 'position', 'years_kept', 'new_years_kept',
                                             'draft_round', 'cost', 'eligible', 'note']
            keeper_human_full_df = keeper_df[keeper_human_full_filter_list]
            human_full_column_list = ['Owner', 'Player', 'Position', 'Old Years Kept', 'New Years Kept',
                                      f'Draft Round {year}', f'Keeper Cost {int(year)+1}', 'Eligible', 'Note']
            keeper_human_full_df.columns = human_full_column_list
        keeper_human_full_html = keeper_human_full_df.to_html(index=False, classes='mystyle')
        save_html_catch(keeper_table_human_full_location, keeper_human_full_html, cloud_storage)
        # I can just save the df as csv, cause the folder directory will be created by the above function

        # Quick and dirty tmp fix
        if cloud_storage:
            tmp = '/tmp/'
            keeper_table_csv = tmp + keeper_table_csv

        keeper_human_full_df.to_csv(keeper_table_csv, index=False)

        # Also generate a filtered keeper table, which will be the default table served from the webpage.
        if draft_type == 'auction':
            keeper_filter_list = ['owner_name', 'player_name', 'position', 'years_kept', 'keep_amount', 'note',
                                  'eligible']
            filtered_keeper_df = keeper_df[keeper_filter_list]
            filter_column_list = ['Owner', 'Player', 'Position', 'Years Kept', f'Keeper Cost {int(year)+1}', 'Note',
                                  'Eligible']
            filtered_keeper_df.columns = filter_column_list

        else:
            keeper_filter_list = ['owner_name', 'player_name', 'position', 'new_years_kept', 'cost', 'note', 'eligible']
            filtered_keeper_df = keeper_df[keeper_filter_list]
            filter_column_list = ['Owner', 'Player', 'Position', 'Years Kept', f'Keeper Cost {int(year)+1}', 'Note',
                                  'Eligible']
            filtered_keeper_df.columns = filter_column_list
        eligible_filter = filtered_keeper_df['Eligible'] == True
        eligible_filtered_keeper_df = filtered_keeper_df[eligible_filter]
        # Save the filtered html table
        keeper_filtered_html = eligible_filtered_keeper_df.to_html(index=False, classes='mystyle')
        save_html_catch(keeper_filtered_table_location, keeper_filtered_html, cloud_storage)

    return


def save_traded_picks_table(picks_debug, picks_league, traded_picks_df):
    """ Generate 2 html tables from the traded picks Dataframe.

    Args:
        picks_debug (Debug): Class representing the Debug information from the config file
        picks_league (League): Class representing the League information from the config file.
        traded_picks_df (DataFrame): DataFrame of traded picks
    """
    refresh = picks_debug.refresh
    cloud_storage = picks_debug.cloud_storage
    year = picks_league.current_year
    league_id = picks_league.current_id
    # Save location for keeper html tables
    traded_picks_table_location = f'data_files/{year}/{league_id}/traded_picks_table.html'
    traded_picks_filtered_table_location = f'data_files/{year}/{league_id}/traded_picks_table_filtered.html'
    traded_picks_table_csv = f'data_files/{year}/{league_id}/traded_picks_table.csv'

    if refresh:
        # Generate a html table from the dataframe.
        # classes is used to allow the table to have unique css styling.
        # The css style sheet will reference .mystyle
        traded_picks_html = traded_picks_df.to_html(index=False, classes='mystyle')
        save_html_catch(traded_picks_table_location, traded_picks_html, cloud_storage)

        # Also generate a filtered keeper table, which will be the default table served from the webpage.
        filtered_traded_picks_list = ['new_owner_display', 'season', 'round', 'previous_owner_display',
                                      'original_owner_display', 'gained_draft_picks', 'lost_draft_picks']

        # Catch for empty trade_picks_df, no traded draft picks
        if traded_picks_df.empty:
            # TODO Consider setting a empty catch to save the table html as.
            filtered_traded_picks_df = traded_picks_df
        else:
            filtered_traded_picks_df = traded_picks_df[filtered_traded_picks_list]
            filtered_traded_column_list = ['New Owner', 'Season', 'Round', 'Previous Owner', 'Original Owner',
                                           'Description of Gained Draft Pick', 'Description of Lost Draft Pick']
            filtered_traded_picks_df.columns = filtered_traded_column_list

        # Save the filtered html table
        traded_picks_filtered_html = filtered_traded_picks_df.to_html(index=False, classes='mystyle')
        save_html_catch(traded_picks_filtered_table_location, traded_picks_filtered_html, cloud_storage)

        # quick tmp fix
        if cloud_storage:
            tmp = '/tmp/'
            traded_picks_table_csv = tmp + traded_picks_table_csv

        filtered_traded_picks_df.to_csv(traded_picks_table_csv, index=False, na_rep='')

    return


def save_kept_players_table(kept_debug, kept_league, kept_players_df):
    """ Generate 2 html tables from the traded picks Dataframe.

    Args:
        kept_debug (Debug): Class representing the Debug information from the config file
        kept_league (League): Class representing the League information from the config file.
        kept_players_df (DataFrame): DataFrame of kept players
    """
    refresh = kept_debug.refresh
    cloud_storage = kept_debug.cloud_storage
    year = kept_league.current_year
    league_id = kept_league.current_id
    # Save location for keeper html tables
    kept_players_table_location = f'data_files/{year}/{league_id}/kept_players/kept_players_table.html'
    kept_players_filter_table_location = f'data_files/{year}/{league_id}/kept_players/kept_players_table_filtered.html'
    kept_players_csv_location = f'data_files/{year}/{league_id}/kept_players/kept_debug_generated_players.csv'

    if refresh:
        # Generate a html table from the dataframe.
        # classes is used to allow the table to have unique css styling.
        # The css style sheet will reference .mystyle
        kept_players_html = kept_players_df.to_html(index=False, classes='mystyle', na_rep='')
        save_html_catch(kept_players_table_location, kept_players_html, cloud_storage)

        # Also generate a filtered keeper table, which will be the default table served from the webpage.
        filtered_kept_players_list = ['display_name', 'player_name', 'years_kept']
        filtered_kept_players_df = kept_players_df[filtered_kept_players_list]
        column_list = ['Owner', 'Player', 'Years Kept']
        filtered_kept_players_df.columns = column_list
        # Save the filtered html table
        kept_players_filtered_html = filtered_kept_players_df.to_html(index=False, classes='mystyle')
        save_html_catch(kept_players_filter_table_location, kept_players_filtered_html, cloud_storage)

        # Cloud Storage catch
        if cloud_storage:
            tmp = '/tmp/'
            kept_players_csv_location = tmp + kept_players_csv_location

        filtered_kept_players_df.to_csv(kept_players_csv_location, index=False, na_rep='')

    return


def upload_cloud(blob_path, source_file):

    # Initial Connect Stuff
    storage_client = storage.Client()

    # Hard coded name for the bucket
    bucket_name = 'test-deploy-364006.appspot.com'

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.upload_from_filename(source_file)
        print('file: ', source_file, ' uploaded to bucket: ', bucket_name, ' successfully')
    except Exception as e:
        print(e)

    return


def download_cloud(source_blob, destination_file):

    # Initial Connect Stuff
    storage_client = storage.Client()

    # Hard coded name for the bucket
    bucket_name = 'test-deploy-364006.appspot.com'

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob)

        # Debug statements
        print(f'Debug for download_cloud: source_blob = {source_blob} destination_file = {destination_file}')

        # Test making the dir first
        # If data_files doesn't exist, create the directory
        # Since the function is called with the full pickle, strip out the file_name and only populate the directories.
        file = destination_file.rsplit('/', 1)[-1]
        folder_string = destination_file.rstrip(file)

        path = Path(folder_string)
        path.mkdir(parents=True, exist_ok=True)

        blob.download_to_filename(destination_file)
    except Exception as e:
        print(f'Inside the error exception handler')
        print(e)

    print(f'Downloaded to {destination_file}')

    return


def main_application(main_debug, main_league):
    """ Main of the application

    Args:
        main_debug (Debug): Class representing the Debug information from the config file
        main_league (League): Class representing the League information from the config file.
    """
    # Get a DataFrame of the league API from Sleeper. Set the trade_deadline
    league_df, trade_deadline = get_league(main_debug, main_league)

    # Get a DataFrame of the rosters from the sleeper API.
    roster_df = get_rosters(main_debug, main_league)

    # Get a DataFrame of the players
    players_df = get_players(main_debug)

    # Get a DataFrame of the drafted players
    draft_df = get_drafted_players(main_debug, main_league)

    # Get a DataFrame of all the transactions in the league
    transactions_df = get_transactions(main_debug, main_league, trade_deadline)

    # Get traded draft picks from transactions
    traded_picks_df = get_traded_picks(main_debug, main_league, transactions_df, roster_df)

    # Process the transactions. Return a list of the traded players, dropped, added
    traded_players, dropped_players, added_players = process_transactions(main_debug, main_league,
                                                                          transactions_df, trade_deadline)

    # Process the kept_players.csv provided by Andrew. Return a DataFrame of kept players populated with Sleeper data
    kept_players_df = process_kept_players(main_debug, main_league, players_df)

    # Generate a keeper Dataframe
    keeper_df = save_process_keepers(main_debug, main_league, roster_df, players_df, kept_players_df, draft_df,
                                     traded_players, added_players, dropped_players)

    # Generate a full and filtered keeper html table to be served by the webpage
    save_keeper_table(main_debug, main_league, keeper_df)

    # Generate a full and filtered traded draft pick html table to be served by the webpage
    # Add catch in case there were no traded picks that year.
    #if not traded_picks_df.empty:
    save_traded_picks_table(main_debug, main_league, traded_picks_df)

    # Generate a full and filtered kept players html table to be served by the webpage
    # Add catch in case kept players dataframe is empty.
    if not kept_players_df.empty:
        save_kept_players_table(main_debug, main_league, kept_players_df)

    nice_print(traded_picks_df)
    nice_print(keeper_df)

    return


if __name__ == "__main__":
    # Only load the config when called from terminal. When main is called have the keeper website override the class.
    # config_league, config_debug = load_config('config.ini')
    # config_league, config_debug = load_config('run_config.ini')
    config_league, config_debug = load_config('yafl_config.ini')

    main_application(config_debug, config_league)

    sys.exit(0)


    # TODO DATE 1/11/2021. Figure out how to handle running the program without calling from webpage for shell
    # operation. The main issue will be load_config and how certain variables are handled. I can probably call a
    # function that will set the year, first_year, and all that stuff. This would have been set by the webpage



    # TODO DATE 01/05/2022.
    # TODO Add filtering to the webpage, should be easy now with the dataframes

    # TODO DATE 08/30/22
    # Fix readme for future Jeff to save him the hassle I just went through. You can not generate stuff for a new league
    # until after a draft has taken place. I tried to do 2022 to handle the pre-draft MW and I crap and it was shit
    # Realized a lot of my logic is based on the league having drafted. That affects keeepers too.
