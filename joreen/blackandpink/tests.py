from django.test import TestCase
from django.core.exceptions import ValidationError

from blackandpink import zoho
from blackandpink.blackandpink import Address, Profile
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


class TestAddressParsing(TestCase):
    def test_po_box_recipient_split(self):
        a = Address.from_zoho(
            {
                "Address_1_Facility": "F.C.I. #1",
                "Address_2": "P.O. Box 3725",
                "Address_4": "",
                "City": "Adelanto",
                "DOC_Unit_Name": "",
                "Facility_Add2_City_State_Zip": "F.C.I. #1; P.O. Box 3725; Adelanto, CA 92301",
                "Facility_Chapter_Affiliation": "[]",
                "Facility_Type": "",
                "ID": "1118888000001338038",
                "Mailing_Address_Date_Current": "...",
                "Money_Sending_Option": "[]",
                "State": "CA",
                "Zip": "92301",
            }
        )
        self.assertEquals(
            dict(a.tag()),
            {
                "Recipient": "F.C.I. #1",
                "USPSBoxID": "3725\n",
                "USPSBoxType": "P.O. Box",
                "PlaceName": "Adelanto",
                "StateName": "CA",
                "ZipCode": "92301",
            },
        )

    def test_tag_texas_address(self):
        self.assertEquals(
            dict(
                Address(
                    name="Reception And Medical Center West Unit",
                    address1="P.O. Box 628",
                    address2="Hwy 231",
                    city="Lake Butler",
                    state="FL",
                    zip="32054-0628",
                ).tag()
            ),
            {
                "Recipient": "Reception And Medical Center West Unit",
                "USPSBoxType": "P.O. Box",
                "USPSBoxID": "628\n",
                "StreetNamePreType": "Hwy",
                "StreetName": "231\n",
                "PlaceName": "Lake Butler",
                "StateName": "FL",
                "ZipCode": "32054-0628",
            },
        )


class TestAddressMatching(TestCase):
    fixtures = ["facilities"]

    def check_address_match(self, zoho, facility, expected_breakdown):
        a1 = Address.from_zoho(zoho)
        a2 = Address.from_facility(facility)
        score, breakdown = a1.compare(a2)
        # print([a1.name, a2.name], breakdown)
        self.assertEquals(dict(breakdown), expected_breakdown)

    def mod(self, dct, update):
        newdict = {}
        newdict.update(dct)
        newdict.update(update)
        return newdict

    def test_byrd(self):

        byrd_unit_zoho = {
            "Address_1_Facility": "Byrd Unit",
            "Address_2": "21 FM 247",
            "Address_4": "",
            "City": "Huntsville",
            "DOC_Unit_Name": "Byrd",
            "Facility_Add2_City_State_Zip": "Byrd Unit; 21 FM 247; Huntsville, TX \xa0"
            "77320",
            "Facility_Chapter_Affiliation": "[]",
            "Facility_Type": "",
            "ID": "1118888000000185267",
            "Mailing_Address_Date_Current": "...",
            "Money_Sending_Option": "[Western Union Online, Jpay]",
            "State": "TX",
            "Zip": "\xa077320",
        }

        byrd_unit_facility = Facility.objects.get(name='James "Jay" H. Byrd Unit')

        self.check_address_match(
            byrd_unit_zoho,
            byrd_unit_facility,
            {
                "AddressNumber": 100,
                "StreetName": 100,
                "StreetNamePreType": 100,
                "city": 100,
                "name": 100,
                "street_total": 100,
            },
        )
        # Mismatched zip
        self.check_address_match(
            self.mod(byrd_unit_zoho, {"Zip": "12345"}),
            byrd_unit_facility,
            {
                "city": 100,
                "street_total": 100.0,
                "name": 100,
                "StreetName": 100,
                "StreetNamePreType": 100,
                "AddressNumber": 100,
                "fatal": "Mismatched zip",
            },
        )

        # Empty facility name
        self.check_address_match(
            self.mod(byrd_unit_zoho, {"Address_1_Facility": ""}),
            byrd_unit_facility,
            {"Missing key Recipient": 0},
        )

        # Empty state
        self.check_address_match(
            self.mod(byrd_unit_zoho, {"State": ""}),
            byrd_unit_facility,
            {"Missing key StateName": 0},
        )

        # Bad zip parsing
        self.assertRaises(
            ValidationError,
            lambda: Address.from_zoho(
                self.mod(byrd_unit_zoho, {"Zip": "1234"})
            ).validate(),
        )
        self.assertRaises(
            ValidationError,
            lambda: Address.from_zoho(self.mod(byrd_unit_zoho, {"Zip": ""})).validate(),
        )

    def test_apalachee(self):
        apalachee_east_zoho = {
            "Address_1_Facility": "Apalachee Corr.- East",
            "Address_2": "35 Apalachee Drive",
            "Address_4": "",
            "City": "Sneads",
            "DOC_Unit_Name": "",
            "Facility_Add2_City_State_Zip": "Apalachee Corr.- East; 35 Apalachee Drive; "
            "Sneads, FL \xa032460",
            "Facility_Chapter_Affiliation": "[]",
            "Facility_Type": "",
            "ID": "1118888000000181483",
            "Mailing_Address_Date_Current": "...",
            "Money_Sending_Option": "[Western Union Online, Jpay]",
            "State": "FL",
            "Zip": "\xa032460",
        }
        apalachee_east_facility = Facility.objects.get(
            name="Apalachee Correctional Institution East"
        )

        self.check_address_match(
            apalachee_east_zoho,
            apalachee_east_facility,
            {
                "AddressNumber": 100,
                "StreetName": 100,
                "StreetNamePostType": 100,
                "city": 100,
                "name": 100,
                "street_total": 100,
            },
        )

        # Wrong street number
        self.check_address_match(
            self.mod(apalachee_east_zoho, {"Address_2": "36 Apalachee Drive"}),
            apalachee_east_facility,
            {
                "AddressNumber": 0,
                "fatal": "Mismatched AddressNumber",
                "city": 100,
                "name": 100,
                "street_total": 0,
            },
        )

    def test_avenal(self):
        avenal_zoho = {
            "Address_1_Facility": "Avenal SP (ASP)",
            "Address_2": "PO Box 9",
            "Address_4": "",
            "City": "Avenal",
            "DOC_Unit_Name": "",
            "Facility_Add2_City_State_Zip": "Avenal SP (ASP); PO Box 9; Avenal, CA \xa0"
            "93204",
            "Facility_Chapter_Affiliation": "[]",
            "Facility_Type": "State",
            "ID": "1118888000000180787",
            "Mailing_Address_Date_Current": "...",
            "Money_Sending_Option": "[Western Union Online, Access Corrections, JPay]",
            "State": "CA",
            "Zip": "\xa093204",
        }
        avenal_facility = Facility.objects.get(
            name="Avenal State Prison", address1="PO Box 9"
        )

        self.check_address_match(
            avenal_zoho,
            avenal_facility,
            {
                "USPSBoxID": 100,
                "USPSBoxType": 100,
                "city": 100,
                "name": 100,  # via parenthetical abbreviation alternate name
                "street_total": 100,
            },
        )

    def test_fci_num_1(self):
        fci_num_1 = {
            "Address_1_Facility": "F.C.I. #1",
            "Address_2": "P.O. Box 3725",
            "Address_4": "",
            "City": "Adelanto",
            "DOC_Unit_Name": "",
            "Facility_Add2_City_State_Zip": "F.C.I. #1; P.O. Box 3725; Adelanto, CA 92301",
            "Facility_Chapter_Affiliation": "[]",
            "Facility_Type": "",
            "ID": "1118888000001338038",
            "Mailing_Address_Date_Current": "...",
            "Money_Sending_Option": "[]",
            "State": "CA",
            "Zip": "92301",
        }
        vim = Facility.objects.get(code="VIM")
        dvmccf = Facility.objects.get(code="DVMCCF")

        self.check_address_match(
            fci_num_1,
            vim,
            {
                "USPSBoxID": 100,
                "USPSBoxType": 100,
                "city": 100,
                "name": 24,
                "street_total": 100.0,
            },
        )
        self.check_address_match(
            fci_num_1,
            dvmccf,
            {
                "city": 100,
                "name": 17,
                "street_total": 0,
                "USPSBoxID": 0,
                "fatal": "Mismatched USPSBoxID",
            },
        )

    def test_san_quentin(self):
        san_quentin_zoho = {
            "Address_1_Facility": "San Quentin S. P.",
            "Address_2": "",
            "Address_4": "",
            "City": "San Quentin",
            "DOC_Unit_Name": "",
            "Facility_Add2_City_State_Zip": "San Quentin S. P.; ; San Quentin, CA 94974",
            "Facility_Chapter_Affiliation": "[San Francisco]",
            "Facility_Type": "State",
            "ID": "1118888000000201003",
            "Mailing_Address_Date_Current": "...",
            "Money_Sending_Option": "[Western Union Online, Access Corrections, JPay]",
            "State": "CA",
            "Zip": "94974",
        }
        self.check_address_match(
            san_quentin_zoho,
            Facility.objects.get(name="San Quentin State Prison"),
            {"city": 100, "name": 79, "street_total": 77, "address1": 77},
        )
