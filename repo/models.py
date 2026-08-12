import secrets

from django.db import models

# Create your models here.
repo_visibility_choices = [
    ('public', 'Public'),
    ('private', 'Private'),
]


class Repo(models.Model):
    owner = models.ForeignKey(
            'users.CustomUser',
            on_delete=models.CASCADE,
            related_name='repos',
            blank=True,
            null=True,)   
     
    organization = models.ForeignKey('organizations.Organization', 
                                     on_delete=models.CASCADE, 
                                     related_name='repos', 
                                     blank=True, null=True)
    
    visibility = models.CharField(max_length=10, 
                                  choices=repo_visibility_choices, 
                                  default='public')
    
    default_branch = models.CharField(
        max_length=255, 
        default='main')

    license = models.CharField(
        max_length=255, 
        blank=True, 
        null=True)

    is_fork = models.BooleanField(default=False)

    fork_parent = models.ForeignKey('self', 
                                    on_delete=models.SET_NULL, 
                                    blank=True, null=True, 
                                    related_name='forks')
    name = models.CharField(max_length=255)

    description = models.TextField(
        blank=True, 
        null=True)

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(owner__isnull=False, organization__isnull=True)
                    | models.Q(owner__isnull=True, organization__isnull=False)
                ),
                name='repo_has_one_owner'
            ),
        ]

    def __str__(self):
        return self.name


class Star(models.Model):
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='stars')

    repository = models.ForeignKey(
        Repo,
        on_delete=models.CASCADE,
        related_name='stars')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'repository'],
                name='unique_star_per_user_repo',
            ),
        ]

    def __str__(self):
        return f"{self.user} starred {self.repository}"


class Branch(models.Model):
    repository = models.ForeignKey(
        Repo,
        on_delete=models.CASCADE,
        related_name='branches')

    name = models.CharField(max_length=255)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['repository', 'name'],
                name='unique_branch_name_per_repo',
            ),
        ]

    def __str__(self):
        return f"{self.repository}:{self.name}"


class Commit(models.Model):
    repository = models.ForeignKey(
        Repo,
        on_delete=models.CASCADE,
        related_name='commits')

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='commits')

    author = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='commits')

    message = models.TextField()

    hash = models.CharField(max_length=40, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.hash:
            self.hash = secrets.token_hex(20)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hash[:7]} - {self.message[:50]}"


issue_status_choices = [
    ('open', 'Open'),
    ('closed', 'Closed'),
]


class Issue(models.Model):
    repository = models.ForeignKey(
        Repo,
        on_delete=models.CASCADE,
        related_name='issues')

    author = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='issues')

    title = models.CharField(max_length=255)

    body = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=10, choices=issue_status_choices, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class IssueComment(models.Model):
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='comments')

    author = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='issue_comments')

    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.issue}"


pull_request_status_choices = [
    ('open', 'Open'),
    ('closed', 'Closed'),
    ('merged', 'Merged'),
]


class PullRequest(models.Model):
    repository = models.ForeignKey(
        Repo,
        on_delete=models.CASCADE,
        related_name='pull_requests')

    author = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='pull_requests')

    source_branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='source_pull_requests')

    target_branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='target_pull_requests')

    title = models.CharField(max_length=255)

    body = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=10, choices=pull_request_status_choices, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PullRequestComment(models.Model):
    pull_request = models.ForeignKey(
        PullRequest,
        on_delete=models.CASCADE,
        related_name='comments')

    author = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='pull_request_comments')

    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.pull_request}"