from stateparsers.states import (
    texas,
    california,
    federal,
    florida,
    newyork,
    pennsylvania,
)
from stateparsers.states import MinimumTermsError  # noqa: F401


name_map = {
    "federal": federal,
    "CA": california,
    "TX": texas,
    "FL": florida,
    "NY": newyork,
    "PA": pennsylvania,
}

AVAILABLE_STATES = name_map.keys()


def get_searcher(state_name):
    if state_name in name_map:
        return name_map[state_name].Search
    raise NotImplementedError(
        "No search interface implemented for state `{}`".format(state_name)
    )


def search(state_name, **kwargs):
    Searcher = get_searcher(state_name)
    return Searcher().search(**kwargs)
