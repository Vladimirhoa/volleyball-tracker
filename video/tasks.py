import os
import subprocess
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