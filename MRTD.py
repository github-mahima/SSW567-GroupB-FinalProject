
"""
SSW 567 - Final Group Project, Part 2
Group B - CRC-16
Machine-Readable Travel Document (MRTD) System
"""


def scanMRZ():
    """
    R1: Interface for an external MRZ scanner.

    Expected to return two strings of 44 characters each.
    The actual scanner is not implemented.
    """
    pass


def getTravelDocumentData():
    """
    R3: Interface for retrieving travel document information
    from a database.

    The actual database is not implemented.
    """
    pass

def calculateCRC16(data):
    """
    R4: Calculate CRC-16/ARC checksum.

    Configuration:
    Polynomial: 0x8005 (reflected: 0xA001)
    Initial value: 0x0000
    Input encoding: ASCII
    Final XOR: 0x0000
    """
    if not isinstance(data, str):
        raise TypeError("Input must be a string")

    crc = 0x0000

    for byte in data.encode("ascii"):
        crc ^= byte

        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    return crc & 0xFFFF


def calculateCheckDigit(data):
    """
    R4: Calculate the MRZ check digit by taking
    the CRC-16 checksum modulo 10.
    """
    return str(calculateCRC16(data) % 10)


def validateMRZDate(date_value, field_name):
    """
    R2: Validate an MRZ date in YYMMDD format.
    Preserve the two-digit year without assigning a century.
    """
    if len(date_value) != 6 or not date_value.isdigit():
        raise ValueError(field_name + ": date must contain six digits")

    year = int(date_value[:2])
    month = int(date_value[2:4])
    day = int(date_value[4:6])

    if month < 1 or month > 12:
        raise ValueError(field_name + ": invalid month")

    days_in_month = [31, 29 if year % 4 == 0 else 28,
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if day < 1 or day > days_in_month[month - 1]:
        raise ValueError(field_name + ": invalid day")

    return True


def decodeMRZ(line1, line2):
    """
    R2: Decode two MRZ strings into passport information.

    Each line must contain exactly 44 characters.
    Uses Group B's customized four-check-digit layout.
    """
    if not isinstance(line1, str) or not isinstance(line2, str):
        raise ValueError("MRZ lines must be strings")

    if len(line1) != 44:
        raise ValueError("MRZ line 1 must contain 44 characters")

    if len(line2) != 44:
        raise ValueError("MRZ line 2 must contain 44 characters")

    allowed_characters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")

    if any(char not in allowed_characters for char in line1):
        raise ValueError("MRZ line 1 contains invalid characters")

    if any(char not in allowed_characters for char in line2):
        raise ValueError("MRZ line 2 contains invalid characters")

    if line2[42] != "<":
        raise ValueError("MRZ line 2 position 43 must be a filler")

    fields = {
        "document_type": line1[0:2],
        "issuing_country": line1[2:5],
        "holder_name": line1[5:44].rstrip("<").replace("<<", ", ").replace("<", " "),
        "passport_number": line2[0:9].rstrip("<"),
        "passport_check_digit": line2[9],
        "nationality": line2[10:13],
        "birth_date": line2[13:19],
        "birth_check_digit": line2[19],
        "sex": line2[20],
        "expiration_date": line2[21:27],
        "expiration_check_digit": line2[27],
        "personal_number": line2[28:42].rstrip("<"),
        "personal_check_digit": line2[43],
        "raw_line1": line1,
        "raw_line2": line2
    }

    validateMRZDate(fields["birth_date"], "birth_date")
    validateMRZDate(fields["expiration_date"], "expiration_date")

    for name in ("passport_check_digit", "birth_check_digit",
                 "expiration_check_digit", "personal_check_digit"):
        if not fields[name].isdigit():
            raise ValueError(name + ": must be a digit")
    
    # Reject malformed required fields.
    if fields["document_type"][0] != "P":
        raise ValueError("Invalid document_type")

    if fields["sex"] not in ("M", "F", "<"):
        raise ValueError("Invalid sex")

    for field_name in ("issuing_country", "nationality"):
        code = fields[field_name]
        if len(code) != 3 or not code.isalpha():
            raise ValueError("Invalid " + field_name)

    return fields


def encodeMRZ(record=None):
    """
    R3: Encode travel document information into two MRZ lines.

    If no record is supplied, retrieve it through the database
    interface. The database itself is not implemented.

    Returns two strings of exactly 44 characters each.
    """
    if record is None:
        record = getTravelDocumentData()

    if not isinstance(record, dict):
        raise ValueError("Travel document data must be a dictionary")

    required_fields = [
        "document_type", "issuing_country", "holder_name",
        "passport_number", "nationality", "birth_date",
        "sex", "expiration_date"
    ]

    for field in required_fields:
        if field not in record or not isinstance(record[field], str):
            raise ValueError("Missing or invalid field: " + field)

        if not record[field].strip():
            raise ValueError("Missing or invalid field: " + field)

    def normalize(value):
        return value.upper()

    document_type = normalize(record["document_type"])
    issuing_country = normalize(record["issuing_country"])
    holder_name = normalize(record["holder_name"])
    passport_number = normalize(record["passport_number"])
    nationality = normalize(record["nationality"])
    birth_date = record["birth_date"]
    sex = normalize(record["sex"])
    expiration_date = record["expiration_date"]
    personal_number = normalize(record.get("personal_number") or "")

    # Convert the holder's name to MRZ notation.
    # Example: JAIN, MAHIMA -> JAIN<<MAHIMA
    if "," in holder_name:
        parts = holder_name.split(",")
        if len(parts) != 2:
            raise ValueError("Invalid holder_name format")
        surname = parts[0].strip().replace(" ", "<")
        given_names = parts[1].strip().replace(" ", "<")
        if not surname or not given_names:
            raise ValueError("Invalid holder_name format")
        holder_name = surname + "<<" + given_names

    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")
    letters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    if len(document_type) != 2 or document_type[0] != "P":
        raise ValueError("Invalid document_type")

    if document_type[1] not in letters and document_type[1] != "<":
        raise ValueError("Invalid document_type")

    for field_name, code in [
        ("issuing_country", issuing_country),
        ("nationality", nationality)
    ]:
        if len(code) != 3 or any(c not in letters for c in code):
            raise ValueError("Invalid " + field_name)

    if len(holder_name) > 39:
        raise ValueError("holder_name exceeds 39 characters")

    if any(c not in letters and c != "<" for c in holder_name):
        raise ValueError("Invalid holder_name characters")

    if "<<" not in holder_name:
        raise ValueError("holder_name must separate names with <<")

    if len(passport_number) > 9 or not passport_number:
        raise ValueError("Invalid passport_number length")

    if any(c not in allowed for c in passport_number):
        raise ValueError("Invalid passport_number characters")

    if sex not in ("M", "F", "<"):
        raise ValueError("Invalid sex")

    if len(personal_number) > 14:
        raise ValueError("personal_number exceeds 14 characters")

    if any(c not in allowed for c in personal_number):
        raise ValueError("Invalid personal_number characters")

    validateMRZDate(birth_date, "birth_date")
    validateMRZDate(expiration_date, "expiration_date")

    # Pad fixed-width fields with MRZ filler characters.
    holder_name = holder_name.ljust(39, "<")
    passport_number = passport_number.ljust(9, "<")
    personal_number = personal_number.ljust(14, "<")

    # Build line 1.
    line1 = document_type + issuing_country + holder_name

    # Build line 2 using Group B's CRC-16 check digits.
    line2 = (
        passport_number
        + calculateCheckDigit(passport_number)
        + nationality
        + birth_date
        + calculateCheckDigit(birth_date)
        + sex
        + expiration_date
        + calculateCheckDigit(expiration_date)
        + personal_number
        + "<"
        + calculateCheckDigit(personal_number)
    )

    return line1, line2


def validateMRZ(line1, line2):
    """
    R4: Validate the four CRC-16 check digits in the MRZ.

    Returns a dictionary containing:
    - status: "success" or "failed"
    - mismatches: list of fields with incorrect check digits

    Each mismatch reports the field, original digit,
    calculated digit, and failed status.
    """
    # Decode and validate the MRZ format first.
    decoded = decodeMRZ(line1, line2)

    # Use original field values, including filler characters,
    # when calculating CRC-16 check digits.
    checks = [
        ("passport_number", line2[0:9], decoded["passport_check_digit"]),
        ("birth_date", line2[13:19], decoded["birth_check_digit"]),
        ("expiration_date", line2[21:27],
         decoded["expiration_check_digit"]),
        ("personal_number", line2[28:42],
         decoded["personal_check_digit"])
    ]

    mismatches = []

    for field_name, field_value, original_digit in checks:
        calculated_digit = calculateCheckDigit(field_value)

        if original_digit != calculated_digit:
            mismatches.append({
                "field": field_name,
                "original_digit": original_digit,
                "calculated_digit": calculated_digit,
                "status": "failed"
            })

    if mismatches:
        return {
            "status": "failed",
            "mismatches": mismatches
        }

    return {
        "status": "success",
        "mismatches": []
    }
