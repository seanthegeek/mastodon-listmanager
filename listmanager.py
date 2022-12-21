import json
import urllib.parse
from typing import Union, List, AnyStr
from datetime import datetime

from mastodon import Mastodon, AttribAccessDict

with open("config.json") as config_file:
    config = json.loads(config_file.read())

mastodon = Mastodon(api_base_url=config["base_url"],
                    client_id=config["client_id"],
                    client_secret=config["client_secret"],
                    access_token=config["access_token"])


def _format_record(record: Union[AttribAccessDict, List,
                   datetime]) -> Union[AttribAccessDict, List, AnyStr]:
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


def get_account(full_username: str) -> Union[AttribAccessDict, None]:
    if "@" not in full_username:
        raise ValueError("Must use the user@domain format")
    results = mastodon.account_search(full_username, limit=1)
    if len(results) == 0:
        return None
    return _format_record(results[0])


def follow_account(full_username: str):
    mastodon.account_follow(get_account(full_username))


def unfollow_account(full_username: str):
    mastodon.account_unfollow(get_account(full_username))


def get_followed_accounts() -> list[AttribAccessDict]:
    return _format_record(mastodon.account_following(mastodon.me()))


def get_lists() -> List[AttribAccessDict]:
    lists = mastodon.lists()
    for _list in lists:
        _list["accounts"] = _format_record(mastodon.list_accounts(_list["id"]))
    return lists


def get_list(list_name: str, create: bool = True) -> AttribAccessDict:
    _list = list(filter(lambda x: x["name"] == list_name, mastodon.lists()))
    if len(_list) == 0:
        if not create:
            ValueError(f"A list named {list_name} does not exist")
        mastodon.list_create(list_name)
        return get_list(list_name)
    _list = _list[0]
    _list["accounts"] = _format_record(mastodon.list_accounts(_list["id"]))
    return _list


def delete_list(list_name: str):
    _list = get_list(list_name, create=False)
    mastodon.list_delete(_list["id"])


def add_account_to_list(full_username, list_name, create_list: bool = True):
    account = get_account(full_username)
    mastodon.account_follow(account["id"])
    _list = get_list(list_name, create=create_list)
    mastodon.list_accounts_add(_list["id"], [account["id"]])


def remove_account_from_list(full_username, list_name):
    account = get_account(full_username)
    _list = get_list(list_name, create=False)
    mastodon.list_accounts_delete(_list["id"], [account["id"]])


def account_in_list(account_id: int,
                    lists: list[AttribAccessDict] = None,
                    list_id: int = None) -> bool:
    if lists is None:
        lists = get_lists()
    if list_id is not None:
        _list = list(filter(lambda x: x["id"] == list_id, lists))
        if len(_list) == 0:
            raise ValueError(f"List ID {list_id} was not found")
        _list = _list[0]
        return account_id in [account["id"] for account in _list["accounts"]]
    for list_ in lists:
        if account_in_list(account_id, lists=lists, list_id=list_["id"]):
            return True
    return False


def get_unlisted_accounts() -> List[AttribAccessDict]:
    _unlisted_accounts = []
    lists = get_lists()
    for account in get_followed_accounts():
        if not account_in_list(account["id"], lists=lists):
            _unlisted_accounts.append(account)
    return _unlisted_accounts
