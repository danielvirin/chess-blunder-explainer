import sys
import io
import shutil
import chess
import chess.pgn
import chess.engine


# -------- display helpers --------
def board_with_coords(board: chess.Board) -> str:
    rows = str(board).splitlines()  # rank 8 -> 1
    out = []
    for i, row in enumerate(rows):
        rank = 8 - i
        out.append(f"{rank}  {row}")
    out.append("   a b c d e f g h")
    return "\n".join(out)


def move_label(ply: int, mover: str) -> str:
    """Convert ply (half-move count starting at 1) to human move number label."""
    move_no = (ply + 1) // 2
    return f"{move_no}..." if mover == "Black" else f"{move_no}."


# -------- input --------
def read_pgn_text() -> str:
    """
    Reads PGN from either:
    - a file path passed as argv[1], OR
    - stdin if no file path is provided (paste + Ctrl+D)
    """
    if len(sys.argv) > 1 and sys.argv[1].strip():
        path = sys.argv[1]
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    return sys.stdin.read()


# -------- Stockfish helpers --------
def find_stockfish_path() -> str:
    path = shutil.which("stockfish")
    if not path:
        raise RuntimeError(
            "Stockfish not found.\n"
            "Install it with:\n"
            "  brew install stockfish\n"
            "Then try again."
        )
    return path


def eval_white_pov(engine: chess.engine.SimpleEngine, board: chess.Board, depth: int) -> float:
    """
    Returns evaluation in pawns from White's perspective.
    Positive = good for White. Negative = good for Black.
    Mate scores become +/-1000.
    """
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    score = info["score"].pov(chess.WHITE)

    if score.is_mate():
        m = score.mate()
        # mate for White => +1000, mate against White => -1000
        return 1000.0 if (m is not None and m > 0) else -1000.0

    cp = score.score(mate_score=100000)
    return (cp / 100.0) if cp is not None else 0.0


def mover_pov_from_white(eval_white: float, mover_color: chess.Color) -> float:
    """Convert White POV eval into 'mover POV' eval (positive = good for the mover)."""
    return eval_white if mover_color == chess.WHITE else -eval_white


def reason_tag(before: float, after: float, drop: float) -> str:
    # Mate swings / forced mate situations
    if abs(after) >= 999 or abs(before) >= 999:
        return "mate threat"

    # Big drops are usually tactical/material
    if drop >= 2.5:
        return "material loss"

    return "positional mistake"


# -------- main analysis --------
def analyse_games(pgn_text: str, depth: int = 12, blunder_drop: float = 1.5) -> None:
    pgn_io = io.StringIO(pgn_text)
    game_number = 0

    stockfish_path = find_stockfish_path()
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        while True:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break

            game_number += 1
            headers = game.headers
            white = headers.get("White", "?")
            black = headers.get("Black", "?")

            # If user pasted raw movetext (no headers), optionally prompt for names
            if (white == "?" and black == "?") and sys.stdin.isatty():
                w = input("White player name (optional): ").strip()
                b = input("Black player name (optional): ").strip()
                white = w if w else "White"
                black = b if b else "Black"

            print(f"\n🎯 Game {game_number}: {white} vs {black}")
            print("-" * 60)

            board = game.board()
            ply = 1

            for move in game.mainline_moves():
                mover_color = board.turn
                mover = "White" if mover_color == chess.WHITE else "Black"

                # Eval BEFORE move (mover POV)
                before_white = eval_white_pov(engine, board, depth=depth)
                before = mover_pov_from_white(before_white, mover_color)

                san = board.san(move)
                board.push(move)

                # Eval AFTER move (mover POV)
                after_white = eval_white_pov(engine, board, depth=depth)
                after = mover_pov_from_white(after_white, mover_color)

                drop = before - after  # positive means mover got worse

                # Blunder conditions:
                # 1) Big eval drop
                is_big_drop = drop >= blunder_drop

                # 2) Mate transitions only (avoid flagging stable winning conversions)
                is_mate_transition = (
                    abs(before) < 999 and abs(after) >= 999
                ) or (
                    abs(before) >= 999 and abs(after) < 999
                )

                if is_big_drop or is_mate_transition:
                    label = move_label(ply, mover)
                    reason = reason_tag(before, after, drop)

                    print(f"🚨 Move {label} ({mover}) played {san}")
                    print(f"   Reason: {reason}")
                    print(f"   Eval for {mover}: {before:+.2f} → {after:+.2f}  (drop {drop:.2f})")
                    print("   Position after the move:")
                    print(board_with_coords(board))
                    print()

                ply += 1

    print("Analysis complete ♟️")


def main():
    # Friendly prompt when running interactively with no file arg
    if len(sys.argv) == 1 and sys.stdin.isatty():
        print("Paste PGN now, then press Ctrl+D to run...\n")

    pgn_text = read_pgn_text()
    if not pgn_text.strip():
        print("No PGN provided.")
        print("Usage:")
        print("  python3 analyse_game.py game.pgn")
        print("  python3 analyse_game.py   (paste PGN, then Ctrl+D)")
        return

    # Tune these anytime:
    # depth: higher = stronger but slower (try 10–14)
    # blunder_drop: in pawns (try 1.0 for more, 2.0 for fewer)
    analyse_games(pgn_text, depth=12, blunder_drop=1.5)


if __name__ == "__main__":
    main()