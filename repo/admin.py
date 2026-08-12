from django.contrib import admin
from .models import Repo, Star, Branch, Commit, Issue, IssueComment, PullRequest, PullRequestComment
# Register your models here.

admin.site.register(Repo)
admin.site.register(Star)
admin.site.register(Branch)
admin.site.register(Commit)
admin.site.register(Issue)
admin.site.register(IssueComment)
admin.site.register(PullRequest)
admin.site.register(PullRequestComment)