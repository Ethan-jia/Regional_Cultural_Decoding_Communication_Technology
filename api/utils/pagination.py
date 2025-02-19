"""
自定义的分页组件，以后如果想要使用这个分页组件，你需要做如下几件事：

在视图函数中：
    def pretty_list(request):
        # 1.根据自己的情况去筛选自己的数据
        queryset = models.UserInfo.objects.filter(**data_dict)
        # 2.实例化分页对象
        page_object = Pagination(request, queryset)
        context = {
            "queryset": page_object.page_queryset,  # 分完页的数据
            "page_string": page_object.html()       # 生成页码
        }
        return render(request, 'user_list.html', context)

在HTML页面中

    {% for obj in queryset %}
        {{obj.xx}}
    {% endfor %}

    <ul class="pagination">
        {{ page_string }}
    </ul>

"""
import copy
from django.utils.safestring import mark_safe


class Pagination(object):

    def __init__(self, request, queryset, page_size=10, page_param="page", page_num=5):
        """
        :param request: 请求的对象
        :param queryset: 符合条件的数据（根据这个数据给他进行分页处理）
        :param page_size: 每页显示多少条数据
        :param page_param: 在URL中传递的获取分页的参数，例如：/user/list/?page=12
        :param page_num: 显示当前页的 前或后几页（页码）
        """
        query_dict = copy.deepcopy(request.GET)  # 拷贝一份请求
        query_dict._mutable = True  # 修改可以拼接的属性
        self.query_dict = query_dict  # 当前的url拼接的参数
        self.page_param = page_param
        page = request.GET.get(page_param, "1")
        # 验证传入的是否为数字
        if page.isdecimal():
            page = int(page)
        else:
            page = 1
        self.page = page  # 当前页数
        self.page_size = page_size
        self.start = (page - 1) * page_size  # 计算显示页数的起始值
        self.end = page * page_size  # 计算显示页数的起始值
        self.page_queryset = queryset[self.start:self.end]  # 分好页的数据,最终显示的数据
        total_count = queryset.count()  # 计算数据的条目数
        total_page_count, div = divmod(total_count, page_size)  # 计算总页码
        if div:  # 向上取整
            total_page_count += 1
        self.total_page_count = total_page_count  # 总页码数
        self.page_num = page_num

    def html(self):
        """生成页码"""
        # 计算显示当前页的前后页数
        # 2 * page_num + 1 ：当前显示的数量
        if self.total_page_count <= 2 * self.page_num + 1:
            # 如果页数少
            start_page = 1
            end_page = self.total_page_count
        else:
            if self.page <= self.page_num:
                # 小极值
                start_page = 1
                end_page = 2 * self.page_num + 1
            else:
                if (self.page + self.page_num) > self.total_page_count:
                    # 大极值
                    start_page = self.total_page_count - 2 * self.page_num
                    end_page = self.total_page_count
                else:
                    # 前后页
                    start_page = self.page - self.page_num
                    end_page = self.page + self.page_num

        # 页码字符列表
        page_str_list = []

        # 上一页：
        if self.page > 1:
            self.query_dict.setlist(self.page_param, [self.page - 1])
            ele = "<li><a href='?{}'>上一页</a></li>".format(self.query_dict.urlencode())
        else:
            self.query_dict.setlist(self.page_param, [1])
            ele = "<li><a href='?{}'>上一页</a></li>".format(self.query_dict.urlencode())
        page_str_list.append(ele)

        # 页码
        for i in range(start_page, end_page + 1):
            self.query_dict.setlist(self.page_param, [i])
            if i == self.page:
                ele = "<li class='active'><a href='?{}'>{}</a></li>".format(self.query_dict.urlencode(), i)
            else:
                ele = "<li><a href='?{}'>{}</a></li>".format(self.query_dict.urlencode(), i)
            page_str_list.append(ele)

        # 下一页：
        if self.page < self.total_page_count:
            self.query_dict.setlist(self.page_param, [self.page + 1])
            ele = "<li><a href='?{}'>下一页</a></li>".format(self.query_dict.urlencode())
        else:
            self.query_dict.setlist(self.page_param, [self.total_page_count])
            ele = "<li><a href='?{}'>下一页</a></li>".format(self.query_dict.urlencode())
        page_str_list.append(ele)
        page_string = mark_safe("".join(page_str_list))
        return page_string
