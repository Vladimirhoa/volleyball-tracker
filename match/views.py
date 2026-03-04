import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.core.files import File
from .models import Match
from django.views.decorators.http import require_POST
from video.models import Video
from .forms import MatchForm
from .forms import RegisterForm
from video.forms import VideoForm
from video.tasks import process_video_task, download_vk_video_task
from video.tasks import process_video_task
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
        vk_link = request.POST.get('vk_link', '').strip()

        # 1. Если пользователь вставил ссылку ВК
        if vk_link:
            video = Video.objects.create(
                user=request.user,
                match=match,
                title=request.POST.get('title') or 'Видео из ВК',
                description=request.POST.get('description', ''),
                status='processing'
            )
            download_vk_video_task.delay(video.id, vk_link)
            return redirect('match_detail', match_id=match.id)

        # 2. Обычная загрузка файла с компьютера
        else:
            form = VideoForm(request.POST, request.FILES)
            if form.is_valid():
                new_video = form.save(commit=False)
                new_video.user = request.user
                new_video.match = match
                new_video.status = 'processing'
                new_video.save()

                if new_video.video:
                    process_video_task.delay(new_video.id)

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


@login_required
@require_POST
def match_delete(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)

    for video in match.videos.all():
        if video.video and os.path.isfile(video.video.path):
            os.remove(video.video.path)

    match.delete()
    return redirect('match_list')


@login_required
@require_POST
def video_delete(request, video_id):
    video = get_object_or_404(Video, id=video_id, user=request.user)
    match_id = video.match.id if video.match else None

    if video.video and os.path.isfile(video.video.path):
        os.remove(video.video.path)

    video.delete()

    if match_id:
        return redirect('match_detail', match_id=match_id)
    return redirect('match_list')