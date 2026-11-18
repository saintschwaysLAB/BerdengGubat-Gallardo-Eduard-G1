from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Organization(models.Model):
    class PartnerType(models.TextChoices):
        NGO = "NGO", "NGO"
        LGU = "LGU", "LGU"
        BOTH = "BOTH", "NGO and LGU"

    name = models.CharField(max_length=160)
    description = models.TextField()
    partner_type = models.CharField(max_length=4, choices=PartnerType.choices)
    partner_name = models.CharField(max_length=160)
    location = models.CharField(max_length=160)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organizations",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "name"]

    def __str__(self):
        return self.name


class Campaign(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    title = models.CharField(max_length=160)
    description = models.TextField()
    goal_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
    )
    deadline = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "title"]
        constraints = [
            models.CheckConstraint(
                condition=Q(goal_amount__gte=Decimal("1.00")),
                name="campaign_goal_at_least_one",
            ),
        ]

    @property
    def progress_percent(self):
        raised = getattr(self, "raised_amount", None) or Decimal("0.00")
        return min(int(raised * 100 / self.goal_amount), 100)

    def __str__(self):
        return self.title


class Donation(models.Model):
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="donations",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="donations",
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.PROTECT,
        related_name="donations",
        blank=True,
        null=True,
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
    )
    message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=Decimal("1.00")),
                name="donation_amount_at_least_one",
            ),
        ]

    def __str__(self):
        return f"{self.donor} donated {self.amount} to {self.organization}"
