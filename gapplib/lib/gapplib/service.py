import os

def is_production():
    return os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/')
