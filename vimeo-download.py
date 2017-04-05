import requests
import base64
from tqdm import tqdm
import sys
import subprocess as sp

FFMPEG_BIN = 'ffmpeg.exe'

master_json_url = sys.argv[1]
base_url = master_json_url[:master_json_url.rfind('/', 0, -26) - 5]

resp = requests.get(master_json_url)
content = resp.json()

heights = [(i, d['height']) for (i, d) in enumerate(content['video'])]
idx, _ = max(heights, key=lambda (_, h): h)
video = content['video'][idx]
video_base_url = base_url + 'video/' + video['base_url']
print 'base url:', video_base_url

filename = 'v.mp4'
video_filename = filename
print 'saving to %s' % filename

video_file = open(filename, 'wb')

init_segment = base64.b64decode(video['init_segment'])
video_file.write(init_segment)

for segment in tqdm(video['segments']):
    segment_url = video_base_url + segment['url']
    resp = requests.get(segment_url, stream=True)
    if resp.status_code != 200:
        print 'not 200!'
        print resp
        print segment_url
        break
    for chunk in resp:
        video_file.write(chunk)

video_file.flush()
video_file.close()

audio = content['audio'][0]
audio_base_url = base_url + audio['base_url'][3:]
print 'base url:', audio_base_url

filename = 'a.mp3'
audio_filename = filename
print 'saving to %s' % filename

audio_file = open(filename, 'wb')

init_segment = base64.b64decode(audio['init_segment'])
audio_file.write(init_segment)

for segment in tqdm(audio['segments']):
    segment_url = audio_base_url + segment['url']
    resp = requests.get(segment_url, stream=True)
    if resp.status_code != 200:
        print 'not 200!'
        print resp
        print segment_url
        break
    for chunk in resp:
        audio_file.write(chunk)

audio_file.flush()
audio_file.close()

filename = sys.argv[2] + '.mp4' if sys.argv[2] else 'video.mp4'

command = [ FFMPEG_BIN,
        '-y', # (optional) overwrite output file if it exists
        '-i', audio_filename,
        '-i',video_filename,
        '-acodec', 'copy',
        '-vcodec', 'h264',
        filename ]

sp.call(command, shell=True)