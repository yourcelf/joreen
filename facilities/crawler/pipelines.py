# -*- coding: utf-8 -*-
from scrapy.exceptions import DropItem
from collections import defaultdict

class FacilitiesPipeline(object):
    def process_item(self, item, spider):
        return item

class RemoveDuplicates(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        ident = (item['identifier'], item['organization'], item['state'])
        if ident in self.ids_seen:
            raise DropItem("Duplicate item found: {}".format(ident))
        else:
            self.ids_seen.add(ident)
            return item

