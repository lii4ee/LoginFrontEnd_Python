import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hardcoded_dev_key'
    # Use the default 'postgres' database for initial setup
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgre:passig@localhost/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
