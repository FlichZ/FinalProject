
document.addEventListener('DOMContentLoaded', function() {
    // Получаем текущие значения фильтров из URL
    var urlParams = new URLSearchParams(window.location.search);
    var selectedTags = urlParams.getAll('tag') || [];

    // Устанавливаем чекбоксы в соответствии с текущими значениями
    selectedTags.forEach(function(value) {
        var filterCheckbox = document.querySelector('input[name="tag"][value="' + value + '"]');
        if (filterCheckbox) {
            filterCheckbox.checked = true;
        }
    });

    // Слушаем изменения в чекбоксах
    document.querySelectorAll('input[name="tag"]').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            var tagValue = this.value;

            if (this.checked) {
                // Добавляем тег к списку выбранных
                if (!selectedTags.includes(tagValue)) {
                    selectedTags.push(tagValue);
                }
            } else {
                // Убираем тег из списка выбранных
                var index = selectedTags.indexOf(tagValue);
                if (index !== -1) {
                    selectedTags.splice(index, 1);
                }
            }

            // Собираем все выбранные теги и формируем строку параметров для URL
            var selectedTagsParams = selectedTags.map(function(tag) {
                return 'tag=' + tag;
            }).join('&');

            // Формируем новый URL с учетом выбранных тегов
            var newUrl = window.location.pathname + '?' + selectedTagsParams;

            // Перезагружаем страницу с учетом выбранных тегов
            window.location.href = newUrl;
        });
    });
});
