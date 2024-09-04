import os
from flask import Flask, send_from_directory, send_file

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/download')
def download():
    return send_file('questionnaire-to-download.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')