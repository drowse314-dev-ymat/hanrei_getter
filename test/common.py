# encoding: utf-8

import os
import hanreifetch


SAMPLE_LIST = os.path.abspath(os.path.sep.join(
    [os.path.dirname(__file__), 'h01_o_01.htm']
))
SAMPLE_JIKEN_URLS = os.path.abspath(os.path.sep.join(
    [os.path.dirname(__file__), 'h01_o_01_jiken_links.txt']
))
SAMPLE_JIKEN = os.path.abspath(os.path.sep.join(
    [os.path.dirname(__file__), 'jiken.html']
))
SAMPLE_JIKEN_ORIGIN = u'http://www.courts.go.jp/search/jhsp0030?hanreiid=52285&hanreiKbn=02'
SAMPLE_JIKEN_ATTRS = os.path.abspath(os.path.sep.join(
    [os.path.dirname(__file__), 'jiken_attr_pairs.txt']
))
SAMPLE_JIKEN_STRUCT = os.path.abspath(os.path.sep.join(
    [os.path.dirname(__file__), 'jiken_struct_attrs.txt']
))
SAMPLE_HANREI_FULL_TEXT = os.path.abspath(os.path.sep.join(
    [os.path.dirname(__file__), 'hanrei_full_text.txt']
))
SAMPLE_HANREI_PDF = os.path.abspath(os.path.sep.join(
    [os.path.dirname(__file__), 'hanrei_pdf.pdf']
))
SAMPLE_HANREI_PDF_ORIGIN = u'http://www.courts.go.jp/hanrei/pdf/js_20100319120650476715.pdf'
SAMPLE_JIKEN_XML = os.path.abspath(os.path.sep.join(
    [os.path.dirname(__file__), 'jiken_xml.xml']
))


def sample_list_html():
    html = open(SAMPLE_LIST, 'rb').read().decode('sjis')
    return html

def sample_jiken_urls():
    list_text = open(SAMPLE_JIKEN_URLS, 'rb').read().decode('utf-8')
    return [item for item in list_text.split(u'\n') if item != u""]

def sample_jiken():
    html = open(SAMPLE_JIKEN, 'rb').read().decode('sjis')
    return html

def sample_jiken_attr_pairs():
    list_text = open(SAMPLE_JIKEN_ATTRS, 'rb').read().decode('utf-8')
    return [tuple(item.split(u',')) for item in list_text.split(u'\n') if item != u""]

def sample_jiken_struct_attrmap():
    list_text = open(SAMPLE_JIKEN_STRUCT, 'rb').read().decode('utf-8')
    pairs = [item.split(u',') for item in list_text.split(u'\n') if item != u""]
    return {attr: val for attr, val in pairs}

def sample_hanrei_full_text():
    text = open(SAMPLE_HANREI_FULL_TEXT, 'rb').read().decode('utf-8')
    return text.strip()

def sample_hanrei_pdfdata():
    return open(SAMPLE_HANREI_PDF, 'rb').read()

def sample_jiken_xml():
    xml = open(SAMPLE_JIKEN_XML, 'rb').read().decode('utf-8')
    return xml

def htmlreader():
    assert hanreifetch.read_html(SAMPLE_LIST) == sample_list_html()

def make_full_uri():
    link = u'/search/jhsp0030?hanreiid=52442&hanreiKbn=02'
    assert hanreifetch.make_full_uri(link) == u'http://www.courts.go.jp/search/jhsp0030?hanreiid=52442&hanreiKbn=02'


def run(noweb=False):
    htmlreader()
    make_full_uri()
