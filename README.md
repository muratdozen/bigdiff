bigdiff
=========

Bigdiff is a primitive yet powerful diff tool to aid in finding the differences between two huge files on the filesystem.


  - Operates on two gzipped plain text files,
  - Diffs the lines (considers line endings as a delimeter),
  - Ignores duplicates - i.e it doesn't matter if a line in a file appears once or repeats multiple times, it counts as the same,
  - Adapts to different memory limits with the __-b__ parameter (see *Memory Usage* on how to adjust this parameter),
  - Is a script written in Python 2.7.1.

Usage
----
```sh
git clone https://github.com/muratdozen/bigdiff.git bigdiff_repo
cd bigdiff_repo
python bigdiff --dir /path/to/dir/containing/the/inputs/ -b 15000
```

Path to the input directory must be absolute and should *only* contain the two gzipped input files which are to be diffed.

The output will be stored in the newly created `/diff` directory.

Running the Tests
----
```sh
# change to directory that contains application.py
cd bigdiff
python -m test.integration-test
```
Make sure `EMPTY_TEST_DIR` variable in `test/integration-test.py` points to an empty directory with read write permissions.

Memory Usage
----
Memory usage is highly dependent on the number of temporary files that are created and this is controlled by the __-b__ parameter. The Python script should be able to store two 32-bit integer lists of size = (number of lines in larger file / b) apart from the usual variables.

Ideally, b should be set to a number slightly higher than (perhaps 1.5x) `2 * (number of lines in larger file) * 32bits / (memory reserved for the script)`. So if we had 1MB of memory available for the script and the larger file had 250,000,000 lines, then (2 * 250,000,000 * 32bits / 1MB) = 2000; in this case, something between 2500 and 3500 would be a good choice for __-b__.

Increase the __-b__ parameter if you find that memory is exhausted.


Disk Space Usage
----
Bigdiff creates temporary files whose sizes are linear in the size of the input. If the average length of lines in the inputs is more than 11 characters, spare free disk space equal to the total size of the two gzipped input files.  If not, expect a higher disk space usage.

Authored by Murat Derya Özen
