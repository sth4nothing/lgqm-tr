import logging
import re
import uuid
from typing import Callable, Dict, List, Optional, Union
from urllib.parse import urljoin

import lxml.etree
import lxml.html

from . import Settings, Thread, Post

_IMG_EXTS = {'jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp'}


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


def _hash_image_link(link: str) -> str:
    '''由链接生成唯一的文件名
    '''
    ext = re.split(r'[/\.]', link)[-1].lower()
    if ext not in _IMG_EXTS:
        ext = '.jpg'
    name = uuid.uuid5(uuid.NAMESPACE_URL, link).hex
    return name + '.' + ext


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
    return ''.join(
        item.strip() if issubclass(type(item), str) else _parse_node(item)
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
    '''`<a href="url">contents</a>`
    '''
    return '[{} {}]'.format(urljoin(Settings.server, node.attrib.get('href')),
                            contents)


def _parser_b(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<b>contents</b>`
    '''
    return "'''{}'''".format(contents)


def _parser_blockquote(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<blockquote>contents</blockquote>`
    '''
    return '{{{{同人注释start}}}}{}{{{{同人注释end}}}}'.format(contents)


def _parser_i(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<i>contents</i>`
    '''
    if node.attrib.get('class') == 'pstatus':
        return ''
    return "''{}''".format(contents)


def _parser_img(node: lxml.html.HtmlElement, contents: str):
    '''`<img src="url" title="title" />`
    '''
    src: Optional[str] = node.attrib.get('file') or node.attrib.get('src')
    title: Optional[str] = node.attrib.get('title')
    # 无效的图片或者论坛表情
    if src is None or predict_bbs_smiley(src):
        return ''

    name = hash_image_link(urljoin(Settings.server, src))
    if title is None:
        return '[[Image:{}|class=img-responsive|thumb|100%|center]]'.format(
            name)
    return '[[Image:{}|class=img-responsive|thumb|100%|center|{}]]'.format(
        name, title)


def _parser_font(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<font>contents</font>`
    '''
    return contents


def _parser_u(node: lxml.html.HtmlElement, contents: str) -> str:
    return '<u>' + contents + '</u>'


def _parser_div(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<div>contents</div>`
    '''
    return contents


def _parser_ol(node: lxml.html.HtmlElement, contents: str) -> str:
    return '\n<ol>\n' + contents.strip() + '\n</ol>\n'


def _parser_ul(node: lxml.html.HtmlElement, contents: str) -> str:
    return '\n<ul>\n' + contents.strip() + '\n</ul>\n'


def _parser_li(node: lxml.html.HtmlElement, contents: str) -> str:
    return '<li>' + contents.strip() + '</li>\n'


def _parser_br(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<br >`
    '''
    return '\n\n'


def _parser_p(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<p>contents</p>`
    '''
    return '\n\n{}\n\n'.format(contents.strip())


def _parser_h1(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<p>contents</p>`
    '''
    eq = '=' * 1
    return '\n\n' + eq + contents.strip() + eq + '\n\n'


def _parser_h2(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<p>contents</p>`
    '''
    eq = '=' * 2
    return '\n\n' + eq + contents.strip() + eq + '\n\n'


def _parser_h3(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<p>contents</p>`
    '''
    eq = '=' * 3
    return '\n\n' + eq + contents.strip() + eq + '\n\n'


def _parser_h4(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<p>contents</p>`
    '''
    eq = '=' * 4
    return '\n\n' + eq + contents.strip() + eq + '\n\n'


def _parser_h5(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<p>contents</p>`
    '''
    eq = '=' * 5
    return '\n\n' + eq + contents.strip() + eq + '\n\n'


def _parser_h6(node: lxml.html.HtmlElement, contents: str) -> str:
    '''`<p>contents</p>`
    '''
    eq = '=' * 6
    return '\n\n' + eq + contents.strip() + eq + '\n\n'


def _predict_bbs_smiley(link: str):
    '''判断是否是表情
    '''
    return bool(re.search(r'static/image/[\w/]+.gif$', link))


def _parse_all_images(html: str) -> List[str]:
    '''搜索所有图片
    '''
    return list(
        urljoin(Settings.server, m.group('src'))
        for m in re.finditer(r'<img[^>]+src="(?P<src>[^"]+)"', html)
        if not predict_bbs_smiley(m.group('src')))


def _sub_attach(post: Post):
    '''替换回复中的附件图片`[attach]aid[/attach]`
    '''
    def _sub_attach_repl(match: re.Match) -> str:
        '''将`[attach]aid[/attach]`替换为html的`img`标签
        '''
        aid = match.group('aid')
        if aid not in post.image_aids:
            # 无效的附件
            return ''

        # 回复正文中已经添加了图片，故从集合中移除避免重复添加图片
        post.image_aids.remove(aid)
        img = post.post_dict['attachments'][aid]
        img_url = img['url'] + img['attachment']
        img_title: Optional[str] = img.get('filename')
        if img_title is None:
            return '<img src="{}" />'.format(img_url)
        return '<img src="{}" title="{}" />'.format(img_url, img_title)

    def _sub_attach_inner(post_html: str):
        return re.sub(r'\[attach\](?P<aid>\d+)\[/attach\]',
                      _sub_attach_repl,
                      post_html,
                      flags=re.M)

    post.post_html = _sub_attach_inner(post.post_html)


def _parse_post(post: Post) -> None:
    '''解析回复
    '''
    sub_attach(post)
    post.post_text = parse_tongren(post.post_html)
    post.images.update((hash_image_link(url), url)
                       for url in parse_all_images(post.post_html))
    # 处理附件图片
    for aid in post.image_aids:
        img = post.post_dict['attachments'][aid]
        img_url = urljoin(Settings.server, img['url'] + img['attachment'])
        img_name = hash_image_link(img_url)
        img_title: Optional[str] = img.get('filename')
        post.images[img_name] = img_url
        if img_title is None:
            post.post_text += '\n[[Image:{}|class=img-responsive|thumb|100%|center]]'.format(
                img_name)
        else:
            post.post_text += '\n[[Image:{}|class=img-responsive|thumb|100%|center|{}]]'.format(
                img_name, img_title)


node_parser: Dict[str, Callable[[lxml.html.HtmlElement, str], str]] = {
    'A': _parser_a,
    'B': _parser_b,
    'BLOCKQUOTE': _parser_blockquote,
    'BR': _parser_br,
    'DIV': _parser_div,
    'FONT': _parser_font,
    'H1': _parser_h1,
    'H1': _parser_h2,
    'H1': _parser_h3,
    'H1': _parser_h4,
    'H1': _parser_h5,
    'H1': _parser_h6,
    'I': _parser_i,
    'IMG': _parser_img,
    'LI': _parser_li,
    'OL': _parser_ol,
    'P': _parser_p,
    'STRONG': _parser_b,
    'U': _parser_u,
    'UL': _parser_ul,
}
hash_image_link = _hash_image_link
parse_all_images = _parse_all_images
parse_post = _parse_post
parse_title = _parse_title
parse_tongren = _parse_tongren
predict_bbs_smiley = _predict_bbs_smiley
predict_tongren = _predict_tongren
safe_name = _safe_name
sub_attach = _sub_attach
