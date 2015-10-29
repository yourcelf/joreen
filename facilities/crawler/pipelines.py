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
        # California has same identifier, same name, same state, multiple
        # addresses.  So we need address lines in our identifier.
        ident = (item['identifier'], item['organization'], item['state'],
                 item.get('address1') or '', item.get('address2') or '')
        if ident in self.ids_seen:
            raise DropItem("Duplicate item found: {}".format(ident))
        else:
            self.ids_seen.add(ident)
            return item

