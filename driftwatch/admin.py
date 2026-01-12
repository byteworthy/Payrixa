from django.contrib import admin
from .models import Customer, Settings, Upload, ClaimRecord, ReportRun, DriftEvent, UserProfile

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'to_email', 'attach_pdf')
    search_fields = ('customer__name', 'to_email')
    list_filter = ('attach_pdf',)

@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'filename', 'status', 'uploaded_at', 'row_count')
    list_filter = ('status', 'customer')
    search_fields = ('filename', 'customer__name')
    date_hierarchy = 'uploaded_at'

@admin.register(ClaimRecord)
class ClaimRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'upload', 'payer', 'cpt', 'outcome', 'submitted_date', 'decided_date')
    list_filter = ('customer', 'outcome', 'payer', 'cpt_group')
    search_fields = ('payer', 'cpt', 'customer__name')
    date_hierarchy = 'submitted_date'

@admin.register(ReportRun)
class ReportRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'run_type', 'status', 'started_at', 'finished_at')
    list_filter = ('run_type', 'status', 'customer')
    search_fields = ('customer__name',)
    date_hierarchy = 'started_at'

@admin.register(DriftEvent)
class DriftEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'report_run', 'payer', 'cpt_group', 'drift_type', 'severity', 'confidence', 'created_at')
    list_filter = ('drift_type', 'customer', 'payer', 'cpt_group')
    search_fields = ('payer', 'cpt_group', 'customer__name')
    date_hierarchy = 'created_at'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'customer')
    search_fields = ('user__username', 'customer__name')
    list_filter = ('customer',)
