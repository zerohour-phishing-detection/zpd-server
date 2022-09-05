Due to exploratory nature of the project alot of overhead exists in the codebase. (e.g., different search engines)
If just the main contribution is required then please inspect:
	/utils/regiondetection.py   -> _findregions(...)
Which contains the converting of a image file into seperate regions as discussed within the paper.

----
Layout of files within the codebase:
----

main.py
	Startup file

requirements.txt
	file containing all python packages involved

/engines/
	Contains python files to interact with search engines

/db/
	Contains sqlite database files containing resources

/log/
	Folder for constructing logs

/utils/
	Contains misceleanous parts of the program.
	Most notably:
		- regiondetection.py
			The Python file that contains the region extraction from a screenshot
		- classifiers.py
			File that contains the classifiers used during testing of the project

/script/
	Stand-along python scripts used during various stages of the project