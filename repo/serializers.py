from rest_framework import serializers

from users.serializers import UserDetailSerializer
from .models import (
    Repo,
    Star,
    Branch,
    Commit,
    Issue,
    IssueComment,
    PullRequest,
    PullRequestComment,
)


class RepoSerializer(serializers.ModelSerializer):
    stars_count = serializers.IntegerField(source='stars.count', read_only=True)

    class Meta:
        model = Repo
        fields = ['id', 'name', 'description', 'owner', 'organization', 'default_branch', 'is_fork', 'fork_parent', 'stars_count']
        read_only_fields = ['id', 'owner', 'organization', 'description', 'is_fork', 'fork_parent']


class RepoDetailSerializer(serializers.ModelSerializer):
    stars_count = serializers.IntegerField(source='stars.count', read_only=True)
    forks_count = serializers.IntegerField(source='forks.count', read_only=True)

    class Meta:
        model = Repo
        fields = [
            'id', 'name', 'description', 'owner', 'organization', 'visibility', 'default_branch',
            'license', 'is_fork', 'fork_parent', 'stars_count', 'forks_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'organization', 'created_at', 'updated_at', 'is_fork', 'fork_parent']


class StarSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = Star
        fields = ['id', 'user', 'repository', 'created_at']
        read_only_fields = ['id', 'user', 'repository', 'created_at']


class StarredRepoSerializer(serializers.ModelSerializer):
    repository = RepoSerializer(read_only=True)

    class Meta:
        model = Star
        fields = ['id', 'repository', 'created_at']


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'repository', 'name', 'is_default', 'created_at']
        read_only_fields = ['id', 'repository', 'is_default', 'created_at']


class CommitSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)

    class Meta:
        model = Commit
        fields = ['id', 'repository', 'branch', 'author', 'message', 'hash', 'created_at']
        read_only_fields = ['id', 'repository', 'author', 'hash', 'created_at']


class IssueCommentSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)

    class Meta:
        model = IssueComment
        fields = ['id', 'issue', 'author', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'issue', 'author', 'created_at', 'updated_at']


class IssueSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = ['id', 'repository', 'author', 'title', 'body', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'repository', 'author', 'status', 'created_at', 'updated_at']


class IssueDetailSerializer(IssueSerializer):
    comments = IssueCommentSerializer(many=True, read_only=True)

    class Meta(IssueSerializer.Meta):
        fields = IssueSerializer.Meta.fields + ['comments']


class PullRequestCommentSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)

    class Meta:
        model = PullRequestComment
        fields = ['id', 'pull_request', 'author', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'pull_request', 'author', 'created_at', 'updated_at']


class PullRequestSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)

    class Meta:
        model = PullRequest
        fields = [
            'id', 'repository', 'author', 'source_branch', 'target_branch',
            'title', 'body', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'repository', 'author', 'status', 'created_at', 'updated_at']

    def validate(self, attrs):
        source_branch = attrs.get('source_branch') or getattr(self.instance, 'source_branch', None)
        target_branch = attrs.get('target_branch') or getattr(self.instance, 'target_branch', None)

        if source_branch and target_branch:
            if source_branch.repository_id != target_branch.repository_id:
                raise serializers.ValidationError(
                    "Kaynak ve hedef dal aynı depoya ait olmalıdır."
                )
            if source_branch.id == target_branch.id:
                raise serializers.ValidationError(
                    "Kaynak ve hedef dal aynı olamaz."
                )
        return attrs


class PullRequestDetailSerializer(PullRequestSerializer):
    comments = PullRequestCommentSerializer(many=True, read_only=True)

    class Meta(PullRequestSerializer.Meta):
        fields = PullRequestSerializer.Meta.fields + ['comments']
