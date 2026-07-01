"""
主体公司管理 — URL 路由
"""
from rest_framework import routers

from dvadmin.company.views import CompanyEntityViewSet

company_url = routers.SimpleRouter()
company_url.register(r"entity", CompanyEntityViewSet, basename="company_entity")

urlpatterns = company_url.urls
