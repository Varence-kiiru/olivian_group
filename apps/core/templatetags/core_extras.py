"""Custom template tags and filters for the core app."""

from django import template
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

User = get_user_model()
register = template.Library()

@register.filter(name='divide')
def divide(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def filter_messages(messages, user):
    """
    Filter messages based on user role/context.
    Management users see management messages, customers see customer messages.
    """
    if not user or not user.is_authenticated:
        # Anonymous users see all messages
        return messages

    # Define management roles
    management_roles = [
        'super_admin', 'manager', 'sales_manager', 'sales_person',
        'project_manager', 'inventory_manager', 'cashier', 'technician'
    ]

    is_management = user.role in management_roles
    is_customer = user.role == 'customer'

    filtered_messages = []

    for message in messages:
        # Check if message has a context tag (management or customer)
        if hasattr(message, 'tags') and message.tags:
            tags = message.tags.split()
            if 'management' in tags and is_management:
                filtered_messages.append(message)
            elif 'customer' in tags and is_customer:
                filtered_messages.append(message)
            elif 'all' in tags:
                # Messages tagged with 'all' are shown to everyone
                filtered_messages.append(message)
        else:
            # No specific tags - default behavior
            if is_management:
                # Management users see all untagged messages
                filtered_messages.append(message)
            elif is_customer:
                # Customers only see explicitly tagged messages for them or 'all' messages
                # This prevents internal management messages from showing to customers
                continue

    return filtered_messages


@register.simple_tag
def get_member_count(room):
    """
    Get the current number of members/participants in a chat room.
    Handles different room types appropriately.
    """
    if room.room_type == 'private':
        return room.participants.count()
    elif room.room_type == 'department':
        # Count users who have groups containing the room name
        group_names = [g.name for g in Group.objects.filter(name__icontains=room.name.lower())]
        if group_names:
            member_ids = set()
            for group_name in group_names:
                try:
                    group = Group.objects.get(name=group_name)
                    for user in group.user_set.filter(is_active=True):
                        member_ids.add(user.id)
                except Group.DoesNotExist:
                    continue
            return len(member_ids)
        return 0
    elif room.room_type == 'project':
        return room.participants.count()
    elif room.room_type == 'general':
        # General rooms are accessible to all authenticated users
        return User.objects.filter(is_active=True).count()
    else:
        return 0


# Pricing and Discount Filters
@register.filter(name='apply_discount')
def apply_discount(price, discount_percentage):
    """Apply discount percentage to price and return discounted amount"""
    try:
        price_decimal = Decimal(str(price))
        discount_decimal = Decimal(str(discount_percentage))
        discount_amount = price_decimal * (discount_decimal / Decimal('100'))
        discounted_price = price_decimal - discount_amount
        # Round to 2 decimal places using banker's rounding
        return discounted_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError, InvalidOperation):
        return price


@register.filter(name='calculate_savings')
def calculate_savings(price, discount_percentage):
    """Calculate the savings amount from original price"""
    try:
        price_decimal = Decimal(str(price))
        discount_decimal = Decimal(str(discount_percentage))
        savings = price_decimal * (discount_decimal / Decimal('100'))
        return savings.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0.00')


@register.filter(name='format_price')
def format_price(price, currency='KES'):
    """Format price with currency"""
    try:
        price_decimal = Decimal(str(price))
        if currency == 'KES':
            return f"{price_decimal:.0f}"
        else:
            return f"{currency} {price_decimal:.2f}"
    except (ValueError, TypeError, InvalidOperation):
        return str(price)


@register.filter(name='show_original_and_discounted')
def show_original_and_discounted(price, discount_percentage):
    """Return a tuple of (original_price, discounted_price, savings) for templates"""
    try:
        price_decimal = Decimal(str(price))
        discount_decimal = Decimal(str(discount_percentage))

        discount_amount = price_decimal * (discount_decimal / Decimal('100'))
        discounted_price = price_decimal - discount_amount
        savings = discount_amount

        return (
            price_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            discounted_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            savings.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )
    except (ValueError, TypeError, InvalidOperation):
        return (price, price, Decimal('0.00'))


@register.simple_tag
def get_discounted_price(price, discount_percentage=0):
    """Simple tag to get discounted price with fallback to original price"""
    if discount_percentage and discount_percentage > 0:
        return apply_discount(price, discount_percentage)
    return price


@register.filter(name='split_name')
def split_name(name, index=None):
    """
    Split a full name into first name and last name.
    Returns the first part if index is 0, last part if index is 1,
    or a dict with 'first_name' and 'last_name' if no index specified.
    """
    if not name or not isinstance(name, str):
        if index == 0:
            return ''
        elif index == 1:
            return ''
        else:
            return {'first_name': '', 'last_name': ''}

    # Strip extra whitespace and split by spaces
    parts = name.strip().split()

    if len(parts) == 0:
        if index == 0:
            return ''
        elif index == 1:
            return ''
        else:
            return {'first_name': '', 'last_name': ''}

    elif len(parts) == 1:
        # Only one part - treat as first name
        if index == 0:
            return parts[0]
        elif index == 1:
            return ''
        else:
            return {'first_name': parts[0], 'last_name': ''}

    else:
        # Multiple parts - first part is first name, rest joined as last name
        first_name = parts[0]
        last_name = ' '.join(parts[1:])

        if index == 0:
            return first_name
        elif index == 1:
            return last_name
        else:
            return {'first_name': first_name, 'last_name': last_name}
