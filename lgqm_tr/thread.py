'''帖子相关的类
'''
from typing import Any, Dict, List

class Thread:
    '''同人主题帖中的所有同人内容
    '''
    def __init__(self, tid: int, title: str, author: str):
        self.tid = tid
        self.title = title
        self.author = author
        self.images: Dict[str, str] = dict()
        self.posts: List[str] = list()


class Post:
    '''帖子中的一条回复
    '''
    def __init__(self, post_dict: Dict[str, Any]):
        self.image_aids = set(post_dict.get('imagelist') or [])
        self.images: Dict[str, str] = dict()
        self.post_dict = post_dict
        self.post_html = post_dict['message']
        self.post_text = ''
