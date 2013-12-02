# -*- coding: utf-8 -*-
from random import choice
from string import digits, letters
import os
# import re

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
# from django.core.mail import send_mail
from django.template.defaultfilters import filesizeformat
from django.utils import six
from django.utils.encoding import force_text
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from PIL import Image

from user.utils import unique_slugify, resize


class FormMixin(object):
    """This form mixin allow display as_divs and allow adding classes to parent divs."""
    row_classes = {}
    error_css_class = 'error'
    required_css_class = 'required'

    def as_divs(self):
        "Returns this form rendered as HTML <div>s."
        return self._html_output(
            normal_row='<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s%(errors)s</div>',
            error_row='%s',
            row_ender='</div>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=False)

    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        """
        Modified version of BaseForm._hmtl_output.
        Helper function for outputting HTML. Used by as_table(), as_ul(), as_p().
        """
        top_errors = self.non_field_errors()  # Errors that should be displayed above all fields.
        output, hidden_fields = [], []

        for name, field in self.fields.items():
            html_class_attr = ''
            bf = self[name]
            bf_errors = self.error_class([conditional_escape(error) for error in bf.errors])  # Escape and cache in local variable.
            if bf.is_hidden:
                if bf_errors:
                    top_errors.extend(['(Hidden field %s) %s' % (name, force_text(e)) for e in bf_errors])
                hidden_fields.append(six.text_type(bf))
            else:
                # Create a 'class="..."' attribute if the row should have any
                # CSS classes applied.
                extra_classes = self.row_classes.get(name, [])
                css_classes = bf.css_classes(extra_classes)
                if css_classes:
                    html_class_attr = ' class="%s"' % css_classes

                if errors_on_separate_row and bf_errors:
                    output.append(error_row % force_text(bf_errors))

                # Add error class on field in case of field errors
                if bf_errors:
                    bf_classes = bf.field.widget.attrs.get('class', "")
                    bf_classes += ' %s' % self.error_css_class
                    bf.field.widget.attrs.update({'class': bf_classes.strip(), })

                if bf.label:
                    label = conditional_escape(force_text(bf.label))
                    # Only add the suffix if the label does not end in
                    # punctuation.
                    if self.label_suffix:
                        if label[-1] not in ':?.!':
                            label = format_html('{0}{1}', label, self.label_suffix)
                    label = bf.label_tag(label) or ''
                else:
                    label = ''

                if field.help_text:
                    help_text = help_text_html % force_text(field.help_text)
                else:
                    help_text = ''

                output.append(normal_row % {
                    'errors': force_text(bf_errors),
                    'label': force_text(label),
                    'field': six.text_type(bf),
                    'help_text': help_text,
                    'html_class_attr': html_class_attr
                })

        if top_errors:
            output.insert(0, error_row % force_text(top_errors))

        if hidden_fields:  # Insert any hidden fields in the last row.
            str_hidden = ''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                if not last_row.endswith(row_ender):
                    # This can happen in the as_p() case (and possibly others
                    # that users write): if there are only top errors, we may
                    # not be able to conscript the last row for our purposes,
                    # so insert a new, empty row.
                    last_row = (normal_row % {'errors': '', 'label': '',
                                              'field': '', 'help_text': '',
                                              'html_class_attr': html_class_attr})
                    output.append(last_row)
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)
        return mark_safe('\n'.join(output))


class CustomAuthenticationForm(FormMixin, AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        label=_("Email"),
        widget=forms.TextInput(attrs={'placeholder': _('email')}))
    password = forms.CharField(
        label=_('password'),
        widget=forms.PasswordInput(attrs={'placeholder': _('password')}))

    row_classes = {
        'username': ['form__field--email', ],
        'password': ['form__field--password', ],
    }


class CustomPasswordResetForm(FormMixin, PasswordResetForm):
    row_classes = {
        'email': ['form__field--email', ],
    }


#  =================
#  = BaseUser forms =
#  =================
class BaseUserCreationForm(FormMixin, forms.Form):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    row_classes = {
        'email': ['form__field--email', ],
        'password1': ['form__field--password', ],
        'password2': ['form__field--password', ],
    }

    email = forms.EmailField(
        label=_("Email"),
        max_length=30,)
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput,
        error_messages={
            'invalid': _("Enter the same password as above, for verification.")})
    fb_token = forms.CharField(
        required=False,
        widget=forms.HiddenInput)
    fb_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', None)
        self.user_class = get_user_model()
        super(BaseUserCreationForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        # Since user.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See Django's issue #13147.
        email = self.cleaned_data["email"]
        try:
            self.user_class.objects.get(email=email)
        except self.user_class.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self):
        email = self.cleaned_data.get('email')
        slug_name = email.split('@')[0]
        slug = unique_slugify(slug_name, self.user_class)
        user_data = {
            'email': email,
            'name': slug,
            'slug': slug,
            'password': self.cleaned_data.get('password1'),
            'fb_token': self.cleaned_data.get('fb_token'),
            'fb_id': self.cleaned_data.get('fb_id'),
        }
        user = self.user_class.objects.create_user(**user_data)
        return user


#  ==============================
#  = Common forms for all users =
#  ==============================
class BaseUserEditionForm(FormMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('name', '_avatar', 'email')

    error_messages = {
        'image_error': _(u"Impossible de redimentionner l'avatar."),
        'image_too_big': _(u"Taille maximale autorisée: {size}. Taille de l'image: {{file_size}}".format(size=filesizeformat(settings.MAX_UPLOAD_SIZE))),
    }

    row_classes = {
        'name': ['form__field--text', ],
        'email': ['form__field--email', ],
        '_avatar': ['form__field--avatar', ],
    }

    def save(self, commit=False, *args, **kwargs):
        super(BaseUserEditionForm, self).save(commit, *args, **kwargs)
        if not self.instance.id or self.change_name:
            self.instance.slug = unique_slugify(self.instance.name, get_user_model(), name=self.instance.name)
        self.instance.save()
        # save small avatar
        if self.small_avatar:
            #Save SimpleUploadedFile into image field
            self.instance._small_avatar.save('%s_small.%s' % (os.path.splitext(self.small_avatar.name)[0], self.small_avatar_ext), self.small_avatar)
            self.instance.save()
        self.save_m2m()
        return self.instance

    def clean_name(self):
        name = self.cleaned_data.get('name')
        self.change_name = not name == self.instance.name
        return name

    def clean__avatar(self):
        avatar = self.cleaned_data.get('_avatar')
        self.small_avatar = None
        if avatar and isinstance(avatar, UploadedFile):
            # Check file size
            if avatar._size > settings.MAX_UPLOAD_SIZE:
                raise forms.ValidationError(self.error_messages['image_too_big'].format(file_size=filesizeformat(avatar._size)))
            # Generate name
            avatar.name = "".join(choice(digits + letters) for i in range(30)) + os.path.splitext(avatar.name)[1]
            # Resize avatar
            try:
                im = Image.open(avatar.file)
            except IOError:
                raise forms.ValidationError(self.error_messages['image_error'])
            else:
                IMG_TYPE = os.path.splitext(avatar.name)[1].strip('.')
                if IMG_TYPE in ('jpeg', 'jpg'):
                    FILE_EXTENSION = 'jpeg'
                elif IMG_TYPE == 'png':
                    FILE_EXTENSION = 'png'
                elif IMG_TYPE == 'gif':
                    FILE_EXTENSION = 'gif'
                else:
                    return
                # Create big avatar
                avatar.file = resize(im, settings.AVATAR_SIZE, FILE_EXTENSION)
                # Create small avatar
                small_avatar = resize(im, settings.AVATAR_SMALLSIZE, FILE_EXTENSION)
                #Save image to a SimpleUploadedFile which can be saved into an ImageField
                self.small_avatar = SimpleUploadedFile(os.path.split(avatar.name)[-1], small_avatar.read(), content_type=IMG_TYPE)
                self.small_avatar_ext = FILE_EXTENSION
        return avatar


class BaseUserDeleteForm(forms.Form):
    password = forms.CharField(
        label=_(u'Mot de passe'),
        widget=forms.PasswordInput)

    error_messages = {
        'invalid_password': _(u'Mot de passe incorrect.')
    }

    def is_valid(self, user, *args, **kwargs):
        self.user = user
        return super(BaseUserDeleteForm, self).is_valid(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        is_users_password = self.user.check_password(password)
        if password and not is_users_password:
            raise forms.ValidationError(self.error_messages['invalid_password'])
        return password


# class ContactForm(forms.Form):
#     email = forms.EmailField()
#     name = forms.CharField(label=_(u'Nom'))
#     message = forms.CharField(widget=forms.Textarea())

#     def send_mail(self):
#         cd = self.cleaned_data
#         send_mail(
#             u'%s %s vous a contacté.' % (settings.EMAIL_SUBJECT_PREFIX, cd.get('name')),
#             cd.get('message'),
#             cd.get('email'),
#             settings.EMAIL_TO,
#         )
