"""SSW 567 Group B Part 3: reproducible CRC-16 encode/decode benchmarks.

Run next to MRTD.py and records_decoded.json:
    python phase3_experiment.py

Timing excludes JSON loading, CSV writing, and chart creation. Each timed
scenario processes the first N records, independently, in the original order.
Assertions are explicit checks inside the timed loop, not the 65-test suite.
The output reports the median of 5 timed runs and saves every individual run.
"""
import csv
import json
import statistics
import time
from pathlib import Path

from MRTD import encodeMRZ, decodeMRZ, validateMRZ

ROOT = Path(__file__).resolve().parent
SIZES = [10, 100] + list(range(1000, 10001, 1000))
REPEATS = 5  # Five independent timed runs per scenario and input size


def to_mrtd_record(item):
    """Convert professor's nested JSON into the Part 2 encoder's field names."""
    first, second = item['line1'], item['line2']
    return {
        'document_type': 'P<',
        'issuing_country': first['issuing_country'],
        'holder_name': first['last_name'] + ', ' + first['given_name'],
        'passport_number': second['passport_number'],
        'nationality': second['country_code'],
        'birth_date': second['birth_date'],
        'sex': second['sex'],
        'expiration_date': second['expiration_date'],
        'personal_number': second['personal_number'],
    }


def split_encoded(value):
    lines = value.split(';')
    if len(lines) != 2 or any(len(line) != 44 for line in lines):
        raise ValueError('Expected two 44-character MRZ lines separated by ;')
    return tuple(lines)


def encode_batch(records, checked):
    for record in records:
        line1, line2 = encodeMRZ(record)
        if checked:
            assert len(line1) == 44 and len(line2) == 44
            assert line1.startswith(record['document_type'] + record['issuing_country'])
            assert validateMRZ(line1, line2)['status'] == 'success'


def decode_batch(pairs, expected, checked):
    for (line1, line2), record in zip(pairs, expected):
        decoded = decodeMRZ(line1, line2)
        if checked:
            assert decoded['issuing_country'] == record['issuing_country']
            assert decoded['holder_name'] == record['holder_name']
            assert decoded['passport_number'] == record['passport_number']
            assert decoded['nationality'] == record['nationality']
            assert decoded['birth_date'] == record['birth_date']
            assert decoded['sex'] == record['sex']
            assert decoded['expiration_date'] == record['expiration_date']
            assert decoded['personal_number'] == record['personal_number']
            assert decoded['raw_line1'] == line1 and decoded['raw_line2'] == line2


def median_seconds(fn, *args):
    samples = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        fn(*args)
        samples.append(time.perf_counter() - start)
    return statistics.median(samples), samples


def save_csv(path, rows, keys):
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main():
    with (ROOT / 'records_decoded.json').open(encoding='utf-8') as file:
        decoded_source = json.load(file)['records_decoded']
    if len(decoded_source) != 10000:
        raise ValueError('Input must contain exactly 10,000 records')

    records = [to_mrtd_record(item) for item in decoded_source]

    # Required deliverable: encode all records with our actual Part 2 function.
    our_encoded = [';'.join(encodeMRZ(record)) for record in records]
    with (ROOT / 'records_encoded.json').open('w', encoding='utf-8') as file:
        json.dump({'records_encoded': our_encoded}, file, indent=2)

    # Decode the newly encoded records, using the Part 2 CRC-16 format.
    encoded_pairs = [split_encoded(value) for value in our_encoded]
    for pair in encoded_pairs:
        assert validateMRZ(*pair)['status'] == 'success'
    decode_batch(encoded_pairs, records, True)

    # Warm up before sampling; prevent first-call overhead skew.
    encode_batch(records[:100], True)
    decode_batch(encoded_pairs[:100], records[:100], True)
    rows = []
    raw_rows = []
    for n in SIZES:
        chunk = records[:n]
        pairs = encoded_pairs[:n]
        # Alternate scenario order to avoid giving one mode a consistent advantage.
        scenarios = [('encode_no_tests_s', encode_batch, chunk, False),
                     ('encode_with_tests_s', encode_batch, chunk, True),
                     ('decode_no_tests_s', decode_batch, pairs, chunk, False),
                     ('decode_with_tests_s', decode_batch, pairs, chunk, True)]
        if (SIZES.index(n) % 2):
            scenarios.reverse()
        row = {'record_count': n}
        for name, fn, *args in scenarios:
            median, samples = median_seconds(fn, *args)
            row[name] = round(median, 8)
            for index, elapsed in enumerate(samples, start=1):
                raw_rows.append({'record_count': n, 'scenario': name,
                                 'repeat': index, 'elapsed_s': round(elapsed, 8)})
        rows.append(row)
        print('Processed {:>5} records: encode {:.5f}/{:.5f}s; decode {:.5f}/{:.5f}s'.format(
            n, row['encode_no_tests_s'], row['encode_with_tests_s'],
            row['decode_no_tests_s'], row['decode_with_tests_s']))

    keys = ['record_count', 'encode_no_tests_s', 'encode_with_tests_s',
            'decode_no_tests_s', 'decode_with_tests_s']
    save_csv(ROOT / 'phase3_timings.csv', rows, keys)
    save_csv(ROOT / 'phase3_raw_runs.csv', raw_rows,
             ['record_count', 'scenario', 'repeat', 'elapsed_s'])
    speed_rows = []
    for row in rows:
        if row['record_count'] in (10, 100, 1000, 10000):
            speed_rows.append({'record_count': row['record_count'], **{
                name.replace('_s', '_ms_per_record'): round(row[name] * 1000 / row['record_count'], 9)
                for name in keys[1:]}})
    save_csv(ROOT / 'phase3_per_transaction.csv', speed_rows,
             ['record_count'] + [k.replace('_s', '_ms_per_record') for k in keys[1:]])
    print('Wrote records_encoded.json, phase3_timings.csv, phase3_raw_runs.csv, phase3_per_transaction.csv')


if __name__ == '__main__':
    main()
