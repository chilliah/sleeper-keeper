import json
import requests
from pprint import pformat
from sleeper_wrapper import League, User, Stats, Players, Drafts


def nice_print(args):
    print('{}'.format(pformat(args)))

def get_league_id(user):
    """ Get the league object from a User object

    Get all the leagues of the user. Find the league id for YAFL 2.0. Return the League obj for YAFL 2.0.

    Args:
        user (obj): User object from sleeper_wrapper_api

    Returns:
        league (obj): League object from sleeper_wrapper_api
    """
    all_leagues = user.get_all_leagues('nfl', 2019)

    for league_info in all_leagues:
        # print('{}'.format(pformat(league['league_id'])))
        if league_info['name'] == 'YAFL 2.0':
            league_id = league_info['league_id']
        else:
            print('User: {} is not part of YAFL 2.0. Exiting...'.format(user.get_username()))
            continue

    league = League(league_id)
    return league

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
        drafted_players (dict): Dictionary of drafted players
    """
    all_drafts = league.get_all_drafts()

    # Sleeper will only have 1 draft, so we can access the first result from the list
    draft_id = all_drafts[0]['draft_id']
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
        round = pick['round']

        drafted_players[player_id] = dict()
        drafted_players[player_id]['full_name'] = full_name
        drafted_players[player_id]['keeper'] = keeper
        drafted_players[player_id]['pick_number'] = pick_number
        drafted_players[player_id]['team_id'] = team_id
        drafted_players[player_id]['round'] = round

    print('{}'.format(pformat(drafted_players)))
    return drafted_players


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
    return user_to_ids


def get_players():
    """ Get all the players from Sleeper

    Use the player obj from the Sleeper API and get all the players from Sleeper. The relevant information for a
    player is stored in the player_dict, which has the following structure:

    {player_key: {'player_name': player name, 'position': position}}

    Returns:
        player_dict (dict): Dictionary of all the players
    """
    print('Getting all players from Sleeper API...')
    # TODO: This takes a while. Comment out for now and remember to put an option to not always grab this from the
    #  sleeper API.
    # players = Players().get_all_players()

    # with open('data_files/dump_players.json', 'w') as f:
    #    f.write(json.dumps(players))

    with open('data_files/dump_players.json') as f:
        data = json.load(f)

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

    return player_dict


def get_transactions(league, trade_deadline):
    """ Go through the transactions and get dropped players after the trade deadline

    Go through all the transactions after the trade deadline and get the dropped players. Add the dropped players
    to the drop_list. The sleeper API breaks transactions up per week, so we have to get the transactions for each
    week after the trade deadline until the last week of the season.

    Args:
        league (obj): Sleeper API league object
        trade_deadline (int): Trade deadline for YAFL

    Returns:
        drop_list (list): List of dropped players
    """
    # Setting trade deadline to week 2 for now
    # TODO: Remove
    trade_deadline = 2
    # Add 1 to the trade deadline. This will be the first week to seach for drops. If a player is dropped after
    # that week, then the player is no longer eligible to be kept.
    week = trade_deadline + 1

    # drop_dict = dict()
    transactions_dict = dict()
    transactions_dict['drops'] = list()
    transactions_dict['adds'] = list()

    # Get the transactions from every week after the trade deadline until the last week of the season, which is 16
    # Any player dropped after the trade deadline is not eligible to be kept.
    # TODO: Change this to 16
    while week != 7:
        # TODO: Transactions are store by week
        transactions = league.get_transactions(week)

        for transaction in transactions:
            # Sleeper API will show the failed transactions also. We only want to process the successful transactions
            if transaction['status'] == 'complete':
                nice_print(transaction)
                if transaction['drops']:
                    player_ids = transaction['drops'].keys()
                    for player_id in player_ids:
                        print('Dropped player: {}'.format(player_id))
                        #drop_list.append(player_id)
                        transactions_dict['drops'].append(player_id)
                if transaction['adds']:
                    player_ids = transaction['adds'].keys()
                    for player_id in player_ids:
                        print('Added player: {}'.format(player_id))
                        # add_list.append(player_id)
                        transactions_dict['adds'].append(player_id)
        week = week + 1

    nice_print(transactions_dict)

    return transactions_dict


def determine_eligible_keepers(roster_dict, player_dict, draft_dict, transactions_dict):
    """

    Args:
        roster_dict (dict): Dictionary of rostered players
        player_dict (dict): Dictionary of all the players in Sleeper
        draft_dict (dict): Dictionary of all drafted players
        transactions_dict (dict): Dictionary of all the transactions after the trade deadline

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
            else:
                keeper_dict[owner][player_id]['drafted'] = False
    nice_print(keeper_dict)

    return keeper_dict


if __name__ == '__main__':

    # Get the user object to get league info
    user_obj = User('chilliah')

    # Get the league object. Will be used to get draft info, transactions, and rosters.
    league = get_league_id(user_obj)

    # Get the username and id
    user_dict = get_users(league)

    # Get a dictionary of all the players
    player_dict = get_players()

    # Get the trade deadline from the league settings
    trade_deadline = get_trade_deadline(league)

    # Get a dictionary of all the drafted players
    draft_dict = get_drafted_players(league)

    # Get a dictionary of all the rostered players
    roster_dict = get_rosters(league, user_dict)

    # Get the transactions after the trade deadline
    transactions = get_transactions(league, trade_deadline)

    # Get the final keeper list
    keeper_dict = determine_eligible_keepers(roster_dict, player_dict, draft_dict, transactions)





    # Output everything to a file to figure out what is happening
    with open('user_dict.json', 'w') as f:
        f.write('{}'.format(pformat(user_dict)))
    with open('draft_dict.json', 'w') as f:
        f.write('{}'.format(pformat(draft_dict)))
    with open('rosters.json', 'w') as f:
        f.write('{}'.format(pformat(roster_dict)))
    with open('player_dict.json', 'w') as f:
        f.write('{}'.format(pformat(player_dict)))
    with open('keeper_dict.json', 'w') as f:
        f.write('{}'.format(pformat(keeper_dict)))
    with open('transactions.json', 'w') as f:
        f.write('{}'.format(pformat(transactions)))

    print(trade_deadline)

    #nice_print(user_dict)

    # user_dict = league.map_users_to_team_name(league.get_users())

    # print('{}'.format(pformat(user_dict)))

    # draft = league.get_all_drafts()
    #
    # print('{}'.format(pformat(draft)))
    #
    # users = league.get_users()
    # #
    # print('{}'.format(pformat(users)))
    #
    # users_dict = league.map_users_to_team_name(users)
    #
    # print('{}'.format(pformat(users_dict)))
    #
    # # users_dict = dict()
    #
    # # for user in users:
    # #     user_id = user['user_id']
    # #     user_name = user['display_name']
    # #
    # #     users_dict[user_id] = user_name
    # #
    # # print('{}'.format(pformat(users_dict)))
    #
    # rosters = league.get_rosters()
    #
    # roster_map = league.map_rosterid_to_ownerid(rosters)
    #
    # print('{}'.format(pformat(roster_map)))
    #
    # # drafts = league.get_all_drafts()
    # #
    # # print('{}'.format(pformat(drafts)))
    # #
    # # players = Players()
    # #
    # # print('{}'.format(pformat(players.get_all_players())))
    #
    # # rosters = league.get_rosters()
    #
    # # print('{}'.format(pformat(rosters)))