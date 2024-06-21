import json

import awsgi

from flask import (
    Flask,
    jsonify,
    render_template,
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("main_page.html")

def handler(event, context):
    print(event)
    print(json.dumps(event))
    return awsgi.response(app, event, context)