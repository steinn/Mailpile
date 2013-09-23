#!/usr/bin/env python
import time

from tests.support import (get_config, get_session, get_mbox, get_mail_index)

config = get_config()
session = get_session()
mbox = get_mbox()
mindex = get_mail_index()

start = time.time()
mindex.scan_mailbox(session, "0", mbox._path, config.open_mailbox)
end = time.time()

print end - start
