# flake8: noqa

from .default_settings import *

DEBUG = True

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": False,
        "BUNDLE_DIR_NAME": "dev/",
        "STATS_FILE": os.path.join(BASE_DIR, "static", "dev", "webpack-stats.json"),
        "POLL_INTERVAL": 0.1,
        "IGNORE": [r".+\.hot-update.js", r".+\.map"],
    }
}
