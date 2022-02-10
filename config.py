import os
PROJECT_ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.dirname(__file__)))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + PROJECT_ROOT + '/data/recommendations'
