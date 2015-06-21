# -*- coding: utf-8 -*-
from django import forms
from django.forms import DateInput
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
import selectable
from selectable.forms import AutoCompleteWidget, AutoCompleteSelectField
from web.lookups import AppUserLookup, HostLookup, DBLookup, ProfileLookup, HostConnectionLookup, DBConnectionLookup, EnvironmentLookup, PrivateKeyLookup
from web.models import AppUser, Profile, HostConnection, Environment, DBConnection


class AppUserForm(forms.ModelForm):
    class Meta:
        model = AppUser
        exclude = ('time_range_enabled', 'time_range_enabled_since', 'time_range_enabled_to', 'allowed_environments', 'last_login')


class AppUserUpdateForm(forms.ModelForm):
    #allowed_environments  = forms.ModelMultipleChoiceField(queryset=Environment.objects.all(), widget=FilteredSelectMultiple("verbose name", is_stacked=False))
    class Meta:
        model = AppUser
        exclude = ('last_login', 'password')


class AdminUserForm(UserChangeForm):
    class Meta:
        model = User
        #exclude = ('email', 'last_login', 'date_joined', 'is_staff', 'is_superuser')
        fields = ['username', 'first_name', 'last_name', 'is_active', 'groups', 'user_permissions', 'password']


class HostConnectionForm(forms.ModelForm):

    class Meta:
        model = HostConnection
        widgets = {
            'password': forms.PasswordInput()
        }


class DBConnectionForm(forms.ModelForm):

    class Meta:
        model = DBConnection
        widgets = {
            'password': forms.PasswordInput()
        }

class FindSessionLogsForm(forms.Form):
    user = forms.ModelChoiceField(queryset=AppUser.objects.all().order_by('last_name'), label=_('User'))
    from_date = forms.DateField(label=_('From'), widget=DateInput(format='%d/%m/%Y', attrs={'class': 'datePicker'}), input_formats=('%d/%m/%Y',))
    to_date = forms.DateField(label=_('To'), widget=DateInput(format='%d/%m/%Y', attrs={'class': 'datePicker'}), input_formats=('%d/%m/%Y',))


class AppUserSearchForm(forms.Form):
    target = AutoCompleteSelectField(label=_(u'User'), lookup_class=AppUserLookup)

class HostSearchForm(forms.Form):
    target = AutoCompleteSelectField(label=_(u'Host'), lookup_class=HostLookup)

class DBSearchForm(forms.Form):
    target = AutoCompleteSelectField(label=_(u'Database'), lookup_class=DBLookup)

class ProfileSearchForm(forms.Form):
    target = AutoCompleteSelectField(label=_(u'Profile'), lookup_class=ProfileLookup)

class HostConnectionSearchForm(forms.Form):
    target = AutoCompleteSelectField(label=_(u'HostConnection'), lookup_class=HostConnectionLookup)


class DBConnectionSearchForm(forms.Form):
    target = AutoCompleteSelectField(label=_(u'DBConnection'), lookup_class=DBConnectionLookup)

class EnvironmentSearchForm(forms.Form):
    target = AutoCompleteSelectField(label=_(u'Environment'), lookup_class=EnvironmentLookup)

class PrivateKeySearchForm(forms.Form):
    target = AutoCompleteSelectField(label=_(u'Private Key'), lookup_class=PrivateKeyLookup)