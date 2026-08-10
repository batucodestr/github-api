from rest_framework import serializers
from .models import Repo

class RepoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repo
        fields = ['id', 'name',  'description' ,'owner', 'default_branch', 'is_fork', 'fork_parent']
        read_only_fields = ['id', 'owner', 'description']

class RepoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repo
        fields = ['id', 'name', 'description', 'owner', 'visibility', 'default_branch', 'license', 'is_fork', 'fork_parent', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

