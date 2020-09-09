from flask import Flask, render_template, send_file
from pprint import pformat
from sleeper_keeper import main_program

app = Flask(__name__)

# Define eligible years as global list
eligible_years = [2019, 2020]
current_year = 2020


@app.route('/')
def default_main():
    """ Base URL route used only for debugging purposes and to make sure that the webserver is running """
    year = current_year

    main_program('chilliah', False, False, None, True, year)

    text = open('data_files/{}/final_keepers.txt'.format(year), 'r+')
    content = text.read()
    text.close()
    return render_template('content.html', text=content)


@app.route('/<year>')
def main(year):
    """ Year route to choose keeper results for a given year

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    # If year is not in eligible years list, then use the current year.
    if year.isnumeric():
        year = int(year)
    if year not in eligible_years:
        year = current_year

    main_program('chilliah', False, False, None, False, year)

    text = open('data_files/{}/final_keepers.txt'.format(year), 'r+')
    content = text.read()
    text.close()
    return render_template('content.html', text=content)


@app.route('/csv/<year>')
def download_csv(year):
    """ csv route to download keeper results as a csv for Meat Wizard

    Args:
        year(int): Year to get keeper results for.
    Returns:
        Rendered content.html template with keeper results
    """
    if year.isnumeric():
        year = int(year)
    if year not in eligible_years:
        return 'Year is not in {}'.format(pformat(eligible_years))
    path = 'data_files/{}/final_keepers.csv'.format(year)
    print(path)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    # Debug for test machine
    # app.run(debug=True)
    app.run(host='0.0.0.0')
