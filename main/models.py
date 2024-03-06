from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.utils import timezone


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

    latitude = models.FloatField(blank=False)
    longitude = models.FloatField(blank=False)

    about_time = models.DateField(blank=True, null=True)
    post_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.id)
        self.post_time = timezone.now()
        super(Post, self).save(*args, **kwargs)


class Comment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    comment = models.CharField(max_length=100)
    comment_time = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        self.comment_time = timezone.now()
        super(Comment, self).save(*args, **kwargs)


class Group(models.Model):
    user_owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
