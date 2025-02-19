from app import models
from api.utils.bootstrap import BootStrapModelForm


class UserModelForm(BootStrapModelForm):
    # from django.core.validators import RegexValidator
    # username = forms.CharField(label="手机号", validators=[RegexValidator(r'^1[3-9]\d{9}$', '手机号格式错误')])
    # username = forms.CharField(label="姓名", disabled=True)

    class Meta:
        model = models.UserInfo
        # fields = ["username", "account", "gender", "depart"]
        fields = "__all__"


class AmountModelForm(BootStrapModelForm):
    # from django.core.validators import RegexValidator
    # username = forms.CharField(label="手机号", validators=[RegexValidator(r'^1[3-9]\d{9}$', '手机号格式错误')])
    # username = forms.CharField(label="姓名", disabled=True)

    class Meta:
        model = models.AmountInfo
        fields = ["amount_price"]
        # fields = "__all__"
