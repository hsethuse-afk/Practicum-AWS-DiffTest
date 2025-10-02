## Running Module Test
### All Imported Modules
    python -m righttyper --all-files ./tests/test.py
 ### Specify the Function Name
    python -m righttyper --all-files --include-functions "^split_words$" ./tests/test.py
 ### Specify the Python File Name
	 python -m righttyper --all-files --include-files "a.py$" ./tests/test.py
## Running Numpy Test

    python -m righttyper ./numpy_test/numpyOut.py
