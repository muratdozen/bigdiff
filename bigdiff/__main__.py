__author__ = 'Murat Derya Ozen'


PROGRAM_DESCRIPTION = """

TODO !!!

"""

import argparse
import logging
import mmh3
from application import bigdiff


def get_argparser():
    """ Defines and returns the ArgumentParser for this program. """
    parser = argparse.ArgumentParser(description=PROGRAM_DESCRIPTION)
    parser.add_argument('-d', '--dir', required=True,
                        help='Absolute path to the directory containing the two input files.')
    parser.add_argument('-b', type=int, required=True,
                        help='Number of buckets (temporary files) to be'
                             ' created for each input file. Memory '
                             'consumption of the program is highly related '
                             'to the number of buckets. The higher this '
                             'number, the less memory consumed.')
    parser.set_defaults(func=main)

    return parser


def main(args):
    logging.basicConfig(
        format='%(levelname)s: %(message)s', level=logging.DEBUG)
    hash_function = mmh3.hash
    # run bigdiff!
    bigdiff(args.dir, args.b, hash_function)


if __name__ == "__main__":
    parser = get_argparser()
    args = parser.parse_args()
    args.func(args)
