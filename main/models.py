from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import http.client
import json


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


class Post(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    slug = models.SlugField(unique=True)
    caption = models.CharField(max_length=100, blank=True, null=True)
    likes = models.IntegerField(default=0)
    photo = models.ImageField(upload_to="post_photos/")

    # i think a post slug is needed for the view post page
    #    post_slug = models.SlugField(unique=True)

    latitude = models.FloatField(blank=False)
    longitude = models.FloatField(blank=False)

    creation_time = models.DateTimeField(auto_now_add=True)

    locationName = models.CharField(max_length=100, editable=False, default="Unknown")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.id)

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

            self.locationName = response["display_name"]

            print(response)
        except Exception as e:
            print(e)
            self.locationName = f"{self.latitude}, {self.longitude}"

        super(Post, self).save(*args, **kwargs)


class Comment(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    comment = models.CharField(max_length=100)

    creation_time = models.DateTimeField(auto_now_add=True)


class Group(models.Model):
    user_owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    name = models.CharField(unique=True, max_length=50)
    slug = models.SlugField(unique=True)
    about = models.CharField(max_length=100)
    is_private = models.BooleanField(default=False)

    creation_time = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Group, self).save(*args, **kwargs)


class GroupMember(models.Model):
    member = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    join_time = models.DateTimeField(auto_now_add=True)


class Report(models.Model):
    pass
