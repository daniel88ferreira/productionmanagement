var notificationTimeout = null;

function showNotification(severity, text) {
    var notification_html = '<div class="col-xs-6 text-right" id="notification">' +
        '<div class="alert alert-dismissible alert-'+severity+'">' +
        '<button type="button" class="close" data-dismiss="alert">&times;</button>' +
        text +
        '</div>' +
        '</div>';
    $("#notification").replaceWith(notification_html);
    clearTimeout(notificationTimeout);
    notificationTimeout = setTimeout(removeNotification, 3000);
}

function removeNotification() {
    var notification_html = '<div class="col-xs-6 text-right" id="notification"></div>';
    $("#notification").html(notification_html);
}
//For getting CSRF token
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(document).ready(function() {
    $("#cancel-exec-order").click(function(e) {
        e.preventDefault();

        var csrftoken = getCookie('csrftoken');
        $.ajax({
            url: window.location.href,
            type: "POST", // http method
            data: {
                csrfmiddlewaretoken: csrftoken,
                action: "cancel-exec-order"
            },
            success: function (json) {
                $("#cancel-exec-order").hide();
                var exec_order_button = $("#create-exec-order");
                exec_order_button.text("Criar Ordem de Execução");
                exec_order_button.removeClass("btn-success");
                exec_order_button.addClass("btn-info");
                $("button[id*='-exec_']").each(function () {
                   $(this).hide()
                });
                showNotification('danger',
                    'Ordem ' + json['deleted_order_description'] + ' : ' + json['deleted_order_id'] + ' removida.');
            },
            error: function () {
                showNotification('danger', 'Erro!');
                location.reload();
            }
        });
    });

    $("#create-exec-order").click(function(e) {
        e.preventDefault();

        var csrftoken = getCookie('csrftoken');
        var create_button = $(this);
        $.ajax({
            url: window.location.href,
            type: "POST", // http method
            data: {
                csrfmiddlewaretoken: csrftoken,
                action: "create-or-show-exec-order"
            },
            success: function (json) {
                if (json['action_performed'] === 'create') {
                    create_button.text("Ver Ordem de Execução");
                    create_button.removeClass("btn-info");
                    create_button.addClass("btn-success");
                    $("#cancel-exec-order").show();
                    $("button[id^='add-to-exec_']").each(function () {
                        $(this).show()
                    });
                    showNotification('success', 'Numero: ' + json['exec_order_number']);
                }
                else if (json['action_performed'] === 'show') {
                    // view exec order
                    console.log("Current exec order: " + json['exec_order_url']);
                    window.document.location = json['exec_order_url'];
                }
            }
        });
    });

    $("button[id^='add-to-exec_']").click(function(e) {
        e.preventDefault();

        var csrftoken = getCookie('csrftoken');
        var order_id = this.id.split("_")[1];
        var this_button = $(this);

        $.ajax({
            url: window.location.href,
            type: "POST", // http method
            data: {
                csrfmiddlewaretoken: csrftoken,
                action: "add-or-from-exec-order",
                order_id: order_id
            },
            success: function (json) {
                if (json['action_performed'] === 'add') {
                    this_button.text("Remove");
                    this_button.removeClass("btn-success");
                    this_button.addClass("btn-danger");
                    showNotification('info', 'Order ' + json['order_number'] + ' added to ExecOrder ' + json['exec_order_number']);
                }
                else if (json['action_performed'] === 'rm') {
                    this_button.text("Add");
                    this_button.removeClass("btn-danger");
                    this_button.addClass("btn-success");
                    showNotification('warning', 'Order ' + json['order_number'] + ' removed from ExecOrder ' + json['exec_order_number']);
                }
            }
        });
    });

    $("button[id^='view_']").click(function(e) {
        e.preventDefault();
        window.document.location = $(this).data("href");
    });
});