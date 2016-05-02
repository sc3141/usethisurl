"""
Assigns request handlers to various routes in application.
If environment variable, 'MAINTENANCE' is assigend a csv list of special values,
the application is configured to respond with 503 'system down for maintenance'
"""
import os
import webapp2

from handlers import ShortenUrl, QueryUrl, RedirectUrl, Maintenance

MAINTENANCE_CATEGORIES=set(['all', 'create', 'query', 'redirect'])

MAINTENANCE = set(os.environ.get('MAINTENANCE', '').split(',')) & MAINTENANCE_CATEGORIES
if 'all' in MAINTENANCE:
    MAINTENANCE |= { 'create', 'query', 'redirect'}

def in_maintenance():
    return MAINTENANCE

_create_handler = Maintenance if 'create' in MAINTENANCE else ShortenUrl
create_or_update = webapp2.WSGIApplication([
    ('/shorturl', _create_handler),
], debug=True)

_query_handler = Maintenance if 'query' in MAINTENANCE else QueryUrl
query = webapp2.WSGIApplication([
    webapp2.Route('/shorturl/<sid:.+>', handler=_query_handler, name='query'),
], debug=True)

_redirect_handler = Maintenance if 'redirect' in MAINTENANCE else RedirectUrl
redirect = webapp2.WSGIApplication([
    webapp2.Route('/<sid:.*>', handler=_redirect_handler, name='redirect'),
], debug=True)
