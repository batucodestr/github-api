from rest_framework import serializers
from .models import Organization, OrganizationMember, OrganizationInvitation, Team, TeamMember, TeamRepository


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = 'owner','name'

class OrganizationMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMember
        fields = '__all__'

class OrganizationDetailSerializer(serializers.ModelSerializer):
    members = OrganizationMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Organization
        fields = '__all__'


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation
        fields = ['id', 'organization', 'invited_user', 'invited_by', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'organization', 'invited_by', 'status', 'created_at', 'updated_at']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'organization', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'organization', 'created_at']


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ['id', 'team', 'user', 'joined_at']
        read_only_fields = ['id', 'team', 'joined_at']


class TeamRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamRepository
        fields = ['id', 'team', 'repository', 'added_at']
        read_only_fields = ['id', 'team', 'added_at']

