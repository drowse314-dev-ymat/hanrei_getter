# encoding: utf-8

from lxml import html, etree
from attest import Tests
import hanreifetch
from .common import (
    sample_jiken, sample_jiken_attr_pairs,
    sample_en_jiken, sample_en_jiken_attr_pairs,
    sample_jiken_struct_attrmap,
    sample_en_jiken_struct_attrmap,
    sample_hanrei_full_text, sample_hanrei_pdfdata,
    sample_jiken_xml,
    sample_en_jiken_xml,
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

def parse_single_attribute_from_en_table():
    attr_block_html = (
        u'<body class="dummy">'
        u'  <table>'
        u'    <tr>'
        u'      <td><pre>attr1</pre></td>'
        u'      <td>value1</td>'
        u'    </tr>'
        u'    <tr>'
        u'      <td><pre>attr2</pre></td>'
        u'      <td>value2</td>'
        u'    </tr>'
        u'    <tr>'
        u'      <td><pre>attr3</pre></td>'
        u'      <td>value3</td>'
        u'    </tr>'
        u'  </table>'
        u'</body>'
    )
    attrs = list(hanreifetch.EnJikenParser().hanrei_attrs_from(attr_block_html))
    assert attrs == [
        (u'attr1', u'value1',),
        (u'attr2', u'value2',),
        (u'attr3', u'value3',),
    ]

def detect_all_hanrei_attrs():
    detected = list(hanreifetch.JikenParser().hanrei_attrs_from(sample_jiken()))
    expected_attrs = sample_jiken_attr_pairs()
    assert set(detected) == set(expected_attrs)

def detect_all_en_hanrei_attrs():
    detected = list(hanreifetch.EnJikenParser().hanrei_attrs_from(sample_en_jiken()))
    expected_attrs = sample_en_jiken_attr_pairs()
    assert set(detected) == set(expected_attrs)

def create_hanrei_struct():
    hanrei = hanreifetch.JikenParser().create_struct_from(sample_jiken())
    expected_attrmap = sample_jiken_struct_attrmap()
    for key in expected_attrmap:
        assert getattr(hanrei, key) == expected_attrmap[key]

def create_en_hanrei_struct():
    hanrei = hanreifetch.EnJikenParser().create_struct_from(sample_en_jiken())
    expected_attrmap = sample_en_jiken_struct_attrmap()
    for key in expected_attrmap:
        assert getattr(hanrei, key) == expected_attrmap[key]

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
    expected_elem = etree.fromstring(sample_jiken_xml().encode(hanreifetch.XML_ENCODING)).findall(u'./Hanrei')[0]
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

def create_en_hanrei_xml():
    hanrei_xml = hanreifetch.EnJikenParser().create_xml_from([(sample_en_jiken(), '2012-Kyo-No.43')])
    expected_xml = sample_en_jiken_xml()
    assert hanrei_xml == expected_xml

def en_attr_conversions():
    # test some complex converters
    en_converters = hanreifetch.EN_HANREI_ATTR_CONVERTERS
    for_trial = en_converters['trial_type']
    for_court = en_converters['court']
    for_decision = en_converters['decision']
    # conversions for trial, court, decision
    simple = u'Desicion of the First Petty Bench, quashed and remanded'
    assert for_trial(simple) == u'Desicion'
    assert for_court(simple) == u'The First Petty Bench'
    assert for_decision(simple) == u'Quashed and remanded'
    multiseps = u'Judgment of the Third Petty Bench, partially quashed and remanded, partially dismissed'
    assert for_trial(multiseps) == u'Judgment'
    assert for_court(multiseps) == u'The Third Petty Bench'
    assert for_decision(multiseps) == u'Partially quashed and remanded, partially dismissed'
    semicolon = u'Judgment of the Second Petty Bench; dismissed'
    assert for_trial(semicolon) == u'Judgment'
    assert for_court(semicolon) == u'The Second Petty Bench'
    assert for_decision(semicolon) == u'Dismissed'
    itstoosimple = u'Dismissed'
    assert for_trial(itstoosimple) == u''
    assert for_court(itstoosimple) == u''
    assert for_decision(itstoosimple) == u'Dismissed'


def jikenparser_unit(noweb=False):
    tests = Tests()
    tests.test(parse_single_attribute)
    tests.test(parse_single_attribute_from_en_table)
    tests.test(detect_all_hanrei_attrs)
    tests.test(detect_all_en_hanrei_attrs)
    tests.test(create_hanrei_struct)
    tests.test(create_en_hanrei_struct)
    tests.test(fetch_full_text)
    if not noweb:
        tests.test(full_text_from_web)
        tests.test(create_hanrei_elem)
        tests.test(create_hanrei_xml)
    tests.test(create_en_hanrei_xml)
    tests.test(en_attr_conversions)
    return tests
