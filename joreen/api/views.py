from django.http import JsonResponse, HttpResponse

from stateparsers import AVAILABLE_STATES, get_searcher, MinimumTermsError

_contiguous_states = None


def get_state(abbr):
    global _contiguous_states
    from localflavor.us.us_states import CONTIGUOUS_STATES, STATES_NORMALIZED

    if _contiguous_states is None:
        _contiguous_states = dict(CONTIGUOUS_STATES)
    return _contiguous_states.get(STATES_NORMALIZED.get(abbr.lower()))


def access_control_headers(response):
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "X-Requested-With"
    response["Access-Control-Max-Age"] = "1800"


def access_control_response(fn):
    def options_handler(request):
        if request.method == "OPTIONS":
            response = HttpResponse("")
            access_control_headers(response)
            return response
        response = fn(request)
        access_control_headers(response)
        return response

    return options_handler


# Create your views here.
@access_control_response
def states(request):
    obj = {"states": {}}
    for abbr in AVAILABLE_STATES:
        state = {
            "abbreviation": abbr,
            "name": str(get_state(abbr) or abbr),
            "minimum_search_terms": get_searcher(abbr).minimum_search_terms,
        }
        obj["states"][abbr] = state
    return JsonResponse(obj)


@access_control_response
def search(request):
    state = request.GET.get("state", "")
    kwargs = {
        "first_name": request.GET.get("first_name", ""),
        "last_name": request.GET.get("last_name", ""),
        "number": request.GET.get("number", ""),
    }

    try:
        searcher = get_searcher(state)()
    except NotImplementedError:
        return JsonResponse({"error": "Unsupported state"}, status=400)

    try:
        res = searcher.search(**kwargs)
    except MinimumTermsError:
        return JsonResponse(
            {
                "error": "{} requires one of {}".format(
                    state, searcher.minimum_search_terms
                )
            },
            status=400,
        )

    try:
        return JsonResponse(
            {
                "state": state,
                "search_terms": kwargs,
                "results": list(map(lambda r: r.to_dict(), res["results"])),
                "errors": res["errors"],
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
