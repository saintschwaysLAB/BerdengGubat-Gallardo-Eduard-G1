from django.urls import path
from .views import (
    AdminDashboardView,
    CampaignCreateView,
    CampaignDeleteView,
    CampaignListView,
    CampaignUpdateView,
    CustomerDashboardView,
    DonationCreateView,
    DonationDeleteView,
    DonationListView,
    DonationUpdateView,
    OrganizationCreateView,
    OrganizationDeleteView,
    OrganizationDetailView,
    OrganizationDonationListView,
    OrganizationLeaderDashboardView,
    OrganizationListView,
    OrganizationUpdateView,
)


urlpatterns = [
    path("", CustomerDashboardView.as_view(), name="dashboard"),
    path("admin-dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path(
        "organization-dashboard/",
        OrganizationLeaderDashboardView.as_view(),
        name="organization_dashboard",
    ),
    path("organizations/", OrganizationListView.as_view(), name="organizations"),
    path("campaigns/", CampaignListView.as_view(), name="campaigns"),
    path(
        "organizations/create/",
        OrganizationCreateView.as_view(),
        name="organization_create",
    ),
    path(
        "organizations/<int:pk>/",
        OrganizationDetailView.as_view(),
        name="organization_detail",
    ),
    path(
        "organizations/<int:pk>/edit/",
        OrganizationUpdateView.as_view(),
        name="organization_edit",
    ),
    path(
        "organizations/<int:pk>/delete/",
        OrganizationDeleteView.as_view(),
        name="organization_delete",
    ),
    path(
        "organizations/<int:organization_id>/campaigns/create/",
        CampaignCreateView.as_view(),
        name="campaign_create",
    ),
    path(
        "campaigns/<int:pk>/edit/",
        CampaignUpdateView.as_view(),
        name="campaign_edit",
    ),
    path(
        "campaigns/<int:pk>/delete/",
        CampaignDeleteView.as_view(),
        name="campaign_delete",
    ),
    path(
        "organizations/<int:organization_id>/donations/",
        OrganizationDonationListView.as_view(),
        name="organization_donations",
    ),
    path("donations/", DonationListView.as_view(), name="donations"),
    path(
        "donations/create/<int:organization_id>/",
        DonationCreateView.as_view(),
        name="donation_create",
    ),
    path(
        "donations/create/campaign/<int:campaign_id>/",
        DonationCreateView.as_view(),
        name="campaign_donation_create",
    ),
    path(
        "donations/<int:pk>/edit/",
        DonationUpdateView.as_view(),
        name="donation_edit",
    ),
    path(
        "donations/<int:pk>/delete/",
        DonationDeleteView.as_view(),
        name="donation_delete",
    ),
]