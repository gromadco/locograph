"""`main` is the top level module for your Flask application."""

import datetime

from flask import Flask, request
from flask import render_template

from google.appengine.ext import db


class User(db.Model):
    email = db.EmailProperty(required=True)
    places = db.ListProperty(db.Link)
    subscribed_at = db.DateTimeProperty()


app = Flask(__name__)

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/')
def hello(name=None):
    """Return index.html. """
    return render_template('index.html')


@app.route('/subscribe', methods=['POST'])
def subscribe():

    links = []
    for i in range(1, 5):
        l = request.form.get('place{}'.format(i), None)
        if l:
            links.append(db.Link(l))

    u = User(
        email=request.form['email'],
        places=links)
    u.suscribed_at = datetime.datetime.now()
    u.put()

    return "Thank you for subscribing!"


@app.route('/users')
def users():

    q = User.all()
    res = ""
    for user in q:
        res += "<strong>{}</strong><br/>".format(user.email)
        res += "<ul>"
        for p in user.places:
            res += '<li><a href="{}">{}</a></li>'.format(p.encode('utf8'), p.encode('utf8'))
        res += "</ul><br/>"

    return res


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
