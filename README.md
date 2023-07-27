vimeo-download
================

Download vimeo video from master.json.

Basically totally rewritten from [the original](https://github.com/eMBee/vimeo-download). Supports multi-thread downloading.

Installation
-------------

* Clone the repo.
* Install requirements with `pip install -r requirements.txt`

Make sure you have ffmpeg installed and in your PATH.


Usage
-----

To use this script, the master url needs to be manually extracted from the page:

   `python vimeo-download.py "http://...master.json?base64_init=1" --output <optional_name>`

To get the master url:

   1. Open the network tab in the inspector
   2. Find the url of a request to the `master.json` file
   3. Run the script with the url as argument

Full help:

      usage: vimeo-download.py [-h] [--output OUTPUT] [--info] [--skip-merge] [--threads THREADS] [--test] url

      positional arguments:
      url                   master json url

      options:
      -h, --help            show this help message and exit
      --output OUTPUT, -o OUTPUT
                              output video filename
      --info, -i            print info and exit
      --skip-merge          downloads only and doesn't merge
      --threads THREADS, -n THREADS
                              number of threads to use (default: 10)
      --test                INTERNAL USAGE ONLY: test mode, only download first 100 segments.