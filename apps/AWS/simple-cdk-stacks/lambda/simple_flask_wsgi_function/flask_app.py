import os
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def hello():
    return 'Hello, World!'

from flask import send_file
@app.route('/download')
def download():
    return send_file('file-to-download.txt', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')