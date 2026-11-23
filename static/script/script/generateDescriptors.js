const faceapi = require('@vladmandic/face-api');
const canvas = require('canvas');
const fs = require('fs');
const path = require('path');

const { Canvas, Image, ImageData } = canvas;
faceapi.env.monkeyPatch({ Canvas, Image, ImageData });

const MODEL_PATH = path.join(__dirname, '../../models');
const IMAGES_PATH = path.join(__dirname, '../../img/img_employe');

async function loadModels() {
	await faceapi.nets.ssdMobilenetv1.loadFromDisk(MODEL_PATH);
	await faceapi.nets.faceLandmark68Net.loadFromDisk(MODEL_PATH);
	await faceapi.nets.faceRecognitionNet.loadFromDisk(MODEL_PATH);
}

async function createLabeledDescriptors() {
	const labels = fs.readdirSync(IMAGES_PATH).filter(file => fs.lstatSync(path.join(IMAGES_PATH, file)).isDirectory());
	const labeledDescriptors = [];

	for (const label of labels) {
		const descriptions = [];
		const images = fs.readdirSync(path.join(IMAGES_PATH, label));

		for (const image of images) {
			const img = await canvas.loadImage(path.join(IMAGES_PATH, label, image));
			const detections = await faceapi.detectSingleFace(img).withFaceLandmarks().withFaceDescriptor();

			if (!detections) {
				console.warn(`Pas de visage détecté pour ${label}/${image}`);
				continue;
			}

			descriptions.push(detections.descriptor);
		}

		if (descriptions.length > 0) {
			labeledDescriptors.push({
				label,
				descriptors: descriptions.map(d => Array.from(d)),
			});
		}
	}

	return labeledDescriptors;
}

(async () => {
	await loadModels();

	const data = await createLabeledDescriptors();

	fs.writeFileSync('descriptors.json', JSON.stringify(data, null, 2));
	console.log('Descriptors générés dans public/descriptors.json');
})();
