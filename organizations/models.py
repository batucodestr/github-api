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


invitation_status_choices = [
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
]


class OrganizationInvitation(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    invited_user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='organization_invitations')
    invited_by = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='sent_invitations')
    status = models.CharField(max_length=10, choices=invitation_status_choices, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'invited_user'],
                condition=models.Q(status='pending'),
                name='unique_pending_invitation_per_user_org',
            ),
        ]

    def __str__(self):
        return f"{self.invited_user} -> {self.organization} ({self.status})"


class Team(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_team_name_per_organization',
            ),
        ]

    def __str__(self):
        return f"{self.organization.name}/{self.name}"


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='team_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')

    def __str__(self):
        return f"{self.user} in {self.team}"


class TeamRepository(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='repositories')
    repository = models.ForeignKey('repo.Repo', on_delete=models.CASCADE, related_name='team_access')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'repository')

    def __str__(self):
        return f"{self.team} -> {self.repository}"