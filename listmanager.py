#!/usr/bin/env python3
import logging
import traceback
import json
import csv
import os.path
import urllib.parse
from typing import Union, List, Dict, AnyStr, TextIO
from io import StringIO
from datetime import datetime

import click

from mastodon import Mastodon, AttribAccessDict, MastodonAPIError

"""A Python module and CLI tool for managing Mastodon lists"""

__version__ = "1.4.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
formatter = logging.Formatter(
    fmt='%(levelname)s:%(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


class _CLIConfig(object):
    def __init__(self, config):
        try:
            with open(config) as config_file:
                config = json.loads(config_file.read())
                if "client_key" not in config and "client_id" in config:
                    config["client_key"] = config["client_id"]
        except FileNotFoundError:
            logger.error(f"File not found: {config_file}")
            exit(-1)

        _mastodon = Mastodon(api_base_url=config["base_url"],
                             client_id=config["client_key"],
                             client_secret=config["client_secret"],
                             access_token=config["access_token"])
        try:
            self.mastodon = SimpleMastodon(_mastodon)
        except Exception as e:
            logger.error(e)
            exit(-1)


def _format_record(record: Union[AttribAccessDict, List, datetime],
                   me: AttribAccessDict = None) -> Union[AttribAccessDict,
                                                         List]:
    if isinstance(record, datetime):
        record = record.strftime(r"%Y-%m-%d %H:%M:%S")
    elif isinstance(record, list):
        for i in range(len(record)):
            _format_record(record[i], me=me)
        return record
    elif isinstance(record, AttribAccessDict):
        for key in record.keys():
            record[key] = _format_record(record[key])
        if "url" in record.keys():
            # acct does not include the domain if the account is on the
            # same server, so we need to add it for portability
            url = urllib.parse.urlparse(record["url"])
            domain = url.hostname
            record["domain"] = domain
            if "acct" in record.keys():
                username = record["username"]
                if me is not None:
                    my_domain = me["domain"]
                    if record["domain"] != my_domain:
                        local_url = f"https://{my_domain}/@{username}@{domain}"
                    else:
                        local_url = f"https://{my_domain}/@{username}"
                    record["local_url"] = local_url
                if "@" not in record["acct"]:
                    record["acct"] = f"{username}@{domain}"
    return record


def _accounts_to_csv_rows(accounts: Union[List[AttribAccessDict],
                                          AttribAccessDict],
                          me: AttribAccessDict = None) -> List[Dict]:
    if isinstance(accounts, AttribAccessDict):
        accounts = [accounts]
    _accounts = accounts.copy()
    _accounts = _format_record(_accounts, me)
    csv_list = []
    for i in range(len(_accounts)):
        account = _accounts[i]
        if "local_url" not in account.keys():
            account["local_url"] = ""
        row = {"Account address": account["acct"],
               "Show boosts": "true",
               "Notify on new posts": "false",
               "Languages": "",
               "Display name": account["display_name"],
               "Bio": account["note"].replace("\n", " "),
               "URL": account["url"],
               "Local URL": account["local_url"],
               "Avatar URL": account["avatar"]}
        csv_list.append(row)
    return csv_list


def accounts_to_csv(accounts: Union[List[AttribAccessDict],
                                    AttribAccessDict],
                    me: AttribAccessDict = None) -> str:
    fields = ["Account address",
              "Show boosts",
              "Notify on new posts",
              "Languages",
              "Display name",
              "Bio",
              "Local URL",
              "URL",
              "Local URL",
              "Avatar URL"]
    with StringIO() as csv_file:
        account_csv = csv.DictWriter(csv_file, fieldnames=fields)
        account_csv.writeheader()
        account_csv.writerows(_accounts_to_csv_rows(accounts, me=me))
        csv_file.seek(0)
        return csv_file.read()


class MastodonResourceNotFound(Exception):
    """Raised when a requested resource cannot be found"""


class SimpleMastodon(object):
    """A simplified Mastodon interface"""

    def __init__(self, mastodon: Mastodon):
        self.mastodon = mastodon
        self.me = _format_record(mastodon.me())

    def get_account(self, account_address: str) -> Union[AttribAccessDict,
                                                         None]:
        account_address = account_address.lstrip("@")
        if "@" not in account_address:
            raise ValueError("Must use the full account address (user@domain)")
        results = self.mastodon.account_search(account_address, limit=1)
        if len(results) == 0:
            raise MastodonResourceNotFound(f"{account_address} not found")
        return _format_record(results[0], me=self.me)

    def follow_account(self, account_address: str,
                       boosts: bool = True, notify: bool = False):
        self.mastodon.account_follow(self.get_account(account_address),
                                     reblogs=boosts, notify=notify)

    def unfollow_account(self, account_address: str):
        self.mastodon.account_unfollow(self.get_account(account_address))

    def get_following_accounts(self,
                               address: str = None) -> list[AttribAccessDict]:
        if address is None:
            return _format_record(self.mastodon.fetch_remaining(
                self.mastodon.account_following(
                    self.me)), me=self.me)
        address = address.lstrip("@")
        domain = address.split("@")[1]
        if domain == self.me["domain"]:
            _mastodon = self.mastodon
        else:
            # Get list directly from the remote instance/server
            _mastodon = Mastodon(api_base_url=f"https://{domain}")
        accounts = _mastodon.account_following(
            _mastodon.account_lookup(address)["id"])
        accounts = _mastodon.fetch_remaining(accounts)
        return _format_record(accounts, me=self.me)

    def get_follower_accounts(self,
                              address: str = None) -> list[AttribAccessDict]:
        if address is None:
            return _format_record(self.mastodon.fetch_remaining(
                self.mastodon.account_followers(
                    self.me)), me=self.me)
        address = address.lstrip("@")
        domain = address.split("@")[1]
        if domain == self.me["domain"]:
            _mastodon = self.mastodon
        else:
            # Get the list directly from the remote instance/server
            _mastodon = Mastodon(api_base_url=f"https://{domain}")
        accounts = _mastodon.account_followers(
            _mastodon.account_lookup(address)["id"])
        accounts = _mastodon.fetch_remaining(accounts)
        return _format_record(accounts, me=self.me)

    def unfollow_all_accounts(self):
        for account in self.get_following_accounts():
            self.unfollow_account(account["acct"])

    def get_lists(self) -> List[AttribAccessDict]:
        lists = self.mastodon.lists()
        for _list in lists:
            _list["accounts"] = _format_record(
                self.mastodon.fetch_remaining(
                    self.mastodon.list_accounts(
                        _list["id"])), me=self.me)
        return lists

    def get_list(self, name: str, create: bool = True) -> AttribAccessDict:
        _list = list(filter(lambda x: x["title"]
                     == name, self.mastodon.lists()))
        if len(_list) == 0:
            if not create:
                raise ValueError(f"A list named {name} does not exist")
            self.mastodon.list_create(name)
            return self.get_list(name)
        _list = _list[0]
        accounts = self.mastodon.list_accounts(_list["id"])
        accounts = self.mastodon.fetch_remaining(accounts)
        _list["accounts"] = _format_record(accounts, me=self.me)
        return _list

    def delete_list(self, list_name: str):
        _list = self.get_list(list_name, create=False)
        self.mastodon.list_delete(_list["id"])

    def add_account_to_list(self, account_address: str,
                            _list: AttribAccessDict = None,
                            list_name: str = None, create_list: bool = True):
        if _list is None and list_name is None:
            raise ValueError("Must supply list or list_name")
        account = self.get_account(account_address)
        if _list is None:
            _list = self.get_list(list_name, create=create_list)
        if not self.account_in_list(account["id"], lists=[_list]):
            # Accounts must be followed before they can be added to a list
            self.mastodon.account_follow(account["id"])
            try:
                self.mastodon.list_accounts_add(_list["id"], [account["id"]])
            except MastodonAPIError as e:
                if e.args[1] == 404:
                    raise MastodonResourceNotFound(
                        "Cannot add "
                        f"{account_address} to a list while "
                        "the follow request is pending.")
                # Ignore errors indicating that an account is already in a list
                if e.args[1] not in [404, 422]:
                    raise e

    def remove_account_from_list(self, account_address, list_name):
        account = self.get_account(account_address)
        _list = self.get_list(list_name, create=False)
        self.mastodon.list_accounts_delete(_list["id"], [account["id"]])

    def remove_all_accounts_from_list(self, list_name: str):
        _list = self.get_list(list_name, create=False)
        for account in _list["accounts"]:
            self.remove_account_from_list(account["acct"], list_name)

    def account_in_list(self, _id: int,
                        lists: list[AttribAccessDict] = None,
                        list_id: int = None) -> bool:
        if lists is None:
            lists = self.get_lists()
        if list_id is not None:
            _list = list(filter(lambda x: x["id"] == list_id, lists))
            if len(_list) == 0:
                raise MastodonResourceNotFound(
                    f"List ID {list_id} was not found")
            _list = _list[0]
            return _id in [account["id"] for account in _list["accounts"]]
        for list_ in lists:
            if self.account_in_list(_id,
                                    lists=lists, list_id=list_["id"]):
                return True
        return False

    def get_unlisted_accounts(self) -> List[AttribAccessDict]:
        _unlisted_accounts = []
        lists = self.get_lists()
        for account in self.get_following_accounts():
            if not self.account_in_list(account["id"], lists=lists):
                _unlisted_accounts.append(account)
        return _unlisted_accounts

    def import_following_csv(self, following_csv: Union[AnyStr, TextIO]):
        if isinstance(following_csv, str):
            following_csv = StringIO(following_csv)
        accounts = csv.DictReader(following_csv)
        for account in accounts:
            account_address = account["Account address"]
            boosts = True
            notify = False
            if "Show boosts" in account.keys():
                if account["Show boosts"].lower() == "false":
                    boosts = False
                if "Notify on new posts" in account.keys():
                    notify = account["Notify on new posts"].lower() == "true"
            try:
                self.follow_account(
                    account_address, boosts=boosts, notify=notify)
            except Exception as e:
                logger.warning(f"Unable to follow {account_address}: {e}")

    def export_following_csv(self, account_address: str = None) -> str:
        accounts = self.get_following_accounts(account_address)
        return accounts_to_csv(accounts, me=self.me)

    def export_unlisted_accounts_csv(self):
        return accounts_to_csv(self.get_unlisted_accounts(), me=self.me)

    def export_follower_csv(self, account_address: str = None) -> str:
        accounts = self.get_follower_accounts(account_address)
        return accounts_to_csv(accounts, me=self.me)

    def import_list_csv(self, list_csv: Union[AnyStr, TextIO], list_name):
        if isinstance(list_csv, str):
            list_csv = StringIO(list_csv)
        accounts = csv.DictReader(list_csv)
        _list = self.get_list(list_name, create=True)
        for account in accounts:
            account_address = account["Account address"]
            try:
                logger.debug(f"Adding {account_address} to {list_name}")
                self.add_account_to_list(
                    account_address, _list=_list)
            except Exception as e:
                logger.warning(
                    f"Unable to add {account_address} to {list_name}: {e}")

    def export_list_csv(self, list_name: str = None) -> str:
        accounts = self.get_list(list_name, create=False)["accounts"]
        return accounts_to_csv(accounts, me=self.me)


@click.group()
@click.version_option(version=__version__)
@click.option("--config", "-c",
              default="config.json",
              show_default=True,
              type=click.Path(),
              help="Path to a configuration file.")
@click.option("--debug", is_flag=True,
              help="Show exception tracebacks.")
@click.pass_context
def _main(ctx, config, debug):
    """A simple CLI for managing Mastodon follows and lists"""
    ctx.obj = _CLIConfig(config)
    ctx.obj.debug = debug
    if debug:
        logger.setLevel(logging.DEBUG)


@_main.command("follow")
@click.argument("account")
@click.pass_context
def _follow(ctx, account):
    """Follow an account."""
    try:
        ctx.obj.mastodon.follow_account(account)
    except Exception as e:
        logger.error(e)
        if ctx.obj.debug:
            logger.error(traceback.format_exc())
        exit(-1)


@_main.command("unfollow")
@click.argument("account")
@click.pass_context
def _unfollow(ctx, account):
    """Unfollow an account."""
    try:
        ctx.obj.mastodon.unfollow_account(account)
    except Exception as e:
        logger.error(e)
        if ctx.obj.debug:
            logger.error(traceback.format_exc())
        exit(-1)


@_main.group("export")
def _export():
    """Export accounts being followed or a list to CSV."""


@_export.command("followers", help="Export the list of follower accounts.")
@click.option("--account", "-a", help="The full address of the account.")
@click.option("--file", "-f", help="A file path to write to.")
@click.pass_context
def _export_followers(ctx, account=None, file=None):
    try:
        output = ctx.obj.mastodon.export_follower_csv(account)
        if file is not None:
            with open(file, "w",
                      encoding="utf-8",
                      newline="\n",
                      errors="replace") as output_file:
                output_file.write(output)
        else:
            click.echo(output)
    except Exception as e:
        logger.error(e)
        if ctx.obj.debug:
            logger.error(traceback.format_exc())
        exit(-1)


@_export.command("following",
                 help="Export the list of accounts being followed.")
@click.option("--account", "-a", help="The full address of the account.")
@click.option("--unlisted", "-u", is_flag=True,
              help="Only output accounts that are not in any list.")
@click.option("--file", "-f", help="A file path to write to.")
@click.pass_context
def export_following(ctx, account=None, unlisted=False, file=None):
    """Export the list of accounts being followed."""
    if account is not None and unlisted:
        logger.error(
            "The --unlisted and --account options cannot be used together.")
        exit(1)
    try:
        if unlisted:
            output = ctx.obj.mastodon.export_unlisted_accounts_csv()
        else:
            output = ctx.obj.mastodon.export_following_csv(account)
        if file is not None:
            with open(file, "w",
                      encoding="utf-8",
                      newline="\n",
                      errors="replace") as output_file:
                output_file.write(output)
        else:
            click.echo(output)
    except Exception as e:
        logger.error(e)
        if ctx.obj.debug:
            logger.error(traceback.format_exc())
        exit(-1)


@_export.command("list", help="Export a list.")
@click.option("--name", "-n",
              help="The name of a list. Omit to show a list of lists. \
Use all to export all lists.")
@click.option("--file", "-f", help="A path to write to.")
@click.pass_context
def _export_list(ctx, name=None, file=None):
    if name is None:
        click.echo("Please provide the name of a list to export. \
Use all to to export all lists to CSV files.")
        for _list in ctx.obj.mastodon.get_lists():
            click.echo(f"{_list['title']} - {len(_list['accounts'])} accounts")
        exit(-1)
    elif name.lower() == "all":
        for _list in ctx.obj.mastodon.get_lists():
            path = f"{_list['title']}.csv"
            if file is not None:
                path = os.path.join(file, path)
            try:
                output = ctx.obj.mastodon.export_list_csv(_list["title"])
                with open(path, "w",
                          encoding="utf-8",
                          newline="\n",
                          errors="replace") as output_file:
                    output_file.write(output)
            except Exception as e:
                logger.error(e)
                if ctx.obj.debug:
                    logger.error(traceback.format_exc())
                exit(-1)
    else:
        try:
            output = ctx.obj.mastodon.export_list_csv(name)
            if file is not None:
                with open(file, "w",
                          encoding="utf-8",
                          newline="\n",
                          errors="replace") as output_file:
                    output_file.write(output)
            else:
                click.echo(output)
        except Exception as e:
            logger.error(e)
            if ctx.obj.debug:
                logger.error(traceback.format_exc())
            exit(-1)


@_main.group("import")
def _import():
    """Import a following CSV or list CSV."""


@_import.command("following", help="Import a CSV list of accounts to follow.")
@click.argument("file")
@click.option("--replace", is_flag=True,
              help="Unfollow all accounts before importing the list.")
@click.pass_context
def _import_following_accounts(ctx, file, replace=False):
    try:
        with open(file, errors="ignore") as input_file:
            input_csv = input_file.read()
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        logger.error(e)
        if ctx.obj.debug:
            logger.error(traceback.format_exc())
        exit(-1)
    if replace:
        ctx.obj.mastodon.mastodon.unfollow_all_accounts()
    ctx.obj.mastodon.import_following_csv(input_csv)


@_import.command("list", help="Add accounts from a CSV to a list.")
@click.argument("file")
@click.argument("list_name")
@click.option("--replace", is_flag=True,
              help="Remove all existing accounts from the list before "
                   "importing the new list.")
@click.pass_context
def _import_list(ctx, file, list_name, replace=False):
    try:
        with open(file, errors="ignore") as input_file:
            input_csv = input_file.read()
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        exit(-1)
    if replace:
        ctx.obj.mastodon.mastodon.remove_all_accounts_from_list(list_name)

    ctx.obj.mastodon.import_list_csv(input_csv, list_name)


@_main.command("whoami",
               help="Returns the full username of the configured account.")
@click.pass_context
def _whoami(ctx):
    account = ctx.obj.mastodon.me
    click.echo(account["acct"])


if __name__ == "__main__":
    _main()
