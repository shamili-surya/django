from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import UserProfile
import re

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    mobile_number = serializers.CharField(max_length=15)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'mobile_number', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if re.search(r'[<>\\/?:%$]', value):
            raise serializers.ValidationError("Username contains invalid characters.")
        return value

    def validate_password(self, value):
        if re.search(r'[<>\\/?:%$]', value):
            raise serializers.ValidationError("Password contains invalid characters.")
        return value

    def validate_mobile_number(self, value):
        if not re.fullmatch(r'[6-9]\d{9}', value):
            raise serializers.ValidationError("Enter a valid 10-digit mobile number starting with 6-9.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def create(self, validated_data):
        mobile_number = validated_data.pop('mobile_number')
        email = validated_data.pop('email')
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=email
        )

        # Assign role based on user count
        role = 'admin' if User.objects.count() == 1 else 'user'

        profile = UserProfile.objects.create(user=user, role=role, mobile_number=mobile_number)

        # Add to group using model
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        return user

    def get_role(self, obj):
        try:
            return obj.userprofile.role
        except UserProfile.DoesNotExist:
            return 'unknown'


# ✅ This is required for saving auth_user_groups table entries manually
class UserGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User.groups.through  # Direct reference to auth_user_groups table
        fields = ['user', 'group']
