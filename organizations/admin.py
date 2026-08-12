from django.contrib import admin

from organizations.models import Organization, OrganizationMember, OrganizationInvitation, Team, TeamMember, TeamRepository

# Register your models here.

admin.site.register(Organization)
admin.site.register(OrganizationMember)
admin.site.register(OrganizationInvitation)
admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(TeamRepository)