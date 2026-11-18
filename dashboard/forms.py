from django import forms

from .models import Campaign, Donation, Organization


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget_class = (
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )
            field.widget.attrs["class"] = widget_class


class OrganizationForm(StyledModelForm):
    class Meta:
        model = Organization
        fields = (
            "name",
            "description",
            "partner_type",
            "partner_name",
            "location",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "is_active" in self.fields:
            self.fields["is_active"].help_text = (
                "Active organizations and campaigns are visible to donors."
            )


class OrganizationCreateForm(OrganizationForm):
    class Meta(OrganizationForm.Meta):
        fields = (
            "name",
            "description",
            "partner_type",
            "partner_name",
            "location",
        )


class CampaignForm(StyledModelForm):
    class Meta:
        model = Campaign
        fields = (
            "title",
            "description",
            "goal_amount",
            "deadline",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "goal_amount": forms.NumberInput(attrs={"min": "1.00", "step": "0.01"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["goal_amount"].label = "Fundraising goal (PHP)"
        self.fields["is_active"].help_text = (
            "Active campaigns are visible to donors."
        )


class DonationForm(StyledModelForm):
    class Meta:
        model = Donation
        fields = ("amount", "message")
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "1.00", "step": "0.01"}),
            "message": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount"].help_text = "Enter an amount of at least PHP 1.00."
