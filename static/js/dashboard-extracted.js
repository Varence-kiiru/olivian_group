// Sidebar toggle and mobile navigation management
document.addEventListener('DOMContentLoaded', function () {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    
    // Create overlay element if it doesn't exist
    let overlay = document.querySelector('.sidebar-overlay');
    if (!overlay && sidebar) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }

    // Helper: persist and restore sidebar scroll position (per session)
    const SIDEBAR_SCROLL_KEY = 'sidebarScrollTop';
    function saveSidebarScroll() {
        try {
            if (sidebar) sessionStorage.setItem(SIDEBAR_SCROLL_KEY, String(sidebar.scrollTop || 0));
        } catch (e) { /* ignore */ }
    }

    function restoreSidebarScroll() {
        try {
            const val = sessionStorage.getItem(SIDEBAR_SCROLL_KEY);
            if (sidebar && val !== null) sidebar.scrollTop = parseInt(val, 10) || 0;
        } catch (e) { /* ignore */ }
    }

    function scrollActiveIntoView() {
        try {
            // prefer .nav-link.active, fallback to first visible nav-link
            const active = sidebar.querySelector('.nav-link.active');
            const target = active || sidebar.querySelector('.nav-link');
            if (!target) return;
            // if target is already visible, don't change user's scroll
            const rect = target.getBoundingClientRect();
            const sidebarRect = sidebar.getBoundingClientRect();
            if (rect.top < sidebarRect.top || rect.bottom > sidebarRect.bottom) {
                // center the active item within the sidebar viewport
                const offset = target.offsetTop - Math.round(sidebar.clientHeight / 2) + Math.round(target.clientHeight / 2);
                sidebar.scrollTo({ top: offset, behavior: 'smooth' });
            }
        } catch (e) { /* ignore */ }
    }

    if (sidebar && sidebarToggle) {
        // Toggle sidebar on button click
        sidebarToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            if (window.innerWidth < 992) {
                // Mobile: toggle .show class for overlay and preserve scroll
                const becomingVisible = !sidebar.classList.contains('show');
                sidebar.classList.toggle('show');
                if (overlay) overlay.classList.toggle('show');

                if (becomingVisible) {
                    // restore previous scroll position and ensure active item is visible
                    restoreSidebarScroll();
                    // small timeout so layout settles before scrolling
                    setTimeout(scrollActiveIntoView, 80);
                } else {
                    // save current scroll so we can restore next time
                    saveSidebarScroll();
                }
            } else {
                // Desktop: toggle collapsed state
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            }
        });

        // Load sidebar collapsed state on desktop
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (window.innerWidth >= 992 && sidebarCollapsed) {
            sidebar.classList.add('collapsed');
        }

        // Close sidebar when clicking outside (mobile)
        function closeSidebarOnOutsideClick(e) {
            if (window.innerWidth < 992) {
                const isClickInsideSidebar = sidebar.contains(e.target);
                const isClickOnToggle = sidebarToggle.contains(e.target);
                const isClickOnNavLink = e.target.closest('.nav-link');
                const isClickOnDropdownToggle = e.target.closest('.dropdown-toggle');
                const isClickOnSubmenu = e.target.closest('.dropdown-menu-nav');
                
                if (!isClickInsideSidebar && !isClickOnToggle) {
                    saveSidebarScroll();
                    sidebar.classList.remove('show');
                    if (overlay) overlay.classList.remove('show');
                }

                // Close when clicking nav link on mobile - BUT NOT dropdown toggles or submenu items
                if (isClickOnNavLink && !isClickOnDropdownToggle && !isClickOnSubmenu && window.innerWidth < 992) {
                    saveSidebarScroll();
                    sidebar.classList.remove('show');
                    if (overlay) overlay.classList.remove('show');
                }
            }
        }

        // Close overlay when clicking on it
        if (overlay) {
            overlay.addEventListener('click', function () {
                saveSidebarScroll();
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            });
        }

        document.addEventListener('click', closeSidebarOnOutsideClick);

        // Handle window resize
        window.addEventListener('resize', function () {
            if (window.innerWidth >= 992) {
                saveSidebarScroll();
                sidebar.classList.remove('show');
                if (overlay) overlay.classList.remove('show');
                // Restore desktop state
                const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
                if (collapsed && !sidebar.classList.contains('collapsed')) {
                    sidebar.classList.add('collapsed');
                }
            }
        });
    }

    // Add active class to current nav link (with safe guards)
    try {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.sidebar .nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href && href !== '#' && currentPath.includes(href)) {
                link.classList.add('active');
            }
        });
    } catch (e) {
        console.error('Error setting active nav link:', e);
    }

    // Restore sidebar scroll and ensure active item is visible on initial load
    try {
        // If sidebar is currently visible (e.g., desktop or left open), restore scroll
        restoreSidebarScroll();
        // Small delay to allow layout to settle, then center active item
        setTimeout(scrollActiveIntoView, 80);
    } catch (e) { /* ignore */ }

    // --- Accessibility & Deep-open Submenu Enhancements ---
    try {
        // Ensure sidebar nav has proper role
        const sidebarNav = sidebar.querySelector('.sidebar-nav');
        if (sidebarNav) {
            sidebarNav.setAttribute('role', 'navigation');
            sidebarNav.setAttribute('aria-label', 'Main navigation');
        }

        // Ensure dropdown toggles have aria-controls and proper aria-expanded state
        const dropdownToggles = sidebar.querySelectorAll('.nav-link.dropdown-toggle');
        dropdownToggles.forEach(toggle => {
            const target = toggle.getAttribute('data-bs-target') || toggle.getAttribute('href');
            if (target && target.startsWith('#')) {
                const id = target.slice(1);
                toggle.setAttribute('aria-controls', id);
                const panel = document.getElementById(id);
                const isShown = panel && panel.classList.contains('show');
                toggle.setAttribute('aria-expanded', isShown ? 'true' : 'false');
            }
            // mark as having a popup
            toggle.setAttribute('aria-haspopup', 'true');
        });

        // Deep-open any submenu that contains an active link
        const collapsePanels = sidebar.querySelectorAll('.collapse');
        collapsePanels.forEach(panel => {
            try {
                if (panel.querySelector('.nav-link.active')) {
                    // Use Bootstrap Collapse API if available
                    if (window.bootstrap && bootstrap.Collapse) {
                        const inst = bootstrap.Collapse.getOrCreateInstance(panel, { toggle: false });
                        inst.show();
                    } else {
                        panel.classList.add('show');
                    }
                    // Ensure the toggle reflects expanded state
                    const toggle = sidebar.querySelector(`[data-bs-target="#${panel.id}"]`);
                    if (toggle) toggle.setAttribute('aria-expanded', 'true');
                }
            } catch (e) { /* ignore per-panel errors */ }
        });

        // Keyboard navigation: arrow keys to move focus between links, Enter/Space to activate
        sidebar.addEventListener('keydown', function (e) {
            const KEY = { DOWN: 'ArrowDown', UP: 'ArrowUp', HOME: 'Home', END: 'End', ENTER: 'Enter', SPACE: ' ' };
            const focusable = Array.from(sidebar.querySelectorAll('.nav-link')).filter(n => n.offsetParent !== null);
            if (!focusable.length) return;
            const activeEl = document.activeElement;
            const idx = focusable.indexOf(activeEl);

            if (e.key === KEY.DOWN) {
                e.preventDefault();
                const next = focusable[(idx + 1) % focusable.length];
                next.focus();
            } else if (e.key === KEY.UP) {
                e.preventDefault();
                const prev = focusable[(idx - 1 + focusable.length) % focusable.length];
                prev.focus();
            } else if (e.key === KEY.HOME) {
                e.preventDefault();
                focusable[0].focus();
            } else if (e.key === KEY.END) {
                e.preventDefault();
                focusable[focusable.length - 1].focus();
            } else if (e.key === KEY.ENTER || e.key === KEY.SPACE) {
                // If focused element is a dropdown toggle, trigger click to open submenu
                if (activeEl && activeEl.classList.contains('dropdown-toggle')) {
                    e.preventDefault();
                    activeEl.click();
                }
            }
        });
    } catch (e) {
        console.error('Sidebar accessibility enhancements error:', e);
    }

    // --- Sidebar search, pinned items, collapsed tooltips, and touch gestures ---
    try {
        // Insert search input under brand (if not already present)
        (function initSidebarSearch() {
            const brand = sidebar.querySelector('.sidebar-brand');
            if (!brand) return;
            if (sidebar.querySelector('.sidebar-search')) return; // already added

            const searchWrap = document.createElement('div');
            searchWrap.className = 'sidebar-search';
            searchWrap.innerHTML = `<input type="search" aria-label="Search navigation" placeholder="Search menu...">`;
            brand.insertAdjacentElement('afterend', searchWrap);

            const input = searchWrap.querySelector('input');
            function filterMenu(q) {
                const term = String(q || '').trim().toLowerCase();
                const links = sidebar.querySelectorAll('.sidebar .nav-link');
                links.forEach(link => {
                    const text = (link.textContent || '').trim().toLowerCase();
                    const visible = term === '' || text.indexOf(term) !== -1;
                    link.style.display = visible ? '' : 'none';
                });
                // also hide section titles that have no visible children
                sidebar.querySelectorAll('.nav-section').forEach(section => {
                    const anyVisible = Array.from(section.querySelectorAll('.nav-link')).some(a => a.style.display !== 'none');
                    section.style.display = anyVisible ? '' : 'none';
                });
            }
            input.addEventListener('input', (e) => filterMenu(e.target.value));
        })();

        // Pinned items: create a small pinned container and allow pinning nav links
        (function initPinnedItems() {
            const nav = sidebar.querySelector('.sidebar-nav');
            if (!nav) return;
            if (sidebar.querySelector('.pinned-section')) return;

            const pinnedSection = document.createElement('div');
            pinnedSection.className = 'pinned-section';
            pinnedSection.innerHTML = `<div class="section-title">Pinned</div><div class="pinned-list" aria-live="polite"></div>`;
            nav.insertAdjacentElement('afterbegin', pinnedSection);
            const pinnedList = pinnedSection.querySelector('.pinned-list');

            const STORAGE_KEY = 'sidebarPinned';
            function getPinned() {
                try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch (e) { return []; }
            }
            function setPinned(arr) { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(arr)); } catch (e) {} }

            function renderPinned() {
                pinnedList.innerHTML = '';
                const pinned = getPinned();
                if (!pinned.length) { pinnedSection.style.display = 'none'; return; }
                pinnedSection.style.display = '';
                pinned.forEach(href => {
                    const orig = sidebar.querySelector(`.nav-link[href="${href}"]`);
                    if (!orig) return;
                    const clone = orig.cloneNode(true);
                    // remove nested pin buttons to avoid recursion
                    const btn = clone.querySelector('.pin-btn'); if (btn) btn.remove();
                    clone.addEventListener('click', (e) => {
                        // close sidebar on mobile when navigating from pinned
                        if (window.innerWidth < 992) { saveSidebarScroll(); sidebar.classList.remove('show'); if (overlay) overlay.classList.remove('show'); }
                    });
                    pinnedList.appendChild(clone);
                });
            }

            // Add pin buttons to all nav links
            sidebar.querySelectorAll('.sidebar .nav-link').forEach(link => {
                // avoid adding pin button to dropdown toggles that are not real destinations
                const href = link.getAttribute('href');
                if (!href || href === '#') return;
                const btn = document.createElement('button');
                btn.className = 'pin-btn';
                btn.setAttribute('aria-pressed', 'false');
                btn.title = 'Pin to top';
                btn.innerHTML = '<i class="fas fa-thumbtack"></i>';
                btn.addEventListener('click', (ev) => {
                    ev.stopPropagation(); ev.preventDefault();
                    const current = getPinned();
                    const idx = current.indexOf(href);
                    if (idx === -1) { current.unshift(href); btn.classList.add('pinned'); btn.setAttribute('aria-pressed','true'); }
                    else { current.splice(idx,1); btn.classList.remove('pinned'); btn.setAttribute('aria-pressed','false'); }
                    setPinned(current.slice(0,12)); // limit pins
                    renderPinned();
                });
                // insert pin button if not already present
                if (!link.querySelector('.pin-btn')) link.appendChild(btn);
            });

            // initialize pin button visual state
            const currentPinned = getPinned();
            sidebar.querySelectorAll('.sidebar .nav-link').forEach(link => {
                const href = link.getAttribute('href');
                const btn = link.querySelector('.pin-btn');
                if (!btn) return;
                if (currentPinned.indexOf(href) !== -1) { btn.classList.add('pinned'); btn.setAttribute('aria-pressed','true'); }
            });

            renderPinned();
        })();

        // Initialize collapsed tooltips using Bootstrap (when collapsed)
        (function initCollapsedTooltips() {
            function updateTooltips() {
                // remove existing titles we added previously
                sidebar.querySelectorAll('.nav-link').forEach(link => {
                    if (!sidebar.classList.contains('collapsed')) {
                        // remove title attribute to avoid duplicate tooltips
                        if (link.dataset.autoTitle) { link.removeAttribute('title'); delete link.dataset.autoTitle; }
                    } else {
                        // add title set from inner text
                        if (!link.getAttribute('title')) {
                            const txt = (link.textContent || '').trim();
                            link.setAttribute('title', txt);
                            link.dataset.autoTitle = 'true';
                        }
                    }
                });
                // (re)initialize bootstrap tooltips if bootstrap present
                if (window.bootstrap && bootstrap.Tooltip) {
                    // destroy existing tip instances to avoid duplicates
                    const tips = sidebar.querySelectorAll('[data-bs-original-title]');
                    tips.forEach(el => {
                        const inst = bootstrap.Tooltip.getInstance(el);
                        if (inst) inst.dispose();
                    });
                    // init new tooltips for visible titles
                    sidebar.querySelectorAll('.nav-link[title]').forEach(el => new bootstrap.Tooltip(el));
                }
            }
            // run on load and on collapse changes
            updateTooltips();
            const observer = new MutationObserver(updateTooltips);
            observer.observe(sidebar, { attributes: true, attributeFilter: ['class'] });
        })();

        // Basic touch gestures: swipe to open/close sidebar on small screens
        (function initTouchGestures() {
            if (!('ontouchstart' in window)) return;
            let startX = 0;
            let startY = 0;
            let tracking = false;

            document.addEventListener('touchstart', function (e) {
                if (e.touches.length !== 1) return;
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
                tracking = true;
            }, { passive: true });

            document.addEventListener('touchmove', function (e) {
                if (!tracking) return;
                const dx = e.touches[0].clientX - startX;
                const dy = e.touches[0].clientY - startY;
                if (Math.abs(dy) > Math.abs(dx)) { tracking = false; return; } // vertical scroll, ignore
                // swipe right to open when near left edge
                if (dx > 60 && startX < 40 && window.innerWidth < 992) {
                    sidebar.classList.add('show'); if (overlay) overlay.classList.add('show'); restoreSidebarScroll(); setTimeout(scrollActiveIntoView,80); tracking = false;
                }
                // swipe left to close when open
                if (dx < -60 && sidebar.classList.contains('show') && window.innerWidth < 992) {
                    saveSidebarScroll(); sidebar.classList.remove('show'); if (overlay) overlay.classList.remove('show'); tracking = false;
                }
            }, { passive: true });

            document.addEventListener('touchend', function () { tracking = false; });
        })();

    } catch (e) {
        console.error('Sidebar enhancements init error:', e);
    }
});
