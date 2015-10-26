import time
import logging
import requests
import requests_cache
from urllib.parse import urlparse

class ThrottleSession(requests.Session):
    """
    A request session that throttles requests per netloc.
    """
    netloc_log = {}
    throttle = 1 # seconds

    def send(self, request, **kwargs):
        netloc = urlparse(request.url).netloc
        last_req = self.netloc_log.get(netloc)
        if last_req:
            now = time.time()
            if now - last_req < self.throttle:
                delay = self.throttle - (now - last_req)
                logging.info(
                    "Throttling request to {} for {} seconds.".format(request.url, delay)
                )
                time.sleep(delay)
        res = super(ThrottleSession, self).send(request, **kwargs)
        self.netloc_log[netloc] = time.time()
        return res

class SessionFactory(requests_cache.CachedSession, ThrottleSession):
    pass

def setup_cache(name="stateparsers_cache"):
    """
    Set up caching for GET and POST, with a custom session factory that
    throttles requests.
    """
    requests_cache.install_cache(
        name,
        # We allow caching of POST (generally not a good idea) because many of
        # the prisoner search forms use POST for searches (generally not a good
        # idea). This means you need to explicitly disable cache when you're
        # making real POST requests:
        # https://requests-cache.readthedocs.org/en/latest/api.html#requests_cache.core.disabled
        allowable_methods=('GET', 'POST'),
        expire_after=60*60*24,
        session_factory=SessionFactory
    )

