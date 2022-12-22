# mastodon-listmanager

One of the biggest points of friction when using [Mastodon][1] is the
[inability][2] to directly view and interact with the follows/follower lists of
users on other Mastodon servers/instances. `mastodon-listmanager`is a CLI
script built as a workaround for this problem.

## Features

- Export the complete following or followers list of another user to a CSV
  file — even if that user is on a different server!
- Export and import lists as CSV files

## Installation

Install Python. It is already installed in macOS and Linux. When using the
Python installer for Windows, make sure that the option to add Python to the
PATH is checked.

After Python is installed, download a copy of this repository, open a
terminal/command prompt , `cd` into the directory, and install the Python
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

Add the displayed API s to a file called `config.json` in the same
directory as `listmanager.py`.

Use this template for the file

```json
{
  "base_url": "https://infosec.exchange",
  "client_id": "REDACTED",
  "client_secret": "REDACTED",
  "access_token": "REDACTED"
}
```

Replace the `base_url` value with the URL of your instance/server.

Note: If you ever need to change the scopes of a Mastodon application, submit
the changes, and then generate a new access token by clicking on the
refresh icon next to the the access token.

## Usage

> python listmanager,py

[1]: https://github.com/mastodon/mastodon
[2]: https://github.com/mastodon/mastodon/issues/19880
