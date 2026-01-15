from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from apps.pos.models import Sale


class Command(BaseCommand):
    help = 'Fix sale totals for existing sales with 0.00 amounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find sales with 0.00 totals that have items
        problematic_sales = Sale.objects.filter(
            grand_total=Decimal('0.00'),
            items__isnull=False
        ).distinct()

        if not problematic_sales.exists():
            self.stdout.write(
                self.style.SUCCESS('No sales found with zero totals that have items.')
            )
            return

        self.stdout.write(f'Found {problematic_sales.count()} sales to fix.')

        fixed_count = 0
        
        for sale in problematic_sales:
            items = sale.items.all()
            if not items.exists():
                continue
                
            # Calculate totals using VAT-inclusive approach (same as ecommerce)
            from apps.core.models import CompanySettings
            
            # Sum all line totals (these are VAT-inclusive)
            vat_inclusive_subtotal = sum(item.line_total for item in items)
            
            # Calculate VAT backwards from inclusive prices
            company_settings = CompanySettings.get_settings()
            vat_rate = Decimal(str(company_settings.vat_rate))
            vat_multiplier = Decimal('1') + (vat_rate / Decimal('100'))
            
            # Extract VAT amount and ex-VAT subtotal
            subtotal_ex_tax = vat_inclusive_subtotal / vat_multiplier
            tax_total = vat_inclusive_subtotal - subtotal_ex_tax
            grand_total = vat_inclusive_subtotal - sale.discount_amount
            
            self.stdout.write(
                f'Sale {sale.sale_number}: '
                f'Subtotal: {subtotal_ex_tax}, Tax: {tax_total}, Total: {grand_total}'
            )
            
            if not dry_run:
                with transaction.atomic():
                    sale.subtotal = subtotal_ex_tax
                    sale.tax_amount = tax_total
                    sale.grand_total = grand_total
                    sale.save(update_fields=['subtotal', 'tax_amount', 'grand_total'])
                    fixed_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would fix {problematic_sales.count()} sales. '
                    'Run without --dry-run to apply changes.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {fixed_count} sales.')
            )
