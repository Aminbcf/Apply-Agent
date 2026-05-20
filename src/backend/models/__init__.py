from .job_application import JobApplication
from .user_profile import UserProfile
from .user_profile_version import UserProfileVersion

# Import all models here so that Base.metadata.create_all() finds them when init_db() runs
__all__ = ["UserProfile", "UserProfileVersion", "JobApplication"]

