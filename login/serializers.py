from rest_framework import serializers
from django.contrib.auth import get_user_model
import re
from .models import Mail, MailRecipient  
User = get_user_model()

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

        # Assign role 'admin' if first user, else 'user'
        role = 'admin' if User.objects.count() == 0 else 'user'

        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=email,
            role=role,
            mobile_number=mobile_number
        )
        return user

    def get_role(self, obj):
        return obj.role if hasattr(obj, 'role') else 'unknown'


class UserGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User.groups.through  # Intermediate table model for user-group relations
        fields = ['customuser', 'group']  # use 'customuser' instead of 'user'

class MailRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailRecipient
        fields = ['user', 'recipient_type']

class MailSerializer(serializers.ModelSerializer):
    to = serializers.ListField(child=serializers.EmailField(), write_only=True)
    cc = serializers.ListField(child=serializers.EmailField(), write_only=True, required=False)
    bcc = serializers.ListField(child=serializers.EmailField(), write_only=True, required=False)

    class Meta:
        model = Mail
        fields = ['id', 'subject', 'body', 'to', 'cc', 'bcc', 'is_draft', 'created_at', 'sent_at']

    def create(self, validated_data):
        sender = self.context['request'].user
        to_emails = validated_data.pop('to', [])
        cc_emails = validated_data.pop('cc', [])
        bcc_emails = validated_data.pop('bcc', [])

        mail = Mail.objects.create(sender=sender, **validated_data)

        for email, r_type in [(to_emails, 'to'), (cc_emails, 'cc'), (bcc_emails, 'bcc')]:
            for addr in email:
                try:
                    user = User.objects.get(email=addr)
                    MailRecipient.objects.create(mail=mail, user=user, recipient_type=r_type)
                except User.DoesNotExist:
                    continue  # Skip invalid emails

        return mail