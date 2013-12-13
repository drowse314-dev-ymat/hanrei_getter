# encoding: utf-8

import re
import collections
import time
import subprocess
import urlparse
try:
    from html import parser as htmlparser
except ImportError:
    import HTMLParser as htmlparser
import requests
from lxml import html, etree


LIST_HTML_ENCODING = 'sjis'
JIKEN_HTML_ENCODING = 'sjis'

URI_BASE = u'http://www.courts.go.jp'

RE_JIKEN_LINK = re.compile(u'<a href="(\/search\/jhsp0030\?hanreiid=\d+&hanreiKbn=\d+)">')
RE_HANREI_ID = re.compile(u'\/search\/jhsp0030\?hanreiid=(\d+)&hanreiKbn=\d+')


class SleepyRequests(object):

    delay = 30.0

    def __init__(self):
        self._is_tired = False

    @property
    def requests(self):
        return self._requests()

    def _requests(self):
        if self._is_tired:
            delay = self.__class__.delay
            self.apologize(delay)
            time.sleep(delay)
        else:
            self._is_tired = True
        return requests

    def apologize(self, delay):
        print('module requests is sleepy... wait for {} seconds'.format(delay))


sleepy = SleepyRequests()


def make_full_uri(path):
    return urlparse.urljoin(URI_BASE, path)

def read_html(filepath):
    html = open(filepath, 'rb').read().decode(LIST_HTML_ENCODING)
    return html


class ListHandler(object):
    
    def jiken_links_from(self, html_text):
        return RE_JIKEN_LINK.findall(html_text)

    def hanreiid_from(self, jiken_path):
        matched = RE_HANREI_ID.match(jiken_path)
        assert bool(matched)
        return matched.groups()[0]


def fetch_jiken_html(jiken_uri):
    res = sleepy.requests.get(jiken_uri)
    return res.content.decode(JIKEN_HTML_ENCODING)

RE_PAGE_MARKER = re.compile(u'- \d+ -')
def full_text_from_pdfdata(pdfdata):
    pdftotext = subprocess.Popen(
        ['pdftotext', '-', '-'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    content = pdftotext.communicate(input=pdfdata)[0].decode('utf-8')
    lines = []
    for line in content.split(u'\n'):
        line = line.strip()
        if line == u"":
            continue
        if RE_PAGE_MARKER.search(line):
            continue
        lines.append(line)
    full_text = u'\n'.join(lines)
    return full_text


HANREI_ATTRS = [
    'jiken_no', 'jiken_name', 'date', 'court',
    'trial_type', 'decision',
    'reference',
    'origin_court', 'origin_jiken_no', 'origin_date',
    'hanji_jikou', 'abstract', 'referred_legislation',
    'full_text',
]
HANREI_ATTR_NAME_MAP = {
    u'事件番号': 'jiken_no', u'事件名': 'jiken_name',
    u'裁判年月日': 'date', u'法廷名': 'court',
    u'裁判種別': 'trial_type', u'結果': 'decision',
    u'判例集等巻・号・頁': 'reference',
    u'原審裁判所名': 'origin_court', u'原審事件番号': 'origin_jiken_no',
    u'原審裁判年月日': 'origin_date',
    u'判示事項': 'hanji_jikou', u'裁判要旨': 'abstract',
    u'参照法条': 'referred_legislation',
    u'全文': 'full_text',
}
RE_FULL_TEXT_HREF = re.compile(u'href="../([^"]+)"')
HANREI_ATTR_CONVERTERS = {
    'full_text': (
            lambda value: make_full_uri(RE_FULL_TEXT_HREF.search(value).groups()[0])
    ),
}
Hanrei = collections.namedtuple('Hanrei', HANREI_ATTRS)


class JikenParser(object):

    def hanrei_attrs_from(self, html_text):
        clean_text = self._clean_entity(html_text)
        elem = html.fromstring(clean_text)
        for dlist in self._listdiv_from(elem):
            for attrdiv in self._attrdiv_from(dlist):
                attr, attr_val = self._parse_attrdiv(attrdiv)
                yield (attr, attr_val)

    def _clean_entity(self, html_text):
        hp = htmlparser.HTMLParser()
        return hp.unescape(html_text)

    def _listdiv_from(self, any_elem):
        divs = any_elem.findall(u'.//div')
        for div in divs:
            div_attrs = div.attrib
            if u'class' in div_attrs and div_attrs[u'class'] == u'dlist':
                yield div

    def _attrdiv_from(self, dlist_elem):
        for div in dlist_elem.findall(u'./div'):
            if u'class' not in div.attrib:
                yield div

    def _parse_attrdiv(self, attrdiv_elem):
        attr_name_div, attr_value_div = attrdiv_elem.findall(u'.//div')
        assert attr_name_div.attrib[u'class'].startswith(u'list4')
        assert attr_value_div.attrib[u'class'].startswith(u'list5')
        return (
            self._inner_html(attr_name_div).strip(),
            self._inner_html(attr_value_div).strip(),
        )

    def _inner_html(self, elem):
        as_string = self._clean_entity(etree.tostring(elem))
        as_string = as_string[as_string.find(elem.text):]
        as_string = as_string[:as_string.find(u'</{}>'.format(elem.tag))]
        return as_string

    def create_struct_from(self, html_text):
        attrs = {}
        for readable_attr, raw_val in self.hanrei_attrs_from(html_text):
            attr = HANREI_ATTR_NAME_MAP[readable_attr]
            val = HANREI_ATTR_CONVERTERS.get(attr, lambda v:v)(raw_val)
            attrs[attr] = val
        return Hanrei(**attrs)

    def get_full_text(self, pdf_uri):
        res = sleepy.requests.get(pdf_uri)
        return full_text_from_pdfdata(res.content)

    def create_hanrei_element(self, hanrei_html, hanreiid=None):
        hanrei_struct = self.create_struct_from(hanrei_html)
        hanrei = self._create_root_elem(hanreiid)

        meta = self._create_meta_elem(hanrei_struct)
        origin_meta = self._create_origin_meta_elem(hanrei_struct)
        hanji_jikou = etree.Element(u'HanjiJikou')
        abstract = etree.Element(u'Abstract')
        referred_legislation = etree.Element(u'ReferredLegislations')
        full_text = self._create_full_text_elem(hanrei_struct)

        hanji_jikou.text = hanrei_struct.hanji_jikou
        abstract.text = hanrei_struct.abstract
        referred_legislation.text = hanrei_struct.referred_legislation

        hanrei.append(meta)
        hanrei.append(origin_meta)
        hanrei.append(hanji_jikou)
        hanrei.append(abstract)
        hanrei.append(referred_legislation)
        hanrei.append(full_text)

        return hanrei

    def _create_root_elem(self, hanreiid):
        hanrei = etree.Element(u'Hanrei')
        if hanreiid is not None:
            hanrei.attrib[u'id'] = hanreiid
        return hanrei

    def _create_meta_elem(self, hanrei_struct):
        meta = etree.Element(u'Meta')

        jiken_no = etree.Element(u'JikenNum')
        name = etree.Element(u'Name')
        date = etree.Element(u'Date')
        trial = self._create_trial_elem(hanrei_struct)
        reference = etree.Element(u'Reference')

        jiken_no.text = hanrei_struct.jiken_no
        name.text = hanrei_struct.jiken_name
        date.text = hanrei_struct.date
        reference.text = hanrei_struct.reference

        meta.append(jiken_no)
        meta.append(name)
        meta.append(date)
        meta.append(trial)
        meta.append(reference)

        return meta

    def _create_trial_elem(self, hanrei_struct):
        trial = etree.Element(u'Trial')

        court = etree.Element(u'Court')
        ttype = etree.Element(u'Type')
        decision = etree.Element(u'Decision')

        court.text = hanrei_struct.court
        ttype.text = hanrei_struct.trial_type
        decision.text = hanrei_struct.decision

        trial.append(court)
        trial.append(ttype)
        trial.append(decision)

        return trial

    def _create_origin_meta_elem(self, hanrei_struct):
        origin_meta = etree.Element(u'OriginMeta')

        court = etree.Element(u'Court')
        jiken_no = etree.Element(u'JikenNum')
        date = etree.Element(u'Date')

        court.text = hanrei_struct.origin_court
        jiken_no.text = hanrei_struct.origin_jiken_no
        date.text = hanrei_struct.origin_date

        origin_meta.append(court)
        origin_meta.append(jiken_no)
        origin_meta.append(date)

        return origin_meta

    def _create_full_text_elem(self, hanrei_struct):
        text = self.get_full_text(hanrei_struct.full_text)
        full_text = etree.Element(u'FullText')
        full_text.text = text
        return full_text

    def create_xml_from(self, hanrei_html_texts):
        root = etree.Element(u'HanreiRecords')
        for html_text, hanrei_id in hanrei_html_texts:
            hanrei_elem = self.create_hanrei_element(html_text, hanreiid=hanrei_id)
            root.append(hanrei_elem)
        xml = etree.tostring(
            root, pretty_print=True,
            xml_declaration=True, encoding='UTF-8',
        ).decode('utf8')
        return self._clean_entity(xml)
