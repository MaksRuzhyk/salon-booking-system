from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


class MasterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def save(self, *args, **kwargs):
        old_photo_name = None

        if self.pk:
            old_photo_name = (
                MasterProfile.objects.filter(pk=self.pk)
                .values_list('photo', flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        if old_photo_name and old_photo_name != self.photo.name:
            storage = self._meta.get_field('photo').storage
            storage.delete(old_photo_name)

    def __str__(self):
        return self.user.username


@receiver(post_delete, sender=MasterProfile)
def delete_profile_photo(sender, instance, **kwargs):
    if instance.photo:
        instance.photo.delete(save=False)
