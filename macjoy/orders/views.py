from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Customer, Order, OrderItem
from django.utils import timezone
from datetime import timedelta


@login_required
def new_order(request):
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        full_name = request.POST.get('full_name')

        customer, created = Customer.objects.get_or_create(
            phone_number=phone,
            defaults={'full_name': full_name}
        )

        if not created:
            customer.full_name = full_name
            customer.total_visits += 1
            customer.save()
        else:
            customer.total_visits = 1
            customer.save()

        order = Order.objects.create(
            order_number=f"MJ-{timezone.now().year}-{str(Order.objects.count() + 1).zfill(3)}",
            customer=customer,
            order_type=request.POST.get('order_type'),
            service_type=request.POST.get('service_type'),
            total_price=request.POST.get('total_price'),
            amount_paid=request.POST.get('amount_paid', 0),
            payment_status=request.POST.get('payment_status'),
            pickup_date=request.POST.get('pickup_date'),
            is_urgent=request.POST.get('is_urgent') == 'on',
            notes=request.POST.get('notes', ''),
        )

        if order.order_type == 'single_item':
            item_names = request.POST.getlist('item_name')
            categories = request.POST.getlist('category')
            descriptions = request.POST.getlist('description')
            quantities = request.POST.getlist('quantity')
            unit_prices = request.POST.getlist('unit_price')

            for i in range(len(item_names)):
                if item_names[i]:
                    OrderItem.objects.create(
                        order=order,
                        item_name=item_names[i],
                        category=categories[i],
                        description=descriptions[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                    )

        return redirect('attendant_orders')

    return render(request, 'orders/new_order.html')


@login_required
def search_customer(request):
    phone = request.GET.get('phone', '')
    try:
        customer = Customer.objects.get(phone_number=phone)
        return JsonResponse({
            'found': True,
            'full_name': customer.full_name,
            'total_visits': customer.total_visits,
        })
    except Customer.DoesNotExist:
        return JsonResponse({'found': False})


@login_required
def attendant_orders(request):
    orders = Order.objects.select_related('customer').order_by('-created_at')

    date_filter = request.GET.get('date_filter', 'all')
    today = timezone.now().date()
    if date_filter == 'today':
        orders = orders.filter(created_at__date=today)
    elif date_filter == 'week':
        orders = orders.filter(created_at__date__gte=today - timedelta(days=7))
    elif date_filter == 'month':
        orders = orders.filter(created_at__date__gte=today - timedelta(days=30))

    status_filter = request.GET.get('status_filter', 'all')
    if status_filter != 'all':
        orders = orders.filter(collection_status=status_filter)

    payment_filter = request.GET.get('payment_filter', 'all')
    if payment_filter != 'all':
        orders = orders.filter(payment_status=payment_filter)

    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(
            customer__full_name__icontains=search
        ) | orders.filter(
            order_number__icontains=search
        )

    context = {
        'orders': orders,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search': search,
    }
    return render(request, 'orders/attendant_orders.html', context)


@login_required
def owner_orders(request):
    orders = Order.objects.select_related('customer').order_by('-created_at')

    date_filter = request.GET.get('date_filter', 'all')
    today = timezone.now().date()

    if date_filter == 'today':
        orders = orders.filter(created_at__date=today)
    elif date_filter == 'week':
        orders = orders.filter(created_at__date__gte=today - timedelta(days=7))
    elif date_filter == 'month':
        orders = orders.filter(created_at__date__gte=today - timedelta(days=30))

    payment_filter = request.GET.get('payment_filter', 'all')
    if payment_filter != 'all':
        orders = orders.filter(payment_status=payment_filter)

    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(
            customer__full_name__icontains=search
        ) | orders.filter(
            order_number__icontains=search
        )

    total_revenue = sum(order.total_price for order in orders)
    total_paid = sum(order.amount_paid for order in orders)
    total_outstanding = total_revenue - total_paid

    context = {
        'orders': orders,
        'total_revenue': total_revenue,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'date_filter': date_filter,
        'payment_filter': payment_filter,
        'search': search,
    }
    return render(request, 'orders/owner_orders.html', context)


@login_required
def clients(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'orders/clients.html', {'customers': customers})


@login_required
def client_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    total_spent = sum(order.amount_paid for order in orders)
    context = {
        'customer': customer,
        'orders': orders,
        'total_spent': total_spent,
    }
    return render(request, 'orders/client_detail.html', context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.order_items.all()
    balance_due = order.total_price - order.amount_paid

    context = {
        'order': order,
        'items': items,
        'balance_due': balance_due,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.collection_status = request.POST.get('collection_status')
        if order.collection_status == 'ready':
            order.completion_date = timezone.now()
        order.save()
    next_url = request.POST.get('next', '')
    return redirect(next_url if next_url else 'attendant_orders')


@login_required
def update_payment_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        payment_status = request.POST.get('payment_status')
        order.payment_status = payment_status
        if payment_status == 'paid':
            order.amount_paid = order.total_price
        order.save()
    next_url = request.POST.get('next', '')
    return redirect(next_url if next_url else 'attendant_orders')