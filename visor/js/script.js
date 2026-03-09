document.addEventListener('DOMContentLoaded', function() {
    var params = new URLSearchParams(window.location.search);
    var bookId = params.get('id');

    if (!bookId) { showError(); return; }

    var basePath = 'biblioteca/' + bookId;
    var metadataUrl = basePath + '/metadata.json';

    var bookData = null;
    var flipBook = null;
    var currentPage = 0;
    var totalPages = 0;
    var isTTSActive = false;
    var autoNarrate = false;
    var isMusicPlaying = false;
    var hasShownConfetti = false;
    var ttsQueue = [];
    var currentUtterance = null;

    var pageFlipSound = null;
    var backgroundMusic = null;
    var musicFadeTimer = null;
    var MUSIC_VOL = 0.05;
    var MUSIC_DUCK_VOL = 0.02;

    var voicesLoaded = false;
    var bestVoice = null;

    function loadVoices() {
        var voices = speechSynthesis.getVoices();
        if (!voices.length) return;
        voicesLoaded = true;
        var lang = (bookData && bookData.language === 'en') ? 'en' : 'es';
        var preferred = ['Natural', 'Soft', 'Enhanced', 'Premium', 'Google', 'Microsoft', 'Luciana', 'Paulina', 'Monica'];
        bestVoice = voices.find(function(v) {
            return v.lang.startsWith(lang) && preferred.some(function(n) { return v.name.indexOf(n) !== -1; });
        }) || voices.find(function(v) {
            return v.lang.startsWith(lang) && /female/i.test(v.name);
        }) || voices.find(function(v) {
            return v.lang.startsWith(lang);
        }) || voices[0];
    }

    if (typeof speechSynthesis !== 'undefined' && speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = loadVoices;
    }

    function checkExpiration(data) {
        if (!data.expires_at) return false;
        var expiry = new Date(data.expires_at);
        if (isNaN(expiry.getTime())) return false;
        return new Date() > expiry;
    }

    function showExpired() {
        document.getElementById('loading-screen').classList.add('hidden');
        var errScreen = document.getElementById('error-screen');
        errScreen.style.display = 'flex';
        var lang = (bookData && bookData.language === 'en') ? 'en' : 'es';
        errScreen.querySelector('h2').textContent = lang === 'es' ? 'eBook Expirado' : 'eBook Expired';
        errScreen.querySelector('p').textContent = lang === 'es'
            ? 'Tu acceso de regalo ha expirado. Puedes comprar acceso permanente por $7 USD.'
            : 'Your gift access has expired. You can purchase permanent access for $7 USD.';
    }

    function init() {
        fetch(metadataUrl)
            .then(function(r) { if (!r.ok) throw new Error('404'); return r.json(); })
            .then(function(data) {
                bookData = data;
                if (checkExpiration(data)) { showExpired(); return; }
                loadVoices();
                try { setupBook(); } catch(e) { console.error('[VISOR]', e); showError(); }
            })
            .catch(function(e) { console.error('[VISOR]', e); showError(); });
    }

    function showError() {
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('error-screen').style.display = 'flex';
    }

    function setupBook() {
        if (!bookData.pages || !bookData.pages.length) { showError(); return; }

        document.getElementById('book-title').textContent = bookData.title || 'Mi Cuento';

        if (bookData.download_pdf) {
            var dl = document.getElementById('btn-download');
            dl.style.display = 'flex';
            dl.addEventListener('click', function() {
                var a = document.createElement('a');
                a.href = basePath + '/' + bookData.download_pdf;
                a.download = bookData.download_pdf;
                a.click();
            });
        }

        totalPages = bookData.pages.length;
        var bookEl = document.getElementById('flipbook');

        var bookAR = bookData.aspect_ratio || 1.0;
        var bookFormat = bookAR < 0.85 ? 'portrait' : 'square';
        document.getElementById('flipbook').dataset.format = bookFormat;

        bookData.pages.forEach(function(page, i) {
            var div = document.createElement('div');
            div.className = 'page';
            div.dataset.pageIndex = i;

            var img = new Image();
            img.src = basePath + '/' + page.image;
            img.alt = 'Pagina ' + (i + 1);
            img.draggable = false;
            div.appendChild(img);

            if (page.text && page.text.trim()) {
                var displayText = page.text.replace(/\n/g, ' ').trim();
                var topText, bottomText;
                var sentences = displayText.match(/[^.!?]+[.!?]+\s*/g);
                if (sentences && sentences.length >= 2) {
                    var midSentence = Math.ceil(sentences.length / 2);
                    topText = sentences.slice(0, midSentence).join('').trim();
                    bottomText = sentences.slice(midSentence).join('').trim();
                } else {
                    topText = '';
                    bottomText = displayText;
                }

                if (topText) {
                    var topEl = document.createElement('div');
                    topEl.className = 'page-text-overlay page-text-top';
                    var firstLetter = topText.charAt(0).toUpperCase();
                    var restTop = topText.substring(1);
                    topEl.innerHTML = '<span class="drop-cap">' + firstLetter + '</span>' + restTop;
                    div.appendChild(topEl);
                }

                if (bottomText) {
                    var bottomEl = document.createElement('div');
                    bottomEl.className = 'page-text-overlay page-text-bottom';
                    if (!topText) {
                        var firstLetter = bottomText.charAt(0).toUpperCase();
                        var rest = bottomText.substring(1);
                        bottomEl.innerHTML = '<span class="drop-cap">' + firstLetter + '</span>' + rest;
                    } else {
                        bottomEl.textContent = bottomText;
                    }
                    div.appendChild(bottomEl);
                }
            }

            bookEl.appendChild(div);
        });

        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('visor').style.display = 'flex';

        var lang = (bookData && bookData.language === 'en') ? 'en' : 'es';
        var hintAudio = document.getElementById('hint-audio-text');
        var hintMusic = document.getElementById('hint-music-text');
        if (hintAudio) hintAudio.textContent = lang === 'en' ? 'Audiobook' : 'Audiolibro';
        if (hintMusic) hintMusic.textContent = lang === 'en' ? 'Music' : 'Musica';

        requestAnimationFrame(function() {
            setTimeout(function() {
                try { initFlipBook(bookEl); } catch(e) { console.error('[VISOR] flip init', e); }
            }, 150);
        });
    }

    function detectRealAspectRatio(callback) {
        var interiorPage = bookData.pages.length > 1 ? bookData.pages[1] : bookData.pages[0];
        var probe = new Image();
        probe.onload = function() {
            var realAR = probe.naturalWidth / probe.naturalHeight;
            callback(realAR);
        };
        probe.onerror = function() {
            callback(bookData.aspect_ratio || 0.75);
        };
        probe.src = basePath + '/' + interiorPage.image;
    }

    function initFlipBook(bookEl) {
        detectRealAspectRatio(function(ar) {
            buildFlipBook(bookEl, ar);
        });
    }

    function buildFlipBook(bookEl, ar) {
        var mobile = window.innerWidth <= 768;

        var topSpace = 70;
        var bottomSpace = 70;
        var sideSpace = 60;
        var maxH = window.innerHeight - topSpace - bottomSpace;
        var maxW = window.innerWidth - sideSpace;

        var pageH, pageW;

        if (mobile) {
            pageH = maxH;
            pageW = pageH * ar;
            if (pageW > maxW * 0.98) {
                pageW = maxW * 0.98;
                pageH = pageW / ar;
            }
        } else {
            pageH = maxH;
            pageW = pageH * ar;
            if (pageW * 2 > maxW) {
                pageW = maxW / 2;
                pageH = pageW / ar;
            }
        }

        if (pageW < 180) pageW = 180;
        if (pageH < 180) pageH = 180;

        flipBook = new St.PageFlip(bookEl, {
            width: Math.round(pageW),
            height: Math.round(pageH),
            size: 'fixed',
            showCover: true,
            maxShadowOpacity: 0.4,
            mobileScrollSupport: true,
            useMouseEvents: true,
            swipeDistance: 30,
            clickEventForward: true,
            usePortrait: mobile,
            startPage: 0,
            drawShadow: true,
            flippingTime: 650,
            startZIndex: 0,
            autoSize: false,
            showPageCorners: true
        });

        flipBook.loadFromHTML(bookEl.querySelectorAll('.page'));

        flipBook.on('flip', function(e) {
            currentPage = e.data;
            updateUI();
            playPageFlip();

            if (currentPage >= totalPages - 1 && !hasShownConfetti) {
                hasShownConfetti = true;
                setTimeout(fireConfetti, 500);
            }

            if (autoNarrate) {
                stopTTS();
                setTimeout(function() { startTTS(); }, 750);
            }
        });

        initAudio();
        updateUI();
        setupControls();
    }

    function updateUI() {
        document.getElementById('page-indicator').textContent = (currentPage + 1) + ' / ' + totalPages;
        document.getElementById('btn-prev').disabled = currentPage <= 0;
        document.getElementById('btn-next').disabled = currentPage >= totalPages - 1;
    }

    function setupControls() {
        document.getElementById('btn-prev').addEventListener('click', function() { if (flipBook) flipBook.flipPrev(); });
        document.getElementById('btn-next').addEventListener('click', function() { if (flipBook) flipBook.flipNext(); });
        document.getElementById('btn-fullscreen').addEventListener('click', toggleFS);
        document.getElementById('btn-zoom').addEventListener('click', toggleZoom);
        document.getElementById('btn-music').addEventListener('click', toggleMusic);

        document.getElementById('tts-play-btn').addEventListener('click', function() {
            if (isTTSActive) { stopTTS(); autoNarrate = false; }
            else { startTTS(); autoNarrate = true; }
        });

        var zo = document.getElementById('zoom-overlay');
        zo.addEventListener('click', function(e) { if (e.target === zo || e.target.id === 'zoom-image') zo.classList.remove('active'); });
        document.getElementById('zoom-close').addEventListener('click', function() { zo.classList.remove('active'); });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowRight' && flipBook) flipBook.flipNext();
            if (e.key === 'ArrowLeft' && flipBook) flipBook.flipPrev();
            if (e.key === 'Escape') { zo.classList.remove('active'); if (document.fullscreenElement) document.exitFullscreen(); }
            if (e.key === ' ') { e.preventDefault(); if (isTTSActive) { stopTTS(); autoNarrate = false; } else { startTTS(); autoNarrate = true; } }
        });
    }

    function initAudio() {
        try {
            pageFlipSound = new Audio('sounds/page-flip.mp3');
            pageFlipSound.volume = 0.25;
            pageFlipSound.preload = 'auto';
        } catch(e) {}

        var mf = 'sounds/background-music.mp3';
        if (bookData && bookData.music) mf = 'sounds/' + bookData.music;

        try {
            backgroundMusic = new Audio(mf);
            backgroundMusic.volume = 0;
            backgroundMusic.loop = true;
            backgroundMusic.preload = 'auto';

            backgroundMusic.addEventListener('timeupdate', function() {
                if (!backgroundMusic.duration || !isMusicPlaying) return;
                var remaining = backgroundMusic.duration - backgroundMusic.currentTime;
                var targetVol = isTTSActive ? MUSIC_DUCK_VOL : MUSIC_VOL;
                if (remaining < 2.5) {
                    backgroundMusic.volume = Math.max(0, targetVol * (remaining / 2.5));
                }
            });

            backgroundMusic.addEventListener('ended', function() {
                if (!isMusicPlaying) return;
                backgroundMusic.currentTime = 0;
                backgroundMusic.volume = 0;
                backgroundMusic.play().catch(function(){});
                var targetVol = isTTSActive ? MUSIC_DUCK_VOL : MUSIC_VOL;
                fadeTo(targetVol, 2000);
            });
        } catch(e) {}
    }

    function fadeTo(target, ms) {
        if (musicFadeTimer) clearInterval(musicFadeTimer);
        if (!backgroundMusic) return;
        var start = backgroundMusic.volume;
        var diff = target - start;
        if (Math.abs(diff) < 0.01) { backgroundMusic.volume = Math.max(0, Math.min(1, target)); return; }
        var steps = 40;
        var dt = ms / steps;
        var n = 0;
        musicFadeTimer = setInterval(function() {
            n++;
            var t = n / steps;
            backgroundMusic.volume = Math.max(0, Math.min(1, start + diff * t * t * (3 - 2 * t)));
            if (n >= steps) { clearInterval(musicFadeTimer); musicFadeTimer = null; backgroundMusic.volume = Math.max(0, Math.min(1, target)); }
        }, dt);
    }

    function duckMusic() {
        if (isMusicPlaying && backgroundMusic) {
            fadeTo(MUSIC_DUCK_VOL, 400);
        }
    }

    function unduckMusic() {
        if (isMusicPlaying && backgroundMusic) {
            fadeTo(MUSIC_VOL, 600);
        }
    }

    function playPageFlip() {
        if (!pageFlipSound) return;
        try { pageFlipSound.currentTime = 0; pageFlipSound.play().catch(function(){}); } catch(e) {}
    }

    function toggleMusic() {
        var btn = document.getElementById('btn-music');
        if (isMusicPlaying) {
            fadeTo(0, 600);
            setTimeout(function() { if (backgroundMusic) backgroundMusic.pause(); }, 650);
            isMusicPlaying = false;
            btn.classList.remove('active');
        } else {
            var startVol = isTTSActive ? MUSIC_DUCK_VOL : MUSIC_VOL;
            if (backgroundMusic) { backgroundMusic.volume = 0; backgroundMusic.play().catch(function(){}); fadeTo(startVol, 1500); }
            isMusicPlaying = true;
            btn.classList.add('active');
        }
    }

    function stopAllAudio() {
        stopTTS();
        if (backgroundMusic) { backgroundMusic.pause(); backgroundMusic.currentTime = 0; backgroundMusic.volume = 0; }
        isMusicPlaying = false;
        var mb = document.getElementById('btn-music');
        if (mb) mb.classList.remove('active');
    }

    function toggleFS() {
        var btn = document.getElementById('btn-fullscreen');
        if (document.fullscreenElement) { document.exitFullscreen(); btn.classList.remove('active'); }
        else { document.documentElement.requestFullscreen().catch(function(){}); btn.classList.add('active'); }
    }

    function toggleZoom() {
        var p = bookData.pages[currentPage];
        if (p) { document.getElementById('zoom-image').src = basePath + '/' + p.image; document.getElementById('zoom-overlay').classList.add('active'); }
    }

    function getVisibleTexts() {
        var texts = [];
        if (!bookData || !bookData.pages) return texts;
        var mobile = window.innerWidth <= 768;

        if (mobile || !flipBook) {
            var p = bookData.pages[currentPage];
            if (p && p.text) texts.push(p.text);
        } else {
            if (currentPage === 0) {
                var c = bookData.pages[0];
                if (c && c.text) texts.push(c.text);
            } else {
                var li = currentPage, ri = currentPage + 1;
                if (li < totalPages && bookData.pages[li] && bookData.pages[li].text) texts.push(bookData.pages[li].text);
                if (ri < totalPages && bookData.pages[ri] && bookData.pages[ri].text) texts.push(bookData.pages[ri].text);
            }
        }
        return texts;
    }

    function startTTS() {
        var texts = getVisibleTexts();
        if (!texts.length) return;
        stopTTS();
        isTTSActive = true;
        autoNarrate = true;
        ttsQueue = texts.slice();
        duckMusic();
        speakNext();
        var btn = document.getElementById('tts-play-btn');
        btn.querySelector('.ic-play').style.display = 'none';
        btn.querySelector('.ic-pause').style.display = 'block';
        btn.classList.add('speaking');
    }

    function speakNext() {
        if (!ttsQueue.length) { finishTTS(); return; }
        var text = ttsQueue.shift();
        currentUtterance = new SpeechSynthesisUtterance(text);
        currentUtterance.lang = (bookData.language === 'en') ? 'en-US' : 'es-ES';
        currentUtterance.rate = 0.85;
        currentUtterance.pitch = 1.2;
        currentUtterance.volume = 1;
        if (!voicesLoaded) loadVoices();
        if (bestVoice) currentUtterance.voice = bestVoice;

        currentUtterance.onend = function() {
            if (isTTSActive && ttsQueue.length) setTimeout(speakNext, 350);
            else finishTTS();
        };
        currentUtterance.onerror = function() {
            if (isTTSActive && ttsQueue.length) speakNext();
            else finishTTS();
        };
        speechSynthesis.speak(currentUtterance);
    }

    function finishTTS() {
        isTTSActive = false;
        ttsQueue = [];
        currentUtterance = null;
        unduckMusic();
        var btn = document.getElementById('tts-play-btn');
        btn.querySelector('.ic-play').style.display = 'block';
        btn.querySelector('.ic-pause').style.display = 'none';
        btn.classList.remove('speaking');
    }

    function stopTTS() {
        speechSynthesis.cancel();
        finishTTS();
    }

    function fireConfetti() {
        if (typeof confetti === 'undefined') return;
        var colors = ['#E130D0', '#F472B6', '#A7F3D0', '#6EE7B7', '#F5C542', '#FBBF24'];
        var end = Date.now() + 5000;
        (function frame() {
            confetti({ particleCount: 3, angle: 60, spread: 55, origin: { x: 0, y: 0.6 }, colors: colors });
            confetti({ particleCount: 3, angle: 120, spread: 55, origin: { x: 1, y: 0.6 }, colors: colors });
            if (Date.now() < end) requestAnimationFrame(frame);
        })();
        setTimeout(function() {
            confetti({ particleCount: 200, spread: 130, origin: { y: 0.45 }, colors: colors, startVelocity: 42, gravity: 0.65, scalar: 1.3, ticks: 220 });
        }, 500);
        setTimeout(function() {
            confetti({ particleCount: 70, spread: 80, origin: { x: 0.25, y: 0.35 }, colors: ['#A7F3D0', '#F5C542'], startVelocity: 28, scalar: 1.5, shapes: ['circle'] });
            confetti({ particleCount: 70, spread: 80, origin: { x: 0.75, y: 0.35 }, colors: ['#E130D0', '#F472B6'], startVelocity: 28, scalar: 1.5, shapes: ['circle'] });
        }, 1400);
    }

    init();
});
