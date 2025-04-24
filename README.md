# Olivian Group - Corporate Website Platform

A comprehensive Django-based corporate website solution designed for manufacturing and industrial businesses. This platform offers a complete set of features for showcasing products, services, and projects while providing robust customer engagement tools.

![Olivian Group](screenshot.png)

## Key Features

- **Responsive Design**: Bootstrap-powered responsive layout that works across all devices
- **Multi-language Support**: Built-in internationalization for global audience reach
- **Content Management**: Full admin interface for managing all website content without coding
- **Product Catalog**: Showcase products with detailed specifications, images, and documentation
- **Project Portfolio**: Display completed projects with categorization and image galleries
- **Service Offerings**: Present services with benefits and detailed descriptions
- **Blog System**: Integrated blog with categories, tags, and commenting functionality
- **Customer Engagement**:
  - Live WhatsApp chat widget
  - Quote request system
  - Newsletter subscription
  - Contact forms
- **Team Management**: Showcase company leadership and team members
- **SEO Optimized**: Built with search engine optimization best practices
- **Social Media Integration**: Connect all your social platforms
- **Analytics Ready**: Prepared for integration with tracking tools

## Technical Stack

- **Backend**: Django framework with Python
- **Frontend**: Bootstrap 5, jQuery, Font Awesome
- **Database**: PostgreSQL (configurable)
- **Media Handling**: Django's media management with lightbox gallery integration
- **Admin Interface**: Enhanced with Django Jazzmin for improved UX
- **Authentication**: Custom user model with profile management

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/olivian-group.git
   cd olivian-group
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   DEBUG=True
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgres://user:password@localhost:5432/olivian_db
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

8. Access the admin interface at `http://127.0.0.1:8000/admin/` and start configuring your site.

## Project Structure

- **core**: Main app containing home page, site settings, and shared components
- **products**: Product catalog management
- **services**: Service offerings management
- **projects**: Project portfolio management
- **blog**: Blog system with categories and tags
- **contact**: Contact forms and inquiry management
- **account**: User authentication and profile management
- **chat**: Live chat functionality

## Configuration

### Site Settings

1. Log in to the admin interface
2. Navigate to Core > Site Settings
3. Configure your site name, logo, favicon, and other global settings

### Content Management

The admin interface provides comprehensive tools for managing:
- Navigation menus
- Hero banners
- About sections
- Team members
- Products and categories
- Services
- Projects
- Blog posts
- Contact information
- Footer sections

## Deployment

For production deployment:

1. Set `DEBUG=False` in your environment variables
2. Configure a proper `ALLOWED_HOSTS` setting
3. Set up static files serving with a CDN or web server
4. Configure a production database
5. Use a WSGI server like Gunicorn
6. Set up HTTPS with a valid SSL certificate

Example deployment with Gunicorn and Nginx:
```bash
gunicorn olivian_group.wsgi:application --bind 0.0.0.0:8000
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
- [jQuery](https://jquery.com/)
- [Lightbox](https://lokeshdhakar.com/projects/lightbox2/)
