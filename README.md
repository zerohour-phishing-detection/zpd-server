[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Ruff](https://github.com/zerohour-phishing-detection/zpd-server/actions/workflows/ruff.yml/badge.svg?branch=main)](https://github.com/zerohour-phishing-detection/zpd-server/actions/workflows/ruff.yml)

# Zerohour Phishing Detection server
This repository contains the backend server of the ZPD decision-support tool.

This project originates from A Decision-Support Tool for Experimentation on Zero-Hour Phishing Detection. Burda, P., Allodi, L., Zannone, N. (2023). In: Foundations and Practice of Security. FPS 2022. LNCS, vol 13877. Springer. https://doi.org/10.1007/978-3-031-30122-3_27

## Usage (development)
For a development environment, we recommend running the server directly with `python3 api.py`. The project is developed with Python 3.11, and the requirements can be installed through `pip install -r requirements.txt`. Moreover, if you wish to use the Google Cloud Vision logo finder, you'll need to set up Google Cloud credentials, see the [Google Cloud Vision setup](#google-cloud-vision-setup) section.

We also recommend working in a Python virtual environment to manage library version conflicts: the `.venv` and `venv` directories will automatically be ignored by Git.

## Usage (production)
For the production environment, there is a Docker setup available in the repository, through the Docker file and Docker Compose file. Running it is as simple as running `docker compose up`, after which it will be deployed to port 5000. Keep in mind that the build stage of the image can take quite some time.

If you wish to use the Google Cloud Vision logo finder, you'll need to set up Google Cloud credentials, see the [Google Cloud Vision setup](#google-cloud-vision-setup) section.

## Google Cloud Vision setup
To be able to use Google Cloud Vision Logo Detection (based in `vision_logo_detection.py`),
you need to add a `.gcloud_creds.json` file, containing a service account key to a Google Cloud Service Account.

### Obtaining Google Cloud Credentials
If you've just started working on this project and noone else has set up Google Cloud yet, you can follow these steps.
1. Sign up for [Google Cloud Free Trial](https://console.cloud.google.com/freetrial). This requires a credit card, but you will not be deducted any money from it. Keep in mind that using a virtual credit card and with a fresh Google account may not work, as you may get an error message (likely because of fraud prevention).
2. Make a project, or just use the initial empty project if you don't plan on using Google Cloud for anything else.
3. Make a Service account (Navigation menu > IAM and admin > Service accounts). No permissions need to be granted. No users need to be granted access.
4. Create keys for the service account (click account > open 'keys' tab), in JSON format. For security purposes, do not share your key with other people, instead make new keys for your fellow developers. If you want, you can also create a service account per developer, that way you can track API usage per person.
5. Keep in mind that this method of providing credentials is the least recommended of all ways Google Cloud allows you to identify, and it is only recommended for a development environment. If you wish to create a proper production setup, see the [Google Cloud docs](https://cloud.google.com/docs/authentication).

## Notes on repository structure
This section contains some information regarding the structure of the files and folders in this repository.
- `api_versions` (source): the different versions of the HTTP API.
- `compare_screens`: temporary screenshots of websites used for processing a check
- `db`: databases for cache (`sessions.db`), settings (`settings.db`) and long-term archive or detection checks and their results (`archive.csv`). The latter has rows in the format `UUID (who requested it),url,timestamp (Unix),settings,result`.
- `files`: temporary data of checks, such as screenshots of the requested page and region highlighting on that page.
- `logo_finders` (source): all implementations of different logo finders, currently the homebrew version (reverse logo region search) and the Google Cloud Vision (vision logo detection).
- `logs`: log files of different verbosities.
- `methods` (source): all detection methods, i.e. the different techniques used for detecting phishing pages. The technique from the aforementioned paper can be found in `dst.py`.
- `saved-classifiers`: the classifier used by the homebrow logo finder to tell logos from other sections of a webpage.
- `search_engines` (source): text and reverse image search engines as an easy-to-use API.
- `settings` (source): different settings storages of client settings
- `templates`: a simple static HTML page to test if the server is online
- `utils` (source): a whole lot of utility source code

## Acknowledgment:
The authors wish to express their gratitude to Ardela Isuf and Sam Cantineau for their work in this project.

## License:
CC Attribution 4.0 International 
