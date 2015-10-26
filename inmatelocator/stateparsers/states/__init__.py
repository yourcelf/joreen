class LookupResult(object):
    STATUS_INCARCERATED = "Incarcerated"
    STATUS_RELEASED = "Released"
    STATUS_UNKNOWN = "Unknown"
    def __init__(self,
            name,
            numbers,
            status,
            facilities,
            search_url,
            result_url,
            extra):
        self.name = name
        self.numbers = numbers
        self.facilities = facilities
        self.search_url = search_url
        self.result_url = result_url
        self.extra = extra

        for key, val in kwargs.iteritems():
            setattr(self, key, val)

def normalize_name(name):
    # Replace all but - and a-z with emptystring.
    name = re.sub("[^-a-z ]", "", name.lower()).strip()
    # Replace - with single space " "
    name = re.sub("-", " ", name)
    # Remove multiple spaces
    name = re.sub("\s+", " ", name)
    return name

def fuzzy_match_address(address, choices):
    scores = []
    for choice in choices:
        score = []
        # Zip handling
        if address.get('state') is not None and address.get('state') != choice.get('state'):
            continue
        z1 = address.get('zip')
        z2 = choice.get('zip')
        if z1 and z2:
            score.append(fuzz.partial_ratio(z1, z2))
        # City, org, address
        for key in ["city", "address1", "organization"]:
           v1 = address.get(key)
           v2 = choice.get(key)
           if v1 is not None and v2 is not None:
               v1 = re.sub('[^a-z0-9 ]', '', v1.lower())
               v2 = re.sub('[^a-z0-9 ]', '', v2.lower())
               score.append(fuzz.ratio(v1, v2))
        if score:
            scores.append((sum(score) / float(len(score)), choice))

    if len(scores) == 0:
        return 0, None

    scores.sort()
    return scores[-1][0], scores[-1][1]


