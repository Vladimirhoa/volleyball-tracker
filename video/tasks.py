import os
import subprocess
import uuid
import yt_dlp
from celery import shared_task
from .models import Video


@shared_task
def process_video_task(video_id):
    try:
        video = Video.objects.get(id=video_id)
        input_path = video.video.path
        output_path = f"{input_path}_compressed.mp4"

        # Команда ffmpeg (сжимаем в 720p)
        command = [
            'ffmpeg', '-y', '-i', input_path,
            '-vcodec', 'libx264', '-crf', '28', '-preset', 'fast',
            '-vf', 'scale=-1:720', '-c:a', 'aac', '-b:a', '128k',
            output_path
        ]

        # Запускаем ffmpeg
        subprocess.run(command, check=True)

        # Если успешно - удаляем оригинал и переименовываем сжатый файл
        os.remove(input_path)
        os.rename(output_path, input_path)

        # Ставим статус "Готово"
        video.status = 'ready'
        video.save()

    except Exception as e:
        video.status = 'error'
        video.save()
        print(f"Ошибка сжатия видео {video_id}: {e}")


@shared_task
def download_vk_video_task(video_id, vk_link):
    try:
        video = Video.objects.get(id=video_id)

        temp_filename = f"/app/media/temp_vk_{uuid.uuid4()}.mp4"

        # Настройки: качаем видео 720p (или ниже) и собираем в mp4
        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'outtmpl': temp_filename,
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([vk_link])
        with open(temp_filename, 'rb') as f:
            video.video.save(f"vk_video_{video_id}.mp4", File(f), save=True)
        os.remove(temp_filename)
        video.status = 'ready'
        video.save()

    except Exception as e:
        video.status = 'error'
        video.save()
        print(f"Ошибка скачивания с ВК для видео {video_id}: {e}")