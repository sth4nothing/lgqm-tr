from lgqm_tr.utils import load_cookies, save_cookies
import logging
import os
import sys
from pathlib import Path

from requests.sessions import Session

import lgqm_tr

logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
    stream = sys.stdout
)

tid = 7319
download_image = True
cookies_path = lgqm_tr.Settings.cookies_path
sess = Session()
if os.path.exists(cookies_path):
    load_cookies(sess, cookies_path)
if download_image:
    r = sess.get(lgqm_tr.Settings.api, params={
                      'module': 'login',
                      'type': 'login',
                  }).json()
    if r['Message'].get('messageval') != 'login_succeed':
        # 登录
        r = sess.post(lgqm_tr.Settings.api,
                    params={
                        'module': 'login',
                        'type': 'login',
                    },
                    data={
                        'username': 'xxxxxxx@yy.com',
                        'password': 'your_password',
                        'loginsubmit': 'yes',
                        'loginfield': 'auto',
                        'questionid': 0,
                        'answer': ''
                    }).json()
        assert r['Message'].get('messageval') == 'login_succeed'
        save_cookies(sess, cookies_path)

th = lgqm_tr.threads.crawl_thread(tid)

thread_dir = Path('./data/', str(tid))

if not thread_dir.exists():
    os.makedirs(str(thread_dir))

# 将生成的文本保存到本地
file_path = thread_dir.joinpath('{}-{}.mediawiki'.format(th.title, th.author))
file_path.write_text('\n\n\n'.join(th.posts))

# 下载图片
for name, url in th.images.items():
    logging.info(f'download img {name} -> {url}')
    img_path = thread_dir.joinpath(name)
    r = sess.get(url)
    img_path.write_bytes(r.content)
