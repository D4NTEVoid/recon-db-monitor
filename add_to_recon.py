
#!/usr/bin/env python3
"""
Recon Database Monitor

Extract registered domains and hostnames from reconnaissance
results and store unique assets in a SQLite database.
"""

import os
import re
import sys
import sqlite3
import subprocess

from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime, timezone


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DB_PATH = Path(
    os.getenv("RECON_DB_PATH", "/databases/recon.db")
)

TABLE_NAME = "subdomains"

# --------------------------------------------------
# Database
# --------------------------------------------------

def ensure_table_exists(cursor):
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            subdomain TEXT,
            date_added TEXT,
            UNIQUE(domain, subdomain)
        )
    """)


# --------------------------------------------------
# Input normalization
# --------------------------------------------------

def extract_hostname(value):
    """Extract and normalize a hostname from a URL or hostname."""

    value = value.strip()

    if not value:
        return None

    try:
        parsed = urlsplit(
            value if "://" in value else f"//{value}"
        )

        hostname = parsed.hostname

        if not hostname:
            return None

        hostname = hostname.rstrip(".").encode("idna").decode("ascii").lower()

        if len(hostname) > 253:
            return None

        if not re.fullmatch(
            r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",
            hostname
        ):
            return None

        return hostname

    except (ValueError, UnicodeError):
        return None


# --------------------------------------------------
# Root domain extraction
# --------------------------------------------------

def get_registered_domains(hostnames):
    """Extract registered domains using Unfurl in one batch."""

    if not hostnames:
        return {}

    input_data = "".join(
        f"https://{hostname}\n"
        for hostname in hostnames
    )

    try:
        result = subprocess.run(
            ["unfurl", "format", "%r.%t"],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=60,
            check=True
        )

    except FileNotFoundError:
        raise RuntimeError("Unfurl is not installed or not in PATH.")

    except subprocess.TimeoutExpired:
        raise RuntimeError("Unfurl execution timed out.")

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Unfurl execution failed: {exc.stderr.strip()}"
        ) from exc

    results = result.stdout.splitlines()

    if len(results) != len(hostnames):
        raise RuntimeError(
            "Unfurl returned an unexpected number of results."
        )

    return dict(zip(hostnames, results))


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file.txt>")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.is_file():
        print(f"[!] Input file not found: {input_file}")
        sys.exit(1)

    try:
        with input_file.open("r", encoding="utf-8") as file:
            hostnames = {
                hostname
                for line in file
                if (hostname := extract_hostname(line))
            }

        if not hostnames:
            print("[!] No valid hostnames found.")
            sys.exit(0)

        print(f"[*] Unique hostnames found: {len(hostnames)}")

        registered_domains = get_registered_domains(
            sorted(hostnames)
        )

        timestamp = datetime.now(timezone.utc).isoformat()

        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(DB_PATH, timeout=30)

        try:
            cursor = conn.cursor()

            ensure_table_exists(cursor)

            records = []

            for hostname, domain in registered_domains.items():

                domain = domain.strip().lower().rstrip(".")

                if not domain:
                    continue

                if not hostname.endswith("." + domain) and hostname != domain:
                    print(f"[!] Invalid domain mapping: {hostname} -> {domain}")
                    continue

                records.append(
                    (domain, hostname, timestamp)
                )

            before = conn.total_changes

            cursor.executemany(
                f"""
                INSERT OR IGNORE INTO {TABLE_NAME}
                (domain, subdomain, date_added)
                VALUES (?, ?, ?)
                """,
                records
            )

            added = conn.total_changes - before

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

        print("[+] Database update completed.")
        print(f"[+] Processed hostnames: {len(hostnames)}")
        print(f"[+] Valid records: {len(records)}")
        print(f"[+] New records added: {added}")
        print(f"[+] Database: {DB_PATH}")

    except (OSError, sqlite3.Error, RuntimeError) as exc:
        print(f"[!] Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
