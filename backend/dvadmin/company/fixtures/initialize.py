"""
主体公司 — 初始化数据

通过 python manage.py init 自动注册菜单路由和按钮权限。
MenuInitSerializer 复用 system app 的序列化器（支持递归嵌套 menu_button/menu_field）。
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "application.settings")
django.setup()

from dvadmin.system.fixtures.initSerializer import MenuInitSerializer
from dvadmin.utils.core_initialize import CoreInitialize


class Initialize(CoreInitialize):
    """主体公司模块初始化器，在 manage.py init 时自动调用"""

    def init_menu(self):
        """
        初始化主体公司管理菜单及按钮权限

        唯一标识: name + web_path + component + component_name
        支持重复执行（已存在则更新，reset=True 时强制覆盖）。
        """
        self.init_base(
            MenuInitSerializer,
            unique_fields=["name", "web_path", "component", "component_name"],
        )

    def run(self):
        self.init_menu()


if __name__ == "__main__":
    Initialize(app="dvadmin.company").run()
