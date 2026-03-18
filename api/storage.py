from pathlib import Path

def dir_size_bytes(path:Path) -> int:
    if not path.exists():
        return 0

    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total