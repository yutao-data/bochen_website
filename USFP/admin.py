from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Tag)
admin.site.register(Area)
admin.site.register(CommonUser)
admin.site.register(VerifiedUser)
admin.site.register(Suggestion)
admin.site.register(ReplySuggestion)
admin.site.register(CommonUserOperation)
admin.site.register(AreaOperation)