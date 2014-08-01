__author__ = 'Murat Derya Ozen'


import glob
import gzip
import logging
import os
import shutil


TEMP_DIR_NAME = "temp"
OUTPUT_DIR_NAME = "diff"
OUTPUT_DIFF_LEFT_FILENAME = "diff-left.gz"
OUTPUT_DIFF_RIGHT_FILENAME = "diff-right.gz"
BUCKET_FILE_NAME_PREFIX = "bucket-"


def join_abs_path(x, y):
    """
    Join two paths x and y and absolutize the result.
    """
    return os.path.abspath(os.path.join(x, y))


def compute_bucket_number_from_hashed_line(hash, num_buckets):
    return hash % num_buckets


def write_hashed_line_to_bucket_file(output_dirpath, num_buckets,
                                     bucket_number, line,
                                     output_file_handles):
    # bucket files' names are prepended with '0' so that
    # all bucket filenames have the same length.
    # e.g if num_buckets is 457,
    # and we're currently writing to bucket_number=9,
    # the bucket file will be numbered 009.
    bucket_number_str = '0' * \
        (len(str(num_buckets - 1)) - len(str(bucket_number))) + \
        str(bucket_number)
    output_filename = join_abs_path(output_dirpath, bucket_number_str + '.gz')
    if bucket_number not in output_file_handles:
        output_file_handles[bucket_number] = gzip.open(output_filename, 'wb')

    output_file_handles[bucket_number].write(line + '\n')


def get_bucket_filenames(dirpath):
    buckets_dirpath = join_abs_path(dirpath, TEMP_DIR_NAME)
    bucket1_dirpath = join_abs_path(buckets_dirpath, '1')
    bucket2_dirpath = join_abs_path(buckets_dirpath, '2')

    bucket1_filenames = os.listdir(bucket1_dirpath)
    bucket2_filenames = os.listdir(bucket2_dirpath)

    bucket1_filenames.sort()
    bucket2_filenames.sort()

    bucket1_filenames = [
        join_abs_path(bucket1_dirpath, f) for f in bucket1_filenames]
    bucket2_filenames = [
        join_abs_path(bucket2_dirpath, f) for f in bucket2_filenames]

    return bucket1_filenames, bucket2_filenames


def extract_original_lines_from_hashes_of_lines(hashes_of_lines,
                                                hash_func, filename):
    """
    Traverse all lines in filename to see if any lines' hash
    is contained in hashes_of_lines.
    """
    results = set()
    if not hashes_of_lines:
        return results
    with gzip.open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            hashed_line = hash_func(line)
            if hashed_line in hashes_of_lines:
                results.add(line)
    return results


def bucketize(hash_func, input_filename, num_buckets, output_dirpath):
    """
    Distribute each line in input_filename to bucket files
    according to the value of hash(line).
    """
    logging.info("Processing file %s", input_filename)
    # while bucketizing, it is preferred to keep a handle to all bucket files
    # and never close them until the end, instead of closing them after each
    # write so that we can make use of gzip's compression power.
    output_file_handles = dict()
    with gzip.open(input_filename, 'r') as file:
        for line in file:
            line = line.strip()
            hashed_line = hash_func(line)
            bucket_number = compute_bucket_number_from_hashed_line(
                hashed_line, num_buckets)
            write_hashed_line_to_bucket_file(
                output_dirpath, num_buckets, bucket_number,
                str(hashed_line), output_file_handles)
    for bucket_number in output_file_handles:
        output_file_handles[bucket_number].close()


def read_gzip_file_lines_into_int_set(filename):
    with gzip.open(filename, 'r') as file:
        return set([int(line) for line in file.readlines()])


def diff_two_bucket_files(bucket1_filename, bucket2_filename):
    lines1 = read_gzip_file_lines_into_int_set(bucket1_filename)
    lines2 = read_gzip_file_lines_into_int_set(bucket2_filename)

    diff_left = lines1 - lines2
    diff_right = lines2 - lines1

    return diff_left, diff_right


def diff_all_buckets(dirpath):
    logging.info("Reading bucket files to compute the diff of hashes.")
    bucket1_filenames, bucket2_filenames = get_bucket_filenames(dirpath)
    resulting_diff_left, resulting_diff_right = set(), set()
    i, j = 0, 0
    while i < len(bucket1_filenames) and j < len(bucket2_filenames):
        bucket1_filename, bucket2_filename = bucket1_filenames[
            i], bucket2_filenames[j]
        bucket1_filename_basepath = os.path.basename(bucket1_filename)
        bucket2_filename_basepath = os.path.basename(bucket2_filename)
        if bucket1_filename_basepath == bucket2_filename_basepath:
            diff_left, diff_right = diff_two_bucket_files(
                bucket1_filename, bucket2_filename)
            resulting_diff_left.update(diff_left)
            resulting_diff_right.update(diff_right)
            i += 1
            j += 1
        else:
            if bucket1_filename_basepath < bucket2_filename_basepath:
                bucket1_lines = read_gzip_file_lines_into_int_set(
                    bucket1_filename)
                resulting_diff_left.update(bucket1_lines)
                i += 1
            else:
                bucket2_lines = read_gzip_file_lines_into_int_set(
                    bucket2_filename)
                resulting_diff_right.update(bucket2_lines)
                j += 1
    while i < len(bucket1_filenames):
        bucket1_filename = bucket1_filenames[i]
        lines = read_gzip_file_lines_into_int_set(bucket1_filename)
        resulting_diff_left.update(lines)
        i += 1
    while j < len(bucket2_filenames):
        bucket2_filename = bucket2_filenames[j]
        lines = read_gzip_file_lines_into_int_set(bucket2_filename)
        resulting_diff_right.update(lines)
        j += 1

    return resulting_diff_left, resulting_diff_right


def get_filenames_from_input_directory(dirpath):
    """
    The input directory should contain only two files;
    namely the file that are to be diffed.
    From these two files, the lexicographically smaller filename is treated
    as File1, and the other as File2.
    """
    dir_contents = glob.glob(os.path.join(dirpath, '*'))
    if not dir_contents:
        raise ValueError("Input directory is empty.")
    if len(dir_contents) != 2:
        raise ValueError("Input directory should contain 2 files only.")
    filename1 = join_abs_path(dirpath, dir_contents[0])
    filename2 = join_abs_path(dirpath, dir_contents[1])
    if not os.path.isfile(filename1) or not os.path.isfile(filename2):
        raise ValueError("Input directory should contain 2 files only.")
    if filename1 >= filename2:
        filename1, filename2 = filename2, filename1

    logging.info("File 1: %s", filename1)
    logging.info("File 2: %s", filename2)
    return filename1, filename2


def create_temp_dirs(dirpath):
    """
    Creates a temporary directory inside the input directory
    and two other directories (named '1' and '2')
    inside the temporary directory.
    """
    buckets_dirpath = join_abs_path(dirpath, TEMP_DIR_NAME)
    os.mkdir(buckets_dirpath)
    buckets1_dirpath = join_abs_path(buckets_dirpath, '1')
    os.mkdir(buckets1_dirpath)
    buckets2_dirpath = join_abs_path(buckets_dirpath, '2')
    os.mkdir(buckets2_dirpath)
    logging.info("Temporary files will be stored in %s", buckets_dirpath)
    return buckets_dirpath, buckets1_dirpath, buckets2_dirpath


def write_diffs_to_output_files(dirpath, diff_left, diff_right):
    logging.info(
        "Writing diffs to directory %s inside %s", OUTPUT_DIR_NAME, dirpath)
    output_dirpath = join_abs_path(dirpath, OUTPUT_DIR_NAME)
    os.mkdir(output_dirpath)
    diffleft_filename = join_abs_path(
        output_dirpath, OUTPUT_DIFF_LEFT_FILENAME)
    diffright_filename = join_abs_path(
        output_dirpath, OUTPUT_DIFF_RIGHT_FILENAME)
    with gzip.open(diffleft_filename, 'wb') as file1:
        if diff_left:
            file1.write('\n'.join(filter(None, diff_left)))
    with gzip.open(diffright_filename, 'wb') as file2:
        if diff_right:
            file2.write('\n'.join(filter(None, diff_right)))
    return output_dirpath


def bigdiff(dirpath, num_buckets, hash_func):
    buckets_dirpath = None
    try:
        logging.info("Bigdiff started.")

        filename1, filename2 = get_filenames_from_input_directory(dirpath)

        # create directory for temporary files
        buckets_dirpath, buckets1_dirpath, buckets2_dirpath = create_temp_dirs(
            dirpath)

        # bucketize both input files
        bucketize(hash_func, filename1, num_buckets, buckets1_dirpath)
        bucketize(hash_func, filename2, num_buckets, buckets2_dirpath)

        logging.info("Bigdiff completed bucketizing both files.")

        # traverse each bucket to compute the diff
        hashed_diff_left, hashed_diff_right = diff_all_buckets(dirpath)

        logging.info("Mapping hashed lines to original lines in the input.")

        # the obtained diff contains the hashes of lines.
        # convert those hashes to original lines
        diff_left = extract_original_lines_from_hashes_of_lines(
            hashed_diff_left, hash_func, filename1)
        diff_right = extract_original_lines_from_hashes_of_lines(
            hashed_diff_right, hash_func, filename2)

        logging.info("Bigdiff obtained the diff successfully."
                     " Diff left: %s lines, diff right: %s lines", len(
            diff_left), len(diff_right))
        # save results to file system
        output__dirpath = write_diffs_to_output_files(
            dirpath, diff_left, diff_right)
        logging.info("Bigdiff output saved to %s.", output__dirpath)
    except Exception, ex:
        logging.exception("Bigdiff failed!")
    finally:
        # finally, clean up temporary files
        if buckets_dirpath:
            logging.info("Cleaning up temporary files in %s.", buckets_dirpath)
            shutil.rmtree(buckets_dirpath)
        logging.info("Done.")
