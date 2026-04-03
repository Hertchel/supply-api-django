import jwt
import logging
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user_model
from .utils import set_current_user, get_current_user

logger = logging.getLogger(__name__)

User = get_user_model()

def get_user_role(user):
    """Get the role of the user from their group."""
    # Add null check for user
    if user is None:
        logger.debug("User is None, returning empty list")
        return []
    
    # Add check for AnonymousUser and is_authenticated
    try:
        if isinstance(user, AnonymousUser):
            logger.debug("User is AnonymousUser, returning empty list")
            return []
        
        if hasattr(user, 'is_authenticated') and user.is_authenticated:
            roles = user.groups.values_list('name', flat=True)  # Get all group names as a list
            logger.debug(f"Roles found for user {user}: {list(roles)}")
            return list(roles)
        else:
            logger.debug(f"User {user} is not authenticated")
            return []
    except Exception as e:
        logger.error(f"Error getting user role: {str(e)}")
        return []

def get_user_from_token(request):
    """Extract user from JWT token in cookies."""
    # Add null check for request
    if request is None:
        logger.error("Request object is None")
        return AnonymousUser()
    
    token = request.COOKIES.get("access_token")
    if token:
        try:
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get("user_id")
            logger.info(f"Decoded user_id: {user_id} from token")
            
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"Authenticated user: {user}")
                    return user
                except User.DoesNotExist:
                    logger.warning(f"User with ID {user_id} does not exist.")
                    return AnonymousUser()
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired.")
        except jwt.DecodeError:
            logger.error("Failed to decode JWT token.")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {str(e)}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while decoding token: {str(e)}")
    else:
        logger.debug("No JWT token found in cookies.")
    
    return AnonymousUser()

class AuthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        logger.debug("Processing request through AuthenticatedUserMiddleware.")
        
        # Initialize user as AnonymousUser by default
        user = AnonymousUser()
        
        try:
            # Extract user from token
            user = get_user_from_token(request)
            logger.debug(f"User extracted from token: {user}")
            
            # Set current user in utils for global access
            set_current_user(user)
            
            # Set request.user with lazy evaluation
            request.user = SimpleLazyObject(lambda: user)
            
            # Get roles for logging purposes
            roles = get_user_role(user)
            logger.debug(f"Roles for user {user}: {roles}")
            
        except Exception as e:
            logger.error(f"Unexpected error in middleware: {str(e)}", exc_info=True)
            # Ensure user is at least AnonymousUser on error
            user = AnonymousUser()
            set_current_user(user)
            request.user = SimpleLazyObject(lambda: user)
        
        # Process the response
        try:
            response = self.get_response(request)
            logger.debug(f'Processed response in AuthenticatedUserMiddleware: {response.status_code}')
            return response
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}", exc_info=True)
            raise