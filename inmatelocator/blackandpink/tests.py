from django.test import TestCase

from blackandpink import zoho
from blackandpink.blackandpink import Address
from facilities.models import Facility

class TestFetchZoho(TestCase):
    def test_fetch_profiles(self):
        res = zoho.fetch_all_profiles()
        self.assertTrue(len(res) > 10000)
        for key in ("B_P_Member_Number", "Facility", "Facility.Address_1_Facility"):
            self.assertTrue(key in res[0])

    def test_fetch_facilities(self):
        res = zoho.fetch_all_facilities()
        self.assertTrue(len(res) > 2000)
#        for r in res:
#            if r['State'] == 'CA':
#                import pprint ; pprint.pprint(r)

class TestAddressMatching(TestCase):
    fixtures = ['facilities']
    def check_address_match(self, zoho, facility, expected_score, expected_breakdown):
        a1 = Address.from_zoho(zoho)
        a2 = Address.from_facility(facility)
        score, breakdown = a1.compare(a2)
        self.assertEquals(dict(breakdown), expected_breakdown)
        self.assertEquals(score, expected_score)

    def test_address_matching(self):
        def mod(dct, update):
            newdict = {}
            newdict.update(dct)
            newdict.update(update)
            return newdict

        byrd_unit_zoho = {
            'Address_1_Facility': 'Byrd Unit',
            'Address_2': '21 FM 247',
            'City': 'Huntsville',
            'DOC_Unit_Name': 'Byrd',
            'Facility_Add2_City_State_Zip': 'Byrd Unit; 21 FM 247; Huntsville, TX \xa0'
                                            '77320',
            'Facility_Chapter_Affiliation': '[]',
            'Facility_Type': '',
            'ID': '1118888000000185267',
            'Mailing_Address_Date_Current': '...',
            'Money_Sending_Option': '[Western Union Online, Jpay]',
            'State': 'TX',
            'Zip': '\xa077320'
        }

        byrd_unit_facility = Facility.objects.get(name='James "Jay" H. Byrd Unit')
        apalachee_east_zoho = {
            'Address_1_Facility': 'Apalachee Corr.- East',
            'Address_2': '35 Apalachee Drive',
            'City': 'Sneads',
            'DOC_Unit_Name': '',
            'Facility_Add2_City_State_Zip': 'Apalachee Corr.- East; 35 Apalachee Drive; '
                                            'Sneads, FL \xa032460',
            'Facility_Chapter_Affiliation': '[]',
            'Facility_Type': '',
            'ID': '1118888000000181483',
            'Mailing_Address_Date_Current': '...',
            'Money_Sending_Option': '[Western Union Online, Jpay]',
            'State': 'FL',
            'Zip': '\xa032460'}
        apalachee_east_facility = Facility.objects.get(
                name='Apalachee Correctional Institution East')

        avenal_zoho = {'Address_1_Facility': 'Avenal SP (ASP)',
            'Address_2': 'PO Box 9',
            'City': 'Avenal',
            'DOC_Unit_Name': '',
            'Facility_Add2_City_State_Zip': 'Avenal SP (ASP); PO Box 9; Avenal, CA \xa0'
                                            '93204',
            'Facility_Chapter_Affiliation': '[]',
            'Facility_Type': 'State',
            'ID': '1118888000000180787',
            'Mailing_Address_Date_Current': '...',
            'Money_Sending_Option': '[Western Union Online, Access Corrections, JPay]',
            'State': 'CA',
            'Zip': '\xa093204'}
        avenal_facility = Facility.objects.get(name="Avenal State Prison",
                address1="PO Box 9")


        matches = [
            (byrd_unit_zoho, byrd_unit_facility, 100, {
                'name': 100, 'address1': 100, 'street_total': 100, 'city': 100
            }),
            (apalachee_east_zoho, apalachee_east_facility, 100, {
                'AddressNumber': 100,
                'StreetName': 100,
                'StreetNamePostType': 100,
                'city': 100,
                'name': 100, 'street_total': 100
            }),
            (avenal_zoho, avenal_facility, 86.33333333333333333, {
                'USPSBoxID': 100,
                'USPSBoxType': 100,
                'city': 100,
                'name': 59,
                'street_total': 100
            }),

            # Mismatched zip
            (mod(byrd_unit_zoho, {'Zip': '12345'}), byrd_unit_facility, 0, {
                'mismatched zip': 0
            }),

            # Empty facility name
            (mod(byrd_unit_zoho, {'Address_1_Facility': ''}), byrd_unit_facility, 0, {
                'Missing key Recipient': 0
            }),

            # Empty state
            (mod(byrd_unit_zoho, {'State': ''}), byrd_unit_facility, 0, {
                'Missing key StateName': 0
            }),

            # Wrong street number
            (mod(apalachee_east_zoho, {'Address_2': '36 Apalachee Drive'}),
             apalachee_east_facility, 66.666666666666667, {
                 'mismatched AddressNumber': 0,
                 'city': 100,
                 'name': 100,
                 'street_total': 0
            }),
        ]
        self.assertRaises(ValueError,
                lambda: Address.from_zoho(mod(byrd_unit_zoho, {'Zip': '1234'})))
        self.assertRaises(ValueError,
                lambda: Address.from_zoho(mod(byrd_unit_zoho, {'Zip': ''})))

        for zoho, facility, score, breakdown in matches:
            self.check_address_match(zoho, facility, score, breakdown)

        
class TestMatchingFacilities(TestCase):
    fixtures = ['facilities']

    def test_find_matching_facilities(self):
        zoho_facilities = zoho.fetch_all_facilities() 
        for zoho_facility in zoho_facilities:
            if "Personal" in zoho_facility.get('Facility_Type', ''):
                continue
            try:
                address = Address.from_zoho(zoho_facility)
            except ValueError:
                continue

            if address.state in ("CA", "TX", "PA", "NY", "FL"):
                zoho_address = Address.from_zoho(zoho_facility)
                score, breakdown, facility = zoho_address.find_matching_facility()
                if facility is None:
                    print()
                    print(zoho_address.flatten())
                elif score < 90:
                    pass
                    #print(score, breakdown, facility)
                    #for key, val in score.items():
                    #    if val < 100:


