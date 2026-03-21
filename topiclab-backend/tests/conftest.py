import os


# Tests must never inherit a production DATABASE_URL by accident.
os.environ.setdefault("TOPICLAB_TESTING", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
