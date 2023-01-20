# Changelog

## 1.3.0

- Only look up the list once when adding multiple users to the same list
  - List imports are **much** faster
- Fix debug output

## 1.2.1

- Fix list exports

## 1.2.0

- Fix bug where only 40 accounts were ever returned in a list (close issue #1) 
- Add `--debug` CLI option

## 1.1.0

- Add `URL` and `Local URL` CSV columns

## 1.0.1

- Provide a helpful error message when attempting to add an account to a list while a follow request is pending
- Fix bug where the `follow` CLI command actually tries to unfollow an account
- PEP 8 code style compliance improvements

## 1.0.0

- Initial release
