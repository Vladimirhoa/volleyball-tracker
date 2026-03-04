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
        is_chunked = request.POST.get('is_chunked') == 'true'

        if is_chunked:
            file_chunk = request.FILES.get('file')
            file_name = request.POST.get('file_name')
            chunk_index = int(request.POST.get('chunk_index', 0))
            total_chunks = int(request.POST.get('total_chunks', 1))

            # Папка для временных файлов
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, f"{request.user.id}_{file_name}")

            mode = 'ab' if chunk_index > 0 else 'wb'
            with open(temp_file_path, mode) as f:
                for chunk in file_chunk.chunks():
                    f.write(chunk)

            if chunk_index == total_chunks - 1:
                title = request.POST.get('title', '')
                description = request.POST.get('description', '')

                video = Video(
                    user=request.user,
                    match=match,
                    title=title,
                    description=description,
                )
                with open(temp_file_path, 'rb') as f:
                    video.video.save(file_name, File(f), save=True)
                os.remove(temp_file_path)

                return JsonResponse({'status': 'success', 'redirect_url': f'/match/{match.id}/'})
            return JsonResponse({'status': 'uploading', 'chunk': chunk_index})

        else:
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