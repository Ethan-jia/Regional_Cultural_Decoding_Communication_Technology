# Create your views here.
import os
import json
import time
import random
import datetime
import requests
import mimetypes
import subprocess

from wsgiref.util import FileWrapper
from datetime import date, timedelta
from wechatpayv3 import WeChatPay, WeChatPayType
from django.http import JsonResponse, StreamingHttpResponse

from app import tasks
from app.models import UserInfo, VideoInfo, AmountInfo, CountInfo, PhotoInfo
from listen1.settings import redis_conn
from tools.random_key import get_random_key
from listen1.settings import BASE_DIR

# 微信支付商户号
MCHID = '1622146167'
# 商户证书私钥
PRIVATE_KEY = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCw4avEOp8y7W91G/tK+9D8nfNVm4JDQlEdVu6Hg+JeaK0Ah2vE2wZfzv5xvN7cPRgFidUlDHw3Mdq5bRRs3uaM2ZHAwLFAgFZfwtOqls5wJTHsNP2ZL19kso+eJXEMmhkYydfLyNgJHqgE5LaxunRyEjno+7ikPHQ2RHr4YzFeVEslOd6KVDhvYIUKB4Kdj9Zl1ZuhOOIT05TOGGUo/5hWVwpfPf6IpHz1gvQMpmNcITTe/2La1s7YKnuH3AVf+aNLKnudYk3A+yabZXylNwe+G2DZViq/nMEyb9nTCHjSbobkWXTZKlfdtF3rFj350mUrJUGg6X+KZ0Uek4l91eUtAgMBAAECggEAKRxKT9FQLwYAYbefME5WxF/xrnP2UquXLrqFtflxI4AwtW7EHXzKfnodqVG8enO4oZDneTTtqeZsb6xqkuM7soDe323pxJQPfzJI/90NHgOHFt86EeBwy3a06ozJOaSXMKu4/CQyEeyOIJUH4Ub0yY5y5zOaNpHWcMZ5zkE/uCx8LVfQs1IXSjubU88UPW/KJh87gGIkTNMzqNgbJ0Dd8Y6n36zE2UlikzB45ldLripUYPFZZQprMhEgU+xk+UHv+V/g70Xb+aGjeR6ote3syCscyV+N7Phss3W9t/NSBkjROrN6C5HWySFYy7OyrKJGzuXjztur2fyLiCLP/dDQAQKBgQDispdWnyRjp/D1DVTCsNeXMxbBJrMXCCbMixwGF7gQp2GJqiDAdV+pAMsyjxdSzQyPkmjVY86qOdPnZGxBzrBgnafPjX96FcM01BWl5tmyLFyoVYaJSjiiVSO14xX/6121+357yb9TpLXbGPAvH9Oflf8zZAjBoGLiias9Aw03+QKBgQDHvqsrOjLhNeh6NyUrRwFDIepjoL9CuhHiJKuhxHBRDfDF2ENZ8JwGB8JPFxoOUNyrkEGsSC2EaJ5WNG7OxEMweInCZUjSmgxuGhl9Hsp3FJH/szNF0cnfvYZ5OEQNcnJNn6InVA8CsZjU4yYV1mqLv2wx7DbhlXBkp31n5cur1QKBgD04AUpxG4CV/6oNeZBB9VZtg32Rl9dmaiPehSjYCurkaKCmgsW2bKjVAAqdPa0slnHHFexaUZsClsjsA5gZ2uOcb47LJVuwuNBxXY85shw9gqAqyHQWyQh9eXFK68v6oYndaqC/MJ3D4yBRsbroG1wDQ7F7GCpBx7Jpfwaw5kbxAoGAAyhUdF57J2w+vI/ampCIyJLkraaA34EpfzWtMOV2ERHzWG1Ow0E2djHxNGbdFpTYqC2jnCGX9pvgxOQXTFV16nI9W0FWoV2mDKeE96Fg+fjtRemDSftDAbJxScFF8iB5Bhkb6xs9EYHVNKhSlc3J6WOhRjjBtVcza6PqK5ZKXfECgYEAr7btGmLEyLg94zaqcAZrmk5E4+5o0CgITQRJWpAFNVlVPvrFo/IB4utR+uTMbgtJNjdIVwrYQq8rw7EEwnHPhSMIO30o7f2p2BaTFV6NiF423EiQ1aOuTtOPw/+mGg6C0BUrhDabtyggEhatThzt06nbJ7havSuzLhzHPqxWTOs="
# 商户证书序列号
CERT_SERIAL_NO = '518E5BC832B4A1ADEEC41DBA12EA4E2F2CE0DA77'
# API v3密钥
APIV3_KEY = 'YT996mnX2sC0KT7TAcWW10g9GDvhTHRk'
# APPID
APPID = 'wx0ca85ad95955ca6c'
# APP_SECRET
APP_SECRET = "13ad214d000f7f624289e6d2302567f8"

# 回调地址，也可以在调用接口的时候覆盖
NOTIFY_URL = 'https://www.xxxx.com/notify'
# 微信支付平台证书缓存目录，初始调试的时候可以设为None
# CERT_DIR = './cert'
CERT_DIR = None
# 微信初始化
wxpay = WeChatPay(
    wechatpay_type=WeChatPayType.JSAPI,
    mchid=MCHID,
    private_key=PRIVATE_KEY,
    cert_serial_no=CERT_SERIAL_NO,
    apiv3_key=APIV3_KEY,
    appid=APPID,
    notify_url=NOTIFY_URL,
    cert_dir=CERT_DIR
)

ffmpeg_path = "/home/nottingchain12/Documents/Listen/ffmpeg_bin/ffmpeg"  # ffmpeg路径
# 视频地址
video_root_path = "videos"
if not os.path.exists(video_root_path):
    os.mkdir(video_root_path)

res = AmountInfo.objects.filter(amount_name="同款生成")
if not res:
    try:
        AmountInfo.objects.create(amount_name="同款生成", amount_price=3)
        AmountInfo.objects.create(amount_name="剪辑串编", amount_price=5)
        AmountInfo.objects.create(amount_name="AI融合剪辑", amount_price=8)
    except:
        pass


def templates(request):
    """
        返回模板信息
        接受的参数有：matting,editing_horizontal,editing_vertical,ai_horizontal,ai_vertical
    """
    # 获取参数 type
    template_type = request.GET.get("type")
    if not template_type:
        return JsonResponse({"code": "Failed", "msg": "No upload type parameters."})

    return_dict = []  # 返回列表
    template_type_0 = template_type.split("_")[0]  # 当前类别 matting,editing,ai
    template_path = os.path.join("templates", template_type_0)
    template_type_1 = ""
    if template_type_0 == "matting":
        template_type_1 = ""
    elif template_type_0 == "editing":
        template_type_1 = template_type.split("_")[1]  # 当前模式 horizontal,vertical
        template_path = os.path.join(template_path, template_type_1)
        template_type_1 = f"/{template_type_1}/"  # 拼接地址用
    elif template_type_0 == "ai":
        template_type_1 = template_type.split("_")[1]  # 当前模式 horizontal,vertical
        template_path = os.path.join(template_path, template_type_1)
        template_type_1 = f"/{template_type_1}/"  # 拼接地址用

    # 获取文件中模板信息
    template_dirs = os.listdir(template_path)
    template_dirs.sort()

    # 读取每个模板中 information 信息
    for _ in template_dirs:
        information_path = os.path.join(os.path.join(template_path, _), "information.json")
        with open(information_path, encoding='UTF-8') as json_obj:
            information_dict = json.load(json_obj)
        information_dict["id"] = _
        information_dict[
            "video_path"] = f"https://{request.META['HTTP_HOST']}/templates/{template_type_0}{template_type_1}/{_}/show.mp4/".replace(
            '\\', '/')
        return_dict.append(information_dict)
    return JsonResponse(return_dict, safe=False)


def swipe_pic(request):
    """获取轮播图地址"""
    query_list = PhotoInfo.objects.filter(is_hide=0)
    return_list = [{
        "image": i.photo_url,
        "type": i.type,
        "appId": i.app_id,
        "path": i.path,
        "url": i.url,
        "envVersion": i.env_version,
    } for i in query_list]
    return JsonResponse(return_list, safe=False)


def get_open_id(request):
    """第一次登录的时候获取openid"""
    # 获取参数 userCode
    js_code = request.GET.get("userCode")
    if not js_code:
        return JsonResponse({"code": "Failed", "msg": "No upload userCode parameters."})

    # 获取参数 userInfo
    user_info = request.GET.get("userInfo")
    if not user_info:
        return JsonResponse({"code": "Failed", "msg": "No upload userInfo parameters."})
    user_info = json.loads(user_info)
    # 获取 openid
    try:
        params = {
            "appid": APPID,
            "secret": APP_SECRET,
            "js_code": js_code,
        }
        r = requests.get("https://api.weixin.qq.com/sns/jscode2session", params=params)
        open_id = json.loads(r.text)["openid"]
    except:
        return JsonResponse({"code": "Failed", "msg": "openId generate failed."})

    # 查找是否有 openid 存在的用户
    user = UserInfo.objects.filter(openid=open_id)
    if user:
        # 存在则修改 user_code
        user.update(user_code=js_code)
    else:
        # 不存在则创建
        UserInfo.objects.create(
            openid=open_id,
            user_code=js_code,
            nickname=user_info["nickName"],
            avatar_url=user_info["avatarUrl"],
            gender=user_info["gender"],
            country=user_info["country"],
            province=user_info["province"],
            city=user_info["city"],
            language=user_info["language"]
        )

        # 计数
        CountInfo.objects.create(
            date=time.strftime("%Y-%m-%d"),
            year=time.strftime("%Y"),
            openid=open_id,
            is_login=1,
            is_make=0,
            is_payment=0,
            date_stamp=datetime.datetime.now()
        )
    return JsonResponse({"code": "OK", "openId": open_id})


def get_login_num(request):
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    now_time = time.strftime("%Y-%m-%d")
    count = CountInfo.objects.filter(date=now_time, openid=open_id)
    if count:
        count.update(is_login=1, date_stamp=datetime.datetime.now())
    else:
        CountInfo.objects.create(
            date=now_time,
            year=time.strftime("%Y"),
            openid=open_id,
            is_login=1,
            is_make=0,
            is_payment=0,
            date_stamp=datetime.datetime.now()
        )
    return JsonResponse({"code": "OK", "msg": "yuanwei."})


def get_order_id(request):
    """获取订单编号 orderid"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.GET.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 随机生成一个 orderId
    order_id = f"LZYJ{time.strftime('%Y%m%d%H%M%S')}{secret_key}"
    return JsonResponse({"code": "OK", "orderId": order_id})


def pay_status(request):
    """修改视频支付状态"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.GET.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 查找视频
    video = VideoInfo.objects.filter(openid=open_id, secret_key=secret_key)

    # 计数
    CountInfo.objects.filter(date=time.strftime("%Y-%m-%d"), openid=open_id).update(is_payment=1)

    if video:
        # 存在则修改 user_code
        video.update(pay_status=1)
        return JsonResponse({"code": "OK"})
    else:
        return JsonResponse({"code": "Failed"})


def get_pre_pay(request):
    """支付金钱接口"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.GET.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 获取参数 orderId
    out_trade_no = request.GET.get("orderId")
    if not out_trade_no:
        return JsonResponse({"code": "Failed", "msg": "No upload orderId parameters."})

    # 获取参数 description
    description = request.GET.get("description")
    if not description:
        return JsonResponse({"code": "Failed", "msg": "No upload description parameters."})

    # 获取参数 amount
    amount = request.GET.get("amount")
    if not amount:
        return JsonResponse({"code": "Failed", "msg": "No upload amount parameters."})

    payer = {'openid': open_id}
    # 查找视频
    video = VideoInfo.objects.filter(openid=open_id, secret_key=secret_key).first()
    if video:
        video_type = video.video_type
        money = int(AmountInfo.objects.filter(amount_name=video_type).first().amount_price)
        amount = money * 100

        # update money
        VideoInfo.objects.filter(openid=open_id, secret_key=secret_key).update(pay_amounts=money)

        # 统一下单
        code, msg = wxpay.pay(
            description=description,
            payer=payer,
            out_trade_no=out_trade_no,
            amount={'total': int(amount)}
        )
        prepay_id_ = json.loads(msg)
        prepay_id = prepay_id_["prepay_id"]
        if code:
            # 签名，使用字段appId、timeStamp、nonceStr、package计算得出的签名值
            timeStamp = str(int(time.time()))
            nonceStr = get_random_key(32)
            package = f'prepay_id={prepay_id}'
            data = [APPID, timeStamp, nonceStr, package]
            paySign = wxpay.sign(data)
            return_data = {
                "code": "OK",
                "timeStamp": timeStamp,
                "paySign": paySign,
                "nonceStr": nonceStr,
                "package": package,
                "money": money
            }
            return JsonResponse(return_data)
        else:
            return JsonResponse({"code": "Failed", "msg": "pay generate failed."})
    else:
        return JsonResponse({"code": "Failed", "msg": "No video found."})


def get_secret_key(request):
    """获取操作的 key 并生成操作目录"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取当前类型：抠图、串接、AI
    template_type = request.GET.get("type")
    if not template_type:
        return JsonResponse({"code": "Failed", "msg": "No upload type parameters."})

    UserInfo.objects.filter(openid=open_id).update(update_time=time.strftime("%Y-%m-%d %H:%M:%S"))

    # 生成secret_key
    secret_key = get_random_key()
    # 当前时间目录,没有则创建
    now_time = time.strftime("%Y-%m-%d")
    video_time_path = os.path.join(video_root_path, now_time)
    if not os.path.exists(video_time_path):
        os.mkdir(video_time_path)
    # 当前时间下的个人用户目录，没有则创建
    video_time_user_path = os.path.join(video_time_path, open_id)
    if not os.path.exists(video_time_user_path):
        os.mkdir(video_time_user_path)
    # 创建当次操作的目录
    secret_key_path = os.path.join(video_time_user_path, secret_key)
    os.mkdir(secret_key_path)
    # 当前用户目录下创建串接所需要的目录
    os.mkdir(os.path.join(secret_key_path, "upload"))
    os.mkdir(os.path.join(secret_key_path, "save"))
    return_dict = {"code": "OK", "secretKey": secret_key}
    return JsonResponse(return_dict)


def query_status(request):
    """小红点：查看我的视频状态是否有未读视频"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 根据生成时间倒序排序
    video_list = VideoInfo.objects.filter(openid=open_id, is_del=0).order_by("-generate_stamp")
    # video_list = Video.query.filter_by(openId=open_id).order_by(Video.generateStamp.desc())
    state_list = [i.read_state for i in video_list]
    if 1 in state_list:
        return JsonResponse({"videoStatus": 1})
    else:
        return JsonResponse({"videoStatus": 0})


def query_my_video(request):
    """读取我的视频列表并修改读取状态"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 根据生成时间倒序排序
    video_list = VideoInfo.objects.filter(openid=open_id, is_del=0).order_by("-generate_stamp")

    return_list = []
    for i in video_list:
        return_list.append({
            "imgSrc": i.picture_url,
            "videoSrc": i.video_url,
            "CreateDate": i.generate_time,
            "ValidDate": i.invalid_time,
            "secretKey": i.secret_key,
            "payStatus": i.pay_status
        })

        # 修改每一个视频的 read_state
        VideoInfo.objects.filter(openid=open_id, secret_key=i.secret_key).update(read_state=0)
        # i.update(read_state=0)
    return JsonResponse(return_list, safe=False)


def subscribe(request):
    """生成有点慢,我先干点别的"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.GET.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 启动celery
    tasks.subscribe_status.delay(open_id, secret_key)
    return JsonResponse({"code": "OK"})


def process(request):
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.GET.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 获取参数 template
    template = request.GET.get("template")
    if not template:
        return JsonResponse({"code": "Failed", "msg": "No upload template parameters."})

    # 获取参数 type
    template_type = request.GET.get("type")
    if not template_type:
        return JsonResponse({"code": "Failed", "msg": "No upload type parameters."})
    if template_type == "matting":
        type_ = ""
    elif template_type in ["ai_horizontal", "ai_vertical", "editing_horizontal", "editing_vertical"]:
        type_ = template_type.split("_")[1]
        template_type = template_type.split("_")[0]
    else:
        return JsonResponse({"code": "Failed", "msg": "type parameter error."})

    # 当前时间目录
    video_time_path = os.path.join(video_root_path, time.strftime("%Y-%m-%d"))
    # 当前用户目录
    video_time_user_path = os.path.join(video_time_path, open_id)
    # 当前用户下操作目录
    secret_key_path = os.path.join(video_time_user_path, secret_key)

    if template_type == "matting":
        task = tasks.matting.delay(secret_key_path, template)
        video_type = "同款生成"
    elif template_type == "editing" and type_ in ["horizontal", "vertical"]:
        video_type = "剪辑串编"
        task = tasks.editing.delay(secret_key_path, template, secret_key, type_)
    elif template_type == "ai" and type_ in ["horizontal", "vertical"]:
        video_type = "AI融合剪辑"
        if type_ == "horizontal":
            task = tasks.horizontal_screen.delay(secret_key_path)
        else:  # type_ == "vertical"
            task = tasks.vertical_screen.delay(secret_key_path)
    else:
        return JsonResponse({"code": "Failed", "msg": "type parameter error."})

    while True:
        if not task:
            return JsonResponse({"code": "Failed", "msg": "video generate failed."})

        if task.state == "PENDING":
            pass
        elif task.state == 'SUCCESS':
            if not task.info:
                return JsonResponse({"code": "Failed", "msg": "video generate failed."})
            else:
                video_path = task.info

            # pictureUrl
            if template_type == "matting":
                c_time = 1
            else:
                c_time = random.randint(0, 20)
            img_path = os.path.join(secret_key_path, f"save/screenshot.png")
            cmd1 = f"{ffmpeg_path} -i {video_path} -ss 00:00:{c_time} -vframes 1 -vf scale=112:101 -y {img_path} -hide_banner -loglevel error"
            result = subprocess.call(cmd1, shell=True)
            if result != 0:
                img_path = os.path.join("image/temp", random.choice(os.listdir("image/temp")))
            picture_url = f"https://{request.META['HTTP_HOST']}/{img_path}/".replace('\\', '/')
            # videomysql
            generate_time = time.strftime("%Y-%m-%d %H:%M:%S")
            invalid_time = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")

            # 创建
            VideoInfo.objects.create(
                openid=open_id,
                picture_url=picture_url,
                video_url=f"https://{request.META['HTTP_HOST']}/{video_path}/".replace('\\', '/'),
                generate_time=generate_time,
                invalid_time=invalid_time,
                video_type=video_type,
                generate_stamp=datetime.datetime.today(),
                secret_key=secret_key,
            )
            # 计数
            CountInfo.objects.filter(date=time.strftime("%Y-%m-%d"), openid=open_id).update(is_make=1)
            break
        elif task.state == 'FAILURE':
            video_path = False
            break
    if not video_path:
        return JsonResponse({"code": "Failed", "msg": "video generate failed."})
    return JsonResponse(
        {"code": "OK", "videoPath": f"https://{request.META['HTTP_HOST']}/{video_path}/".replace('\\', '/')})


def videos_upload(request):
    # 获取参数 openId
    open_id = request.POST.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.POST.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 获取参数 videoName
    video_name_ = request.POST.get("videoName")
    if not video_name_:
        return JsonResponse({"code": "Failed", "msg": "No upload videoName parameters."})

    # 当前模板
    template = request.POST.get("template")
    template_type = request.POST.get("type")
    platform = request.POST.get("platform")

    video_m_name = video_name_[-19:]
    video_name = f"{video_m_name[:15]}_{video_m_name[15:]}"

    # 当前时间目录
    video_time_path = os.path.join(video_root_path, time.strftime("%Y-%m-%d"))
    # 当前用户目录
    video_time_user_path = os.path.join(video_time_path, open_id)
    # 当前用户下操作目录
    secret_key_path = os.path.join(video_time_user_path, secret_key)
    # 上传视频的目录
    video_upload_path = os.path.join(secret_key_path, "upload")
    # 上传视频的地址
    video_path = os.path.join(video_upload_path, video_name)
    video_m_path = os.path.join(video_upload_path, video_m_name)

    # 获取上传的文件,如果没有文件,则默认为None
    File = request.FILES.get("file", None)
    if File is None:
        return JsonResponse({"code": "Failed", "msg": "No files for upload."})
    else:
        # 打开特定的文件进行二进制的写操作
        with open(video_path, 'wb+') as f:
            # 分块写入文件
            for chunk in File.chunks():
                f.write(chunk)
    if template_type in ["ai_horizontal", "ai_vertical"]:
        tasks.ai_upload.delay(template_type, video_path)
    elif template_type in ["editing_horizontal", "editing_vertical"]:
        tasks.editing_upload.delay(video_path, template_type, video_m_path, video_upload_path)
    else:
        tasks.matting_upload.delay(template, template_type, platform, video_path, video_m_path, video_upload_path)
    return JsonResponse({"code": "OK"})


def videos_clear(request):
    """清空视频文件夹"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.GET.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 当前时间目录
    video_time_path = os.path.join(video_root_path, time.strftime("%Y-%m-%d"))
    # 当前用户目录
    video_time_user_path = os.path.join(video_time_path, open_id)
    # 当前用户下操作目录
    secret_key_path = os.path.join(video_time_user_path, secret_key)
    # 上传视频的目录
    video_upload_path = os.path.join(secret_key_path, "upload")
    video_save_path = os.path.join(secret_key_path, "save")
    # 删除视频
    video_list = os.listdir(video_upload_path)
    save_list = os.listdir(video_save_path)
    redis_conn.delete(f'{secret_key_path}##pic_num')
    try:
        for _ in video_list:
            os.remove(os.path.join(video_upload_path, _))
        for _ in save_list:
            os.remove(os.path.join(video_save_path, _))
        return JsonResponse({"code": "OK"})
    except:
        return JsonResponse({"code": "Failed", "msg": "video delete failed."})


def videos_remove(request):
    """个人视频展示界面删除视频"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.GET.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 删除mysql
    VideoInfo.objects.filter(openid=open_id, secret_key=secret_key).update(is_del=1)

    # # 当前时间目录
    # video_time_path = os.path.join(video_root_path, time.strftime("%Y-%m-%d"))
    # # 当前用户目录
    # video_time_user_path = os.path.join(video_time_path, open_id)
    # # 当前用户下操作目录
    # secret_key_path = os.path.join(video_time_user_path, secret_key)
    # # 删除视频
    # try:
    #     shutil.rmtree(secret_key_path)
    #     return JsonResponse({"code": "OK"})
    # except FileNotFoundError:
    #     return JsonResponse({"code": "Failed", "msg": "video delete failed."})
    return JsonResponse({"code": "OK"})


def videos_delete(request):
    """视频上传处 删除一个视频"""
    # 获取参数 openId
    open_id = request.GET.get("openId")
    if not open_id:
        return JsonResponse({"code": "Failed", "msg": "No upload openId parameters."})

    # 获取参数 secret_key
    secret_key = request.GET.get("secretKey")
    if not secret_key:
        return JsonResponse({"code": "Failed", "msg": "No upload secretKey parameters."})

    # 获取参数 secret_key
    video_name_ = request.GET.get("videoName")
    if not video_name_:
        return JsonResponse({"code": "Failed", "msg": "No upload videoName parameters."})

    video_name = video_name_[-19:]

    # 当前时间目录
    video_time_path = os.path.join(video_root_path, time.strftime("%Y-%m-%d"))
    # 当前用户目录
    video_time_user_path = os.path.join(video_time_path, open_id)
    # 当前用户下操作目录
    secret_key_path = os.path.join(video_time_user_path, secret_key)
    # 上传视频的目录
    video_upload_path = os.path.join(secret_key_path, "upload")
    # 上传视频的地址
    video_path = os.path.join(video_upload_path, video_name)

    json_upload_path = os.path.join(video_upload_path, "information.json")
    if os.path.exists(json_upload_path):
        with open(json_upload_path, encoding="utf-8") as json_obj:
            information_list = json.load(json_obj)

        index = -1
        for _ in range(len(information_list)):
            if information_list[_]["video_name"] == video_path:
                index = _
                break
        try:
            del information_list[index]
        except:
            return JsonResponse({"code": "Failed", "msg": "video delete failed."})
        with open(json_upload_path, 'w', encoding='utf-8') as f:
            json.dump(information_list, f)
    # 删除视频
    if os.path.exists(video_path):
        try:
            os.remove(video_path)
            return JsonResponse({"code": "OK"})
        except:
            return JsonResponse({"code": "Failed", "msg": "video delete failed."})
    else:
        if os.path.exists(os.path.splitext(video_path)[0] + '_.mp4'):
            try:
                os.remove(os.path.splitext(video_path)[0] + '_.json')
                return JsonResponse({"code": "OK"})
            except:
                return JsonResponse({"code": "Failed", "msg": "video delete failed."})
        return JsonResponse({"code": "Failed", "msg": "video not exist."})


def stream(request, path, suffix):
    """将文件以流媒体的方式响应"""
    path = f"{BASE_DIR}/{path}.{suffix}".replace('\\', '/')
    size = os.path.getsize(path)
    content_type, encoding = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
    resp['Content-Length'] = str(size)
    resp['Accept-Ranges'] = 'bytes'
    return resp
