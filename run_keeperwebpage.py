from flask import Flask, render_template, send_file
from pprint import pformat
from sleeper_keeper import main_application, load_config, League, Debug


# TODO 1/13/22 Webpage rewrite:
#   Break the webpage into 2 different sites. 1 for YAFL and 1 for RUN.
#   Considering 2 separate config files, cause it might make it easier to update while the program is running.
#   YAFL Links
#       Home, Year, Traded Picks, Kept Players, Full, Filters, Refresh, CSV

# Base class for YAFL league, just so I don't have to load it as often.
run_league_base, run_debug_base = load_config('run_config.ini')

app = Flask(__name__)


@app.route('/')
def main_endpoint():
    """ Base URL route

    Display the current year saved keepers. This is also the Home button in the banner.

    Return:
        Returns the rendered templated of the keeper function
    """
    # Load the base yafl objects. These are the current objects.
    run_league_current = run_league_base
    # run_debug_current = run_debug_base  # Don't need right now

    year = run_league_current.current_year
    print(year)
    league_id = run_league_current.current_id
    print(league_id)

    # Location of the saved filtered keeper list
    keeper_filtered_table_location = f'data_files/{year}/{league_id}/keeper_table_filtered.html'

    text = open(keeper_filtered_table_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The RUN League Eligible Keepers for {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('run_table_content.html', table_header=table_header_str, table=content)


@app.route('/<year>')
def year_endpoint(year):
    """ Year route to choose keeper results for a given year. Loads the saved filtered keeper list for the year

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    run_year_endpoint_league = run_league_base
    run_year_endpoint_debug = run_debug_base

    # Load the year to id dictionary
    eligible_years = run_year_endpoint_league.eligible_years
    current_year = run_year_endpoint_league.current_year
    year_to_id = run_year_endpoint_league.year_to_id

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

    # Catch for 2020 run keepers which will not be generated from sleeper API
    if int(year) == 2020:
        run_2020_keepers_file_location = f'data_files/{year}/run_2020_keepers/run_keepers_2020.html'

        text = open(run_2020_keepers_file_location, 'r+')
        content = text.read()
        text.close()

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('run_table_content.html', table=content)

    # Location of the saved filtered keeper list
    keeper_filtered_table_location = f'data_files/{year}/{league_id}/keeper_table_filtered.html'

    # print(keeper_filtered_table_location)  # Debug statement

    text = open(keeper_filtered_table_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The RUN League Eligible Keepers for {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('run_table_content.html', table_header=table_header_str, table=content)


@app.route('/kept/<year>')
def kept_endpoint(year):
    """ Load the kept players for each year.

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    run_kept_endpoint_league = run_league_base
    run_kept_endpoint_debug = run_debug_base

    # Load the year to id dictionary
    eligible_years = run_kept_endpoint_league.eligible_years
    first_year = run_kept_endpoint_league.first_year
    current_year = run_kept_endpoint_league.current_year
    year_to_id = run_kept_endpoint_league.year_to_id

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
        run_2020_keepers_file_location = f'data_files/{year}/run_2020_keepers/run_keepers_2020.html'
        text = open(run_2020_keepers_file_location, 'r+')
        content = text.read()
        text.close()
        return render_template('run_content.html', text=content)

    # Location of the saved filtered keeper list
    kept_players_filter_table_location = f'data_files/{year}/{league_id}/kept_players/kept_players_table_filtered.html'

    # print(keeper_filtered_table_location)  # Debug statement

    text = open(kept_players_filter_table_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The RUN League Kept Players for {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('run_table_content.html', table_header=table_header_str, table=content)


@app.route('/full/<year>')
def full_endpoint(year):
    """ Full Endpoint. Will display all rostered players and their keeper status and cost.

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    run_full_endpoint_league = run_league_base
    run_full_endpoint_debug = run_debug_base

    # Load the year to id dictionary
    eligible_years = run_full_endpoint_league.eligible_years
    first_year = run_full_endpoint_league.first_year
    current_year = run_full_endpoint_league.current_year
    year_to_id = run_full_endpoint_league.year_to_id

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

    # Catch for 2020 run keepers which will not be generated from sleeper API
    if int(year) == 2020:
        run_2020_keepers_file_location = f'data_files/{year}/run_2020_keepers/run_keepers_2020.html'

        text = open(run_2020_keepers_file_location, 'r+')
        content = text.read()
        text.close()

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('run_table_content.html', table=content)

    # Location of the saved filtered keeper list
    keeper_table_human_full_location = f'data_files/{year}/{league_id}/keeper_human_table.html'
    # print(keeper_filtered_table_location)  # Debug statement

    text = open(keeper_table_human_full_location, 'r+')
    content = text.read()
    text.close()

    table_header_str = f'The RUN League Eligible Keepers for {year}'

    # Consider renaming this to run_tablecontent.html to allow for having different nav bars
    return render_template('run_table_content.html', table_header=table_header_str, table=content)


@app.route('/csv/<year>')
def csv_endpoint(year):
    """ CSV endpoint for scope creep Meat Wizard

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    run_csv_endpoint_league = run_league_base
    run_csv_endpoint_debug = run_debug_base

    # Load the year to id dictionary
    eligible_years = run_csv_endpoint_league.eligible_years
    first_year = run_csv_endpoint_league.first_year
    current_year = run_csv_endpoint_league.current_year
    year_to_id = run_csv_endpoint_league.year_to_id

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

    # Catch for 2020 run keepers which will not be generated from sleeper API
    if int(year) == 2020:
        run_2020_keepers_file_location = f'data_files/{year}/run_2020_keepers/run_keepers_2020.html'

        text = open(run_2020_keepers_file_location, 'r+')
        content = text.read()
        text.close()

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('run_table_content.html', table=content)

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
    run_refresh_league = run_league_base
    run_refresh_debug = run_debug_base

    # Eligible refresh types
    eligible_refresh_types = ['quick', 'full', 'players']

    if refresh_type not in eligible_refresh_types:
        refresh_type = 'quick'

    # If refresh type is quick, then o
    if refresh_type == 'quick':
        year = run_refresh_league.current_year
        league_id = run_refresh_league.current_id

        # Set refresh to True, cause we want to update the transactions.
        run_refresh_debug.refresh = True

        # Run the program.
        main_application(run_refresh_debug, run_refresh_league)

        keeper_table_human_full_location = f'data_files/{year}/{league_id}/keeper_human_table.html'

        text = open(keeper_table_human_full_location, 'r+')
        content = text.read()
        text.close()
        table_header_str = f'The RUN League Eligible Keepers for {year}'

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('run_table_content.html', table_header=table_header_str, table=content)
    elif refresh_type == 'full':
        eligible_years = run_refresh_league.eligible_years
        year_to_id = run_refresh_league.year_to_id
        for eligible_year in eligible_years:
            if eligible_year == 2020:
                continue

            year = eligible_year
            league_id = year_to_id[year]

            # Set refresh to True, cause we want to update the transactions.
            run_refresh_debug.refresh = True

            print(f'Refreshing all leagues. Will take a long time. {eligible_years} Refreshing {len(eligible_years)}')

            main_application(run_refresh_debug, run_refresh_league)

        # I should be the only one hitting this endpoint, so I will display the large, unfiltered keeper_table.
        keeper_table_location = f'data_files/{year}/{league_id}/keeper_table.html'

        text = open(keeper_table_location, 'r+')
        content = text.read()
        text.close()
        table_header_str = f'The RUN League Eligible Keepers for {year}'

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('run_table_content.html', table_header=table_header_str, table=content)
    elif refresh_type == 'players':
        year = run_refresh_league.current_year
        league_id = run_refresh_league.current_id

        # Set refresh to False, cause we want to update the transactions.
        # Only get the players
        run_refresh_debug.refresh = False
        run_refresh_debug.player_refresh = True

        main_application(run_refresh_debug, run_refresh_league)

        # I should be the only one hitting this endpoint, so I will display the large, unfiltered keeper_table.
        keeper_table_location = f'data_files/{year}/{league_id}/keeper_table.html'

        text = open(keeper_table_location, 'r+')
        content = text.read()
        text.close()

        table_header_str = f'The RUN League Eligible Keepers for {year}'

        # Consider renaming this to run_tablecontent.html to allow for having different nav bars
        return render_template('run_table_content.html', table_header=table_header_str, table=content)


if __name__ == "__main__":
    # Debug for test machine
    app.run(debug=True)
    #app.run(host='0.0.0.0')
