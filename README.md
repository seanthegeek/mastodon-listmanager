# mastodon-listmanager

One of the biggest points of friction when using [Mastodon][1] is the
[inability][2] to directly view and interact with the follows/follower lists of
users on other Mastodon servers/instances. `listmanager.py` is a CLI
script built as a workaround for this problem.

## Features

- Export the complete following or followers list of another user to a CSV
  file — even if that user is on a different server!
- Import a list of accounts to follow
- Export and import your lists as CSV files for easy sharing
- Intuitive CLI and API

## Installation

Install Python. It is already installed in macOS and Linux. When using the
Python installer for Windows, make sure that the option to add Python to the
PATH is checked.

After Python is installed, download a copy of this repository, open a
terminal/command prompt, `cd` into the directory, and install the Python
requirements.

> pip install --user -U -r requirements.txt

## Setup

1. Log into your Mastodon instance in a web browser.
2. Click Preferences
3. Click Development
4. Click on the New Application button

Use an application name of your choice, then uncheck all roles. Enable these:

- `read:accounts`
- `read:follows`
- `read:lists`
- `read:search`
- `write:follows`
- `write:lists`
- `follows`

Then click Submit.

Add the displayed API keys to a file called `config.json` in the same
directory as `listmanager.py`.

Use this template for the file:

```json
{
  "base_url": "https://infosec.exchange",
  "client_id": "REDACTED",
  "client_secret": "REDACTED",
  "access_token": "REDACTED"
}
```

Replace the `base_url` value with the URL of your instance/server.

**Note**: If you ever need to change the scopes of a Mastodon application, submit
the changes, and then generate a new access token by clicking on the
refresh icon next to the access token.

Use the `whoami` command to test your credentials.

> python listmanager.py whoami

## CLI help

```text
Usage: listmanager.py [OPTIONS] COMMAND [ARGS]...

  A simple CLI for managing Mastodon follows and lists

Options:
  --version          Show the version and exit.
  -c, --config PATH  Path to a configuration file.  [default: config.json]
  --debug            Show exception tracebacks.
  --help             Show this message and exit.

Commands:
  export    Export accounts being followed or a list to CSV.
  follow    Follow an account.
  import    Import a following accounts CSV or list CSV.
  unfollow  Unfollow an account.
  whoami    Returns the full username of the configured account.
```

```text
Usage: listmanager.py export [OPTIONS] COMMAND [ARGS]...

  Export accounts being followed or a list to CSV.

Options:
  --help  Show this message and exit.

Commands:
  followers  Export the list of follower accounts.
  following  Export the list of accounts being followed.
  list       Export a list.
```

```text
Usage: listmanager.py export followers [OPTIONS]

  Export the list of follower accounts.

Options:
  -a, --account TEXT  The full address of the account.
  -f, --file TEXT     A file path to write to.
  --help              Show this message and exit.
```

```text
Usage: listmanager.py export following [OPTIONS]

  Export the list of accounts being followed.

Options:
  -a, --account TEXT  The full address of the account.
  -u, --unlisted      Only output accounts that are not in any list.
  -f, --file TEXT     A file path to write to.
  --help              Show this message and exit.
```

```text
Usage: listmanager.py export list [OPTIONS]

  Export a list.

Options:
  -n, --name TEXT  The name of a list. Omit to show a list of lists.
  -f, --file TEXT  A file path to write to.
  --help           Show this message and exit.
```

```text
Usage: listmanager.py import [OPTIONS] COMMAND [ARGS]...

  Import a following CSV or list CSV.

Options:
  --help  Show this message and exit.

Commands:
  following  Import a CSV list of accounts to follow.
  list       Add accounts from a CSV to a list.
```

```text
Usage: listmanager.py import following [OPTIONS] FILE

  Import a CSV list of accounts to follow.

Options:
  --replace  Unfollow all accounts before importing the list.
  --help     Show this message and exit.
```

```text
Usage: listmanager.py import list [OPTIONS] FILE LIST_NAME

  Add accounts from a CSV to a list.

Options:
  --replace  Remove all existing accounts from the list before importing the
             new list.
  --help     Show this message and exit.
```

[1]: https://github.com/mastodon/mastodon
[2]: https://github.com/mastodon/mastodon/issues/19880
