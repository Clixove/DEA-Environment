function export_html(id, filename) {
    const text = document.getElementById(id).innerHTML;
    if (text.length > 0) {
        const blob = new Blob([text], {type: "text/plain;charset=utf-8"});
        const link = document.createElement('a');
        link.download = filename;
        link.href = window.URL.createObjectURL(blob);
        link.click();
        window.URL.revokeObjectURL(link.href);
    }
}
function set_compact(id) {
    const ul = document.getElementById(id);
    ul.setAttribute("class", "d-flex flex-wrap");
    const li = ul.children;
    for (let x=0; x<li.length; x++) {
        li[x].setAttribute("class", "flex-item text-nowrap");
        li[x].setAttribute("style", "width: 14rem; overflow-x: hidden;");
    }
}
function set_expand(id) {
    const ul = document.getElementById(id);
    ul.removeAttribute("class");
}
function check_all(button, checkbox_list_id) {
    const cbs = document.getElementById(checkbox_list_id).querySelectorAll('input[type=checkbox]');
    if (button.checked) {
        cbs.forEach((cb) => cb.checked = true);
    } else {
        cbs.forEach((cb) => cb.checked = false);
    }
}
function async_submit_form(form_id, url, response_id) {
    $('#' + form_id).submit(function (e) {
        e.preventDefault();
        $.ajax({
            type: 'POST',
            url: url,
            data: $(this).serialize(),
            success: (response) => {document.getElementById(response_id).innerHTML = response;},
        });
    });
}
function scale_svg(container_id, max_width=400, height_ratio=1) {
    let svg = document.getElementById(container_id).getElementsByTagName('svg');
    for (let i=0; i < svg.length; i++) {
        let this_svg = svg[i];
        let proper_width_ = Math.min(this_svg.parentNode.offsetWidth, max_width);
        const proper_height_ = proper_width_ * height_ratio;
        this_svg.setAttribute('width', proper_width_.toString() + 'px');
        this_svg.setAttribute('height', proper_height_.toString() + 'px')
    }
}
