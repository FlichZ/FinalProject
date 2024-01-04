document.addEventListener('DOMContentLoaded', function () {
            var titleInput = document.querySelector('#id_title');
            var slugInput = document.querySelector('#id_slug');

            titleInput.addEventListener('input', function () {
                var titleValue = titleInput.value;
                var slugValue = slugify(titleValue, { lower: true, strict: true });
                slugInput.value = slugValue;
            });
        });


    document.addEventListener('DOMContentLoaded', function() {
      const nameInput = document.querySelector('#id_name');
      const slugInput = document.querySelector('#id_slug');

      nameInput.addEventListener('input', function() {
        const nameValue = this.value.trim().toLowerCase().replace(/\s+/g, '-');
        slugInput.value = nameValue;
      });
    });
