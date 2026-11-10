
"""
SSW 567 - Final Group Project, Part 2
Group B - Unit Tests
"""

import unittest
from unittest.mock import patch

from MRTD import scanMRZ, getTravelDocumentData


class TestMRTDInterfaces(unittest.TestCase):

    
    def test_mock_scanner(self):
        # R1: Mock hardware scanning and verify that the
        # returned MRZ strings can be processed by the decoder.
        from MRTD import decodeMRZ

        line1 = "P<USAJAIN<<MAHIMA".ljust(44, "<")
        line2 = (
            "A12345678" + "0" +
            "USA" +
            "990515" + "0" +
            "F" +
            "300630" + "0" +
            "12345678901234" +
            "<" + "0"
        )

        with patch("MRTD.scanMRZ", return_value=(line1, line2)) as mock_scan:
            scanned_line1, scanned_line2 = mock_scan()
            result = decodeMRZ(scanned_line1, scanned_line2)

            mock_scan.assert_called_once_with()
            self.assertEqual(result["passport_number"], "A12345678")
            self.assertEqual(result["nationality"], "USA")

    def test_mock_database(self):
        # R3: Verify the database interface can be mocked
        # to provide travel document information.
        with patch("MRTD.getTravelDocumentData") as mock_db:
            mock_db.return_value = {
                "passport_number": "A12345678",
                "nationality": "USA"
            }

            result = mock_db()

            self.assertEqual(result["passport_number"], "A12345678")
            self.assertEqual(result["nationality"], "USA")


class TestCRC16(unittest.TestCase):

    def test_crc16_known_value(self):
        # Verify CRC-16/ARC against a known reference value.
        from MRTD import calculateCRC16
        self.assertEqual(calculateCRC16("123456789"), 0xBB3D)

    def test_check_digit_known_value(self):
        # Verify the check digit is CRC-16 modulo 10.
        from MRTD import calculateCheckDigit
        self.assertEqual(calculateCheckDigit("123456789"), "3")

    def test_crc16_empty_string(self):
        # Verify that empty input returns the initial checksum.
        from MRTD import calculateCRC16
        self.assertEqual(calculateCRC16(""), 0)

    def test_crc16_invalid_input(self):
        # Verify non-string input is rejected.
        from MRTD import calculateCRC16
        with self.assertRaises(TypeError):
            calculateCRC16(12345)

    def test_crc16_different_inputs(self):
        # Verify that different input strings produce
        # their independently calculated expected checksums.
        from MRTD import calculateCRC16
        self.assertEqual(calculateCRC16("A"), 0x30C0)
        self.assertEqual(calculateCRC16("B"), 0x3180)
    
    def test_crc16_with_filler(self):
        # Verify CRC-16 correctly processes MRZ filler characters.
        from MRTD import calculateCRC16
        self.assertIsInstance(calculateCRC16("ABC<<<<"), int)

    def test_crc16_with_leading_zeros(self):
        # Verify leading zeros affect the checksum correctly.
        from MRTD import calculateCRC16
        self.assertNotEqual(
            calculateCRC16("001234567"),
            calculateCRC16("1234567")
        )

    def test_crc16_none_input(self):
        # Verify None is rejected as an invalid input type.
        from MRTD import calculateCRC16
        with self.assertRaises(TypeError):
            calculateCRC16(None)

    def test_crc16_list_input(self):
        # Verify list input is rejected.
        from MRTD import calculateCRC16
        with self.assertRaises(TypeError):
            calculateCRC16(["A", "B"])

    def test_crc16_non_ascii(self):
        # Verify non-ASCII characters are rejected.
        from MRTD import calculateCRC16
        with self.assertRaises(UnicodeEncodeError):
            calculateCRC16("CAFÉ")

    def test_crc16_long_input(self):
        # Verify checksum remains within the 16-bit range
        # when processing a long ASCII string.
        from MRTD import calculateCRC16
        result = calculateCRC16("ABC123<" * 100)
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 65535)

    def test_check_digit_range(self):
        # Verify the generated check digit is one numeric
        # character between 0 and 9.
        from MRTD import calculateCheckDigit
        result = calculateCheckDigit("A12345678")
        self.assertEqual(len(result), 1)
        self.assertIn(result, "0123456789")

    
class TestMRZDecoding(unittest.TestCase):

    def setUp(self):
        # Prepare fictional MRZ data using the Group B format.
        self.line1 = "P<USAJAIN<<MAHIMA".ljust(44, "<")
        self.line2 = (
            "A12345678" + "0" +
            "USA" +
            "990515" + "0" +
            "F" +
            "300630" + "0" +
            "12345678901234" +
            "<" + "0"
        )

    def test_decode_valid_mrz(self):
        # Verify both valid MRZ lines are decoded correctly.
        from MRTD import decodeMRZ
        result = decodeMRZ(self.line1, self.line2)

        self.assertEqual(result["document_type"], "P<")
        self.assertEqual(result["issuing_country"], "USA")
        self.assertEqual(result["holder_name"], "JAIN, MAHIMA")
        self.assertEqual(result["passport_number"], "A12345678")
        self.assertEqual(result["nationality"], "USA")
        self.assertEqual(result["birth_date"], "990515")
        self.assertEqual(result["sex"], "F")
        self.assertEqual(result["expiration_date"], "300630")
        self.assertEqual(result["personal_number"], "12345678901234")

    def test_decode_extract_check_digits(self):
        # Verify all four original check digits are extracted.
        from MRTD import decodeMRZ
        result = decodeMRZ(self.line1, self.line2)

        self.assertEqual(result["passport_check_digit"], "0")
        self.assertEqual(result["birth_check_digit"], "0")
        self.assertEqual(result["expiration_check_digit"], "0")
        self.assertEqual(result["personal_check_digit"], "0")

    def test_decode_short_line1(self):
        # Reject line 1 when it contains fewer than 44 characters.
        from MRTD import decodeMRZ
        with self.assertRaisesRegex(ValueError, "line 1"):
            decodeMRZ(self.line1[:-1], self.line2)

    def test_decode_short_line2(self):
        # Reject line 2 when it contains fewer than 44 characters.
        from MRTD import decodeMRZ
        with self.assertRaisesRegex(ValueError, "line 2"):
            decodeMRZ(self.line1, self.line2[:-1])

    def test_decode_invalid_character(self):
        # Reject an unsupported character in MRZ line 1.
        from MRTD import decodeMRZ
        invalid_line1 = "@" + self.line1[1:]

        with self.assertRaisesRegex(ValueError, "line 1"):
            decodeMRZ(invalid_line1, self.line2)

    def test_decode_lowercase_character(self):
        # Reject lowercase characters in scanned MRZ input.
        from MRTD import decodeMRZ
        invalid_line2 = "a" + self.line2[1:]

        with self.assertRaisesRegex(ValueError, "line 2"):
            decodeMRZ(self.line1, invalid_line2)

    def test_decode_invalid_filler(self):
        # Verify position 43 of line 2 must contain '<'.
        from MRTD import decodeMRZ
        invalid_line2 = self.line2[:42] + "A" + self.line2[43:]

        with self.assertRaisesRegex(ValueError, "position 43"):
            decodeMRZ(self.line1, invalid_line2)

    def test_decode_invalid_birth_month(self):
        # Reject birth dates containing an invalid month.
        from MRTD import decodeMRZ
        invalid_line2 = self.line2[:13] + "991315" + self.line2[19:]

        with self.assertRaisesRegex(ValueError, "invalid month"):
            decodeMRZ(self.line1, invalid_line2)

    def test_decode_invalid_expiration_day(self):
        # Reject expiration dates containing an invalid day.
        from MRTD import decodeMRZ
        invalid_line2 = self.line2[:21] + "300632" + self.line2[27:]

        with self.assertRaisesRegex(ValueError, "invalid day"):
            decodeMRZ(self.line1, invalid_line2)

    def test_decode_non_string_input(self):
        # Verify the decoder rejects missing or non-string MRZ data.
        from MRTD import decodeMRZ
        with self.assertRaisesRegex(ValueError, "must be strings"):
            decodeMRZ(None, self.line2)

    def test_decode_invalid_check_digit(self):
        # Reject a nonnumeric passport check digit.
        from MRTD import decodeMRZ
        invalid_line2 = self.line2[:9] + "A" + self.line2[10:]

        with self.assertRaisesRegex(ValueError, "must be a digit"):
            decodeMRZ(self.line1, invalid_line2)

    def test_decode_preserves_raw_lines(self):
        # Verify the original MRZ strings are retained for CRC validation.
        from MRTD import decodeMRZ
        result = decodeMRZ(self.line1, self.line2)

        self.assertEqual(result["raw_line1"], self.line1)
        self.assertEqual(result["raw_line2"], self.line2)


class TestMRZEncoding(unittest.TestCase):

    def setUp(self):
        # Fictional passport data for encoding tests.
        self.record = {
            "document_type": "P<",
            "issuing_country": "USA",
            "holder_name": "JAIN, MAHIMA",
            "passport_number": "A12345678",
            "nationality": "USA",
            "birth_date": "990515",
            "sex": "F",
            "expiration_date": "300630",
            "personal_number": "12345678901234"
        }

    def test_encode_valid_record(self):
        # Verify a valid record produces two 44-character lines.
        from MRTD import encodeMRZ

        line1, line2 = encodeMRZ(self.record)

        self.assertEqual(len(line1), 44)
        self.assertEqual(len(line2), 44)

    def test_encode_name_format(self):
        # Verify surname and given name use MRZ separators.
        from MRTD import encodeMRZ

        line1, line2 = encodeMRZ(self.record)

        self.assertTrue(line1.startswith("P<USAJAIN<<MAHIMA"))
        self.assertEqual(line1[-1], "<")

    def test_encode_uppercase(self):
        # Verify lowercase input is converted to uppercase.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["issuing_country"] = "usa"
        record["holder_name"] = "jain, mahima"

        line1, line2 = encodeMRZ(record)

        self.assertTrue(line1.startswith("P<USAJAIN<<MAHIMA"))

    def test_encode_check_digits(self):
        # Verify all four inserted check digits use CRC-16.
        from MRTD import encodeMRZ, calculateCheckDigit

        line1, line2 = encodeMRZ(self.record)

        self.assertEqual(
            line2[9], calculateCheckDigit(line2[0:9])
        )
        self.assertEqual(
            line2[19], calculateCheckDigit(line2[13:19])
        )
        self.assertEqual(
            line2[27], calculateCheckDigit(line2[21:27])
        )
        self.assertEqual(
            line2[43], calculateCheckDigit(line2[28:42])
        )

    def test_encode_missing_field(self):
        # Verify missing required data is rejected.
        from MRTD import encodeMRZ

        record = self.record.copy()
        del record["passport_number"]

        with self.assertRaisesRegex(ValueError, "passport_number"):
            encodeMRZ(record)

    def test_encode_invalid_date(self):
        # Verify an invalid birth date is rejected.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["birth_date"] = "991315"

        with self.assertRaisesRegex(ValueError, "invalid month"):
            encodeMRZ(record)

    def test_encode_name_too_long(self):
        # Verify names exceeding 39 characters are rejected.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["holder_name"] = "LONGSURNAME, " + "A" * 35

        with self.assertRaisesRegex(ValueError, "exceeds"):
            encodeMRZ(record)

    def test_encode_optional_personal_number(self):
        # Verify a missing optional personal number uses fillers.
        from MRTD import encodeMRZ

        record = self.record.copy()
        del record["personal_number"]

        line1, line2 = encodeMRZ(record)

        self.assertEqual(line2[28:42], "<" * 14)
        self.assertEqual(line2[42], "<")

    def test_encode_invalid_sex(self):
        # Verify unsupported sex values are rejected.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["sex"] = "X"

        with self.assertRaisesRegex(ValueError, "Invalid sex"):
            encodeMRZ(record)

    def test_encode_mock_database(self):
        # Verify encoder retrieves data through a mocked database
        # when no record is supplied directly.
        from MRTD import encodeMRZ
        from unittest.mock import patch

        with patch("MRTD.getTravelDocumentData",
                   return_value=self.record) as mock_db:

            line1, line2 = encodeMRZ()

            mock_db.assert_called_once_with()
            self.assertEqual(len(line1), 44)
            self.assertEqual(len(line2), 44)

    def test_encode_decode_roundtrip(self):
        # Verify that encoding followed by decoding preserves
        # the original passport information.
        from MRTD import encodeMRZ, decodeMRZ

        line1, line2 = encodeMRZ(self.record)
        decoded = decodeMRZ(line1, line2)

        self.assertEqual(decoded["holder_name"], "JAIN, MAHIMA")
        self.assertEqual(decoded["passport_number"], "A12345678")
        self.assertEqual(decoded["nationality"], "USA")
        self.assertEqual(decoded["birth_date"], "990515")
        self.assertEqual(decoded["expiration_date"], "300630")
        self.assertEqual(decoded["personal_number"], "12345678901234")


class TestMRZValidation(unittest.TestCase):

    def setUp(self):
        # Create a valid fictional passport record.
        # The encoder generates correct CRC-16 check digits.
        from MRTD import encodeMRZ

        self.record = {
            "document_type": "P<",
            "issuing_country": "USA",
            "holder_name": "JAIN, MAHIMA",
            "passport_number": "A12345678",
            "nationality": "USA",
            "birth_date": "990515",
            "sex": "F",
            "expiration_date": "300630",
            "personal_number": "12345678901234"
        }

        self.line1, self.line2 = encodeMRZ(self.record)

    def change_digit(self, position):
        # Replace a check digit with a different numeric digit.
        # Positions use zero-based Python indexing.
        original = self.line2[position]
        replacement = str((int(original) + 1) % 10)

        return (
            self.line2[:position]
            + replacement
            + self.line2[position + 1:]
        )

    def test_validate_success(self):
        # Verify all correct check digits produce success.
        from MRTD import validateMRZ

        result = validateMRZ(self.line1, self.line2)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["mismatches"], [])

    def test_validate_passport_mismatch(self):
        # Verify an incorrect passport check digit is reported.
        from MRTD import validateMRZ

        invalid_line2 = self.change_digit(9)
        result = validateMRZ(self.line1, invalid_line2)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["mismatches"]), 1)
        self.assertEqual(
            result["mismatches"][0]["field"],
            "passport_number"
        )

    def test_validate_birth_date_mismatch(self):
        # Verify an incorrect birth-date check digit is reported.
        from MRTD import validateMRZ

        invalid_line2 = self.change_digit(19)
        result = validateMRZ(self.line1, invalid_line2)

        self.assertEqual(len(result["mismatches"]), 1)
        self.assertEqual(
            result["mismatches"][0]["field"],
            "birth_date"
        )

    def test_validate_expiration_mismatch(self):
        # Verify an incorrect expiration check digit is reported.
        from MRTD import validateMRZ

        invalid_line2 = self.change_digit(27)
        result = validateMRZ(self.line1, invalid_line2)

        self.assertEqual(len(result["mismatches"]), 1)
        self.assertEqual(
            result["mismatches"][0]["field"],
            "expiration_date"
        )

    def test_validate_personal_number_mismatch(self):
        # Verify an incorrect personal-number digit is reported.
        from MRTD import validateMRZ

        invalid_line2 = self.change_digit(43)
        result = validateMRZ(self.line1, invalid_line2)

        self.assertEqual(len(result["mismatches"]), 1)
        self.assertEqual(
            result["mismatches"][0]["field"],
            "personal_number"
        )

    def test_validate_multiple_mismatches(self):
        # Verify the system identifies all four incorrect digits.
        from MRTD import validateMRZ

        invalid_line2 = self.line2

        for position in (9, 19, 27, 43):
            original = invalid_line2[position]
            replacement = str((int(original) + 1) % 10)

            invalid_line2 = (
                invalid_line2[:position]
                + replacement
                + invalid_line2[position + 1:]
            )

        result = validateMRZ(self.line1, invalid_line2)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["mismatches"]), 4)

        fields = [item["field"] for item in result["mismatches"]]

        self.assertEqual(
            fields,
            [
                "passport_number",
                "birth_date",
                "expiration_date",
                "personal_number"
            ]
        )

    def test_validate_mismatch_report_details(self):
        # Verify the mismatch report contains every required field.
        from MRTD import validateMRZ, calculateCheckDigit

        invalid_line2 = self.change_digit(9)
        result = validateMRZ(self.line1, invalid_line2)

        mismatch = result["mismatches"][0]

        self.assertEqual(mismatch["field"], "passport_number")
        self.assertEqual(mismatch["original_digit"], invalid_line2[9])
        self.assertEqual(
            mismatch["calculated_digit"],
            calculateCheckDigit(invalid_line2[0:9])
        )
        self.assertEqual(mismatch["status"], "failed")

    def test_validate_invalid_mrz_length(self):
        # Verify validation rejects malformed MRZ input.
        from MRTD import validateMRZ

        with self.assertRaisesRegex(ValueError, "line 2"):
            validateMRZ(self.line1, self.line2[:-1])

    def test_validate_invalid_date(self):
        # Verify invalid dates are rejected before CRC checking.
        from MRTD import validateMRZ

        invalid_line2 = (
            self.line2[:13] + "991315" + self.line2[19:]
        )

        with self.assertRaisesRegex(ValueError, "invalid month"):
            validateMRZ(self.line1, invalid_line2)


class TestAdditionalMutationCases(unittest.TestCase):
    """
    Additional tests created after the initial MutPy run.
    These target surviving mutants in date validation,
    encoding, and input validation.
    """

    def setUp(self):
        # Fictional valid record used as a baseline.
        self.record = {
            "document_type": "P<",
            "issuing_country": "USA",
            "holder_name": "JAIN, MAHIMA",
            "passport_number": "A12345678",
            "nationality": "USA",
            "birth_date": "990515",
            "sex": "F",
            "expiration_date": "300630",
            "personal_number": "12345678901234"
        }

    def test_mutation_01_zero_month(self):
        # Kill mutants that incorrectly permit month 00.
        from MRTD import validateMRZDate

        with self.assertRaisesRegex(ValueError, "invalid month"):
            validateMRZDate("990015", "birth_date")

    def test_mutation_02_zero_day(self):
        # Kill mutants that incorrectly permit day 00.
        from MRTD import validateMRZDate

        with self.assertRaisesRegex(ValueError, "invalid day"):
            validateMRZDate("990500", "birth_date")

    def test_mutation_03_leap_year_valid(self):
        # Confirm February 29 is accepted for leap year 00.
        from MRTD import validateMRZDate

        self.assertTrue(
            validateMRZDate("000229", "birth_date")
        )

    def test_mutation_04_non_leap_year(self):
        # Reject February 29 in a non-leap year.
        from MRTD import validateMRZDate

        with self.assertRaisesRegex(ValueError, "invalid day"):
            validateMRZDate("010229", "birth_date")

    def test_mutation_05_thirty_day_month(self):
        # Reject April 31 because April has only 30 days.
        from MRTD import validateMRZDate

        with self.assertRaisesRegex(ValueError, "invalid day"):
            validateMRZDate("990431", "birth_date")

    def test_mutation_06_valid_first_day(self):
        # Confirm January 1 is accepted as a boundary day.
        from MRTD import validateMRZDate

        self.assertTrue(
            validateMRZDate("990101", "birth_date")
        )

    def test_mutation_07_invalid_document_type(self):
        # Reject a document type not beginning with P.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["document_type"] = "X<"

        with self.assertRaisesRegex(ValueError, "document_type"):
            encodeMRZ(record)

    def test_mutation_08_short_document_type(self):
        # Reject a one-character passport document type.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["document_type"] = "P"

        with self.assertRaisesRegex(ValueError, "document_type"):
            encodeMRZ(record)

    def test_mutation_09_invalid_country_length(self):
        # Reject country codes shorter than three characters.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["issuing_country"] = "US"

        with self.assertRaisesRegex(ValueError, "issuing_country"):
            encodeMRZ(record)

    def test_mutation_10_invalid_passport_length(self):
        # Reject passport numbers exceeding nine characters.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["passport_number"] = "A123456789"

        with self.assertRaisesRegex(ValueError, "passport_number"):
            encodeMRZ(record)

    def test_mutation_11_invalid_personal_number(self):
        # Reject personal numbers exceeding 14 characters.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["personal_number"] = "123456789012345"

        with self.assertRaisesRegex(ValueError, "personal_number"):
            encodeMRZ(record)

    def test_mutation_12_empty_required_field(self):
        # Reject an empty required field instead of
        # silently producing an invalid MRZ.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["nationality"] = ""

        with self.assertRaisesRegex(ValueError, "nationality"):
            encodeMRZ(record)

    def test_mutation_13_invalid_field_type(self):
        # Reject an integer instead of a string.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["passport_number"] = 123456789

        with self.assertRaisesRegex(ValueError, "passport_number"):
            encodeMRZ(record)

    def test_mutation_14_multiple_name_separators(self):
        # Reject ambiguous names with multiple commas.
        from MRTD import encodeMRZ

        record = self.record.copy()
        record["holder_name"] = "JAIN, MAHIMA, TEST"

        with self.assertRaisesRegex(ValueError, "holder_name"):
            encodeMRZ(record)

class TestFinalRequirementChecks(unittest.TestCase):

    def setUp(self):
        self.record = {
            "document_type": "P<",
            "issuing_country": "USA",
            "holder_name": "JAIN, MAHIMA",
            "passport_number": "A12345678",
            "nationality": "USA",
            "birth_date": "990515",
            "sex": "F",
            "expiration_date": "300630",
            "personal_number": "12345678901234"
        }

    def test_decode_invalid_sex(self):
        # R2: Reject an unsupported sex character.
        from MRTD import encodeMRZ, decodeMRZ

        line1, line2 = encodeMRZ(self.record)
        invalid_line2 = line2[:20] + "Z" + line2[21:]

        with self.assertRaisesRegex(ValueError, "Invalid sex"):
            decodeMRZ(line1, invalid_line2)

    def test_encode_multiple_nationalities(self):
        # R3: Verify MRZ encoding with different ICAO country codes.
        from MRTD import encodeMRZ

        for country in ("USA", "CAN", "IND", "GBR"):
            with self.subTest(country=country):
                record = self.record.copy()
                record["nationality"] = country
                _, line2 = encodeMRZ(record)

                self.assertEqual(line2[10:13], country)
                self.assertEqual(len(line2), 44)

    def test_decode_invalid_nationality(self):
        # R2: Reject a numeric nationality code.
        from MRTD import encodeMRZ, decodeMRZ

        line1, line2 = encodeMRZ(self.record)
        invalid_line2 = line2[:10] + "123" + line2[13:]

        with self.assertRaisesRegex(ValueError, "Invalid nationality"):
            decodeMRZ(line1, invalid_line2)


class TestAdditionalVerification(unittest.TestCase):

    def test_crc16_exact_filler_checksum(self):
        # Verify the exact CRC-16 result for MRZ filler characters.
        from MRTD import calculateCRC16

        self.assertEqual(calculateCRC16("ABC<<<<"), 0xA4C6)

    def test_encode_decode_round_trip(self):
        # Verify that encoded passport information can be
        # decoded without changing important field values.
        from MRTD import encodeMRZ, decodeMRZ

        record = {
            "document_type": "P<",
            "issuing_country": "USA",
            "holder_name": "SMITH, JANE",
            "passport_number": "B98765432",
            "nationality": "CAN",
            "birth_date": "020215",
            "sex": "F",
            "expiration_date": "300630",
            "personal_number": "123456789"
        }

        line1, line2 = encodeMRZ(record)
        decoded = decodeMRZ(line1, line2)

        self.assertEqual(len(line1), 44)
        self.assertEqual(len(line2), 44)
        self.assertEqual(decoded["holder_name"], "SMITH, JANE")
        self.assertEqual(decoded["passport_number"], "B98765432")
        self.assertEqual(decoded["nationality"], "CAN")
        self.assertEqual(decoded["birth_date"], "020215")
        self.assertEqual(decoded["personal_number"], "123456789")

if __name__ == "__main__":
    unittest.main()
