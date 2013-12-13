# encoding: utf-8

import difflib
import hanreifetch
from .common import (
    SAMPLE_JIKEN_ORIGIN,
    sample_list_html, sample_jiken_urls, sample_jiken,
)


def detect_jiken_url():
    line = u'<td class="list1 width_hs_left"> <a href="/search/jhsp0030?hanreiid=52442&hanreiKbn=02">最高裁判例</a>'
    assert hanreifetch.ListHandler().jiken_links_from(line) == [u'/search/jhsp0030?hanreiid=52442&hanreiKbn=02']

def get_hanreiid():
    path = u'/search/jhsp0030?hanreiid=52442&hanreiKbn=02'
    fetched = hanreifetch.ListHandler().hanreiid_from(path) 
    assert fetched == u'52442'

def detect_all_jiken_urls():
    detected = hanreifetch.ListHandler().jiken_links_from(sample_list_html())
    expected_urls = sample_jiken_urls()
    assert set(detected) == set(expected_urls)

def fetch_jiken_page():
    fetched = hanreifetch.fetch_jiken_html(SAMPLE_JIKEN_ORIGIN)
    expected_html = sample_jiken()
    matcher = difflib.SequenceMatcher(None, fetched, expected_html)
    assert matcher.ratio() > 0.99, 'failed to fetch Jiken page correctly / if not a coding issue, check the original page'


def run(noweb=False):
    detect_jiken_url()
    get_hanreiid()
    detect_all_jiken_urls()
    if not noweb:
        fetch_jiken_page()
