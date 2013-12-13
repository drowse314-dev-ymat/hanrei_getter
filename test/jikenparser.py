# encoding: utf-8

from lxml import html, etree
import hanreifetch
from .common import (
    sample_jiken, sample_jiken_attr_pairs,
    sample_jiken_struct_attrmap,
    sample_hanrei_full_text, sample_hanrei_pdfdata,
    sample_jiken_xml,
    SAMPLE_HANREI_PDF_ORIGIN,
)


def parse_single_attribute():
    attr_block_html = (
        u'<body class="dummy">'
        u'<div class="dlist">'
        u'  <div>'
        u'    <div class="list4_top">attr1</div>'
        u'    <div class="list5_top">'
        u'      value1'
        u'    </div>'
        u'  </div>'
        u'  <div class="clear"></div>'
        u'  <div>'
        u'    <div class="list4">attr2</div>'
        u'    <div class="list5_long">'
        u'      value2'
        u'    </div>'
        u'  </div>'
        u'  <div class="clear"></div>'
        u'</div>'
        u'<div class="dlist">'
        u'  <div>'
        u'    <div class="list4_pdf">attr3</div>'
        u'    <div class="list5_long">'
        u'      value3'
        u'    </div>'
        u'  </div>'
        u'  <div class="clear"></div>'
        u'</div>'
        u'</body>'
    )
    attrs = list(hanreifetch.JikenParser().hanrei_attrs_from(attr_block_html))
    assert attrs == [
        (u'attr1', u'value1',),
        (u'attr2', u'value2',),
        (u'attr3', u'value3',),
    ]

def detect_all_hanrei_attrs():
    detected = list(hanreifetch.JikenParser().hanrei_attrs_from(sample_jiken()))
    expected_attrs = sample_jiken_attr_pairs()
    assert set(detected) == set(expected_attrs)

def create_hanrei_struct():
    hanrei = hanreifetch.JikenParser().create_struct_from(sample_jiken())
    expected_attrmap = sample_jiken_struct_attrmap()
    for key in expected_attrmap:
        assert getattr(hanrei, key) == expected_attrmap[key], u'{}: {}'.format(getattr(hanrei, key), expected_attrmap[key]).encode('utf8')

def fetch_full_text():
    full_text = hanreifetch.full_text_from_pdfdata(sample_hanrei_pdfdata())
    expected_text = sample_hanrei_full_text()
    assert full_text == expected_text

def full_text_from_web():
    full_text = hanreifetch.JikenParser().get_full_text(SAMPLE_HANREI_PDF_ORIGIN)
    expected_text = sample_hanrei_full_text()
    assert full_text == expected_text

def create_hanrei_elem():
    import HTMLParser
    hp = HTMLParser.HTMLParser()
    hanrei_elem = hanreifetch.JikenParser().create_hanrei_element(sample_jiken(), hanreiid='52442')
    expected_elem = etree.fromstring(sample_jiken_xml().encode('utf8')).findall(u'./Hanrei')[0]
    hanrei_xml = hp.unescape(etree.tostring(hanrei_elem, pretty_print=True)).strip()
    expected_xml = hp.unescape(etree.tostring(expected_elem, pretty_print=True)).strip()
    assert (
        [hline.strip() for hline in hanrei_xml.split(u'\n')] ==
        [eline.strip() for eline in expected_xml.split(u'\n')]
    )

def create_hanrei_xml():
    hanrei_xml = hanreifetch.JikenParser().create_xml_from([(sample_jiken(), '52442')])
    expected_xml = sample_jiken_xml()
    assert hanrei_xml == expected_xml


def run(noweb=False):
    parse_single_attribute()
    detect_all_hanrei_attrs()
    create_hanrei_struct()
    fetch_full_text()
    if not noweb:
        full_text_from_web()
        create_hanrei_elem()
        create_hanrei_xml()
