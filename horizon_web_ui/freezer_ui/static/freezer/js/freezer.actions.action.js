function hideEverything() {
    // Common controls
    $("#id_backup_name").closest(".form-group").hide();
    $("#id_container").closest(".form-group").hide();
    $("#id_path_to_backup").closest(".form-group").hide();
    $("#id_storage").closest(".form-group").hide();

    // Backup specific controls
    $("#id_mysql_conf").closest(".form-group").hide();
    $("#id_mode").closest(".form-group").hide();
    $("#id_sql_server_conf").closest(".form-group").hide();
    $("#id_cinder_vol_id").closest(".form-group").hide();
    $("#id_nova_inst_id").closest(".form-group").hide();

    // Restore specific controls
    $("#id_restore_abs_path").closest(".form-group").hide();
    $("#id_restore_from_host").closest(".form-group").hide();
    $("#id_restore_from_date").closest(".form-group").hide();

    // Admin specific controls
    $("#id_remove_older_than").closest(".form-group").hide();
    $("#id_remove_from_date").closest(".form-group").hide();
    $("#id_get_object").closest(".form-group").hide();
    $("#id_dst_file").closest(".form-group").hide();

    // SSH specific controls
    $("#id_ssh_key").closest(".form-group").hide();
    $("#id_ssh_username").closest(".form-group").hide();
    $("#id_ssh_host").closest(".form-group").hide();

}

function showAdminOptions() {
    $("#id_remove_older_than").closest(".form-group").show();
    $("#id_remove_from_date").closest(".form-group").show();
    $("#id_get_object").closest(".form-group").show();
    $("#id_dst_file").closest(".form-group").show();
}

function showBackupOptions() {
    $("#id_is_windows").closest(".form-group").show();
    $("#id_mode").closest(".form-group").show();
    $("#id_container").closest(".form-group").show();
    $("#id_path_to_backup").closest(".form-group").show();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_storage").closest(".form-group").show();
}

function showRestoreOptions() {
    $("#id_container").closest(".form-group").show();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_restore_abs_path").closest(".form-group").show();
    $("#id_restore_from_host").closest(".form-group").show();
    $("#id_restore_from_date").closest(".form-group").show();
    $("#id_storage").closest(".form-group").show();
}

function showNovaOptions() {
    $("#id_mode").closest(".form-group").show();
    $("#id_nova_inst_id").closest(".form-group").show();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_container").closest(".form-group").show();
}

function showCinderOptions() {
    $("#id_mode").closest(".form-group").show();
    $("#id_cinder_vol_id").closest(".form-group").show();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_container").closest(".form-group").show();
}

function showSSHOptions(){
    $("#id_ssh_key").closest(".form-group").show();
    $("#id_ssh_username").closest(".form-group").show();
    $("#id_ssh_host").closest(".form-group").show();
}

hideEverything();

$("#id_action").change(function() {
    // Update the inputs according freezer action

    if ($("#id_action").val() == 'backup') {
        hideEverything();
        showBackupOptions();
    }
    else if ($("#id_action").val() == 'restore') {
        hideEverything();
        showRestoreOptions();
    }
    else if ($("#id_action").val() == 'admin') {
        hideEverything();
        showAdminOptions();
    }
    else  {
        hideEverything();
    }
});


$("#id_storage").change(function() {
    // Update the inputs according freezer action

    if ($("#id_storage").val() == 'swift') {
        hideEverything();
        showBackupOptions();
    }
    else if ($("#id_storage").val() == 'ssh') {
        hideEverything();
        showBackupOptions();
        showSSHOptions();
    }
    else if ($("#id_storage").val() == 'local') {
        hideEverything();
        showBackupOptions();
    }
    else  {
        hideEverything();
    }
});


$("#id_mode").change(function() {
    if ($("#id_action").val() == 'backup') {
        if ($("#id_mode").val() == 'fs') {
            hideEverything();
            showBackupOptions();
        }
        else if ($("#id_mode").val() == 'mysql') {
            hideEverything();
            showBackupOptions();
            $("#id_mysql_conf").closest(".form-group").show();
            $("#id_sql_server_conf").closest(".form-group").hide();
        }
        else if ($("#id_mode").val() == 'mssql') {
            hideEverything();
            showBackupOptions();
            $("#id_sql_server_conf").closest(".form-group").show();
            $("#id_mysql_conf").closest(".form-group").hide();
        }
        else if ($("#id_mode").val() == 'mongo') {
            hideEverything();
            showBackupOptions();
            $("#id_sql_server_conf").closest(".form-group").hide();
            $("#id_mysql_conf").closest(".form-group").hide();
        }
        else if ($("#id_mode").val() == 'cinder') {
            hideEverything();
            showCinderOptions();
            $("#id_cinder_vol_id").closest(".form-group").show().addClass("required");
        }
        else if ($("#id_mode").val() == 'nova') {
            hideEverything();
            showNovaOptions();
            $("#id_nova_inst_id").closest(".form-group").show().addClass("required");
        }
        else {

        }
    }
});

