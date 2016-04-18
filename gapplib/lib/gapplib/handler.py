"""
Implements useful utilities for use within handlers.
"""

import logging
import urlparse
import httplib
import os

from google.appengine.api import modules
from google.appengine.api.app_identity import app_identity

from status_templates import GENERIC_STATUS_TEMPLATE,NOT_FOUND_STATUS_TEMPLATE

def host_url():
    hostname = app_identity.get_default_version_hostname()
    return urlparse.urlunsplit(('http', hostname, '', '', ''))

def host_path(path):
    return os.path.join(host_url(), path)

def module_url(module):
    host = modules.get_hostname(module=module)
    return urlparse.urlunsplit(('http', host, '', '', ''))

def module_path(module, path):
    if isinstance(path, str):
        return os.path.join(module_url(module), path)
    else:
        return os.path.join(module_url(module), *path)


def write_error(response, code, message=None):
    response.set_status(code)
    if message:
        response.out.write(message)

def write_and_log_error(response, code, message=None):
    if message:
        logging.error("status {code}: {msg}".format(code=code, msg=message))

    write_error(response, code, message)

def render_error(response, code, message=None):
    response.set_status(code)

    template = NOT_FOUND_STATUS_TEMPLATE if code == httplib.NOT_FOUND else GENERIC_STATUS_TEMPLATE

    content = template.format(
        code=code,
        std_desc=response.http_status_message(code),
        message=message if message else '')

    response.out.write(content)

def render_and_log_error(response, code, message=None):
    if message:
        logging.error("status {code}: {msg}".format(code=code, msg=message))

    render_error(response, code, message)