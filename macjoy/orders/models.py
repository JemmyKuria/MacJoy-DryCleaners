import uuid
from django.db import models

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)
    total_visits = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customers'
        managed = False  # This model is read-only, managed externally

    def __str__(self):
        return f"{self.full_name} - {self.phone_number}"


class Order(models.Model):

    ORDER_TYPE_CHOICES = [
        ('basket', 'Basket'),
        ('single_item', 'Single Item'),
    ]
    SERVICE_TYPE_CHOICES = [
        ('laundry', 'Laundry Only'),
        ('pressing', 'Pressing Only'),
        ('both', 'Laundry & Pressing'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('unpaid', 'Unpaid'),
    ]
    COLLECTION_STATUS_CHOICES = [
        ('received', 'Received'),
        ('ready', 'Ready for Collection'),
        ('collected', 'Collected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    collection_status = models.CharField(max_length=20, choices=COLLECTION_STATUS_CHOICES, default='received')
    is_urgent = models.BooleanField(default=False)
    pickup_date = models.DateField()
    completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'
        managed = False  # This model is read-only, managed externally

    def __str__(self):
        return f"{self.order_number} - {self.customer.full_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            last = Order.objects.order_by('-created_at').first()
            number = (int(last.order_number.split('-')[-1]) + 1) if last else 1
            self.order_number = f"MJ-{self.created_at.year if self.created_at else '2025'}-{str(number).zfill(3)}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):

    CATEGORY_CHOICES = [
        ('corporate', 'Corporate'),
        ('event', 'Event'),
        ('graduation', 'Graduation'),
        ('choir', 'Choir'),
        ('military', 'Military'),
        ('regular', 'Regular'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item_name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'
        managed = False  # This model is read-only, managed externally

    def __str__(self):
        return f"{self.item_name} - {self.order.order_number}"