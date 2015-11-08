import scrapy
from crawler.items import FacilityItem
from crawler.utils import e, phone_number_re
import re
import datetime
from urlparse import urljoin
from addresscleaner import parse_address, format_address

alternate_names = {
    'Apalachee Correctional Institution East': ['APALACHEE EAST UNIT'],
    'Apalachee Correctional Institution West': ['APALACHEE WEST UNIT'],
    'Baker Re-Entry Center': ['BAKER RE-ENTRY CENTR'],
    'Berrydale Forestry Camp': ['BERRYDALE FRSTRY CMP'],
    'Blackwater River Correctional Facility': ['BLACKWATER C.F.'],
    'Bridges Of Jacksonville': ['BRIDGES OF JACKSONVI'],
    'Central Florida Reception Center': ['CFRC-MAIN'],
    'Central Florida Reception Center East Unit': ['CFRC-EAST'],
    'Central Florida Reception Center South Unit': ['CFRC-SOUTH'],
    'Columbia Correctional Institution Annex': ['COLUMBIA ANNEX'],
    'Cross City Correctional Institution': ['CROSS CITY EAST UNIT'],
    'Everglades Re-Entry Center': ['EVERGLADES RE-ENTRY'],
    "Florida Women's Reception Center": ['FL.WOMENS RECPN.CTR'],
    'Florida State Prison': ['FSP'],
    'Florida State Prison West Unit': ['FSP West Unit'],
    'Franklin Work Camp': ['FRANKLIN CI WORK CMP'],
    'Gadsden Re-Entry Center': ['GADSDEN RE-ENTRY CTR'],
    'Gulf Correctional Institution Annex': ['GULF C.I.- ANNEX'],
    'Hamilton Correctional Institution Annex': ['HAMILTON ANNEX'],
    'Lancaster Work Camp': ['LANCASTER W.C.'],
    'Liberty Work Camp - South Unit': ['LIBERTY SOUTH UNIT'],
    'Lowell Correctional Institution Annex': ['LOWELL ANNEX'],
    'Northwest Florida Reception Center': ['NWFRC', 'NWFRC Main Unit', 'NWFRC MAIN UNIT.'],
    'Northwest Florida Reception Center Annex': ['NWFRC Annex', 'NWFRC ANNEX.'],
    'Okeechobee Correctional Institution': ['OKEECHOBEE WORK CAMP'],
    'Rmc Work Camp': ['R.M.C WORK CAMP'],
    'Reception And Medical Center': ['R.M.C.- MAIN UNIT'],
    'Reception And Medical Center West Unit': ['R.M.C.- WEST UNIT'],
    'Re-Entry Center Of Ocala': ['REENTRY CTR OF OCALA'],
    'Santa Rosa Correctional Institution Annex': ['SANTA ROSA ANNEX'],
    'South Florida Reception Center': ['S.F.R.C.'],
    'South Florida Reception Center South Unit': ['S.F.R.C SOUTH UNIT'],
    'Sago Palm Re-Entry Center': ['SAGO PALM RE-ENTRY C'],
    'Santa Rosa Work Camp': ['SANTA ROSA WORK CMP'],
    'St. Petersburg Community Release Center': ['ST. PETE C.R.C.'],
    'Sumter Correctional Institution': ['SUMTER  C.I.'],
    'Sumter Basic Training Unit': ['SUMTER B.T.U.'],
    'Suncoast Community Release Center': ['SUNCOAST C.R.C.(FEM)'],
    'Suwannee Correctional Institution': ['SUWANNEE C.I'],
    'Tallahassee Community Release Center': ['TALLAHASSEE C.R.C'],
    'Taylor Correctional Institution Annex': ['TAYLOR ANNEX'],
    'Tomoka Crc - 285': ['TOMOKA CRC-285'],
    'Tomoka Crc - 298': ['TOMOKA CRC-298'],
    'Tth Of Tarpon Springs': ['TTH OF TARPON SPRING'],
    'Union Correctional Work Camp': ['UNION WORK CAMP'],
    'Wakulla Correctional Institution Annex': ['WAKULLA ANNEX'],
    'West Palm Beach Community Release Center': ['W.PALM BEACH C.R.C.'],
}

common_abbreviations = {
    'Correctional Institution': 'C.I.',
    'Correctional Facility': 'C.F.',
    'Community Release Center': 'C.R.C.',
    'Road Prison': 'R.P.',
    'Work Camp': 'W.C.'
}

class FloridaSpider(scrapy.Spider):
    name = "florida"
    allowed_domains = ["www.dc.state.fl.us"]
    start_urls = ["http://www.dc.state.fl.us/orginfo/facilitydir.html"]
    download_delay = 1

    def get_alternate_names(self, name):
        alts = []
        if name in alternate_names:
            alts = alts + alternate_names[name]

        for find, replace in common_abbreviations.items():
            if find in name:
                alts.append(name.replace(find, replace))

        alts = list(set(alts))
        return alts

    def is_facility(self, td):
        text = e(td.xpath('.//text()'))
        if "501 South Calhoun Street" in text:
            return False

        anchors = td.xpath('.//a')
        # Return true if there's a link to a facility in it.
        for a in anchors:
            href = e(a.xpath('./@href'))
            if re.match("^/facilities/[^\/]+/\d+\.html$", href):
                return True

        text = "\n".join(t.strip() for t in text.split("\n") if t.strip())
        # Return false if there's no address
        if not re.search("(Florida|FL),?\s+\d{5}(-\d{4})?", text):
            return False

        # Return true if it has a facility number.
        name = text.split("\n")[0]
        if re.search("^[0-9a-f]{3} ", name, re.I):
            return True
        if "(Male)" in name or "(Female)" in name:
            return True
        
        # Return false if it looks like an office or a idrector
        if re.search("(?<!Post )Office", text):
            return False
        if "Director" in text:
            return False

        return True

    def filter_lines(self, text):
        """
        Given the text from a result, filter out all lanes and parts that are
        not part of an address.
        """
        kept = []
        annexes = []
        lines = text.split("\n")
        for line in lines:
            line = re.sub('\s+', ' ', line)
            line = line.strip()
            # Remove asterix prefixes
            line = re.sub('^\*\s*', '', line)
            # Remove (Male), (Female), (Male Youth), (Female, Youth)
            line = re.sub("\((Fem|M)ale(,? Youth)?\)", "", line).strip()
            # Check for whether this is an indication of an annex
            annex_match = re.match("^(Annex|(West|South|East|North) Unit(?! Fax)).*", line)
            if not line or line.lower() == "(contract facility)":
                continue
            elif annex_match:
                annex = kept[::]
                if line == "South Unit:" and kept[0] == "South Florida Reception Center":
                    # Special case for a result that reformulates the whole
                    # address. Start over with address lines here.
                    annexes.append(kept)
                    kept = annex[:1]
                    kept[0] = kept[0] + " South Unit"
                else:
                    # Set the name as facility + annex/south unit/etc
                    annex[0] = u" ".join((annex[0], annex_match.group(1)))


                    # Check if we have a new address to sub in
                    parts = line.split(": ")
                    if len(parts) > 1 and not phone_number_re.search(parts[1]):
                        annex[1] = parts[1].strip()
                    annexes.append(annex)
            elif (phone_number_re.search(line) or
                  re.search("^Fax: \(\d\d\d\)", line) or
                  re.match("^\d{3}-\d{4}$", line)):

                continue
            elif line == "Mailing Address:" or line == "or:":
                kept = kept[:1]
            else:
                kept.append(line)
        annexes.insert(0, kept)
        return annexes

    def parse(self, response):
        facility_text = []
        for td in response.xpath('//td'):
            if not self.is_facility(td):
                continue
            text = e(td.xpath('.//text()'))
            units = self.filter_lines(text)
            for unit in units:
                name_line, address_lines = unit[0], unit[1:]
                item = FacilityItem()
                item['administrator'] = "Florida"
                item['operator'] = "Florida Department of Corrections"
                item['source'] = "crawler"
                anchors = td.xpath('.//a')
                # Match listings that have a 3-digit identifier followed by a
                # name.  These are all probation offices or other non-prisons
                # (e.g. they don't house people).
                id_name_match = re.match("^(\d\d[a-z\d])\s*-?\s*(.*)$", name_line, re.I)
                if id_name_match:
                    #print "Skipping {}".format(name_line)
                    continue
                else:
                    item['organization'] = name_line
                    if len(anchors) > 0:
                        for annex_term in ("Annex", "South Unit", "East Unit", "West Unit"):
                            if annex_term in text:
                                for anchor in anchors:
                                    text = e(anchor.xpath('./text()'))
                                    href = e(anchor.xpath('./@href'))
                                    anchor_name = e(anchor.xpath('./@name'))
                                    if annex_term in text:
                                        break
                        else:
                            text = e(anchors[0].xpath('./text()'))
                            href = e(anchors[0].xpath('./@href'))
                            anchor_name = e(anchors[0].xpath('./@name'))
                        id_match =  re.match('.*/(\d+).html', href)
                        item['identifier'] = id_match.group(1) if id_match else None
                        item['url'] = u"#".join((response.url, anchor_name))
                    else:
                        item['identifier'] = None

                if not item.get('url'):
                    item['url'] = response.url

                item['organization'] = item['organization'].title()
                # Fix a problem with .title()... argh.
                item['organization'] = item['organization'].replace("Women'S", "Women's")

                item['organization'] = re.sub(r'\bci\b', "Correctional Institution", item['organization'], flags=re.I)
                item['alternate_names'] = self.get_alternate_names(item['organization'])
                address = parse_address(u"\n".join([item['organization']] + address_lines))
                item['address1'] = address['address1']
                if 'address2' in address:
                    item['address2'] = address['address2']
                item['city'] = address['city']
                item['state'] = address['state']
                item['zip'] = address['zip']
                # Special case city/address2 swaps that happen as a result of extra newlines.
                if item['city'] == '' and item['address2']:
                    item['city'], item['address2'] = item['address2'], item['city']

                # Get the type
                if ("Correctional Institution" in item['organization'] or
                      "Correctional Facility" in item['organization'] or
                      "Reception Center" in item['organization'] or
                      "Reception and Medical Center" in item['organization'] or
                      "Reception And Medical Center" in item['organization'] or
                      "State Prison" in item['organization'] or
                      "Desoto Annex" in item['organization'] or
                      "Quincy Annex" in item['organization']):
                    item['type'] = "Correctional Institution"
                elif "Forestry Camp" in item['organization']:
                    item['type'] = "Forestry Camp"
                elif ("Work Camp" in item['organization'] or
                      "Training Unit" in item['organization']):
                    item['type'] = "Work Camp"
                elif "Road Prison" in item['organization']:
                    item['type'] = "Road Prison"
                elif ("Community Release Center" in item['organization'] or
                      "CRC" in item['organization'] or
                      "Crc" in item['organization'] or
                      "Tth" in item['organization'] or
                      "Bridge" in item['organization'] or
                      "SHISA House" in item['organization'] or
                      "Shisa House" in item['organization']):
                    item['type'] = "Community Release Center"
                elif "Re-Entry Center" in item['organization']:
                    item['type'] = "Re-Entry Center"
                else:
                    raise Exception(item['organization'])

                yield item

