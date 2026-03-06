import os
import subprocess
import uuid
import yt_dlp
from celery import shared_task
from .models import Video
from django.core.files import File
import time
from celery import shared_task
from django.conf import settings
import re


@shared_task
def process_video_task(video_id):
    try:
        video = Video.objects.get(id=video_id)
        input_path = video.video.path
        output_path = f"{input_path}_compressed.mp4"

        duration_cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', input_path
        ]
        result = subprocess.run(duration_cmd, stdout=subprocess.PIPE, text=True)
        total_duration = float(result.stdout.strip())
        command = [
            'ffmpeg', '-y', '-i', input_path,
            '-vcodec', 'libx264', '-crf', '28', '-preset', 'fast',
            '-vf', 'scale=-1:720', '-c:a', 'aac', '-b:a', '128k',
            output_path
        ]

        process = subprocess.Popen(command, stderr=subprocess.PIPE, text=True)

        last_progress = 0
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

        for line in process.stderr:
            match = time_pattern.search(line)
            if match:
                hours, minutes, seconds = map(float, match.groups())
                current_time = hours * 3600 + minutes * 60 + seconds

                if total_duration > 0:
                    percent = int((current_time / total_duration) * 100)
                    if percent - last_progress >= 5:
                        video.progress = percent
                        video.save(update_fields=['progress'])
                        last_progress = percent

        process.wait()

        if process.returncode == 0:
            os.remove(input_path)
            os.rename(output_path, input_path)

            video.status = 'ready'
            video.progress = 100
            video.save(update_fields=['status', 'progress'])
        else:
            raise Exception(f"FFmpeg завершился с ошибкой, код: {process.returncode}")

    except Exception as e:
        video = Video.objects.get(id=video_id)
        video.status = 'error'
        video.save(update_fields=['status'])
        print(f"Ошибка сжатия видео {video_id}: {e}")


@shared_task
def download_vk_video_task(video_id, vk_link):
    try:
        video = Video.objects.get(id=video_id)
        temp_filename = f"/app/media/temp_web_{uuid.uuid4()}.mp4"

        # Храним прогресс в списке, чтобы иметь к нему доступ из внутренней функции
        last_progress = [0]

        def progress_hook(d):
            if d['status'] == 'downloading':
                # yt-dlp отдает строку типа "  1.2%", иногда с ANSI-цветами. Очищаем ее.
                percent_str = d.get('_percent_str', '0%').replace('%', '')
                percent_clean = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).strip()

                try:
                    percent = int(float(percent_clean))
                    # Обновляем БД с шагом в 5%
                    if percent - last_progress[0] >= 5 or percent == 100:
                        video.progress = percent
                        video.save(update_fields=['progress'])
                        last_progress[0] = percent
                except ValueError:
                    pass

        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'outtmpl': temp_filename,
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],  # <--- ПОДКЛЮЧАЕМ ХУК
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([vk_link])

        with open(temp_filename, 'rb') as f:
            video.video.save(f"web_video_{video_id}.mp4", File(f), save=True)

        os.remove(temp_filename)
        video.status = 'ready'
        video.progress = 100
        video.save(update_fields=['status', 'progress'])

    except Exception as e:
        video.status = 'error'
        video.save(update_fields=['status'])
        print(f"Ошибка скачивания для видео {video_id}: {e}")


@shared_task
def cleanup_temp_files_task():
    age_in_seconds = 24 * 60 * 60
    current_time = time.time()

    deleted_count = 0

    temp_uploads_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
    if os.path.exists(temp_uploads_dir):
        for filename in os.listdir(temp_uploads_dir):
            filepath = os.path.join(temp_uploads_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > age_in_seconds:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"Удален старый чанк: {filename}")
                    except Exception as e:
                        print(f"Ошибка удаления {filename}: {e}")

    if os.path.exists(settings.MEDIA_ROOT):
        for filename in os.listdir(settings.MEDIA_ROOT):
            if filename.startswith('temp_web_') and filename.endswith('.mp4'):
                filepath = os.path.join(settings.MEDIA_ROOT, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > age_in_seconds:
                        try:
                            os.remove(filepath)
                            deleted_count += 1
                            print(f"Удален старый скачанный файл: {filename}")
                        except Exception as e:
                            print(f"Ошибка удаления {filename}: {e}")

    return f"Очистка завершена. Удалено файлов: {deleted_count}"