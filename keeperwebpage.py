from flask import Flask, render_template
from sleeper_keeper import main_program

app = Flask(__name__)


@app.route('/')
def main():
    """ Base URL route used only for debugging purposes and to make sure that the webserver is running """

    main_program('chilliah', False, False, None, False)

    text = open('final_keepers.txt', 'r+')
    content = text.read()
    text.close()
    return render_template('content.html', text=content)


@app.route('/debug')
def debug():
    """ Base URL route used only for debugging purposes and to make sure that the webserver is running """

    main_program('chilliah', False, False, None, False)

    text = open('final_keepers.txt', 'r+')
    content = text.read()
    text.close()
    return render_template('content.html', text=content)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
