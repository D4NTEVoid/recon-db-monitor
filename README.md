# Recon DB Monitor

A lightweight Python utility for collecting, normalizing, and tracking discovered subdomains in a centralized SQLite database.

Designed to complement automated reconnaissance pipelines, this utility processes discovered URLs and hostnames, extracts their registered domains using Unfurl, and stores unique hostname records.

## Features

- **Hostname Extraction:** Extracts hostnames from URLs and domain inputs.
- **Domain Normalization:** Normalizes hostnames to lowercase and IDNA format.
- **Registered Domain Identification:** Uses Unfurl to identify registered domains.
- **SQLite Integration:** Stores reconnaissance results in a centralized database.
- **Duplicate Prevention:** Uses database uniqueness constraints to prevent duplicate records.
- **Timestamp Tracking:** Records when each hostname was first added.
- **Batch Processing:** Processes multiple hostnames in a single Unfurl execution.
- **Configurable Database:** Supports custom database locations through environment variables.

## Requirements

- Python 3.9+
- SQLite3
- [Unfurl](https://github.com/tomnomnom/unfurl)

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/recon-db-monitor.git
cd recon-db-monitor
```

Make the script executable:

```bash
chmod +x add_to_recon.py
```

Ensure Unfurl is installed and accessible through your system PATH.

## Configuration

The default database location is:

```text
/databases/recon.db
```

You can override it using:

```bash
export RECON_DB_PATH="$HOME/recon/recon.db"
```

The database and its parent directory are created automatically if they do not exist.

## Usage

```bash
python3 add_to_recon.py <input_file>
```

Example:

```bash
python3 add_to_recon.py live_subdomains.txt
```

The input file can contain URLs or hostnames:

```text
https://api.example.com
https://dev.example.com/login
http://www.example.com
api.example.com
```

## Database Structure

The utility creates a `subdomains` table when it does not already exist.

| Column | Description |
|---|---|
| `id` | Unique record identifier |
| `domain` | Registered/root domain |
| `subdomain` | Normalized hostname |
| `date_added` | UTC timestamp of insertion |

A unique constraint on `(domain, subdomain)` prevents duplicate hostname records.

## Integration with Recon Pipelines

This utility can be used alongside automated reconnaissance tools.

For example:

```bash
./Recon.sh example.com

python3 add_to_recon.py \
    /targets/example.com/live_subdomains.txt
```

This allows discovered hostnames to be imported into a centralized SQLite database for subsequent asset tracking and analysis.

## Example Output

```text
[*] Unique hostnames found: 25
[+] Database update completed.
[+] Processed hostnames: 25
[+] Valid records: 25
[+] New records added: 18
[+] Database: /databases/recon.db
```

## Responsible Use

This utility is intended for authorized reconnaissance, asset management, penetration testing, and bug bounty research.

Only collect and process information from assets you are authorized to assess.

## License

MIT License (subject to confirmation of licensing rights and third-party dependency terms).
