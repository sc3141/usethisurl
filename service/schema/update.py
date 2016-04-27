import logging
import os

import webapp2

from google.appengine.ext import deferred
from google.appengine.api import users

from service.schema import update_message
from versions import gigondas


def restrict_access(vers):
    problem = ''
    user = users.get_current_user()
    admins = set(os.environ.get('ADMINISTRATORS', set()).split(','))
    if not admins:
        problem  = update_message(vers=vers, msg="no admin account configured (in app.yaml)")
    elif not user:
        problem = update_message(vers=vers, msg="unable to proceed. no current user")
    elif user.email() not in admins:
        problem = update_message(vers=vers, msg="user '{}' not an administrator".format(user.email()))

    return problem


class UpdateHandler(webapp2.RequestHandler):
    def get(self, **kwargs):
        task=None
        vers = kwargs.get('vers', '???')
        if vers == 'gigondas':
            task=gigondas.update_schema
        elif not vers:
            message = update_message(msg='version missing')
            logging.error(message)
            self.response.out.write(message)
        else:
            message = update_message(vers=vers, msg="migration to version '%s' not supported" % vers)
            logging.error(message)
            self.response.out.write(message)

        if task:
            access_problem = restrict_access(vers)
            if access_problem:
                logging.warning(access_problem)
                self.response.out.write(access_problem)
            else:
                deferred.defer(task)
                message = update_message(vers=vers, msg="Schema migration successfully initiated.")
                logging.info(message)
                self.response.out.write(message)


app = webapp2.WSGIApplication([
    webapp2.Route('/schema/update/<vers:.+>', handler=UpdateHandler, name='schema_update'),
], debug=True)
