'''
爬取帖子
'''
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from requests import Session

from . import Post, Settings, Thread, parse, utils


def crawl_thread(tid: int,
                 sess: Optional[Session] = None,
                 title: Optional[str] = None) -> Thread:
    if sess is None:
        sess = Session()
        # 如果要下载附件图片，则必须要登录
        if os.path.exists(Settings.cookies_path):
            utils.load_cookies(sess, Settings.cookies_path)
    r = sess.get(Settings.api,
                 params={
                     'module': 'viewthread',
                     'tid': tid,
                     'page': 1
                 }).json()
    if title is None:
        title_full: str = r['Variables']['thread']['subject']
        title = parse.parse_title(title_full)
    title = parse.safe_name(title)

    author: str = r['Variables']['thread']['author']
    author_id: str = r['Variables']['thread']['authorid']
    replies: str = r['Variables']['thread']['replies']
    logging.info(f'爬取《{title}》- {author} - {tid} {author_id}')
    logging.info('last_post: {}'.format(r['Variables']['thread']['lastpost']))

    r = sess.get(Settings.api,
                 params={
                     'module': 'viewthread',
                     'tid': tid,
                     'page': 1,
                     'ppp': replies,
                     'authorid': author_id,
                 }).json()

    th = Thread(tid, title, author)

    for i, post_dict in enumerate(r['Variables']['postlist']):
        html: str = post_dict['message']
        if parse.predict_tongren(html):
            post = Post(post_dict)
            parse.parse_post(post)
            th.posts.append(post.post_text)
            if post.images:
                th.images.update(post.images)
                logging.info(f'{i + 1}楼共有{len(post.images)}个图片附件')
    return th
