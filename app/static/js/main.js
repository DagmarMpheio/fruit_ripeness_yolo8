document.querySelectorAll('.dropzone_input').forEach(inputElement => {
    const dropzoneElement = inputElement.closest('.dropzone');
    dropzoneElement.addEventListener('click', e => {
      inputElement.click();
    });
    inputElement.addEventListener('change', e => {
      if (inputElement.files.length) {
        updateThumbnail(dropzoneElement, inputElement.files[0]);
      }
    });
  
    dropzoneElement.addEventListener('drop', e => {
      e.preventDefault();
      if (e.dataTransfer.files.length) {
        inputElement.files = e.dataTransfer.files;
        updateThumbnail(dropzoneElement, e.dataTransfer.files[0]);
      }
    });
  });
  
  function updateThumbnail(dropzoneElement, file) {
    let thumbnailElement = dropzoneElement.querySelector('.dropzone_thumb');
    if (dropzoneElement.querySelector('.dropzone_prompt')) {
      dropzoneElement.querySelector('.dropzone_prompt').remove();
    }
    if (!thumbnailElement) {
      thumbnailElement = document.createElement('div');
      thumbnailElement.classList.add('dropzone_thumb');
      dropzoneElement.appendChild(thumbnailElement);
    }
    thumbnailElement.dataset.label = file.name;
  
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        thumbnailElement.style.backgroundImage = `url('${reader.result}')`;
      };
    } else {
      thumbnailElement.style.backgroundImage = null;
    }
  }
  