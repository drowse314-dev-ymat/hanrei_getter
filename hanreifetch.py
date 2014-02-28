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
import logbook


logger_handler = logbook.StderrHandler()
logger_handler.format_string = '({record.channel}[{record.time:%H:%M}]) {record.message}'

LIST_HTML_ENCODING = 'sjis'
EN_LIST_HTML_ENCODING = 'iso-8859-1'
JIKEN_HTML_ENCODING = 'sjis'
EN_JIKEN_HTML_ENCODING = 'iso-8859-1'
XML_ENCODING = 'UTF-8'

URI_BASE = u'http://www.courts.go.jp'

RE_JIKEN_LINK = re.compile(u'<a href="(\/search\/jhsp0030\?hanreiid=\d+&hanreiKbn=\d+)">')
RE_EN_JIKEN_LINK = re.compile(u'<a href="(http://www\.courts\.go\.jp/english/judgments/text/[^"]+)"')
RE_HANREI_ID = re.compile(u'\/search\/jhsp0030\?hanreiid=(\d+)&hanreiKbn=\d+')
RE_EN_HANREI_ID = re.compile(
    u'http://www\.courts\.go\.jp/english/judgments/text/\d{4}\.\d{1,2}\.\d{1,2}-(.+)\.html'
)


class SleepyRequests(object):

    class_logger = logbook.Logger('delay-requester')
    class_logger.handlers.append(logger_handler)
    delay = 30.0

    def __init__(self):
        self._is_tired = False

    @property
    def logger(self):
        return self.__class__.class_logger

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
        self.logger.info('module requests is sleepy... wait for {} seconds'.format(delay))


sleepy = SleepyRequests()


def make_full_uri(path):
    return urlparse.urljoin(URI_BASE, path)

def read_html(filepath, encoding=LIST_HTML_ENCODING):
    html = open(filepath, 'rb').read().decode(encoding)
    return html


class ListHandler(object):

    re_jiken_link = RE_JIKEN_LINK
    re_hanrei_id = RE_HANREI_ID

    def jiken_links_from(self, html_text):
        links = self.__class__.re_jiken_link.findall(html_text)
        return self._listuniq(links)

    def hanreiid_from(self, jiken_path):
        matched = self.__class__.re_hanrei_id.match(jiken_path)
        assert bool(matched)
        return matched.groups()[0]

    def _listuniq(self, items):
        uniq = []
        for el in items:
            if el not in uniq:
                uniq.append(el)
        return uniq


class EnListHandler(ListHandler):

    re_jiken_link = RE_EN_JIKEN_LINK
    re_hanrei_id = RE_EN_HANREI_ID

    def hanreiid_from(self, jiken_path):
        matched = super(EnListHandler, self).hanreiid_from(jiken_path)
        hanreiid = self._transform_en_hanreiid(matched)
        return hanreiid

    def _transform_en_hanreiid(self, raw_hanrei_num):
        hanreiid = raw_hanrei_num.replace(u'.', u'')
        hanreiid = hanreiid.replace(u'No', u'No.')
        return hanreiid


def fetch_jiken_html(jiken_uri, encoding=JIKEN_HTML_ENCODING):
    res = sleepy.requests.get(jiken_uri)
    return res.content.decode(encoding)

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

    attr_map = HANREI_ATTR_NAME_MAP
    attr_converters = HANREI_ATTR_CONVERTERS

    def hanrei_attrs_from(self, html_text):
        clean_text = self._clean_entity(html_text)
        elem = html.fromstring(clean_text)
        for attr, attr_val in self.attrs_from_elem(elem):
            yield (attr, attr_val)

    def _clean_entity(self, html_text):
        hp = htmlparser.HTMLParser()
        return hp.unescape(html_text)

    def attrs_from_elem(self, elem):
        for dlist in self._listdiv_from(elem):
            for attrdiv in self._attrdiv_from(dlist):
                attr, attr_val = self._parse_attrdiv(attrdiv)
                yield attr, attr_val

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
        def _regattr(k, v):
            attrs[k] = v

        for readable_attr, raw_val in self.hanrei_attrs_from(html_text):
            readable_attr = self.attr_name_hook(readable_attr)
            attr = self.__class__.attr_map[readable_attr]
            converters = self.__class__.attr_converters
            if attr is None:
                pass
            elif isinstance(attr, list):
                for a in attr:
                    val = converters.get(a, lambda v:v)(raw_val)
                    _regattr(a, val)
            else:
                val = converters.get(attr, lambda v:v)(raw_val)
                _regattr(attr, val)

        attrs = self.attrs_setup(attrs)
        for key in attrs.keys():
            if key not in HANREI_ATTRS:
                attrs.pop(key)

        return Hanrei(**attrs)

    def attr_name_hook(self, attr_name):
        return attr_name

    def attrs_setup(self, attrs):
        return attrs

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
        full_text = self.create_full_text_elem(hanrei_struct)

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

    def create_full_text_elem(self, hanrei_struct):
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
            xml_declaration=True, encoding=XML_ENCODING,
        ).decode(XML_ENCODING)
        return self._clean_entity(xml)


EN_HANREI_ATTR_NAME_MAP = {
    u'Date': u'date',
    u'Case number': u'jiken_no', u'Reporter': u'reference',
    u'Title': None, u'Case name': u'jiken_name',
    u'Result': [u'trial_type', u'court', u'decision'],
    u'Court of the Second Instance': [u'origin_court', u'origin_date'],
    u'Summary': u'abstract',
    u'References': u'referred_legislation',
    u'Main text': u'full_text_main',
    u'Reasons': u'full_text_reason',
    u'Presiding Judge': u'full_text_judge',
}
def _decision_splitter(origin_result_info):
    return re.split(u'[,;] ', origin_result_info, maxsplit=1)
def _origin_dater(origin_info_text):
    parts = origin_info_text.split(u' of ')
    if len(parts) < 2:
        return u''
    else:
        return parts[1]
EN_HANREI_ATTR_CONVERTERS = {
    'trial_type': (lambda v: v.split(u' of ')[0]),
    'court': (lambda v: _decision_splitter(v)[0].split(u' of ')[1].title()),
    'decision': (lambda v: _decision_splitter(v)[1].capitalize()),
    'origin_date': (lambda v: _origin_dater(v)),
    'origin_court': (lambda v: v.split(u',')[0]),
}


class EnJikenParser(JikenParser):

    attr_map = EN_HANREI_ATTR_NAME_MAP
    attr_converters = EN_HANREI_ATTR_CONVERTERS

    def attrs_from_elem(self, elem):
        if elem.tag == u'table':
            table_elem = elem
        else:
            table_elem = self._table_from(elem)
        for tr in self._table_rows_in(table_elem):
            attr_td, val_td = self._tdpair_from(tr)
            attr = self._strip_only_text(attr_td)
            val = self._strip_only_text(val_td)
            yield (attr, val)

    def _table_from(self, any_elem):
        tables = any_elem.findall(u'.//table')
        assert len(tables) > 0, 'data table not found'
        for i, t in enumerate(tables):
            t = tables[i]
            num_trs = len(t.findall(u'.//tr'))
            if num_trs < 2:
                tables.pop(i)
        assert len(tables) == 1, 'multiple data tables found'
        return tables[0]

    def _table_rows_in(self, table_elem):
        for tr in table_elem.findall(u'.//tr'):
            yield tr

    def _tdpair_from(self, tr_elem):
        tds = tr_elem.findall(u'.//td')
        assert len(tds) == 2
        attr_td, val_td = tds
        return attr_td, val_td

    def _strip_only_text(self, any_elem):
        text = u''
        if any_elem.text:
            text += any_elem.text
        for desc in any_elem.iterdescendants():
            if desc.text:
                text += desc.text
            if desc.tag == u'br':
                text += u'<br/>'  # include only breaks.
            if desc.tail:
                text += desc.tail
        return text

    hookers = [u'Date', u'Summary', u'Main text']
    def attr_name_hook(self, attr_name):
        for common_seq in self.__class__.hookers:
            if attr_name.startswith(common_seq):
                return common_seq
        else:
            return attr_name

    def attrs_setup(self, attrs):
        attrs = self._attrs_setup_missing(attrs)
        attrs = self._make_full_text(attrs)
        return attrs

    def _attrs_setup_missing(self, attrs):
        attrs.update(origin_jiken_no=u'', hanji_jikou=u'')
        return attrs

    def _make_full_text(self, attrs):
        main_text = attrs.pop(u'full_text_main')
        reason = attrs.pop(u'full_text_reason')
        judge = attrs.pop(u'full_text_judge')
        attrs[u'full_text'] = u'\n'.join([
            u'Main text:',
            main_text,
            u'Reasons:',
            reason,
            u'Presiding Judge:',
            judge,
        ])
        return attrs

    def create_full_text_elem(self, hanrei_struct):
        full_text = etree.Element(u'FullText')
        full_text.text = hanrei_struct.full_text
        return full_text
