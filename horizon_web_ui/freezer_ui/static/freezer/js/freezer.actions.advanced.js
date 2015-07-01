function hideIncrementalOptions() {
    $("#id_max_level").closest(".form-group").hide();
    $("#id_always_level").closest(".form-group").hide();
    $("#id_restart_always_level").closest(".form-group").hide();
}

$("#id_no_incremental").click(function() {
    if ($("#id_no_incremental").is(":checked")) {
        $("#id_max_level").closest(".form-group").hide();
        $("#id_always_level").closest(".form-group").hide();
        $("#id_restart_always_level").closest(".form-group").hide();
    }
    else {
        $("#id_max_level").closest(".form-group").show();
        $("#id_always_level").closest(".form-group").show();
        $("#id_restart_always_level").closest(".form-group").show();
    }
});


hideIncrementalOptions();