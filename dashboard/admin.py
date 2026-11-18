from django.contrib import admin

from .models import Campaign, Donation, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "partner_type", "partner_name", "location", "is_active")
    list_filter = ("partner_type", "is_active")
    search_fields = ("name", "partner_name", "location")


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("organization", "campaign", "donor", "amount", "created_at")
    list_filter = ("created_at",)
    search_fields = ("organization__name", "donor__username", "donor__email")


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "goal_amount", "deadline", "is_active")
    list_filter = ("is_active", "deadline")
    search_fields = ("title", "organization__name")
