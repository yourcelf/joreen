SCRAPY=venv/bin/scrapy crawl
SCRAPY_ARGS=--loglevel WARNING -t json -o -

all: california federal florida newyork pennsylvania texas illinois

california:
	$(SCRAPY) california $(SCRAPY_ARGS)

federal:
	$(SCRAPY) federal $(SCRAPY_ARGS)

florida:
	$(SCRAPY) florida $(SCRAPY_ARGS)

newyork:
	$(SCRAPY) newyork $(SCRAPY_ARGS)

pennsylvania:
	$(SCRAPY) pennsylvania $(SCRAPY_ARGS)

texas:
	$(SCRAPY) texas $(SCRAPY_ARGS)

illinois:
	$(SCRAPY) illinois $(SCRAPY_ARGS)
