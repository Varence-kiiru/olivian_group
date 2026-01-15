// Notification manager extracted from templates/dashboard/base.html
class NotificationManager {
    constructor() {
        this.init();
    }

    init() {
        if (this.checkNotificationElements()) {
            this.loadNotifications();
            this.setupEventListeners();
            setInterval(() => this.loadNotifications(), 120000);
        }
    }

    checkNotificationElements() {
        this.notificationCount = document.getElementById('notificationCount');
        this.notificationDropdown = document.getElementById('notificationDropdown');
        this.markAllRead = document.getElementById('markAllRead');
        this.notificationList = document.getElementById('notificationList');
        return !!(this.notificationCount && this.notificationDropdown && this.markAllRead && this.notificationList);
    }

    setupEventListeners() {
        if (this.markAllRead) {
            this.markAllRead.addEventListener('click', (e) => {
                e.preventDefault();
                this.markAllAsRead();
            });
        }

        if (this.notificationDropdown) {
            this.notificationDropdown.addEventListener('shown.bs.dropdown', () => this.loadNotifications());
        }

        // delegation for notification item clicks
        if (this.notificationList) {
            this.notificationList.addEventListener('click', (e) => {
                const item = e.target.closest('.notification-item');
                if (!item) return;
                const id = item.dataset.id;
                const link = item.dataset.link || '';
                this.handleNotificationClick(id, link);
            });
        }
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications/', { credentials: 'same-origin' });
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            this.updateNotificationCount(data.unread_count || 0);
            this.renderNotifications(data.notifications || []);
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    updateNotificationCount(count) {
        if (!this.notificationCount) return;
        this.notificationCount.textContent = count;
        this.notificationCount.style.display = count > 0 ? 'flex' : 'none';
    }

    renderNotifications(notifications) {
        const container = this.notificationList;
        if (!container) return;
        container.innerHTML = '';
        
        // Filter to show only unread notifications
        const unreadNotifications = notifications.filter(n => !n.is_read);
        
        if (unreadNotifications.length === 0) {
            container.innerHTML = `<div class="text-center py-4"><i class="fas fa-bell-slash fa-2x text-muted mb-2"></i><p class="text-muted mb-0">No new notifications</p></div>`;
            return;
        }

        const frag = document.createDocumentFragment();
        unreadNotifications.forEach(n => {
            const div = document.createElement('div');
            div.className = `notification-item unread`;
            div.dataset.id = n.id;
            div.dataset.link = n.link_url || '';
            div.style.cursor = 'pointer';

            // Icon container with notification type icon
            const iconContainer = document.createElement('div');
            iconContainer.className = 'notification-item-icon';
            const icon = document.createElement('i');
            const iconClass = this.getNotificationIcon(n.type || 'info');
            icon.className = iconClass;
            iconContainer.appendChild(icon);

            // Content wrapper - minimal: title + time only
            const contentWrapper = document.createElement('div');
            contentWrapper.style.flex = '1';

            const title = document.createElement('div');
            title.className = 'notification-item-message';
            title.textContent = n.title || '';

            const time = document.createElement('div');
            time.className = 'notification-item-time';
            time.textContent = this.timeAgo(n.created_at || new Date().toISOString());

            contentWrapper.appendChild(title);
            contentWrapper.appendChild(time);

            div.appendChild(iconContainer);
            div.appendChild(contentWrapper);

            frag.appendChild(div);
        });

        container.appendChild(frag);
    }

    async handleNotificationClick(notificationId, linkUrl) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'X-CSRFToken': getCsrfToken(), 'Content-Type': 'application/json' }
            });
            if (response.ok) {
                this.loadNotifications();
                if (linkUrl) window.location.href = linkUrl;
            }
        } catch (error) {
            console.error('Error handling notification click:', error);
        }
    }

    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark-all-read/', { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': getCsrfToken(), 'Content-Type': 'application/json' } });
            if (response.ok) this.loadNotifications();
        } catch (error) { console.error('Error marking all notifications as read:', error); }
    }

    timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }

    getNotificationIcon(type) {
        const iconMap = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle',
            'message': 'fas fa-envelope',
            'alert': 'fas fa-bell',
            'order': 'fas fa-shopping-cart',
            'payment': 'fas fa-credit-card',
            'user': 'fas fa-user',
            'system': 'fas fa-cog'
        };
        return iconMap[type] || iconMap['info'];
    }
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

document.addEventListener('DOMContentLoaded', () => { window.notificationManager = new NotificationManager(); });
