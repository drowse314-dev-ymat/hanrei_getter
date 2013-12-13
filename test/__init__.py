# encoding: utf-8


from . import common, listfetch, jikenparser


def test(args):
    common.run()
    listfetch.run(noweb=args.noweb)
    jikenparser.run(noweb=args.noweb)
