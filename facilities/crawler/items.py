# -*- coding: utf-8 -*-

import scrapy

class FacilityItem(scrapy.Item):
    source = scrapy.Field()
    url = scrapy.Field()
    date = scrapy.Field()
    identifier = scrapy.Field()
    organization = scrapy.Field()
    address1 = scrapy.Field()
    address2 = scrapy.Field()
    address3 = scrapy.Field()
    alternate_names = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
    zip = scrapy.Field()
    phone = scrapy.Field()
    extra = scrapy.Field()
    administrator = scrapy.Field()
    operator = scrapy.Field()
    type = scrapy.Field()
    general = scrapy.Field()
