from stateparsers.states import texas, california, federal, florida, newyork, pennsylvania

name_map = {
    "california": california,
    "texas": texas,
    "federal": federal,
    "florida": florida,
    "newyork": newyork,
    "pennsylvania": pennsylvania
}

AVAILABLE_STATES = name_map.keys()

def search(state_name, **kwargs):
    if state_name not in name_map:
        raise NotImplementedError(
            "No search interface implemented for state `{}`".format(state_name)
        )
    module = name_map[state_name]
    return module.search(**kwargs)
