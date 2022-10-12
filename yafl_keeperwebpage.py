from flask import Flask, render_template, send_file
from pprint import pformat
from sleeper_keeper import main_application, load_config, League, Debug


# TODO 1/13/22 Webpage rewrite:
#   Break the webpage into 2 different sites. 1 for YAFL and 1 for RUN.
#   Considering 2 separate config files, cause it might make it easier to update while the program is running.
#   YAFL Links
#       Home, Year, Traded Picks, Kept Players, Full, Filters, Refresh, CSV

# Base class for YAFL league, just so I don't have to load it as often.
yafl_league_base, yafl_debug_base = load_config('yafl_config.ini')

app = Flask(__name__)


@app.route('/')
def main_endpoint():
    """ Base URL route

    Display the current year saved keepers. This is also the Home button in the banner.

    Return:
        Returns the rendered templated of the keeper function
    """
    # Load the base yafl objects. These are the current objects.
    yafl_league_current = yafl_league_base
    # yafl_debug_current = yafl_debug_base  # Don't need right now

    year = yafl_league_current.current_year
    print(year)
    league_id = yafl_league_current.current_id
    print(league_id)

    # Location of the saved filtered keeper list
    keeper_filtered_table_location = f'data_files/{year}/{league_id}/keeper_table_filtered.html'

    text = open(keeper_filtered_table_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The YAFL 2.0 Eligible Keepers for {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('yafl_table_content.html', table_header=table_header_str, table=content)


@app.route('/<year>')
def year_endpoint(year):
    """ Year route to choose keeper results for a given year. Loads the saved filtered keeper list for the year

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    yafl_year_endpoint_league = yafl_league_base
    yafl_year_endpoint_debug = yafl_debug_base

    # Load the year to id dictionary
    eligible_years = yafl_year_endpoint_league.eligible_years
    current_year = yafl_year_endpoint_league.current_year
    year_to_id = yafl_year_endpoint_league.year_to_id

    # print(eligible_years)  # Debug statement
    # print(f'{year} from the endpoint')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    # If year is not a numeric, then use the current year.
    if not year.isnumeric():
        year = current_year

    # print(f'{year} after the numeric check. {type(year)}')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    if int(year) not in eligible_years:
        print(f'{year} not in {eligible_years}')
        year = current_year

    # Set the league_id based on the year from the endpoint
    league_id = year_to_id[int(year)]

    # Location of the saved filtered keeper list
    keeper_filtered_table_location = f'data_files/{year}/{league_id}/keeper_table_filtered.html'

    # print(keeper_filtered_table_location)  # Debug statement

    text = open(keeper_filtered_table_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The YAFL 2.0 Eligible Keepers for {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('yafl_table_content.html', table_header=table_header_str, table=content)


@app.route('/picks/<year>')
def picks_endpoint(year):
    """ Year route to choose keeper results for a given year. Loads the saved filtered keeper list for the year

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    yafl_picks_endpoint_league = yafl_league_base
    yafl_picks_endpoint_debug = yafl_debug_base

    # Load the year to id dictionary
    eligible_years = yafl_picks_endpoint_league.eligible_years
    current_year = yafl_picks_endpoint_league.current_year
    year_to_id = yafl_picks_endpoint_league.year_to_id

    # print(eligible_years)  # Debug statement
    # print(f'{year} from the endpoint')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    # If year is not a numeric, then use the current year.
    if not year.isnumeric():
        year = current_year

    # print(f'{year} after the numeric check. {type(year)}')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    if int(year) not in eligible_years:
        print(f'{year} not in {eligible_years}')
        year = current_year

    # Set the league_id based on the year from the endpoint
    league_id = year_to_id[int(year)]

    # Location of the saved filtered keeper list
    traded_picks_filtered_table_location = f'data_files/{year}/{league_id}/traded_picks_table_filtered.html'

    # print(keeper_filtered_table_location)  # Debug statement

    text = open(traded_picks_filtered_table_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The YAFL 2.0 Traded Draft Picks for {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('yafl_table_content.html', table_header=table_header_str, table=content)


@app.route('/kept/<year>')
def kept_endpoint(year):
    """ Load the kept players for each year.

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    yafl_kept_endpoint_league = yafl_league_base
    yafl_kept_endpoint_debug = yafl_debug_base

    # Load the year to id dictionary
    eligible_years = yafl_kept_endpoint_league.eligible_years
    first_year = yafl_kept_endpoint_league.first_year
    current_year = yafl_kept_endpoint_league.current_year
    year_to_id = yafl_kept_endpoint_league.year_to_id

    # print(eligible_years)  # Debug statement
    # print(f'{year} from the endpoint')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    # If year is not a numeric, then use the current year.
    if not year.isnumeric():
        year = current_year

    # print(f'{year} after the numeric check. {type(year)}')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    if int(year) not in eligible_years:
        print(f'{year} not in {eligible_years}')
        year = current_year

    # Set the league_id based on the year from the endpoint
    league_id = year_to_id[int(year)]

    # Add a catch for the first year meme
    if int(year) == first_year:
        first_year_meme = f'data_files/{year}/{league_id}/kept_players/kept_players_meme_2019.txt'
        text = open(first_year_meme, 'r+')
        content = text.read()
        text.close()
        return render_template('yafl_content.html', text=content)

    # Location of the saved filtered keeper list
    kept_players_filter_table_location = f'data_files/{year}/{league_id}/kept_players/kept_players_table_filtered.html'

    # print(keeper_filtered_table_location)  # Debug statement

    text = open(kept_players_filter_table_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The YAFL 2.0 Kept Players {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('yafl_table_content.html', table_header=table_header_str, table=content)


@app.route('/full/<year>')
def full_endpoint(year):
    """ Full Endpoint. Will display all rostered players and their keeper status and cost.

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    yafl_full_endpoint_league = yafl_league_base
    yafl_full_endpoint_debug = yafl_debug_base

    # Load the year to id dictionary
    eligible_years = yafl_full_endpoint_league.eligible_years
    first_year = yafl_full_endpoint_league.first_year
    current_year = yafl_full_endpoint_league.current_year
    year_to_id = yafl_full_endpoint_league.year_to_id

    # print(eligible_years)  # Debug statement
    # print(f'{year} from the endpoint')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    # If year is not a numeric, then use the current year.
    if not year.isnumeric():
        year = current_year

    # print(f'{year} after the numeric check. {type(year)}')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    if int(year) not in eligible_years:
        print(f'{year} not in {eligible_years}')
        year = current_year

    # Set the league_id based on the year from the endpoint
    league_id = year_to_id[int(year)]

    # Location of the saved filtered keeper list
    keeper_table_human_full_location = f'data_files/{year}/{league_id}/keeper_human_table.html'
    # print(keeper_filtered_table_location)  # Debug statement

    text = open(keeper_table_human_full_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The YAFL 2.0 Eligible Keepers for {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('yafl_table_content.html', table_header=table_header_str, table=content)


@app.route('/csv/<year>')
def csv_endpoint(year):
    """ CSV endpoint for scope creep Meat Wizard

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    yafl_csv_endpoint_league = yafl_league_base
    yafl_csv_endpoint_debug = yafl_debug_base

    # Load the year to id dictionary
    eligible_years = yafl_csv_endpoint_league.eligible_years
    first_year = yafl_csv_endpoint_league.first_year
    current_year = yafl_csv_endpoint_league.current_year
    year_to_id = yafl_csv_endpoint_league.year_to_id

    # print(eligible_years)  # Debug statement
    # print(f'{year} from the endpoint')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    # If year is not a numeric, then use the current year.
    if not year.isnumeric():
        year = current_year

    # print(f'{year} after the numeric check. {type(year)}')  # Debug statement

    # If year is not in eligible years list, then use the current year.
    if int(year) not in eligible_years:
        print(f'{year} not in {eligible_years}')
        year = current_year

    # Set the league_id based on the year from the endpoint
    league_id = year_to_id[int(year)]

    # Location of the saved filtered keeper list
    # TODO Rename the keep csv to include league name and year
    keeper_table_csv = f'data_files/{year}/{league_id}/keeper_table.csv'

    return send_file(keeper_table_csv, as_attachment=True)


@app.route('/refresh/<refresh_type>')
def refresh_endpoint(refresh_type):
    """ Refresh endpoint. Based on refresh_type refresh different version of the site.

    Args:
        refresh_type(str): Type of refresh.
    Returns:
        Rendered content.html template with keeper results
    """
    yafl_refresh_league = yafl_league_base
    yafl_refresh_debug = yafl_debug_base

    # Eligible refresh types
    eligible_refresh_types = ['quick', 'full', 'players']

    if refresh_type not in eligible_refresh_types:
        refresh_type = 'quick'

    # If refresh type is quick, then o
    if refresh_type == 'quick':
        year = yafl_refresh_league.current_year
        league_id = yafl_refresh_league.current_id

        # Set refresh to True, cause we want to update the transactions.
        yafl_refresh_debug.refresh = True

        # Run the program.
        main_application(yafl_refresh_debug, yafl_refresh_league)

        keeper_table_human_full_location = f'data_files/{year}/{league_id}/keeper_human_table.html'

        text = open(keeper_table_human_full_location, 'r+')
        content = text.read()
        text.close()

        table_header_str = f'The YAFL 2.0 Eligible Keepers for {year}'

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('yafl_table_content.html', table_header=table_header_str, table=content)
    elif refresh_type == 'full':
        eligible_years = yafl_refresh_league.eligible_years
        year_to_id = yafl_refresh_league.year_to_id
        for eligible_year in eligible_years:
            year = eligible_year
            league_id = year_to_id[year]

            # Set refresh to True, cause we want to update the transactions.
            yafl_refresh_debug.refresh = True

            print(f'Refreshing all leagues. Will take a long time. {eligible_years} Refreshing {len(eligible_years)}')

            main_application(yafl_refresh_debug, yafl_refresh_league)

        # I should be the only one hitting this endpoint, so I will display the large, unfiltered keeper_table.
        keeper_table_location = f'data_files/{year}/{league_id}/keeper_table.html'

        text = open(keeper_table_location, 'r+')
        content = text.read()
        text.close()

        table_header_str = f'The YAFL 2.0 Eligible Keepers for {year}'

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('yafl_table_content.html', table_header=table_header_str, table=content)
    elif refresh_type == 'players':
        year = yafl_refresh_league.current_year
        league_id = yafl_refresh_league.current_id

        # Set refresh to False, cause we want to update the transactions.
        # Only get the players
        yafl_refresh_debug.refresh = False
        yafl_refresh_debug.player_refresh = True

        main_application(yafl_refresh_debug, yafl_refresh_league)

        # I should be the only one hitting this endpoint, so I will display the large, unfiltered keeper_table.
        keeper_table_location = f'data_files/{year}/{league_id}/keeper_table.html'

        text = open(keeper_table_location, 'r+')
        content = text.read()
        text.close()

        table_header_str = f'The YAFL 2.0 Eligible Keepers for {year}'

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('yafl_table_content.html', table_header=table_header_str, table=content)


if __name__ == "__main__":
    # Debug for test machine
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=80)
