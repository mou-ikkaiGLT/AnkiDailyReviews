# AnkiDailyReviews

A script that generates a GitHub contribution graph-style heatmap of your Anki daily card reviews as an SVG.

![Anki Daily Reviews](heatmap.svg)

## Usage

**Manual update:**
```bash
python3 generate_heatmap.py
```

Or use the provided shell script, which also commits and pushes:
```bash
./update.sh
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--db PATH` | See platform defaults below | Path to Anki collection |
| `--out PATH` | `heatmap.svg` (next to script) | Output SVG path |

## Auto-update (macOS)

A Launch Agent can regenerate and push the heatmap daily at 9 AM so your README stays current automatically.

```bash
./toggle.sh enable    # install — runs daily at 9 AM
./toggle.sh disable   # uninstall
./toggle.sh status    # check current state
```

Requires the machine to be on (or wake from sleep) at 9 AM and `git push` to be authenticated (SSH key or credential helper).

Logs are written to `update.log`.

## Requirements

- Python 3 (stdlib only — no dependencies)
- Anki installed with a local collection
- macOS (auto-update); Windows supported for manual use

## Platform support

| Platform | Default DB path |
|----------|----------------|
| macOS | `~/Library/Application Support/Anki2/User 1/collection.anki2` |
| Windows | `%APPDATA%\Anki2\User 1\collection.anki2` |

If your collection is in a non-standard location, use `--db PATH`.

## How it works

- Reads review history directly from Anki's SQLite database (`revlog` table)
- Respects your configured rollover hour so early-AM reviews count under the correct date
- Displays the last 53 weeks in a Sun–Sat grid
- Blue color scale, new shade every 50 cards

## Embedding in a README

Commit `heatmap.svg` to your repo, then reference it via raw URL:

```markdown
![Anki Daily Reviews](https://raw.githubusercontent.com/<username>/<repo>/main/heatmap.svg)
```
