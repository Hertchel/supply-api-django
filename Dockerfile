
# Python base image
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /django-app

# Install system dependencies required by mysqlclient
RUN apk add --no-cache \
    build-base \
    pkgconf \
    mariadb-connector-c-dev

# Install Python dependencies
COPY requirements.txt /django-app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . /django-app/

# Expose port 8000
EXPOSE 8000

# Run the application using Gunicorn
CMD ["sh", "-c", "gunicorn SupplyAPI.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --threads 2"]
