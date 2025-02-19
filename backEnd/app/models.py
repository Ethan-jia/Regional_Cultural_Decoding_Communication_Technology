from django.db import models


# Create your models here.

class AmountInfo(models.Model):
    """ 价格表 """
    amount_name = models.CharField(verbose_name="商品名称", max_length=20)
    amount_price = models.IntegerField(verbose_name="商品价格")


class PhotoInfo(models.Model):
    photo_name = models.CharField(verbose_name="图片名称", max_length=50)
    photo_url = models.CharField(verbose_name="图片地址", max_length=500)
    is_hide = models.IntegerField(default=0, verbose_name="是否隐藏")  # 0 未隐藏 1 隐藏
    # 不跳转 none  内部H5 internal 外部小程序 external
    type = models.CharField(default="none", verbose_name="跳转类型", max_length=10)
    app_id = models.CharField(default="", verbose_name="appid", max_length=100)
    path = models.CharField(default="", verbose_name="跳转path", max_length=500)
    url = models.CharField(default="", verbose_name="跳转url", max_length=500)
    # develop 开发版 trial 体验版 release 正式版
    env_version = models.CharField(default="", verbose_name="图片地址", max_length=10)


class CountInfo(models.Model):
    date = models.CharField(max_length=15, verbose_name="日期")
    year = models.CharField(max_length=5, verbose_name="年")
    openid = models.CharField(max_length=40, verbose_name="用户id")
    is_login = models.IntegerField(default=0, verbose_name="是否登录")
    is_make = models.IntegerField(default=0, verbose_name="是否生成视频")
    is_payment = models.IntegerField(default=0, verbose_name="是否付款")
    date_stamp = models.DateTimeField(verbose_name="日期时间戳")
    insert_time = models.DateTimeField(auto_now=True, verbose_name="插入数据时间")


class UserInfo(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="序号")
    nickname = models.CharField(max_length=255, blank=True, null=True, verbose_name="用户昵称")
    avatar_url = models.CharField(max_length=2550, blank=True, null=True, verbose_name="用户头像")
    gender = models.IntegerField(blank=True, null=True, verbose_name="用户性别")  # 0 未知 1 男性 2 女性
    country = models.CharField(max_length=255, blank=True, null=True, verbose_name="用户所在国家")
    province = models.CharField(max_length=255, blank=True, null=True, verbose_name="用户所在省份")
    city = models.CharField(max_length=255, blank=True, null=True, verbose_name="用户所在城市")
    # en 英文 zh_CN 简体中文 zh_TW 繁体中文
    language = models.CharField(max_length=255, blank=True, null=True, verbose_name="所用的语言")
    insert_time = models.DateTimeField(auto_now=True, verbose_name="插入数据时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新数据时间")
    openid = models.CharField(max_length=255, verbose_name="用户id")
    user_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="临时key")
    video_num = models.IntegerField(default=0, verbose_name="视频条数")
    pay_num = models.IntegerField(default=0, verbose_name="支付金额")


class VideoInfo(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name="序号")
    openid = models.CharField(max_length=255, verbose_name="用户id")
    picture_url = models.CharField(max_length=2550, blank=True, null=True, verbose_name="视频图像地址")
    video_url = models.CharField(max_length=2550, blank=True, null=True, verbose_name="视频地址")
    generate_time = models.CharField(max_length=20, blank=True, null=True, verbose_name="视频生成时间")
    invalid_time = models.CharField(max_length=20, blank=True, null=True, verbose_name="视频失效时间")
    read_state = models.IntegerField(default=1, verbose_name="视频状态")  # 0 已读 1 未读
    insert_time = models.DateTimeField(auto_now=True, verbose_name="插入数据时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新数据时间")
    secret_key = models.CharField(max_length=20, blank=True, null=True, verbose_name="秘钥")
    generate_stamp = models.DateTimeField(blank=True, null=True, verbose_name="视频生成时间戳")
    video_type = models.CharField(max_length=10, blank=True, null=True, verbose_name="视频类型")
    pay_status = models.IntegerField(default=0, verbose_name="视频支付状态")  # 0 未支付 1 已支付
    pay_amounts = models.IntegerField(default=0, verbose_name="视频支付金额")
    is_del = models.IntegerField(default=0, verbose_name="视频支付状态")  # 0 未删除 1 已删除
