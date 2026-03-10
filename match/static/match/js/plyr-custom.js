document.addEventListener('DOMContentLoaded', () => {
    const players = Plyr.setup('.js-player', {
        controls: [
            'play-large', 'play', 'progress', 'current-time',
            'duration', 'mute', 'volume', 'settings', 'pip', 'fullscreen'
        ],
        settings: ['speed'],
        speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
        i18n: { speed: 'Скорость', normal: 'Обычная' },
        seekTime: 10,
        doubleClick: { togglesFullscreen: false } // Отключаем стандартный фулскрин
    });

    players.forEach(player => {
        const container = player.elements.container;
        let lastTapTime = 0;

        container.addEventListener('click', (e) => {
            // Игнорируем клики по панели управления
            if (e.target.closest('.plyr__controls')) return;

            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTapTime;

            if (tapLength < 300 && tapLength > 0) {
                const rect = container.getBoundingClientRect();
                const clickX = e.clientX - rect.left;

                if (clickX < rect.width / 2) {
                    player.rewind(10);
                    showRipple(container, ' 10 сек', 'left');
                } else {
                    player.forward(10);
                    showRipple(container, '10 сек ', 'right');
                }

                if (!player.playing) player.play();
                lastTapTime = 0;
            } else {
                lastTapTime = currentTime;
            }
        });
    });

    function showRipple(container, text, side) {
        const existing = container.querySelector('.youtube-ripple');
        if (existing) existing.remove();

        const ripple = document.createElement('div');
        ripple.className = `youtube-ripple ${side}`;
        ripple.innerText = text;
        container.appendChild(ripple);

        setTimeout(() => ripple.remove(), 500);
    }
});