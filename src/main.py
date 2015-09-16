"""`main` is the top level module for Flask application."""

import datetime

from flask import Flask, redirect, render_template, request
from jinja2 import Markup

from decorators import admin_required
from models import (
    Digest, Place, Update, User, UserPlace)


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
@admin_required
def users_view():
    return render_template("users.html", users=User.all())


@app.route('/u/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def user_updates_page(user_id=None):
    user = User.get_by_id(user_id)
    places = [x.place for x in user.places_subscribed.order('-place')]
    digests = list(Digest.all().filter('user =', user).order('-created_at').run(limit=5))
    if digests:
        last_digest = digests[-1]
    else:
        last_digest = None
    updates = {}
    for p in places:
        place_updates = Update.all()
        place_updates = place_updates.filter('place =', p)
        place_updates = place_updates.order('-added_at')
        if last_digest:
            place_updates = place_updates.filter('added_at >', last_digest.created_at)
        updates[p.key().id()] = list(place_updates.run(limit=10))
    return render_template(
        "user.html",
        user=user,
        places=places,
        digests=digests,
        last_digest=last_digest,
        updates=updates
    )


@app.route('/d/<int:digest_id>', methods=['GET'])
def digest_page(digest_id=None):
    digest = Digest.get_by_id(digest_id)
    user = digest.user
    places = [x.place for x in user.places_subscribed.order('-place')]
    updates = {}
    for p in places:
        place_updates = Update.all()
        place_updates = place_updates.filter('place =', p)
        place_updates = place_updates.order('-added_at')
        place_updates = place_updates.filter('added_at <', digest.created_at)
        if digest.previous_digest_at:
            place_updates = place_updates.filter('added_at >', digest.previous_digest_at)
        updates[p.key().id()] = list(place_updates.run(limit=10))
    return render_template(
        "digest.html",
        user=user,
        places=places,
        digest=digest,
        updates=updates
    )


@app.route('/u/<int:user_id>/digest/create', methods=['POST'])
@admin_required
def user_create_digest(user_id=None):
    user = User.get_by_id(user_id)
    last_digest = Digest.all().filter('user =', user).order('-created_at').fetch(1)
    if last_digest:
        last_digest = last_digest[0]
    else:
        last_digest = None
    d = Digest(
        user=user,
        previous_digest_at=None if not last_digest else last_digest.created_at
    )
    d.save()
    return redirect('/u/{}'.format(user_id))


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
                if u.places_subscribed.count() >= 4:
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


@app.route('/update/<int:update_id>/delete', methods=['GET'])
@admin_required
def update_delete_page(update_id=None):
    u = Update.get_by_id(update_id)
    u.delete()
    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect('/')


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


@app.template_filter('format_update')
def format_update_filter(u):
    return Markup(
        """<a href="{}">{}</a> | <a href="/update/{}/delete">Delete</a> """.format(
            u.link, u.info, u.key().id()
        )
    )
