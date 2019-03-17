from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.widgets import AdminPageChooser

from .models import Site, SiteLanguage


class SiteForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = Site
        fields = ['hostname', 'port', 'site_name', 'is_default_site']


class SiteLanguageForm(forms.ModelForm):

    class Meta:
        model = SiteLanguage
        fields = ['language', 'root_page', 'is_active']


SiteLanguageFormSetBase = forms.inlineformset_factory(Site, SiteLanguage, form=SiteLanguageForm, extra=0)

class SiteLanguageFormSet(SiteLanguageFormSetBase):
    minimum_forms = 1
    minimum_forms_message = _("Please specify at least one language for this site.")

    def add_fields(self, form, *args, **kwargs):
        super().add_fields(form, *args, **kwargs)

        # Hide delete field
        form.fields['DELETE'].widget = forms.HiddenInput()

        # Use page chooser for root page
        form.fields['root_page'].widget = AdminPageChooser()