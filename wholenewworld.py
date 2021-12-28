import configparser
import time
from itertools import chain
import requests

import pandas as pd
import os
import sys
import json
from pprint import pformat
from sleeper_wrapper import League, User, Stats, Players, Drafts

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
#

#   Config File
#       League Name
#       this might not be needed


def nice_print(args):
    """ Pretty print args. Real talk, best function I've ever written.

    Args:
        args: Thing to pretty print
    """
    #print('{}'.format(pformat(args)))
    print(f'{pformat(args)}')


# TODO Remove this function after done messing with dataframes
def get_user_dataframe(refresh, league):
    """ Get users in league. Returns a diction of user id and user names.

    user_df: ['display_name', 'user_id']

    Args:
        league (obj): League object from sleeper_wrapper_api

    Returns:
        user_df (dataframe): Dataframe obj of user_id and user_name
    """
    # Save file location
    users_pkl_location = f'data_files/{year}/users_df.pkl'

    if refresh:
        print('Getting all users in league...')
        users = league.get_users()

        # Create dataframe from users API call with display_name and user_id as columns
        users_df = pd.DataFrame(users)

        # Set index to user_id for loc
        # users_df.set_index('user_id', inplace=True)

        # Sort the DF by the user_id, will use this to drop in the display_name to the rosters_df
        users_df.sort_values(by=['user_id'], inplace=True)

        # This gets the name of the manager
        # 12/23/21 - This is for the old users_df. I changed it and now the index is not user_id
        # print(users_df.loc['461690174502334464']['display_name'])

        # Pickle and save the dataframe for offline use
        users_df.to_pickle(users_pkl_location)

    users_df = open_pickle_catch(users_pkl_location)

    nice_print(users_df)

    return users_df


def open_pickle_catch(file_location):
    """ Try to open the file and file_location, if it does not open assert

    Args:
        file_location (str): Directory of the pickle file to read

    Return:
        file_df (DataFrame): DataFrame read from the pickle file

    """
    try:
        with open(file_location) as f:
            file_df = pd.read_pickle(file_location)
    except Exception as e:
        print(e)
        assert_string = f'Unable to open {file_location}. \n Use --refresh to get data from Sleeper API'
        assert False, assert_string

    return file_df


def get_players(refresh):
    """ Get all the players from Sleeper save in DataFrame

    Args:
        refresh (bool): Refresh flag from cmd line

    Returns:
        players_df (DataFrame): DateFrame of all the players
    """
    # Save file location
    players_pkl_location = 'data_files/common/players_df.pkl'

    if refresh:
        print('Getting all players from Sleeper API...')
        players = get_sleeper_api('players', '', '')

        players_df = pd.DataFrame.from_dict(players)

        # Debug statements
        print(players_df.index)
        print(players_df.columns)

        # Player access examples for later
        print(players_df['LAR']['first_name'])
        print(players_df['5870']['fantasy_positions'])

        # Pickle and save the dataframe for offline use
        players_df.to_pickle(players_pkl_location)

    players_df = open_pickle_catch(players_pkl_location)

    return players_df


# TODO This is the old RUN keeper webpage stuff
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


def get_drafted_players(refresh, league_id, year):
    """ Get the drafted players in YAFL 2.0 save to draft_df DataFrame

    Args:
        refresh (bool): Refresh flag from cmd line
        league_id (int): League object from sleeper_wrapper_api for YAFL 2.0
        year (int): Year of league to get API data from

    Returns:
        draft_df (DataFrame): DataFrame of drafted players
    """
    # Save file locations
    draft_pkl_location = f'data_files/{year}/draft_df.pkl'
    draft_base_pkl_location = f'data_files/{year}/draft_base_df.pkl'
    if refresh:
        print('Getting all draft picks from league...')
        # Get all the drafts for the league
        all_drafts = get_sleeper_api('league', str(league_id), 'drafts')

        # Sleeper will only have 1 draft, so we can access the first result from the list
        draft_id = all_drafts[0]['draft_id']

        # Create base draft object with draft_id
        draft_base = get_sleeper_api('draft', draft_id, '')

        # Create a base draft dataframe object. This will likely later be used for making the draft board
        draft_base_df = pd.json_normalize(draft_base, max_level=0)
        draft_base_df.to_pickle(draft_base_pkl_location)
        nice_print(draft_base_df)

        # Get the picks for the draft at draft_id
        draft = get_sleeper_api('draft', draft_id, 'picks')

        # These are the columns to keep in the draft dataframe
        # TODO Handle Auction as well here and probably need to re think about the index set
        draft_df = pd.DataFrame(draft)

        # Set player_id to the index, so loc can be called with player_id
        draft_df.set_index('player_id', inplace=True)

        # # Here's the loc for the player name from the player_id.
        # print('Player Full Name {} {}'.format(draft_df.loc['4046']['metadata']['first_name'],
        #                                       draft_df.loc['4046']['metadata']['last_name']))

        nice_print(draft_df)

        # Pickle and save the dataframe for offline use
        draft_df.to_pickle(draft_pkl_location)

    draft_df = open_pickle_catch(draft_pkl_location)
    # TODO Return draft_base_df as well and also probably need to set

    return draft_df


def load_config():
    """ Open config file and get variables we need

    The config file, config.ini, should be in the root directory of the project with sleeper_keeper.py (main).
    Format for config file is:
         [league]
            year = 2021
            name = YAFL 2.0

    Returns:
        year (int): Year of league
        name (str): Name of league
    """
    config = configparser.ConfigParser()
    print(config.sections())
    config.read('config.ini')
    print(config.sections())

    # Get the info we want like year and league name
    league_year = config.getint('league', 'year')
    league_name = config.get('league', 'name')
    league_id_config = config.get('league', 'id')

    return league_year, league_name, league_id_config


def get_rosters(refresh, league_id, year):
    """ Get the current roster for each team.

    Gets the roster for every team from the league object. Maps the user_id to the display_name. Saves it to disk.

    Args:
        refresh (bool): Boolean to trigger Sleeper API calls
        league_id (str): League ID from Sleeper API
        year (int): Year of league to get API data

    Returns:
        rosters_df (DataFrame): DataFrame of the roster Sleeper API call
    """
    # Save file location
    rosters_pkl_location = f'data_files/{year}/rosters_df.pkl'

    if refresh:
        # Get the users from the Sleeper API to get the display_name for the rosters_df
        print('Getting all users in league...')
        users = get_sleeper_api('league', league_id, 'users')

        # Create dataframe from users API call with display_name and user_id as columns
        # Sort the DF by the user_id, will use this to drop in the display_name to the rosters_df
        users_df = pd.DataFrame(users)  # , columns=['display_name', 'user_id'])
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
            display_name = users_df['display_name']
            rosters_df['display_name'] = display_name
        else:
            print(f'The roster_df and user_df have different user_id columns. Manual inspection required')
            exit()

        # Pickle and save the dataframe for offline use
        rosters_df.to_pickle(rosters_pkl_location)

    rosters_df = open_pickle_catch(rosters_pkl_location)

    nice_print(rosters_df)

    return rosters_df


def get_transactions(refresh, league_id, trade_deadline, year):
    """ Go through the transactions and get dropped players after the trade deadline

    Get all the transactions from the Sleeper API after the trade deadline till the end of the season. Filter the
    completed transactions into a Dataframe, which will be used to determine the dropped players after the trade
    deadline.

    transactions_dataframe:
        transaction_id      creator              status     drops         draft_picks  consenter_ids  status_updated
        769105866526982144  468535859126202368   complete   {'4972': 11}  []           [11]           1637741217895

    Args:
        refresh (bool): Boolean to determine if a call should be made to the Sleeper API
        league_id (str): League ID tog et Sleeper API data
        trade_deadline (int): Trade deadline for YAFL
        year (int): Year of league to get API data

    Returns:
        final_transactions_df (Dataframe): Dataframe of completed transactions after trade deadline
    """
    # Save file location
    transactions_pkl_location = f'data_files/{year}/transactions_df.pkl'

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

            time.sleep(0.5)

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
        final_transactions_df.to_pickle(transactions_pkl_location)

    final_transactions_df = open_pickle_catch(transactions_pkl_location)
    nice_print(final_transactions_df)

    return final_transactions_df


def process_transactions(transactions_df, trade_deadline):
    """ Process the transactions_df to get the traded players, traded draft picks, and dropped players

    Create a list of the traded players for keeper reset tracking
    Create a list of the dropped players for keeper tracking
    Create a DataFrame of the trade draft picks for future processing.

    Args:
        transactions_df (DataFrame): Transactions from the Sleeper API in a DataFrame
        trade_deadline (int): Trade deadline for league

    Returns:
        traded_players (list): List of player_ids that have been traded
        dropped_players (list): List of player_ids that have been dropped after the trade deadline
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

    # Get the dropped players from the transactions_df
    # Use a lamba function to get all the transactions past the trade_deadline and put them in a dropped players DF
    # Drop the Nan transactions to avoid key errors, then flatten the list and get the dropped players
    drops_filter = transactions_df['week'].apply(lambda x: x > trade_deadline)
    drops_df = transactions_df[drops_filter]
    drops_clean_df = drops_df['drops'].dropna()
    dropped_list = drops_clean_df.to_list()
    dropped_players = set().union(*(d.keys() for d in dropped_list))

    # Draft picks are stored as a list of list.
    # Use a list comprehension to turn it into a flat list then put it in a DF.
    # Save it for future stuff like picturing the draft pick changes
    draft_picks_lol_df = transactions_df['draft_picks']
    draft_picks_lol = draft_picks_lol_df.to_list()
    draft_picks_list = [draft_pick for draft_picks_list in draft_picks_lol for draft_pick in draft_picks_list]
    draft_picks_df = pd.DataFrame(draft_picks_list)
    draft_picks_file_location = f'data_files/{year}/draft_df.pkl'
    draft_picks_df.to_pickle(draft_picks_file_location)

    nice_print(f'Traded Draft Picks: {draft_picks_df}')
    print(f'dropped_players: {dropped_players}')
    print(f'traded_players: {traded_players}')

    return traded_players, dropped_players, draft_picks_df


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
    #print(f'Getting {sleeper_base_url} from Sleeper API')
    sleeper_json_string = requests.get(sleeper_base_url)
    sleeper_json = sleeper_json_string.json()
    #print(f'Response from Sleeper API: ')
    #nice_print(sleeper_json)

    return sleeper_json


def get_league(refresh, league_id, year):
    """ Create a DataFrame from the league endpoint to get the league stats. Get the trade deadline from league DF

    Args:
        refresh (bool): Boolean for refresh
        league_id (int): League ID from config file
        year (int): Year of league to get API data

    Returns:
        league_df (DataFrame): DataFrame of the league API
        trade_deadline (int): Week of the trade deadline
    """
    # Save file location
    league_pkl_location = f'data_files/{year}/league_df.pkl'

    if refresh:
        print('Getting league from Sleeper API...')
        league = get_sleeper_api('league', str(league_id), '')

        # The league json blob needs to be normalized, cause of the series  mix type error
        league_df = pd.json_normalize(league, max_level=0)

        # Pickle and save the dataframe for offline use
        league_df.to_pickle(league_pkl_location)

    league_df = open_pickle_catch(league_pkl_location)
    trade_deadline = league_df['settings'][0]['trade_deadline']

    nice_print(league_df)
    print(f'Trade deadline is week: {trade_deadline}')

    return league_df, trade_deadline


def process_kept_players(league_id):
    """ Process the draft picks and add them to the rosters_df

    Args:
        draft_picks_df (DataFrame): Dataframe of the draft picks

    Return:
        draft_picks_list (list): List of draft picks
    """
    # TODO DATE - 12/24/21: Kept Player Task
    # TODO - There's a lot more work here to do than it looks like.
    # Need to examine the keeper csv files with Pandas and see if it is worth pandaing them and then pickling?
    # It is probably worth it. Then I also need to incorporate the player data from the sleeper API with the
    # kept players csv.
    # I should also look into the rosters dataframe and the draft dataframe and see if the kept sections for those
    # players will show the correct infomtion


    draft_picks_list = []

    return draft_picks_list


def determine_eligible_keepers(
        roster_dict, player_dict, draft_dict, transactions_dict, traded_picks_dict, kept_players_dict):
    """ Go through the rostered players for a team and determine their keeper eligibility

    Go through the rostered players for each team. If that player was added or dropped, then they are not eligible to
    be kept. If that player was drafted, use the draft cost to determine their keeper cost. If that player was not
    drafted they will cost a round 8 pick, which is determined by the rules of YAFL.

    Args:
        roster_dict (dict): Dictionary of rostered players
        player_dict (dict): Dictionary of all the players in Sleeper
        draft_dict (dict): Dictionary of all drafted players
        transactions_dict (dict): Dictionary of all the transactions after the trade deadline
        traded_picks_dict (dict): Dictionary of all the traded picks
        kept_players_dict (dict): Dictionary of all the kept players

    Returns:
        keeper_dict (dict): Dictionary of eligible keepers
    """
    keeper_dict = dict()

    for owner in roster_dict:
        keeper_dict[owner] = dict()
        keeper_dict[owner]['owner_id'] = roster_dict[owner]['owner_id']
        nice_print(owner)
        for player_id in roster_dict[owner]['player_ids']:
            # If a player was dropped or added, he is not eligible to be kept. Do not add them to the keeper_dict
            if player_id in transactions_dict['drops'] or player_id in transactions_dict['adds']:
                continue
            keeper_dict[owner][player_id] = dict()
            keeper_dict[owner][player_id] = player_dict[player_id]
            if player_id in draft_dict:
                keeper_dict[owner][player_id]['drafted'] = True
                keeper_dict[owner][player_id]['pick_number'] = draft_dict[player_id]['pick_number']
                keeper_dict[owner][player_id]['round'] = draft_dict[player_id]['round']
                keeper_dict[owner][player_id]['is_keeper'] = draft_dict[player_id]['keeper']
                # The draft price for a player is an additional round pick. So if a player was drafted in round 4,
                # they will cost a round 3 draft pick to keep. A player can be kept up to 3 year.
                keeper_dict[owner][player_id]['keeper_cost'] = draft_dict[player_id]['round'] - 1
            else:
                keeper_dict[owner][player_id]['drafted'] = False
                # UDFA cost a round 8 pick to keep
                keeper_dict[owner][player_id]['keeper_cost'] = 8
            # If the player was kept, add years_kept to the keeper_dict. If not set the years_kept to 0.
            if player_id in kept_players_dict:
                keeper_dict[owner][player_id]['years_kept'] = kept_players_dict[player_id]['years_kept']
            else:
                keeper_dict[owner][player_id]['years_kept'] = 0

        # Determine if an owner has traded a draft_pick
        # Since multiple trades can happen a week, need to loop through all the weeks and all the traded picks for each
        # week.
        for week in traded_picks_dict:
            for weekly_traded_pick in traded_picks_dict[week]:
                if roster_dict[owner]['roster_id'] == weekly_traded_pick['owner_id']:
                    keeper_dict[owner]['gained_draft_picks'] = dict()
                    keeper_dict[owner]['gained_draft_picks']['round'] = weekly_traded_pick['round']
                    keeper_dict[owner]['gained_draft_picks']['season'] = weekly_traded_pick['season']
                    # To get the new owner, need to loop through rosters to map roster id to owner
                    for map_owner in roster_dict:
                        if roster_dict[map_owner]['roster_id'] == weekly_traded_pick['previous_owner_id']:
                            keeper_dict[owner]['gained_draft_picks']['new_owner'] = map_owner
                if roster_dict[owner]['roster_id'] == weekly_traded_pick['previous_owner_id']:
                    keeper_dict[owner]['lost_draft_picks'] = dict()
                    keeper_dict[owner]['lost_draft_picks']['round'] = weekly_traded_pick['round']
                    keeper_dict[owner]['lost_draft_picks']['season'] = weekly_traded_pick['season']
                    # To get the new owner, need to loop through rosters to map roster id to owner
                    for map_owner in roster_dict:
                        if roster_dict[map_owner]['roster_id'] == weekly_traded_pick['owner_id']:
                            keeper_dict[owner]['lost_draft_picks']['new_owner'] = map_owner

    nice_print(keeper_dict)
    return keeper_dict


if __name__ == "__main__":
    #league, first_year = get_league_id()
    #user_dict = get_users(league)
    #nice_print(user_dict)
    # keeper_csv_to_table()
    year, name, league_id = load_config()
    print(year)
    # Put the current year and eligible years in the config file. Then I can keep the keeper webpage as it is and
    # Just have that web page call the stuff. OMFG this is the year solution I have been thinking about this whole time
    # And this should be the right way to do it.
    print(name)
    print(league_id)

    # TODO DATE - 12/24/21: The year problem with the rewrite
    # TODO - Need to solve problem of how to call for each year for history sake/ website
    # TODO - Or just figure out a way to run from different config files?
    # Put the current year and eligible years in the config file. Then I can keep the keeper webpage as it is and
    # Just have that web page call the stuff. OMFG this is the year solution I have been thinking about this whole time
    # And this should be the right way to do it.

    # Get user dataframe
    refresh = False
    # users_df = get_user_dataframe(refresh, league)

    league_df, trade_deadline = get_league(refresh, league_id, year)

    # # Get a dictionary of all the rostered players
    roster_df = get_rosters(refresh, league_id, year)

    # Get a dictionary of all the players
    players_df = get_players(refresh)

    # # Get a dictionary of all the drafted players
    draft_df = get_drafted_players(refresh, league_id, year)

    # # Get the transactions after the trade deadline
    transactions_df = get_transactions(refresh, league_id, trade_deadline, year)

    traded_players, dropped_players, draft_picks_df = process_transactions(transactions_df, trade_deadline)

    # TODO DATE - 12/24/21: Combining data from draft and roster DataFrames
    # TODO - Pick up here. Need to work on the draft_df. How much work needs to be done to combine it with display_name
    # TODO - Need to get everything for the keeper function
    # TODO - How will I handle kept_players? Just make a DF out of the CSV like from the RUN test file.

    nice_print(draft_picks_df)
    nice_print(roster_df)

    # TODO DATE - 12/24/21: Process Kept Players work (see function TODO DATE)

    kept_players_df = process_kept_players(league_id)

    exit()

    # TODO - Also need to figure out the kept_players and first_years stuff from get_league_id() in old code

    # nice_print(users_df)
    # nice_print(trade_df)
    # nice_print(roster_df.keys())
    # nice_print(roster_df['players']['461650521292271616'])
    # nice_print(trade_df['draft_picks', '765649664203956224'])

    exit()

    # Get the final keeper list
    keeper_dict = determine_eligible_keepers(
        roster_dict,
        player_dict,
        draft_dict,
        transactions,
        traded_picks,
        kept_dict
    )

    # # Get a list of traded players and dictionary of traded draft picks
    #trades, traded_picks = get_trades(league)

    # # Get the user object to get league info
    # user_obj = User(username)
    #
    # # Get the league object. Will be used to get draft info, transactions, and rosters.
    # league = get_league_id(user_obj, year)
    #
    # # Get the username and id
    # user_dict = get_users(league)
    #
    # # Get a dictionary of all the players
    # player_dict = get_players(refresh, year)
    #
    # # Get the trade deadline from the league settings
    # trade_deadline = get_trade_deadline(league)
    #
    # # Get a dictionary of all the drafted players
    # draft_dict = get_drafted_players(league)
    #
    # # Get a dictionary of all the rostered players
    # roster_dict = get_rosters(league, user_dict)
    #
    # # Get the transactions after the trade deadline
    # transactions = get_transactions(league, trade_deadline)
    #
    # # Get a list of traded players and dictionary of traded draft picks
    # trades, traded_picks = get_trades(league)
    #
    # # DEBUG code to process traded_picks
    # # process_traded_picks(roster_dict, traded_picks)
    #
    # # Get the final keeper list
    # keeper_dict = determine_eligible_keepers(
    #     roster_dict,
    #     player_dict,
    #     draft_dict,
    #     transactions,
    #     traded_picks,
    #     kept_dict
    # )







