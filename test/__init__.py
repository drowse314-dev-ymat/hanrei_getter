# encoding: utf-8

from attest import Tests
from . import common, listfetch, jikenparser


def tests(args):
    all_tests = Tests(
        [
            common.common_unit(),
            listfetch.listfetch_unit(noweb=args.noweb),
            jikenparser.jikenparser_unit(noweb=args.noweb),
        ],
    )
    return all_tests
