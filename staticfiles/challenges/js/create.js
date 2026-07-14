// Показывает поле "Другая игра", только когда выбран соответствующий пункт.
// Больше JS на этой странице не требуется — всё остальное делает Django.
document.addEventListener('DOMContentLoaded', function () {
    var select = document.getElementById('id_game_select');
    var wrapper = document.getElementById('id_game_other_wrapper');

    function toggleOtherField() {
        if (select.value === 'other') {
            wrapper.classList.remove('hidden');
        } else {
            wrapper.classList.add('hidden');
        }
    }

    if (select && wrapper) {
        toggleOtherField();
        select.addEventListener('change', toggleOtherField);
    }
});
