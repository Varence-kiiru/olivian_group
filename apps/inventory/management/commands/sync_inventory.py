from django.core.management.base import BaseCommand
from django.db import transaction
from apps.products.models import Product
from apps.inventory.models import InventoryItem, Warehouse

class Command(BaseCommand):
    help = 'Sync product stock with inventory management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create inventory items for products that don\'t have them',
        )
        parser.add_argument(
            '--sync-quantities',
            action='store_true', 
            help='Sync quantities from inventory back to products',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Inventory Sync Starting ===\n")
        
        # Get default warehouse
        try:
            warehouse = Warehouse.objects.filter(is_active=True).first()
            if not warehouse:
                warehouse = Warehouse.objects.create(
                    name="Main Warehouse",
                    code="MAIN",
                    address="Default warehouse location",
                    total_capacity=1000.00
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Created default warehouse: {warehouse}")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error creating warehouse: {e}")
            )
            return

        # Statistics
        products_count = Product.objects.count()
        inventory_count = InventoryItem.objects.count()
        
        self.stdout.write(f"Found {products_count} products")
        self.stdout.write(f"Found {inventory_count} inventory items")
        
        if options['create_missing']:
            self.create_missing_inventory_items(warehouse)
            
        if options['sync_quantities']:
            self.sync_quantities_to_products()
            
        # Final stats
        final_inventory_count = InventoryItem.objects.count()
        self.stdout.write(f"\nFinal count: {final_inventory_count} inventory items")
        self.stdout.write(self.style.SUCCESS("=== Sync Complete ==="))

    def create_missing_inventory_items(self, warehouse):
        """Create inventory items for products that don't have them"""
        products_without_inventory = Product.objects.exclude(
            id__in=InventoryItem.objects.values_list('product_id', flat=True)
        )
        
        created_count = 0
        
        with transaction.atomic():
            for product in products_without_inventory:
                if product.quantity_in_stock > 0:
                    InventoryItem.objects.create(
                        product=product,
                        warehouse=warehouse,
                        quantity_on_hand=product.quantity_in_stock,
                        reorder_point=product.low_stock_threshold,
                        maximum_stock=max(product.quantity_in_stock * 2, 100),
                        safety_stock=product.low_stock_threshold,
                        average_cost=product.cost_price,
                        last_cost=product.cost_price
                    )
                    created_count += 1
                    self.stdout.write(f"Created inventory for: {product.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} inventory items")
        )

    def sync_quantities_to_products(self):
        """Sync inventory quantities back to product stock fields"""
        synced_count = 0
        
        with transaction.atomic():
            for product in Product.objects.all():
                total_qty = product.total_inventory_quantity
                if product.quantity_in_stock != total_qty:
                    product.quantity_in_stock = total_qty
                    product.save(update_fields=['quantity_in_stock'])
                    synced_count += 1
                    self.stdout.write(f"Synced {product.name}: {total_qty} units")
        
        self.stdout.write(
            self.style.SUCCESS(f"Synced {synced_count} products")
        )
