import os
import datetime

from app import models
from api.utils.pagination import Pagination

from dateutil import relativedelta
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.db.models.aggregates import Sum
from api.utils.form import AmountModelForm


def login_h(request):
    if request.method == "GET":
        return render(request, "login.html")
    else:
        username = request.POST.get("user")
        password = request.POST.get("pwd")

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
        return redirect("/user/list/")


@login_required
def user_list(request):
    """ 用户列表"""
    res = models.PhotoInfo.objects.filter()
    if not res:
        try:
            template_path = os.path.join("image", "carousel")
            template_list = os.listdir(template_path)
            template_list.sort()
            for i in range(len(template_list)):
                models.PhotoInfo.objects.create(
                    photo_name=template_list[i],
                    photo_url=f"http://{request.META['HTTP_HOST']}/image/carousel/{template_list[i]}/".replace('\\',
                                                                                                               '/')
                )
        except:
            pass

    query_dict = {}
    search_data = request.GET.get("q", "")
    if search_data:
        query_dict["nickname__contains"] = search_data

    queryset = models.UserInfo.objects.filter(**query_dict)

    for i in queryset:
        video_num = models.VideoInfo.objects.filter(openid=i.openid, is_del=0).count()
        pay_num = models.VideoInfo.objects.filter(openid=i.openid, is_del=0).aggregate(nums=Sum('pay_amounts'))["nums"]
        if not pay_num:
            pay_num = 0
        models.UserInfo.objects.filter(openid=i.openid).update(video_num=video_num, pay_num=pay_num)

    queryset = models.UserInfo.objects.filter(**query_dict)
    page_obj = Pagination(request, queryset)
    context = {
        "search_data": search_data,
        "queryset": page_obj.page_queryset,
        "page_string": page_obj.html()
    }
    return render(request, "user_list.html", context)


@login_required
def video_list(request, openid):
    """ 用户视频列表 """
    return render(request, "video_list.html", {"openid": openid})


@login_required
def video_list_table(request, openid):
    """ 用户视频列表 """
    page = int(request.GET.get("page", 0))
    page_size = int(request.GET.get("limit", 0))
    start = (page - 1) * page_size  # 计算显示页数的起始值
    end = page * page_size  # 计算显示页数的起始值
    queryset = models.VideoInfo.objects.filter(openid=openid, is_del=0)[start:end]
    return_dict = {
        "code": 0,
        "msg": "",
        "count": models.VideoInfo.objects.filter(openid=openid, is_del=0).count(),
    }
    data = []
    index = 1
    for i in queryset:
        res = {
            "id": index,
            "video_url": i.video_url,
            "generate_stamp": i.generate_stamp.strftime("%Y-%m-%d %H:%M:%S"),
            "video_type": i.video_type,
            "pay_status": "已支付" if i.pay_status else "未支付",
            "pay_amounts": i.pay_amounts,
        }
        data.append(res)
        index += 1
    return_dict["data"] = data
    return JsonResponse(return_dict)


def users_create(query_type, query_time_stamp):
    """
    query_type:
                要查询的类型： year / month / day  (str)
                year 按当前年: 展示当年每个月数据
                month 按当前月: 展示当月每个日数据
                day 按当前日: 展示当日每个时段数据

    query_time_stamp：
                要查询的时间戳： (timestamp)

    """
    # 现在的时间信息
    now_time_stamp = datetime.datetime.now()
    now_year_str = now_time_stamp.strftime("%Y")
    now_month_str = now_time_stamp.strftime("%m")
    now_day_str = now_time_stamp.strftime("%d")
    now_hour_str = now_time_stamp.strftime("%H")

    # 要查询的时间信息
    query_year_str = query_time_stamp.strftime("%Y")
    query_month_str = query_time_stamp.strftime("%m")
    query_day_str = query_time_stamp.strftime("%d")

    # 查询次数（循环次数）
    if query_type == "year":
        if now_year_str == query_year_str:
            cycle_num = int(now_month_str)
        else:
            cycle_num = 12
    elif query_type == "month":
        if now_year_str == query_year_str and now_month_str == query_month_str:
            cycle_num = int(now_day_str)
        else:
            split_joint_time_stamp = datetime.datetime.strptime(f"{query_year_str}-{query_month_str}-1", "%Y-%m-%d")
            res_time_stamp = split_joint_time_stamp + relativedelta.relativedelta(
                months=1) - relativedelta.relativedelta(days=1)
            cycle_num = int(res_time_stamp.strftime("%d"))
    else:
        if now_year_str == query_year_str and now_month_str == query_month_str and now_day_str == query_day_str:
            cycle_num = int(now_hour_str)
        else:
            cycle_num = 24

    # 拼接查询的时间戳
    if query_type == "year":
        query_time_str = f"{query_year_str}-1-1"
        query_time_stamp = datetime.datetime.strptime(query_time_str, "%Y-%m-%d")
    elif query_type == "month":
        query_time_str = f"{query_year_str}-{query_month_str}-1"
        query_time_stamp = datetime.datetime.strptime(query_time_str, "%Y-%m-%d")
    else:
        query_time_str = f"{query_year_str}-{query_month_str}-{query_day_str} 0"
        query_time_stamp = datetime.datetime.strptime(query_time_str, "%Y-%m-%d %H")

    # 准备返回数据列表
    type1_data = []
    type2_data = []
    type3_data = []
    data_list1 = []
    data_list2 = []
    data_list3 = []
    x_axis = []

    # 查询数据
    for i in range(cycle_num):
        if query_type == "year":
            res_time_stamp = query_time_stamp + relativedelta.relativedelta(months=i)
            res_year = res_time_stamp.strftime("%Y")
            res_month = res_time_stamp.strftime("%m")
            type1_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "is_login": 1
            }
            type2_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "is_make": 1
            }
            type3_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "is_payment": 1
            }
            type4_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "pay_status": 1
            }
            x_axis.append(res_time_stamp.strftime("%Y-%m"))
        elif query_type == "month":
            res_time_stamp = query_time_stamp + relativedelta.relativedelta(days=i)
            res_year = res_time_stamp.strftime("%Y")
            res_month = res_time_stamp.strftime("%m")
            res_day = res_time_stamp.strftime("%d")
            type1_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "date_stamp__day": res_day,
                "is_login": 1
            }
            type2_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "date_stamp__day": res_day,
                "is_make": 1
            }
            type3_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "date_stamp__day": res_day,
                "is_payment": 1
            }
            type4_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "generate_stamp__day": res_day,
                "pay_status": 1
            }
            x_axis.append(res_time_stamp.strftime("%Y-%m-%d"))
        else:
            res_time_stamp = query_time_stamp + relativedelta.relativedelta(hours=i)
            res_year = res_time_stamp.strftime("%Y")
            res_month = res_time_stamp.strftime("%m")
            res_day = res_time_stamp.strftime("%d")

            start_time = query_time_stamp + datetime.timedelta(hours=i)
            end_time = query_time_stamp + datetime.timedelta(hours=i + 1)
            type1_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "date_stamp__day": res_day,
                "date_stamp__range": (start_time, end_time),
                "is_login": 1
            }
            type2_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "date_stamp__day": res_day,
                "date_stamp__range": (start_time, end_time),
                "is_make": 1
            }
            type3_query_dict = {
                "date_stamp__year": res_year,
                "date_stamp__month": res_month,
                "date_stamp__day": res_day,
                "date_stamp__range": (start_time, end_time),
                "is_payment": 1
            }
            type4_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "generate_stamp__day": res_day,
                "generate_stamp__range": (start_time, end_time),
                "pay_status": 1
            }
            x_axis.append(f'{start_time.strftime("%H")}时 ~ {end_time.strftime("%H")}时')

        type1_video_list = models.CountInfo.objects.filter(**type1_query_dict)
        type2_video_list = models.CountInfo.objects.filter(**type2_query_dict)
        type3_video_list = models.CountInfo.objects.filter(**type3_query_dict)

        data_list1.append(len(type1_video_list))
        data_list2.append(len(type2_video_list))
        data_list3.append(len(type3_video_list))

        if len(type1_video_list) == 0:
            type2_num = 0
            type3_num = 0
        else:
            type2_num = int(len(type2_video_list) / len(type1_video_list) * 100)
            type3_num = int(len(type3_video_list) / len(type1_video_list) * 100)
        type1_data.append(type2_num)
        type2_data.append(type3_num)
        type3_data.append(models.VideoInfo.objects.filter(**type4_query_dict).count())

    # 如果是按天查询并且是当天加一个当前小时的数据
    if query_type == "day" and now_year_str == query_year_str and now_month_str == query_month_str and now_day_str == query_day_str:
        n_time = query_time_stamp + datetime.timedelta(hours=cycle_num)
        type1_query_dict = {
            "date_stamp__year": query_year_str,
            "date_stamp__month": query_month_str,
            "date_stamp__day": query_day_str,
            "date_stamp__gt": n_time,
            "is_login": 1
        }
        type2_query_dict = {
            "date_stamp__year": query_year_str,
            "date_stamp__month": query_month_str,
            "date_stamp__day": query_day_str,
            "date_stamp__gt": n_time,
            "is_make": 1
        }
        type3_query_dict = {
            "date_stamp__year": query_year_str,
            "date_stamp__month": query_month_str,
            "date_stamp__day": query_day_str,
            "date_stamp__gt": n_time,
            "is_payment": 1
        }
        type4_query_dict = {
            "generate_stamp__year": query_year_str,
            "generate_stamp__month": query_month_str,
            "generate_stamp__day": query_day_str,
            "generate_stamp__gt": n_time,
            "pay_status": 1
        }
        x_axis.append(f'{n_time.strftime("%H")}时 ~ 此时')

        type1_video_list = models.CountInfo.objects.filter(**type1_query_dict)
        type2_video_list = models.CountInfo.objects.filter(**type2_query_dict)
        type3_video_list = models.CountInfo.objects.filter(**type3_query_dict)

        data_list1.append(len(type1_video_list))
        data_list2.append(len(type2_video_list))
        data_list3.append(len(type3_video_list))

        if len(type1_video_list) == 0:
            type2_num = 0
            type3_num = 0
        else:
            type2_num = int(len(type2_video_list) / len(type1_video_list) * 100)
            type3_num = int(len(type3_video_list) / len(type1_video_list) * 100)
        type1_data.append(type2_num)
        type2_data.append(type3_num)
        type3_data.append(models.VideoInfo.objects.filter(**type4_query_dict).count())

    return type1_data, type2_data, type3_data, x_axis, data_list1, data_list2, data_list3


@login_required
def users_list(request):
    """ 用户图表页面 """
    # 现在的时间信息
    now_time_stamp = datetime.datetime.now()
    now_year_str = now_time_stamp.strftime("%Y")
    now_month_str = now_time_stamp.strftime("%m")
    now_day_str = now_time_stamp.strftime("%d")

    # 获取到的时间
    query_type = request.GET.get("query_type")
    query_year = request.GET.get("query_year")
    query_month = request.GET.get("query_month")
    query_day = request.GET.get("query_day")

    # 如果没获取到给默认值
    if query_type is None:
        query_type = "day"
    if query_year is None:
        query_year = now_year_str
    if query_month is None:
        query_month = now_month_str
    if query_day is None:
        query_day = now_day_str

    # 准备按年统计下拉菜单
    year_list = [i["year"] for i in models.CountInfo.objects.values("year").annotate()]
    year_list = list(set(year_list))
    year_list.sort()

    # 准备按月统计下拉菜单
    if query_year == now_year_str:
        month_list = [str(j + 1) for j in range(int(now_month_str))]
    else:
        month_list = [str(j + 1) for j in range(12)]

    # 准备按日统计下拉菜单
    if query_year == now_year_str and query_month == now_month_str:
        day_list = [str(j + 1) for j in range(int(now_day_str))]
    else:
        split_joint_time_stamp = datetime.datetime.strptime(f"{query_year}-{query_month}-1", "%Y-%m-%d")
        res_time_stamp = split_joint_time_stamp + relativedelta.relativedelta(
            months=1) - relativedelta.relativedelta(days=1)
        day_list = [str(j + 1) for j in range(int(res_time_stamp.strftime("%d")))]

    context = {
        "query_type": query_type,
        "query_year": query_year,
        "query_month": query_month,
        "query_day": query_day,
        "year_list": year_list,
        "month_list": month_list,
        "day_list": day_list
    }
    return render(request, "users_list.html", context)


@login_required
def users_line(request):
    """ 绘制用户图表折线图 """
    # 接收的信息
    query_type = request.GET.get("query_type")
    query_year = request.GET.get("query_year")
    query_month = request.GET.get("query_month")
    query_day = request.GET.get("query_day")

    # 现在的时间信息
    now_time_stamp = datetime.datetime.now()
    now_year_str = now_time_stamp.strftime("%Y")
    now_month_str = now_time_stamp.strftime("%m")
    now_day_str = now_time_stamp.strftime("%d")

    # 接收 null 时候给默认值
    if not query_type:
        query_type = "day"
    if not query_year:
        query_year = now_year_str
    if not query_month:
        query_month = now_month_str
    if not query_day:
        query_day = now_day_str

    # 要查询的时间
    query_time_stamp = datetime.datetime.strptime(f"{query_year}-{query_month}-{query_day}", "%Y-%m-%d")

    # 获取数据
    type1_data, type2_data, type3_data, x_axis, data_list1, data_list2, data_list3 = users_create(query_type,
                                                                                                  query_time_stamp)

    # 拼接返回数据
    legend = ['用户活跃率', '用户下载率']
    series_list = [
        {
            "name": '用户活跃率',
            "type": 'line',
            "data": type1_data
        },
        {
            "name": '用户下载率',
            "type": 'line',
            "data": type2_data
        }
    ]
    result = {
        "status": True,
        "data": {
            'legend': legend,
            'series_list': series_list,
            'x_axis': x_axis,
        }
    }
    return JsonResponse(result)


@login_required
def users_table(request):
    """ 绘制用户图表表格 """
    # 接收的信息
    query_type = request.GET.get("query_type")
    query_year = request.GET.get("query_year")
    query_month = request.GET.get("query_month")
    query_day = request.GET.get("query_day")

    # 现在的时间信息
    now_time_stamp = datetime.datetime.now()
    now_year_str = now_time_stamp.strftime("%Y")
    now_month_str = now_time_stamp.strftime("%m")
    now_day_str = now_time_stamp.strftime("%d")

    # 接收 null 时候给默认值
    if query_type == "null":
        query_type = "day"
    if query_year == "null":
        query_year = now_year_str
    if query_month == "null":
        query_month = now_month_str
    if query_day == "null":
        query_day = now_day_str

    # 要查询的时间
    query_time_stamp = datetime.datetime.strptime(f"{query_year}-{query_month}-{query_day}", "%Y-%m-%d")

    # 获取数据
    type1_data, type2_data, type3_data, x_axis, data_list1, data_list2, data_list3 = users_create(query_type,
                                                                                                  query_time_stamp)

    # 拼接返回数据
    return_dict = {
        "code": 0,
        "msg": "",
        "count": len(type1_data),
        "data": [
            {
                "date": x_axis[i],
                "data1": data_list1[i],
                "data2": data_list2[i],
                "data3": data_list3[i],
                "data4": type3_data[i],
                "rate1": type1_data[i],
                "rate2": type2_data[i],
            } for i in range(len(type1_data))
        ]
    }
    return JsonResponse(return_dict)


@login_required
def amount_list(request):
    """ 价格页面 """
    queryset = models.AmountInfo.objects.all()
    page_obj = Pagination(request, queryset)
    context = {
        "queryset": page_obj.page_queryset,
        "page_string": page_obj.html()
    }
    return render(request, "amount_list.html", context)


@login_required
def amount_edit(request, uid):
    """ 修改用户 """
    # 查询要修改的对象
    obj = models.AmountInfo.objects.filter(id=uid).first()

    if request.method == "GET":
        form = AmountModelForm(instance=obj)
        return render(request, "amount_edit.html", {"form": form})

    form = AmountModelForm(data=request.POST, instance=obj)
    # 如果验证成功
    if form.is_valid():
        # 保存到数据库
        form.save()
        return redirect("/amount/list/")

    return render(request, "amount_edit.html", {"form": form})


@login_required
def photo_list(request):
    template_path = os.path.join("image", "carousel")
    if request.method == "POST":
        photo_obj = request.FILES.get("photo", None)
        template_list = os.listdir(template_path)
        res_list = [int(i.split(".")[0]) for i in template_list]
        max_num = max(res_list)
        try:
            photo_name = request.FILES.get("photo").name
            photo_type = photo_name.split(".")[-1]
            photo_name = f"{max_num + 1}.{photo_type}"
            photo_path = os.path.join(template_path, photo_name)
            # 打开特定的文件进行二进制的写操作
            with open(photo_path, 'wb+') as f:
                # 分块写入文件
                for chunk in photo_obj.chunks():
                    f.write(chunk)
            models.PhotoInfo.objects.create(
                photo_name=photo_name,
                photo_url=f"http://{request.META['HTTP_HOST']}/{photo_path}/".replace('\\', '/')
            )
            return redirect("/photo/list/")
        except:
            pass

    queryset = models.PhotoInfo.objects.all()
    return render(request, "photo_list.html", {"queryset": queryset})


@login_required
def photo_delete(request, name):
    template_path = os.path.join("image", "carousel")
    photo_path = os.path.join(template_path, name)
    os.remove(photo_path)
    models.PhotoInfo.objects.filter(photo_name=name).delete()
    return redirect("/photo/list/")


@login_required
def photo_hide(request, name):
    obj = models.PhotoInfo.objects.filter(photo_name=name).first()
    res = obj.is_hide
    if res:
        is_hide = 0
    else:
        is_hide = 1
    models.PhotoInfo.objects.filter(photo_name=name).update(is_hide=is_hide)
    return redirect("/photo/list/")


@login_required
def photo_goto(request, name):
    if request.method == "POST":
        type_ = request.POST.get("type")
        path = request.POST.get("path")
        url = request.POST.get("url")
        appid = request.POST.get("appid")
        env_version = request.POST.get("env_version")
        if type_ == "none":
            models.PhotoInfo.objects.filter(photo_name=name).update(
                type="none",
                app_id="",
                env_version="",
                path="",
                url=""
            )
        elif type_ == "internal":
            models.PhotoInfo.objects.filter(photo_name=name).update(
                type="internal",
                app_id="",
                env_version="",
                path="",
                url=url
            )
        elif type_ == "external":
            models.PhotoInfo.objects.filter(photo_name=name).update(
                type="external",
                app_id=appid,
                env_version=env_version,
                path=path,
                url=""
            )
        else:
            return redirect("/photo/list/")
        return redirect("/photo/list/")
    obj = models.PhotoInfo.objects.filter(photo_name=name).first()
    return render(request, "photo_goto.html", {"obj": obj})


def chart_create(query_type, query_time_stamp):
    """
    query_type:
                要查询的类型： year / month / day  (str)
                year 按当前年: 展示当年每个月数据
                month 按当前月: 展示当月每个日数据
                day 按当前日: 展示当日每个时段数据

    query_time_stamp：
                要查询的时间戳： (timestamp)

    """
    # 现在的时间信息
    now_time_stamp = datetime.datetime.now()
    now_year_str = now_time_stamp.strftime("%Y")
    now_month_str = now_time_stamp.strftime("%m")
    now_day_str = now_time_stamp.strftime("%d")
    now_hour_str = now_time_stamp.strftime("%H")

    # 要查询的时间信息
    query_year_str = query_time_stamp.strftime("%Y")
    query_month_str = query_time_stamp.strftime("%m")
    query_day_str = query_time_stamp.strftime("%d")

    # 查询次数（循环次数）
    if query_type == "year":
        if now_year_str == query_year_str:
            cycle_num = int(now_month_str)
        else:
            cycle_num = 12
    elif query_type == "month":
        if now_year_str == query_year_str and now_month_str == query_month_str:
            cycle_num = int(now_day_str)
        else:
            split_joint_time_stamp = datetime.datetime.strptime(f"{query_year_str}-{query_month_str}-1", "%Y-%m-%d")
            res_time_stamp = split_joint_time_stamp + relativedelta.relativedelta(
                months=1) - relativedelta.relativedelta(days=1)
            cycle_num = int(res_time_stamp.strftime("%d"))
    else:
        if now_year_str == query_year_str and now_month_str == query_month_str and now_day_str == query_day_str:
            cycle_num = int(now_hour_str)
        else:
            cycle_num = 24

    # 拼接查询的时间戳
    if query_type == "year":
        query_time_str = f"{query_year_str}-1-1"
        query_time_stamp = datetime.datetime.strptime(query_time_str, "%Y-%m-%d")
    elif query_type == "month":
        query_time_str = f"{query_year_str}-{query_month_str}-1"
        query_time_stamp = datetime.datetime.strptime(query_time_str, "%Y-%m-%d")
    else:
        query_time_str = f"{query_year_str}-{query_month_str}-{query_day_str} 0"
        query_time_stamp = datetime.datetime.strptime(query_time_str, "%Y-%m-%d %H")

    # 准备返回数据列表
    type1_data = []
    type2_data = []
    type3_data = []
    x_axis = []
    all_data = []

    # 查询数据
    for i in range(cycle_num):
        if query_type == "year":
            res_time_stamp = query_time_stamp + relativedelta.relativedelta(months=i)
            res_year = res_time_stamp.strftime("%Y")
            res_month = res_time_stamp.strftime("%m")
            type1_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "video_type": "同款生成",
                "pay_status": 1
            }
            type2_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "video_type": "剪辑串编",
                "pay_status": 1
            }
            type3_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "video_type": "AI融合剪辑",
                "pay_status": 1
            }
            x_axis.append(res_time_stamp.strftime("%Y-%m"))
        elif query_type == "month":
            res_time_stamp = query_time_stamp + relativedelta.relativedelta(days=i)
            res_year = res_time_stamp.strftime("%Y")
            res_month = res_time_stamp.strftime("%m")
            res_day = res_time_stamp.strftime("%d")
            type1_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "generate_stamp__day": res_day,
                "video_type": "同款生成",
                "pay_status": 1
            }
            type2_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "generate_stamp__day": res_day,
                "video_type": "剪辑串编",
                "pay_status": 1
            }
            type3_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "generate_stamp__day": res_day,
                "video_type": "AI融合剪辑",
                "pay_status": 1
            }
            x_axis.append(res_time_stamp.strftime("%Y-%m-%d"))
        else:
            res_time_stamp = query_time_stamp + relativedelta.relativedelta(hours=i)
            res_year = res_time_stamp.strftime("%Y")
            res_month = res_time_stamp.strftime("%m")
            res_day = res_time_stamp.strftime("%d")

            start_time = query_time_stamp + datetime.timedelta(hours=i)
            end_time = query_time_stamp + datetime.timedelta(hours=i + 1)
            type1_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "generate_stamp__day": res_day,
                "generate_stamp__range": (start_time, end_time),
                "video_type": "同款生成",
                "pay_status": 1
            }
            type2_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "generate_stamp__day": res_day,
                "generate_stamp__range": (start_time, end_time),
                "video_type": "剪辑串编",
                "pay_status": 1
            }
            type3_query_dict = {
                "generate_stamp__year": res_year,
                "generate_stamp__month": res_month,
                "generate_stamp__day": res_day,
                "generate_stamp__range": (start_time, end_time),
                "video_type": "AI融合剪辑",
                "pay_status": 1
            }
            x_axis.append(f'{start_time.strftime("%H")}时 ~ {end_time.strftime("%H")}时')

        type1_video_list = models.VideoInfo.objects.filter(**type1_query_dict)
        type2_video_list = models.VideoInfo.objects.filter(**type2_query_dict)
        type3_video_list = models.VideoInfo.objects.filter(**type3_query_dict)

        type1_data.append(sum([i.pay_amounts for i in type1_video_list]))
        type2_data.append(sum([i.pay_amounts for i in type2_video_list]))
        type3_data.append(sum([i.pay_amounts for i in type3_video_list]))

    # 如果是按天查询并且是当天加一个当前小时的数据
    if query_type == "day" and now_year_str == query_year_str and now_month_str == query_month_str and now_day_str == query_day_str:
        n_time = query_time_stamp + datetime.timedelta(hours=cycle_num)
        type1_query_dict = {
            "generate_stamp__year": query_year_str,
            "generate_stamp__month": query_month_str,
            "generate_stamp__day": query_day_str,
            "generate_stamp__gt": n_time,
            "video_type": "同款生成",
            "pay_status": 1
        }
        type2_query_dict = {
            "generate_stamp__year": query_year_str,
            "generate_stamp__month": query_month_str,
            "generate_stamp__day": query_day_str,
            "generate_stamp__gt": n_time,
            "video_type": "剪辑串编",
            "pay_status": 1
        }
        type3_query_dict = {
            "generate_stamp__year": query_year_str,
            "generate_stamp__month": query_month_str,
            "generate_stamp__day": query_day_str,
            "generate_stamp__gt": n_time,
            "video_type": "AI融合剪辑",
            "pay_status": 1
        }

        x_axis.append(f'{n_time.strftime("%H")}时 ~ 此时')

        type1_video_list = models.VideoInfo.objects.filter(**type1_query_dict)
        type2_video_list = models.VideoInfo.objects.filter(**type2_query_dict)
        type3_video_list = models.VideoInfo.objects.filter(**type3_query_dict)

        type1_data.append(sum([i.pay_amounts for i in type1_video_list]))
        type2_data.append(sum([i.pay_amounts for i in type2_video_list]))
        type3_data.append(sum([i.pay_amounts for i in type3_video_list]))

        for j in range(cycle_num + 1):
            all_data.append(type1_data[j] + type2_data[j] + type3_data[j])
    else:
        for j in range(cycle_num):
            all_data.append(type1_data[j] + type2_data[j] + type3_data[j])

    return type1_data, type2_data, type3_data, all_data, x_axis


@login_required
def chart_list(request):
    """ 数据图表页面 """
    # 现在的时间信息
    now_time_stamp = datetime.datetime.now()
    now_year_str = now_time_stamp.strftime("%Y")
    now_month_str = now_time_stamp.strftime("%m")
    now_day_str = now_time_stamp.strftime("%d")

    # 获取到的时间
    query_type = request.GET.get("query_type")
    query_year = request.GET.get("query_year")
    query_month = request.GET.get("query_month")
    query_day = request.GET.get("query_day")

    # 如果没获取到给默认值
    if query_type is None:
        query_type = "day"
    if query_year is None:
        query_year = now_year_str
    if query_month is None:
        query_month = now_month_str
    if query_day is None:
        query_day = now_day_str

    # 准备按年统计下拉菜单
    year_list = [i["year"] for i in models.CountInfo.objects.values("year").annotate()]
    year_list = list(set(year_list))
    year_list.sort()

    # 准备按月统计下拉菜单
    if query_year == now_year_str:
        month_list = [str(j + 1) for j in range(int(now_month_str))]
    else:
        month_list = [str(j + 1) for j in range(12)]

    # 准备按日统计下拉菜单
    if query_year == now_year_str and query_month == now_month_str:
        day_list = [str(j + 1) for j in range(int(now_day_str))]
    else:
        split_joint_time_stamp = datetime.datetime.strptime(f"{query_year}-{query_month}-1", "%Y-%m-%d")
        res_time_stamp = split_joint_time_stamp + relativedelta.relativedelta(
            months=1) - relativedelta.relativedelta(days=1)
        day_list = [str(j + 1) for j in range(int(res_time_stamp.strftime("%d")))]

    context = {
        "query_type": query_type,
        "query_year": query_year,
        "query_month": query_month,
        "query_day": query_day,
        "year_list": year_list,
        "month_list": month_list,
        "day_list": day_list
    }
    return render(request, "chart_list.html", context)


""" 生成随机数据
def get_random_key(length=10):
    import random
    import string
    num_count = random.randint(1, length - 1)
    letter_count = length - num_count
    num_list = [random.choice(string.digits) for _ in range(num_count)]
    letter_list = [random.choice(string.ascii_uppercase) for _ in range(letter_count)]
    all_list = num_list + letter_list
    random.shuffle(all_list)
    return "".join([i for i in all_list])

import random
from datetime import date, timedelta
for i in range(400):
    res_time_stamp = date.today() - i * timedelta(days=1)
    models.VideoInfo.objects.create(
        openid=get_random_key(),
        picture_url="test",
        video_url="test",
        generate_time=res_time_stamp,
        invalid_time=res_time_stamp,
        video_type=random.choice(['同款生成', '剪辑串编', 'AI融合剪辑']),
        generate_stamp=res_time_stamp,
        secret_key=get_random_key(),
        pay_status=random.choice([0, 1]),
        pay_amounts=random.choice([3, 5, 8])
    )
"""


@login_required
def chart_line(request):
    """ 绘制数据图表表格 """
    # 接收的信息
    query_type = request.GET.get("query_type")
    query_year = request.GET.get("query_year")
    query_month = request.GET.get("query_month")
    query_day = request.GET.get("query_day")

    # 现在的时间信息
    now_time_stamp = datetime.datetime.now()
    now_year_str = now_time_stamp.strftime("%Y")
    now_month_str = now_time_stamp.strftime("%m")
    now_day_str = now_time_stamp.strftime("%d")

    # 接收 null 时候给默认值
    if not query_type:
        query_type = "day"
    if not query_year:
        query_year = now_year_str
    if not query_month:
        query_month = now_month_str
    if not query_day:
        query_day = now_day_str

    # 要查询的时间
    query_time_stamp = datetime.datetime.strptime(f"{query_year}-{query_month}-{query_day}", "%Y-%m-%d")

    # 获取数据
    type1_data, type2_data, type3_data, all_data, x_axis = chart_create(query_type, query_time_stamp)

    # 拼接返回数据
    legend = ['同款生成', '剪辑串编', 'AI融合剪辑', '总销售额']
    series_list = [
        {
            "name": '同款生成',
            "type": 'line',
            "data": type1_data
        },
        {
            "name": '剪辑串编',
            "type": 'line',
            "data": type2_data
        },
        {
            "name": 'AI融合剪辑',
            "type": 'line',
            "data": type3_data
        },
        {
            "name": '总销售额',
            "type": 'line',
            "stack": 'Total',
            "data": all_data
        }
    ]

    result = {
        "status": True,
        "data": {
            'legend': legend,
            'series_list': series_list,
            'x_axis': x_axis,
        }
    }
    return JsonResponse(result)


@login_required
def chart_table(request):
    """ 绘制数据图表表格 """
    # 接收的信息
    query_type = request.GET.get("query_type")
    query_year = request.GET.get("query_year")
    query_month = request.GET.get("query_month")
    query_day = request.GET.get("query_day")

    # 现在的时间信息
    now_time_stamp = datetime.datetime.now()
    now_year_str = now_time_stamp.strftime("%Y")
    now_month_str = now_time_stamp.strftime("%m")
    now_day_str = now_time_stamp.strftime("%d")

    # 接收 null 时候给默认值
    if query_type == "null":
        query_type = "day"
    if query_year == "null":
        query_year = now_year_str
    if query_month == "null":
        query_month = now_month_str
    if query_day == "null":
        query_day = now_day_str

    # 要查询的时间
    query_time_stamp = datetime.datetime.strptime(f"{query_year}-{query_month}-{query_day}", "%Y-%m-%d")

    # 获取数据
    type1_data, type2_data, type3_data, all_data, x_axis = chart_create(query_type, query_time_stamp)

    # 拼接返回数据
    return_dict = {
        "code": 0,
        "msg": "",
        "count": len(type1_data),
        "data": [
            {
                "date": x_axis[i],
                "data1": type1_data[i],
                "data2": type2_data[i],
                "data3": type3_data[i],
                "data4": all_data[i],
            } for i in range(len(type1_data))
        ]
    }
    return JsonResponse(return_dict)
