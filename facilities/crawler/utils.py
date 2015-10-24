import os
import re
import json
from fuzzywuzzy import fuzz
from addresscleaner.us_states import STATES_NORMALIZED

replacements = {
    u"\xa0": " ",
    u"\u2013": "-"
}
def e(sel):
    val = "".join(sel.extract()).strip()
    for fro, to in replacements.iteritems():
        val = val.replace(fro, to)
    return val

phone_number_re = re.compile("(\(?\d{3}\)?\s*-?\s*\d{3}\s*-?\s*\d{4})")
texas_unit_type_re = re.compile(" (Unit|Complex|Transfer Facility|Prison|State Jail|Medical Facility|Geriatric Facility|Correctional (Center|Facility)|Treatment( Facility)?)$", re.I)

