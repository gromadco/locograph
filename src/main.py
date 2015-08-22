"""`main` is the top level module for Flask application."""

import datetime

from flask import Flask, request
from flask import render_template

from google.appengine.ext import db


class User(db.Model):
    email = db.EmailProperty(required=True)
    places = db.ListProperty(db.Link)
    subscribed_at = db.DateTimeProperty(auto_now_add=True)

    def __repr__(self):
        return '< User = %s >' % (self.email)


class Place(db.Model):
    title = db.StringProperty()
    info = db.TextProperty(indexed=False)
    added_at = db.DateTimeProperty(auto_now_add=True)

    def __repr__(self):
        return '< Place = %s >' % (self.title)


class UserPlace(db.Model):
    user = db.ReferenceProperty(User, required=True, collection_name='user_memberships')
    place = db.ReferenceProperty(Place, required=True, collection_name='place_memberships')

    def __repr__(self):
        return '< User = %s, Place = %s >' % (self.user, self.place)


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


# @app.route('/users_and_places')
# def users():
#
#     q = User.all()
#     res = ""
#     for x in q:
#         res += "<strong>{}</strong><br/>".format(x.user_memberships.order('-place')[0])
#         res += "<strong>{}</strong><br/>".format(x.place.title)
#         res += "<ul>"
#         res += "</ul><br/>"
#
#     return res


@app.route('/places', methods=['GET', 'POST'])
def places(name=None):

    if request.method == 'POST':
        print request.form
        title = request.form.get('place_title', '')
        info = request.form.get('place_info', '')
        if title:
            p = Place()
            p.title = title
            p.info = info
            p.put()

    # for GET and POST

    qs = Place.all()
    qs.order('added_at')

    return render_template('places.html', places=qs)


@app.route('/p/<int:place_id>', methods=['GET', 'POST'])
def place_page(place_id=None):

    if request.method == 'POST':
        print request.form

        email = request.form.get('email', '')
        print email
        if email not in [u.email for u in User.all()]:
            u = User(
                email=email,
                suscribed_at=datetime.datetime.now())
            u.put()
            print "email {0} was added".format(u.email)
        else:
            # users = User.all()

            # user = User.gql("WHERE email = {0}".format(email)).get()
            u = User.gql("WHERE email = '{0}'".format(email)).get()
            print "email {0} already exists".format(u.email)

            # u.filter("email =", email)
            # result = u.get()

            # u = User.query(User.email == email).get()

            # for user in users:
            #     if user.email == email:
            #         u = user

        print u
        p = Place.get_by_id(place_id)
        print p

        up = UserPlace(
            user=u,
            place=p
        )
        up.put()

    p = Place.get_by_id(place_id)
    print p.place_memberships.order('-user')[0]
    up = UserPlace.all()

    subscribers = []
    for x in up:
        print x
        if x.place == p:
            print(x.user)
            subscribers.append(x.user.email)

    return render_template('place.html', place=p, subscribers=subscribers)


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
