from django.contrib import admin
from .models import LearningCategory, LearningItem, TrackVisibility


class LearningItemInline(admin.TabularInline):
    model = LearningItem
    extra = 1
    fields = ("title", "order", "image", "is_active")


@admin.register(LearningCategory)
class LearningCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "track", "order")
    list_filter = ("track",)
    inlines = [LearningItemInline]


@admin.register(LearningItem)
class LearningItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "order", "is_active")
    list_filter = ("category__track", "is_active")
    search_fields = ("title",)


@admin.register(TrackVisibility)
class TrackVisibilityAdmin(admin.ModelAdmin):
    list_display = ("track", "show_in_learning", "show_in_practice", "show_in_validation", "show_in_tts")
    list_display_links = ("track",)
    list_editable = ("show_in_learning", "show_in_practice", "show_in_validation", "show_in_tts")
    list_filter = ("show_in_learning", "show_in_practice", "show_in_validation", "show_in_tts")
