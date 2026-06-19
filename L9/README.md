# rssmds

App for MDS Lab9: A toy CLI RSS feed reader with a web interface.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# subscribe to feeds
python -m rssmds add "https://blog.rust-lang.org/feed.xml"
python -m rssmds add "https://hnrss.org/newest?count=10"

# or discover feeds from a website
python -m rssmds discover "https://xkcd.com"
python -m rssmds discover "https://xkcd.com" --add   # subscribe automatically

# fetch new entries
python -m rssmds fetch

# browse entries
python -m rssmds list
python -m rssmds list --unread
python -m rssmds list --feed 1 --limit 20

# read an entry
python -m rssmds read 3

# manage feeds
python -m rssmds feeds
python -m rssmds remove 2

# mark as read
python -m rssmds mark-read --feed 1
python -m rssmds mark-read --all

# stats
python -m rssmds stats

# export
python -m rssmds export opml
python -m rssmds export json -o entries.json

# web interface
python -m rssmds serve
python -m rssmds serve --port 9000
```

Then open http://127.0.0.1:8080 in a browser.

## Tests

```bash
pytest -v
mypy rssmds/ --strict
```

## Project structure

```
rssmds/
  __main__.py    entry point
  cli.py         argument parsing and subcommands
  config.py      YAML configuration with defaults
  db.py          SQLite schema and queries
  discovery.py   find RSS/Atom feeds from a webpage URL
  fetcher.py     HTTP requests with conditional GET (ETag/Last-Modified)
  formatting.py  terminal output, JSON/OPML export, HTML stripping
  parser.py      RSS 2.0 and Atom XML parsing, date normalization
  web.py         web interface (entries, feeds, stats)
```

## Configuration

Optional. Create `~/.rssmds/config.yml`:

```yaml
db_path: /path/to/rssmds.db
fetch_timeout: 30
max_entries_per_list: 100
```

Without a config file, the database is created as `rssmds.db` in the current directory.
