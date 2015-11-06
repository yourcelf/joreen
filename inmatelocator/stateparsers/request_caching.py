import time
import logging
import requests_cache
from urllib.parse import urlparse

import collections
from contextlib import contextmanager
from datetime import datetime, timedelta
from operator import itemgetter

import requests
from requests import Session as OriginalSession
from requests.hooks import dispatch_hook

from requests_cache import backends
from requests_cache.compat import basestring

class ThrottleSession(OriginalSession):
    """
    A request session that throttles requests per netloc.
    """
    netloc_log = {}
    throttle_duration = 1 # seconds
    max_retries = 2

    def throttle(self, request):
        netloc = urlparse(request.url).netloc
        last_req = self.netloc_log.get(netloc)
        # Implement as a loop so separate threads sharing this session will
        # continue to wait.
        while self.netloc_log.get(netloc) and time.time() - self.netloc_log[netloc] < self.throttle_duration:
            delay = self.throttle_duration - (time.time() - self.netloc_log[netloc])
            print("Throttling request to {} for {} seconds.".format(request.url, delay))
            logging.info(
                "Throttling request to {} for {} seconds.".format(request.url, delay)
            )
            time.sleep(delay)
        return netloc

    def send(self, request, **kwargs):
        netloc = self.throttle(request)

        # Set a start time to fend off other threads.
        self.netloc_log[netloc] = time.time()

        # Try a connection it fails, with a good long pause in between.
        retries = 0
        while retries < self.max_retries:
            try:
                print("REQUEST:", request.method, request.url, request.body)
                res = super(ThrottleSession, self).send(request, **kwargs)
                break
            except requests.exceptions.ConnectionError:
                retries += 1
                if retries >= self.max_retries:
                    raise
                else:
                    dur = self.throttle_duration * 5
                    # Signal other threads to hold off while we wait.
                    self.netloc_log[netloc] = time.time() + dur
                    time.sleep(dur)
                    continue

        # Set the final time.
        self.netloc_log[netloc] = time.time()
        return res

def setup_cache(name="cache/stateparsers", netloc_throttle=1):
    """
    Set up caching for GET and POST, with a custom session factory that
    throttles requests.
    """

    class SessionFactory(CachedSession):
        throttle_duration = netloc_throttle

    requests_cache.install_cache(
        name,
        # We allow caching of POST (generally not a good idea) because many of
        # the prisoner search forms use POST for searches (generally not a good
        # idea). This means you need to explicitly disable cache when you're
        # making real POST requests:
        # https://requests-cache.readthedocs.org/en/latest/api.html#requests_cache.core.disabled
        allowable_methods=('GET', 'POST'),
        allowable_codes=(200, 301, 302, 307), # allow all non-error responses to get cached
        expire_after=60*60*24,
        session_factory=SessionFactory
    )

####################################################################################
# Te below is duplicated from requests_cache so that we can have a session
# factory with a different parent class, the better to implement throttling.
####################################################################################

def _normalize_parameters(params):
    """ If builtin dict is passed as parameter, returns sorted list
    of key-value pairs
    """
    if type(params) is dict:
        return sorted(params.items(), key=itemgetter(0))
    return params

class CachedSession(ThrottleSession):
    """ Requests ``Sessions`` with caching support.
    """

    def __init__(self, cache_name='cache', backend=None, expire_after=None,
                 allowable_codes=(200,), allowable_methods=('GET',),
                 old_data_on_error=False, **backend_options):
        """
        :param cache_name: for ``sqlite`` backend: cache file will start with this prefix,
                           e.g ``cache.sqlite``
                           for ``mongodb``: it's used as database name
                           
                           for ``redis``: it's used as the namespace. This means all keys
                           are prefixed with ``'cache_name:'``
        :param backend: cache backend name e.g ``'sqlite'``, ``'mongodb'``, ``'redis'``, ``'memory'``.
                        (see :ref:`persistence`). Or instance of backend implementation.
                        Default value is ``None``, which means use ``'sqlite'`` if available,
                        otherwise fallback to ``'memory'``.
        :param expire_after: ``timedelta`` or number of seconds after cache will be expired
                             or `None` (default) to ignore expiration
        :type expire_after: float
        :param allowable_codes: limit caching only for response with this codes (default: 200)
        :type allowable_codes: tuple
        :param allowable_methods: cache only requests of this methods (default: 'GET')
        :type allowable_methods: tuple
        :kwarg backend_options: options for chosen backend. See corresponding
                                :ref:`sqlite <backends_sqlite>`, :ref:`mongo <backends_mongo>` 
                                and :ref:`redis <backends_redis>` backends API documentation
        :param include_get_headers: If `True` headers will be part of cache key.
                                    E.g. after get('some_link', headers={'Accept':'application/json'})
                                    get('some_link', headers={'Accept':'application/xml'}) is not from cache.
        :param ignored_parameters: List of parameters to be excluded from the cache key.
                                   Useful when requesting the same resource through different
                                   credentials or access tokens, passed as parameters.
        :param old_data_on_error: If `True` it will return expired cached response if update fails
        """
        if backend is None or isinstance(backend, basestring):
            self.cache = backends.create_backend(backend, cache_name,
                                                 backend_options)
        else:
            self.cache = backend
        self._cache_name = cache_name

        if expire_after is not None and not isinstance(expire_after, timedelta):
            expire_after = timedelta(seconds=expire_after)
        self._cache_expire_after = expire_after

        self._cache_allowable_codes = allowable_codes
        self._cache_allowable_methods = allowable_methods
        self._return_old_data_on_error = old_data_on_error
        self._is_cache_disabled = False
        super(CachedSession, self).__init__()

    def send(self, request, **kwargs):
        if (self._is_cache_disabled
            or request.method not in self._cache_allowable_methods):
            response = super(CachedSession, self).send(request, **kwargs)
            response.from_cache = False
            return response

        cache_key = self.cache.create_key(request)

        def send_request_and_cache_response():
            response = super(CachedSession, self).send(request, **kwargs)
            if response.status_code in self._cache_allowable_codes:
                self.cache.save_response(cache_key, response)
            response.from_cache = False
            return response

        response, timestamp = self.cache.get_response_and_time(cache_key)
        if response is None:
            return send_request_and_cache_response()

        if self._cache_expire_after is not None:
            is_expired = datetime.utcnow() - timestamp > self._cache_expire_after
            if is_expired:
                if not self._return_old_data_on_error:
                    self.cache.delete(cache_key)
                    return send_request_and_cache_response()
                try:
                    new_response = send_request_and_cache_response()
                except Exception:
                    return response
                else:
                    if new_response.status_code not in self._cache_allowable_codes:
                        return response
                    return new_response

        # dispatch hook here, because we've removed it before pickling
        response.from_cache = True
        response = dispatch_hook('response', request.hooks, response, **kwargs)
        return response

    def request(self, method, url, params=None, data=None, **kwargs):
        response = super(CachedSession, self).request(
            method, url,
            _normalize_parameters(params),
            _normalize_parameters(data),
            **kwargs
        )
        if self._is_cache_disabled:
            return response

        main_key = self.cache.create_key(response.request)
        for r in response.history:
            self.cache.add_key_mapping(
                self.cache.create_key(r.request), main_key
            )
        return response

    @contextmanager
    def cache_disabled(self):
        """
        Context manager for temporary disabling cache
        ::
            >>> s = CachedSession()
            >>> with s.cache_disabled():
            ...     s.get('http://httpbin.org/ip')
        """
        self._is_cache_disabled = True
        try:
            yield
        finally:
            self._is_cache_disabled = False

    def __repr__(self):
        return (
            "<CachedSession(%s('%s', ...), expire_after=%s, "
            "allowable_methods=%s)>" % (
                self.cache.__class__.__name__, self._cache_name,
                self._cache_expire_after, self._cache_allowable_methods
            )
        )

