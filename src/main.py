"""`main` is the top level module for Flask application."""

import datetime

from flask import Flask, request
from flask import render_template

from google.appengine.ext import db
import flask


class User(db.Model):
    email = db.EmailProperty(required=True)
    places = db.ListProperty(db.Link)
    subscribed_at = db.DateTimeProperty()


class Place(db.Model):
    title = db.StringProperty()
    info = db.TextProperty(indexed=False)
    added_at = db.DateTimeProperty(auto_now_add=True)


class UserPlace(db.Model):
    user = db.ReferenceProperty(User, collection_name='user_memberships')
    place = db.ReferenceProperty(Place, collection_name='place_memberships')


class Update(db.Model):
    place = db.ReferenceProperty(Place)
    link = db.LinkProperty()
    info = db.TextProperty(indexed=False)
    added_at = db.DateTimeProperty(auto_now_add=True)


class PlaceLink(db.Model):
    place = db.ReferenceProperty(Place)
    link = db.LinkProperty()
    added_at = db.DateTimeProperty(auto_now_add=True)


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


@app.route('/places', methods=['GET', 'POST'])
def places(name=None):

    if request.method == 'POST':
        # link = request.form.get('place{}'.format(i), None)
        # link = request.json('link', None)
        link = request.json['link']
        info = request.json['link']

        if link:
            qs = Place.all()
            for place in qs:
                if place.link == link:
                    response = {
                        'status': 1,
                        'message': "This place already exists!"
                    }
                    print response
                    return flask.jsonify(response)
            else:
                p = Place()
                p.link = link
                p.info = info
                p.put()

                response = {
                    'status': 0,
                    'message': "Ok!"
                }
                print response
                return flask.jsonify(response)
    else:
        qs = Place.all()
        qs.order('added_at')

        # response = "<ul>"
        # for place in qs:
        #     # response += "<strong>{0}</strong><br/>".format(place.link)
        #     response += "<li><strong>{0}</strong></li>".format(place.link)
        # response += "</ul>"
        # return response

        return render_template('places.html', places=qs)


@app.route('/about')
def about(name=None):
    """Return about.html. """
    return render_template('about.html')


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
