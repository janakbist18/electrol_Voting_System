from __future__ import annotations

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Election, Candidate, Constituency, Party, VoterProfile, ResultTally

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        email = validated_data["email"].lower()
        user = User.objects.create_user(username=email, email=email, password=validated_data["password"])
        return user

class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ["id", "title", "description", "start_at", "end_at", "status"]

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ["id", "name_en", "name_np", "abbreviation", "symbol_text"]

class ConstituencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Constituency
        fields = ["id", "name", "code", "election_id"]

class CandidateSerializer(serializers.ModelSerializer):
    party = PartySerializer()
    constituency = ConstituencySerializer()
    class Meta:
        model = Candidate
        fields = ["id", "full_name_en", "full_name_np", "party", "constituency"]

class VoteSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField()

class ResultRowSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField()
    party = serializers.CharField()
    votes = serializers.IntegerField()

class ResultsSerializer(serializers.Serializer):
    election_id = serializers.IntegerField()
    constituency_id = serializers.IntegerField()
    rows = ResultRowSerializer(many=True)

class VoterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoterProfile
        fields = ["citizenship_id", "phone", "is_verified", "constituency"]
        read_only_fields = ["is_verified"]