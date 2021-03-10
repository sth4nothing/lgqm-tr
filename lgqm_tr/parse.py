import logging
import os
import re
from typing import Callable, Dict, List, Union
from urllib.parse import urljoin

import lxml.etree
import lxml.html

from . import Settings


def _safe_name(name: str) -> str:
    ''' 转换成合法的windows文件名
    '''
    conversion = {
        '\\': '',
        '/': '',
        ':': '：',
        '&': '+',
        '*': '',
        '?': '？',
        '|': ' ',
        '\r': ' ',
        '\n': ' ',
        '\'': ' ',
        '"': ' ',
    }

    def repl(m: re.Match):
        origin = m.group()
        if origin in conversion:
            return conversion[origin]
        return origin

    reg = re.compile(r'''[ \\/:&*?<>|\r\n'"]''', re.MULTILINE)
    return reg.sub(repl, name)


def _parse_title(title_full: str) -> str:
    '''从帖子标题中获取同人标题
    '''
    m = re.search(r'^(?:\s*【[^】]*】)?\s*(?P<title>\S+)', title_full)
    if m is None:
        return title_full
    return m.group('title')


def _parse_node(node: lxml.html.HtmlElement) -> str:
    if node.tag.upper() in node_parser:
        lxml.etree._ElementUnicodeResult
        return node_parser[node.tag.upper()](node, _parse_node_contents(node))
    logging.warn(f'未知的TAG: {node.tag}')
    return node.text_content()


def _parse_node_contents(node: lxml.html.HtmlElement) -> str:
    items: List[Union[str, lxml.html.HtmlElement]] = node.xpath(
        'child::text()|child::*')
    return ''.join(item.strip() if issubclass(type(item), str) else _parse_node(item)
                   for item in items)


def _parse_tongren(post: str) -> str:
    '''把Variables->postlist->message转换成wiki的格式
    '''
    root: lxml.html.HtmlElement = lxml.html.fragment_fromstring(
        post, create_parent='div')
    return _parse_node_contents(root)


def _is_quote(root: lxml.html.HtmlElement) -> bool:
    '''判断该post是否为对他人的回复
    '''
    divs: List[lxml.html.HtmlElement] = root.xpath('/div/div[@class="quote"]')
    for div in divs:
        if re.search(r'\S+\s发表于\s\d{4}-\d{1,2}-\d{1,2}', div.text_content()):
            return True
    return False


def _predict_tongren(post: str) -> bool:
    '''预测Variables->postlist->message是否为同人
    '''
    root: lxml.html.HtmlElement = lxml.html.fragment_fromstring(
        post, create_parent='div')
    return not _is_quote(root) and len(
        root.text_content()) >= Settings.limit_length


def _parser_a(node: lxml.html.HtmlElement, contents: str) -> str:
    return '[{} {}]'.format(urljoin(Settings.server, node.attrib.get('href')),
                            contents)


def _parser_b(node: lxml.html.HtmlElement, contents: str) -> str:
    return "'''{}'''".format(contents)


def _parser_blockquote(node: lxml.html.HtmlElement, contents: str) -> str:
    return '{{{{同人注释start}}}}{}{{{{同人注释end}}}}'.format(contents)

def _parser_i(node: lxml.html.HtmlElement, contents: str) -> str:
    if node.attrib.get('class') == 'pstatus':
        return ''
    return "''{}''".format(contents)


def _parser_font(node: lxml.html.HtmlElement, contents: str) -> str:
    return contents


def _parser_div(node: lxml.html.HtmlElement, contents: str) -> str:
    return contents

def _parser_br(node: lxml.html.HtmlElement, contents: str) -> str:
    return '\n\n'


def _parser_p(node: lxml.html.HtmlElement, contents: str) -> str:
    return '\n\n{}\n\n'.format(contents)


safe_name = _safe_name
parse_title = _parse_title
parse_tongren = _parse_tongren
predict_tongren = _predict_tongren
node_parser: Dict[str, Callable[[lxml.html.HtmlElement, str], str]] = {
    'A': _parser_a,
    'B': _parser_b,
    'BLOCKQUOTE': _parser_blockquote,
    'BR': _parser_br,
    'FONT': _parser_font,
    'I': _parser_i,
    'DIV': _parser_div,
    'STRONG': _parser_b,
    'P': _parser_p,
}
