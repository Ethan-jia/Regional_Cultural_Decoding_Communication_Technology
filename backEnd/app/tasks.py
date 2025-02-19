import datetime
import os
import cv2  # opencv-python
import json
import time
import glob
import math
import random
import ffmpeg  # ffmpeg-python
import requests
import subprocess
import traceback
import shutil

from datetime import date, timedelta
from celery import shared_task

from dateutil import relativedelta
from app.models import VideoInfo
from listen1.settings import redis_conn
from app.video_ai_process12 import *

# # APPID，应用ID，服务商模式下为服务商应用ID，即官方文档中的sp_appid
# APPID = 'wx0bd63ae3ece721b1'
# # APP_SECRET
# APP_SECRET = "ba35d06724b45e258ee0e22a79c86ed6"

# APPID
APPID = 'wx0ca85ad95955ca6c'
# APP_SECRET
APP_SECRET = "13ad214d000f7f624289e6d2302567f8"

ffmpeg_path = "/home/nottingchain12/Documents/Listen/ffmpeg_bin/ffmpeg"  # ffmpeg路径
ffprobe_path = "/home/nottingchain12/Documents/Listen/ffmpeg_bin/ffprobe"  # ffprobe路径
base_path = "/home/nottingchain12/Documents/listen1"


@shared_task
def subscribe_status(open_id, secret_key):
    params = {
        "appid": APPID,
        "secret": APP_SECRET,
    }
    r = requests.get("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential", params=params)
    access_token = json.loads(r.text)['access_token']
    begin_time = time.time()
    while True:
        time.sleep(5)
        # 查找视频
        video_obj = VideoInfo.objects.filter(openid=open_id, secret_key=secret_key).first()
        if video_obj is not None:
            data = {
                "touser": open_id,
                "template_id": "w3vvFG2HHxGrLanXNagDCwz7uNw_RtXV1xvOQrV4kHE",
                "page": "/pages/travel/index",
                "data": {
                    "thing1": {"value": f"阆中{video_obj.video_type}视频"},
                    "date2": {"value": video_obj.generate_time},
                    "thing3": {"value": "打开小程序查作品"},
                    "date6": {"value": video_obj.invalid_time},
                    "phrase9": {"value": "已完成"},
                }
            }
            break
        now_time = time.time()
        if now_time - begin_time > 60:
            generateTime = time.strftime("%Y-%m-%d %H:%M:%S")
            invalidTime = time.strftime("%Y-%m-%d")
            data = {
                "touser": open_id,
                "template_id": "w3vvFG2HHxGrLanXNagDCwz7uNw_RtXV1xvOQrV4kHE",
                "page": "/pages/travel/index",
                "data": {
                    "thing1": {"value": f"阆中游记视频"},
                    "date2": {"value": generateTime},
                    "thing3": {"value": "请重新尝试生成视频"},
                    "date6": {"value": invalidTime},
                    "phrase9": {"value": "失败"},
                }
            }
            break

    url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"
    r = requests.post(url, data=json.dumps(data))
    print(json.loads(r.text))


@shared_task
def matting_upload(template, template_type, platform, video_path, video_m_path, video_upload_path):
    if template == "1":
        template_time = 17
    elif template == "2":
        template_time = 18
    else:
        return False

    # 获取上传视频相关信息
    temp_path = f"{base_path}/{video_path}"
    probe = ffmpeg.probe(temp_path, cmd=ffprobe_path)
    video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    upload_time = float(video_stream["duration"])  # 视频时长

    # 模板视频与接收的视频时长差
    if template_time > upload_time:
        video_time = math.floor(upload_time)
    else:
        video_time = template_time

    if template == "2" and template_type == "matting" and platform == "ios":
        filter_complex = f"select='between(t,0,{video_time})',setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1"
        filter_complex = f"select='between(t,0,{video_time})',setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1,transpose=2,scale=1920:1080"
        acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "{filter_complex}" -c:v h264_nvenc -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'
    elif template == "2" and template_type == "matting" and platform == "android":
        filter_complex = f"select='between(t,0,{video_time})',setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1,scale=1920:1080"
        acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "{filter_complex}" -c:v h264_nvenc -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'
    elif template == "1" and template_type == "matting":
        filter_complex = f"select='between(t,0,{video_time})',setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1"
        acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "{filter_complex}" -c:v h264_nvenc -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'

    result = subprocess.call(acmd, shell=True)
    if result == 0:
        json_upload_path = os.path.join(video_upload_path, "information.json")
        with open(json_upload_path, 'w', encoding='utf-8') as f:
            json.dump({"duration": str(video_time)}, f)
        # 删除临时视频
        os.remove(video_path)


@shared_task
def matting(secret_key_path, template):
    try:
        a = time.time()
        # 上传视频的目录
        video_upload_path = os.path.join(secret_key_path, "upload")
        matting_save_path = os.path.join(secret_key_path, "save")
        matting_template_path = os.path.join("templates", "matting")
        if len(os.listdir(matting_save_path)):

            for _ in os.listdir(matting_save_path):
                os.remove(os.path.join(matting_save_path, _))
        video_name = os.listdir(video_upload_path)[0]

        # 上传视频的地址
        video_path = os.path.join(video_upload_path, video_name)
        matting_save_video_path = os.path.join(matting_save_path, video_name)
        video_template_path = os.path.join(os.path.join(matting_template_path, template), "template.mp4")
        audio_template_path = os.path.join(os.path.join(matting_template_path, template), "bgsound.mp3")
        json_upload_path = os.path.join(video_upload_path, "information.json")

        # check
        begin_time = time.time()
        end_exist = False
        while not end_exist:
            end_exist = True
            if not os.path.exists(video_path):
                end_exist = False
            else:
                if os.stat(video_path).st_size == 0:
                    end_exist = False
                else:
                    log_path = os.path.join(video_upload_path, "error.log")
                    result = subprocess.call(f'{ffmpeg_path} -v error -i {video_path} -f null - 2>{log_path}',
                                             shell=True)
                    if result == 0:
                        if os.path.exists(log_path):
                            if os.stat(log_path).st_size != 0:
                                print("os.stat(log_path).st_size:", os.stat(log_path).st_size)
                                end_exist = False
                        else:
                            print(f"{log_path} not exist!!")
                            end_exist = False
                    else:
                        end_exist = False

        while True:
            if os.path.exists(json_upload_path):
                with open(json_upload_path, encoding="utf-8") as json_obj:
                    duration_dict = json.load(json_obj)
                break
            now_time = time.time()
            if now_time - begin_time > 20:
                return False

        # 抠图过程
        matting_dict = {
            "config": "matting/matting_model/deploy.yaml",
            "save_dir": video_upload_path,
            "bg_video_path": video_template_path,
            "video_path": video_path,
        }
        matting_cmd = f"python matting/bg_replace.py" + "".join(
            [f" --{key} {value}" for key, value in matting_dict.items()])
        result = subprocess.call(matting_cmd, shell=True)
        if result != 0:
            return False
        # 添加音频
        video_matting_path = os.path.join(video_upload_path, f"{video_name.split('.')[0]}.avi")
        add_sound_cmd = f'{ffmpeg_path} -i {video_matting_path} -i {audio_template_path} -t {duration_dict["duration"]} -c:v h264_nvenc -b:v 2M -bufsize 2M -y {matting_save_video_path} -loglevel quiet'
        # subprocess.Popen(add_sound_cmd, shell=True, stdout=None, stderr=None).wait()
        result = subprocess.call(add_sound_cmd, shell=True)
        if result == 0:
            return matting_save_video_path
        else:
            return False
    except Exception as e:
        traceback.print_exc()
        return False


@shared_task
def editing_upload(video_path, template_type, video_m_path, video_upload_path):
    temp_path = f"{base_path}/{video_path}"
    probe = ffmpeg.probe(temp_path, cmd=ffprobe_path)
    vc = cv2.VideoCapture(temp_path)
    height = vc.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = vc.get(cv2.CAP_PROP_FRAME_WIDTH)
    video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    duration = int(float(video_stream["duration"]))  # time
    if template_type == "editing_horizontal":
        if width < height:  # 竖屏
            # 竖屏 - 横屏
            acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "[0]scale=1080:1920,setsar=sar=0/1,settb=AVTB,split[a][b];[a]scale=-1:ih/2,crop=iw:iw*9/16,boxblur=8:2,scale=1920:1080[c];[b]scale=-1:1080[d];[c][d]overlay=(W-w)/2:0" -acodec copy -c:v h264_nvenc -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'
        else:  # 横屏
            acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "[0]scale=1920:1080,setsar=sar=0/1,settb=AVTB" -acodec copy -c:v h264_nvenc -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'
    elif template_type == "editing_vertical":
        if width < height:  # 竖屏
            acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "[0]scale=1080:1920,settb=AVTB" -acodec copy -c:v h264_nvenc -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'
        else:  # 横屏
            # 横屏 - 竖屏
            acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "[0]scale=1920:1080,settb=AVTB,split[a][b];[a]scale=iw/2:-1,crop=ih*9/16:ih,boxblur=8:2,scale=1080:1920[c];[b]scale=1080:-1[d];[c][d]overlay=0:(H-h)/2" -acodec copy -c:v h264_nvenc -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'
    else:
        return False
    result = subprocess.call(acmd, shell=True)

    json_upload_path = os.path.join(video_upload_path, "information.json")
    if os.path.exists(json_upload_path):
        with open(json_upload_path, encoding="utf-8") as json_obj:
            information_list = json.load(json_obj)
            information_list.append({"video_name": video_m_path, "duration": str(duration)})
        with open(json_upload_path, 'w', encoding='utf-8') as f:
            json.dump(information_list, f)
    else:
        with open(json_upload_path, 'w', encoding='utf-8') as f:
            json.dump([{"video_name": video_m_path, "duration": str(duration)}], f)
    try:
        if result == 0:
            # 删除临时视频
            os.remove(temp_path)
    except Exception as e:
        traceback.print_exc()
        return False


@shared_task
def editing(secret_key_path, template, secret_key, type_):
    try:
        a = time.time()
        splicing_upload_path = os.path.join(secret_key_path, "upload")
        splicing_save_path = os.path.join(secret_key_path, "save")
        splicing_save_video_path = os.path.join(splicing_save_path, f"{secret_key}.mp4")
        json_upload_path = os.path.join(splicing_upload_path, "information.json")

        # check
        begin_time = time.time()
        while True:
            r_list = glob.glob(f'{splicing_upload_path}/*_.mp4')
            if len(r_list) == 0:
                try:
                    with open(json_upload_path, encoding="utf-8") as json_obj:
                        information_list = json.load(json_obj)
                except:
                    pass
                if len(information_list) == len(os.listdir(splicing_upload_path)) - 1:
                    break
            now_time = time.time()
            if now_time - begin_time > 10:
                return False

        if type_ == "vertical" and template == "1":
            all_time = 63.7
            start_time = 10.033
            end_time = 9.8
        elif type_ == "horizontal" and template == "1":
            all_time = 70.4
            start_time = 7.7
            end_time = 3.733
        elif type_ == "vertical" and template == "2":
            all_time = 59.466
            start_time = 8
            end_time = 14.7
        elif type_ == "horizontal" and template == "2":
            all_time = 64.833
            start_time = 6.4
            end_time = 5.2

        available_time = all_time - start_time - end_time
        len_list = len(information_list)
        one_time = int(available_time / len_list)
        sum_time = start_time + end_time

        filter_cmd = '-filter_complex "[0]settb=AVTB[C00];'
        for i in range(len_list):
            current_time = int(information_list[i]["duration"])

            if current_time < one_time:
                filter_cmd += f'[{i + 1}]settb=AVTB[C0{i + 1}];'
                sum_time += current_time
            else:
                _ = random.randint(0, current_time - one_time)
                filter_cmd += f"[{i + 1}]select='between(t,{_},{_ + one_time})',setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1[C0{i + 1}];"
                sum_time += one_time
        filter_cmd += f'[{len_list + 1}]settb=AVTB[C0{len_list + 1}];'
        video_num = len_list + 2

        for i in range(video_num):
            in_str = f"[C0{i}]"
            filter_cmd += in_str
        filter_cmd += f"concat=n={video_num}[temp];"
        af_str = f'[{video_num}:a]afade=t=out:st={format(sum_time - 3, ".3f")}:d=3[a1]" '
        filter_cmd += af_str

        # cmd
        cmd1 = f"{ffmpeg_path} -i templates/editing/{type_}/{template}/start.mp4 "
        for _ in range(len_list):
            cmd1 += f"-i {information_list[_]['video_name']} "
        cmd1 += f"-i templates/editing/{type_}/{template}/end.mp4 -i templates/editing/{type_}/{template}/bgsound.mp3 "
        cmd1 += f'-ss 00:00:00 -t {format(sum_time, ".3f")} '
        cmd1 += filter_cmd
        cmd1 += f'-map "[temp]" -map "[a1]" -c:v h264_nvenc -r 30 -preset medium -b:v 2M -bufsize 2M '
        cmd1 += f'-y {splicing_save_video_path} -hide_banner -loglevel error'
        result = subprocess.call(cmd1, shell=True)
        if result == 0:
            print(f'{time.time() - a} s')
            return splicing_save_video_path
        else:
            return False
    except Exception as e:
        traceback.print_exc()
        return False


@shared_task
def ai_upload(video_type, video_path):
    start_time = time.time()
    extracted_fragments = extract_frames(video_path)
    recognized_fragments = analyze_prediction(*predict_(
        onnxruntime.InferenceSession("resnet18.onnx", providers=['CPUExecutionProvider']), extracted_fragments,
        transforms.Compose([transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])]),
        idx_to_class))
    video_path_splitext0 = os.path.splitext(video_path)[0]
    with open(video_path_splitext0 + '.json', 'w', encoding='utf-8') as f:
        json.dump(recognized_fragments, f)
    video_dir = os.path.dirname(os.path.dirname(video_path))
    fragment_second = 3.4
    split_num = 0
    if recognized_fragments:
        for rf in recognized_fragments:
            split_num += int((rf[1] - rf[0] - fragment_second) // (2 + fragment_second)) + 1
    if split_num > 0:  # [(0.0, 6.5, '张飞庙_大门')]
        vc = cv2.VideoCapture(video_path)
        height = vc.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = vc.get(cv2.CAP_PROP_FRAME_WIDTH)
        video_m_path = video_path_splitext0 + '#.mp4'
        if video_type == 'ai_horizontal':  #
            single_time = 1.2
            front_second = 1.5
            template_video_dir = "/home/nottingchain12/Documents/listen1/templates/ai/horizontal/1"
            last_clip_time = 10 + 16 / 30
            if width < height:
                # 竖屏 -> 横屏
                acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "[0]scale=-1:ih/2,crop=iw:iw*9/16,boxblur=2:2,scale=1920:1080[c];[0]scale=-1:1080[d];[c][d]overlay=(W-w)/2:0" -c:v h264_nvenc -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'
                subprocess.call(acmd, shell=True)
                no_changed = False
            else:
                subprocess.call(
                    f'{ffmpeg_path} -i {video_path} -an -r 30 -y {video_m_path} -hide_banner -loglevel error',
                    shell=True)
                no_changed = True
        else:
            single_time = 1.2
            front_second = 1.5
            template_video_dir = "/home/nottingchain12/Documents/listen1/templates/ai/vertical/1"
            last_clip_time = 9 + 23 / 30
            if width > height:
                acmd = f'{ffmpeg_path} -i {video_path} -filter_complex "[0]scale=iw/2:-1,crop=ih*9/16:ih,boxblur=2:2,scale=1080:1920[c];[0]scale=1080:-1[d];[c][d]overlay=0:(H-h)/2" -c:v h264_nvenc  -an -r 30 -b:v 2M -bufsize 2M -y {video_m_path} -loglevel quiet'
                subprocess.call(acmd, shell=True)
                no_changed = False
            else:
                subprocess.call(
                    f'{ffmpeg_path} -i {video_path} -an -r 30 -y {video_m_path} -hide_banner -loglevel error',
                    shell=True)
                no_changed = True
        fps = '30'
        save_dir = 'save'
        d2 = str(0.6 * single_time)
        last_remain_second = last_clip_time - front_second - single_time * 6
        last_remain_second = str(last_remain_second)
        single_time = str(single_time)
        front_second = str(front_second)
        pic_num = redis_conn.get(f'{video_dir}##pic_num')
        fragment_num = len(recognized_fragments)
        if pic_num == None:
            redis_conn.set(f'{video_dir}##pic_num', fragment_num)
            if fragment_num < 6:
                extract_pic = fragment_num
            else:
                extract_pic = 6
            pic_num = 0
        else:
            if int(pic_num) < 6:
                if int(pic_num) + fragment_num < 6:
                    extract_pic = fragment_num
                else:
                    extract_pic = 6 - int(pic_num)
                redis_conn.incr(f'{video_dir}##pic_num', amount=fragment_num)
            else:
                extract_pic = 0
        if extract_pic:
            photo_scale = '768x440' if video_type == 'ai_horizontal' else "440x768"
            result_list = []
            if no_changed:
                extract_video_path = video_path
            else:
                extract_video_path = video_m_path
            while True:
                if os.path.exists(extract_video_path):
                    break
            for index, recognized_fragment in enumerate(recognized_fragments):
                if index < extract_pic:
                    cmd_str = f"""{ffmpeg_path} -i {extract_video_path} -ss {recognized_fragment[0] + 1} -frames:v 1 -vf "scale={photo_scale},drawbox=x=0:y=0:w=iw:h=ih:color=white@0.6:t=15" -y {video_dir}/save/{str(int(pic_num) + index)}.jpg -hide_banner -loglevel error"""
                    resut = subprocess.call(cmd_str, shell=True)
                    while resut:
                        resut = subprocess.call(cmd_str, shell=True)
            for i in range(int(pic_num) + 1, int(pic_num) + extract_pic + 1):
                while True:
                    if os.path.exists(f'{video_dir}/save/{str(i - 1)}.jpg'):
                        if os.stat(f'{video_dir}/save/{str(i - 1)}.jpg').st_size != 0:
                            break
                if i == 2:
                    result = end_2(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, d2)
                    while result:
                        result = end_2(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, d2)
                elif i < 6:
                    exec(f"""result=end_{str(i)}(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir)
while result:
    result = end_{str(i)}(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir)
""")
                elif i == 6:
                    result = end_6(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir)
                    while result:
                        result = end_6(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir)
                    result = end_7(template_video_dir, photo_scale, last_remain_second, fps, video_dir, save_dir)
                    while result:
                        result = end_7(template_video_dir, photo_scale, last_remain_second, fps, video_dir, save_dir)
                else:
                    raise Exception("i>6!!!!")
    else:
        os.rename(video_path, video_path_splitext0 + '#.mp4')


@shared_task
def horizontal_screen(video_dir):
    class_frame_num_dict = {'牌坊': 1, '川北道署': 2, '贡院': 2, '文庙': 2, '街景': 1, '张飞庙': 2, '中天楼': 2,
                            '华光楼': 2}
    extra_class_name_set = {'牌坊', '街景'}
    material_video_dir = "/home/nottingchain12/Documents/listen1/material/horizontal"
    template_video_dir = "/home/nottingchain12/Documents/listen1/templates/ai/horizontal/1"
    original_checkpoint_list = [[('00:00-00:00 -05:06', None)],  # 1.开头
                                [('-05:06 07:16-08:02', 'fade')],  # 2.牌坊
                                [('07:16-08:02 10:00-10:16', 'fade'),  # 3.川北道署
                                 ('10:00-10:16 -12:26', None)],  # 4.川北道署
                                [('-12:26 15:10-15:22', 'fade'),  # 5.贡院
                                 ('15:10-15:22 -18:03', None)],  # 6.贡院
                                [('-18:03 20:16-20:28', 'fade'),  # 7.文庙
                                 ('20:16-20:28 22:27-23:13', 'fade')],  # 8.文庙
                                [('22:27-23:13 -25:22', None)],  # 9.街景
                                [('-25:22 28:02-28:14', 'fade'),  # 10.张飞庙
                                 ('28:02-28:14 30:19-30:29', 'fadeblack')],  # 11.张飞庙
                                [('30:19-30:29 33:05-33:17', 'fade'),  # 12.中天楼
                                 ('33:05-33:17 35:24-36:06', 'fadeblack')],  # 13.中天楼
                                [('35:24-36:06 38:08-38:20', 'fade'),  # 14.华光楼
                                 ('38:08-38:20 40:25-41:11', 'fadeblack')],  # 15.华光楼
                                [('40:25-41:11 -51:11', None)]]
    fragment_second = 3.4
    fragment_interval_second = 1
    scale = "1920:1080"
    photo_scale = "768x440"
    single_time = 1.2
    front_second = 1.5
    pic_num = redis_conn.get(f'{video_dir}##pic_num')
    if pic_num is None:
        return random.choice(glob.glob(f'{template_video_dir}/ai_composite_*.mp4')).replace(
            r'/home/nottingchain12/Documents/listen1/', '')
    else:
        pic_num = int(pic_num)
    surplus_num = 6 - pic_num if pic_num < 6 else 0
    result = whole_process(video_dir, material_video_dir, template_video_dir,
                           class_frame_num_dict, extra_class_name_set, original_checkpoint_list,
                           surplus_num, fragment_interval_second,
                           scale=scale, photo_scale=photo_scale, single_time=single_time, front_second=front_second)
    if result == 0:
        return f"{video_dir}/save/ai_composite.mp4"
    else:
        return False


@shared_task
def vertical_screen(video_dir):
    class_frame_num_dict = {'牌坊': 1, '川北道署': 2, '张飞庙': 3, '文庙': 2, '街景': 1, '贡院': 3, '中天楼': 3}
    extra_class_name_set = {'牌坊', '街景'}
    material_video_dir = "/home/nottingchain12/Documents/listen1/material/vertical"
    template_video_dir = "/home/nottingchain12/Documents/listen1/templates/ai/vertical/1"
    original_checkpoint_list = [[('00:00-00:00 05:04-05:20', 'fade')],  # 1 start
                                [('05:04-05:20 07:14-07:28', 'fade')],  # 2 牌坊
                                [('07:14-07:28 09:20-10:06', 'fade'),  # 3 川北道署
                                 ('09:20-10:06 -11:27', None)],  # 4 川北道署
                                [('-11:27 13:19-14:04', 'fade'),  # 5 张飞庙
                                 ('13:19-14:04 16:01-16:17', 'fade'),  # 6 张飞庙
                                 ('16:01-16:17 19:00-20:21', 'fadeblack')],  # 7 张飞庙
                                [('19:00-20:21 22:14-23:00', 'fade'),  # 8 文庙
                                 ('22:14-23:00 26:01-26:17', 'fadewhite')],  # 9 文庙
                                [('26:01-26:17 -29:09', None)],  # 10 街景
                                [('-29:09 31:14-32:00', 'fade'),  # 11 贡院
                                 ('31:14-32:00 34:17-35:03', 'fade'),  # 12 贡院
                                 ('34:17-35:03 -37:29', None)],  # 13 贡院
                                [('-37:29 39:29-40:15', 'fade'),  # 14 中天楼
                                 ('39:29-40:15 -41:27', None),  # 15 中天楼
                                 ('-41:27 -44:11', None)],  # 16 中天楼
                                [('-44:11 -54:04', None)]  # end  46:05+1*6+
                                ]
    fragment_second = 3.4
    fragment_interval_second = 1
    scale = "1080:1920"
    photo_scale = "440x768"
    single_time = 1.2
    front_second = 1.5
    pic_num = redis_conn.get(f'{video_dir}##pic_num')
    if pic_num:
        pic_num = int(pic_num)
    else:
        return random.choice(glob.glob(f'{template_video_dir}/ai_composite_*.mp4')).replace(
            r'/home/nottingchain12/Documents/listen1/', '')
    surplus_num = 6 - pic_num if pic_num < 6 else 0
    result = whole_process(video_dir, material_video_dir, template_video_dir,
                           class_frame_num_dict, extra_class_name_set, original_checkpoint_list,
                           surplus_num, fragment_interval_second,
                           scale=scale, photo_scale=photo_scale, single_time=single_time, front_second=front_second)
    if result == 0:
        return f"{video_dir}/save/ai_composite.mp4"
    else:
        return False


@shared_task
def test():
    now_time = datetime.datetime.now()
    res_time_stamp = now_time - relativedelta.relativedelta(days=3)
    res_time = res_time_stamp.strftime("%Y-%m-%d")
    VideoInfo.objects.filter(generate_stamp__lte=res_time).update(is_del=1)

    enerate_time = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f'run task: {enerate_time}')
    VideoInfo.objects.filter(invalid_time=time.strftime("%Y-%m-%d")).update(is_del=1)

    # video_root_path = "videos"
    # delete_name = (date.today() + timedelta(days=-3)).strftime("%Y-%m-%d")
    # delete_dir_path = os.path.join(video_root_path, delete_name)
    # try:
    #     shutil.rmtree(delete_dir_path)
    # except FileNotFoundError:
    #     pass
