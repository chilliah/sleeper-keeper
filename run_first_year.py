import pandas as pd


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


if __name__ == "__main__":
    keeper_csv_to_table()
