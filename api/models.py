import pyotp
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class CustomUserManager(BaseUserManager):

    def create(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create(email, password, **extra_fields)


class CustomUser(AbstractUser):
    employee_id = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    is_active = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=10, null=True, blank=True)
    otp_expiration = models.DateTimeField(null=True, blank=True)
    otp_secret = models.CharField(max_length=32, null=True, blank=True)

    objects = CustomUserManager()

    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def generate_otp(self):
        totp = pyotp.TOTP(self.otp_secret)
        self.otp_code = totp.now()
        self.otp_expiration = timezone.now() + timezone.timedelta(minutes=5)
        self.save()
        return self.otp_code

    def verify_otp(self, otp_code):
        if self.otp_code == otp_code and timezone.now() < self.otp_expiration:
            self.otp_code = None
            self.otp_expiration = None
            self.save()
            return True
        return False


class RecentActivity(models.Model):
    ACTIVITY_TYPES = (
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_role = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} {self.get_activity_type_display()} {self.content_type}"


class Requesitioner(models.Model):
    requisition_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=50)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)


class CampusDirector(models.Model):
    cd_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class PurchaseRequest(models.Model):
    pr_no = models.CharField(max_length=50, primary_key=True)
    res_center_code = models.CharField(max_length=50, null=True, blank=True)
    office = models.CharField(max_length=200)
    # fund_cluster = models.CharField(max_length=50, null=True, blank=True)
    purpose = models.CharField(max_length=255)
    status = models.CharField(max_length=255, default='Pending for Approval')
    requisitioner = models.ForeignKey(Requesitioner, related_name="purchase_requests", on_delete=models.CASCADE)
    campus_director = models.ForeignKey(CampusDirector, related_name="purchase_requests", on_delete=models.CASCADE)
    mode_of_procurement = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    reviewed_by = models.ForeignKey(
    Requesitioner,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='reviewed_requests'
)

#    fund_cluster = models.ForeignKey(
#        'FundCluster', 
#        on_delete=models.SET_NULL, 
#        null=True, 
#        blank=True,
#        related_name='purchase_requests'
#    )
    
    office = models.ForeignKey(
        'Office',  
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='purchase_requests'
    )

    STATUS_DESCRIPTIONS = {
        "Pending for Approval": "The purchase request has been submitted and is awaiting review and approval.",
        "Approved": "The purchase request has been reviewed and approved for further processing.",
        "Rejected": "The purchase request has been reviewed and denied.",
        "Cancelled": "The purchase request has been cancelled.",
        "Forwarded to Procurement": "The purchase request has been forwarded to the procurement team.",
        "Received by the Procurement": "Procurement acknowledged receipt and will process it.",
        "Ready to Order": "Approved and ready for supplier order.",
        "Order Placed": "Order successfully placed with the supplier.",
        "Items Delivered": "Ordered items have been delivered.",
        "Ready for Distribution": "Items ready for distribution.",
        "Completed": "Process successfully completed.",
    }

    def __str__(self):
        return self.pr_no

    def get_status_description(self):
        return self.STATUS_DESCRIPTIONS.get(self.status, "Unknown status.")


class TrackStatus(models.Model):
    pr_no = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=150)
    description = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pr_no} - {self.status}"


class Item(models.Model):
    item_no = models.CharField(max_length=50, primary_key=True)
    purchase_request = models.ForeignKey(PurchaseRequest, related_name="items", on_delete=models.CASCADE)
    stock_property_no = models.CharField(max_length=20)
    unit = models.CharField(max_length=255)
    item_description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_description

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)


class RequestForQuotation(models.Model):
    rfq_no = models.CharField(max_length=50, primary_key=True)
    supplier_name = models.CharField(max_length=255)
    supplier_address = models.CharField(max_length=255)
    tin = models.CharField(max_length=50, null=True, blank=True)
    is_vat = models.BooleanField(default=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='quotations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Quotation: {self.rfq_no}'


class ItemQuotation(models.Model):
    item_quotation_no = models.CharField(max_length=50, primary_key=True)
    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.CASCADE, related_name='item_quotations')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='item_quotations')
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    brand_model = models.CharField(max_length=255)
    is_low_price = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Item Quotation: {self.rfq.rfq_no}'
    
    @property
    def purchase_request(self):
        return self.item.purchase_request


class AbstractOfQuotation(models.Model):
    aoq_no = models.CharField(max_length=50, primary_key=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='abstracts')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Abstract of Quotation for {self.purchase_request.pr_no}'


class Supplier(models.Model):
    supplier_no = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_person = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    tin = models.CharField(max_length=50)
    aoq = models.ForeignKey(AbstractOfQuotation, on_delete=models.CASCADE, related_name='suppliers', null=True, blank=True)
    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.CASCADE, related_name='suppliers')
    is_added = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SupplierItem(models.Model):
    supplier_item_no = models.CharField(max_length=50, primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplier_items')
    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.CASCADE, related_name='supplier_items')
    item_quotation = models.ForeignKey(ItemQuotation, on_delete=models.CASCADE, related_name='supplier_items')
    item_quantity = models.PositiveIntegerField()
    item_cost = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.supplier_item_no

    def save(self, *args, **kwargs):
        self.total_amount = self.item_quantity * self.item_cost
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    po_no = models.CharField(max_length=50, primary_key=True)
    status = models.CharField(max_length=150, default="In Progress")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='purchase_orders')
    request_for_quotation = models.ForeignKey(RequestForQuotation, on_delete=models.CASCADE, related_name='purchase_orders')
    abstract_of_quotation = models.ForeignKey(AbstractOfQuotation, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.po_no


class PurchaseOrderItem(models.Model):
    po_item_no = models.CharField(max_length=50, primary_key=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='po_items')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='po_items')
    supplier_item = models.ForeignKey(SupplierItem, on_delete=models.CASCADE, related_name='po_items')
    quantity_ordered = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.po_item_no


class InspectionAndAcceptance(models.Model):
    inspection_no = models.CharField(max_length=50, primary_key=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='inspections')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='inspections')
    inspection_date = models.DateTimeField(auto_now_add=True)
    inspector_name = models.CharField(max_length=255)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.inspection_no


class DeliveredItems(models.Model):
    delivery_id = models.CharField(max_length=50, primary_key=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='deliveries')
    inspection = models.ForeignKey(InspectionAndAcceptance, on_delete=models.CASCADE, related_name='delivered_items')
    supplier_item = models.ForeignKey(SupplierItem, on_delete=models.CASCADE, related_name='deliveries')
    quantity_delivered = models.PositiveIntegerField()
    date_received = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=True)
    is_partial = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.purchase_request.pr_no} - {self.delivery_id}'


class StockItems(models.Model):
    stock_id = models.CharField(max_length=50, primary_key=True)
    inspection = models.ForeignKey(InspectionAndAcceptance, on_delete=models.CASCADE, related_name='stock_items')
    supplier_item = models.ForeignKey(SupplierItem, on_delete=models.CASCADE, related_name='stock_items')
    quantity_received = models.PositiveIntegerField()
    quantity_on_hand = models.PositiveIntegerField()
    location = models.CharField(max_length=255)
    date_received = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.stock_id} - {self.supplier_item.supplier_item_no}'


class RequisitionIssueSlip(models.Model):
    ris_no = models.CharField(max_length=50, primary_key=True)
    res_center_code = models.CharField(max_length=10)
    division = models.CharField(max_length=50)
    office = models.CharField(max_length=50)
    is_stock_available = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField()
    remarks = models.TextField()
    purpose = models.CharField(max_length=255)
    requested_by = models.CharField(max_length=100)
    approved_by = models.CharField(max_length=100)
    issued_by = models.CharField(max_length=100)
    received_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.ris_no} - {self.office}'


class Budget(models.Model):
    budget_no = models.CharField(max_length=50, primary_key=True)
    department = models.CharField(max_length=50)
    budget_allocation = models.DecimalField(max_digits=15, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=15, decimal_places=2)
    fiscal_year = models.IntegerField()

    def __str__(self):
        return f'Budget: {self.department} - {self.budget_allocation}'


class Bidding(models.Model):
    bidding_no = models.CharField(max_length=50, primary_key=True)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='biddings')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='biddings')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    bid_date = models.DateTimeField(auto_now_add=True)
    is_winner = models.BooleanField(default=False)

    def __str__(self):
        return f'Bidding: {self.supplier.name} - {self.total_amount}'


class BACMember(models.Model):
    member_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=255)
    position = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# The FundCluster and Office models are added to provide structured data for the fund clusters and offices, which can be linked to purchase requests for better data integrity and easier querying.
class FundCluster(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class Office(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']