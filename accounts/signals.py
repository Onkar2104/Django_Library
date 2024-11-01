from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_delete, sender=User)
def post_delete_user(sender, instance, **kwargs):
    # Ensure you're not accessing instance attributes that don't exist anymore
    print(f"Deleted user: {instance.email}")  
