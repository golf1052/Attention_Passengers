function orientScreen() {
    if (screen.orientation.type.startsWith('landscape')) {
        document.getElementById('img').src = 'image.png';
    } else {
        document.getElementById('img').src = 'phone-image.png';
    }
}

screen.orientation.addEventListener('change', function(e) {
    orientScreen();
});

document.getElementById('playPauseButton').addEventListener('click', function() {
    const audio = document.getElementById('audio');
    if (audio.paused) {
        audio.play();
        document.getElementById('playPauseImg').src = 'pause-fill.svg';
    } else {
        audio.pause();
        document.getElementById('playPauseImg').src = 'play-fill.svg';
    }
});

document.getElementById('audio').addEventListener('ended', function() {
    document.getElementById('playPauseImg').src = 'play-fill.svg';
});

orientScreen();
