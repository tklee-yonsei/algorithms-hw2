"""Measures linear-probing cost against the load factor and compares it with Knuth.

Run with `make experiment`. Writes experiments/results.csv and experiments/results.svg.
"""

import csv
import os
import random
import string

from src.hash_table import HashTable

CAPACITY = 4093
LOAD_FACTORS = [round(0.1 * step, 1) for step in range(1, 10)]
TRIALS = 20
MISSING_KEYS_PER_TRIAL = 2000
SEED = 2026
ALPHABET = string.ascii_lowercase + string.digits

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "results.csv")
SVG_PATH = os.path.join(HERE, "results.svg")


def knuth_success(alpha: float) -> float:
    return (1 + 1 / (1 - alpha)) / 2


def knuth_failure(alpha: float) -> float:
    return (1 + 1 / (1 - alpha) ** 2) / 2


def random_url(rng: random.Random) -> str:
    host = "".join(rng.choice(ALPHABET) for _ in range(rng.randint(5, 12)))
    path = "".join(rng.choice(ALPHABET) for _ in range(rng.randint(4, 16)))
    return f"https://{host}.com/{path}"


def run_trial(alpha: float, rng: random.Random) -> tuple[float, float]:
    table = HashTable(capacity=CAPACITY, max_load=None)
    target = round(alpha * CAPACITY)

    stored = []
    while len(stored) < target:
        url = random_url(rng)
        before = len(table)
        table.put(url, None)
        if len(table) > before:
            stored.append(url)

    success = sum(table.probe_count(url) for url in stored) / len(stored)

    failure_total = 0
    counted = 0
    while counted < MISSING_KEYS_PER_TRIAL:
        url = random_url(rng)
        probes = table.probe_count(url)
        # An absent key ends on an empty slot, so it is never found in the table.
        if _is_stored(table, url):
            continue
        failure_total += probes
        counted += 1
    return success, failure_total / counted


def _is_stored(table: HashTable, url: str) -> bool:
    try:
        table.get(url)
    except KeyError:
        return False
    return True


def measure() -> list[dict]:
    rng = random.Random(SEED)
    rows = []
    for alpha in LOAD_FACTORS:
        trials = [run_trial(alpha, rng) for _ in range(TRIALS)]
        measured_success = sum(t[0] for t in trials) / TRIALS
        measured_failure = sum(t[1] for t in trials) / TRIALS
        rows.append(
            {
                "load_factor": alpha,
                "success_measured": measured_success,
                "success_knuth": knuth_success(alpha),
                "failure_measured": measured_failure,
                "failure_knuth": knuth_failure(alpha),
            }
        )
    return rows


def write_csv(rows: list[dict]) -> None:
    columns = ["load_factor", "success_measured", "success_knuth", "failure_measured", "failure_knuth"]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row["load_factor"]] + [f"{row[name]:.4f}" for name in columns[1:]])


def print_table(rows: list[dict]) -> None:
    print(f"capacity={CAPACITY}, trials={TRIALS}, missing keys/trial={MISSING_KEYS_PER_TRIAL}, seed={SEED}")
    print(f"{'alpha':>5} | {'success':>9} {'Knuth':>9} {'diff%':>7} | {'failure':>9} {'Knuth':>9} {'diff%':>7}")
    for row in rows:
        success_diff = (row["success_measured"] / row["success_knuth"] - 1) * 100
        failure_diff = (row["failure_measured"] / row["failure_knuth"] - 1) * 100
        print(
            f"{row['load_factor']:>5.1f} | {row['success_measured']:>9.3f} {row['success_knuth']:>9.3f} {success_diff:>+6.1f}% |"
            f" {row['failure_measured']:>9.3f} {row['failure_knuth']:>9.3f} {failure_diff:>+6.1f}%"
        )


def write_svg(rows: list[dict]) -> None:
    width, height = 720, 460
    left, right, top, bottom = 70, 30, 50, 70
    plot_w, plot_h = width - left - right, height - top - bottom
    y_max = max(max(row["failure_measured"], row["failure_knuth"]) for row in rows)
    y_max = (int(y_max / 10) + 1) * 10

    def x(alpha: float) -> float:
        return left + (alpha - 0.1) / 0.8 * plot_w

    def y(value: float) -> float:
        return top + plot_h - value / y_max * plot_h

    def line(key: str, color: str, dashed: bool) -> str:
        points = " ".join(f"{x(row['load_factor']):.1f},{y(row[key]):.1f}" for row in rows)
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        markers = "".join(
            f'<circle cx="{x(row["load_factor"]):.1f}" cy="{y(row[key]):.1f}" r="3.5" fill="{color}"/>'
            for row in rows
        )
        return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"{dash}/>{markers}'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"'
        ' font-family="sans-serif" font-size="12">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" font-size="16">'
        "Linear probing: average probes vs load factor</text>",
    ]
    for tick in range(0, y_max + 1, 10):
        parts.append(f'<line x1="{left}" y1="{y(tick):.1f}" x2="{width - right}" y2="{y(tick):.1f}" stroke="#ddd"/>')
        parts.append(f'<text x="{left - 8}" y="{y(tick) + 4:.1f}" text-anchor="end">{tick}</text>')
    for row in rows:
        parts.append(
            f'<text x="{x(row["load_factor"]):.1f}" y="{top + plot_h + 20}" text-anchor="middle">'
            f'{row["load_factor"]:.1f}</text>'
        )
    parts += [
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="black"/>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{width - right}" y2="{top + plot_h}" stroke="black"/>',
        f'<text x="{left + plot_w / 2}" y="{height - 30}" text-anchor="middle">load factor (alpha)</text>',
        f'<text x="18" y="{top + plot_h / 2}" text-anchor="middle" transform="rotate(-90 18 {top + plot_h / 2})">'
        "average probes</text>",
        line("failure_knuth", "#d62728", True),
        line("failure_measured", "#d62728", False),
        line("success_knuth", "#1f77b4", True),
        line("success_measured", "#1f77b4", False),
    ]
    legend = [
        ("success (measured)", "#1f77b4", False),
        ("success (Knuth)", "#1f77b4", True),
        ("failure (measured)", "#d62728", False),
        ("failure (Knuth)", "#d62728", True),
    ]
    for index, (label, color, dashed) in enumerate(legend):
        lx = left + 10 + index * 160
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        parts.append(f'<line x1="{lx}" y1="{height - 12}" x2="{lx + 28}" y2="{height - 12}" stroke="{color}" stroke-width="2"{dash}/>')
        parts.append(f'<text x="{lx + 34}" y="{height - 8}">{label}</text>')
    parts.append("</svg>")
    with open(SVG_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(parts) + "\n")


def main() -> None:
    rows = measure()
    write_csv(rows)
    write_svg(rows)
    print_table(rows)
    print(f"wrote {CSV_PATH}")
    print(f"wrote {SVG_PATH}")


if __name__ == "__main__":
    main()
