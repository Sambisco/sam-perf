const sections = [
	{ container: '.content-list1', pagination: '#pagination1', counter: '#showingInfo1' },
	{ container: '.content-list2', pagination: '#pagination2', counter: '#showingInfo2' },
	{ container: '.content-list3', pagination: '#pagination3', counter: '#showingInfo3' }
];

const pageSize = 20;
let activeSectionIndex = 0;

// --- Initialisation et rendu ---
function updateSectionItems(index) {
	const s = sections[index];
	s.items = $(s.container).children('.result').toArray();
	s.filtered = [...s.items];
	s.currentPage = 1;
	renderSection(s);
}

function renderSection(s) {
	const total = s.filtered.length;
	const totalPages = Math.ceil(total / pageSize);
	const start = (s.currentPage - 1) * pageSize;
	const end = Math.min(start + pageSize, total);

	// Affichage des éléments
	$(s.container).empty();
	for (let i = start; i < end; i++) $(s.container).append(s.filtered[i]);

	// Compteur
	if (total === 0) {
		$(s.counter).text(`Affichage de l'élément 0 à 0 sur 0 éléments`);
	} else {
		$(s.counter).text(`Affichage de l'élément ${start + 1} à ${end} sur ${total} éléments`);
	}

	// Pagination
	const pag = $(s.pagination);
	pag.empty();
	// 🚫 Si aucun élément → ne pas créer de boutons
	if (total === 0) return;

	const btnFirst = $('<button>&lt;&lt;</button>').prop('disabled', s.currentPage === 1).click(() => { s.currentPage = 1; renderSection(s); });
	const btnPrev = $('<button>&lt;</button>').prop('disabled', s.currentPage === 1).click(() => { s.currentPage--; renderSection(s); });
	const btnNext = $('<button>&gt;</button>').prop('disabled', s.currentPage === totalPages).click(() => { s.currentPage++; renderSection(s); });
	const btnLast = $('<button>&gt;&gt;</button>').prop('disabled', s.currentPage === totalPages).click(() => { s.currentPage = totalPages; renderSection(s); });

	pag.append(btnFirst, btnPrev);

	let maxButtons = 5;
	let startPage = Math.max(1, s.currentPage - Math.floor(maxButtons / 2));
	let endPage = Math.min(totalPages, startPage + maxButtons - 1);
	if (endPage - startPage + 1 < maxButtons) startPage = Math.max(1, endPage - maxButtons + 1);

	if (startPage > 1) {
		pag.append($('<button>1</button>').click(() => { s.currentPage = 1; renderSection(s); }));
		if (startPage > 2) pag.append($('<button class="pointille">...</button>'));
	}

	for (let i = startPage; i <= endPage; i++) {
		const btn = $('<button>' + i + '</button>').addClass(i === s.currentPage ? 'active' : '').click(() => { s.currentPage = i; renderSection(s); });
		pag.append(btn);
	}

	if (endPage < totalPages) {
		if (endPage < totalPages - 1) pag.append($('<button class="pointille">...</button>'));
		pag.append($('<button>' + totalPages + '</button>').click(() => { s.currentPage = totalPages; renderSection(s); }));
	}

	pag.append(btnNext, btnLast);
}

// --- Recherche et changement de section ---
$('.section-btn').click(function () {
	$('.section-btn').removeClass('active');
	$(this).addClass('active');
	const index = $(this).data('index');
	$('.main-sous-content-div').removeClass('active-main-sous-content');
	$('.main-sous-content-div').eq(index).addClass('active-main-sous-content');
	activeSectionIndex = index;

	const query = $('.searchBox').val().toLowerCase();
	const s = sections[activeSectionIndex];
	s.filtered = s.items.filter(div => $(div).text().toLowerCase().includes(query));
	s.currentPage = 1;
	renderSection(s);
});

$('.searchBox').on('keyup', function () {
	const query = $(this).val().toLowerCase();
	const s = sections[activeSectionIndex];
	s.filtered = s.items.filter(div => $(div).text().toLowerCase().includes(query));
	s.currentPage = 1;
	renderSection(s);
});

// --- Fonction pour prepend un élément dans content-list2 ---
// --- Fonction pour prepend un élément dans content-list2 ---
function prependElementById(id_raw) {
	const s = sections[1]; // content-list2

	// Retirer de items et mettre en début
	const index = s.items.findIndex(div => $(div).attr('id') === 'prepend_row_' + id_raw);
	if (index !== -1) {
		const element = s.items.splice(index, 1)[0];
		s.items.unshift(element);
	}

	// Même pour filtered
	const filteredIndex = s.filtered.findIndex(div => $(div).attr('id') === 'prepend_row_' + id_raw);
	if (filteredIndex !== -1) {
		const filteredElement = s.filtered.splice(filteredIndex, 1)[0];
		s.filtered.unshift(filteredElement);
	}

	// Afficher la page 1 pour voir le prepend
	s.currentPage = 1;
	renderSection(s);

	// ⚡ Mise à jour des inputs après que l'élément soit dans le DOM
	const $textInputAdd = $('#text-input-add_' + id_raw);
	const $textInputPrix = $('#text-input-add-prix_' + id_raw);

	if ($textInputAdd.length ) {
		$textInputAdd.val($('#add_quantite_' + id_raw).val());
	}
	if ($textInputPrix.length) {
		$textInputPrix.val(Number($('#add_prix_' + id_raw).val()).toLocaleString('fi-FI'));
	}
}
function prependElementById_add(id_raw) {
	const s = sections[1]; // content-list2

	// Retirer de items et mettre en début
	const index = s.items.findIndex(div => $(div).attr('id') === 'prepend_row_' + id_raw);
	if (index !== -1) {
		const element = s.items.splice(index, 1)[0];
		s.items.unshift(element);
	}

	// Même pour filtered
	const filteredIndex = s.filtered.findIndex(div => $(div).attr('id') === 'prepend_row_' + id_raw);
	if (filteredIndex !== -1) {
		const filteredElement = s.filtered.splice(filteredIndex, 1)[0];
		s.filtered.unshift(filteredElement);
	}

	// Afficher la page 1 pour voir le prepend
	s.currentPage = 1;
	renderSection(s);

	// ⚡ Mise à jour des inputs après que l'élément soit dans le DOM
	
}
// --- Initialisation des sections ---
sections.forEach((s, index) => updateSectionItems(index));
