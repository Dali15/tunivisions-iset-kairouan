(() => {
    const initializeCrop = (widget) => {
        const form = widget.closest('form');
        const input = form?.querySelector('input[type="file"][name="profile_picture"]');
        const stage = widget.querySelector('[data-crop-stage]');
        const image = widget.querySelector('[data-crop-image]');
        const zoom = widget.querySelector('[data-crop-zoom]');
        const status = widget.querySelector('[data-crop-status]');
        const submitButton = form?.querySelector('button[type="submit"]');

        if (!form || !input || !stage || !image || !zoom || !status) {
            throw new Error('Le composant de recadrage de la photo de profil est incomplet.');
        }

        let objectUrl = null;
        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;
        let dragging = false;
        let dragStartX = 0;
        let dragStartY = 0;
        let cropReady = false;

        const setStatus = (message, isError = false) => {
            status.textContent = message;
            status.classList.toggle('is-error', isError);
        };

        const drawPreview = () => {
            const side = stage.clientWidth;
            if (!side || !image.naturalWidth || !image.naturalHeight) return;

            const zoomFactor = Number(zoom.value);
            scale = Math.max(side / image.naturalWidth, side / image.naturalHeight) * zoomFactor;
            const width = image.naturalWidth * scale;
            const height = image.naturalHeight * scale;
            offsetX = Math.min(0, Math.max(side - width, offsetX));
            offsetY = Math.min(0, Math.max(side - height, offsetY));
            image.style.width = `${width}px`;
            image.style.height = `${height}px`;
            image.style.left = `${offsetX}px`;
            image.style.top = `${offsetY}px`;
        };

        input.addEventListener('change', () => {
            cropReady = false;
            const file = input.files?.[0];
            if (!file) {
                widget.classList.remove('has-image');
                image.removeAttribute('src');
                if (objectUrl) URL.revokeObjectURL(objectUrl);
                objectUrl = null;
                setStatus('Choisissez une photo pour la recadrer avant l’enregistrement.');
                return;
            }

            if (!file.type.startsWith('image/')) {
                input.value = '';
                widget.classList.remove('has-image');
                setStatus('Le fichier sélectionné n’est pas une image valide.', true);
                return;
            }

            if (objectUrl) URL.revokeObjectURL(objectUrl);
            objectUrl = URL.createObjectURL(file);
            image.onload = () => {
                widget.classList.add('has-image');
                zoom.value = '1.15';
                const side = stage.clientWidth;
                const baseScale = Math.max(side / image.naturalWidth, side / image.naturalHeight);
                const height = image.naturalHeight * baseScale * Number(zoom.value);
                offsetX = (side - image.naturalWidth * baseScale * Number(zoom.value)) / 2;
                offsetY = (side - height) * 0.15;
                drawPreview();
                setStatus('Faites glisser la photo et ajustez le zoom.');
            };
            image.onerror = () => {
                widget.classList.remove('has-image');
                setStatus('Impossible de lire cette image. Essayez un autre fichier.', true);
            };
            image.src = objectUrl;
        });

        zoom.addEventListener('input', drawPreview);

        stage.addEventListener('pointerdown', (event) => {
            if (!widget.classList.contains('has-image')) return;
            dragging = true;
            dragStartX = event.clientX - offsetX;
            dragStartY = event.clientY - offsetY;
            stage.setPointerCapture(event.pointerId);
        });
        stage.addEventListener('pointermove', (event) => {
            if (!dragging) return;
            offsetX = event.clientX - dragStartX;
            offsetY = event.clientY - dragStartY;
            drawPreview();
        });
        stage.addEventListener('pointerup', () => { dragging = false; });
        stage.addEventListener('pointercancel', () => { dragging = false; });
        window.addEventListener('resize', drawPreview);

        form.addEventListener('submit', async (event) => {
            if (cropReady || !input.files?.[0]) return;
            event.preventDefault();
            if (!image.complete || !image.naturalWidth) {
                setStatus('Attendez que l’aperçu de la photo soit prêt.', true);
                return;
            }

            if (submitButton) submitButton.disabled = true;
            setStatus('Préparation de la photo recadrée…');
            try {
                const side = stage.clientWidth;
                const sourceSize = side / scale;
                const sourceX = -offsetX / scale;
                const sourceY = -offsetY / scale;
                const canvas = document.createElement('canvas');
                canvas.width = 512;
                canvas.height = 512;
                const context = canvas.getContext('2d');
                if (!context) throw new Error('Le recadrage d’image n’est pas disponible dans ce navigateur.');
                context.drawImage(image, sourceX, sourceY, sourceSize, sourceSize, 0, 0, 512, 512);

                const blob = await new Promise((resolve, reject) => {
                    canvas.toBlob((result) => {
                        if (result) resolve(result);
                        else reject(new Error('La création de la photo recadrée a échoué.'));
                    }, 'image/jpeg', 0.92);
                });
                const fileName = (input.files[0].name.replace(/\.[^.]+$/, '') || 'profile') + '-crop.jpg';
                const croppedFile = new File([blob], fileName, { type: 'image/jpeg', lastModified: Date.now() });
                const transfer = new DataTransfer();
                transfer.items.add(croppedFile);
                input.files = transfer.files;
                cropReady = true;
                form.requestSubmit(event.submitter || undefined);
            } catch (error) {
                setStatus(error.message || 'Impossible de préparer la photo recadrée.', true);
                if (submitButton) submitButton.disabled = false;
            }
        });
    };

    document.querySelectorAll('[data-profile-crop]').forEach(initializeCrop);
})();
