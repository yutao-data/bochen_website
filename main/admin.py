from django.contrib import admin
from .models import main
# Register your models here.

class mainManager(admin.ModelAdmin):
    # 列表页显示哪些字段的列
    list_display = ['title', 'content']
    # 控制list_display中的字段 哪些可以链接到修改页
    list_display_links = ['title']
    # 添加过滤器
    list_filter = ['title']
    # 添加搜索框[模糊查询]
    search_fields = ['title']
    # 添加可在列表页编辑的字段 与list_display_links不能为同一个 互斥
    list_editable = ['content']

admin.site.register(main, mainManager)
