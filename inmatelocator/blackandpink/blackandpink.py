# -*- coding: utf-8 -*-
import re
from collections import defaultdict
from fuzzywuzzy import fuzz
import probablepeople
import usaddress
from django.core.exceptions import ValidationError

from facilities.models import Facility
import stateparsers
from stateparsers.states import BaseStateSearch
from blackandpink import zoho
from blackandpink.models import ContactCheck

class ProfileMatchResultSet(object):
    def __init__(self, profile):
        self.matches = []
        self.profile = profile
        self.searches_tried = defaultdict(list)

    def add(self, lookup_result, source=None, params=None):
        self.searches_tried[source].append(params)
        score, breakdown = self.profile.compare_to_lookup_result(lookup_result)
        self.matches.append(ProfileMatchResult(
            profile=self.profile,
            score=score,
            breakdown=breakdown,
            source=source,
            result=lookup_result,
            params=params
        ))
        return score

    def empty(self):
        return ProfileMatchResult(profile=self.profile)

    def _add_meta(self, pmr):
        pmr.out_of = len(self.matches)
        pmr.searches = dict(self.searches_tried)

    def __len__(self):
        return len(self.matches)

    def __iter__(self):
        return iter(sorted(self.matches, key=lambda m: m.score, reverse=True))

    def best(self):
        try:
            for match in self:
                self._add_meta(match)
                return match
        except StopIteration:
            pass
        match = self.empty()
        self._add_meta(match)
        return match

class ProfileMatchResult(object):

    def __init__(self, profile=None, score=0, result=None, breakdown=None,
                 source=None, params=None):
        self.profile = profile
        self.score = score
        self.result = result
        self.breakdown = breakdown or {}
        self.source = source
        self.params = params

        self.status = None
        self.facility_match = None
        self.out_of = None
        self.searches = None

    def classify(self, facility_directory):
        if self.result is None or self.score <= 90:
            self.status = ContactCheck.STATUS.not_found
            self.facility_match = None
            return

        if self.result and self.result.status == self.result.STATUS_RELEASED:
            if self.profile.status in ("Released", "Deceased"):
                self.status = ContactCheck.STATUS.found_released_zoho_agrees
                self.facility_match = None
                return
            else:
                self.status = ContactCheck.STATUS.found_released_zoho_disagrees
                self.facility_match = None
                return

        # Compare addresses of matched facilities
        matched_facilities = list(self.result.facilities)
        if len(matched_facilities) == 0:
            self.status = ContactCheck.STATUS.found_unknown_facility
            self.facility_match = None
            return

        # Does one of the returned facilities match the current address?
        for facility in matched_facilities:
            match = self.profile.address.compare_to_facility(facility)
            if match.is_valid():
                self.status = ContactCheck.STATUS.found_facility_matches
                self.facility_match = match
                return

        # Facility differs. Pick one of the matched results to use.
        try:
            facility = [f for f in matched_facilities if f.general][0]
        except IndexError:
            # Arbitrarily pick one. :(
            facility = matched_facilities[0]

        # Does zoho have our facility?
        zoho_matches = []
        facility_match = facility_directory.get_by_facility(facility)
        if facility_match:
            self.status = ContactCheck.STATUS.found_facility_differs_zoho_has
            self.facility_match = facility_match
            return
        else:
            self.status = ContactCheck.STATUS.found_facility_differs_zoho_lacks
            self.facility_match = AddressFacilityMatch(None, None, None, facility)
            return

class Profile(object):
    def __init__(self, bp_member_number, number='', first_name='',
            middle_name='', last_name='', suffix='', status='', 
            **address_args):
        self.bp_member_number = bp_member_number
        self.number = number
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.suffix = suffix
        self.status = status
        if address_args:
            self.address = Address(**address_args)
        else:
            self.address = None

    def status_is_searchable(self):
        return self.status not in ("Deceased", "Released")

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
                for result in res['results']:
                    score = matches.add(result, source, params)
                    if score == 100:
                        return matches
        return matches

    @property
    def first_initial(self):
        if self.first_name:
            return self.first_name[0]
        return ""

    @classmethod
    def from_zoho(self, kwargs):
        u = {
            'number': kwargs.get('Number', None),
            'bp_member_number': kwargs.get('B_P_Member_Number', None),
            'status': kwargs.get('Status', None)
        }
        for key in ("First_Name", "Middle_Name", "Last_Name", "Suffix"):
            u[key.lower()] = kwargs.get(key, '')
        if "Facility.Address_1_Facility" in kwargs or "Address_1_Facility" in kwargs:
            address = Address.from_zoho(kwargs)
        else:
            address = None
        profile = Profile(**u)
        profile.address = address
        profile.zoho_profile = kwargs
        return profile

    @classmethod
    def _norm(cls, s):
        return re.sub('[^\w]', '', (s or '').lower())

    def compare_number(self, lookup_result):
        number_scores = {}
        for num_key, lookup_num in lookup_result.numbers.items():
            if lookup_num.lstrip('0') == self.number:
                score = 100
            else:
                score = fuzz.ratio(self.number, lookup_num)
            number_scores[num_key] = score
        total = max(number_scores.values()) if number_scores else 0
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
                full_name = u"{first} {middle} {last}".format(
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
        r'\sCorr\. Fac(\.|ility)': ' Correctional Facility',
        r'\sCorr\.-?': ' Correctional Institution',
        r'\sC\.I\.': ' Correctional Institution',
        r'\s- Fed\.': '',
    }

    def __init__(self, name=None, address1=None, address2=None, city=None,
            state=None, zip=None, alternate_names=None,
            zoho_id=None, zoho_key=None, **noise):
        if state:
            state = BaseStateSearch.get_state(state)
        self.name = name
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zip = zip
        self.alternate_names = alternate_names or []
        self.zoho_id = zoho_id
        self.zoho_key = zoho_key

        self.zip = re.sub('[^\d-]', '', self.zip)

    def validate(self):
        if not re.match('\d{5}(-\d{4})?', self.zip):
            raise ValidationError("Invalid zip code")

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
            # Only full zoho facility objects have the ID; profiles have a
            # non-unique key as a concatenation of the Facility/Address2/city/state/zip.
            'zoho_id': z['ID'] if not prefix else None,
            'zoho_key': z['Facility'] if prefix else z['Facility_Add2_City_State_Zip']
        }
        if a['name'] and not a['address1']:
            a['address1'] = a['name']
            a['name'] = None
        if a['name']:
            for fro, to in cls.zoho_replacement_map.items():
                a['name'] = re.sub(fro, to, a['name'])

        match = re.match(r'^(?P<main>.*)\s\((?P<abbr>[A-Z]{2,})\)$', a.get('name') or '')
        if match:
            a['name'] = match.group('main').strip()
            a['alternate_names'] = [match.group('abbr')]
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

    def _parse_split_recipient(self, flat):
        lines = flat.split("\n")
        recipient, others = lines[0], lines[1:]
        try:
            parsed, atype = usaddress.tag("\n".join(others))
        except usaddress.RepeatedLabelError:
            return None
        else:
            if ('USPSBoxID' in parsed or 'AddressNumber' in parsed) and ('Recipient' not in parsed):
                parsed['Recipient'] = recipient
            else:
                parsed = None
        return parsed

    def tag(self):
        if self.name:
            # Parse without recipient for more reliable results.
            parsed = self._parse_split_recipient(self.flatten())
                
            # Even if parsing didn't raise an exception, sometimes the results are
            # junky. Make sure that "Recipient" is in there.
            if parsed and 'Recipient' in parsed:
                return parsed

        return {
            'usaddress_bailed': True,
            'ZipCode': self.zip,
            'Recipient': self.name if self.name is not None else self.address1,
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
            return re.sub('[^\w\s]', '', part.lower().strip())

        # Required fields
        for key in ('Recipient', 'ZipCode', 'StateName'):
            if not _both_have(key):
                return 0, {'Missing key {}'.format(key): 0}


        scores = {}
        fatal = False

        # Ensure that substrings of zipcode are equal.
        if fuzz.partial_ratio(a1_tagged['ZipCode'], a2_tagged['ZipCode']) != 100:
            fatal = "Mismatched zip"

        # Ensure that states are equal.
        s1 = BaseStateSearch.get_state(a1_tagged['StateName'].lower())
        s2 = BaseStateSearch.get_state(a2_tagged['StateName'].lower())
        if s1 is None or s2 is None or (s1 != s2):
            fatal = "Mismatched state"

        #
        # Fuzzy match recipient and street address. We'll take an average of scores
        # comparing the recipient, city, and address.
        #

        # Compare names
        a1_names = [a1.name or a1_tagged.get('Recipient')] + a1.alternate_names
        a2_names = [a2.name or a2_tagged.get('Recipient')] + a2.alternate_names
        for a1_name in a1_names:
            for a2_name in a2_names:
                scores['name'] = max(
                    scores.get('name', 0),
                    fuzz.ratio(a1_name.lower(), a2_name.lower()))

        # city
        if _both_have("PlaceName"):
            scores['city'] = fuzz.ratio(_address_part_norm(a1_tagged["PlaceName"]),
                                        _address_part_norm(a2_tagged["PlaceName"]))

        # street address
        street_score = {}
        if a1_tagged.get('usaddress_bailed') or a2_tagged.get('usaddress_bailed'):
            # usaddress bailed while attempting to tag one of the addresses.  Just
            # fuzzy match on address1 and address2 instead.

            # Fall back to name if address1 is missing.
            a1_address1 = a1.address1 or a1.name or ""
            a1_address2 = a1.address2 or ""
            a2_address1 = a2.address1 or a2.name or ""
            a2_address2 = a2.address2 or ""

            for v1,v2,key in ((a1_address1, a2_address1, 'address1'),
                              (a1_address2, a2_address2, 'address2')):
                v1 = _address_part_norm(v1)
                v2 = _address_part_norm(v2)
                if v1 or v2:
                    street_score[key] = fuzz.ratio(v1, v2)
        else:
            # Keys to check if either address has it.
            one_has_exact_keys = ['AddressNumber', 'USPSBoxID']
            # Keys to check only if both addresses have it.
            both_have_exact_keys = []
            # Keys to check for fuzzy matches.
            one_has_fuzzy_keys = [
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
            both_have_fuzzy_keys = []

            # If both have a PO Box, only pay attention to the non-PO Box keys
            # that they both share.  This is to not penalize addresses that
            # list both a street address and PO Box when compared to an address
            # that only lists the PO Box.  But if both addresses contain a
            # street address as well as a PO Box, consider the street addresses
            # too.
            if _both_have('USPSBoxID'):
                both_have_exact_keys = [k for k in one_has_exact_keys if 'USPS' not in k]
                one_has_exact_keys = [k for k in one_has_exact_keys if 'USPS' in k]
                both_have_fuzzy_keys = [k for k in one_has_fuzzy_keys if 'USPS' not in k]
                one_has_fuzzy_keys = [k for k in one_has_fuzzy_keys if 'USPS' in k]

            for check, keylist, exact in (
                    (_one_has, one_has_exact_keys, True),
                    (_both_have, both_have_exact_keys, True),
                    (_one_has, one_has_fuzzy_keys, False),
                    (_both_have, both_have_fuzzy_keys, False)):
                for key in keylist:
                    if check(key):
                        a1_norm = _address_part_norm(a1_tagged.get(key, ''))
                        a2_norm = _address_part_norm(a2_tagged.get(key, ''))
                        if exact:
                            # Exact check
                            if a1_norm != a2_norm:
                                fatal = 'Mismatched {}'.format(key)
                                street_score[key] = 0
                                break
                            else:
                                street_score[key] = 100
                        else:
                            # Fuzzy check
                            street_score[key] = fuzz.ratio(a1_norm, a2_norm)
                else:
                    continue
                break

        if street_score:
            scores['street_total'] = sum(street_score.values()) / float(len(street_score))
        elif ('Recipient' in a1_tagged and 'Recipient' in a2_tagged and \
              _address_part_norm(a1_tagged['Recipient']) == \
              _address_part_norm(a2_tagged['Recipient'])):
            # There's no "street" part listed in the address, but the
            # recipients exist and match up. This is likely to be a
            # "streetless" address like "Montgomery Air Force Base".
            scores['street_total'] = 100
        else:
            scores['street_total'] = 0
        score = sum(scores.values()) / float(len(scores))
        breakdown = scores
        breakdown.update(street_score)
        if fatal:
            breakdown['fatal'] = fatal
        return score, breakdown

    def compare_to_facility(self, facility):
        score, breakdown = self.compare(Address.from_facility(facility))
        return AddressFacilityMatch(self, score, breakdown, facility)

    def find_matching_facilities(self, constrain_zip=False):
        """
        Find the Facility object in the database that best matches this
        address.
        
        Return a tuple of (score, breakdown, facility).
         - score: "percent match" of facility -- 100 is a perfect match.
         - breakdown: a dict explaining components that went into the score.
         - facility: a facility object, or None.
        """
        facilities = Facility.objects.filter(state=self.state)
        if constrain_zip:
            facilities = Facility.objects.filter(zip__icontains=self.zip[0:5])
        matches = []
        for facility in facilities:
            matches.append(self.compare_to_facility(facility))

        matches.sort(key=lambda m: m.score, reverse=True)
        return [m for m in matches[0:5]]

class AddressFacilityMatch(object):
    def __init__(self, address, score, breakdown, facility):
        self.address = address
        self.score = score
        self.breakdown = breakdown
        self.facility = facility
        self.fatal = breakdown.get('fatal', False) if breakdown else False

    def is_valid(self):
        return not self.fatal and self.score > 90 or (
            self.breakdown.get('street_total', 0) == 100 and \
            self.breakdown.get('name', 0) > 50
        )

class FacilityDirectory(object):
    def __init__(self):
        self.matches = {}
        self.facilities = {}
        self.facility_types = {}
        for zoho_facility in zoho.fetch_all_facilities():
            self.add_facility(zoho_facility)

    def add_facility(self, zoho_facility):
        key = zoho_facility['Facility_Add2_City_State_Zip']
        # There are duplicate addresses.  Prefer the ones that have more
        # contacts.
        if key in self.matches:
            existing = self.matches[key].zoho_facility
            if (len(zoho_facility['Mailing_Address_Date_Current']) <=
                    len(existing['Mailing_Address_Date_Current'])):
                return

        self.facility_types[key] = (
            self.facility_types.get(key) or zoho_facility['Facility_Type']
        )
        address = Address.from_zoho(zoho_facility)
        matches = address.find_matching_facilities(constrain_zip=True)
        for match in matches:
            if match.is_valid():
                match.zoho_facility = zoho_facility
                self.facilities[match.facility.id] = match
                found = True
                self.matches[key] = match
                break
        else:
            self.matches[key] = AddressFacilityMatch(
                address=address, facility=None, score=0, breakdown=None)
            self.matches[key].zoho_facility = zoho_facility

    def get_facility_type(self, key=None, zoho_profile=None):
        if key:
            return self.facility_types.get(key)
        elif zoho_profile:
            return self.facility_types.get(zoho_profile['Facility'])
        else:
            raise Exception("Need a lookup key or zoho profile")

    def get_by_zoho_address(self, zoho_address):
        for lookup in ('Facility_Add2_City_State_Zip', 'Facility'):
            if lookup in zoho_address:
                key = lookup
                break
        else:
            raise Exception("Lookup key not found")
        return self.matches.get(key)

    def get_by_facility(self, facility):
        return self.facilities.get(facility.id)
