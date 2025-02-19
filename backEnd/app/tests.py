from django.test import TestCase

# Create your tests here.
import subprocess
ffmpeg_path = "/home/nottingchain12/Documents/Listen/ffmpeg_bin/ffmpeg"  # ffmpeg路径
video_path = "/home/nottingchain12/Documents/listen1/templates/editing/horizontal/2/end.mp4"
video_m_path = "/home/nottingchain12/Documents/listen1/templates/editing/horizontal/2/end1.mp4"
acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "[0]scale=1920:1080,setsar=sar=0/1,settb=AVTB" -acodec copy -c:v h264_nvenc -an -r 30 -b:v 4M -bufsize 4M -y {video_m_path} -loglevel quiet'
result = subprocess.call(acmd, shell=True)