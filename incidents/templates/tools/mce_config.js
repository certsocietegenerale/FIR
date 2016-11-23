tinyMCE.init({
    mode: "textareas",
    editor_selector: "mce",
    theme: "modern",
    skin: "light",
    plugins: "paste,table,code,preview,fullscreen",
    language: "{{ mce_lang }}",
    directionality: "ltr",
    height:'400',
    toolbar: "undo redo | styleselect | bold italic | bullist numlist outdent indent code",
    statusbar:false,
});
