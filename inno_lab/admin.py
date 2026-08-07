from django.contrib import admin

from .models import LegacyStorageEntry, PlanStep, Product, ProductPhoto, TransferPlan


class ProductPhotoInline(admin.TabularInline):
    model = ProductPhoto
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'source', 'overall_score', 'date', 'created_at')
    list_filter = ('source', 'category')
    search_fields = ('name', 'brand', 'conclusion', 'whats_new')
    inlines = [ProductPhotoInline]


class PlanStepInline(admin.TabularInline):
    model = PlanStep
    extra = 0


@admin.register(TransferPlan)
class TransferPlanAdmin(admin.ModelAdmin):
    list_display = ('product', 'line', 'progress', 'start_date', 'updated_at')
    list_filter = ('line',)
    inlines = [PlanStepInline]


@admin.register(LegacyStorageEntry)
class LegacyStorageEntryAdmin(admin.ModelAdmin):
    list_display = ('key', 'updated_at')
    readonly_fields = ('key', 'value', 'updated_at')
