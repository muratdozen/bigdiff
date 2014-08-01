__author__ = 'Murat Derya Ozen'


import gzip
import logging
import mmh3
import os
import random
import shutil
import application


# This directory is used for tests.
# It should be an absolute path and should exist
# and contain no items inside.
EMPTY_TEST_DIR = "/Users/murat/Desktop/bigdiff/test/"
test_case_ctr = 0


def read_gzip_file_lines_into_set(filename):
    """
    Returns a set containing all lines (stripped of \n) in the file.
    """
    with gzip.open(filename, 'r') as file:
        return set([line.strip() for line in file.readlines()])


def create_test_input_files(input1, input2):
    """
    Creates two files from the two inputs where
    each element is a line in the file.
    Inputs are shuffled.
    """
    random.shuffle(input1)
    random.shuffle(input2)
    filename1 = application.join_abs_path(EMPTY_TEST_DIR, 'file-1.gz')
    filename2 = application.join_abs_path(EMPTY_TEST_DIR, 'file-2.gz')

    with gzip.open(filename1, 'wb') as file1:
        file1.write('\n'.join(input1))
    with gzip.open(filename2, 'wb') as file2:
        file2.write('\n'.join(input2))


def clean_up_test_dir():
    for item in os.listdir(EMPTY_TEST_DIR):
        item_path = application.join_abs_path(EMPTY_TEST_DIR, item)
        if os.path.isfile(item_path):
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)


def get_resulting_diffs():
    """
    Read contents of the diffs from the output files.
    """
    diff_dirpath = application.join_abs_path(
        EMPTY_TEST_DIR, application.OUTPUT_DIR_NAME)
    diffleft_filename = application.join_abs_path(
        diff_dirpath, application.OUTPUT_DIFF_LEFT_FILENAME)
    diffright_filename = application.join_abs_path(
        diff_dirpath, application.OUTPUT_DIFF_RIGHT_FILENAME)

    diff_left = read_gzip_file_lines_into_set(diffleft_filename)
    diff_right = read_gzip_file_lines_into_set(diffright_filename)

    return diff_left, diff_right


def run_test(input1, input2, num_buckets, hash_function,
             expected_diffleft, expected_diffright):
    actual_diffleft, actual_diffright = None, None
    try:
        create_test_input_files(input1, input2)
        global test_case_ctr
        test_case_ctr += 1
        application.bigdiff(EMPTY_TEST_DIR, num_buckets, hash_function)
        actual_diffleft, actual_diffright = get_resulting_diffs()
        assert set(expected_diffleft) == actual_diffleft and set(
            expected_diffright) == actual_diffright
        logging.info("Test case #%s OK!\n", test_case_ctr)
    except Exception, ex:
        msg = """
        ***
        Test case #%s FAILED!
        Input1: %s, Input2: %s, num_buckets: %s

        Expected diffleft: %s
        Actual diffleft: %s

        Expected diffright: %s
        Actual diffright: %s
        ***
        """
        logging.error(msg, test_case_ctr, input1, input2, num_buckets,
                      expected_diffleft, actual_diffleft,
                      expected_diffright, actual_diffright)
        raise
    finally:
        clean_up_test_dir()


def test():
    for num_buckets in [2, 3, 5, 10, 50, 100, 500, 1000,
                        3567, 9570, 10000, 14691]:
        for hash_function in [mmh3.hash]:
            testcase = lambda i1, i2, expctd1, expctd2: run_test(
                i1, i2, num_buckets, hash_function, expctd1, expctd2)
            # test cases
            testcase([''], [''], [], [])
            testcase([''], ['a'], [], ['a'])
            testcase(['a'], [''], ['a'], [])
            testcase([''], ['a', 'b', 'c'], [], ['a', 'b', 'c'])
            testcase(['a', 'b', 'c'], [''], ['a', 'b', 'c'], [])
            testcase(['a'], ['a'], [], [])
            testcase(['a', 'b', 'c'], ['a', 'b', 'c'], [], [])
            testcase(['a'], ['a', 'b', 'c'], [], ['b', 'c'])
            testcase(['a', 'b', 'c'], ['a'], ['b', 'c'], [])
            testcase(['a', 'b', 'c', 'd'], ['a', 'b', 'c'], ['d'], [])
            testcase(['a', 'b', 'c'], ['a', 'b', 'c', 'd'], [], ['d'])
            testcase(['a', 'b', 'c', 'x'], ['a', 'b', 'c', 'd'], ['x'], ['d'])
            testcase(
                ['a', 'b', 'c', 'x', 'y'], ['a', 'b', 'c', 'd'], ['x', 'y'], ['d'])
            testcase(['a', 'b', 'c', 'd'], ['a', 'b', 'c', 'x'], ['d'], ['x'])
            testcase(
                ['a', 'b', 'c', 'd'], ['a', 'b', 'c', 'x', 'y'], ['d'], ['x', 'y'])
            # test duplicates
            testcase(['a', 'b', 'c', 'a'], ['a', 'b', 'c'], [], [])
            testcase(
                ['a', 'b', 'c', 'a'], ['b', 'c', 'c', 'c', 'c'], ['a'], [])
            testcase(['a', 'b', 'a'], ['b', 'c', 'c', 'c', 'c'], ['a'], ['c'])
            # test raw RDF data
            testcase([
                '<http://rdf.freebase.com/ns/m.05p0zcn>	<http://rdf.freebase.com/ns/type.object.key>	"/wikipedia/de_id/914739"	.',
                '<http://rdf.freebase.com/ns/m.05p0zcn>	<http://rdf.freebase.com/ns/type.object.key>	"/wikipedia/en_id/21902865"',
                '<http://rdf.freebase.com/ns/m.05p0zcn>	<http://rdf.freebase.com/ns/type.object.type>	<http://rdf.freebase.com/ns/people.person>	.',
                '<http://rdf.freebase.com/ns/m.05p0zpm>	<http://rdf.freebase.com/key/key.en>	"lago_di_toblino"	.',
                '<http://rdf.freebase.com/ns/m.05p0zpm>	<http://rdf.freebase.com/key/key.wikipedia.en_title>	"Lago_di_Toblino"	.',
                '<http://rdf.freebase.com/ns/m.05p0zpm>	<http://rdf.freebase.com/key/key.wikipedia.en_id>	"21916892"	.',
                '<http://rdf.freebase.com/ns/m.05p1dp7>	<http://www.w3.org/2000/01/rdf-schema#label>	"Robert P. Madden"@en	.',
                '<http://rdf.freebase.com/ns/m.05p1x5l>	<http://rdf.freebase.com/key/key.wikipedia.en>	"Sunday_VS_Magazine$003A_Shuketsu$0021_Chojo_Daikessen"	.',
                '<http://rdf.freebase.com/ns/m.05p1x5l>	<http://rdf.freebase.com/key/key.wikipedia.en>	"Sunday_VS_Magazine$003A_Shuketsu$0021_Chojo_Daikessen"	.',
                '<http://rdf.freebase.com/ns/m.05p21_k>	<http://rdf.freebase.com/key/key.wikipedia.en>	"Microsoft_Semblio"	.'
            ],
                [
                '<http://rdf.freebase.com/ns/m.05p0zcn>	<http://rdf.freebase.com/ns/type.object.key>	"/wikipedia/de_id/914739"	.',
                '<http://rdf.freebase.com/ns/m.05p24zf>	<http://rdf.freebase.com/ns/type.object.name>	"Truman McGill Hobbs"@en	.',
                '<http://rdf.freebase.com/ns/m.05p24zf>	<http://rdf.freebase.com/key/key.wikipedia.en_title>	"Truman_McGill_Hobbs"	.',
                '<http://rdf.freebase.com/ns/m.05p28nb>	<http://rdf.freebase.com/ns/type.object.key>	"/wikipedia/pl_id/1526881"	.',
                '<http://rdf.freebase.com/ns/m.05p28nb>	<http://www.w3.org/2000/01/rdf-schema#label>	"Kośnik"@pl	.',
                '<http://rdf.freebase.com/ns/m.05p1x5l>	<http://rdf.freebase.com/key/key.wikipedia.en>	"Sunday_VS_Magazine$003A_Shuketsu$0021_Chojo_Daikessen"	.'
            ],
                [
                '<http://rdf.freebase.com/ns/m.05p0zcn>	<http://rdf.freebase.com/ns/type.object.key>	"/wikipedia/en_id/21902865"',
                '<http://rdf.freebase.com/ns/m.05p0zcn>	<http://rdf.freebase.com/ns/type.object.type>	<http://rdf.freebase.com/ns/people.person>	.',
                '<http://rdf.freebase.com/ns/m.05p0zpm>	<http://rdf.freebase.com/key/key.en>	"lago_di_toblino"	.',
                '<http://rdf.freebase.com/ns/m.05p0zpm>	<http://rdf.freebase.com/key/key.wikipedia.en_title>	"Lago_di_Toblino"	.',
                '<http://rdf.freebase.com/ns/m.05p0zpm>	<http://rdf.freebase.com/key/key.wikipedia.en_id>	"21916892"	.',
                '<http://rdf.freebase.com/ns/m.05p1dp7>	<http://www.w3.org/2000/01/rdf-schema#label>	"Robert P. Madden"@en	.',
                '<http://rdf.freebase.com/ns/m.05p21_k>	<http://rdf.freebase.com/key/key.wikipedia.en>	"Microsoft_Semblio"	.'
            ],
                [
                '<http://rdf.freebase.com/ns/m.05p24zf>	<http://rdf.freebase.com/ns/type.object.name>	"Truman McGill Hobbs"@en	.',
                '<http://rdf.freebase.com/ns/m.05p24zf>	<http://rdf.freebase.com/key/key.wikipedia.en_title>	"Truman_McGill_Hobbs"	.',
                '<http://rdf.freebase.com/ns/m.05p28nb>	<http://rdf.freebase.com/ns/type.object.key>	"/wikipedia/pl_id/1526881"	.',
                '<http://rdf.freebase.com/ns/m.05p28nb>	<http://www.w3.org/2000/01/rdf-schema#label>	"Kośnik"@pl	.'
            ])
    logging.info("All tests passed!")


if __name__ == "__main__":
    logging.basicConfig(
        format='%(levelname)s: %(message)s', level=logging.DEBUG)
    test()