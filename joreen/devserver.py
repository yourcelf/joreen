#!/usr/bin/env python3
import os
import subprocess
import argparse

BASE = os.path.abspath(os.path.dirname(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="localhost:8000")
parser.add_argument("--only", type=str, default="")
parser.add_argument("--not", type=str, default="", dest="not_")


def main():
    # Build default run list
    to_run = {"webpack", "runserver", "celery"}

    # Check for "only" and "not" flags
    args = parser.parse_args()
    if args.only:
        to_run = set(args.only.split(","))
    if args.not_:
        for skip in args.not_.split(","):
            to_run.remove(skip)

    try:
        procs = []
        if "runserver" in to_run:
            procs.append(
                subprocess.Popen(
                    ["python", os.path.join(BASE, "manage.py"), "runserver", args.host],
                    cwd=BASE,
                    env=os.environ,
                )
            )

        if "webpack" in to_run:
            procs.append(
                subprocess.Popen(
                    ["node", os.path.join(BASE, "webpack", "devserver.js")],
                    cwd=BASE,
                    env=os.environ,
                )
            )

        if "celery" in to_run:
            procs.append(
                subprocess.Popen(
                    [
                        "celery",
                        "-A",
                        "joreen",
                        "worker",
                        "-B",
                        "-l",
                        "warn",
                        "-Q",
                        ",".join(("celery",)),
                    ],
                    cwd=BASE,
                    env=os.environ,
                )
            )
        [proc.wait() for proc in procs]
    except Exception:
        for proc in procs:
            proc.kill()
        try:
            raise
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
