/* ===========================
   RUBIK PROPERTIES – EFFECTS
   =========================== */

// 1. Parallax Move (Background Depth)
const hero = document.querySelector('.hero-parallax');
if (hero) {
    window.addEventListener('mousemove', (e) => {
        let x = e.clientX / window.innerWidth;
        let y = e.clientY / window.innerHeight;
        // Moves the background slightly in the opposite direction
        hero.style.backgroundPosition = `${50 + x * 5}% ${50 + y * 5}%`;
    });
}

// 2. Reveal on Scroll
function reveal() {
    var reveals = document.querySelectorAll(".reveal, .reveal-left, .reveal-right");
    for (var i = 0; i < reveals.length; i++) {
        var windowHeight = window.innerHeight;
        var elementTop = reveals[i].getBoundingClientRect().top;
        var elementVisible = 150;
        if (elementTop < windowHeight - elementVisible) {
            reveals[i].classList.add("active");
        }
    }
}
window.addEventListener("scroll", reveal);
// Trigger once on load
window.addEventListener("load", reveal);

// 3. Magnetic Button Effect
const magneticBtns = document.querySelectorAll(".magnetic-btn");

magneticBtns.forEach(btn => {
    btn.addEventListener("mousemove", function (e) {
        const position = btn.getBoundingClientRect();
        const x = e.clientX - position.left - position.width / 2;
        const y = e.clientY - position.top - position.height / 2;

        btn.style.transform = `translate(${x * 0.3}px, ${y * 0.5}px) scale(1.05)`;
    });

    btn.addEventListener("mouseout", function () {
        btn.style.transform = "translate(0px, 0px) scale(1)";
    });
});

// 4. Interactive Carousel Logic
function moveSlide(btn, direction) {
    const container = btn.closest('.carousel-container');
    const slider = container.querySelector('.slider');
    const slideWidth = slider.querySelector('.slide').offsetWidth;
    slider.scrollBy({ left: direction * slideWidth, behavior: 'smooth' });
}

function goToSlide(dot, index) {
    const container = dot.closest('.carousel-container');
    const slider = container.querySelector('.slider');
    const slideWidth = slider.querySelector('.slide').offsetWidth;
    slider.scrollTo({ left: index * slideWidth, behavior: 'smooth' });
}

// Update dots and counter on scroll
document.addEventListener('scroll', function (e) {
    if (e.target.classList && e.target.classList.contains('slider')) {
        const slider = e.target;
        const container = slider.closest('.carousel-container');
        const dots = container.querySelectorAll('.dot');
        const counter = container.querySelector('.carousel-counter');
        const slideWidth = slider.querySelector('.slide').offsetWidth;
        const activeIndex = Math.round(slider.scrollLeft / slideWidth);

        // Update Counter
        if (counter) {
            counter.innerText = `${activeIndex + 1}/${dots.length}`;
        }

        // Update Dots
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === activeIndex);
        });
    }
}, true);

// 5. Carousel Auto-play
function initAutoplay() {
    const carousels = document.querySelectorAll('.carousel-container');
    carousels.forEach(container => {
        const slider = container.querySelector('.slider');
        const slides = slider.querySelectorAll('.slide');
        if (slides.length <= 1) return;

        let interval = setInterval(() => {
            const slideWidth = slides[0].offsetWidth;
            if (slider.scrollLeft + slideWidth >= slider.scrollWidth - 10) {
                slider.scrollTo({ left: 0, behavior: 'smooth' });
            } else {
                slider.scrollBy({ left: slideWidth, behavior: 'smooth' });
            }
        }, 5000); // Change every 5 seconds

        // Pause on hover
        container.addEventListener('mouseenter', () => clearInterval(interval));
        container.addEventListener('mouseleave', () => {
            interval = setInterval(() => {
                const slideWidth = slides[0].offsetWidth;
                if (slider.scrollLeft + slideWidth >= slider.scrollWidth - 10) {
                    slider.scrollTo({ left: 0, behavior: 'smooth' });
                } else {
                    slider.scrollBy({ left: slideWidth, behavior: 'smooth' });
                }
            }, 5000);
        });
    });
}
window.addEventListener('load', initAutoplay);

// Mobile Menu Toggle
window.addEventListener('DOMContentLoaded', () => {
    const menu = document.querySelector('#mobile-menu');
    const menuLinks = document.querySelector('#nav-menu');

    if (menu && menuLinks) {
        menu.addEventListener('click', function () {
            menu.classList.toggle('is-active');
            menuLinks.classList.toggle('active');
        });
    }
});
// 6. Secret Admin Access (Desktop Shortcut + Mobile Long Press)
window.addEventListener('DOMContentLoaded', () => {
    const adminBtn = document.getElementById('admin-btn');
    const triggerArea = document.getElementById('admin-trigger');
    let pressTimer;

    if (!adminBtn || !triggerArea) return;

    // --- Persistence: Check if Admin Mode was previously enabled ---
    if (localStorage.getItem('isAdminMode') === 'true') {
        adminBtn.style.display = 'inline-block';
    }

    // --- DESKTOP: SECRET KEY ('A' + 'D' together) ---
    let keysPressed = {};
    document.addEventListener('keydown', (e) => {
        keysPressed[e.key.toLowerCase()] = true;
        if (keysPressed['a'] && keysPressed['d']) {
            const isHidden = adminBtn.style.display === 'none';
            adminBtn.style.display = isHidden ? 'inline-block' : 'none';
            localStorage.setItem('isAdminMode', isHidden ? 'true' : 'false');
            console.log("Admin Mode Toggled via Keyboard");
        }
    });

    document.addEventListener('keyup', (e) => {
        delete keysPressed[e.key.toLowerCase()];
    });

    // --- MOBILE: LONG PRESS ON LOGO TRIGGER AREA (3 SECONDS) ---
    triggerArea.addEventListener('touchstart', (e) => {
        pressTimer = window.setTimeout(() => {
            const isHidden = adminBtn.style.display === 'none' || adminBtn.style.display === '';
            adminBtn.style.display = isHidden ? 'inline-block' : 'none';
            localStorage.setItem('isAdminMode', isHidden ? 'true' : 'false');
            // Alert removed to prevent popups: alert(isHidden ? "Admin Access Unlocked" : "Admin Access Locked");
        }, 3000); // 3 seconds hold
    }, { passive: true });

    triggerArea.addEventListener('touchend', () => {
        clearTimeout(pressTimer);
    });

    triggerArea.addEventListener('touchcancel', () => {
        clearTimeout(pressTimer);
    });
});
