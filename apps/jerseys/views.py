import csv
from collections import defaultdict

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import JerseyOrderForm
from .models import JerseyOrder


def _catalog():
    return [
        {
            'code': code,
            'label': label,
            'rate': JerseyOrder.rate_for(code),
            'is_shirt': code in JerseyOrder.SHIRT_ITEMS,
        }
        for code, label in JerseyOrder.ITEM_CHOICES
    ]


def _taken_numbers():
    return list(
        JerseyOrder.objects.exclude(jersey_number='')
        .select_related('user')
        .order_by('jersey_number', 'wearer_name')
        .values('jersey_number', 'wearer_name', 'gender', 'user__username')
    )


def _summary():
    rows = (
        JerseyOrder.objects
        .values('item_type', 'size', 'gender')
        .annotate(quantity=Sum('quantity'))
        .order_by('item_type', 'gender', 'size')
    )
    item_labels = dict(JerseyOrder.ITEM_CHOICES)
    gender_labels = dict(JerseyOrder.GENDER_CHOICES)
    grouped = defaultdict(list)
    grand_total = 0
    total_quantity = 0
    for row in rows:
        rate = JerseyOrder.rate_for(row['item_type'])
        quantity = row['quantity'] or 0
        total = rate * quantity
        grand_total += total
        total_quantity += quantity
        grouped[row['item_type']].append({
            'item': item_labels.get(row['item_type'], row['item_type']),
            'size': row['size'],
            'gender': gender_labels.get(row['gender'], row['gender']),
            'quantity': quantity,
            'rate': rate,
            'total': total,
        })
    return grouped, total_quantity, grand_total


@login_required
def jersey_orders_view(request):
    form = JerseyOrderForm(user=request.user)
    if request.method == 'POST':
        form = JerseyOrderForm(request.POST, user=request.user)
        if form.is_valid():
            order = form.save()
            messages.success(
                request,
                f"Added {order.quantity} x {order.get_item_type_display()} for {order.wearer_name}."
            )
            return redirect('jersey-orders')

    own_orders = JerseyOrder.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'form': form,
        'own_orders': own_orders,
        'catalog': _catalog(),
        'size_measurements': JerseyOrder.SIZE_MEASUREMENTS,
        'taken_numbers': _taken_numbers(),
    }
    return render(request, 'jerseys/order_form.html', context)


@login_required
def delete_jersey_order_view(request, order_id):
    order = get_object_or_404(JerseyOrder, id=order_id)
    if not request.user.is_staff and order.user_id != request.user.id:
        messages.error(request, "You cannot delete another member's order.")
        return redirect('jersey-orders')
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Order line removed.')
    return redirect('jersey-orders-admin' if request.user.is_staff else 'jersey-orders')


@staff_member_required
def jersey_orders_admin_view(request):
    summary, total_quantity, grand_total = _summary()
    orders = JerseyOrder.objects.select_related('user').order_by(
        'user__first_name',
        'user__username',
        'wearer_name',
    )
    return render(request, 'jerseys/admin_summary.html', {
        'orders': orders,
        'summary': dict(summary),
        'total_quantity': total_quantity,
        'grand_total': grand_total,
        'taken_numbers': _taken_numbers(),
    })


@staff_member_required
def export_jersey_orders_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="jersey_orders.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Member',
        'For',
        'Gender',
        'Wearer name',
        'Item',
        'Size',
        'Quantity',
        'Jersey number',
        'Unit price',
        'Line total',
        'Notes',
    ])
    for order in JerseyOrder.objects.select_related('user').order_by('user__username', 'wearer_name'):
        writer.writerow([
            order.user.get_full_name() or order.user.username,
            order.get_for_person_display(),
            order.get_gender_display(),
            order.wearer_name,
            order.get_item_type_display(),
            order.size,
            order.quantity,
            order.jersey_number,
            order.unit_price,
            order.line_total,
            order.notes,
        ])
    return response
