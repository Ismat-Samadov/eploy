# users/utils.py

def is_profile_complete(profile):
    # Define your criteria for a complete profile
    required_fields = ['birth_date', 'gender', 'nationality', 'address', 'phone_number']
    for field in required_fields:
        if not getattr(profile, field, None):
            return False
    # Optionally check related fields like experiences, education, etc.
    if not profile.workexperience_set.exists():
        return False
    if not profile.education_set.exists():
        return False
    return True
