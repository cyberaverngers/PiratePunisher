#!/usr/bin/env python3
"""PiratePunisher - minimal single-file demo

Usage:
  python main.py --example

This file is intentionally minimal and safe: it only simulates punishing spammy senders
and performs no network actions. Suitable for quick demos and for running in Colab.
"""
import argparse


def main(example: bool = False) -> int:
    print("PiratePunisher demo")
    if example:
        print("Running example: scanning an 'inbox' and 'punishing' spammers (dry-run)")
        inbox = [
            {"from": "spammer@example.com", "subject": "Buy now"},
            {"from": "friend@example.com", "subject": "Hi"},
        ]
        for m in inbox:
            if "spammer" in m["from"]:
                print(f"[PUNISH] {m['from']} -> simulated block")
            else:
                print(f"[OK] {m['from']}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--example", action="store_true", help="Run demo example")
    args = parser.parse_args()
    raise SystemExit(main(example=args.example))
