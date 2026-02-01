# Chess Blunder Explainer ♟️

A Stockfish-powered command-line tool that analyses chess PGNs and flags blunders
using evaluation swings.

The tool focuses on **meaningful mistakes** by detecting large evaluation drops
and mate threats, rather than naive “hung piece” rules.

---

## Features
- Paste a PGN directly into the terminal
- Detect blunders using Stockfish evaluation drops
- Identify mate threats and decisive mistakes
- Clear move numbering (e.g. `36... Qd6`)
- Board visualisation with coordinates
- Minimal, fast CLI workflow

---

## Requirements
- Python 3.10+
- `python-chess`
- Stockfish (installed separately)

---

## Setup

Install Python dependencies:
```bash
pip install python-chess
```

Install Stockfish (macOS via Homebrew):
```bash
brew install stockfish
```

---

## Usage

### Paste PGN into terminal
```bash
python3 analyse_game.py
```

Paste a PGN, then press **Ctrl + D** to run analysis.

### Analyse a PGN file
```bash
python3 analyse_game.py game.pgn
```

---

## Example Output

```
🚨 Move 36... Qd6
   Reason: material loss
   Eval for Black: +3.63 → +0.41  (drop 3.22)
```

---

## Blunder Logic

A move is flagged when:
- The evaluation drops by a configurable threshold (default: 1.5), or
- The move allows or misses a forced mate

Winning conversions are not flagged.

---

## Project Status
- Version: v1.0
- Engine-backed analysis
- CLI-only by design

Planned future improvements:
- Best-move suggestions
- Blunder severity labels
- Batch PGN analysis