document.addEventListener('DOMContentLoaded', function () {

  const photoInput = document.getElementById('photo-input');
  const avatarPreview = document.getElementById('avatar-preview');
  const avatarPlaceholder = document.getElementById('avatar-placeholder');

  if (!photoInput) return;

  photoInput.addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
      // Показати превью
      if (avatarPlaceholder) avatarPlaceholder.style.display = 'none';
      avatarPreview.src = e.target.result;
      avatarPreview.style.display = 'block';
    };
    reader.readAsDataURL(file);
  });

});
