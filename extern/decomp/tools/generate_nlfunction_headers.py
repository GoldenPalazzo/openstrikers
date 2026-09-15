#!/usr/bin/env python3

from pathlib import Path
import sys


def main() -> None:
    source = Path(sys.argv[1])
    data = source.read_bytes()

    for value in sys.argv[2:]:
        output = Path(value)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and output.read_bytes() == data:
            continue
        output.write_bytes(data)


if __name__ == "__main__":
    main()
