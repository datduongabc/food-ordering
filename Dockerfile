FROM php:8.2-apache

# Install system dependencies, PostgreSQL/MySQL PDO drivers & OPcache for fast response times
RUN apt-get update && apt-get install -y \
    libpq-dev \
    unzip \
    git \
    && docker-php-ext-install pdo pdo_pgsql pgsql pdo_mysql opcache \
    && a2enmod rewrite headers expires deflate \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Configure PHP OPcache for high performance
RUN { \
    echo 'opcache.enable=1'; \
    echo 'opcache.memory_consumption=128'; \
    echo 'opcache.interned_strings_buffer=16'; \
    echo 'opcache.max_accelerated_files=10000'; \
    echo 'opcache.validate_timestamps=1'; \
    echo 'opcache.revalidate_freq=0'; \
    } > /usr/local/etc/php/conf.d/opcache-recommended.ini

# Set Apache DocumentRoot to /var/www/html/public and optimize Apache settings
ENV APACHE_DOCUMENT_ROOT=/var/www/html/public
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf \
    && sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf \
    && echo "ServerName localhost" >> /etc/apache2/apache2.conf \
    && echo "HostnameLookups Off" >> /etc/apache2/apache2.conf \
    && echo "KeepAlive On" >> /etc/apache2/apache2.conf \
    && echo "EnableMMAP Off" >> /etc/apache2/apache2.conf \
    && echo "EnableSendfile Off" >> /etc/apache2/apache2.conf

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Install PHP dependencies
COPY composer.json composer.lock* ./
RUN composer install --no-dev --optimize-autoloader --no-interaction \
    || composer update --no-dev --optimize-autoloader --no-interaction

# Copy application source
COPY . .

# Ensure image upload directories are writable by Apache
RUN chown -R www-data:www-data /var/www/html/public/images

EXPOSE 80
