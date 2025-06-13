document.addEventListener('DOMContentLoaded', function() {
    // Menu Mobile
    const hamburgerMenu = document.getElementById('hamburger-icon'); // Usando ID
    const closeMenuIcon = document.getElementById('close-menu-icon'); // Usando ID
    const mobileNav = document.getElementById('mobile-nav-menu'); // Usando ID
    const mobileNavOverlay = document.querySelector('.mobile-nav-overlay');
    const body = document.body;

    function openMobileMenu() {
        mobileNav.classList.add('active');
        mobileNavOverlay.classList.add('active');
        body.classList.add('no-scroll');
    }

    function closeMobileMenu() {
        mobileNav.classList.remove('active');
        mobileNavOverlay.classList.remove('active');
        body.classList.remove('no-scroll');
    }

    if (hamburgerMenu) {
        hamburgerMenu.addEventListener('click', openMobileMenu);
    }
    if (closeMenuIcon) {
        closeMenuIcon.addEventListener('click', closeMobileMenu);
    }
    if (mobileNavOverlay) {
        mobileNavOverlay.addEventListener('click', closeMobileMenu);
    }

    // Fechar menu mobile ao clicar em um link (dentro do menu lateral), exceto dropdowns
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-main-links a:not(.dropbtn-mobile), .mobile-nav-product-links a:not(.dropbtn-mobile), .mobile-nav-bottom-links a');
    mobileNavLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (mobileNav.classList.contains('active')) {
                // Adicione um pequeno atraso para a navegação começar antes de fechar o menu
                // Isso evita que o clique no link seja bloqueado pelo fechamento imediato.
                setTimeout(closeMobileMenu, 150); 
            }
        });
    });

    // Flash messages auto-hide
    const flashMessagesContainer = document.querySelector('.flash-messages');
    if (flashMessagesContainer) {
        const flashMessages = flashMessagesContainer.querySelectorAll('.alert');
        flashMessages.forEach(msg => {
            setTimeout(() => {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-20px)';
                setTimeout(() => msg.remove(), 500); // Remove after transition
            }, 5000); // Hide after 5 seconds
        });
    }

    // Dropdown menu (desktop)
    const dropdowns = document.querySelectorAll('.main-nav .dropdown');
    dropdowns.forEach(dropdown => {
        const dropbtn = dropdown.querySelector('.dropbtn');
        const dropdownContent = dropdown.querySelector('.dropdown-content');

        if (dropbtn) {
            dropbtn.addEventListener('click', function(event) {
                event.preventDefault(); // Impede a navegação do link principal do dropdown

                // Fecha outros dropdowns abertos, a menos que seja o mesmo
                dropdowns.forEach(otherDropdown => {
                    if (otherDropdown !== dropdown) {
                        otherDropdown.querySelector('.dropdown-content').style.display = 'none';
                        // Reset the arrow if it's a dropdown with an arrow
                        const otherArrow = otherDropdown.querySelector('.arrow-down');
                        if (otherArrow) {
                            otherArrow.style.transform = 'rotate(45deg)'; // Default state
                        }
                    }
                });

                // Alterna a visibilidade do dropdown atual
                const isVisible = dropdownContent.style.display === 'block';
                dropdownContent.style.display = isVisible ? 'none' : 'block';

                // Gira a seta do dropdown desktop
                const arrow = this.querySelector('.arrow-down');
                if (arrow) {
                    arrow.style.transform = isVisible ? 'rotate(45deg)' : 'rotate(225deg)';
                }
            });
        }
    });

    // Fechar dropdowns desktop se clicar fora
    window.addEventListener('click', function(event) {
        if (!event.target.matches('.main-nav .dropbtn, .main-nav .dropbtn *, .main-nav .dropdown-content, .main-nav .dropdown-content *')) {
            dropdowns.forEach(dropdown => {
                let dropdownContent = dropdown.querySelector('.dropdown-content');
                let arrow = dropdown.querySelector('.arrow-down');
                if (dropdownContent && dropdownContent.style.display === 'block') {
                    dropdownContent.style.display = 'none';
                    if (arrow) {
                        arrow.style.transform = 'rotate(45deg)'; // Reset arrow
                    }
                }
            });
        }
    });


    // Dropdown menu (mobile - dentro do mobile-nav)
    const mobileDropdowns = document.querySelectorAll('.mobile-nav .dropdown-mobile');
    mobileDropdowns.forEach(dropdown => {
        const dropbtnMobile = dropdown.querySelector('.dropbtn-mobile');
        const dropdownContentMobile = dropdown.querySelector('.dropdown-content-mobile');
        const arrowIcon = dropbtnMobile ? dropbtnMobile.querySelector('i.fas.fa-chevron-down') : null; // Pega o ícone de seta

        if (dropbtnMobile && dropdownContentMobile) {
            dropbtnMobile.addEventListener('click', function(event) {
                event.preventDefault(); // Evita navegação padrão do link

                // Alterna a visibilidade do conteúdo do dropdown
                const isVisible = dropdownContentMobile.style.display === 'block';
                dropdownContentMobile.style.display = isVisible ? 'none' : 'block';

                // Gira o ícone de seta
                if (arrowIcon) {
                    if (isVisible) {
                        arrowIcon.classList.remove('fa-chevron-up');
                        arrowIcon.classList.add('fa-chevron-down');
                    } else {
                        arrowIcon.classList.remove('fa-chevron-down');
                        arrowIcon.classList.add('fa-chevron-up');
                    }
                }
            });
        }
    });

    // Ocultar dropdowns mobile quando o menu mobile é fechado
    // Isso é importante para resetar o estado quando o usuário reabre o menu
    mobileNav.addEventListener('transitionend', function() {
        if (!mobileNav.classList.contains('active')) {
            mobileDropdowns.forEach(dropdown => {
                const dropdownContentMobile = dropdown.querySelector('.dropdown-content-mobile');
                const arrowIcon = dropdown.querySelector('.dropbtn-mobile i.fas.fa-chevron-down, .dropbtn-mobile i.fas.fa-chevron-up');
                
                if (dropdownContentMobile) {
                    dropdownContentMobile.style.display = 'none'; // Esconde o conteúdo
                }
                if (arrowIcon) {
                    arrowIcon.classList.remove('fa-chevron-up'); // Garante que a seta esteja para baixo
                    arrowIcon.classList.add('fa-chevron-down');
                }
            });
        }
    });
});