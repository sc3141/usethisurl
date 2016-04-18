from google.appengine.ext import ndb

import short_id

MAX_URL_LENGTH = 4096

class ShortUrl(ndb.Model):
    """A main model for representing a url entry."""
    short_id= ndb.StringProperty(indexed=True)
    url = ndb.BlobProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

