var url = $(location).attr("origin");
url += '/freezer_ui/api/clients';

$.ajax({
    url: url,
    type: "GET",
    cache: false,
    dataType: 'json',
    contentType: 'application/json; charset=utf-8' ,
    success: function(data) {
        $.each(data, function(index, item) {
            $("#available_clients").append(
                '<tr><td class="multi_select_column">' +
                '<input type="radio" name="client" value=' + item["client"]["client_id"] + '></td>' +
                '<td>' + item["client"]["hostname"] + '</td></tr>'
            );
        });
    },
    error: function(request, error) {
        console.error(error);
        $("#available_clients").append(
                '<tr><td>Error getting client list</td></tr>'
            );
    }
});

