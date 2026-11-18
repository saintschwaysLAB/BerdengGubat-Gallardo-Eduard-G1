from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser

from .models import Campaign, Donation, Organization


class DashboardBrandNavigationTests(TestCase):
    def test_brand_returns_each_authenticated_role_to_its_dashboard(self):
        role_dashboards = (
            (CustomUser.Role.CUSTOMER, "dashboard"),
            (CustomUser.Role.ORG_LEADER, "organization_dashboard"),
            (CustomUser.Role.ADMIN, "admin_dashboard"),
        )

        for index, (role, dashboard_name) in enumerate(role_dashboards):
            with self.subTest(role=role):
                user = CustomUser.objects.create_user(
                    username=f"branduser{index}",
                    password="StrongPassword123!",
                    role=role,
                )
                self.client.force_login(user)
                response = self.client.get(reverse(dashboard_name))

                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    f'<a href="{reverse(dashboard_name)}" class="brand">Berdeng Gubat</a>',
                )
                self.assertTrue(response.wsgi_request.user.is_authenticated)


class DonationFeatureTests(TestCase):
    def setUp(self):
        self.donor = CustomUser.objects.create_user(
            username="donor",
            password="StrongPassword123!",
            role=CustomUser.Role.CUSTOMER,
        )
        self.other_donor = CustomUser.objects.create_user(
            username="otherdonor",
            password="StrongPassword123!",
            role=CustomUser.Role.CUSTOMER,
        )
        self.leader = CustomUser.objects.create_user(
            username="leader",
            password="StrongPassword123!",
            role=CustomUser.Role.ORG_LEADER,
        )
        self.other_leader = CustomUser.objects.create_user(
            username="otherleader",
            password="StrongPassword123!",
            role=CustomUser.Role.ORG_LEADER,
        )
        self.organization = self.create_organization(self.leader, "Forest Care")
        self.other_organization = self.create_organization(
            self.other_leader, "River Care"
        )

    def create_organization(self, owner, name):
        return Organization.objects.create(
            name=name,
            description=f"Support {name}",
            partner_type=Organization.PartnerType.NGO,
            partner_name="Green Partners",
            location="Quezon City",
            created_by=owner,
        )

    def create_donation(self, donor=None, organization=None, amount="100.00"):
        return Donation.objects.create(
            donor=donor or self.donor,
            organization=organization or self.organization,
            amount=amount,
        )

    def create_campaign(self, organization=None, title="Native Forest Recovery"):
        return Campaign.objects.create(
            organization=organization or self.organization,
            title=title,
            description="Restore native forest habitat.",
            goal_amount="1000.00",
        )

    def test_donor_dashboard_shows_at_most_three_active_organizations(self):
        for index in range(4):
            self.create_organization(self.leader, f"Extra Organization {index}")
        inactive = self.create_organization(self.leader, "Inactive Organization")
        inactive.is_active = False
        inactive.save()
        self.client.force_login(self.donor)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["organizations"]), 3)
        self.assertNotContains(response, "Inactive Organization")

    def test_donor_dashboard_features_three_active_campaigns(self):
        campaigns = [
            self.create_campaign(title=f"Reforestation {index}")
            for index in range(4)
        ]
        inactive = self.create_campaign(title="Inactive planting campaign")
        inactive.is_active = False
        inactive.save()
        self.client.force_login(self.donor)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["campaigns"]), 3)
        self.assertNotContains(response, "Inactive planting campaign")
        self.assertIn(campaigns[0], response.context["campaigns"])

    def test_admin_can_publish_campaign_for_organization_and_donor_sees_it(self):
        admin = CustomUser.objects.create_user(
            username="admin",
            password="StrongPassword123!",
            role=CustomUser.Role.ADMIN,
        )
        organization = self.create_organization(admin, "Admin-managed Forest")
        self.client.force_login(admin)

        detail_response = self.client.get(
            reverse("organization_detail", kwargs={"pk": organization.pk})
        )
        self.assertContains(detail_response, "Create fundraiser")

        response = self.client.post(
            reverse(
                "campaign_create",
                kwargs={"organization_id": organization.pk},
            ),
            {
                "title": "Community Reforestation Drive",
                "description": "Restore native tree cover.",
                "goal_amount": "5000.00",
                "deadline": "",
                "is_active": "on",
            },
        )
        detail_url = reverse("organization_detail", kwargs={"pk": organization.pk})
        self.assertRedirects(response, detail_url)
        self.assertContains(self.client.get(detail_url), "Community Reforestation Drive")

        self.client.force_login(self.donor)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(
            list(response.context["campaigns"].values_list("title", flat=True)),
            ["Community Reforestation Drive"],
        )

    def test_leader_can_create_update_and_delete_campaigns_for_owned_organization(self):
        self.client.force_login(self.leader)
        create_url = reverse(
            "campaign_create", kwargs={"organization_id": self.organization.pk}
        )
        response = self.client.post(
            create_url,
            {
                "title": "Plant a Native Forest",
                "description": "Reforest the hillside with native trees.",
                "goal_amount": "25000.00",
                "deadline": "",
                "is_active": "on",
            },
        )

        campaign = Campaign.objects.get(title="Plant a Native Forest")
        detail_url = reverse(
            "organization_detail", kwargs={"pk": self.organization.pk}
        )
        self.assertRedirects(response, detail_url)
        self.assertContains(self.client.get(detail_url), "Plant a Native Forest")
        self.assertEqual(campaign.organization, self.organization)

        edit_url = reverse("campaign_edit", kwargs={"pk": campaign.pk})
        response = self.client.post(
            edit_url,
            {
                "title": "Plant a Native Forest Updated",
                "description": "Updated planting plan.",
                "goal_amount": "30000.00",
                "deadline": "",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, detail_url)
        self.assertContains(
            self.client.get(detail_url), "Plant a Native Forest Updated"
        )
        campaign.refresh_from_db()
        self.assertEqual(campaign.title, "Plant a Native Forest Updated")
        self.assertEqual(str(campaign.goal_amount), "30000.00")

        response = self.client.get(
            reverse(
                "campaign_edit",
                kwargs={
                    "pk": self.create_campaign(
                        self.other_organization, "Someone else's campaign"
                    ).pk
                },
            )
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("campaign_delete", kwargs={"pk": campaign.pk})
        )
        self.assertRedirects(response, detail_url)
        self.assertFalse(Campaign.objects.filter(pk=campaign.pk).exists())

    def test_campaign_donation_is_linked_and_updates_progress(self):
        campaign = self.create_campaign()
        self.client.force_login(self.donor)
        response = self.client.post(
            reverse("campaign_donation_create", kwargs={"campaign_id": campaign.pk}),
            {"amount": "250.00", "message": "Plant more trees"},
        )

        self.assertRedirects(response, reverse("donations"))
        donation = Donation.objects.get()
        self.assertEqual(donation.campaign, campaign)
        self.assertEqual(donation.organization, self.organization)

        self.client.force_login(self.other_donor)
        response = self.client.get(reverse("campaigns"))
        listed_campaign = response.context["campaigns"].get(pk=campaign.pk)
        self.assertEqual(listed_campaign.raised_amount, donation.amount)
        self.assertEqual(listed_campaign.progress_percent, 25)

    def test_campaigns_from_inactive_organizations_cannot_receive_donations(self):
        campaign = self.create_campaign()
        self.organization.is_active = False
        self.organization.save()
        self.client.force_login(self.donor)

        response = self.client.get(
            reverse("campaign_donation_create", kwargs={"campaign_id": campaign.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_donor_can_create_update_and_delete_their_donation(self):
        self.client.force_login(self.donor)
        create_url = reverse(
            "donation_create", kwargs={"organization_id": self.organization.pk}
        )
        response = self.client.post(
            create_url,
            {"amount": "125.50", "message": "For local planting"},
        )

        self.assertRedirects(response, reverse("donations"))
        donation = Donation.objects.get()
        self.assertEqual(donation.donor, self.donor)
        self.assertEqual(donation.organization, self.organization)
        self.assertEqual(str(donation.amount), "125.50")

        edit_url = reverse("donation_edit", kwargs={"pk": donation.pk})
        response = self.client.post(
            edit_url,
            {"amount": "200.00", "message": "Updated contribution"},
        )
        self.assertRedirects(response, reverse("donations"))
        donation.refresh_from_db()
        self.assertEqual(str(donation.amount), "200.00")
        self.assertEqual(donation.message, "Updated contribution")

        delete_url = reverse("donation_delete", kwargs={"pk": donation.pk})
        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse("donations"))
        self.assertFalse(Donation.objects.filter(pk=donation.pk).exists())

    def test_donor_cannot_create_invalid_or_other_users_donations(self):
        self.client.force_login(self.donor)
        create_url = reverse(
            "donation_create", kwargs={"organization_id": self.organization.pk}
        )
        response = self.client.post(create_url, {"amount": "0", "message": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Donation.objects.exists())

        donation = self.create_donation(donor=self.other_donor)
        edit_url = reverse("donation_edit", kwargs={"pk": donation.pk})
        self.assertEqual(self.client.get(edit_url).status_code, 404)

    def test_donors_can_only_see_their_own_donations(self):
        own_donation = self.create_donation()
        other_donation = self.create_donation(
            donor=self.other_donor, organization=self.other_organization
        )
        self.client.force_login(self.donor)

        response = self.client.get(reverse("donations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Forest Care")
        self.assertNotContains(response, "River Care")
        self.assertEqual(list(response.context["donations"]), [own_donation])
        self.assertNotIn(other_donation, response.context["donations"])

    def test_leader_can_create_and_manage_only_their_organizations(self):
        self.client.force_login(self.leader)
        response = self.client.post(
            reverse("organization_create"),
            {
                "name": "New Forest Project",
                "description": "Replant native trees.",
                "partner_type": Organization.PartnerType.BOTH,
                "partner_name": "Local NGO and LGU",
                "location": "Baguio",
            },
        )

        organization = Organization.objects.get(name="New Forest Project")
        self.assertRedirects(
            response,
            reverse("organization_detail", kwargs={"pk": organization.pk}),
        )
        self.assertEqual(organization.created_by, self.leader)
        self.assertTrue(organization.is_active)
        self.assertEqual(
            self.client.get(
                reverse("organization_edit", kwargs={"pk": self.other_organization.pk})
            ).status_code,
            404,
        )

    def test_leader_can_review_donations_for_their_organization_only(self):
        own_donation = self.create_donation()
        self.create_donation(
            donor=self.other_donor, organization=self.other_organization
        )
        self.client.force_login(self.leader)

        response = self.client.get(
            reverse(
                "organization_donations",
                kwargs={"organization_id": self.organization.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["donations"]), [own_donation])
        self.assertEqual(
            self.client.get(
                reverse(
                    "organization_donations",
                    kwargs={"organization_id": self.other_organization.pk},
                )
            ).status_code,
            404,
        )

    def test_organization_with_donations_cannot_be_deleted(self):
        self.create_donation()
        self.client.force_login(self.leader)

        response = self.client.post(
            reverse("organization_delete", kwargs={"pk": self.organization.pk})
        )

        self.assertRedirects(
            response,
            reverse("organization_detail", kwargs={"pk": self.organization.pk}),
        )
        self.assertTrue(Organization.objects.filter(pk=self.organization.pk).exists())

    def test_organization_without_donations_can_be_deleted(self):
        self.client.force_login(self.leader)

        response = self.client.post(
            reverse("organization_delete", kwargs={"pk": self.organization.pk})
        )

        self.assertRedirects(response, reverse("organizations"))
        self.assertFalse(Organization.objects.filter(pk=self.organization.pk).exists())

    def test_donors_cannot_create_organizations(self):
        self.client.force_login(self.donor)

        response = self.client.get(reverse("organization_create"))

        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(
            Organization.objects.filter(created_by=self.donor).exists()
        )

    def test_donation_pages_require_login(self):
        response = self.client.get(reverse("donations"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('donations')}",
        )
