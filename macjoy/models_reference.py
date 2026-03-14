# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Customers(models.Model):
    id = models.UUIDField(primary_key=True)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(unique=True, max_length=15)
    total_visits = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customers'


class OrderItems(models.Model):
    id = models.UUIDField(primary_key=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING)
    item_name = models.CharField(max_length=100)
    category = models.TextField()  # This field type is a guess.
    description = models.TextField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'order_items'


class Orders(models.Model):
    id = models.UUIDField(primary_key=True)
    order_number = models.CharField(unique=True, max_length=20)
    customer = models.ForeignKey(Customers, models.DO_NOTHING)
    order_type = models.TextField()  # This field type is a guess.
    service_type = models.TextField()  # This field type is a guess.
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    payment_status = models.TextField(blank=True, null=True)  # This field type is a guess.
    collection_status = models.TextField(blank=True, null=True)  # This field type is a guess.
    is_urgent = models.BooleanField(blank=True, null=True)
    pickup_date = models.DateField()
    completion_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class Users(models.Model):
    id = models.UUIDField(primary_key=True)
    full_name = models.CharField(max_length=100)
    role = models.TextField()  # This field type is a guess.
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
