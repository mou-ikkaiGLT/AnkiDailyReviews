#!/usr/bin/env python3
"""Generate a GitHub-style SVG heatmap of Anki daily card reviews."""

import argparse
import calendar
import datetime
import os
import sqlite3
import sys
from datetime import timedelta

DB_PATH = "~/Library/Application Support/Anki2/User 1/collection.anki2"

COLORS = [          # checked highest-first
    (201, "#79c0ff"),
    (151, "#4a9eff"),
    (101, "#2970d4"),
    ( 51, "#1a4a8a"),
    (  1, "#0d2140"),
    (  0, "#161b22"),   # 0 reviews
]
FUTURE_COLOR = "#0d1117"   # blends into background

# Layout (px)
CELL, GAP, STEP = 11, 2, 13
COLS, ROWS = 53, 7
LEFT_MARGIN, TOP_MARGIN, RIGHT_MARGIN = 30, 45, 10
LEGEND_HEIGHT = 30


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Anki review heatmap SVG")
    parser.add_argument("--db", default=DB_PATH, help="Path to Anki collection.anki2")
    parser.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "heatmap.svg"),
        help="Output SVG path",
    )
    return parser.parse_args()


def get_rollover(conn) -> int:
    """Return rollover offset in seconds from Anki config."""
    cur = conn.cursor()
    cur.execute("SELECT val FROM config WHERE key='rollover'")
    row = cur.fetchone()
    if row is None:
        return 4 * 3600  # default 4 AM
    return int(row[0]) * 3600


def fetch_daily_counts(db_path: str, rollover_secs: int, cutoff_epoch: int) -> dict:
    """Return {date_str: count} for all review dates from cutoff onward."""
    path = os.path.expanduser(db_path)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rollover_secs = get_rollover(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                date((id / 1000) - :rollover_secs, 'unixepoch', 'localtime') AS review_date,
                count(*) AS card_count
            FROM revlog
            WHERE (id / 1000) - :rollover_secs >= :cutoff_epoch
            GROUP BY review_date
            ORDER BY review_date
            """,
            {"rollover_secs": rollover_secs, "cutoff_epoch": cutoff_epoch},
        )
        return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()


def color_for(count: int) -> str:
    for threshold, color in COLORS:
        if count >= threshold:
            return color
    return COLORS[-1][1]


def build_svg(daily_counts: dict, grid_start: datetime.date, today: datetime.date, total_reviews: int) -> str:
    svg_width = LEFT_MARGIN + COLS * STEP + RIGHT_MARGIN
    svg_height = TOP_MARGIN + ROWS * STEP + LEGEND_HEIGHT

    lines = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" '
        f'style="background:#0d1117;border-radius:6px;">'
    )

    # Title
    total_str = f"{total_reviews:,}"
    lines.append(
        f'  <text x="{LEFT_MARGIN}" y="20" font-family="monospace" font-size="12" '
        f'fill="#e6edf3">{total_str} reviews in the last year</text>'
    )

    # Month labels
    month_labels = {}  # col -> month abbrev
    for col in range(COLS):
        d = grid_start + timedelta(weeks=col)
        # emit label on first column of each new month
        if col == 0 or d.month != (grid_start + timedelta(weeks=col - 1)).month:
            month_labels[col] = d.strftime("%b")

    for col, label in month_labels.items():
        x = LEFT_MARGIN + col * STEP
        lines.append(
            f'  <text x="{x}" y="40" font-family="monospace" font-size="10" '
            f'fill="#8b949e">{label}</text>'
        )

    # Day labels (Mon=1, Wed=3, Fri=5 → rows 1,3,5)
    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for row, label in day_labels.items():
        y = TOP_MARGIN + row * STEP + CELL  # baseline within the cell row
        lines.append(
            f'  <text x="{LEFT_MARGIN - 2}" y="{y}" font-family="monospace" font-size="9" '
            f'fill="#8b949e" text-anchor="end">{label}</text>'
        )

    # Grid cells
    for col in range(COLS):
        for row in range(ROWS):
            d = grid_start + timedelta(days=col * 7 + row)
            x = LEFT_MARGIN + col * STEP
            y = TOP_MARGIN + row * STEP
            date_str = d.isoformat()

            if d > today:
                fill = FUTURE_COLOR
                lines.append(
                    f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}"/>'
                )
            else:
                count = daily_counts.get(date_str, 0)
                fill = color_for(count)
                title = f"{date_str}: {count} review{'s' if count != 1 else ''}"
                lines.append(
                    f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}">'
                    f'<title>{title}</title></rect>'
                )

    # Legend
    legend_y = TOP_MARGIN + ROWS * STEP + 10
    legend_swatches = list(reversed(COLORS))  # least → most
    swatch_step = STEP

    less_x = LEFT_MARGIN
    lines.append(
        f'  <text x="{less_x}" y="{legend_y + CELL}" font-family="monospace" font-size="9" '
        f'fill="#8b949e">Less</text>'
    )
    swatch_start_x = less_x + 28
    for i, (_, color) in enumerate(legend_swatches):
        sx = swatch_start_x + i * swatch_step
        lines.append(
            f'  <rect x="{sx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
    more_x = swatch_start_x + len(legend_swatches) * swatch_step + 2
    lines.append(
        f'  <text x="{more_x}" y="{legend_y + CELL}" font-family="monospace" font-size="9" '
        f'fill="#8b949e">More</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    args = parse_args()

    today = datetime.date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    current_week_sunday = today - timedelta(days=days_since_sunday)
    grid_start = current_week_sunday - timedelta(weeks=52)

    cutoff_epoch = calendar.timegm(grid_start.timetuple())

    db_path = os.path.expanduser(args.db)
    if not os.path.exists(db_path):
        print(f"Error: Anki database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    daily_counts = fetch_daily_counts(args.db, 0, cutoff_epoch)
    total_reviews = sum(daily_counts.values())

    svg = build_svg(daily_counts, grid_start, today, total_reviews)

    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Heatmap written to: {out_path}")


if __name__ == "__main__":
    main()
