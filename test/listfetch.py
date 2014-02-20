# encoding: utf-8

import difflib
from attest import Tests
import hanreifetch
from .common import (
    SAMPLE_JIKEN_ORIGIN,
    sample_list_html, sample_jiken_urls, sample_jiken,
    sample_en_list_html, sample_en_jiken_urls,
)


def detect_jiken_url():
    line = u'<td class="list1 width_hs_left"> <a href="/search/jhsp0030?hanreiid=52442&hanreiKbn=02">最高裁判例</a>'
    assert hanreifetch.ListHandler().jiken_links_from(line) == [u'/search/jhsp0030?hanreiid=52442&hanreiKbn=02']

def detect_en_jiken_url():
    jiken_line = (
        u'<dt>1. <strong>'
            u'<a href="http://www.courts.go.jp/english/judgments/text/2013.11.21-2012.-Kyo-.No..43.html" target="_blank">'
            u'2012 (Kyo) No. 43'
            u'</a>'
        u'</strong> (score: -1)</dt>'
    )
    assert hanreifetch.EnListHandler().jiken_links_from(jiken_line) == [
        u'http://www.courts.go.jp/english/judgments/text/2013.11.21-2012.-Kyo-.No..43.html'
    ]

def get_hanreiid():
    path = u'/search/jhsp0030?hanreiid=52442&hanreiKbn=02'
    fetched = hanreifetch.ListHandler().hanreiid_from(path) 
    assert fetched == u'52442'

def get_en_hanreiid():
    uri = u'http://www.courts.go.jp/english/judgments/text/2013.11.21-2012.-Kyo-.No..43.html'
    fetched = hanreifetch.EnListHandler().hanreiid_from(uri)
    assert fetched == u'2012-Kyo-No.43'

def detect_all_jiken_urls():
    detected = hanreifetch.ListHandler().jiken_links_from(sample_list_html())
    expected_urls = sample_jiken_urls()
    assert len(detected) == len(expected_urls)
    assert set(detected) == set(expected_urls)

def detect_all_en_jiken_urls():
    detected = hanreifetch.EnListHandler().jiken_links_from(sample_en_list_html())
    expected_urls = sample_en_jiken_urls()
    assert len(detected) == len(expected_urls)
    assert set(detected) == set(expected_urls)

def fetch_jiken_page():
    fetched = hanreifetch.fetch_jiken_html(SAMPLE_JIKEN_ORIGIN)
    expected_html = sample_jiken()
    matcher = difflib.SequenceMatcher(None, fetched, expected_html)
    assert matcher.ratio() > 0.99, 'failed to fetch Jiken page correctly / if not a coding issue, check the original page'


def listfetch_unit(noweb=False):
    tests = Tests()
    tests.test(detect_jiken_url)
    tests.test(detect_en_jiken_url)
    tests.test(get_hanreiid)
    tests.test(get_en_hanreiid)
    tests.test(detect_all_jiken_urls)
    tests.test(detect_all_en_jiken_urls)
    if not noweb:
        tests.test(fetch_jiken_page)
    return tests
