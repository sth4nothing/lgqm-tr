'''
爬取帖子
'''
import logging
import os
from typing import Dict, List, Optional
from urllib.parse import urljoin

from requests import Session

from . import Settings, parse, utils


class Thread:
    '''同人主题帖中的所有同人内容
    '''
    def __init__(self, tid: int, title: str, author: str):
        self.tid = tid
        self.title = title
        self.author = author
        self.images: Dict[str, str] = dict()
        self.posts: List[str] = list()


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

    for i, post in enumerate(r['Variables']['postlist']):
        html: str = post['message']
        if parse.predict_tongren(html):
            text = parse.parse_tongren(html)
            th.images.update((parse.hash_image_link(url), url)
                             for url in parse.parse_all_images(html))
            img_cnt = 0
            if post.get('attachments'):  # 附件图片
                for attach in post['attachments'].values():
                    if int(attach.get('attachimg', '0')):
                        img_cnt += 1
                        img_url = urljoin(Settings.server,
                                          attach['url'] + attach['attachment'])
                        img_name = parse.hash_image_link(img_url)
                        img_title: Optional[str] = attach.get('filename')
                        th.images[img_name] = img_url
                        if img_title is None:
                            text += '\n[[Image:{}|class=img-responsive|thumb|100%|center]]'.format(
                                img_name)
                        else:
                            text += '\n[[Image:{}|class=img-responsive|thumb|100%|center|{}]]'.format(
                                img_name, img_title)
            if img_cnt:
                logging.info(f'{i + 1}楼共有{img_cnt}个图片附件')
            th.posts.append(text)
    return th
