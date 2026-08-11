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