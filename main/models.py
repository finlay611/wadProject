from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
import http.client
import json
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    slug = models.SlugField(unique=True)
    biography = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to="profile_pictures/")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.user.username)
        super(UserProfile, self).save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class Group(models.Model):
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    members = models.ManyToManyField(UserProfile, related_name="groups")

    name = models.CharField(unique=True, max_length=50)
    slug = models.SlugField(unique=True)
    about = models.CharField(max_length=100)
    color = models.CharField(max_length=7)
    # is_private = models.BooleanField(default=False)

    created_time = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Group, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


@receiver(post_save, sender=Group)
def group_creator_is_owner(instance: Group, **kwargs):
    instance.members.add(instance.created_by)


class Post(models.Model):
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)

    slug = models.SlugField(unique=True)
    slug_uuid = models.UUIDField(default=uuid.uuid4)
    caption = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to="post_photos/")

    latitude = models.FloatField(blank=False)
    longitude = models.FloatField(blank=False)

    created_time = models.DateTimeField(auto_now_add=True)

    location_name = models.CharField(max_length=100, editable=False, default="Unknown")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.slug_uuid)

        # Get a place name from OpenStreetMap API
        try:
            conn = http.client.HTTPSConnection("nominatim.openstreetmap.org")

            # User agent is required so that they don't block us because they don't know what we're doing!
            conn.request(
                "GET",
                f"/reverse?lat={self.latitude}&lon={self.longitude}&format=json",
                headers={
                    "User-Agent": "PhotoGraph/1.0 (University of Glasgow student project)"
                },
            )

            response = json.loads(conn.getresponse().read())

            self.location_name = response["display_name"]

            print(response)
        except Exception as e:
            print(e)
            self.location_name = f"{self.latitude}, {self.longitude}"

        super(Post, self).save(*args, **kwargs)


class Comment(models.Model):
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    comment = models.CharField(max_length=100)

    created_time = models.DateTimeField(auto_now_add=True)


class PostReport(models.Model):
    reporter = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporter} on {self.post_id}."

    class Meta:
        verbose_name_plural = "Post Reports"


class UserReport(models.Model):
    reporter = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "User Reports"


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} likes {self.post.slug}"
