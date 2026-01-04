// Custom Order Admin JavaScript

(function($) {
    'use strict';
    
    // Wait for DOM to be ready using Django's jQuery
    window.addEventListener('load', function() {
        const $ = django.jQuery;
        
        // Auto-calculate order totals when items are modified
        function calculateOrderTotal() {
            let subtotal = 0;
            
            $('.order-items-inline .tabular tbody tr:not(.empty-form)').each(function() {
                let quantity = parseFloat($(this).find('input[name*="quantity"]').val()) || 0;
                let price = parseFloat($(this).find('input[name*="price"]').val()) || 0;
                let lineTotal = quantity * price;
                
                subtotal += lineTotal;
                $(this).find('.line-total').text('$' + lineTotal.toFixed(2));
            });
            
            // Calculate VAT (16%)
            let vat = subtotal * 0.16;
            let total = subtotal + vat;
            
            $('#order-subtotal').text('$' + subtotal.toFixed(2));
            $('#order-vat').text('$' + vat.toFixed(2));
            $('#order-total').text('$' + total.toFixed(2));
        }
        
        // Event handlers
        $(document).on('input change', '.order-items-inline input', calculateOrderTotal);
        
        // Status change confirmation
        $(document).on('change', 'select[name="status"]', function(e) {
            const newStatus = $(this).val();
            const currentStatus = $(this).data('current-status');
            
            if (newStatus !== currentStatus && newStatus === 'cancelled') {
                if (!confirm('Are you sure you want to cancel this order? This action cannot be undone.')) {
                    e.preventDefault();
                    $(this).val(currentStatus);
                }
            }
        });
        
        // Order notes functionality
        $('.order-notes textarea').on('input', function() {
            const maxLength = 500;
            const currentLength = $(this).val().length;
            const remaining = maxLength - currentLength;
            
            $(this).siblings('.notes-counter').text(remaining + ' characters remaining');
            $(this).siblings('.notes-counter')
                .toggleClass('text-warning', remaining < 50);
        });
        
        // Print order functionality
        $('.print-order-btn').on('click', function(e) {
            e.preventDefault();
            const orderId = $(this).data('order-id');
            
            if (orderId) {
                window.open(`/admin/orders/${orderId}/print/`, '_blank', 
                    'width=800,height=600,scrollbars=yes,resizable=yes');
            }
        });
        
        // Refresh order data
        $('.refresh-order-btn').on('click', function(e) {
            e.preventDefault();
            location.reload();
        });
        
        // Auto-save draft changes
        let autoSaveTimer;
        const autoSaveDelay = 2000; // 2 seconds
        
        $('.order-form input, .order-form select, .order-form textarea').on('input change', function() {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(function() {
                console.log('Auto-saving order changes...');
                // Add auto-save implementation if needed
            }, autoSaveDelay);
        });
        
        // Delete confirmation
        $('.delete-order-item').on('click', function(e) {
            if (!confirm('Are you sure you want to remove this item from the order?')) {
                e.preventDefault();
            }
        });
        
        // Initial calculation
        calculateOrderTotal();
        
        console.log('Order admin JavaScript initialized successfully');
    });
    
})(window.django ? django.jQuery : jQuery);
