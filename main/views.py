from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from main.forms import (
    UserForm,
    UserProfileForm,
    CustomPasswordChangeForm,
    ChangeInfoForm,
    PostForm, 
    ReportForm, UserReportForm
)
from django.contrib import messages
from main.models import UserProfile, Post, Comment, PostReport, User, UserReport
from django.views import View

def index(request):
    return render(request, "photoGraph/index.html")


def about(request):
    return render(request, "photoGraph/about.html")


def contact_us(request):
    return render(request, "photoGraph/contact_us.html")


def show_user_profile(request, user_profile_slug):
    context_dict = {}

    try:
        user_profile = UserProfile.objects.get(slug=user_profile_slug)

        if (request.user == user_profile.user):
            return redirect(reverse("main:my_account"))

        user_posts = Post.objects.filter(created_by=user_profile)
        context_dict["user_profile"] = user_profile
        context_dict["posts"] = user_posts

    except UserProfile.DoesNotExist:
        context_dict["user_profile"] = None

    return render(request, "photoGraph/user_profile.html", context=context_dict)

def show_location(request):
    location_name = request.GET.get('location_name', '')
    context_dict = {"location_name": location_name}

    try:
        location_posts = Post.objects.filter(location_name=location_name)
        context_dict["posts"] = location_posts

    except Exception:
        pass

    return render(request, "photoGraph/location.html", context=context_dict)


def view_post(request, user_profile_slug, post_slug):
    context_dict = {}

    try:
        user_profile = UserProfile.objects.get(slug=user_profile_slug)
        post = Post.objects.get(created_by=user_profile, slug=post_slug)
        context_dict["post"] = post

        comments = Comment.objects.filter(post=post)
        context_dict["comments"] = comments

    except (UserProfile.DoesNotExist, Post.DoesNotExist):
        context_dict["post"] = None

    return render(request, "photoGraph/post.html", context=context_dict)


@login_required
def report_post(request, post_id): 
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=PostReport(reporter=request.user.userprofile, post_id=post))
        if form.is_valid():
            form.save()
            return render(request, 'photoGraph/report_post.html', {'post': post, 'form': form, 'show_popup': True})
    else:
        form = ReportForm()
    return render(request, 'photoGraph/report_post.html', {'post': post, 'form': form})

@login_required
def report_detail(request, report_id):
    if not request.user.is_superuser:
        return redirect('main:index')
    
    report = get_object_or_404(PostReport, id=report_id)
    related_reports = PostReport.objects.filter(post_id=report.post_id).exclude(id=report_id)
    reasons = [report.reason] + list(related_reports.values_list('reason', flat=True))
    return render(request, 'photoGraph/report_detail.html', {'report': report, 'reasons': reasons})

@login_required
def delete_post_view(request, post_id):
    if not request.user.is_superuser:
        return redirect('main:index')
    
    post = get_object_or_404(Post, id=post_id)
    post_reports = PostReport.objects.filter(post_id=post.id)

    if request.method == 'POST':
        post_reports.delete()
        post.delete()
        return redirect('admin:main_postreport_changelist')

    return render(request, 'photoGraph/delete_post_report.html', {'post': post})

@login_required
def report_user(request, user_id):
    reported_user = get_object_or_404(UserProfile, user_id=user_id)

    if request.method == 'POST':
        form = UserReportForm(request.POST, instance=UserReport(reporter=request.user.userprofile, user_id=reported_user.user))
        if form.is_valid():
            form.save()
            return render(request, 'photoGraph/report_user.html', {'reported_user': reported_user, 'form': form, 'show_popup': True})
    else:
        form = UserReportForm()
    return render(request, 'photoGraph/report_user.html', {'reported_user': reported_user, 'form': form})

@login_required
def user_report_detail(request, report_id):
    if not request.user.is_superuser:
        return redirect('main:index')

    user_report = get_object_or_404(UserReport, id=report_id)
    related_reports = UserReport.objects.filter(user_id=user_report.user_id).exclude(id=report_id)
    reasons = [user_report.reason] + list(related_reports.values_list('reason', flat=True))

    context = {'report': user_report, 'user_profile': user_report.user_id, 'related_reports': related_reports, 'reasons': reasons}
    return render(request, 'photograph/user_report_detail.html', context)

@login_required
def delete_user_view(request, user_id):
    if not request.user.is_superuser:
        return redirect('main:index')
    
    user_report = get_object_or_404(UserReport, user_id=user_id)
    reported_user = user_report.user_id

    if request.method == 'POST':
        reported_user.delete()
        user_report.delete()
        return redirect('admin:main_userreport_changelist') 

    context = {'report': user_report}
    return render(request, 'main/delete_user_report.html', context)


def signup(request):
    registered = False

    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user

            if "picture" in request.FILES:
                profile.picture = request.FILES["picture"]

            profile.save()
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(
        request,
        "photoGraph/signup.html",
        context={
            "user_form": user_form,
            "profile_form": profile_form,
            "registered": registered,
        },
    )


def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                next = request.POST.get("next", None)
                redirect_url = reverse("main:index")
                if (next):
                    redirect_url = next
                return redirect(redirect_url)
            else:
                return HttpResponse("Your photoGraph account is disabled.")

        else:
            messages.error(request, "Invalid login details supplied. Please try again.")
            return render(request, 'photoGraph/login.html', {'username': username})
    else:
        return render(request, "photoGraph/login.html")


@login_required
def logout_page(request):
    logout(request)
    return redirect(reverse("main:index"))


def update_profile(request):
    form = PasswordResetForm()
    if request.method == "POST":
        form.PasswordResetForm(request.POST)
        form.save(commit=True)


def password_change_view(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save
            update_session_auth_hash(request, user)
            messages.sucess(request, "Password Changed Sucessfully")
            return redirect(
                reverse("photoGraph:my_account")
            )  # should go back to the my account page
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, "photoGraph/passwordChange.html", {"form": form})


def info_change_view(request):
    if request.method == "POST":
        form = ChangeInfoForm(request.user, request.POST)
        if form.is_valid():
            user = form.save
            update_session_auth_hash(request, user)
            messages.sucess(request, "Information Changed Sucessfully")
            return redirect(
                reverse("main:my_account")
            )  # should go back to the my account page
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = ChangeInfoForm(request.user)
    return render(request, "photoGraph/infoChange.html", {"form": form})


@login_required
def my_account(request):
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        user_posts = Post.objects.filter(created_by=request.user.userprofile)
        return render(
            request,
            "photoGraph/my_account.html",
            {"user_profile": user_profile, "posts": user_posts},
        )
    else:
        return redirect(reverse("main:login"))


@login_required
def edit_post(request, postSlug):  # needs a slug for post ID
    post = Post.objects.get(slug=postSlug)
    return render(request, "photoGraph/edit_post.html", {"post": post})


@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.created_by = UserProfile.objects.get(user=request.user)
            post.save()

            return redirect(
                reverse("main:index")
            )
        else:
            print(form.errors)
            messages.error(request, "Please correct the error below.")
    else:
        form = PostForm(initial={
            "latitude": request.GET.get("lat", ""),
            "longitude": request.GET.get("lng", "")
        })

    return render(request, "photoGraph/create_post.html", {"form": form})


POST_FILTER_ON = True


def get_posts_json(request):
    result = {}

    postObjects = []
    # Find bounds
    if POST_FILTER_ON:
        southEast = (float(request.GET.get("seLat")), float(request.GET.get("seLon")))
        northWest = (float(request.GET.get("nwLat")), float(request.GET.get("nwLon")))

        postObjects = Post.objects.filter(
            latitude__gte=southEast[0],
            latitude__lte=northWest[0],
            longitude__gte=northWest[1],
            longitude__lte=southEast[1],
        ).order_by("-likes")
    else:
        postObjects = Post.objects.all().order_by("-likes")

    # Filter posts
    for post in postObjects:

        postDict = {
            "lat": post.latitude,
            "lon": post.longitude,
            "user_name": post.created_by.slug,
            "location_name": post.location_name,
            "location_url": reverse("main:show_location") + "?location_name=" + post.location_name,
            "likes": post.likes,
            "date": post.created_time,
            "caption": post.caption,
            "photo_url": post.photo.url,
            "user_url": reverse("main:show_user_profile", args=[post.created_by.slug]),
            "post_url": reverse("main:view_post", args=[post.created_by.slug, post.slug])
        }
        if post.location_name not in result.keys():
            result[post.location_name] = [postDict]
        else:
            result[post.location_name].append(postDict)

    return JsonResponse(result, safe=False)
