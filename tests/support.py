import os
import json
import re
import shutil
import tempfile
from collections import defaultdict
from email.message import Message
from datetime import datetime

from mailpile.app import ConfigManager
from mailpile.mailutils import IncrementalMbox
from mailpile.search import MailIndex
from mailpile.ui import Session


def cache(func):
    missing = object()

    def _wrapper(*args, **kwargs):
        if _wrapper._result != missing:
            return _wrapper._result
        _wrapper._result = func(*args, **kwargs)
        return _wrapper._result
    _wrapper._result = missing
    return _wrapper


@cache
def get_workdir():
    tmp_dir = tempfile.mkdtemp(prefix="mailpile_test_")
    get_workdir._workdir = tmp_dir
    print "workdir:", tmp_dir
    return tmp_dir


def rm_workdir():
    workdir = get_workdir._workdir
    if workdir:
        return workdir
    try:
        shutil.rmtree(workdir)
    except OSError:
        pass


@cache
def get_session(config=None):
    if config is None:
        config = get_config()
    return Session(config)


@cache
def get_config():
    workdir = get_workdir()
    config = ConfigManager(workdir=workdir)
    session = get_session(config)
    config.load(session)
    return config


@cache
def get_mbox():
    """ Get an IncrementalMbox instance and add to config.
    """
    mbox_path = os.path.join(get_workdir(), "test_mbox")
    mbox = IncrementalMbox(mbox_path)
    add_test_messages(mbox)

    config = get_config()
    session = get_session()
    config.parse_set(session, "mailbox:0 = {0}".format(mbox._path))
    config.save()
    return mbox


@cache
def get_mail_index():
    config = get_config()
    return MailIndex(config)


def scan_mailbox():
    config = get_config()
    session = get_session()
    mbox = get_mbox()
    mindex = get_mail_index()
    return mindex.scan_mailbox(session, "0", mbox._path, config.open_mailbox)


def _get_name(email):
    name = email.split("@")[0]
    if name.isalpha():
        return name
    name = name.replace(".", " ").replace("_", " ")
    return name


def get_test_data():
    fin = open("tests/data/1000_messages.json", "r")
    return json.load(fin)


def add_test_messages(mbox):
    """ Add test messages to mailbox
    """
    # Test data generated using
    # http://www.databasetestdata.com/
    #
    # Field Name | Type
    # ----------------------
    # Id      - <auto increment>
    # from    - <Email>
    # to      - <Email>
    # date    - <DateTime>
    # subject - <Sentences>
    # message - <Paragraphs>
    #
    test_data = get_test_data()

    for raw_msg in test_data:
        raw_msg["fname"] = _get_name(raw_msg["from"])
        raw_msg["tname"] = _get_name(raw_msg["to"])
        date = datetime.strptime(raw_msg["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
        raw_msg["date"] = date.strftime("%a, %d %b %Y %H:%M:%S")
        raw_msg["subject"] = raw_msg["subject"].replace("\n", " ")

        msg = Message()
        msg.add_header("From", "{fname} <{from}>".format(**raw_msg))
        msg.add_header("To", "{tname} <{to}>".format(**raw_msg))
        msg.add_header("Subject", "{subject}".format(**raw_msg))
        msg.add_header("Date", "{date}".format(**raw_msg))
        msg.add_header("Message-ID",
                       "<{id}@local.machine.example>".format(**raw_msg))
        msg.set_payload(raw_msg["message"])
        mbox.add(msg)

    return mbox


WORD_REGEXP = re.compile('[^\s!@#$%^&*\(\)_+=\{\}\[\]:'
                         '\"|;\'\\\<\>\?,\.\/\-]{2,}')


def _tokenize_message(msg):
    # This is just a copy of how text is tokenized in the mail index.
    # see: mailpile.search:MailIndex.message_keywords
    return list(re.findall(WORD_REGEXP, msg.lower()))


def get_test_data_inverted_index():
    """ Generate inverted index for test data """
    test_data = get_test_data()
    index = defaultdict(set)
    for raw_msg in test_data:
        _id = int(raw_msg["id"])
        txt = " ".join([raw_msg[key]
                        for key in ("message", "subject", "from")])
        tokens = set(_tokenize_message(txt))
        for t in tokens:
            index[t].add(_id)
    return index
