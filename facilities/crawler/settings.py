# -*- coding: utf-8 -*-

# Scrapy settings for facilities crawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'facilities.crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'facilities (+http://www.yourdomain.com)'

DOWNLOADER_MIDDLEWARES = {
  "scrapy.extensions.donwloadermiddleware.httpcache.HttpCacheMiddleware": None
}
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"
HTTPCACHE_POLICY = "scrapy.extensions.httpcache.DummyPolicy"
HTTPCACHE_ENABLED = True

ITEM_PIPELINES = {
    'crawler.pipelines.FacilitiesPipeline': 300,
    'crawler.pipelines.RemoveDuplicates': 500
}
