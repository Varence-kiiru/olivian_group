// Olivian Group - API Communication

const API = {
    // Base configuration
    baseUrl: window.location.origin,
    
    // Get CSRF token from cookies
    getCsrfToken: function() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    // Default headers for API requests
    getHeaders: function() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
        };
    },

    // Generic API request method
    request: async function(url, options = {}) {
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    // GET request
    get: function(url) {
        return this.request(url, { method: 'GET' });
    },

    // POST request
    post: function(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // PUT request
    put: function(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    // DELETE request
    delete: function(url) {
        return this.request(url, { method: 'DELETE' });
    },

    // Specific API endpoints for Olivian Group
    endpoints: {
        // Products
        getProducts: () => API.get('/api/products/'),
        getProduct: (id) => API.get(`/api/products/${id}/`),
        
        // Quotations
        getQuotations: () => API.get('/api/quotations/'),
        createQuotation: (data) => API.post('/api/quotations/', data),
        
        // Projects
        getProjects: () => API.get('/api/projects/'),
        getProject: (id) => API.get(`/api/projects/${id}/`),
        
        // Dashboard stats
        getDashboardStats: () => API.get('/api/dashboard/stats/'),
        
        // User profile
        getUserProfile: () => API.get('/api/auth/user/'),
        updateUserProfile: (data) => API.put('/api/auth/user/', data),
        
        // Cart operations
        getCartCount: () => API.get('/api/cart/count/'),
        addToCart: (productId, quantity = 1) => API.post('/shop/cart/add/', {
            product_id: productId,
            quantity: quantity
        }),
        removeFromCart: (itemId) => API.delete(`/shop/cart/remove/${itemId}/`),
        updateCartItem: (itemId, quantity) => API.put(`/shop/cart/update/${itemId}/`, {
            quantity: quantity
        }),
        clearCart: () => API.delete('/shop/cart/clear/')
    }
};

// Export for global use
window.API = API;
