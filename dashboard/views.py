from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.models import CustomUser

from .forms import (
    CampaignForm,
    DonationForm,
    OrganizationCreateForm,
    OrganizationForm,
)
from .models import Campaign, Donation, Organization


def is_admin(user):
    return user.is_superuser or user.role == CustomUser.Role.ADMIN


def dashboard_url_for(user):
    if is_admin(user):
        return "admin_dashboard"
    if user.role == CustomUser.Role.ORG_LEADER:
        return "organization_dashboard"
    return "dashboard"


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in self.allowed_roles and not (
            is_admin(request.user) and CustomUser.Role.ADMIN in self.allowed_roles
        ):
            messages.error(request, "You do not have permission to access that page.")
            return redirect(dashboard_url_for(request.user))
        return super().dispatch(request, *args, **kwargs)


class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if is_admin(request.user):
            return redirect("admin_dashboard")
        if request.user.role == CustomUser.Role.ORG_LEADER:
            return redirect("organization_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_count"] = CustomUser.objects.filter(
            role=CustomUser.Role.CUSTOMER
        ).count()
        context["is_admin"] = False
        context["campaigns"] = (
            Campaign.objects.filter(
                is_active=True,
                organization__is_active=True,
            )
            .select_related("organization")
            .annotate(raised_amount=Sum("donations__amount"))[:3]
        )
        context["organizations"] = Organization.objects.filter(is_active=True)[:3]
        donations = Donation.objects.filter(
            donor=self.request.user
        ).select_related("organization", "campaign")
        context["donations"] = donations[:5]
        context["donation_total"] = donations.aggregate(total=Sum("amount"))["total"]
        return context


class OrganizationLeaderDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/organization_leader_panel.html"
    allowed_roles = (CustomUser.Role.ORG_LEADER, CustomUser.Role.ADMIN)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and is_admin(request.user):
            return redirect("admin_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organizations"] = (
            Organization.objects.filter(created_by=self.request.user)
            .annotate(donation_total=Sum("donations__amount"))
            .prefetch_related(
                Prefetch(
                    "campaigns",
                    queryset=Campaign.objects.annotate(
                        raised_amount=Sum("donations__amount")
                    ),
                    to_attr="fundraising_campaigns",
                )
            )
        )
        context["organization_count"] = context["organizations"].count()
        context["campaign_count"] = Campaign.objects.filter(
            organization__created_by=self.request.user
        ).count()
        return context


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/admin_panel.html"
    allowed_roles = (CustomUser.Role.ADMIN,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer_count"] = CustomUser.objects.filter(
            role=CustomUser.Role.CUSTOMER
        ).count()
        context["leader_count"] = CustomUser.objects.filter(
            role=CustomUser.Role.ORG_LEADER
        ).count()
        context["admin_count"] = CustomUser.objects.filter(
            role=CustomUser.Role.ADMIN
        ).count()
        context["organization_count"] = Organization.objects.count()
        context["campaign_count"] = Campaign.objects.count()
        context["donation_count"] = Donation.objects.count()
        return context


class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = "dashboard/organization_list.html"
    context_object_name = "organizations"

    def get_queryset(self):
        queryset = Organization.objects.select_related("created_by").annotate(
            donation_total=Sum("donations__amount")
        )
        if is_admin(self.request.user):
            return queryset
        if self.request.user.role == CustomUser.Role.ORG_LEADER:
            return queryset.filter(created_by=self.request.user)
        return queryset.filter(is_active=True)


class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = "dashboard/organization_detail.html"
    context_object_name = "organization"

    def get_queryset(self):
        queryset = Organization.objects.select_related("created_by").annotate(
            donation_total=Sum("donations__amount")
        )
        if is_admin(self.request.user):
            return queryset
        if self.request.user.role == CustomUser.Role.ORG_LEADER:
            return queryset.filter(created_by=self.request.user)
        return queryset.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage"] = is_admin(self.request.user) or (
            self.object.created_by_id == self.request.user.pk
        )
        campaigns = self.object.campaigns.annotate(
            raised_amount=Sum("donations__amount")
        )
        if not context["can_manage"]:
            campaigns = campaigns.filter(is_active=True)
        context["campaigns"] = campaigns
        return context


class OrganizationCreateView(RoleRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationCreateForm
    template_name = "dashboard/organization_form.html"
    allowed_roles = (CustomUser.Role.ORG_LEADER, CustomUser.Role.ADMIN)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Organization created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("organization_detail", kwargs={"pk": self.object.pk})


class OrganizationOwnerQuerysetMixin:
    def get_queryset(self):
        queryset = Organization.objects.all()
        if is_admin(self.request.user):
            return queryset
        return queryset.filter(created_by=self.request.user)


class OrganizationUpdateView(
    RoleRequiredMixin, OrganizationOwnerQuerysetMixin, UpdateView
):
    model = Organization
    form_class = OrganizationForm
    template_name = "dashboard/organization_form.html"
    allowed_roles = (CustomUser.Role.ORG_LEADER, CustomUser.Role.ADMIN)

    def form_valid(self, form):
        messages.success(self.request, "Organization updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("organization_detail", kwargs={"pk": self.object.pk})


class OrganizationDeleteView(
    RoleRequiredMixin, OrganizationOwnerQuerysetMixin, DeleteView
):
    model = Organization
    template_name = "dashboard/organization_confirm_delete.html"
    success_url = reverse_lazy("organizations")
    allowed_roles = (CustomUser.Role.ORG_LEADER, CustomUser.Role.ADMIN)

    def form_valid(self, form):
        if self.object.donations.exists():
            messages.error(
                self.request,
                "This organization has donation records and cannot be deleted. "
                "Deactivate it from the organization edit page instead.",
            )
            return HttpResponseRedirect(
                reverse("organization_detail", kwargs={"pk": self.object.pk})
            )
        messages.success(self.request, "Organization deleted successfully.")
        return super().form_valid(form)


class CampaignListView(LoginRequiredMixin, ListView):
    model = Campaign
    template_name = "dashboard/campaign_list.html"
    context_object_name = "campaigns"

    def get_queryset(self):
        queryset = Campaign.objects.select_related("organization").annotate(
            raised_amount=Sum("donations__amount")
        )
        if is_admin(self.request.user):
            return queryset
        if self.request.user.role == CustomUser.Role.ORG_LEADER:
            return queryset.filter(organization__created_by=self.request.user)
        return queryset.filter(
            is_active=True,
            organization__is_active=True,
        )


class CampaignCreateView(RoleRequiredMixin, CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = "dashboard/campaign_form.html"
    allowed_roles = (CustomUser.Role.ORG_LEADER, CustomUser.Role.ADMIN)

    def get_organization(self):
        organizations = Organization.objects.all()
        if not is_admin(self.request.user):
            organizations = organizations.filter(created_by=self.request.user)
        return get_object_or_404(organizations, pk=self.kwargs["organization_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.get_organization()
        return context

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        messages.success(self.request, "Fundraising campaign created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "organization_detail",
            kwargs={"pk": self.object.organization_id},
        )


class CampaignOwnerQuerysetMixin:
    def get_queryset(self):
        queryset = Campaign.objects.select_related("organization")
        if is_admin(self.request.user):
            return queryset
        return queryset.filter(organization__created_by=self.request.user)


class CampaignUpdateView(RoleRequiredMixin, CampaignOwnerQuerysetMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = "dashboard/campaign_form.html"
    allowed_roles = (CustomUser.Role.ORG_LEADER, CustomUser.Role.ADMIN)

    def form_valid(self, form):
        messages.success(self.request, "Fundraising campaign updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "organization_detail",
            kwargs={"pk": self.object.organization_id},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.object.organization
        return context


class CampaignDeleteView(RoleRequiredMixin, CampaignOwnerQuerysetMixin, DeleteView):
    model = Campaign
    template_name = "dashboard/campaign_confirm_delete.html"
    allowed_roles = (CustomUser.Role.ORG_LEADER, CustomUser.Role.ADMIN)

    def get_success_url(self):
        return reverse(
            "organization_detail",
            kwargs={"pk": self.object.organization_id},
        )

    def form_valid(self, form):
        if self.object.donations.exists():
            messages.error(
                self.request,
                "This campaign has donation records and cannot be deleted. "
                "Deactivate it by editing the campaign instead.",
            )
            return HttpResponseRedirect(
                reverse(
                    "organization_detail",
                    kwargs={"pk": self.object.organization_id},
                )
            )
        messages.success(self.request, "Fundraising campaign deleted successfully.")
        return super().form_valid(form)


class OrganizationDonationListView(RoleRequiredMixin, ListView):
    model = Donation
    template_name = "dashboard/organization_donations.html"
    context_object_name = "donations"
    allowed_roles = (CustomUser.Role.ORG_LEADER, CustomUser.Role.ADMIN)

    def get_queryset(self):
        organizations = Organization.objects.all()
        if not is_admin(self.request.user):
            organizations = organizations.filter(created_by=self.request.user)
        self.organization = get_object_or_404(
            organizations, pk=self.kwargs["organization_id"]
        )
        return Donation.objects.filter(
            organization=self.organization
        ).select_related("donor")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.organization
        context["donation_total"] = self.object_list.aggregate(
            total=Sum("amount")
        )["total"]
        return context


class DonationListView(LoginRequiredMixin, ListView):
    model = Donation
    template_name = "dashboard/donation_list.html"
    context_object_name = "donations"

    def get_queryset(self):
        queryset = Donation.objects.select_related(
            "donor", "organization", "campaign"
        )
        if is_admin(self.request.user):
            return queryset
        if self.request.user.role == CustomUser.Role.ORG_LEADER:
            return queryset.filter(
                organization__created_by=self.request.user
            )
        return queryset.filter(donor=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["donation_total"] = self.object_list.aggregate(
            total=Sum("amount")
        )["total"]
        context["is_admin"] = is_admin(self.request.user)
        return context


class DonationCreateView(RoleRequiredMixin, CreateView):
    model = Donation
    form_class = DonationForm
    template_name = "dashboard/donation_form.html"
    allowed_roles = (CustomUser.Role.CUSTOMER,)

    def get_target(self):
        if "campaign_id" in self.kwargs:
            campaign = get_object_or_404(
                Campaign.objects.select_related("organization"),
                pk=self.kwargs["campaign_id"],
                is_active=True,
                organization__is_active=True,
            )
            return campaign.organization, campaign
        organization = get_object_or_404(
            Organization,
            pk=self.kwargs["organization_id"],
            is_active=True,
        )
        return organization, None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization, campaign = self.get_target()
        context["organization"] = organization
        context["campaign"] = campaign
        return context

    def form_valid(self, form):
        organization, campaign = self.get_target()
        form.instance.donor = self.request.user
        form.instance.organization = organization
        form.instance.campaign = campaign
        messages.success(
            self.request,
            "Your donation record was saved. No payment was processed.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("donations")


class DonationOwnerQuerysetMixin:
    def get_queryset(self):
        return Donation.objects.filter(donor=self.request.user).select_related(
            "organization"
        )


class DonationUpdateView(RoleRequiredMixin, DonationOwnerQuerysetMixin, UpdateView):
    model = Donation
    form_class = DonationForm
    template_name = "dashboard/donation_form.html"
    allowed_roles = (CustomUser.Role.CUSTOMER,)

    def form_valid(self, form):
        messages.success(self.request, "Donation record updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("donations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.object.organization
        context["campaign"] = self.object.campaign
        return context


class DonationDeleteView(RoleRequiredMixin, DonationOwnerQuerysetMixin, DeleteView):
    model = Donation
    template_name = "dashboard/donation_confirm_delete.html"
    success_url = reverse_lazy("donations")
    allowed_roles = (CustomUser.Role.CUSTOMER,)

    def form_valid(self, form):
        messages.success(self.request, "Donation record deleted successfully.")
        return super().form_valid(form)
