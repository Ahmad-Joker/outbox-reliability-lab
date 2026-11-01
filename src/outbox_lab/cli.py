"""Local CLI, worker and reproducible fault-injection demonstration."""
from __future__ import annotations

import argparse
import json
import os
import time
import uuid

from .service import IdempotencyConflict, InputError, OutboxService


def main() -> None:
    parser = argparse.ArgumentParser(description="Outbox reliability lab")
    parser.add_argument("--db", default=os.environ.get("OUTBOX_DB", "outbox.db"), help="SQLite file path")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    submit = sub.add_parser("submit")
    submit.add_argument("--amount", type=int, required=True, help="integer cents")
    submit.add_argument("--key", required=True, help="idempotency key")
    worker = sub.add_parser("worker")
    worker.add_argument("--failure", choices=["none", "before", "after"], default="none")
    loop = sub.add_parser("loop")
    loop.add_argument("--interval", type=float, default=1.0)
    sub.add_parser("recover")
    sub.add_parser("stats")
    sub.add_parser("events")
    sub.add_parser("demo")
    args = parser.parse_args()
    svc = OutboxService(args.db)
    try:
        if args.cmd == "init":
            result = {"database": args.db, "initialized": True}
        elif args.cmd == "submit":
            result = svc.create_order(args.amount, args.key)
        elif args.cmd == "worker":
            result = svc.process_one(failure=args.failure) or {"outcome": "no_due_events"}
        elif args.cmd == "loop":
            if args.interval <= 0:
                parser.error("--interval must be positive")
            print("Worker loop running; Ctrl-C to stop", flush=True)
            try:
                while True:
                    svc.recover_stale()
                    event = svc.process_one()
                    if event:
                        print(json.dumps(event), flush=True)
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                return
        elif args.cmd == "recover":
            result = {"recovered": svc.recover_stale()}
        elif args.cmd == "stats":
            result = svc.stats()
        elif args.cmd == "events":
            result = svc.list_events()
        else:
            base = time.time()
            first = svc.create_order(1250, "demo-"+str(uuid.uuid4()), now=base)
            failed = svc.process_one(failure="before", now=base)
            retried = svc.process_one(now=base+2)
            second = svc.create_order(2500, "demo-"+str(uuid.uuid4()), now=base+3)
            crash = svc.process_one(failure="after", now=base+3)
            recovered = svc.recover_stale(now=base+34)
            replayed = svc.process_one(now=base+35)
            result = {"first": first, "injected_failure": failed, "retried": retried,
                      "second": second, "simulated_crash": crash, "leases_recovered": recovered,
                      "replayed": replayed, "stats": svc.stats()}
        print(json.dumps(result, indent=2, sort_keys=True))
    except (InputError, IdempotencyConflict) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
