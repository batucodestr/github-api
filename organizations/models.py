from django.db import models
# Create your models here.

role_choices = [
    ('admin', 'Admin'),
    ('member', 'Member'),
]


'''
Organization
------------
id
owner (FK -> User)
name
display_name
description
avatar
website
location
created_at
updated_at
'''

class Organization(models.Model):
    owner = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='organizations')
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='organization_avatars/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


'''
OrganizationMember
------------------
organization (FK)
user (FK)
role
joined_at
'''

class OrganizationMember(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='organization_memberships')
    role = models.CharField(max_length=50, choices=role_choices, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"