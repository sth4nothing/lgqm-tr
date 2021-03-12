import logging
import os
import sys
from pathlib import Path

from requests.sessions import Session

import lgqm_tr

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

tid = 7319
download_image = True
cookies_path = lgqm_tr.Settings.cookies_path
sess = Session()
sess.headers.update({
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36 Edg/89.0.774.45',
})
if os.path.exists(cookies_path):
    lgqm_tr.utils.load_cookies(sess, cookies_path)
if download_image:
    r = sess.get(lgqm_tr.Settings.api,
                 params={
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
        lgqm_tr.utils.save_cookies(sess, cookies_path)

th = lgqm_tr.crawl.crawl_thread(tid, sess)

thread_dir = Path('./data/', str(tid))

if not thread_dir.exists():
    os.makedirs(str(thread_dir))

# 将生成的文本保存到本地
file_path = thread_dir.joinpath('{}-{}.mediawiki'.format(th.title, th.author))
file_path.write_text('\n\n\n'.join(th.posts), encoding='UTF-8')

# 下载图片
for name, url in th.images.items():
    logging.info(f'download img {name} -> {url}')
    img_path = thread_dir.joinpath(name)
    r = sess.get(url, headers={
        'accept': 'image/*',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-dest': 'image',
    }, verify=False)
    img_path.write_bytes(r.content)
