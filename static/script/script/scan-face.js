const video = document.getElementById('video-face');
const canvas = document.getElementById('overlay-face');
const ctx = canvas.getContext('2d');
const resultsInput = document.getElementById('resultsInput-face');
const resultsDiv = document.getElementById('resultsDiv-face');

async function startVideo() {
	try {
		const stream = await navigator.mediaDevices.getUserMedia({ video: true });
		video.srcObject = stream;
	} catch (err) {
		console.error("Erreur d'accès caméra :", err);
		resultsDiv.textContent = 'Erreur d’accès caméra';
	}
}

// Charger les modèles face-api
Promise.all([
	faceapi.nets.tinyFaceDetector.loadFromUri('../models'),
	faceapi.nets.faceLandmark68Net.loadFromUri('../models'),
	faceapi.nets.faceRecognitionNet.loadFromUri('../models'),
	faceapi.nets.ssdMobilenetv1.loadFromUri('../models')
]).then(startVideo);

function fetchLabelImages() {
	return $.ajax({
		url: '../controller/pointage/getLabelsWithImages',
		method: 'GET',
		dataType: 'json'
	});
}

async function loadLabeledImages() {
	const data = await fetchLabelImages();

	return Promise.all(
		data.map(async entry => {
			const descriptions = [];

			for (const imageRelPath of entry.images.slice(0, 2)) { // max 2 images/personne
				try {
					const img = await faceapi.fetchImage(`../img/img_employe/${imageRelPath}`);
					const detection = await faceapi
						.detectSingleFace(img)
						.withFaceLandmarks()
						.withFaceDescriptor();

					if (detection) {
						descriptions.push(detection.descriptor);
					}
				} catch (err) {
					console.error(`Erreur chargement ${imageRelPath}`, err);
				}
			}

			if (descriptions.length === 0) return null;
			return new faceapi.LabeledFaceDescriptors(entry.label, descriptions);
		})
	).then(results => results.filter(r => r !== null));
}

video.addEventListener('play', async () => {
	canvas.width = video.videoWidth;
	canvas.height = video.videoHeight;

	const displaySize = { width: video.videoWidth, height: video.videoHeight };
	faceapi.matchDimensions(canvas, displaySize);

	const labeledDescriptors = await loadLabeledImages();

	// Seuil strict mais tolérant (ajustable)
	const faceMatcher = new faceapi.FaceMatcher(labeledDescriptors, 0.60);

	resultsDiv.textContent = 'Prêt pour la reconnaissance faciale';
	let alreadySubmitted = false;

	setInterval(async () => {
		const detections = await faceapi
			.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
			.withFaceLandmarks()
			.withFaceDescriptors();

		const resizedDetections = faceapi.resizeResults(detections, displaySize);
		ctx.clearRect(0, 0, canvas.width, canvas.height);

		const results = resizedDetections.map(d =>
			faceMatcher.findBestMatch(d.descriptor)
		);

		results.forEach((result, i) => {
			const box = resizedDetections[i].detection.box;
			let label;

			if (result.label === 'unknown' || result.distance >= 0.60) {
				label = 'Inconnu';
			} else if (result.distance >= 0.48) {
				label = `? ${result.label} (${result.distance.toFixed(2)})`; // Incertain
			} else {
				label = `${result.label} (${result.distance.toFixed(2)})`; // Fiable
			}

			const drawBox = new faceapi.draw.DrawBox(box, { label });
			drawBox.draw(canvas);
		});

		const nameList = results.map(r => {
			if (r.label === 'unknown' || r.distance >= 0.60) return 'Inconnu';
			if (r.distance >= 0.48) return `?${r.label}`; // Incertain
			return r.label; // Fiable
		});

		resultsDiv.innerHTML =
			'Visages détectés :' +
			(nameList.length ? nameList.join('<br>') : 'Aucun visage reconnu');
		resultsInput.value = nameList.join(', ');

		// Gérer fond transparent selon détection
		const hasFace = resizedDetections.length > 0;
		const overlay = document.getElementById('overlay-face');
		overlay.style.backgroundColor = hasFace ? 'transparent' : 'rgba(0, 0, 0, 0.7)';

		// Soumettre uniquement si au moins un visage fiable reconnu (<0.48)
		const hasRecognizedFace = results.some(
			r => r.label !== 'unknown' && r.distance < 0.48
		);
		if (hasRecognizedFace && !alreadySubmitted) {
			alreadySubmitted = true;
			$('#insertpointage').submit();

			setTimeout(() => {
				alreadySubmitted = false;
			}, 5000);
		}
	}, 300);

});

// Gérer la soumission
$(document).ready(function () {
	$("#insertpointage").on('submit', function (e) {
		e.preventDefault();
		const input = $('#resultsInput-face');
		if (input.length === 0) return;

		const matricule = input.val().trim();
		if (matricule === '') {
			Swal.fire({
				icon: 'warning',
				title: 'Champ vide',
				text: 'Aucun matricule détecté.',
				timer: 2000,
				showConfirmButton: false
			});
			return;
		}

		$.ajax({
			type: 'POST',
			url: '../controller/pointage/saveRecognitionByMatricule.php',
			data: { matricule },
			dataType: 'json',
			success: function (response) {
				showProgressAndThenSwal(response);
			},
			error: function (xhr, status, error) {
				Swal.fire({
					icon: 'error',
					title: 'Erreur serveur',
					text: 'Une erreur serveur est survenue.',
					timer: 2000,
					showConfirmButton: false
				});
			}
		});
	});
});

// Progress bar + SweetAlert

function showProgressAndThenSwal(response) {
	const container = document.getElementById("progressbar-container-face");
	const bar = document.getElementById("progressbar-face");
	const percentText = document.getElementById("progress-percent-face");

	container.style.display = "block";
	bar.style.width = "0%";
	percentText.textContent = "0%";

	let width = 0;
	const duration = 500;
	const intervalTime = 5;
	const increment = (intervalTime / duration) * 100;

	const interval = setInterval(() => {
		width += increment;

		if (width >= 100) {
			width = 100;
			clearInterval(interval);
			bar.style.width = "100%";
			percentText.textContent = "100%";

			// Affichage du message
			setTimeout(() => {
				container.style.display = "none";
				playAudio();
				Swal.fire({
					icon: response.status === "success" ? "success" : "error",
					title: response.status === "success" ? "Pointage enregistré" : "Erreur",
					text: response.message,
					timer: 2000,
					showConfirmButton: false
				});

				// Réinitialiser la barre après l'affichage
				bar.style.width = "0%";
				percentText.textContent = "0%";
			}, 300);
		}

		bar.style.width = width + "%";
		percentText.textContent = Math.floor(width) + "%";
	}, intervalTime);
}

function playAudio() {
	var x = document.getElementById("myAudio2");
	x.play();
}
