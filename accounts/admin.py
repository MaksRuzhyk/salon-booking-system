from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from .models import MasterProfile
# Register your models here.
@admin.register(MasterProfile)
class MasterProfileAdmin(UnfoldModelAdmin):
    list_display = ('user', 'photo')
    search_fields = ('user__username', 'user__first_name')