import webapp2

from handlers import ShortenUrl, QueryUrl, RedirectUrl

create_or_update = webapp2.WSGIApplication([
    ('/shorturl', ShortenUrl),
], debug=True)

query = webapp2.WSGIApplication([
    webapp2.Route('/shorturl/<sid:.+>', handler=QueryUrl, name='query'),
], debug=True)

redirect = webapp2.WSGIApplication([
    webapp2.Route('/<sid:.*>', handler=RedirectUrl, name='redirect'),
], debug=True)
