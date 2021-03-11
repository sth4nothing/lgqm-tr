import json
from pathlib import Path

from requests import Session


def save_cookies(sess: Session, cookies_path: str):
    cookies = [{
        'name': c.name,
        'value': c.value,
        'domain': c.domain,
        'path': c.path
    } for c in sess.cookies]
    with open(cookies_path, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent='  ')


def load_cookies(sess: Session, cookies_path: str):
    with open(cookies_path, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    for c in cookies:
        sess.cookies.set(**c)
