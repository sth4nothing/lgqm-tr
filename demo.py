import logging
import os
import sys
from pathlib import Path

import lgqm_tr

logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
    stream = sys.stdout
)

tid = 7319

th = lgqm_tr.threads.crawl_thread(tid)

thread_dir = Path('./data/', str(tid))

if not thread_dir.exists():
    os.makedirs(str(thread_dir))

file_path = thread_dir.joinpath('{}-{}.txt'.format(th.title, th.author))
file_path.write_text('\n\n\n'.join(th.posts))
