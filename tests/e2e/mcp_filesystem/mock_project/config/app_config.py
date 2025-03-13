"""
Application configuration settings
"""

# Flask configuration
SECRET_KEY = 'dev-secret-key-for-testing-only'
DEBUG = True
TESTING = False

# Database configuration
DATABASE_URI = 'sqlite:///mock_project.db'

# API configuration
API_VERSION = 'v1'
API_PREFIX = f'/api/{API_VERSION}'

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Feature flags
ENABLE_REGISTRATION = True
ENABLE_PASSWORD_RESET = True