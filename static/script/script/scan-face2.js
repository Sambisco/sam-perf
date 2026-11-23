// =====================
// CONFIG
// =====================
const video = document.getElementById('video-face');
const canvas = document.getElementById('overlay-face');
const ctx = canvas.getContext('2d');
const status = document.getElementById('status');
const result = document.getElementById('result');
const faceDiv = document.querySelector('#focus-box-face .scan .face');
const resultsInput = document.getElementById('resultsInput-face');
const REPEAT_VOICE_COUNT = 1; // nombre de répétitions des messages vocaux

// =====================
// VOIX
// =====================
function speakMessage(message, repeat = 1) {
	if (!('speechSynthesis' in window) || !message) return;
	for (let i = 0; i < repeat; i++) {
		const utterance = new SpeechSynthesisUtterance(message);
		utterance.lang = 'fr-FR';
		utterance.rate = 1;
		utterance.volume = 1;
		speechSynthesis.speak(utterance);
	}
}

// =====================
// WEBCAM
// =====================
async function startVideo() {
	try {
		const stream = await navigator.mediaDevices.getUserMedia({ video: {} });
		video.srcObject = stream;
	} catch (e) {
		status.textContent = "Erreur accès caméra: " + e;
	}
}

// =====================
// CAPTURE SNAPSHOT
// =====================
function captureSnapshot(video) {
	const snapCanvas = document.createElement('canvas');
	snapCanvas.width = video.videoWidth;
	snapCanvas.height = video.videoHeight;
	const snapCtx = snapCanvas.getContext('2d');
	snapCtx.drawImage(video, 0, 0, snapCanvas.width, snapCanvas.height);
	return snapCanvas.toDataURL('image/jpeg');
}

// =====================
// RECONNAISSANCE
// =====================
async function recognizeFace(base64Image) {
	try {
		const response = await $.ajax({
			url: '/controller/pointage/reconnaissance_facial',
			method: 'POST',
			contentType: 'application/json',
			data: JSON.stringify({ image: base64Image }),
			dataType: 'json'
		});

		if (response.status === "error" && response.retry_after) {
			const waitSeconds = response.retry_after;
			Swal.fire({
				icon: "warning",
				title: "Déjà pointé récemment",
				text: `Veuillez attendre ${waitSeconds} secondes avant de re-pointer.`,
				timerProgressBar: true,
				showConfirmButton: false,
				timer: 2000,
			});
			speakMessage(`Déjà pointé récemment. Veuillez attendre ${waitSeconds} secondes.`, REPEAT_VOICE_COUNT);
			return null;
		} else if (response.status === "success" && response.results.length > 0) {
			const res = response.results[0]; // ⚡ Prend le premier résultat
			showProgressAndThenSwal(response);
			speakMessage(`${res.nom_complet}, matricule ${res.matricule}, pointé avec succès`, REPEAT_VOICE_COUNT);
			return res; // ⚡ retourne l'objet complet pour récupérer nom_complet et matricule
		} else {
			Swal.fire({
				icon: "error",
				title: "Erreur",
				text: response.message || "Une erreur est survenue.",
				timer: 2000,
				timerProgressBar: true,
				showConfirmButton: false,
			});
			speakMessage(response.message || "Une erreur est survenue", REPEAT_VOICE_COUNT);
			return null;
		}
	} catch (err) {
		console.error("Erreur reconnaissance:", err);
	
		speakMessage("Erreur serveur, veuillez réessayer", REPEAT_VOICE_COUNT);
		return null;
	}
}

// =====================
// PROGRESS BAR
// =====================
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
				resultsInput.value = "";
				bar.style.width = "0%";
				percentText.textContent = "0%";
			}, 300);
		}
		bar.style.width = width + "%";
		percentText.textContent = Math.floor(width) + "%";
	}, intervalTime);
}

function playAudio() {
	const x = document.getElementById("myAudio2");
	if (x) x.play();
}

// =====================
// WEBCAM + FACEAPI LOOP
// =====================
let lastFaceDescriptor = null;
const FACE_CHANGE_THRESHOLD = 0.4;

Promise.all([
	faceapi.nets.tinyFaceDetector.loadFromUri('/static/models'),
	faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
	faceapi.nets.faceRecognitionNet.loadFromUri('/static/models')
]).then(() => {
	status.textContent = "Modèles chargés";
	startVideo();
});

video.addEventListener('play', () => {
	const displaySize = { width: video.videoWidth, height: video.videoHeight };
	canvas.width = displaySize.width;
	canvas.height = displaySize.height;
	faceapi.matchDimensions(canvas, displaySize);

	setInterval(async () => {
		const detection = await faceapi.detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.3 }))
			.withFaceLandmarks()
			.withFaceDescriptor();

		ctx.clearRect(0, 0, canvas.width, canvas.height);

		if (detection) {
			status.textContent = "Visage détecté, reconnaissance en cours...";
			const resizedDetection = faceapi.resizeResults(detection, displaySize);
			faceapi.draw.drawDetections(canvas, resizedDetection);
			faceapi.draw.drawFaceLandmarks(canvas, resizedDetection);

			const currentDescriptor = detection.descriptor;
			let isNewFace = true;
			if (lastFaceDescriptor) {
				const distance = faceapi.euclideanDistance(currentDescriptor, lastFaceDescriptor);
				if (distance < FACE_CHANGE_THRESHOLD) {
					isNewFace = false;
					status.textContent = "Même visage détecté — attente pour éviter répétition";
				}
			}

			if (isNewFace) {
				lastFaceDescriptor = currentDescriptor;
				const snapshot = captureSnapshot(video);
				const res = await recognizeFace(snapshot);

				if (faceDiv) {
					faceDiv.classList.add('face-detected');
					faceDiv.classList.remove('no-face');
				}

				canvas.style.backgroundColor = 'transparent';

				if (res) {
					result.textContent = `Reconnu : ${res.nom_complet}`;
					resultsInput.value = res.nom_complet;
				} else {
					result.textContent = "Visage non reconnu";
					resultsInput.value = "";
				}
			}

		} else {
			status.textContent = "Aucun visage détecté";
			result.textContent = "";
			resultsInput.value = "";
			lastFaceDescriptor = null;

			if (faceDiv) {
				faceDiv.classList.remove('face-detected');
				faceDiv.classList.add('no-face');
			}

			canvas.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
		}
	}, 1500);
});
