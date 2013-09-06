import unittest

from mailpile.util import STOPLIST
from tests.support import (get_mbox, get_config, get_session, get_mail_index,
                           scan_mailbox, get_test_data_inverted_index)


class test_MailIndex(unittest.TestCase):

    def setUp(self):
        self.config = get_config()
        self.session = get_session()
        self.mbox = get_mbox()
        self.mindex = get_mail_index()

    def test_scan_mailbox(self):
        added = scan_mailbox()
        self.assertEqual(len(self.mbox), added)

    def test_search(self):
        scan_mailbox()
        iindex = get_test_data_inverted_index()
        for c, (word, msg_ids) in enumerate(iindex.iteritems()):
            if word.lower() in STOPLIST:
                continue
            hits = self.mindex.search(self.session, [word])
            amsg = "{} != {} - {} - {}".format(hits, msg_ids, word, c)
            self.assertEqual(sorted(hits), sorted(msg_ids), amsg)
