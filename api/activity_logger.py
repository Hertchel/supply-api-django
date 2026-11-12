from django.contrib.contenttypes.models import ContentType

from .models import RecentActivity
from .middleware import get_user_role


def log_activity(user, activity_type, target):
    """
    Record an activity performed by an authenticated user.

    user: The user who performed the action.
    activity_type: Added, Updated, Deleted, Registered,
                   Logged in, Logged out, or Activated.
    target: The model instance associated with the activity.
    """

    if not user or not user.is_authenticated:
        return

    if target is None:
        return

    RecentActivity.objects.create(
        user=user,
        user_role=get_user_role(user),
        activity_type=activity_type,
        content_type=ContentType.objects.get_for_model(target),
        object_id=str(target.pk),
    )