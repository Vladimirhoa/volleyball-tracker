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
from video.forms import VideoForm, VideoEditForm
from video.tasks import process_video_task, download_vk_video_task
from video.tasks import process_video_task
from django.urls import reverse
import shutil
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
@login_required
def match_list(request):
    matches = Match.objects.filter(user=request.user).order_by('-date')
    user_videos = Video.objects.filter(user=request.user)
    user_total_size = sum(v.file_size for v in user_videos if v.file_size) or 0

    context = {
        'matches': matches,
        'user_total_size': user_total_size,
    }

    if request.user.is_superuser:
        all_videos = Video.objects.all()
        total_server_size = sum(v.file_size for v in all_videos if v.file_size) or 0
        total, used, free = shutil.disk_usage(settings.MEDIA_ROOT)

        context['total_server_size'] = total_server_size
        context['free_disk_space'] = free

    return render(request, 'match/match_list.html', context)


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

    return render(request, 'match/match_form.html', {'form': form, 'heading': 'Создание матча.'})


@login_required
def video_create(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)

    if request.method == 'POST':
        if request.POST.get('is_chunked') == 'true':
            chunk = request.FILES.get('file')
            file_name = request.POST.get('file_name')
            chunk_index = int(request.POST.get('chunk_index', 0))
            total_chunks = int(request.POST.get('total_chunks', 1))
            title = request.POST.get('title', '')
            description = request.POST.get('description', '')

            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, f"user_{request.user.id}_{file_name}")

            mode = 'ab' if chunk_index > 0 else 'wb'
            with open(temp_file_path, mode) as f:
                for chunk_data in chunk.chunks():
                    f.write(chunk_data)

            if chunk_index == total_chunks - 1:
                with open(temp_file_path, 'rb') as f:
                    video = Video(
                        user=request.user,
                        match=match,
                        title=title or file_name, # Если название не указали, берем имя файла
                        description=description,
                        status='processing'
                    )
                    video.video.save(file_name, File(f), save=False)
                    video.save()

                os.remove(temp_file_path)

                process_video_task.delay(video.id)

                return JsonResponse({
                    'status': 'success',
                    'redirect_url': reverse('match_detail', args=[match.id])
                })

            return JsonResponse({'status': 'uploading'})

        vk_link = request.POST.get('vk_link', '').strip()
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

    return render(request, 'match/video_form.html', {'form': form, 'match': match, 'heading': 'Загрузить видео.'})


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

@login_required
@user_passes_test(lambda u: u.is_superuser)
def custom_admin_dashboard(request):
    users = User.objects.all()
    user_stats = []

    for user in users:
        videos = Video.objects.filter(user=user)
        video_count = videos.count()
        total_size = sum(v.file_size for v in videos if v.file_size) or 0

        user_stats.append({
            'user': user,
            'video_count': video_count,
            'total_size': total_size
        })

    return render(request, 'match/admin_dashboard.html', {'user_stats': user_stats})

@login_required
def video_progress(request, video_id):
    video = get_object_or_404(Video, id=video_id, user=request.user)
    return JsonResponse({
        'status': video.status,
        'progress': video.progress
    })

def public_match_view(request, share_token):
    # Ищем матч по уникальному токену
    match = get_object_or_404(Match, share_token=share_token)
    videos = match.videos.filter(status='ready') # Показываем только готовые видео
    return render(request, 'match/public_match.html', {'match': match, 'videos': videos})

def public_video_view(request, share_token):
    # Ищем видео по уникальному токену
    video = get_object_or_404(Video, share_token=share_token)
    return render(request, 'match/public_video.html', {'video': video})

@login_required
def match_edit(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    if request.method == "POST":
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            return redirect('match_detail', match_id=match.id)
    else:
        form = MatchForm(instance=match)
    return render(request, 'match/match_form.html', {"form": form, "match": match, "heading": "Редактирование матча."})

@login_required
def video_edit(request, video_id):
    video = get_object_or_404(Video, id=video_id, user=request.user)
    match = video.match
    if request.method == "POST":
        form = VideoEditForm(request.POST, instance=video)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'title': video.title,
                    'description': video.description
                })
            return redirect('match_detail', match_id=video.match.id)
    else:
        form = VideoEditForm(instance=video)
    return render(request, 'match/match_form.html', {"form": form, "match": match, "heading": "Редактирование матча."})