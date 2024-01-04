 document.addEventListener('DOMContentLoaded', function() {
      const nameInput = document.querySelector('#id_name');
      const slugInput = document.querySelector('#id_slug');

      nameInput.addEventListener('input', function() {
        const nameValue = this.value.trim().toLowerCase().replace(/\s+/g, '-');
        slugInput.value = nameValue;
      });
    });