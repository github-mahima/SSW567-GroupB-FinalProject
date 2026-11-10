"""Plot SSW 567 Part 3 timings. Requires matplotlib; run after phase3_experiment.py."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
SERIES = [
    ('encode_no_tests_s', 'Encode — no assertions'),
    ('encode_with_tests_s', 'Encode — assertions'),
    ('decode_no_tests_s', 'Decode — no assertions'),
    ('decode_with_tests_s', 'Decode — assertions'),
]

def load(name):
    with (ROOT / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def plot(rows, filename, title, suffix, ylabel):
    plt.figure(figsize=(10, 6))
    xs = [int(r['record_count']) for r in rows]
    for key, label in SERIES:
        field = key.replace('_s', suffix)
        plt.plot(xs, [float(r[field]) for r in rows], marker='o', label=label)
    plt.title(title)
    plt.xlabel('Number of passport records')
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(ROOT / filename, dpi=180)
    plt.close()

if __name__ == '__main__':
    plot(load('phase3_timings.csv'), 'phase3_execution_times.png',
         'MRTD Encoding and Decoding Execution Times', '_s', 'Execution time (seconds)')
    plot(load('phase3_per_transaction.csv'), 'phase3_time_per_transaction.png',
         'MRTD Average Processing Time per Record', '_ms_per_record',
         'Average time per transaction (milliseconds)')
    print('Created phase3_execution_times.png and phase3_time_per_transaction.png')
