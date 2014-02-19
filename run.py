# encoding: utf-8

import os
import argparse
import hanreifetch
import logbook


logger = logbook.Logger('hanrei-collect')
logger.handlers.append(hanreifetch.logger_handler)

SAVE_INTO = os.path.abspath(os.path.sep.join(
    [u'.', u'./hanreidata']
))


def target_htmls(target_dirs):
    for d in target_dirs:
        for root, dirs, files in os.walk(d):
            for filename in files:
                yield os.path.sep.join(
                    [root, filename]
                )

def make_xml_filname(source_html_path):
    filename = os.path.basename(source_html_path)
    without_ext = filename.split(os.path.extsep)[:-1]
    xml_filename = os.path.extsep.join(without_ext + [u'xml'])
    return os.path.sep.join(
        [SAVE_INTO, xml_filename]
    )


class HanreiXMLCreator(object):

    def __init__(self, en_list=False):
        if en_list:
            self._listhandler = hanreifetch.EnListHandler()
            self._jikenparser = hanreifetch.EnJikenParser()
        else:
            self._listhandler = hanreifetch.ListHandler()
            self._jikenparser = hanreifetch.JikenParser()

    def process_html(self, html_path, tofile=None):
        if tofile is None:
            tofile = make_xml_filname(html_path)
        logger.notice(u'-- going to save xml to "{}"'.format(tofile))

        if not self.check_cache(tofile):

            html_text = self.load_html(html_path)
            jiken_uris = list(self.jiken_uris(html_text))

            logger.notice(u'-- {} hanrei links found'.format(len(jiken_uris)))

            with open(tofile, 'wb') as xmlfile:
                xmltext = self._jikenparser.create_xml_from(self.iter_jiken_html(jiken_uris))
                as_bytes = xmltext.encode(hanreifetch.XML_ENCODING)
                xmlfile.write(as_bytes)

        else:
            logger.notice(u'-- cache found')

        logger.notice(u'done!')

    def check_cache(self, tofile):
        if os.path.exists(tofile):
            return True
        return False

    def load_html(self, html_path):
        return hanreifetch.read_html(html_path)

    def jiken_uris(self, html_text):
        listhandler = self._listhandler
        for jiken_uri in listhandler.jiken_links_from(html_text):
            yield jiken_uri, listhandler.hanreiid_from(jiken_uri)

    def iter_jiken_html(self, jiken_uris):
        for uri, hanrei_id in jiken_uris:
            jiken_html = hanreifetch.fetch_jiken_html(
                hanreifetch.make_full_uri(uri)
            )
            yield jiken_html, hanrei_id


def run(args):

    html_paths = list(target_htmls(args.target_dirs))
    num_htmls = len(html_paths)
    logger.notice(u'{} html files found.'.format(num_htmls))

    xml_creator = HanreiXMLCreator(en_list=args.en_list)

    for i, html_path in enumerate(html_paths, start=1):

        logger.notice(u'#{}/{}: processing "{}"...'.format(i, num_htmls, html_path))
        xml_creator.process_html(html_path)


if __name__ == '__main__':
    argX = argparse.ArgumentParser()
    argX.add_argument('target_dirs', nargs='+')
    argX.add_argument('--en_list', action='store_true', default=False)
    args = argX.parse_args()
    run(args)
