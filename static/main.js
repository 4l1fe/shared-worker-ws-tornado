var worker = new SharedWorker("static/shared_worker.js"),
    logs = $('#logs'),
    received = $('#received'),
    client_id = Cookies.get('client_id');


function upload() {
    var logs = $('#logs'),
        form = $('form').get(0),
        form_data = new FormData(form);

    $.ajax({
        url: form.action,
        method: 'POST',
        data: form_data,
        contentType: false,
        processData: false,
        success: function(data, status, jqxhr) {
            logs.append('success sending')
        },
        error: function(jqxhr, status, error ) {
            logs.append(error)
        }
    })
}


function human_readable(bytes) {
    var thresh = 1000,
        units = ['kB','MB','GB','TB','PB','EB','ZB','YB'],
        u = -1;

    if(Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }

    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);

    return bytes.toFixed(1)+' '+units[u];
}

worker.port.addEventListener('message', function(event) {
    var msg = JSON.parse(event.data);

    if (msg['received']) {
        received.text(human_readable(msg['received']));
    }
    else if (msg['connection']) {
        logs.append(msg['connection']);
    }
}, false);


$(function() {
    $(document).on('click', 'button', upload);

    $('#client_id').text(client_id);
    worker.port.start();
});