# -*- coding: utf-8 -*-

import re
import scrapy
import datetime
from crawler.items import FacilityItem
from crawler.utils import e, texas_unit_type_re
from urlparse import urljoin
import probablepeople

alternate_name_map = {
    "Carole S. Young Medical Facility": ["CAROL YOUNG COMPLEX"],
    "Christina Melton Crain Unit": ["Crain Unit - Women's Prison"],
    "Diboll Correctional Center": ["DIBOLL PRIV"],
    "East Texas Multi-Use Facility": ["EAST TEXAS TREATMENT FACILITY"],
    "Hospital Galveston": ["HOSPITAL-GALV", "GALVESTON"],
    "Beauford H. Jester I Unit": ["JESTER I"],
    "Beauford H. Jester II Unit": ["JESTER II"],
    "Beauford H. Jester III Unit": ["JESTER III"],
    "Beauford H. Jester IV Unit": ["JESTER IV"],
    "Billy Moore Correctional Center": ["BMCC"],
    "Joe F. Gurney Transfer Facility": ["JOE F GURNEY"],
    "Joe Kegans State Jail": ["KEGANS STATE J"],
    "John R. Lindsey State Jail": ["LINDSEY SJ"],
    "Lockhart Correctional Facility": ["LOCKHART PRIV P"],
    "T3": ["LOCKHART WORK FAC"],
    "Wallace Pack Unit": ["PACK I"],
    "Lucile Plane State Jail": ["PLANE JAIL"],
    "W. F. Ramsey Unit": ["RAMSEY I"],
    "T.L. Roach Unit": ["ROACH BT CAMP"],
    "South Texas Intermediate Sanction Facility": ["SOUTH TEXAS ISF"],
    "Travis County State Jail": ["TRAVIS JAIL"],
    "John Montford Unit": ["West Texas Hospital", "WEST TEXAS HOSP"],
    "West Texas Intermediate Sanction Facility": ["WEST TEXAS ISF"],
    "Willacy County State Jail": ["WILLACY"],
    "Linda Woodman State Jail": ["WOODMAN SJ"],
}


class TexasSpider(scrapy.Spider):
    name = "texas"
    allowed_domains = ["tdcj.state.tx.us"]
    start_urls = ["http://tdcj.state.tx.us/unit_directory/index.html"]
    download_delay = 5

    def alternate_names(self, item):
        """
        Texas names their prisons after people, and then uses permutations of
        first/middle/last, nicknames, and initials when refering to them in
        different places. Ugh.
        """
        name = item['organization']
        alts = alternate_name_map.get(item['identifier'], alternate_name_map.get(item['organization'], []))

        # Skip out for non-person named things
        if "Texas" in name or name == "Hospital Galveston" or "T3" == item['identifier']:
            return alts

        def add_suffixes(name_variants):
            suffixed = []
            for name in name_variants:
                suffixed.append(name)
                suffixed.append(u'{} Unit'.format(name))
                suffixed.append(u'{} Prison'.format(name))
            return suffixed

        # Remove the unit suffix -- we'll add all variants with suffix later.
        name = texas_unit_type_re.sub("", name)

        # For single words, just add suffixes and exit.
        if len(name.split()) == 1:
            alts += add_suffixes([name])
            return alts

        # Parse the names into parts.  Special case some names that
        # probablepeople doesn't do right.
        if name == "Price Daniel":
            parsed = {'Surname': 'Daniel', 'GivenName': 'Price'}
        elif name == "O.L. Luther":
            parsed = {'Surname': 'Luther', 'FirstInitial': 'O', 'MiddleInitial': 'L'}
        elif name == "Reverend C.A. Holliday":
            parsed = {"PrefixOther": "Reverend", "FirstInitial": "C", "MiddleInitial": "A",
                    "Surname": "Holliday"}
        else:
            parsed, ntype  = probablepeople.tag(name)
            if ntype != "Person":
                raise Exception("probablepeople tagged an unexpected name type `{}` for `{}`".format(ntype, name))

        name_set = set([name])
        if 'Surname' in parsed:
            name_set.add(parsed['Surname'])

            if 'GivenName' in parsed or 'FirstInitial' in parsed:
                first = parsed.get('GivenName', parsed.get('FirstInitial'))
                # First initial, last name
                name_set.add(u"{} {}".format(first[0], parsed['Surname']))
                # Regular first/last
                name_set.add(u"{} {}".format(first, parsed['Surname']))

                # First and last w/o initial
                if 'MiddleInitial' in parsed or 'MiddleName' in parsed:
                    name_set.add(u"{} {}".format(first, parsed['Surname']))

            # Add nickname - lastname.
            if 'Nickname' in parsed:
                name_set.add(u"{} {}".format(
                    re.sub('[^a-zA-Z]', '', parsed['Nickname']),
                    parsed['Surname']))

        else:
            raise Exception("Too few name parts for {}, ``{}``".format(name, parsed))

        # Special case for name-changing nicknames
        if parsed.get('Surname') == "Clements":
            name_set.add("Bill Clements") # nickname

        # Add the unit/prison suffixes onto the names.
        alts += add_suffixes(name_set)

        return alts

    def parse(self, response):
        for row in response.css('table.os tr'):
            tds = row.css('td')
            # Catch interstitials and headers
            if len(tds) < 7:
                continue

            name, unit, operator, gender, ptype, region, county = [
                e(td.css('::text')) for td in tds
            ]
            name = name.replace('*', '')

            url = urljoin(response.url, e(tds[0].xpath('.//a/@href')))

            item = FacilityItem()
            item['source'] = "crawler"
            item['administrator'] = "Texas"
            item['operator'] = {
                    "CCA": "Corrections Corporation of America",
                    "CID": "TDCJ Correctional Institutions Division",
                    "GEO": "The GEO Group, Inc.",
                    "MTC": "Management and Training Corporation"
            }[operator]
            type_map = {
                "ISF": "Intermediate Sanction Facility",
                "DDP": "Developmental Disabilities Program",
                "PPT": "Pre-Parole Transfer Facility",
                "SAFPF": "Substance Abuse Felony Punishment Facility"
            }
            item['type'] = ptype
            for acronym, expansion in type_map.iteritems():
                item['type'] = item['type'].replace(acronym, expansion)

            item['url'] = url
            item['date'] = datetime.datetime.utcnow().isoformat()
            item['identifier'] = unit

            # This doesn't help, just gets in the way.
            #item['extra'] = {
            #    "operator": operator, "gender": gender, "type": ptype,
            #    "region": region, "county": county
            #}

            request = scrapy.Request(url, callback=self.parse_facility_page)
            request.meta['item'] = item
            yield request

    def parse_facility_page(self, response):
        item = response.meta['item']
        rows = response.css("table tr")

        address_text = None
        name_text = None
        for row in rows:
            tds = row.css("td")
            if len(tds) == 2:
                if e(tds[0].css('::text')) == "Unit Full Name:":
                    name_text = e(tds[1].css('::text'))
                if e(tds[0].css('::text')) == "Unit Address and Phone Number:":
                    address_text = e(tds[1].css('::text'))
        if address_text is None:
            raise Exception(u"Null address text for " + response.url)
        if name_text is None:
            raise Exception(u"Null name text for " + response.url)

        match = re.match("^(.*?)[\s\n]+(\(\d{3}\)\s\d{3}-\d{4}).*$", address_text)
        if match:
            address = match.group(1).strip()
            phone = match.group(2).strip()
        else:
            raise Exception(u"Unmatched address/phone: ``{}``".format(text))

        address_items = []
        if " / " in name_text:
            # Ugh - special case where the directory lists two institutions in
            # one.
            item2 = FacilityItem()
            item2['source'] = item['source']
            item2['url'] = item['url']
            item2['date'] = item['date']
            item2['administrator'] = item['administrator']
            item2['operator'] = item['operator']
            item['identifier'], item2['identifier'] = item['identifier'].split(' / ')
            item['organization'], item2['organization'] = name_text.split(' / ')
            if " / " in item['type']:
                item['type'], item2['type'] = item['type'].split(" / ")
            else:
                item2['type'] = item['type']
            
            address_parts = address.split(" / ")
            address_items.append((item, address_parts[0]))
            address_items.append((item2, address_parts[1]))
        else:
            item['organization'] = name_text
            address_items.append((item, address))


        for item, address in address_items:
            item['organization'] = re.sub('\s+', ' ', item['organization'])
            item['alternate_names'] = self.alternate_names(item)
            parts = [p.strip() for p in address.split(", ")]
            if len(parts) == 3:
                a, c, sz = parts
                a2 = None
            elif len(parts) == 4:
                a, a2, c, sz = parts
            else:
                raise Exception("Unmatched parts: {}".format(address))
            item['address1'] = a
            item['city'] = c
            item['state'] = sz.split()[0]
            if item['state'] != "TX":
                raise Exception("Bad state: {} (from `{}`)".format(item['state'], text))
            item['zip'] = sz.split()[1]
            item['phone'] = phone
            yield item
