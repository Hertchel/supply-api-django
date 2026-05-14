import pyotp
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
from .models import FundCluster, Office
# Serializers for the API endpoints, including user registration, login, and data representation for various models.
from .groups import assign_role_and_save
from .models import *

from .models import CustomUser

from .models import (
    Item,
    Supplier,
    SupplierItem,
    AbstractOfQuotation
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "first_name", "last_name", "email"]


class CreateUserSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    role = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('employee_id', 'first_name', 'last_name', 'role', 'email', 'password', 'password2')
        extra_kwargs = {'password': {'write_only': True}, 'password2': {'write_only': True}}

    def validate(self, attrs):
        print('validated')
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Password fields didnt match.'})
        return attrs

    def create(self, validated_data):
        # employee_id = validated_data.pop('employee_id')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        role = validated_data.pop('role')
        role_map = {
            "Supply Officer": "supply",
            "BAC Officer": "bac",
            "Requisitioner": "requisitioner"
        }

        role = role_map.get(role, role)
        if role.lower() == "supply":
            prefix = "Supply"

        elif role.lower() == "bac":
            prefix = "BAC"

        elif role.lower() == "requisitioner":
            prefix = "Req"

        else:
            prefix = "EMP"
        existing_users = CustomUser.objects.filter(
            role=role.lower(),
            employee_id__startswith=f"{prefix}-"
        )

        highest_number = 0

        for user_obj in existing_users:
            try:
                number_part = int(user_obj.employee_id.split("-")[1])
                highest_number = max(highest_number, number_part)
            except:
                pass

        employee_id = f"{prefix}-{highest_number + 1}"
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create(employee_id=employee_id, first_name=first_name, last_name=last_name, email=email, password=password)
        user.is_active = not settings.IS_USER_ACTIVATION_ENABLED

        # generate secret after registration
        user.otp_secret = pyotp.random_base32()
        print(f'otp secret created: {user.otp_secret}')
        user.set_password(password)
        user.role = role

        # assign the role and save the user
        assign_role_and_save(user, role)
        if role.lower() == "requisitioner":
            Requesitioner.objects.create(
                user=user,
                name=f"{user.first_name} {user.last_name}",
            )
        return user

class CustomUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_email(self, value):
        if CustomUser.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = '__all__'
    def get_role(self, obj):
        # This method retrieves the group names as a comma-separated string
        return ', '.join(obj.groups.values_list('name', flat=True))

class LoginTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        # Get the standard token
        token = super().get_token(user)

        # Add custom claims
        role = user.groups.first()  # Get the user's first group (role)
        token['role'] = role.name if role else None  # Add role to the token
        token['email'] = user.email  # Add email to the token

        return token

    
class RecentActivitySerializer(serializers.ModelSerializer):
    content_type = serializers.StringRelatedField()
    user = serializers.StringRelatedField()

    class Meta:
        model = RecentActivity
        fields = ['id', 'user', 'user_role', 'activity_type', 'timestamp', 'content_type', 'object_id']
        

class TrackStatusSerializer(serializers.ModelSerializer):
    
    class Meta: 
        model = TrackStatus
        fields = '__all__'


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class CampusDirectorSerializer(serializers.ModelSerializer):
    
    class Meta: 
        model = CampusDirector
        fields = '__all__'



class RequesitionerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Requesitioner
        fields = '__all__'

# The FundClusterSerializer and OfficeSerializer are added to provide structured data representation for the FundCluster and Office models, which can be used in API responses and requests to ensure consistency and clarity when dealing with fund clusters and offices in the context of purchase requests.
class FundClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundCluster
        fields = ['id', 'code', 'name', 'description']


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'code', 'name', 'department']

class RequisitionerItemSerializer(serializers.ModelSerializer):

    class Meta:

        model = Item

        fields = [
            'item_no',
            'item_description',
            'quantity',
            'unit',
            'unit_cost',
            'total_cost'
        ]
class PurchaseRequestSerializer(serializers.ModelSerializer):

    requisitioner = serializers.PrimaryKeyRelatedField(
        queryset=Requesitioner.objects.all()
    )

    requisitioner_details = RequesitionerSerializer(
        source='requisitioner',
        read_only=True
    )

    campus_director = serializers.PrimaryKeyRelatedField(
        queryset=CampusDirector.objects.all()
    )

    campus_director_details = CampusDirectorSerializer(
        source='campus_director',
        read_only=True
    )

    fund_cluster = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    office = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all()
    )

    office_details = OfficeSerializer(
        source='office',
        read_only=True
    )

    reviewed_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    reviewed_by_details = serializers.SerializerMethodField()

    items = serializers.SerializerMethodField()

    supplier_name = serializers.SerializerMethodField()

    winning_bidder = serializers.SerializerMethodField()

    class Meta:

        model = PurchaseRequest

        fields = [
            'pr_no',
            'res_center_code',
            'fund_cluster',
            'office',
            'office_details',
            'purpose',
            'status',
            'requisitioner',
            'requisitioner_details',
            'reviewed_by',
            'reviewed_by_details',
            'campus_director',
            'campus_director_details',
            'mode_of_procurement',
            'total_amount',
            'created_at',
            'updated_at',

            # NEW
            'items',
            'supplier_name',
            'winning_bidder'
        ]

    def get_reviewed_by_details(self, obj):

        if obj.reviewed_by:

            return {
                "id": obj.reviewed_by.id,
                "name":
                f"{obj.reviewed_by.first_name} "
                f"{obj.reviewed_by.last_name}",
                "email": obj.reviewed_by.email
            }

        return None

    def get_items(self, obj):

        items = Item.objects.filter(
            purchase_request=obj
        )

        return RequisitionerItemSerializer(
            items,
            many=True
        ).data

    def get_supplier_name(self, obj):

        supplier_item = SupplierItem.objects.filter(
            rfq__purchase_request=obj
        ).first()

        if supplier_item and supplier_item.supplier:
            return supplier_item.supplier.name

        return None

    def get_winning_bidder(self, obj):

        aoq = AbstractOfQuotation.objects.filter(
            purchase_request=obj
        ).first()

        if not aoq:
            return None

        supplier_item = SupplierItem.objects.filter(
            supplier__aoq=aoq
        ).first()

        if supplier_item and supplier_item.supplier:
            return supplier_item.supplier.name

        return None
        
class ItemSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    class Meta:
        model = Item
        fields = '__all__'
        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
        }
        

class RequestForQuotationSerializer(serializers.ModelSerializer):

    class Meta:
        model = RequestForQuotation
        fields = '__all__'


class ItemQuotationSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), write_only=True)
    item_details = ItemSerializer(source='item', read_only=True)
    
    class Meta:
        model = ItemQuotation
        fields = '__all__'
        extra_kwargs = {
            'item': {'write_only': True},
            'item_details': {'read_only': True}
        }


class AbstractOfQuotationSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    class Meta:
        model = AbstractOfQuotation
        fields = '__all__'
        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
        }


class BACMemberSerializer(serializers.ModelSerializer):

    class Meta:
        model = BACMember
        fields = '__all__' 


class SupplierSerializer(serializers.ModelSerializer):
    aoq = serializers.PrimaryKeyRelatedField(queryset=AbstractOfQuotation.objects.all(), write_only=True)
    aoq_details = AbstractOfQuotationSerializer(source='aoq', read_only=True)

    rfq = serializers.PrimaryKeyRelatedField(queryset=RequestForQuotation.objects.all(), write_only=True)
    rfq_details = RequestForQuotationSerializer(source='rfq', read_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'
        extra_kwargs = {
            'aoq': {'write_only': True},
            'aoq_details': {'read_only': True},
            'rfq': {'write_only': True},
            'rfq_details': {'read_only': True},
        }


class SupplierItemSerializer(serializers.ModelSerializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all(), write_only=True)
    supplier_details = SupplierSerializer(source='supplier', read_only=True)

    rfq = serializers.PrimaryKeyRelatedField(queryset=RequestForQuotation.objects.all(), write_only=True)
    rfq_details = RequestForQuotationSerializer(source='rfq', read_only=True)

    item_quotation = serializers.PrimaryKeyRelatedField(queryset=ItemQuotation.objects.all(), write_only=True)
    item_quotation_details = ItemQuotationSerializer(source='item_quotation', read_only=True)

    class Meta:
        model = SupplierItem
        fields = '__all__'
        extra_kwargs = {
            'supplier': {'write_only': True},
            'supplier_details': {'read_only': True},
            'rfq': {'write_only': True},
            'rfq_details': {'read_only': True},
            'item_quotation': {'write_only': True},
            'item_quotation_details': {'read_only': True},
        }


class PurchaseOrderSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    request_for_quotation = serializers.PrimaryKeyRelatedField(queryset=RequestForQuotation.objects.all(), write_only=True)
    rfq_details = RequestForQuotationSerializer(source='request_for_quotation', read_only=True)

    abstract_of_quotation = serializers.PrimaryKeyRelatedField(queryset=AbstractOfQuotation.objects.all(), write_only=True)
    aoq_details = AbstractOfQuotationSerializer(source='abstract_of_quotation', read_only=True)

    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all(), write_only=True)
    supplier_details = SupplierSerializer(source='supplier', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
            'request_for_quotation': {'write_only': True},
            'rfq_details': {'read_only': True},
            'abstract_of_quotation': {'write_only': True},
            'aoq_details': {'read_only': True},
            'supplier': {'write_only': True},
            'supplier_details': {'read_only': True},
        }
        

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    purchase_order = serializers.PrimaryKeyRelatedField(queryset=PurchaseOrder.objects.all(), write_only=True)
    po_details = PurchaseOrderSerializer(source='purchase_order', read_only=True)
    
    supplier_item = serializers.PrimaryKeyRelatedField(queryset=SupplierItem.objects.all(), write_only=True)
    supplier_item_details = SupplierItemSerializer(source='supplier_item', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'
        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
            'purchase_order': {'write_only': True},
            'po_details': {'read_only': True},
            'supplier_item': {'write_only': True},
            'supplier_item_details': {'read_only': True},
        }


class InspectionAndAcceptanceSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    purchase_order = serializers.PrimaryKeyRelatedField(queryset=PurchaseOrder.objects.all(), write_only=True)
    po_details = PurchaseOrderSerializer(source='purchase_order', read_only=True)
    
    class Meta:
        model = InspectionAndAcceptance
        fields = '__all__'
        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
            'purchase_order': {'write_only': True},
            'po_details': {'read_only': True},
        }


class DeliveredItemsSerializer(serializers.ModelSerializer):
    purchase_request = serializers.PrimaryKeyRelatedField(queryset=PurchaseRequest.objects.all(), write_only=True)
    pr_details = PurchaseRequestSerializer(source='purchase_request', read_only=True)

    inspection = serializers.PrimaryKeyRelatedField(queryset=InspectionAndAcceptance.objects.all(), write_only=True)
    inspection_details = InspectionAndAcceptanceSerializer(source='inspection', read_only=True)

    supplier_item = serializers.PrimaryKeyRelatedField(queryset=SupplierItem.objects.all(), write_only=True)
    item_details = SupplierItemSerializer(source='supplier_item', read_only=True)

    class Meta:
        model = DeliveredItems
        fields = '__all__'
        extra_kwargs = {
            'purchase_request': {'write_only': True},
            'pr_details': {'read_only': True},
            'inspection': {'write_only': True},
            'inspection_details': {'read_only': True},
            'supplier_item': {'write_only': True},
            'item_details': {'read_only': True}
        }


class StockItemsSerializer(serializers.ModelSerializer):
    inspection = serializers.PrimaryKeyRelatedField(queryset=InspectionAndAcceptance.objects.all(), write_only=True)
    inspection_details = InspectionAndAcceptanceSerializer(source='inspection', read_only=True)

    supplier_item = serializers.PrimaryKeyRelatedField(queryset=SupplierItem.objects.all(), write_only=True)
    item_details = SupplierItemSerializer(source='supplier_item', read_only=True)

    class Meta:
        model = StockItems
        fields = '__all__'
        extra_kwargs = {
            'inspection': {'write_only': True},
            'inspection_details': {'read_only': True},
            'supplier_item': {'write_only': True},
            'item_details': {'read_only': True}
        }


class RequisitionIssueSlipSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequisitionIssueSlip
        fields = '__all__'

class RequestForQuotationDetailSerializer(serializers.ModelSerializer):
    items = ItemQuotationSerializer(source="item_quotations", many=True, read_only=True)

    class Meta:
        model = RequestForQuotation
        fields = '__all__'