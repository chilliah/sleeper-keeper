from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def main():
    """ Generate First RUN Keeper Webpage
    """
    #text = open('data_files/run_files/kept_table.html', 'r+')
    text = open('data_files/2021/kept_table.html', 'r+')
    content = text.read()
    text.close()

    return render_template('tablecontent.html', table=content)


@app.route('/sneakypeeky')
def sneaky():
    """ Generate First RUN Keeper Webpage
    """
    #text = open('data_files/run_files/kept_table.html', 'r+')
    text = open('data_files/2021/kept_table_full.html', 'r+')
    content = text.read()
    text.close()

    return render_template('tablecontent.html', table=content)


@app.route('/pickypeeky')
def draftpicky():
    """ Generate First RUN Keeper Webpage
    """
    #text = open('data_files/run_files/kept_table.html', 'r+')
    #text = open('data_files/2021/kept_table_full.html', 'r+')
    text = open('data_files/2021/picks_table_full.html', 'r+')
    content = text.read()
    text.close()

    return render_template('tablecontent.html', table=content)


if __name__ == "__main__":
    # Debug for test machine
    app.run(debug=True)
    #app.run(host='0.0.0.0')
