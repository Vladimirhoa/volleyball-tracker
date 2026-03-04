from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Match
from .forms import MatchForm
from video.forms import VideoForm
from .forms import RegisterForm
@login_required
def match_list(request):
    matches = Match.objects.filter(user=request.user).order_by('-date')
    return render(request, 'match/match_list.html', {'matches': matches})


@login_required
def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    videos = match.videos.all()

    return render(request, 'match/match_detail.html', {'match': match, 'videos': videos})

@login_required
def match_create(request):
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            new_match = form.save(commit=False)
            new_match.user = request.user
            new_match.save()
            return redirect('match_list')
    else:
        form = MatchForm()

    return render(request, 'match/match_form.html', {'form': form})


@login_required
def video_create(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)

    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            new_video = form.save(commit=False)
            new_video.user = request.user
            new_video.match = match
            new_video.save()
            return redirect('match_detail', match_id=match.id)
    else:
        form = VideoForm()

    return render(request, 'match/video_form.html', {'form': form, 'match': match})


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})