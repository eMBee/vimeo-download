import argparse
import base64
import concurrent.futures
import datetime
import random
import re
import string
from pathlib import Path
from subprocess import run
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

# Prefix for this run
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
SALT = ''.join(random.choice(string.digits) for _ in range(3))
OUT_PREFIX = TIMESTAMP + '-' + SALT


# Modiifed from https://www.peterbe.com/plog/best-practice-with-retries-with-requests
def requests_retry_session(
    retries=5,
    backoff_factor=0.2,
    status_forcelist=(502, 503, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def download(url):
    resp = requests_retry_session().get(url)
    if resp.status_code != 200:
        print('not 200!')
        print(resp)
        print(url)
        return False
    return resp.content


def download_segments(base_url, content, output, threads=10, simulate=False, test=False):
    success = True

    content.sort(key=lambda d: (d.get('width', 0) * d.get('height', 0), d.get('framerate', 0), d.get('bitrate', 0)), reverse=True)
    best = content[0]

    print('Variant info:')
    for variant in content:
        # print some info
        print(f'[{variant["id"]}] {variant["format"]}, {variant["mime_type"]}, {variant["codecs"]}, ', end='')
        if 'width' in variant:
            print(f'{variant["width"]}x{variant["height"]}, ', end='')
        if 'framerate' in best:
            print(f'{variant["framerate"]:.2f} fps, ', end='')
        if 'bitrate' in variant:
            print(f'nominal: {variant["bitrate"] /1024/1024:.2f} Mbps ', end='')
        if 'avg_bitrate' in variant:
            print(f'(avg: {variant["avg_bitrate"] /1024/1024:.2f} Mbps)', end='')
        print()

    print(f'Automatically picks the best one ({best["id"]}).')

    best_base_url = urljoin(base_url, best['base_url'])
    print('Base url:', best_base_url)
    print(f'Saving to {output}')

    if simulate:
        return success

    output_temp = output.with_suffix(output.suffix + '.dl')
    video_file = output_temp.open('wb')

    init_segment = base64.urlsafe_b64decode(best['init_segment'])
    video_file.write(init_segment)

    if 'index_segment' in best:
        segment_url = best_base_url + best['index_segment']
        video_file.write(download(segment_url))

    # cap best['segments'] to 100 for testing
    if test:
        best['segments'] = best['segments'][:100]

    progress = tqdm(total=len(best['segments']), desc='Downloading segments', ncols=150)
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {}
        for i in range(len(best['segments'])):
            segment_url = best_base_url + best['segments'][i]['url']
            futures[ex.submit(download, segment_url)] = i

        downloaded_content = []
        to_do = 0
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            content = future.result()
            futures.pop(future)
            if content != False:
                downloaded_content.append((i, content))
                _ = []
                for idx, content in sorted(downloaded_content):
                    if idx == to_do:
                        video_file.write(content)
                        to_do += 1
                        progress.update(1)
                    else:
                        _.append((idx, content))
                downloaded_content = _
            else:
                success = False
                break

    progress.close()
    video_file.flush()
    video_file.close()

    if success:
        output_temp.rename(output)
    else:
        print('Download failed. Temp file is kept at', output_temp)
    return success


def merge_audio_video(video_filename, audio_filename, output_filename):
    command = ['ffmpeg', '-hide_banner',
               '-i', video_filename,
               '-i', audio_filename,
               '-c', 'copy', output_filename
               ]
    print("FFMPEG command is:", command)
    run(command)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", action="store", help="master json url")
    parser.add_argument("--output", "-o", action="store", help="output video filename", default=None)
    parser.add_argument("--info", "-i", action="store_true", help="print info and exit")
    parser.add_argument("--skip-merge", action="store_true", help="downloads only and doesn't merge")
    parser.add_argument("--threads", "-n", action="store", help="number of threads to use (default: 10)", default=10, type=int)
    parser.add_argument("--test", action="store_true", help="INTERNAL USAGE ONLY: test mode, only download first 100 segments.")
    args = parser.parse_args()

    # Set output filename depending on defaults
    if args.output:
        if not args.output.lower().endswith('.mp4'):
            args.output += '.mp4'
        output = Path(args.output)
    else:
        output = Path(OUT_PREFIX + '.mp4')
    print("Output filename set to:", output)

    video_output = output.with_name(f'{output.stem}_video.mp4')
    audio_output = output.with_name(f'{output.stem}_audio.mp4')

    master_json_url = args.url

    # get the content
    resp = requests_retry_session().get(master_json_url)
    if resp.status_code != 200:
        match = re.search(r'<TITLE>(.+)<\/TITLE>', resp.content, re.IGNORECASE)
        title = match.group(1)
        print('HTTP error (' + str(resp.status_code) + '): ' + title)
        quit(0)
    content = resp.json()
    base_url = urljoin(master_json_url, content['base_url'])

    print('Download video part...')
    if not download_segments(base_url, content['video'], video_output, simulate=args.info, threads=args.threads):
        quit()
    if not content['audio']:
        if args.info:
            print('No audio part.')
            quit()
        else:
            print('No audio part. It\'s possible video track already has audio. Rename video part to output.')
            video_output.rename(output)
        quit()
    print('Download audio part...')
    if not download_segments(base_url, content['audio'], audio_output, simulate=args.info, threads=args.thread):
        quit()

    # Combine audio and video
    if not args.skip_merge:
        merge_audio_video(video_output, audio_output, output)

