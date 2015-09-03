from google.appengine.ext import db


class User(db.Model):
    email = db.EmailProperty(required=True)
    places = db.ListProperty(db.Link)
    places_input = db.ListProperty(str)
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
    user = db.ReferenceProperty(User, required=True, collection_name='places_subscribed')
    place = db.ReferenceProperty(Place, required=True, collection_name='place_memberships')

    def __repr__(self):
        return '< User = %s, Place = %s >' % (self.user, self.place)


class Update(db.Model):
    place = db.ReferenceProperty(Place, collection_name='place_updates')
    link = db.LinkProperty()
    info = db.TextProperty(indexed=False)
    added_at = db.DateTimeProperty(auto_now_add=True)


class PlaceLink(db.Model):
    place = db.ReferenceProperty(Place)
    link = db.LinkProperty()
    added_at = db.DateTimeProperty(auto_now_add=True)


class Digest(db.Model):
    user = db.ReferenceProperty(User, required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    previous_digest_at = db.DateTimeProperty()
