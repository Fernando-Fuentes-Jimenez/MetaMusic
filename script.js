// script.js

// Registra los plugins de GSAP
gsap.registerPlugin(ScrollTrigger);

document.addEventListener('DOMContentLoaded', () => {

    // --- Efecto de "Desbloqueo" de la Página de Inicio ---
    const mainPage = document.querySelector('.main-page');
    const unlockButton = document.querySelector('.unlock-button');
    const websiteContent = document.getElementById('website-content');
    const navbar = document.querySelector('.navbar');

    // Asegura que los data-text estén configurados para el efecto glitch
    document.querySelector('.glitch').setAttribute('data-text', document.querySelector('.glitch').textContent);
    document.querySelector('.sub-glitch').setAttribute('data-text', document.querySelector('.sub-glitch').textContent);

    // Inicialmente, el contenido principal está oculto y el scroll deshabilitado
    gsap.set(websiteContent, { opacity: 0, y: 20 });
    document.body.style.overflowY = 'hidden';
    gsap.set(navbar, { y: "-100%" }); // Oculta la navbar al inicio

    unlockButton.addEventListener('click', () => {
        // Timeline para una secuencia de animaciones fluida al desbloquear
        let unlockTimeline = gsap.timeline({
            onComplete: () => {
                mainPage.classList.add('unlocked');
                mainPage.style.display = 'none';
                document.body.style.overflowY = 'auto'; // Habilita el scroll
                navbar.classList.add('visible'); // Muestra la navbar
            }
        });

        unlockTimeline
            .to(mainPage.querySelector('.main-logo'), { scale: 0.8, opacity: 0, duration: 0.5, ease: "back.in(1.7)" })
            .to(mainPage.querySelector('h1'), { y: -50, opacity: 0, duration: 0.5, ease: "power2.in" }, "<0.1")
            .to(mainPage.querySelector('h2'), { y: -30, opacity: 0, duration: 0.4, ease: "power2.in" }, "<0.1")
            .to(mainPage.querySelector('p'), { y: -20, opacity: 0, duration: 0.3, ease: "power2.in" }, "<0.1")
            .to(unlockButton, { scale: 0, opacity: 0, duration: 0.5, ease: "back.in(1.7)" }, "<0.1")
            .to(mainPage, {
                opacity: 0,
                duration: 0.8,
                ease: "power2.inOut",
                onComplete: () => {
                    // Muestra y anima el contenido principal
                    gsap.to(websiteContent, {
                        opacity: 1,
                        y: 0,
                        duration: 1.5,
                        ease: "power3.out"
                    });
                    gsap.to(navbar, {
                        y: "0%", // Anima la navbar para que aparezca
                        duration: 0.8,
                        ease: "power3.out"
                    });
                    websiteContent.classList.add('visible');
                }
            }, ">"); // ">" asegura que la animación de la página principal ocurre después de los elementos
    });


    // --- Animaciones de Scroll con GSAP y ScrollTrigger ---

    // 1. Hero Section Parallax
    gsap.to(".parallax-layer.layer-1", {
        yPercent: 30, // Se mueve más lento
        ease: "none",
        scrollTrigger: {
            trigger: ".hero",
            start: "top top",
            end: "bottom top",
            scrub: true,
            invalidateOnRefresh: true // Importante para responsive
        }
    });

    gsap.to(".parallax-layer.layer-2", {
        yPercent: 50, // Se mueve más rápido
        ease: "none",
        scrollTrigger: {
            trigger: ".hero",
            start: "top top",
            end: "bottom top",
            scrub: true,
            invalidateOnRefresh: true
        }
    });

    // 2. Animaciones de entrada para todas las secciones de contenido
    gsap.utils.toArray('.section-content').forEach(section => {
        // Excluir el hero de esta animación ya que tiene su propia lógica de aparición
        if (!section.classList.contains('hero')) {
            gsap.fromTo(section,
                { opacity: 0, y: 50 },
                {
                    opacity: 1,
                    y: 0,
                    duration: 1.2,
                    ease: "power2.out",
                    scrollTrigger: {
                        trigger: section,
                        start: "top 80%", // Empieza la animación cuando el top de la sección está al 80% del viewport
                        end: "bottom top", // Termina cuando la sección sale por abajo
                        toggleActions: "play none none reverse", // Play al entrar, reverse al salir
                        // markers: true // Descomentar para depuración
                    }
                }
            );
        }
    });

    // 3. Animaciones de split-layout (contenido de izquierda y derecha)
    gsap.utils.toArray('.split-layout').forEach(layout => {
        const contentLeft = layout.querySelector('.content-left');
        const contentRight = layout.querySelector('.content-right');
        const imagePlaceholder = layout.querySelector('.image-placeholder');

        // Animación para el contenido de la izquierda
        if (contentLeft) {
            gsap.fromTo(contentLeft,
                { opacity: 0, x: -100 },
                {
                    opacity: 1,
                    x: 0,
                    duration: 1.5,
                    ease: "power3.out",
                    scrollTrigger: {
                        trigger: layout,
                        start: "top 75%",
                        toggleActions: "play none none reverse",
                    }
                }
            );
        }

        // Animación para el contenido de la derecha
        if (contentRight) {
            gsap.fromTo(contentRight,
                { opacity: 0, x: 100 },
                {
                    opacity: 1,
                    x: 0,
                    duration: 1.5,
                    ease: "power3.out",
                    scrollTrigger: {
                        trigger: layout,
                        start: "top 75%",
                        toggleActions: "play none none reverse",
                    }
                }
            );
        }

        // Animación de rotación 3D para los mockups al hacer scroll
        if (imagePlaceholder) {
            gsap.to(imagePlaceholder, {
                rotationY: 15,
                rotationX: 5,
                scale: 1.05,
                ease: "power1.inOut",
                scrollTrigger: {
                    trigger: layout,
                    start: "top bottom",
                    end: "bottom top",
                    scrub: true
                }
            });
        }
    });

    // 4. Smooth scroll para los enlaces de la navbar
    document.querySelectorAll('.nav-links a').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            gsap.to(window, { duration: 1, scrollTo: targetId, ease: "power2.inOut" });
        });
    });

    // --- NUEVA FUNCIONALIDAD: Copiar email al portapapeles si el mailto falla ---
    const emailToCopy = 'm.metamusic@gmail.com'; // Define el email aquí para fácil edición

    document.querySelectorAll('.cta-buttons .button').forEach(button => {
        button.addEventListener('click', function(e) {
            // Intenta abrir el cliente de correo primero (comportamiento estándar del mailto)
            // No hacemos e.preventDefault() aquí para permitir que el mailto se dispare.

            // Luego, como fallback o acción secundaria, copiamos al portapapeles
            navigator.clipboard.writeText(emailToCopy).then(() => {
                // Pequeño feedback visual de que se ha copiado
                const originalText = this.textContent;
                this.textContent = '¡Email copiado!';
                gsap.to(this, {
                    backgroundColor: '#00B894', // Cambia a verde
                    duration: 0.3,
                    yoyo: true,
                    repeat: 1, // Dos veces (ida y vuelta)
                    onComplete: () => {
                        this.textContent = originalText; // Vuelve al texto original
                        // Restaura el color si es el botón secundario
                        if (this.classList.contains('secondary')) {
                            this.style.backgroundColor = 'transparent';
                        }
                    }
                });
            }).catch(err => {
                console.error('Error al copiar el email al portapapeles:', err);
                // Aquí podrías mostrar un alert o un mensaje de error si no se pudo copiar
                alert('No se pudo copiar el email automáticamente. Por favor, cópialo manualmente: ' + emailToCopy);
            });

            // Si es el segundo botón y tiene target="_blank", déjalo, aunque en mailto no tiene efecto.
            // Si quieres que no intente abrir el cliente de correo, harías e.preventDefault() aquí
            // y solo usarías la copia al portapapeles. Pero es mejor intentar primero el mailto.
        });
    });

});

// El efecto Ripple para todos los botones ya está manejado en CSS.
