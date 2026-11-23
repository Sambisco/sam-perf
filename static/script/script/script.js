$(document).on("click", "li:has(ul)", function (e) {
    $("ul", this).toggle("slow");
    $(".arrow", this).toggleClass("fa-chevron-up")
})
$(document).on("click", ".desktop", function (e) {
    let sidebar = $(".sidebar");
    console.log(sidebar);
    $(sidebar).toggleClass("close");

})
$(document).on("click", ".mobile", function (e) {
    let sidebar = $(".sidebar");
    console.log(sidebar);
    $(sidebar).toggleClass("showMobile");
})
$(document).on("click", "#header-button-search", function (e) {
    $(".search-box").toggle("slow");
    $(".user-box").hide()
    $(".notification-box").hide();
})
$(document).on('click', '#cart', function (e) {
    $(".tour-panier").show('slow');
})
$(document).on('click', '.btn-close-panier', function (e) {
    $(".tour-panier").hide('slow');
})
$(document).on("click", ".profile", function () {
    $("#deconnect").fadeIn();
    $(".search-box").hide();
})
$(document).on("click", ".show-notification", function () {
    $(".notification-box").toggle("slow");
    $(".search-box").hide();
})
$(document).on("click", "#btn-deconnect", function () {
    window.location = "../controller/deconnect";
})
const productContainers = [...document.querySelectorAll('.top_slider')];
const nxtBtn = [...document.querySelectorAll('.nxt-btn_slider')];
const preBtn = [...document.querySelectorAll('.pre-btn_slider')];

productContainers.forEach((item, i) => {
    let containerDimensions = item.getBoundingClientRect();
    let containerWidth = containerDimensions.width;

    nxtBtn[i].addEventListener('click', () => {
        item.scrollLeft += containerWidth;
    })

    preBtn[i].addEventListener('click', () => {
        item.scrollLeft -= containerWidth;
    })
})
jQuery(function ($) {

    $("#btn-modal-ajouter-i").click(function () {
        $(".grand").fadeIn();
    });
    $("#btn-modal-ajouter").click(function () {
        $(".moyen").fadeIn();
    });
    $(".close-modal").click(function () {
        $(".grand").fadeOut();
        $(".moyen").fadeOut();
        $(".petit").fadeOut();
    });
    // バブリングを停止
    $(".overlay-inner").click(function (event) {
        event.stopPropagation();
    });
});


$(document).on("click", ".close-alert-info", function () {
    $('.alert-info').hide();
})


$(window).on('scroll', function () {
    let top = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    if (top > 100) {
        $('.scroll-to-top').fadeIn();
    } else {
        $('.scroll-to-top').fadeOut();
    }
});

$(document).on("click", ".scroll-to-top", function () {
    $('html, body').animate({ scrollTop: 0 }, 360);
    return false;

})
$(document).on("click", ".active_nav_click", function (e) {
    e.preventDefault()
    $(".active_nav_click").removeClass("active_nav");
    $(this).addClass("active_nav");
})
$(function () {
    $(".bouton-add-div").draggable();
    $(".bouton-add-div1").draggable();
    $(".content-calendrier").draggable();
});
$(function () {

});
function updateTitle(section, pageName, target) {
    $(target).removeClass('active-title-page'); // reset
    if (section === "page") {
        if (pageName.toLowerCase() === "section-contrat-1") {
            $(target).html("Recruitement").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-dmt-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-depart-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-attestation-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-certificat-1") {
            $(target).html("Départ").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-domiciliation-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-affectation-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-indemnite-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-conge-annuel-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-conge-maternite-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-cotisation-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-salaire-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-renumeration-conge-annuel-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-renumeration-conge-maternite-1") {
            $(target).html("Employés").addClass('active-title-page');
        }
        // section deux
        if (pageName.toLowerCase() === "section-contrat-2") {
            $(target).html("Contrat").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-dmt-2") {
            $(target).html("DMT").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-depart-2") {
            $(target).html("Départ").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-attestation-2") {
            $(target).html("Attestation de travail").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-certificat-2") {
            $(target).html("certificat de travail").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-domiciliation-2") {
            $(target).html("Domiciliation de salaire").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-affectation-2") {
            $(target).html("Affectation").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-indemnite-2") {
            $(target).html("Demande indemnite").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-conge-annuel-2") {
            $(target).html("Conge annuel").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-conge-maternite-2") {
            $(target).html("Conge maternite").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-cotisation-2") {
            $(target).html("Cotisation").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-salaire-2") {
            $(target).html("Salaire").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-renumeration-conge-annuel-2") {
            $(target).html("Renumeration conge annuel").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-renumeration-conge-maternite-2") {
            $(target).html("Renumeration conge maternite").addClass('active-title-page');
        }

    } else if (section === "gstock") {
        if (pageName.toLowerCase() === "section-entree-1") {
            $(target).html("Matiére");
        } else if (pageName.toLowerCase() === "section-sortie-1") {
            $(target).html("Matiére").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-sortie-ex-1") {
            $(target).html("Matiére").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-affectation-gs-1") {
            $(target).html("Matiére").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-mutation-1") {
                $(target).html("Affectation").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-dotation-1") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-reception-1") {
            $(target).html("Fournisseur").addClass('active-title-page');
        }
        // section deux
        if (pageName.toLowerCase() === "section-entree-2") {
            $(target).html("Entrée");
        } else if (pageName.toLowerCase() === "section-sortie-2") {
            $(target).html("Sortie interne").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-sortie-ex-2") {
            $(target).html("Sortie externe").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-affectation-gs-2") {
            $(target).html("Affectation").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-mutation-2") {
            $(target).html("Mutation").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-dotation-2") {
            $(target).html("Dotation").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-reception-2") {
            $(target).html("Reception").addClass('active-title-page');
        }
        // section trois
        if (pageName.toLowerCase() === "section-entree-3") {
            $(target).html("Fournisseur");
        } else if (pageName.toLowerCase() === "section-sortie-3") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-affectation-gs-3") {
            $(target).html("Employés").addClass('active-title-page');
        } else if (pageName.toLowerCase() === "section-mutation-3") {
            $(target).html("Employés").addClass('active-title-page');
        }
    }
}

// Clic sur Employé
$(document).on('click', '#employe', function (e) {
    e.preventDefault();
    // RESSOURCES HUMAINES
    updateTitle("page", "section-contrat-1", '.page-title-1');
    updateTitle("page", "section-dmt-1", '.page-title-2');
    updateTitle("page", "section-depart-1", '.page-title-3');
    updateTitle("page", "section-attestation-1", '.page-title-4');
    updateTitle("page", "section-certificat-1", '.page-title-5');
    updateTitle("page", "section-domiciliation-1", '.page-title-6');
    updateTitle("page", "section-affectation-1", '.page-title-7');
    updateTitle("page", "section-indemnite-1", '.page-title-8');
    updateTitle("page", "section-conge-annuel-1", '.page-title-9');
    updateTitle("page", "section-conge-maternite-1", '.page-title-10');
    updateTitle("page", "section-cotisation-1", '.page-title-11');
    updateTitle("page", "section-salaire-1", '.page-title-12');
    updateTitle("page", "section-renumeration-conge-annuel-1", '.page-title-13');
    updateTitle("page", "section-renumeration-conge-maternite-1", '.page-title-14');


    // GESTION DES MATIERES

    updateTitle("gstock", "section-entree-1", '.gstock-title-1');
    updateTitle("gstock", "section-sortie-1", '.gstock-title-2');
    updateTitle("gstock", "section-sortie-ex-1", '.gstock-title-ex-2');
    updateTitle("gstock", "section-affectation-gs-1", '.gstock-title-3');
    updateTitle("gstock", "section-mutation-1", '.gstock-title-mu-1');
    updateTitle("gstock", "section-dotation-1", '.gstock-title-4');
    updateTitle("gstock", "section-reception-1", '.gstock-title-5');

});

// Clic sur Service
$(document).on('click', '#service', function (e) {
    e.preventDefault();
    // RESSOURCES HUMAINES

    updateTitle("page", "section-contrat-2", '.page-title-1');
    updateTitle("page", "section-dmt-2", '.page-title-2');
    updateTitle("page", "section-depart-2", '.page-title-3');
    updateTitle("page", "section-attestation-2", '.page-title-4');
    updateTitle("page", "section-certificat-2", '.page-title-5');
    updateTitle("page", "section-domiciliation-2", '.page-title-6');
    updateTitle("page", "section-affectation-2", '.page-title-7');
    updateTitle("page", "section-indemnite-2", '.page-title-8');
    updateTitle("page", "section-conge-annuel-2", '.page-title-9');
    updateTitle("page", "section-conge-maternite-2", '.page-title-10');
    updateTitle("page", "section-cotisation-2", '.page-title-11');
    updateTitle("page", "section-salaire-2", '.page-title-12');
    updateTitle("page", "section-renumeration-conge-annuel-2", '.page-title-13');
    updateTitle("page", "section-renumeration-conge-maternite-2", '.page-title-14');

// GESTION DES MATIERES
    updateTitle("gstock", "section-entree-2", '.gstock-title-1');
    updateTitle("gstock", "section-sortie-2", '.gstock-title-2');
    updateTitle("gstock", "section-sortie-ex-2", '.gstock-title-ex-2');
    updateTitle("gstock", "section-affectation-gs-2", '.gstock-title-3');
    updateTitle("gstock", "section-mutation-2", '.gstock-title-mu-1');
    updateTitle("gstock", "section-dotation-2", '.gstock-title-4');
    updateTitle("gstock", "section-reception-2", '.gstock-title-5');


});
$(document).on('click', '#pverbal', function (e) {
    e.preventDefault();
    updateTitle("gstock", "section-entree-3", '.gstock-title-1');
    updateTitle("gstock", "section-sortie-3", '.gstock-title-2');
    updateTitle("gstock", "section-affectation-gs-3", '.gstock-title-3');
    updateTitle("gstock", "section-mutation-3", '.gstock-title-mu-1');

})

$(document).on('click', '#employe', function (e) {
    $('.main-sous-content2').addClass("active-main-sous-content");
    $('.main-sous-content1').removeClass("active-main-sous-content");
    $('.main-sous-content3').removeClass("active-main-sous-content");
})
$(document).on('click', '#service', function (e) {
    $('.main-sous-content1').addClass("active-main-sous-content");
    $('.main-sous-content2').removeClass("active-main-sous-content");
    $('.main-sous-content3').removeClass("active-main-sous-content");
})
$(document).on('click', '#pverbal', function (e) {
    $('.main-sous-content3').addClass("active-main-sous-content");
    $('.main-sous-content1').removeClass("active-main-sous-content");
    $('.main-sous-content2').removeClass("active-main-sous-content");
})
$(document).on('click', '.open-download1', function (e) {
    $('.download1').toggle("slow");
})
$(document).on('click', '.open-download2', function (e) {
    $('.download2').toggle("slow");
})
$(document).on('click', '.open-download3', function (e) {
    $('.download3').toggle("slow");
})
$(document).on('click', '.open-download4', function (e) {
    $('.download4').toggle("slow");
})
$(document).on('click', '.open-download5', function (e) {
    $('.download5').toggle("slow");
})
$(document).on('click', '.open-download6', function (e) {
    $('.download6').toggle("slow");
})


$('#tableau1').on('click', function (e) {
    $("#tableau1-modal").fadeIn();
});
$('#tableau2').on('click', function (e) {
    $("#tableau2-modal").fadeIn();
});
$('#tableau3').on('click', function (e) {
    $("#tableau3-modal").fadeIn();
});
$('#tableau4').on('click', function (e) {
    $("#tableau4-modal").fadeIn();
});
$('#tableau5').on('click', function (e) {
    $("#tableau5-modal").fadeIn();
});
$('#tableau6').on('click', function (e) {
    $("#tableau6-modal").fadeIn();
});
$('#tableau7').on('click', function (e) {
    $("#tableau7-modal").fadeIn();
});
$(document).on('click', '.calendar', function (e) {
    $('.calendrier').toggleClass("showcalendar")
})
$('#Exportindemnite').click(function () {
    let table = $("#example1").clone();
    console.log(table);
    table.find(".no-export").each(function () {
        $(this).remove();
    });
    TableToExcel.convert(table[0], {
        name: `Demande-Indemnite.xlsx`,
        sheet: {
            name: 'Indemnite'
        }
    });
});

const iconsswitcher = document.querySelector(".icons-switcher");
const colorswitchers = document.querySelector(".color-box");

iconsswitcher?.addEventListener("click", () => {
    colorswitchers.classList.toggle("open-switch");
});

const themes = ["principal", "green", "purple", "red"];
const btnswitchers = document.querySelectorAll(".btn-switcher");

btnswitchers.forEach(btn => {
    btn.addEventListener("click", (e) => {
        const target = e.currentTarget;
        const datacolor = target.getAttribute("data-color");
        const theme = getThemeFromColor(datacolor);

        if (!theme) return;

        // Appliquer le thème
        document.documentElement.className = theme;
        localStorage.setItem("mode", theme);

        // Fermer le switcher
        document.querySelector(".open-switch")?.classList.remove("open-switch");

        // Mettre à jour l'état actif
        document.querySelector(".active-color")?.classList.remove("active-color");
        target.classList.add("active-color");

        // Appeler la fonction (si elle existe)
        if (typeof get_years === "function") {
            get_years();
        }
    });
});

function getThemeFromColor(color) {
    switch (color) {
        case "#005f9e": return "principal";
        case "#04640e": return "green";
        case "#8e44ad": return "purple";
        case "#93080d": return "red";
        default: return null;
    }
}

// Au chargement : appliquer le thème sauvegardé
const savedMode = localStorage.getItem("mode");
if (themes.includes(savedMode)) {
    document.documentElement.className = savedMode;
    btnswitchers.forEach(btn => {
        btn.classList.remove("active-color");
        if (btn.getAttribute("data-color") === getColorFromTheme(savedMode)) {
            btn.classList.add("active-color");
        }
    });
}

function getColorFromTheme(theme) {
    switch (theme) {
        case "principal": return "#005f9e";
        case "green": return "#04640e";
        case "purple": return "#8e44ad";
        case "red": return "#93080d";
        default: return null;
    }
}

  function decodeUTF8(str) {
    try {
        return decodeURIComponent(escape(str));
    } catch (e) {
        return str;
    }
}

$(".tab_btn").on("click", function () {
    var index = $(this).index();

    $(".tab_btn").removeClass("active_tab");
    $(this).addClass("active_tab");

    $(".content_tab").removeClass("active_tab").hide();
    $(".content_tab").eq(index).addClass("active_tab").show();

    // ✅ Redessiner les DataTables visibles
});

// MENU-DASHBOARD
$(document).ready(function () {
    // Click sur icône menu
    $('.card-menu').click(function (e) {
        e.stopPropagation();
        const $submenu = $(this).children('.submenu');
        $('.submenu').not($submenu).slideUp(200); // ferme les autres
        $submenu.slideToggle(200);
    });

    // Clique ailleurs ferme tout
    $(document).click(function () {
        $('.submenu').slideUp(200);
    });
    
    const favicon = document.getElementById("favicon");
    const href = favicon.href.split("?")[0];
    favicon.href = href + "?v=" + new Date().getTime();

});
$(document).ready(function () {
    var swiper = new Swiper(".mySwiper", {
        effect: "coverflow",
        grabCursor: true,
        centeredSlides: true,
        slidesPerView: "auto",
        loop: true,
        spaceBetween: 30,
        coverflowEffect: {
            rotate: 0,
            stretch: 0,
            depth: 200,
            modifier: 2.5,
            slideShadows: true,
        },
        navigation: { nextEl: ".swiper-button-next", prevEl: ".swiper-button-prev" },
    });

});
$(function () { // équivalent de $(document).ready(...)
    // délégué sur .bar-container-menu pour être sûr même si les <li> sont ajoutés dynamiquement
    $('.bar-container-menu').on('click', 'li', function (e) {
        e.preventDefault(); // empêche href="#" de remonter en haut de page
        console.log('li cliqué:', this, 'index --i:', $(this).attr('style'));

        // retire la classe bar-container-active sur tous les li du même bar-container-menu
        $(this).closest('.bar-container-menu').find('li').removeClass('bar-container-active');

        // ajoute la classe bar-container-active au li cliqué
        $(this).addClass('bar-container-active');
        
    });

    // debug: vérifie qu'on a bien des éléments
    console.log('jQuery OK, nb bar-container-menus:', $('.bar-container-menu').length, 'nb li dans premier bar-container-menu:', $('.bar-container-menu').first().find('li').length);
});