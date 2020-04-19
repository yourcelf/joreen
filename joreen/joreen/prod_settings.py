# flake8: noqa
from .default_settings import *

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": True,
        "BUNDLE_DIR_NAME": "dist/",
        "STATS_FILE": os.path.join(BASE_DIR, "static", "dist", "webpack-stats.json"),
    }
}
