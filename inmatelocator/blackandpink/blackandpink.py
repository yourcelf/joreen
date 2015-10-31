# -*- coding: utf-8 -*-
import re
from fuzzywuzzy import fuzz
import facilities
import probablepeople
import usaddress

from stateparsers.states import BaseStateSearch
from facilities.models import Facility

class ProfileMatchResultSet(object):
    def __init__(self, profile):
        self.matches = []
        self.profile = profile
        self.searches_tried = defaultdict(list)

    def add(self, lookup_result, source, params):
        self.searches_tried[source].append(params)
        score, breakdown = profile.compare_to_lookup_result(lookup_result)
        self.matches.append({
            'score': score,
            'breakdown': breakdown,
            'source': source,
            'params': params
        })
        return score

    def empty(self):
        return {'score': 0, 'result': None, 'breakdown': {}, 'source': None}

    def _add_meta(self, dct):
        dct['out of'] = len(self.matches)
        dct['searches'] = dict(self.searches_tried)

    def __len__(self):
        return len(self.matches)

    def __iter__(self):
        return sorted(self.matches, key=lambda m: m['score'], reverse=True)

    def best(self):
        try:
            match = iter(self).next()
        except StopIteration:
            match = self.empty()
        self._add_meta(match)
        return match

class Profile(object):
    def __init__(self, bp_member_number, number='', first_name='',
            middle_name='', last_name='', suffix='', **address_args):
        self.bp_member_number = bp_member_number
        self.number = number
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.suffix = suffix
        if address_args:
            self.address = Address(**address_args)
        else:
            self.address = None

    def search(self):
        if not self.address:
            search_args = []
            warnings.warn(
                    "Missing address for bp member number {}".format(self.bp_member_number)
            )
            return []

        searchers = []
        try:
            state_search = stateparsers.get_searcher(self.address.state)()
            searchers.append((self.address.state, state_search))
        except NotImplementedError:
            pass
        searchers.append(('federal', stateparsers.get_searcher("federal")()))

        # Try searching by number first, then first+last, then first
        # initial + last.  If the searcher supports it, finish with
        # searching for just last.
        search_terms = [
            ('number',),
            ('first_name', 'last_name'),
            ('first_initial', 'last_name'),
            ("last_name",)
        ]

        matches = ProfileMatchResultSet(self)
        for source, searcher in searchers:
            for terms in search_terms:
                params = {}
                for term in terms:
                    params[term] = getattr(self, term)
                try:
                    res = searcher.search(**params)
                except stateparsers.MinimumTermsError:
                    continue
                for result in res.results:
                    score = matches.add(result, source, params)
                    if score == 100:
                        return matches.best()
        return matches.best()

    @property
    def first_initial(self):
        if self.first_name:
            return self.first_name[0]
        return ""

    @classmethod
    def from_zoho(self, **kwargs):
        u = {
            'number': kwargs.get('Number', None),
            'bp_member_number': kwargs.get('B_P_Member_Number', None)
        }
        for key in ("First_Name", "Middle_Name", "Last_Name", "Suffix"):
            u[key.lower()] = kwargs.get(key, '')
        if "Facility.Address_1_Facility" in kwargs or "Address_1_Facility" in kwargs:
            self.address = Address.from_zoho(**kwargs)
        else:
            self.address = None
        return Profile(**u)

    @classmethod
    def _norm(cls, s):
        return re.sub('[^\w]', '', s.lower())

    def compare_number(self, lookup_result):
        number_scores = {}
        for num_key, lookup_num in lookup_result.numbers.iteritems():
            if lookup_num.lstrip('0') == self.number:
                score = 100
            else:
                score = fuzz.ratio(self.number, lookup_num)
            number_scores[num_key] = score
        total = max(number_scores.values()) if numer_scores else 0
        return total, (number_scores or {'number': 'not found'})

    def compare_name(self, lookup_result):
        try:
            parts, ptype = probablepeople.tag(lookup_result.name)
        except probablepeople.RepeatedLabelError:
            parts = None

        def ratio(n1, n2):
            return fuzz.partial_ratio(self._norm(n1), self._norm(n2))

        score = {}
        if parts is not None and ptype == "Person":
            # Compare based on probablepeople.tag's estimation
            p_first = parts.get('GivenName') or parts.get('FirstInitial')
            p_middle = parts.get('MiddleName') or parts.get('MiddleInitial')
            p_last = parts.get('Surname') or parts.get('LastInitial')
            p_suffix = parts.get("SuffixGenerational") or parts.get("SuffixOther")


            if self.first_name:
                score['first'] = ratio(self.first_name, p_first)
            if self.middle_name and p_middle:
                score['middle'] = ratio(self.middle_name, p_middle)
            if self.last_name:
                score['last'] = ratio(self.last_name, p_last or '')
            if self.suffix and p_suffix:
                score['suffix'] = ratio(self.suffix, p_suffix)
            
        else:
            # Working without the benefit of probablepeople.tag, do our best.
            if "," in lookup_result.name:
                # Assume last, first.
                full_name = u"{last}, {first} {middle}".format(
                    last=self.last_name, first=self.first_name, middle=self.middle_name
                ).strip()
            else:
                full_name = u"{First_Name} {Middle_Name} {Last_Name}".format(
                    last=self.last_name, first=self.first_name, middle=self.middle_name
                )
            full_name = re.sub('\s+', ' ', full_name) # remove duplicate spaces
            if self.suffix:
                full_name += u", {suffix}".format(suffix=self.suffix)
            score['full'] = ratio(full_name, lookup_result.name)
        return sum(score.values()) / float(len(score)), score

    def compare_to_lookup_result(self, lookup_result):
        number_score, number_breakdown = self.compare_number(lookup_result)
        name_score, name_breakdown = self.compare_name(lookup_result)
        if self.number and number_score == 100:
            return 100, number_breakdown
        score_breakdown = {}
        score_breakdown.update(number_breakdown)
        score_breakdown.update(name_breakdown)
        return min(number_score, name_score), score_breakdown

class Address(object):
    zoho_replacement_map = {
        r'\bCorr\. Fac(\.|ility)': 'Correctional Facility',
        r'\bCorr\.-?': 'Correctional Institution',
        r'\bC\.I\.': 'Correctional Institution',
    }

    def __init__(self, name=None, address1=None, address2=None, city=None,
            state=None, zip=None, alternate_names=None, **noise):
        if state:
            state = BaseStateSearch.get_state(state)
        self.name = name
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zip = zip
        self.alternate_names = alternate_names or []

        self.zip = re.sub('[^\d-]', '', self.zip)
        if not re.match('\d{5}(-\d{4})?', self.zip):
            raise ValueError("Invalid zip code")

    @classmethod
    def from_facility(cls, facility):
        args = ("name", "address1", "address2", "city", "state", "zip")
        kwargs = dict((k, getattr(facility, k)) for k in args)
        kwargs['alternate_names'] = list(
            facility.alternatename_set.values_list('name', flat=True)
        )
        return cls(**kwargs)

    @classmethod
    def from_zoho(cls, zoho_address):
        if "Facility.Address_1_Facility" in zoho_address:
            prefix = "Facility."
        else:
            prefix = ""
        z = zoho_address
        a = {
            'name': z[prefix + 'Address_1_Facility'].strip(),
            'address1': z[prefix + 'Address_2'].strip(),
            'city': z[prefix + 'City'].strip(),
            'state': z[prefix + 'State'].strip(),
            'zip': z[prefix + 'Zip'].strip(),
        }
        if a['name'] and not a['address1']:
            a['address1'] = a['name']
            a['name'] = None
        if a['name']:
            for fro, to in cls.zoho_replacement_map.items():
                a['name'] = re.sub(fro, to, a['name'])
        return cls(**a)

    def flatten(self):
        parts = []
        haz = lambda key: hasattr(self, key) and getattr(self, key)
        if haz('name'): parts.append(self.name)
        if haz('address1'): parts.append(self.address1)
        if haz('address2'): parts.append(self.address2)

        if haz('city') and haz('state') and haz('zip'):
            parts.append("{}, {}  {}".format(self.city, self.state, self.zip))
        else:
            if haz('city'): parts.append(self.city)
            if haz('state'): parts.append(self.state)
            if haz('zip'): parts.append(self.zip)
        return u"\n".join(parts)


    def tag(self):
        # Special case: ignore addresses with 'Unit' in the name, which texas
        # has, and usadress borks.
        if self.name and "Unit" not in self.name:
            flat = self.flatten()
            parsed = None
            try:
                parsed, atype = usaddress.tag(flat)
            except usaddress.RepeatedLabelError:
                pass
            # Even if parsing didn't raise an exception, sometimes the results are
            # junky. Make sure that "Recipient" is in there.
            if parsed and 'Recipient' in parsed:
                return parsed

        return {
            'usaddress_bailed': True,
            'ZipCode': self.zip,
            'Recipient': self.name,
            'PlaceName': self.city,
            'StateName': self.state
        }

    def compare(self, other_address):
        """
        Given two addresses, calculate a score for similarity. The score can be
        roughly interpreted as a "percent match", where 100% means exactly
        similar.  Returns a tuple of (score, breakdown), where breakdown is a
        dict which explains elements that went into the calculation.
        """
        a1 = self
        a2 = other_address

        a1_tagged = a1.tag()
        a2_tagged = a2.tag()

        def _both_have(key):
            return bool(a1_tagged.get(key) and a2_tagged.get(key))

        def _one_has(key):
            return bool(a1_tagged.get(key) or a2_tagged.get(key))

        def _address_part_norm(part):
            return re.sub('[^\w\s]', '', part.lower())

        # Required fields
        for key in ('Recipient', 'ZipCode', 'StateName'):
            if not _both_have(key):
                return 0, {'Missing key {}'.format(key): 0}

        # Ensure that substrings of zipcode are equal.
        if fuzz.partial_ratio(a1_tagged['ZipCode'], a2_tagged['ZipCode']) != 100:
            return 0, {'mismatched zip': 0}

        # Ensure that states are equal.
        s1 = BaseStateSearch.get_state(a1_tagged['StateName'].lower())
        s2 = BaseStateSearch.get_state(a2_tagged['StateName'].lower())
        if s1 is None or s2 is None or (s1 != s2):
            return 0, {'mismatched state': 0}



        scores = {}

        #
        # Fuzzy match recipient and street address. We'll take an average of scores
        # comparing the recipient, city, and address.
        #

        # Compare names
        a1_names = [a1.name] + a1.alternate_names
        a2_names = [a2.name] + a2.alternate_names
        for a1_name in a1_names:
            for a2_name in a2_names:
                scores['name'] = max(
                    scores.get('name', 0),
                    fuzz.ratio(a1_name.lower(), a2_name.lower()))

        # city
        if _both_have("PlaceName"):
            scores['city'] = fuzz.ratio(a1_tagged[key], a2_tagged[key])

        # street address
        street_score = {}
        if a1_tagged.get('usaddress_bailed') or a2_tagged.get('usaddress_bailed'):
            # usaddress bailed while attempting to tag one of the addresses.  Just
            # fuzzy match on address1 and address2 instead.
            for key in ("address1", "address2"):
                v1 = _address_part_norm(getattr(a1, key) or "")
                v2 = _address_part_norm(getattr(a2, key) or "")
                if v1 or v2:
                    street_score[key] = fuzz.ratio(v1, v2)
        else:
            exact_keys = ['AddressNumber', 'USPSBoxID']
            fuzzy_keys = [
                'StreetName',
                'AddressNumberPrefix',
                'AddressNumberSuffix',
                'StreetNamePreDirectional',
                'StreetNamePostDirectional',
                'StreetNamePreModifier',
                'StreetNamePostType',
                'StreetNamePreType',
                'USPSBoxType',
                'USPSBoxGroupType',
                'USPSBoxGroupID',
                'SubaddressIdentifier',
                'SubaddressType',
            ]
            for key in exact_keys:
                if _one_has(key):
                    if a1_tagged.get(key) != a2_tagged.get(key):
                        street_score = {'mismatched {}'.format(key): 0}
                        break
                    else:
                        street_score[key] = 100
            else:
                for key in fuzzy_keys:
                    if _one_has(key):
                        street_score[key] = fuzz.ratio(
                            _address_part_norm(a1_tagged.get(key, '')),
                            _address_part_norm(a2_tagged.get(key, '')))

        if street_score:
            scores['street_total'] = sum(street_score.values()) / float(len(street_score))
        else:
            scores['street_total'] = 0
        score = sum(scores.values()) / float(len(scores))
        breakdown = scores
        breakdown.update(street_score)
        return score, breakdown

    def find_matching_facility(self, constrain_zip=False):
        """
        Find the Facility object in the database that best matches this
        address.
        
        Return a tuple of (score, breakdown, facility).
         - score: "percent match" of facility -- 100 is a perfect match.
         - breakdown: a dict explaining components that went into the score.
         - facility: a facility object, or None.
        """
        facilities = Facility.objects.filter(
            state=self.state
        )
        if constrain_zip:
            facilities = Facility.objects.filter(zip__icontains=self.zip[0:5])
        matches = []
        for facility in facilities:
            score, breakdown = self.compare(Address.from_facility(facility))
            matches.append((score, breakdown, facility))
        if matches:
            matches.sort(key=lambda m: m[0], reverse=True)
            return matches[0]
        return (0, {}, None)

