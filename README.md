# A decision-support tool for experimentation on zero-hour phishing detection
Code and test data for anti-phishing tool: A decision-support tool for experimentation on zero-hour phishing detection (in submission) - Pavlo Burda, Luca Allodi and Nicola Zannone, Eindhoven University of Technology, The Netherlands

## Abstract
>New, sophisticated phishing campaigns victimize targets in few hours from attack delivery.
Some techniques can spot these zero-hour attacks, at the cost of additional user intervention. Further research is needed to fill this gap.
We present a phishing detection tool that enables research on zero-hour detection and user intervention trade-offs.

## Usage
First, dependencies in [requirements.txt](requirements.txt) and python3 shall be installed.
Then, there are two steps to test the scripts:
- [Flask API](api.py) starts the flask API server with `python3 api.py` (or via `flask app run`, keep in mind the `PATH` variables for this)
	- The server runs locally on port 5000
	- POST requests can be built, such as:
		- >test_json = {
		- > "URL": "https://idsrv.lv1871.de/Login",
		- > "uuid": "63054094-01c4-11ed-b939-0242ac120002",
		- > "pagetitle": "Lebensversicherung von 1871 a. G. München",
		- > "image64": "",
		- > "phishURL" : "http://bogusurl1.co.uk"
		- >}
	- the output of the process can be found in [sessions.db](db/sessions.db) and [output_operational.db](db/output_operational.db)
- [evaluation](evaluation) contains scripts to automate the evaluation from a sample of phishing/non-phishing sites
	- The used dataset for sampling benign and phishing data can be found [here](https://surfdrive.surf.nl/files/index.php/s/xndCmdvb7yzM8ED).
- [check-classifiers.py](check-classifiers.py) and [hit-verifier.py](hit-verifier.py) are middleware to pre-process `output_operational.db` for the evaluation
- [ROC.py](ROC.py) carries out the final evaluation with two databases as input ('phishing' and 'benign')

 
## Acknowledgment:
The authors wish to express their gratitude to Ardela Isuf and Sam Cantineau for their work in this project.

## License:
CC Attribution 4.0 International 
