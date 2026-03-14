from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from orders.models import Order, Customer, OrderItem
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from accounts.models import CustomUser
from django.contrib import messages


@login_required
def attendant_dashboard(request):
    request.session['role'] = request.user.role
    request.session.modified = True
    today = timezone.now().date()
    total_orders_today = Order.objects.filter(created_at__date=today).count()
    pending_orders = Order.objects.filter(collection_status='received').count()
    ready_orders = Order.objects.filter(collection_status='ready').count()
    urgent_orders = Order.objects.filter(is_urgent=True).exclude(collection_status='collected')
    recent_orders = Order.objects.order_by('-created_at')[:5]

    context = {
        'total_orders_today': total_orders_today,
        'pending_orders': pending_orders,
        'ready_orders': ready_orders,
        'urgent_orders': urgent_orders,
        'recent_orders': recent_orders,
    }
    return render(request, 'dashboard/attendant_dashboard.html', context)


@login_required
def owner_dashboard(request):
    request.session['role'] = request.user.role
    request.session.modified = True
    today = timezone.now().date()
    first_day_this_month = today.replace(day=1)
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)

    orders_today = Order.objects.filter(created_at__date=today)
    revenue_today = orders_today.aggregate(Sum('total_price'))['total_price__sum'] or 0
    uncollected = Order.objects.filter(collection_status='ready').count()
    unpaid_balance = Order.objects.exclude(
        payment_status='paid'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    paid_balance = Order.objects.exclude(
        payment_status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    outstanding_balance = unpaid_balance - paid_balance

    chart_labels = []
    chart_data = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        revenue = Order.objects.filter(
            created_at__date=day
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        chart_labels.append(day.strftime('%b %d'))
        chart_data.append(float(revenue))

    this_month_orders = Order.objects.filter(created_at__date__gte=first_day_this_month)
    last_month_orders = Order.objects.filter(
        created_at__date__gte=first_day_last_month,
        created_at__date__lte=last_day_last_month
    )

    this_month_revenue = this_month_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    last_month_revenue = last_month_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    this_month_order_count = this_month_orders.count()
    last_month_order_count = last_month_orders.count()

    new_clients_this_month = Customer.objects.filter(
        created_at__date__gte=first_day_this_month
    ).count()

    if last_month_revenue > 0:
        revenue_growth = ((this_month_revenue - last_month_revenue) / last_month_revenue) * 100
    else:
        revenue_growth = 100 if this_month_revenue > 0 else 0

    if last_month_order_count > 0:
        orders_growth = ((this_month_order_count - last_month_order_count) / last_month_order_count) * 100
    else:
        orders_growth = 100 if this_month_order_count > 0 else 0

    service_breakdown_raw = list(Order.objects.values('service_type').annotate(
        count=Count('id'),
        revenue=Sum('total_price')
    ).order_by('-revenue'))

    total_orders_count = sum(s['count'] for s in service_breakdown_raw)

    service_breakdown = []
    for service in service_breakdown_raw:
        service_breakdown.append({
            'service_type': service['service_type'],
            'count': service['count'],
            'revenue': service['revenue'],
            'percentage': round((service['count'] / total_orders_count * 100), 1) if total_orders_count > 0 else 0
        })

    categories_raw = list(OrderItem.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count'))

    total_items = sum(cat['count'] for cat in categories_raw)

    categories = []
    for cat in categories_raw:
        categories.append({
            'category': cat['category'],
            'count': cat['count'],
            'percentage': round((cat['count'] / total_items * 100), 1) if total_items > 0 else 0
        })

    top_clients = Customer.objects.annotate(
        total_spent=Sum('orders__total_price'),
        order_count=Count('orders__id')
    ).filter(total_spent__isnull=False).order_by('-total_spent')[:5]

    total_clients = Customer.objects.count()
    returning_clients = Customer.objects.filter(total_visits__gt=1).count()
    new_clients_ratio = round((new_clients_this_month / total_clients * 100), 1) if total_clients > 0 else 0
    returning_ratio = round((returning_clients / total_clients * 100), 1) if total_clients > 0 else 0

    urgent_uncollected = Order.objects.filter(
        is_urgent=True
    ).exclude(collection_status='collected').select_related('customer')

    overdue_orders = Order.objects.filter(
        pickup_date__lt=today
    ).exclude(collection_status='collected').select_related('customer')

    old_unpaid = Order.objects.filter(
        payment_status='unpaid',
        created_at__date__lte=today - timedelta(days=7)
    ).select_related('customer')

    context = {
        'orders_today': orders_today.count(),
        'revenue_today': revenue_today,
        'uncollected': uncollected,
        'outstanding_balance': outstanding_balance,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'this_month_revenue': this_month_revenue,
        'last_month_revenue': last_month_revenue,
        'revenue_growth': round(revenue_growth, 1),
        'this_month_order_count': this_month_order_count,
        'last_month_order_count': last_month_order_count,
        'orders_growth': round(orders_growth, 1),
        'new_clients_this_month': new_clients_this_month,
        'service_breakdown': service_breakdown,
        'categories': categories,
        'top_clients': top_clients,
        'total_clients': total_clients,
        'returning_ratio': returning_ratio,
        'new_clients_ratio': new_clients_ratio,
        'urgent_uncollected': urgent_uncollected,
        'overdue_orders': overdue_orders,
        'old_unpaid': old_unpaid,
    }
    return render(request, 'dashboard/owner_dashboard.html', context)


@login_required
def analytics(request):
    request.session['role'] = request.user.role
    request.session.modified = True
    if request.session['role'] != 'owner':
        return redirect('attendant_dashboard')

    today = timezone.now().date()
    period = request.GET.get('period', 'month')

    if period == 'week':
        start_date = today - timedelta(days=7)
        label_format = '%a %d'
    elif period == 'month':
        start_date = today - timedelta(days=30)
        label_format = '%b %d'
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
        label_format = '%b %d'
    elif period == 'year':
        start_date = today - timedelta(days=365)
        label_format = '%b %Y'
    else:
        start_date = today - timedelta(days=30)
        label_format = '%b %d'

    orders_in_period = Order.objects.filter(created_at__date__gte=start_date)

    revenue_labels = []
    revenue_data = []

    if period == 'year':
        current = start_date.replace(day=1)
        while current <= today:
            month_end = (current.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            revenue = Order.objects.filter(
                created_at__date__gte=current,
                created_at__date__lte=month_end
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0
            revenue_labels.append(current.strftime('%b %Y'))
            revenue_data.append(float(revenue))
            current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    else:
        days = (today - start_date).days + 1
        for i in range(days):
            day = start_date + timedelta(days=i)
            revenue = Order.objects.filter(
                created_at__date=day
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0
            revenue_labels.append(day.strftime(label_format))
            revenue_data.append(float(revenue))

    total_revenue = orders_in_period.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = orders_in_period.count()
    avg_order_value = round(float(total_revenue) / total_orders, 2) if total_orders > 0 else 0
    best_day_revenue = max(revenue_data) if revenue_data else 0
    best_day_label = revenue_labels[revenue_data.index(best_day_revenue)] if revenue_data and best_day_revenue > 0 else 'N/A'

    service_data_raw = list(orders_in_period.values('service_type').annotate(count=Count('id')))
    service_labels = [s['service_type'].replace('_', ' ').title() for s in service_data_raw]
    service_counts = [s['count'] for s in service_data_raw]

    category_data_raw = list(OrderItem.objects.filter(
        order__created_at__date__gte=start_date
    ).values('category').annotate(count=Count('id')).order_by('-count'))
    category_labels = [c['category'].replace('_', ' ').title() for c in category_data_raw]
    category_counts = [c['count'] for c in category_data_raw]

    from django.db.models.functions import ExtractWeekDay
    weekday_data = orders_in_period.annotate(
        weekday=ExtractWeekDay('created_at')
    ).values('weekday').annotate(count=Count('id')).order_by('weekday')
    weekday_map = {1: 'Sun', 2: 'Mon', 3: 'Tue', 4: 'Wed', 5: 'Thu', 6: 'Fri', 7: 'Sat'}
    weekday_labels = [weekday_map.get(d['weekday'], '') for d in weekday_data]
    weekday_counts = [d['count'] for d in weekday_data]

    payment_data_raw = list(orders_in_period.values('payment_status').annotate(count=Count('id')))
    payment_labels = [p['payment_status'].title() for p in payment_data_raw]
    payment_counts = [p['count'] for p in payment_data_raw]

    outstanding_0_7 = Order.objects.filter(
        payment_status='unpaid',
        created_at__date__gte=today - timedelta(days=7)
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    outstanding_7_30 = Order.objects.filter(
        payment_status='unpaid',
        created_at__date__gte=today - timedelta(days=30),
        created_at__date__lt=today - timedelta(days=7)
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    outstanding_30_plus = Order.objects.filter(
        payment_status='unpaid',
        created_at__date__lt=today - timedelta(days=30)
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    new_client_labels = []
    new_client_data = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        count = Customer.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).count()
        new_client_labels.append(month_start.strftime('%b %Y'))
        new_client_data.append(count)

    top_10_clients = Customer.objects.annotate(
        total_spent=Sum('orders__total_price'),
        order_count=Count('orders__id')
    ).filter(total_spent__isnull=False).order_by('-total_spent')[:10]

    total_clients = Customer.objects.count()
    returning_clients = Customer.objects.filter(total_visits__gt=1).count()
    new_only_clients = total_clients - returning_clients

    context = {
        'period': period,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'best_day_revenue': best_day_revenue,
        'best_day_label': best_day_label,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'service_labels': service_labels,
        'service_counts': service_counts,
        'category_labels': category_labels,
        'category_counts': category_counts,
        'weekday_labels': weekday_labels,
        'weekday_counts': weekday_counts,
        'payment_labels': payment_labels,
        'payment_counts': payment_counts,
        'outstanding_0_7': outstanding_0_7,
        'outstanding_7_30': outstanding_7_30,
        'outstanding_30_plus': outstanding_30_plus,
        'new_client_labels': new_client_labels,
        'new_client_data': new_client_data,
        'top_10_clients': top_10_clients,
        'total_clients': total_clients,
        'returning_clients': returning_clients,
        'new_only_clients': new_only_clients,
    }
    return render(request, 'dashboard/analytics.html', context)


@login_required
def settings(request):
    request.session['role'] = request.user.role
    request.session.modified = True
    if request.session['role'] != 'owner':
        return redirect('attendant_dashboard')

    attendants = CustomUser.objects.filter(role='attendant')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                role='attendant',
            )
            user.first_name = full_name
            user.save()
            messages.success(request, f'Attendant account for {full_name} created successfully.')
            return redirect('settings')

    return render(request, 'dashboard/settings.html', {'attendants': attendants})


@login_required
def toggle_attendant(request, user_id):
    if request.user.role != 'owner':
        return redirect('attendant_dashboard')
    attendant = get_object_or_404(CustomUser, id=user_id)
    attendant.is_active = not attendant.is_active
    attendant.save()
    return redirect('settings')