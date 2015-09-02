"""`main` is the top level module for Flask application."""

import datetime

from flask import Flask, request
from flask import render_template

from models import (
    Place, Update, User, UserPlace)


app = Flask(__name__)

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/')
def main(name=None):
    """Return index.html. """
    return render_template('index.html')


@app.route('/subscribe', methods=['POST'])
def subscribe():

    places_input = []
    for i in range(1, 5):
        p = request.form.get('place{}'.format(i), None)
        if p:
            places_input.append(p)

    u = User(
        email=request.form['email'],
        places_input=places_input)
    u.suscribed_at = datetime.datetime.now()
    u.put()

    return "Thank you for subscribing!"


@app.route('/users')
def users():

    q = User.all()
    res = ""
    for user in q:
        res += u'<strong><a href="/u/{}">{}</a></strong><br/>'.format(
            user.email, user.email)
        res += "<ul>"
        for p in user.places:
            res += u'<li><a href="{}">{}</a></li>'.format(p, p)
        for p in user.places_input:
            res += u'<li>{}</li>'.format(p)
        res += "</ul><br/>"

    return res


@app.route('/places', methods=['GET', 'POST'])
def places(name=None):

    if request.method == 'POST':
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
        p = Place.get_by_id(place_id)

        # for add subscriber form
        if 'email' in request.form:
            email = request.form.get('email', '')
            if email not in [u.email for u in User.all()]:
                u = User(
                    email=email,
                    suscribed_at=datetime.datetime.now())
                u.put()
            else:
                u = User.gql("WHERE email = '{0}'".format(email)).get()

            if u.email not in [pm.user.email for pm in p.place_memberships.order('-user')]:
                if u.user_memberships.count() >= 4:
                    return "This user has maximum subscribing"

                up = UserPlace(
                    user=u,
                    place=p
                )
                up.put()
            else:
                return "This user already exists in subscribers!"

        # for add update form
        elif 'update_link' in request.form and 'update_info' in request.form:
            update_link = request.form.get('update_link', '')
            update_info = request.form.get('update_info', '')
            u = Update(
                place=p,
                link=update_link,
                info=update_info
            )
            u.put()

    p = Place.get_by_id(place_id)
    updates = [update for update in p.place_updates.order('-added_at')]

    return render_template('place.html', place=p, updates=updates)


@app.route('/u/<email>', methods=['GET', 'POST'])
def user_updates_page(email=None):

    if request.method == 'POST':
        pass

    u = User.gql("WHERE email = '{0}'".format(email)).get()
    q = u.user_memberships.order('-place')

    res = u""
    for x in q:
        res += u"<strong>{}</strong><br/>".format(x.place.title)
        res += u"<ul>"
        updates = x.place.place_updates
        for pu in updates:
            res += u'<li><a href="{}">{}</a></li>'.format(pu.link, pu.info)
        res += u"</ul><br/>"

    return res


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
