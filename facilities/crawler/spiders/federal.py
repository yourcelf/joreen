import json
import scrapy
from crawler.items import FacilityItem
from crawler.utils import e
import re
import datetime
from urlparse import urljoin
from addresscleaner import parse_address, format_address
import logging

class FederalSpider(scrapy.Spider):
    name = "federal"
    allowed_domains = ["www.bop.gov"]
    start_urls = ["http://www.bop.gov/locations/list.jsp"]
    download_delay = 1

    def parse(self, response):
        anchors = response.xpath('//a')
        for a in anchors:
            href = e(a.xpath('./@href'))
            url = urljoin(response.url, href)
            match = re.search("/locations/[^/]+/([^/]+)/?$", url)
            if match:
                code = match.group(1).upper()
                # The URLs append "O" to the end of some offices.
                if len(code) == 4 and code[-1] == "O":
                    code = code[0:3]
                item = FacilityItem()
                item['source'] = "crawler"
                item['identifier'] = code
                item['url'] = "http://www.bop.gov/PublicInfo/execute/phyloc?todo=query&output=json&code={}".format(code)
                request = scrapy.Request(item['url'], callback=self.parse_institution)
                request.meta['item'] = item
                yield request
            elif re.search("/locations/search.jsp", url):
                request = scrapy.Request(url, callback=self.parse)
                yield request

    def parse_institution(self, res):
        data = json.loads(res.body)
        item = res.meta['item']
        item['administrator'] = "Federal Bureau of Prisons"
        item['operator'] = "Federal Bureau of Prisons"
        item['alternate_names'] = [item['identifier']]
        for i,location in enumerate(data['Locations']):
            if i == 0:
                item['organization'] = location['nameTitle']
            else:
                item['alternate_names'].append(location['nameTitle'])
            item['alternate_names'].append(location['name'])
            item['alternate_names'].append(location['nameDisplay'])

        if 'organization' not in item or not item['organization']:
            raise Exception("Location nameTitle not found in ``{}``".format(res.body))

        addresses = data['Addresses']
        addresses_by_type = dict([(a['addressTypeName'], a) for a in addresses])
        address = addresses_by_type.get("Inmate Mail/Parcels",
                addresses_by_type.get("Physical Address"))

        if address:
            item['type'] = address.get('faclTypeDescription', '')
            item['address1'] = address['street']
            if address.get('street2'):
                item['address2'] = address['street2']
            item['city'] = address['city'].title()
            item['state'] = address['state']
            item['zip'] = address['zipCode']
        else:
            logging.warning(
                "Inmate Mail/Parcels address not found for federal institution {}, available types: {}".format(
                    item['identifier'], addresses_by_type.keys()
                )
            )
            item['state'] = ''
        return item
