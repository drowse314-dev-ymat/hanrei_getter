# encoding: utf-8

import argparse
import test


if __name__ == '__main__':

    argX = argparse.ArgumentParser()
    argX.add_argument('--noweb', action='store_true', default=False)
    args = argX.parse_args()

    tests = test.tests(args)
    tests.run()
