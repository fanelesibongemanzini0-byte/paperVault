from django.contrib import admin
from django.contrib import admin

from .models import PastPaper


@admin.action(description="Approve selected papers")
def approve_papers(modeladmin, request, queryset):
    queryset.update(status="approved")


@admin.action(description="Reject selected papers")
def reject_papers(modeladmin, request, queryset):
    queryset.update(status="rejected")


@admin.action(description="Mark selected papers as pending")
def mark_pending(modeladmin, request, queryset):
    queryset.update(status="pending")


@admin.register(PastPaper)
class PastPaperAdmin(admin.ModelAdmin):
    list_display = ("module_code", "module_name", "year", "semester", "paper_type", "status", "uploaded_at")
    list_filter = ("status", "faculty", "year", "semester", "paper_type")
    search_fields = ("module_code", "module_name")
    actions = [approve_papers, reject_papers, mark_pending]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Papers added directly by staff through /admin/ are already trusted,
        # so default the status to "approved" on the add form. Public
        # submissions (via the /submit/ page, which doesn't expose this
        # field) still default to "pending" per the model's own default.
        if obj is None and "status" in form.base_fields:
            form.base_fields["status"].initial = "approved"
        return form
# Register your models here.
