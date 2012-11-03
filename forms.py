from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36
from django.template import Context, loader
from django import forms
from django.core.mail import send_mail
from django.conf import settings

class UserCreationForm( forms.ModelForm ):
    username = forms.RegexField( 
        label = "Username",
        max_length = 30,
        regex = r'^[\w.+-]+$',
        help_text = "Required. 30 characters or fewer. Letters, digits and /./+/-/_ only.",
        error_messages = {'invalid': "This value may contain only letters, numbers and /./+/-/_ characters."}
    )
    password = forms.CharField( 
        label = "Password",
        widget = forms.PasswordInput
    )
    email = forms.EmailField( 
        label = "Email",
        max_length = 75
    )

    class Meta:
        model = User
        fields = ( "username", )

    def clean_email( self ):
        email = self.cleaned_data["email"]
        users_found = User.objects.filter( email__iexact = email )
        if len( users_found ) >= 1:
            raise forms.ValidationError( "A user with that email already exist." )
        return email

    def save( self, commit = True, domain_override = None,
             email_template_name = 'registration/signup_email.html',
             use_https = False, token_generator = default_token_generator ):

        user = super( UserCreationForm, self ).save( commit = False )
        user.set_password( self.cleaned_data["password"] )
        user.email = self.cleaned_data["email"]
        user.is_active = False

        if commit:
            user.save()
        if not domain_override:
            current_site = Site.objects.get_current()
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        t = loader.get_template( email_template_name )

        c = {
            'email': user.email,
            'domain': domain,
            'site_name': site_name,
            'uid': int_to_base36( user.id ),
            'user': user,
            'token': token_generator.make_token( user ),
            'protocol': use_https and 'https' or 'http',
        }

        if settings.IN_PRODUCTION:
            # send email
            send_mail( 
                "Confirmation link sent on %s" % site_name,
                t.render( Context( c ) ),
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )

        return user
