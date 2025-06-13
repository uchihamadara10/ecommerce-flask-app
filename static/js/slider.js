document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelectorAll('.banner-slide');
    const dotsContainer = document.querySelector('.slider-dots');
    const prevButton = document.querySelector('.slider-nav.prev');
    const nextButton = document.querySelector('.slider-nav.next');
    let currentSlide = 0;
    let slideInterval;

    if (slides.length === 0) return; // Se não houver banners, sai

    // Cria os pontos de navegação
    slides.forEach((_, index) => {
        const dot = document.createElement('span');
        dot.classList.add('dot');
        dot.setAttribute('data-slide-index', index);
        dotsContainer.appendChild(dot);
        dot.addEventListener('click', () => {
            showSlide(index);
            resetInterval();
        });
    });

    const dots = document.querySelectorAll('.dot');

    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.remove('active');
            if (i === index) {
                slide.classList.add('active');
            }
        });
        dots.forEach((dot, i) => {
            dot.classList.remove('active');
            if (i === index) {
                dot.classList.add('active');
            }
        });
        currentSlide = index;
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }

    function prevSlide() {
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(currentSlide);
    }

    function startInterval() {
        slideInterval = setInterval(nextSlide, 5000); // Troca a cada 5 segundos
    }

    function resetInterval() {
        clearInterval(slideInterval);
        startInterval();
    }

    // Event Listeners para botões
    if (prevButton) {
        prevButton.addEventListener('click', () => {
            prevSlide();
            resetInterval();
        });
    }
    if (nextButton) {
        nextButton.addEventListener('click', () => {
            nextSlide();
            resetInterval();
        });
    }

    // Inicia o slider
    showSlide(0);
    startInterval();
});