from .job_application import JobApplication
from .user_profile import UserProfile

# Import all models here so that Base.metadata.create_all() finds them when init_db() runs
__all__ = ["UserProfile", "JobApplication"]
