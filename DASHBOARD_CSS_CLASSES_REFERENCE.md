# Dashboard CSS Classes Reference Guide

## Sidebar Components

### `.sidebar`
Fixed positioning, gradient background, 100vh height, z-index 1000.
- **States**: `.collapsed` (80px width), `.show` (full width on mobile overlay)
- **Mobile**: Off-canvas from left, hidden by default at <992px

### `.sidebar-overlay`
Semi-transparent dark overlay, appears behind sidebar on mobile.
- **States**: `.show` (opacity 1, visible)
- **Mobile**: Full screen, z-index 999, auto-created by JS

### `.sidebar-brand`
Container for logo/brand name.
- Hides text span when `.sidebar.collapsed`
- Padding: 1.5rem, border-bottom separator

### `.nav-section`
Groups related navigation items.
- Margin-bottom: 2rem
- `.nav-section-title` styled as uppercase label (hidden when sidebar collapsed)

### `.nav-link`
Individual navigation item.
- Flexbox, centered vertically
- Highlight bar on left (4px, animated with scaleY)
- States: `:hover`, `.active`
- Icons: 20px width, Font Awesome compatible
- Mobile touch target: min-height 44px

---

## Topbar Components

### `.topbar`
Sticky header, white background, 70px height.
- Flexbox: space-between layout
- Box-shadow for depth
- z-index 100 (above content, below modals)
- **Mobile**: Height reduced to 65px (<768px), padding reduced to 0.75rem

### `.topbar-left`
Contains hamburger toggle and breadcrumb.
- Flexbox with gap: 1rem
- Responsive gap reduction on mobile
- Min-width: 0 (flex shrinking enabled)

### `.topbar-right`
Contains notification bell and user dropdown.
- Flexbox with gap: 1rem
- Responsive gap reduction: 0.5rem (<768px), 0.25rem (<576px)

### `.sidebar-toggle`
Hamburger menu button.
- No background by default
- Hover: light background + primary color
- **Size**: 44px × 44px (desktop), 40px × 40px (mobile), 36px × 36px (small mobile)
- Font-size responsive: 1.2rem → 1rem → 0.9rem

### `.breadcrumb`
Navigation breadcrumb trail.
- Hidden on mobile (<768px)
- Only `.breadcrumb-item.active` shown on mobile
- Link color: primary-color

---

## Notification System

### `.topbar-notification`
Bell icon button.
- Icon size: 1.4rem
- Min-width/height: 44px (touch target)
- Border-radius: 8px
- Hover: light background + primary color
- Active: scale(0.95) feedback

### `.notification-badge`
Red circular badge showing unread count.
- Position: absolute, top: -8px, right: -5px
- Size: 22px × 22px
- Font: 0.65rem, bold, white, center-aligned
- White border: 2px
- Hidden when empty (display: none if textContent is empty)
- Shadow: 0 2px 8px rgba(220, 53, 69, 0.3)

### `.notification-dropdown`
Dropdown container for notifications.
- Max-width: 400px (responsive reduction on mobile)
- Border-radius: 12px
- Box-shadow: var(--shadow-lg)
- Animation: slideDown (0.3s ease-out)

### `.notification-dropdown .dropdown-header`
Header with "Notifications" title.
- Background: gradient (primary-light to primary)
- Color: white
- Border-radius: 12px 12px 0 0
- Padding: 1rem 1.25rem
- Contains "Mark all read" button

### `.notification-item`
Individual notification in list.
- Padding: 1rem
- Border-bottom separator
- States: `:hover` (light background), `.unread` (light blue left border)
- Cursor: pointer
- Flex layout for icon + content

### `.notification-item.unread`
Unread notification variant.
- Background: #f0f7ff (light blue)
- Left border: 4px solid primary-color

### `.notification-item-icon`
Icon inside notification (1.25rem).

### `.notification-item-text`
Text container (title + time).
- Flex: 1 (grows to fill space)

### `.notification-item-message`
Message text.
- Font-size: 0.9rem
- Color: dark-color
- Margin-bottom: 0.25rem

### `.notification-item-time`
Timestamp text.
- Font-size: 0.75rem
- Color: #999
- Lighter gray color

---

## User Account Area

### `.topbar-user`
Container for user avatar + name/dropdown.
- Flexbox, gap: 0.5rem
- Display: flex, align-items: center

### `.user-avatar`
Circular user profile indicator.
- Size: 40px × 40px
- Border-radius: 50% (circle)
- Background: primary-color (fallback if no image)
- Color: white (for initials)
- Font-weight: 600, font-size: 0.9rem
- Border: 2px solid white
- Box-shadow: 0 2px 8px rgba(56, 182, 255, 0.2)
- **With image**: `<img>` fills 100%, object-fit: cover

### `.user-dropdown`
Dropdown menu container.
- **State**: `.show` (Bootstrap dropdown open)

### `.user-dropdown .dropdown-toggle`
Trigger button for dropdown.
- **Default arrow**: removed (`::after { display: none }`)
- Displays avatar + username

### `.user-dropdown .dropdown-menu`
Dropdown menu list.
- Min-width: 220px
- Border-radius: 12px
- Box-shadow: var(--shadow-lg)
- Border: 1px solid #e3e6f0
- Padding: 0.5rem 0

### `.user-dropdown .dropdown-item`
Individual menu item (Profile, Settings, Logout).
- Padding: 0.75rem 1rem
- Color: dark-color
- Hover/Focus: light-color background + primary-color text
- Transition: all 0.3s ease

### `.user-dropdown .dropdown-divider`
Visual separator between groups.
- Margin: 0.25rem 0 (compact)

### `.user-dropdown .dropdown-header`
Section header (if any).
- Padding: 0.75rem 1rem
- Color: dark-color
- Font-weight: 600
- Font-size: 0.9rem

---

## Floating Chat Button

### `.floating-chat-icon`
Container for chat button.
- Position: fixed
- Bottom: 30px, Right: 30px
- Z-index: 1050 (above most content)
- **Mobile**: Bottom: 20px, Right: 20px (<576px)

### `.chat-button`
Circular floating action button.
- Size: 60px × 60px
- Border-radius: 50% (circle)
- Background: gradient (primary to primary-dark)
- Color: white
- Border: 3px solid white
- Font-size: 1.4rem
- Box-shadow: 0 4px 20px rgba(56, 182, 255, 0.3)
- Hover: scale(1.1), shadow increases
- Active: scale(0.95) feedback
- Transition: all 0.3s ease
- **Mobile sizes**: 50px × 50px (tablet), 45px × 45px (<576px)

### `.chat-badge`
Notification count badge on chat button.
- Position: absolute, top: -8px, right: -5px
- Size: 22px × 22px
- Background: danger-color (red)
- Color: white
- Font: 0.65rem, bold
- Border-radius: 50%
- Border: 2px solid white
- Display: flex (always visible if has content)

---

## Content Area

### `.main-content`
Main page content wrapper.
- Margin-left: var(--sidebar-width) (desktop)
- Margin-left: 0 (mobile <992px)
- Min-height: 100vh
- Transition: margin-left 0.3s ease

### `.content-area`
Padding container for page content.
- Padding: 2rem (desktop), 1.5rem 1rem (tablet), 1rem (mobile)
- Responsive adjustments for small screens

### `.page-header`
Title + subtitle section.
- Margin-bottom: responsive (2rem → 1.5rem → 1rem)

### `.page-title`
H1-style page title.
- Font-size: 1.75rem (desktop), 1.4rem (tablet), 1.2rem (mobile)
- Font-weight: 700
- Color: dark-color
- Margin-bottom: 0.5rem

### `.page-subtitle`
Descriptive subtitle.
- Font-size: 0.95rem (desktop), 0.85rem (mobile)
- Color: #666

---

## Card Components

### `.card`
Content card wrapper.
- Border: none
- Border-radius: 10px (12px on mobile for consistency)
- Box-shadow: var(--shadow)
- Margin-bottom: 1.5rem (responsive)
- Background: white
- **Responsive**: border-radius 8px (<768px), margin-bottom 1rem

### `.card-header`
Card title/header section.
- Background: white
- Border-bottom: 1px solid #e3e6f0
- Padding: 1.25rem (responsive: 1rem)
- Border-radius: 10px 10px 0 0 (top corners only)

### `.card-title`
Title inside card header.
- Font-size: 1.1rem (responsive: 1rem)
- Font-weight: 600
- Color: dark-color
- Margin: 0

### `.card-body`
Main content area of card.
- Padding: 1.25rem (responsive: 1rem)

---

## Table Components

### `.table`
Data table styling.
- **Responsive**: Font-size 0.85rem (<768px), 0.75rem (<576px)
- Margin-bottom: 1rem

### `.table thead th`
Table header cell.
- **Mobile**: Padding 0.75rem 0.5rem (<768px), font-size 0.8rem
- **Small mobile**: Padding 0.5rem 0.25rem (<576px), font-size 0.7rem

### `.table td`
Table data cell.
- **Mobile**: Padding responsive (same as thead)

### `.table-responsive`
Container for scrollable tables.
- Border-radius: 8px
- Overflow: hidden
- Responsive font-size adjustments

---

## Button Components

### `button`, `.btn`
All buttons enforce accessibility sizing.
- Min-height: 44px
- Min-width: 44px
- Transition: all 0.3s ease
- **Mobile**: Font-size 0.9rem, padding 0.5rem 1rem

### `.btn-small`, `.btn-sm`
Small variant buttons.
- Min-height: 36px
- Min-width: 36px
- **Mobile**: Font-size 0.8rem, padding 0.4rem 0.6rem

---

## Utility Classes

### `.text-primary`
Primary color text (`--primary-color`).

### `.bg-primary`
Primary color background.

### `.border-primary`
Primary color border.

### `.loading-spinner`
Animated loading indicator.
- 30px × 30px
- Border: 3px solid #f3f3f3, top: primary-color
- Rotation animation (spin)

### `.system-messages`
Container for toast notifications.
- Position: fixed, top: 80px, right: 20px
- Z-index: 9999
- Max-width: 400px, responsive width: 100%

### `.message-alert`
Individual alert toast.
- Margin-bottom: 10px
- Border: none, border-radius: 12px
- Box-shadow: 0 4px 20px rgba(0,0,0,0.15)
- Backdrop-filter: blur(10px)
- Animation: slideInRight (0.5s ease-out)

---

## Animations

### `@keyframes spin`
Loading spinner rotation.
- 0%: rotate(0deg)
- 100%: rotate(360deg)
- Duration: 1s, linear

### `@keyframes slideInRight`
Toast notification entrance.
- from: translateX(100%), opacity: 0
- to: translateX(0), opacity: 1
- Duration: 0.5s ease-out

### `@keyframes slideDown`
Notification dropdown entrance.
- from: translateY(-10px), opacity: 0
- to: translateY(0), opacity: 1
- Duration: 0.3s ease-out

### `@keyframes fadeIn`
Overlay entrance.
- from: opacity: 0
- to: opacity: 1
- Duration: 0.3s ease

---

## Responsive Media Queries Summary

| Breakpoint | Use Case | Key Changes |
|-----------|----------|-------------|
| **≤991px** | Tablet/Mobile | Sidebar becomes off-canvas, main-content full width |
| **≤768px** | Mobile | Reduced padding, smaller fonts, hidden breadcrumb |
| **≤576px** | Small Mobile | Minimal padding, optimized spacing, smaller buttons |

---

## Touch Target Sizes (Accessibility)
- **Primary buttons**: 44px × 44px minimum
- **Secondary buttons**: 40px × 40px minimum (when grouped)
- **Small buttons**: 36px × 36px minimum
- **Icons**: 44px minimum surrounding space
- **Dropdowns**: Min-width 200px, comfortable touch zone

---

## Transitions & Animations
All transitions use `var(--transition)` which defaults to `all 0.3s ease` for consistency.

---

## Color Variables Reference
- `--primary-color`: #38b6ff (Light Blue)
- `--primary-dark`: #2c8fd6 (Darker Blue)
- `--primary-light`: #5cc3ff (Lighter Blue)
- `--dark-color`: #2c3e50 (Dark Gray)
- `--light-color`: #f8f9fa (Light Gray/White)
- `--danger-color`: #dc3545 (Red, for badges/alerts)
- `--success-color`: #28a745 (Green)
- `--warning-color`: #ffc107 (Yellow)
- `--info-color`: #17a2b8 (Teal)

