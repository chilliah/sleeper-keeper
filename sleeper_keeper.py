import argparse
import json
import os
import sys
from pathlib import Path
from pprint import pformat
from sleeper_wrapper import League, User, Stats, Players, Drafts
from textwrap import dedent


def nice_print(args):
    """ Pretty print args

    Args:
        args: Thing to pretty print
    """
    print('{}'.format(pformat(args)))


def get_league_id(user, year, league_name):
    """ Get the league object from a User object

    Get all the leagues of the user. Find the league id for league_name. Return the League obj.
    Check if year is the first year of the league and if so, set the first_year bool.

    Args:
        user (obj): User object from sleeper_wrapper_api
        year (int): Year of the league to pull information from sleeper API
        league_name (str): Name of the league to pull information from sleeper API

    Returns:
        league (obj): League object from sleeper_wrapper_api
        first_year (bool): True if year is the first year of a league
    """
    all_leagues = user.get_all_leagues('nfl', year)

    # Search all the leagues user plays in and find the one with league_name to get the league_id
    for league_info in all_leagues:
        # Find the ID for the league name
        if league_info['name'] == league_name:
            league_id = league_info['league_id']
            print('League Name: {} found. League ID:  {}...'.format(league_name, league_id))
            break
        else:
            print('League Name: {} is not {}. Checking next league...'.format(league_info['name'], league_name))
            continue
    else:
        # League name not found.
        print('League Name: {} not found. Exiting...'.format(league_name))
        sys.exit(0)

    league = League(league_id)

    # Save the league_dict to data_files. This allows offline mode to check for first year.
    # TODO can I just solve this by creating a blank file for the year?
    league_dict = league.get_league()
    nice_print(league_dict)
    write_data_files(league_dict, 'league_dict')

    # If this is the first year of a league, then previous_league_id will be None.
    # Set first_year to True. This will be used later to check that the kept players have been processed.
    previous_league_id = league_dict['previous_league_id']
    print('{}'.format(previous_league_id))
    first_year = False
    if previous_league_id is None:
        first_year = True

    return league, first_year


def get_drafted_players(league):
    """ Get the drafted players in YAFL 2.0

    Create a Drafts object from the YAFL League object. Get all the picks in the last draft and create
    a dictionary with all the usefully information for YAFL keepers.

    drafted_players have the following structure:
    {player_id: {full_name: full name of player,
                 keeper: bool,
                 pick_number: number player was picked,
                 round: round player was drafted }}

    Args:
        league (obj): League object from sleeper_wrapper_api for YAFL 2.0

    Returns:
        draft_type (str) : Type of draft the league is using the the season
        drafted_players (dict): Dictionary of drafted players
    """
    # Get all drafts for a league
    all_drafts = league.get_all_drafts()

    # TODO Figure out a better way to get the draft data cause dynasty leagues can have multiple drafts
    #  Maybe use a config file with the draft type or specific draft id?
    # Sleeper will only have 1 draft, so we can access the first result from the list
    # Write it to a file, so offline mode can determine draft type
    specific_draft = all_drafts[0]
    nice_print(specific_draft)
    write_data_files(specific_draft, 'draft_api')

    # Get the draft type and store it for keeper cost calculations
    draft_type = specific_draft['type']
    print("Draft Type: {}".format(draft_type))

    draft_id = specific_draft['draft_id']
    draft = Drafts(draft_id)
    draft_picks = draft.get_all_picks()
    drafted_players = dict()

    # Loop through each pick and get relevant information.
    for pick in draft_picks:
        full_name = '{} {}'.format(pick['metadata']['first_name'], pick['metadata']['last_name'])
        player_id = pick['player_id']
        keeper = pick['is_keeper']
        pick_number = pick['pick_no']
        team_id = pick['picked_by']
        draft_round = pick['round']

        if draft_type == "auction":
            amount = pick['metadata']['amount']
        else:
            amount = 0

        drafted_players[player_id] = dict()
        drafted_players[player_id]['full_name'] = full_name
        drafted_players[player_id]['keeper'] = keeper
        drafted_players[player_id]['pick_number'] = pick_number
        drafted_players[player_id]['team_id'] = team_id
        drafted_players[player_id]['round'] = draft_round
        drafted_players[player_id]['amount'] = amount

    print('{}'.format(pformat(drafted_players)))
    write_data_files(drafted_players, 'draft_dict')
    return draft_type, drafted_players


def get_trade_deadline(league):
    """ Get the trade deadline from the Sleeper API

    Args:
        league (obj): League object from sleeper_wrapper_api

    Returns:
        trade_deadline (int): Week of the trade deadline
    """
    league_info = league.get_league()
    trade_deadline = league_info['settings']['trade_deadline']
    return trade_deadline


def get_rosters(league, user_name_dict):
    """ Get the current roster for each team.

    Gets the roster for every team from the league object. Places the roster information into a dictionary.

    roster_dict has the following structure:
        {owner_name: {owner_id: id, players_ids: [list of player ids], roster_id: id}}

    Args:
        league:
        user_name_dict:

    Returns:
        roster_dict (dict): Dictionary
    """
    rosters = league.get_rosters()
    roster_dict = dict()

    # Loop through each roster and get relevant information
    for roster in rosters:
        owner_id = roster['owner_id']
        owner_name = user_name_dict[owner_id]
        roster_id = roster['roster_id']
        players = roster['players']
        print('Roster: {}'.format(pformat(roster)))

        roster_dict[owner_name] = dict()
        roster_dict[owner_name]['owner_id'] = owner_id
        roster_dict[owner_name]['roster_id'] = roster_id
        roster_dict[owner_name]['player_ids'] = players

    nice_print(roster_dict)
    write_data_files(roster_dict, 'rosters')
    return roster_dict


def get_users(league):
    """ Get users in league. Returns a diction of user id and user names.

    user_to_ids: {user_id: user_name}

    Args:
        league (obj): League object from  sleeper_wrapper_api

    Returns:
        user_to_ids (dict): Dictionary of user_id and user_name
    """
    users = league.get_users()
    user_to_ids = dict()

    for user in users:
        user_id = user['user_id']
        user_name = user['display_name']
        user_to_ids[user_id] = user_name

    write_data_files(user_to_ids, 'user_dict')
    return user_to_ids


def get_players(refresh, year):
    """ Get all the players from Sleeper

    Use the player obj from the Sleeper API and get all the players from Sleeper. The relevant information for a
    player is stored in the player_dict, which has the following structure:

    {player_key: {'player_name': player name, 'position': position}}

    Args:
        refresh (bool): Refresh flag from cmd line
        year (int): Year of YAFL 2.0

    Returns:
        player_dict (dict): Dictionary of all the players
    """
    # Pulling all the player data is a >8MB HTTP GET from the Sleeper API. I want to reduce that traffic.
    # If the command line arg refresh is set, pull all the player data from the Sleeper API and save to data_files
    if refresh:
        print('Getting all players from Sleeper API...')
        players = Players().get_all_players()
        write_data_files(players, 'dump_players')

    # Try to open the data file for the players. If we can not access, assert and recommend them to use the
    # --refresh flag
    try:
        with open('data_files/{}/dump_players.json'.format(year)) as f:
            data = json.load(f)
    except Exception as e:
        print(e)
        assert False, 'Unable to open data_files/{}/dump_players.json. \n Use --refresh to get data from Sleeper API'.format(year)

    players = data
    player_dict = dict()

    for player in players:
        player_id = players[player]['player_id']
        player_name = '{} {}'.format(players[player]['first_name'], players[player]['last_name'])
        position = players[player]['position']

        player_dict[player_id] = dict()
        player_dict[player_id]['player_name'] = player_name
        player_dict[player_id]['position'] = position

    nice_print(player_dict)
    write_data_files(player_dict, 'player_dict')
    return player_dict


def get_transactions(league, trade_deadline):
    """ Go through the transactions and get dropped players after the trade deadline

    Go through all the transactions after the trade deadline and get the dropped and added players. Add those players
    to a 'drop' or 'add' list in the transactions_dict. The sleeper API breaks transactions up per week, so we have
    to get the transactions for each week after the trade deadline until the last week of the season.

    transactions_dict:
    {'drops': [list of dropped player ids], 'adds':[list of added players]}

    Args:
        league (obj): Sleeper API league object
        trade_deadline (int): Trade deadline for YAFL

    Returns:
        drop_list (list): List of dropped players
    """
    # Add 1 to the trade deadline. This will be the first week to search for drops. If a player is dropped after
    # that week, then the player is no longer eligible to be kept.
    week = trade_deadline + 1

    transactions_dict = dict()
    transactions_dict['drops'] = list()
    transactions_dict['adds'] = list()

    # Get the transactions from every week after the trade deadline until the last week of the season, which is 16
    # Any player dropped after the trade deadline is not eligible to be kept.
    # TODO: Change this to 17
    while week != 19:
        # TODO: Transactions are store by week
        transactions = league.get_transactions(week)

        print('Transactions for week {}'.format(week))

        for transaction in transactions:
            # Sleeper API will show the failed transactions also. We only want to process the successful transactions
            if transaction['status'] == 'complete':
                nice_print(transaction)
                if transaction['drops']:
                    player_ids = transaction['drops'].keys()
                    for player_id in player_ids:
                        print('Dropped player: {}'.format(player_id))
                        # drop_list.append(player_id)
                        transactions_dict['drops'].append(player_id)
                if transaction['adds']:
                    player_ids = transaction['adds'].keys()
                    for player_id in player_ids:
                        print('Added player: {}'.format(player_id))
                        # add_list.append(player_id)
                        transactions_dict['adds'].append(player_id)

        week = week + 1

    # nice_print(transactions_dict)
    write_data_files(transactions_dict, 'transactions')
    return transactions_dict


# Testing a new method to get traded picks, since we don't care about trades
def get_trades(league):
    """ Go through all the transactions. Get a list of traded players and traded draft picks.

    traded_picks: {week, [{owner_id, previous_owner_id, round}, {owner_id, previous_owner_id, round}]}

    The draft_picks information from the Sleeper API is a list for each trade. This means I will need to iterate
    through the list to then access the dictionary directly.

    Args:
        league (obj): League object from Sleeper API

    Returns:
        traded_players (list): List of player_ids of traded players
        traded_picks (dict): Dictionary of traded picks
    """
    traded_players = list()
    week = 0
    traded_picks = dict()

    while week != 18:
        # Dictionary to hold the traded_picks from the transactions
        traded_picks[week] = dict()
        transactions = league.get_transactions(week)

        for transaction in transactions:
            if transaction['status'] == 'complete':
                if transaction['type'] == 'trade':
                    player_ids = transaction['adds'].keys()
                    for player_id in player_ids:
                        traded_players.append(player_id)
                    if transaction['draft_picks']:
                        traded_picks[week] = transaction['draft_picks']

        week = week + 1

    write_data_files(traded_picks, 'traded_picks')
    return traded_players, traded_picks


def write_data_files(write_dict, file_name):
    """ Save information from Sleeper API to data files

    Saves the GETS from the Sleeper API to data files for offline use. Writes each dictionary to a json file
    Files will be saved at data_files/'write_dict'/'file_name'.json

    Args:
        write_dict (dict): Dictionary to write to file
        file_name (str): Name of saved file .json will be appended to the end
    """
    path = Path('./data_files/{}'.format(year))
    path.mkdir(parents=True, exist_ok=True)

    with open('data_files/{}/{}.json'.format(year, file_name), 'w') as f:
        f.write(json.dumps(write_dict))


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


def pretty_print_keepers(keeper_dict, year):
    """ Print the final keeper information to a file in a human-readable format

    Args:
        keeper_dict (dict): Dictionary of final keeper information
        year (int): Year of YAFL 2.0
    """
    with open('data_files/{}/final_keepers.txt'.format(year), 'w') as f:
        print('The YAFL 2.0 Eligible Keepers for {}\n'.format(year))
        f.write('The YAFL 2.0 Eligible Keepers for {}\n'.format(year))
        for owner in keeper_dict:
            print('Manager: {}\n'.format(owner))
            f.write('Manager: {}\n'.format(owner))

            for player_id in keeper_dict[owner]:
                if player_id == 'owner_id':
                    continue
                # Print out traded away draft pick information
                if player_id == 'lost_draft_picks':
                    new_owner = keeper_dict[owner]['lost_draft_picks']['new_owner']
                    draft_round = keeper_dict[owner]['lost_draft_picks']['round']
                    season = keeper_dict[owner]['lost_draft_picks']['season']
                    print('\t*Lost a {} round {} draft pick. Traded to {}\n'.format(season, draft_round, new_owner))
                    f.write('\t*Lost a {} round {} draft pick. Traded to {}\n'.format(season, draft_round, new_owner))
                    continue
                # Print out gained draft pick information
                if player_id == 'gained_draft_picks':
                    previous_owner = keeper_dict[owner]['gained_draft_picks']['new_owner']
                    draft_round = keeper_dict[owner]['gained_draft_picks']['round']
                    season = keeper_dict[owner]['gained_draft_picks']['season']
                    print('\t*Gained a {} round {} draft pick acquired from {}\n'.format(
                        season,
                        draft_round,
                        previous_owner))
                    f.write('\t*Gained a {} round {} draft pick acquired from {}\n'.format(
                        season,
                        draft_round,
                        previous_owner))
                    continue
                player_name = keeper_dict[owner][player_id]['player_name']
                keeper_cost = keeper_dict[owner][player_id]['keeper_cost']
                position = keeper_dict[owner][player_id]['position']
                years_kept = keeper_dict[owner][player_id]['years_kept']
                # Only print the years kept if it not 0. Always printing the years kept cluttered the screen
                if years_kept == 0:
                    print('\t{} {} - Keeper Cost: Round {}.\n'.format(player_name, position, keeper_cost,))
                    f.write('\t{} {} - Keeper Cost: Round {}.\n'.format(player_name, position, keeper_cost,))
                else:
                    print('\t{} {} - Keeper Cost: Round {}. Years Kept {}\n'.format(player_name,
                                                                                    position,
                                                                                    keeper_cost,
                                                                                    years_kept
                                                                                    ))
                    f.write('\t{} {} - Keeper Cost: Round {}. Years Kept {}\n'.format(player_name,
                                                                                      position,
                                                                                      keeper_cost,
                                                                                      years_kept
                                                                                      ))


def csv_print_keepers_original(keeper_dict, year):
    """ Print the final keeper information to a csv file for Meat "Scope Creep" Wizard

    This was how I originally formatted the keepers csv file. Updated to a new format for csv, but keeping this
    in case the new one does not work well.

    Args:
        keeper_dict (dict): Dictionary of final keeper information
        year (int): Year of YAFL 2.0
    """
    with open('data_files/{}/final_keepers_{}.csv'.format(year, year), 'w') as f:
        print('The YAFL 2.0 Eligible Keepers,')
        f.write('The YAFL 2.0 Eligible Keepers,')
        print('MeatWizard is a little scope-creeping bitch,')
        f.write('MeatWizard is a little scope-creeping bitch,')
        for owner in keeper_dict:
            print('Manager: {},'.format(owner))
            f.write('Manager: {},'.format(owner))

            for player_id in keeper_dict[owner]:
                if player_id == 'owner_id':
                    continue
                # Print out traded away draft pick information
                if player_id == 'lost_draft_picks':
                    new_owner = keeper_dict[owner]['lost_draft_picks']['new_owner']
                    draft_round = keeper_dict[owner]['lost_draft_picks']['round']
                    season = keeper_dict[owner]['lost_draft_picks']['season']
                    print('*Lost a {} round {} draft pick. Traded to {},'.format(season, draft_round, new_owner))
                    f.write('*Lost a {} round {} draft pick. Traded to {},'.format(season, draft_round, new_owner))
                    continue
                # Print out gained draft pick information
                if player_id == 'gained_draft_picks':
                    previous_owner = keeper_dict[owner]['gained_draft_picks']['new_owner']
                    draft_round = keeper_dict[owner]['gained_draft_picks']['round']
                    season = keeper_dict[owner]['gained_draft_picks']['season']
                    print('*Gained a {} round {} draft pick acquired from {},'.format(
                        season,
                        draft_round,
                        previous_owner))
                    f.write('*Gained a {} round {} draft pick acquired from {},'.format(
                        season,
                        draft_round,
                        previous_owner))
                    continue
                player_name = keeper_dict[owner][player_id]['player_name']
                keeper_cost = keeper_dict[owner][player_id]['keeper_cost']
                print('{} - Keeper Cost: Round {},'.format(player_name, keeper_cost))
                f.write('{} - Keeper Cost: Round {},'.format(player_name, keeper_cost))


def csv_print_keepers(keeper_dict, year):
    """ Print the final keeper information to a csv file for Meat "Scope Creep" Wizard

    Args:
        keeper_dict (dict): Dictionary of final keeper information
        year (int): Year of YAFL 2.0
    """
    with open('data_files/{}/final_keepers_{}.csv'.format(year, year), 'w') as f:
        print('The YAFL 2.0 Eligible Keepers for {}\n'.format(year))
        f.write('The YAFL 2.0 Eligible Keepers for {}\n'.format(year))
        print('MeatWizard is a little scope-creeping bitch\n')
        f.write('MeatWizard is a little scope-creeping bitch\n')
        print('Delete these first 3 lines and it will import nice as a CSV.\n')
        f.write('Delete these first 3 lines and it will import nice as a CSV.\n')
        print('Manager,Player_Name,Position,Keeper_Cost,Years_kept\n')
        f.write('Manager,Player_Name,Position,Keeper_Cost,Years_kept\n')
        for owner in keeper_dict:
            for player_id in keeper_dict[owner]:
                if player_id == 'owner_id':
                    continue
                # Print out traded away draft pick information
                if player_id == 'lost_draft_picks':
                    new_owner = keeper_dict[owner]['lost_draft_picks']['new_owner']
                    draft_round = keeper_dict[owner]['lost_draft_picks']['round']
                    season = keeper_dict[owner]['lost_draft_picks']['season']
                    print('*Lost a {} round {} draft pick. Traded to {},'.format(season, draft_round, new_owner))
                    f.write('*Lost a {} round {} draft pick. Traded to {},'.format(season, draft_round, new_owner))
                    continue
                # Print out gained draft pick information
                if player_id == 'gained_draft_picks':
                    previous_owner = keeper_dict[owner]['gained_draft_picks']['new_owner']
                    draft_round = keeper_dict[owner]['gained_draft_picks']['round']
                    season = keeper_dict[owner]['gained_draft_picks']['season']
                    print('*Gained a {} round {} draft pick acquired from {},'.format(
                        season,
                        draft_round,
                        previous_owner))
                    f.write('*Gained a {} round {} draft pick acquired from {},'.format(
                        season,
                        draft_round,
                        previous_owner))
                    continue
                player_name = keeper_dict[owner][player_id]['player_name']
                keeper_cost = keeper_dict[owner][player_id]['keeper_cost']
                position = keeper_dict[owner][player_id]['position']
                years_kept = keeper_dict[owner][player_id]['years_kept']
                print('{},{},{},{},{}\n'.format(owner, player_name, position, keeper_cost, years_kept))
                f.write('{},{},{},{},{}\n'.format(owner, player_name, position, keeper_cost, years_kept))


def position_keeper(keeper_dict, position):
    """ Generate a list of keepers for given position

    Args:
        keeper_dict (dict): Dictionary of eligible keepers
        position (str): Position for which to generate keeper list
    """
    eligible_positions = ['QB', 'RB', 'WR', 'TE', 'DEF']

    if position.upper() not in eligible_positions:
        print('{} not an eligible position. Eligible positions are: QB, RB, WR, TE, or DEF'.format(position))
        return

    with open('positional_keepers.txt', 'w') as f:
        print('{} keeper costs'.format(position))
        f.write('{} keeper costs\n'.format(position))

        for owner in keeper_dict:
            print('Manager: {}'.format(owner))
            f.write('Manager: {}\n'.format(owner))
            for player_id in keeper_dict[owner]:
                if player_id == 'owner_id':
                    continue
                if player_id == 'lost_draft_picks':
                    continue
                if player_id == 'gained_draft_picks':
                    continue
                # Only print keeper information, if the player plays the position
                if position == keeper_dict[owner][player_id]['position']:
                    player_name = keeper_dict[owner][player_id]['player_name']
                    keeper_cost = keeper_dict[owner][player_id]['keeper_cost']
                    print('\t{} - Keeper Cost: Round {}'.format(player_name, keeper_cost))
                    f.write('\t{} - Keeper Cost: Round {}\n'.format(player_name, keeper_cost))

    return


def process_traded_picks(roster_dict, traded_picks):
    """ This is a debug function that I may use in the future. If I decide to split out the traded draft picks from
    the over all keeper information

    Args:
        roster_dict (dict): Dictionary of rosters
        traded_picks (dict): Dictionary of traded_picks
    """
    keeper_dict = dict()
    for week in traded_picks:
        for weekly_traded_pick in traded_picks[week]:
            print('Owner_ID: {}'.format(weekly_traded_pick['owner_id']))
            print('Previous_Owner_ID: {}'.format(weekly_traded_pick['previous_owner_id']))

    for owner in roster_dict:
        keeper_dict[owner] = dict()
        keeper_dict[owner]['owner_id'] = roster_dict[owner]['owner_id']
        nice_print(owner)

        print('Looking for traded_picks for {} with owner_id {}'.format(
            roster_dict[owner],
            roster_dict[owner]['owner_id']
        ))
        for week in traded_picks:
            for weekly_traded_pick in traded_picks[week]:
                if roster_dict[owner]['roster_id'] == weekly_traded_pick['owner_id']:
                    print("Owner_ID: {} has gained a round {} in {}".format(
                        weekly_traded_pick['owner_id'],
                        weekly_traded_pick['round'],
                        weekly_traded_pick['season']
                    ))
                if roster_dict[owner]['roster_id'] == weekly_traded_pick['previous_owner_id']:
                    print("Owner_ID: {} has lost a round {} in {}".format(
                        weekly_traded_pick['previous_owner_id'],
                        weekly_traded_pick['round'],
                        weekly_traded_pick['season']
                    ))


def main_program(username, debug, refresh, position, offline, year, league_name):
    """ Run the main application

    Args:
        username (str): Username of owner in league_name
        debug (bool): Debug argument flag. Print debug output.
        refresh (bool): Refresh argument flag. Refresh player data from Sleeper API
        position (str): Position argument. Get keeper value for given position.
        offline (bool): Offline argument. Run in offline mode.
        year (int): Year of league information to acquire.
        league_name (str): Name of league. Must EXACTLY match the name in sleeper.
    """
    # 2019 was the first year of YAFL 2.0, so there was no kept player list. Load an empty kept_player dictionary
    # TODO This is should be handled by the config file. Maybe a kept variable? Eitherway changing this logic for RUN integration
    # TODO Actually going to make this a check function.
    # first_year from user or config file? Can I get first year from the API? Do I need to get it from the API?
    # if year == first_year:
    #    kept_dict = dict()
    # # Changing this for now. Right now this is hard coded for YAFL and needs to be updated to support multiple leagues
    # if year == 2019:
    #     kept_dict = dict()
    # else:
    #     try:
    #         with open('data_files/{}/kept_players/processed_kept_players.json'.format(year)) as f:
    #             kept_dict = json.load(f)
    #     except Exception as e:
    #         print(e)
    #         assert False, 'Unable to open processed_kept_players.json. Run process_kept_csv.py.'

    if offline:
        # TODO Add a way to get draft_type offline.
        #  Also add way to get first_year offline. Currently getting this in the league function
        # For offline mode we need to get all the files from data_files. If the file does not exist, remind the user
        # to use --refresh to get and store data
        try:
            with open('data_files/{}/player_dict.json'.format(year)) as f:
                player_dict = json.load(f)
        except Exception as e:
            print(e)
            assert False, 'Unable to open data_files/player_dict.json. \n Use --refresh to get data from Sleeper API'

        try:
            with open('data_files/{}/draft_dict.json'.format(year)) as f:
                draft_dict = json.load(f)
        except Exception as e:
            print(e)
            assert False, 'Unable to open data_files/draft_dict.json. \n Use --refresh to get data from Sleeper API'

        try:
            with open('data_files/{}/rosters.json'.format(year)) as f:
                roster_dict = json.load(f)
        except Exception as e:
            print(e)
            assert False, 'Unable to open data_files/rosters.json. \n Use --refresh to get data from Sleeper API'

        try:
            with open('data_files/{}/transactions.json'.format(year)) as f:
                transactions = json.load(f)
        except Exception as e:
            print(e)
            assert False, 'Unable to open data_files/transactions.json. \n Use --refresh to get data from Sleeper API'

        # Not saving trades.json anymore. Might need it later for resetting trade value for yafl cause of the value
        # reset rule which I fear may be a rule we regret in the future like with other complicated rules (player sub)
        # try:
        #     with open('data_files/{}/trades.json'.format(year)) as f:
        #         trades = json.load(f)
        # except Exception as e:
        #     print(e)
        #     assert False, 'Unable to open data_files/trades.json. \n Use --refresh to get data from Sleeper API'

        try:
            with open('data_files/{}/traded_picks.json'.format(year)) as f:
                traded_picks = json.load(f)
        except Exception as e:
            print(e)
            assert False, 'Unable to open data_files/traded_picks.json. \n Use --refresh to get data from Sleeper API'

        try:
            with open('data_files/{}/league_dict.json'.format(year)) as f:
                league_dict = json.load(f)
        except Exception as e:
            print(e)
            assert False, 'Unable to open data_files/league_dict.json. \n Use --refresh to get data from Sleeper API'

        try:
            with open('data_files/{}/draft_api.json'.format(year)) as f:
                draft_api_dict = json.load(f)
        except Exception as e:
            print(e)
            assert False, 'Unable to open data_files/draft_api.json. \n Use --refresh to get data from Sleeper API'

        # If this is the first year of a league, then previous_league_id will be None.
        # There will be no kept_player list for the first year, so load an empty kept_player dictionary.
        previous_league_id = league_dict['previous_league_id']
        if previous_league_id is None:
            kept_dict = dict()
        else:
            try:
                with open('data_files/{}/kept_players/processed_kept_players.json'.format(year)) as f:
                    kept_dict = json.load(f)
            except Exception as e:
                print(e)
                assert False, 'Unable to open processed_kept_players.json. Run process_kept_csv.py.'

        keeper_dict = determine_eligible_keepers(
            roster_dict,
            player_dict,
            draft_dict,
            transactions,
            traded_picks,
            kept_dict
        )
        pretty_print_keepers(keeper_dict, year)

        if position:
            position_keeper(keeper_dict, position)

        return

    # Get the user object to get league info
    user_obj = User(username)

    # Get the league object. Will be used to get draft info, transactions, and rosters.
    league, first_year = get_league_id(user_obj, year, league_name)

    # If this is the first year of a league, there will be no kept_player list. Load an empty kept_player dictionary
    if first_year:
        kept_dict = dict()
    else:
        try:
            with open('data_files/{}/kept_players/processed_kept_players.json'.format(year)) as f:
                kept_dict = json.load(f)
        except Exception as e:
            print(e)
            assert False, 'Unable to open processed_kept_players.json. Run process_kept_csv.py.'

    # Get the username and id
    user_dict = get_users(league)

    # Get a dictionary of all the players
    player_dict = get_players(refresh, year)

    # Get the trade deadline from the league settings
    trade_deadline = get_trade_deadline(league)

    # Get a dictionary of all the drafted players
    draft_type, draft_dict = get_drafted_players(league)

    # Get a dictionary of all the rostered players
    roster_dict = get_rosters(league, user_dict)

    # Get the transactions after the trade deadline
    transactions = get_transactions(league, trade_deadline)

    # Get a list of traded players and dictionary of traded draft picks
    trades, traded_picks = get_trades(league)

    # DEBUG code to process traded_picks
    # process_traded_picks(roster_dict, traded_picks)

    # Get the final keeper list
    keeper_dict = determine_eligible_keepers(
        roster_dict,
        player_dict,
        draft_dict,
        transactions,
        traded_picks,
        kept_dict
    )

    # TODO This is actually broken. I want debug files to output as things are crashing. This is fine if everything is
    # TODO working, but I need to change this to output the debug files right as we are accessing the API.
    # TODO I think I should move this to a function that is called by other functions and pass debug to the functions
    if debug:
        # If debug_files doesn't exist, create the directory
        # if not os.path.isdir('./debug_files'):
        #     try:
        #         os.mkdir('debug_files')
        #     except Exception as e:
        #         print(e)
        #         assert False
        path = Path('./debug_files')
        path.mkdir(parents=True, exist_ok=True)

        # Output everything to a file to figure out what is happening
        with open('debug_files/user_dict.json', 'w') as f:
            f.write('{}'.format(pformat(user_dict)))
        with open('debug_files/draft_dict.json', 'w') as f:
            f.write('{}'.format(pformat(draft_dict)))
        with open('debug_files/rosters.json', 'w') as f:
            f.write('{}'.format(pformat(roster_dict)))
        with open('debug_files/player_dict.json', 'w') as f:
            f.write('{}'.format(pformat(player_dict)))
        with open('debug_files/keeper_dict.json', 'w') as f:
            f.write('{}'.format(pformat(keeper_dict)))
        with open('debug_files/transactions.json', 'w') as f:
            f.write('{}'.format(pformat(transactions)))
        with open('debug_files/trades.json', 'w') as f:
            f.write('{}'.format(pformat(trades)))
        with open('debug_files/traded_picks.json', 'w') as f:
            f.write('{}'.format(pformat(traded_picks)))

    # if refresh:
    #     # If data_files doesn't exist, create the directory
    #     # if not os.path.isdir('./data_files'):
    #     #     try:
    #     #         os.mkdir('data_files')
    #     #     except Exception as e:
    #     #         print(e)
    #     #         assert False
    #
    #     # New way to check for path. Keeping old way in comments for now. Delete it later.
    #     path = Path('./data_files/{}'.format(year))
    #     path.mkdir(parents=True, exist_ok=True)
    #
    #     with open('data_files/{}/user_dict.json'.format(year), 'w') as f:
    #         f.write(json.dumps(user_dict))
    #     with open('data_files/{}/draft_dict.json'.format(year), 'w') as f:
    #         f.write(json.dumps(draft_dict))
    #     with open('data_files/{}/rosters.json'.format(year), 'w') as f:
    #         f.write(json.dumps(roster_dict))
    #     with open('data_files/{}/player_dict.json'.format(year), 'w') as f:
    #         f.write(json.dumps(player_dict))
    #     with open('data_files/{}/keeper_dict.json'.format(year), 'w') as f:
    #         f.write(json.dumps(keeper_dict))
    #     with open('data_files/{}/transactions.json'.format(year), 'w') as f:
    #         f.write(json.dumps(transactions))
    #     with open('data_files/{}/trades.json'.format(year), 'w') as f:
    #         f.write(json.dumps(trades))
    #     with open('data_files/{}/traded_picks.json'.format(year), 'w') as f:
    #         f.write(json.dumps(traded_picks))

    csv_print_keepers(keeper_dict, year)
    pretty_print_keepers(keeper_dict, year)

    if position:
        position_keeper(keeper_dict, position)

    return


def save_draft_information(user):
    """ Save the draft information for the current year of YAFL

    This function might change in the future. I think it's possible to get past draft data, if so then I can get
    draft data from those without the need to save them. It might also be possible to get past draft data from the
    user endpoint.

    Currently this function gets the draft data from YAFL and saves it to a file /saved_drafts/draft_xxxx.json, where
    xxxx is the year.

    Args:
        user (str): Username of a YAFL manager
    """
    # Get the user object to get league info
    user_obj = User(user)

    # Get the league object. Will be used to get draft info.
    league = get_league_id(user_obj)

    season = league.get_league()['season']

    all_drafts = league.get_all_drafts()

    # Sleeper will only have 1 draft, so we can access the first result from the list
    draft_id = all_drafts[0]['draft_id']
    draft = Drafts(draft_id)
    draft_picks = draft.get_all_picks()
    nice_print(draft_picks)

    # Might be able to use draft.get_specific_draft() to get the season for the draft if this function changes in
    # the future
    # specific_picks = draft.get_specific_draft()

    # If saved_drafts doesn't exist, create the directory
    if not os.path.isdir('./saved_drafts'):
        try:
            os.mkdir('saved_drafts')
        except Exception as e:
            print(e)
            assert False

    with open('saved_drafts/draft_{}.json'.format(season), 'w') as f:
        f.write(json.dumps(draft_picks))


if __name__ == '__main__':
    main_help_text = dedent(
        ''' Generates a list of eligible keepers for YAFL 2.0.

        For first time use, run with --refresh. Ex: 'python sleeper_keeper.py chilliah 2019 "YAFL 2.0" --refresh'
        
        Results are saved to final_keepers.txt.

        You must run with a username from YAFL 2.0.
        You must run with a valid year for YAFL 2.0.
        You must run with a valid league name that exactly matches the league name from Sleeper.
        To get new data from the Sleeper API, use the optional argument '--refresh'.
        To print all output to files, use the optional argument '--debug'.
        To run in offline mode, use the optional argument '--offline'.
        To get keeper values for a specific position, use the optional argument '--pos QB'.
            Valid positions are QB, WR, RB, TE, and DEF. Results are saved to position_keepers.txt. '''
    )
    parser = argparse.ArgumentParser(description=main_help_text, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('user', type=str, help='Username of owner in league')
    parser.add_argument('year', type=int, help='Year to pull information from league')
    parser.add_argument('name', type=str, help='Name of league. Must exactly match Sleeper')
    parser.add_argument('--refresh',
                        default=None,
                        action='store_true',
                        help='Get new player data from the Sleeper API'
                        )
    parser.add_argument('--debug',
                        default=None,
                        action='store_true',
                        help='Print everything to file for debug'
                        )
    parser.add_argument('--offline',
                        default=None,
                        action='store_true',
                        help='Run in Offline Mode. Use saved data from previous run.'
                        )
    parser.add_argument('--pos', type=str, default=None, help='Get keeper values for specified position')
    # TODO This can probably be removed. I can get drafts from previous years by just calling the year in the API.
    parser.add_argument('--store_draft', default=None, action='store_true', help='Store draft for RUN.')

    args = parser.parse_args()
    user = args.user
    year = args.year
    league_name = args.name
    refresh = args.refresh
    debug = args.debug
    position = args.pos
    offline = args.offline
    store_draft = args.store_draft

    if store_draft:
        save_draft_information(user)
        sys.exit(0)

    main_program(user, debug, refresh, position, offline, year, league_name)

    sys.exit(0)
