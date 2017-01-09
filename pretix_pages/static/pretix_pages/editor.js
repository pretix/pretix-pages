$(function () {
    var slug_generated = !$("form[data-id]").attr("data-id");
    $('#id_slug').on("keydown keyup keypress", function () {
        slug_generated = false;
    });
    $('input[id^=id_title_]').on("keydown keyup keypress change", function () {
        if (slug_generated) {
            var title = $('input[id^=id_title_]').filter(function () {
                return !!this.value;
            }).first().val();  // First non-empty language
            var slug = title.toLowerCase()
                .replace(/\s+/g, '-')
                .replace(/[^\w\-]+/g, '')
                .replace(/\-\-+/g, '-')
                .replace(/^-+/, '')
                .replace(/-+$/, '')
                .substr(0, 150);
            $('#id_slug').val(slug);
        }
    });
});
