"""Admin configuration for the calculator app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    EmissionFactor,
    EmissionFactorChangelog,
    FootprintCategory,
    FootprintEntry,
)


class EmissionFactorChangelogInline(admin.TabularInline):
    """Inline changelog in the EmissionFactor admin."""

    model = EmissionFactorChangelog
    extra = 0
    readonly_fields = ["changed_by", "old_value", "new_value", "source_citation", "changed_at"]
    can_delete = False


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    """Admin view for emission factors with full changelog visibility."""

    list_display = [
        "factor_id",
        "category",
        "subcategory",
        "factor_value",
        "unit",
        "source_version",
        "effective_date",
        "is_active",
        "source_link",
    ]
    list_filter = ["category", "is_active", "source_version"]
    search_fields = ["factor_id", "subcategory", "source"]
    readonly_fields = ["created_at"]
    inlines = [EmissionFactorChangelogInline]
    ordering = ["category", "factor_id"]

    @admin.display(description="Source")
    def source_link(self, obj: EmissionFactor) -> str:
        """Render source_url as a clickable link in the admin list."""
        return format_html('<a href="{}" target="_blank">View source</a>', obj.source_url)

    def save_model(self, request, obj, form, change):
        """Auto-create a changelog entry when a factor is changed via admin."""
        if change and form.changed_data:
            old = EmissionFactor.objects.get(pk=obj.pk)
            EmissionFactorChangelog.objects.create(
                factor=obj,
                changed_by=request.user,
                old_value=old.factor_value if "factor_value" in form.changed_data else None,
                new_value=obj.factor_value,
                source_citation=f"Admin update by {request.user}. Old version: {old.source_version}",
                change_reason="Updated via Django admin — please add source citation in notes field.",
            )
        super().save_model(request, obj, form, change)


@admin.register(EmissionFactorChangelog)
class EmissionFactorChangelogAdmin(admin.ModelAdmin):
    """Read-only audit log view."""

    list_display = ["factor", "changed_by", "old_value", "new_value", "changed_at"]
    list_filter = ["changed_at", "changed_by"]
    readonly_fields = ["factor", "changed_by", "old_value", "new_value", "source_citation", "change_reason", "changed_at"]
    ordering = ["-changed_at"]

    def has_add_permission(self, request):
        return False  # Changelog entries are only created programmatically

    def has_delete_permission(self, request, obj=None):
        return False  # Audit log is immutable


class FootprintCategoryInline(admin.TabularInline):
    """Inline category breakdown in FootprintEntry admin."""

    model = FootprintCategory
    extra = 0
    readonly_fields = ["category", "co2e_kg", "percentage"]
    can_delete = False


@admin.register(FootprintEntry)
class FootprintEntryAdmin(admin.ModelAdmin):
    """Admin view for footprint calculation sessions."""

    list_display = ["user", "date", "mode", "total_co2e_kg", "factor_version", "created_at"]
    list_filter = ["mode", "factor_version", "date"]
    search_fields = ["user__email"]
    readonly_fields = ["created_at", "updated_at", "raw_data"]
    inlines = [FootprintCategoryInline]
    ordering = ["-date"]
