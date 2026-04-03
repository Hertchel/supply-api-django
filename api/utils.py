import threading
import logging
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

_thread_locals = threading.local()

def set_current_user(user):
    """Store the current user in thread local storage."""
    try:
        _thread_locals.user = user
        if user and not isinstance(user, AnonymousUser):
            logger.debug(f"Current user set to: {user}")
    except Exception as e:
        logger.error(f"Error setting current user: {str(e)}")

def get_current_user():
    """Get the current user from thread local storage."""
    try:
        user = getattr(_thread_locals, 'user', None)
        return user if user else None
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None

def clear_current_user():
    """Clear the current user from thread local storage."""
    try:
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
            logger.debug("Current user cleared")
    except Exception as e:
        logger.error(f"Error clearing current user: {str(e)}")

def has_current_user():
    """Check if a current user is set in thread local storage."""
    try:
        user = getattr(_thread_locals, 'user', None)
        return user is not None and user != AnonymousUser()
    except Exception as e:
        logger.error(f"Error checking current user: {str(e)}")
        return False

def get_current_user_id():
    """Get the ID of the current user."""
    try:
        user = get_current_user()
        if user and not isinstance(user, AnonymousUser) and hasattr(user, 'id'):
            return user.id
        return None
    except Exception as e:
        logger.error(f"Error getting current user ID: {str(e)}")
        return None

def get_current_user_role():
    """Get the role of the current user."""
    try:
        user = get_current_user()
        if user and not isinstance(user, AnonymousUser) and hasattr(user, 'is_authenticated') and user.is_authenticated:
            # Get user roles from groups
            if hasattr(user, 'groups'):
                roles = user.groups.values_list('name', flat=True)
                return list(roles)
        return []
    except Exception as e:
        logger.error(f"Error getting current user role: {str(e)}")
        return []

def is_authenticated():
    """Check if the current user is authenticated."""
    try:
        user = get_current_user()
        if user and not isinstance(user, AnonymousUser):
            return hasattr(user, 'is_authenticated') and user.is_authenticated
        return False
    except Exception as e:
        logger.error(f"Error checking authentication: {str(e)}")
        return False