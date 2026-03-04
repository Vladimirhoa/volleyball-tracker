from django.contrib import admin
from .models import Match
from video.models import Video

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    inlines = [VideoInline]

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Video) and not getattr(instance, 'user_id', None):
                instance.user = request.user
            instance.save()
        formset.save_m2m()