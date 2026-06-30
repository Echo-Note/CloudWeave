from django.apps import AppConfig


class CompanyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dvadmin.company"
    verbose_name = "主体公司管理"
