'''
爬取帖子
'''
import logging
from typing import Dict, List, Optional

import requests

from . import Settings, parse


class Thread:
    '''同人主题帖中的所有同人内容
    '''
    def __init__(self, tid: int, title: str, author: str):
        self.tid = tid
        self.title = title
        self.author = author
        self.images: Dict[str, str] = dict()
        self.posts: List[str] = list()


def download_thread_images(th: Thread):
    pass


def crawl_thread(tid: int, download_image: bool = True, title: Optional[str] = None) -> Thread:
    sess = requests.Session()
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
    logging.debug(f'爬取《{title}》- {author} - {tid} {author_id}')
    logging.debug('last_post: {}'.format(r['Variables']['thread']['lastpost']))

    r = sess.get(Settings.api,
                 params={
                     'module': 'viewthread',
                     'tid': tid,
                     'page': 1,
                     'ppp': replies,
                     'authorid': author_id,
                 }).json()

    th = Thread(tid, title, author)

    for post in r['Variables']['postlist']:
        text: str = post['message']
        if parse.predict_tongren(text):
            th.posts.append(parse.parse_tongren(text))
    if download_image:
        download_thread_images(th)
    return th
