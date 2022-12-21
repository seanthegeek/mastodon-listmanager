import logging
import json
import urllib.parse
from typing import Union, List, AnyStr
from datetime import datetime

import click

from mastodon import Mastodon, AttribAccessDict

"""A Python module and CLI tool for managing Mastodon lists"""

__version__ = "1.0.0"


class _CLIConfig(object):
    def __init__(self, config):
        logging.basicConfig(level=logging.WARNING,
                            format="%(levelname)s: %(message)s")
        with open(config) as config_file:
            config = json.loads(config_file.read())

        _mastodon = Mastodon(api_base_url=config["base_url"],
                             client_id=config["client_id"],
                             client_secret=config["client_secret"],
                             access_token=config["access_token"])
        try:
            self.mastodon = SimpleMastodon(_mastodon)
        except Exception as e:
            logging.error(e)
            exit(-1)


def _format_record(record: Union[AttribAccessDict, List,
                                 datetime]) -> Union[
                                              AttribAccessDict, List, AnyStr]:
    if isinstance(record, datetime):
        record = record.strftime(r"%Y-%m-%d %H:%M:%S")
    elif isinstance(record, list):
        for i in range(len(record)):
            _format_record(record[i])
        return record
    elif isinstance(record, AttribAccessDict):
        for key in record.keys():
            record[key] = _format_record(record[key])
        if "url" in record.keys():
            url = urllib.parse.urlparse(record["url"])
            domain = url.hostname
            record["domain"] = domain
            if "acct" in record.keys():
                if "@" not in record["acct"]:
                    username = record["username"]
                    record["acct"] = f"{username}@{domain}"
    return record


class SimpleMastodon(object):
    """A simplified Mastodon interface"""

    def __init__(self, mastodon: Mastodon):
        self.mastodon = mastodon
        self.mastodon.account_verify_credentials()

    def get_account(self, full_username: str) -> Union[AttribAccessDict, None]:
        if "@" not in full_username:
            raise ValueError("Must use the user@domain format")
        results = self.mastodon.account_search(full_username, limit=1)
        if len(results) == 0:
            return None
        return _format_record(results[0])

    def follow_account(self, full_username: str):
        self.mastodon.account_follow(self.get_account(full_username))

    def unfollow_account(self, full_username: str):
        self.mastodon.account_unfollow(self.get_account(full_username))

    def get_followed_accounts(self) -> list[AttribAccessDict]:
        return _format_record(self.mastodon.account_following(self.mastodon.me()))

    def get_lists(self) -> List[AttribAccessDict]:
        lists = self.mastodon.lists()
        for _list in lists:
            _list["accounts"] = _format_record(self.mastodon.list_accounts(_list["id"]))
        return lists

    def get_list(self, list_name: str, create: bool = True) -> AttribAccessDict:
        _list = list(filter(lambda x: x["name"] == list_name, self.mastodon.lists()))
        if len(_list) == 0:
            if not create:
                ValueError(f"A list named {list_name} does not exist")
            self.mastodon.list_create(list_name)
            return self.get_list(list_name)
        _list = _list[0]
        _list["accounts"] = _format_record(self.mastodon.list_accounts(_list["id"]))
        return _list

    def delete_list(self, list_name: str):
        _list = self.get_list(list_name, create=False)
        self.mastodon.list_delete(_list["id"])

    def add_account_to_list(self, full_username, list_name, create_list: bool = True):
        account = self.get_account(full_username)
        self.mastodon.account_follow(account["id"])
        _list = self.get_list(list_name, create=create_list)
        self.mastodon.list_accounts_add(_list["id"], [account["id"]])

    def remove_account_from_list(self, full_username, list_name):
        account = self.get_account(full_username)
        _list = self.get_list(list_name, create=False)
        self.mastodon.list_accounts_delete(_list["id"], [account["id"]])

    def account_in_list(self, account_id: int,
                        lists: list[AttribAccessDict] = None,
                        list_id: int = None) -> bool:
        if lists is None:
            lists = self.get_lists()
        if list_id is not None:
            _list = list(filter(lambda x: x["id"] == list_id, lists))
            if len(_list) == 0:
                raise ValueError(f"List ID {list_id} was not found")
            _list = _list[0]
            return account_id in [account["id"] for account in _list["accounts"]]
        for list_ in lists:
            if self.account_in_list(account_id, lists=lists, list_id=list_["id"]):
                return True
        return False

    def get_unlisted_accounts(self) -> List[AttribAccessDict]:
        _unlisted_accounts = []
        lists = self.get_lists()
        for account in self.get_followed_accounts():
            if not self.account_in_list(account["id"], lists=lists):
                _unlisted_accounts.append(account)
        return _unlisted_accounts


@click.group()
@click.version_option(version=__version__)
@click.option("--config", "-c", default="config.json", help="Path to a configuration file.")
@click.pass_context
def _main(ctx, config):
    """A simple CLI for managing Mastodon lists"""
    ctx.obj = _CLIConfig(config)


@_main.command("whoami",
               help="Returns the full username of thc configured account")
@click.pass_context
def _whoami(ctx):
    account = ctx.obj.mastodon.mastodon.me()
    account = _format_record(account)
    click.echo(account["acct"])


if __name__ == "__main__":
    _main()