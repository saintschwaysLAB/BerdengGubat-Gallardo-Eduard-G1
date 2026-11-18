from django.test import TestCase
from django.urls import reverse
from .models import CustomUser


class SignUpViewTests(TestCase):
    def test_success_message_is_shown_after_sign_up(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newstudent",
                "email": "student@example.com",
                "first_name": "New",
                "last_name": "Student",
                "role": CustomUser.Role.CUSTOMER,
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("login"))
        self.assertContains(response, "Account created successfully")
        self.assertTrue(CustomUser.objects.filter(username="newstudent").exists())

    def test_organization_leader_can_sign_up_and_is_redirected_to_their_dashboard(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "leader",
                "email": "leader@example.com",
                "role": CustomUser.Role.ORG_LEADER,
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )
        self.assertRedirects(response, reverse("login"))
        user = CustomUser.objects.get(username="leader")
        self.assertEqual(user.role, CustomUser.Role.ORG_LEADER)

        response = self.client.post(
            reverse("login"),
            {"username": "leader", "password": "StrongPassword123!"},
        )
        self.assertRedirects(response, reverse("organization_dashboard"))

    def test_public_signup_cannot_create_an_admin(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newadmin",
                "email": "admin@example.com",
                "role": CustomUser.Role.ADMIN,
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username="newadmin").exists())


class ProfileUpdateViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="student",
            password="StrongPassword123!",
            email="old@example.com",
        )

    def test_authenticated_user_can_update_their_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("profile_edit"),
            {
                "username": "updatedstudent",
                "email": "updated@example.com",
                "first_name": "Updated",
                "last_name": "Student",
                "role": CustomUser.Role.ADMIN,
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updatedstudent")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Student")
        self.assertEqual(self.user.role, CustomUser.Role.CUSTOMER)

    def test_profile_update_requires_authentication(self):
        response = self.client.get(reverse("profile_edit"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('profile_edit')}",
        )
