from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from .models import Sale, SaleItem, Payment, CashierSession, SaleSequence
from apps.inventory.models import InventoryItem, StockMovement


@receiver(post_save, sender=SaleItem)
@receiver(post_delete, sender=SaleItem)
def update_sale_totals_on_item_change(sender, instance, **kwargs):
    """Update sale totals when sale items are added, updated, or deleted"""
    sale = instance.sale
    
    # Calculate totals from sale items (VAT-inclusive approach)
    items = sale.items.all()
    if items.exists():
        # Sum all line totals (these are VAT-inclusive)
        vat_inclusive_subtotal = sum(item.line_total for item in items)
        
        # Calculate VAT backwards from inclusive prices
        from apps.core.models import CompanySettings
        company_settings = CompanySettings.get_settings()
        vat_rate = Decimal(str(company_settings.vat_rate))
        vat_multiplier = Decimal('1') + (vat_rate / Decimal('100'))
        
        # Extract VAT amount and ex-VAT subtotal
        subtotal_ex_vat = vat_inclusive_subtotal / vat_multiplier
        tax_total = vat_inclusive_subtotal - subtotal_ex_vat
        
        # Grand total is the VAT-inclusive amount minus any sale-level discount
        grand_total = vat_inclusive_subtotal - sale.discount_amount
    else:
        subtotal_ex_vat = Decimal('0.00')
        tax_total = Decimal('0.00')
        grand_total = Decimal('0.00')
    
    # Update sale totals
    Sale.objects.filter(pk=sale.pk).update(
        subtotal=subtotal_ex_vat,  # Store ex-VAT subtotal
        tax_amount=tax_total,
        grand_total=grand_total
    )


@receiver(post_save, sender=SaleItem)
def update_inventory_on_sale(sender, instance, created, **kwargs):
    """Update inventory when items are sold"""
    if created and instance.sale.status == 'completed':
        try:
            # Find inventory item for this product
            inventory_item = InventoryItem.objects.get(
                product=instance.product,
                warehouse__store=instance.sale.session.terminal.store
            )
            
            # Create stock movement
            StockMovement.objects.create(
                inventory_item=inventory_item,
                movement_type='sale',
                quantity=-instance.quantity,  # Negative for outgoing
                reference_number=instance.sale.receipt_number,
                notes=f"POS Sale - {instance.sale.receipt_number}",
                created_by=instance.sale.cashier
            )
            
            # Update inventory quantity
            inventory_item.quantity_on_hand -= instance.quantity
            inventory_item.save()
            
        except InventoryItem.DoesNotExist:
            # Log this issue - product sold but no inventory record
            pass


@receiver(post_save, sender=Payment)
def update_payment_totals(sender, instance, created, **kwargs):
    """Update sale payment totals when payment is added"""
    if instance.status == 'completed':
        sale = instance.sale
        total_paid = sale.payments.filter(status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Update sale payment amounts
        sale.amount_paid = total_paid
        sale.change_amount = max(Decimal('0.00'), total_paid - sale.grand_total)
        sale.save(update_fields=['amount_paid', 'change_amount'])


@receiver(post_save, sender=Sale)
def update_customer_stats(sender, instance, created, **kwargs):
    """Update customer statistics when sale is completed"""
    if instance.status == 'completed' and instance.customer:
        customer = instance.customer
        
        # Use the Customer model's built-in method to update purchase stats
        # This will automatically update total_orders, total_spent, loyalty_points, and last_purchase_date
        customer.update_purchase_stats(instance.grand_total, instance.transaction_time)


@receiver(post_save, sender=CashierSession)
def calculate_session_expected_cash(sender, instance, created, **kwargs):
    """Calculate expected cash when session is closed"""
    if instance.status == 'closed' and instance.expected_cash is None:
        # Calculate expected cash based on sales and cash movements
        cash_sales = Sale.objects.filter(
            session=instance,
            payment_method='cash',
            status='completed'
        ).aggregate(total=models.Sum('grand_total'))['total'] or Decimal('0.00')
        
        cash_movements_in = instance.cash_movements.filter(
            movement_type__in=['cash_in', 'float_add']
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        cash_movements_out = instance.cash_movements.filter(
            movement_type__in=['cash_out', 'payout', 'drop']
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        expected_cash = instance.opening_cash + cash_sales + cash_movements_in - cash_movements_out
        
        # Calculate variance if closing cash is provided
        variance = Decimal('0.00')
        if instance.closing_cash is not None:
            variance = instance.closing_cash - expected_cash
        
        # Update the session
        CashierSession.objects.filter(pk=instance.pk).update(
            expected_cash=expected_cash,
            cash_variance=variance
        )


@receiver(post_delete, sender=SaleItem)
def revert_inventory_on_item_delete(sender, instance, **kwargs):
    """Revert inventory when sale item is deleted"""
    if instance.sale.status == 'completed':
        try:
            inventory_item = InventoryItem.objects.get(
                product=instance.product,
                warehouse__store=instance.sale.session.terminal.store
            )
            
            # Create reversal stock movement
            StockMovement.objects.create(
                inventory_item=inventory_item,
                movement_type='adjustment',
                quantity=instance.quantity,  # Positive to add back
                reference_number=f"REV-{instance.sale.receipt_number}",
                notes=f"Reversal - Sale item deleted from {instance.sale.receipt_number}",
                created_by=None  # System generated
            )
            
            # Update inventory quantity
            inventory_item.quantity_on_hand += instance.quantity
            inventory_item.save()
            
        except InventoryItem.DoesNotExist:
            pass


# Import models after defining signals to avoid circular imports
from django.db import models
