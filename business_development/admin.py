from django.contrib import admin
from .models import Interaction, Opportunity, Partner, Prospect

admin.site.register([Partner, Prospect, Opportunity, Interaction])
