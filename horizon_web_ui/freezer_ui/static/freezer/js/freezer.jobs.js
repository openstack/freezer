/* Launch Jobs workflow */

function hideEverything() {
    // Common controls
    $("#id_is_windows").closest(".form-group").hide();
    $("#id_backup_name").closest(".form-group").hide();
    $("#id_container").closest(".form-group").hide();
    $("#id_path_to_backup").closest(".form-group").hide();
    $("#id_insecure").closest(".form-group").hide();
    $("#id_os_auth_ver").closest(".form-group").hide();
    $("#id_dry_run").closest(".form-group").hide();
    $("#id_encryption_password").closest(".form-group").hide();
    $("#id_exclude").closest(".form-group").hide();
    $("#id_log_file").closest(".form-group").hide();
    $("#id_proxy").closest(".form-group").hide();
    $("#id_max_priority").closest(".form-group").hide();
    $("#id_quiet").closest(".form-group").hide();
    $("#id_advanced_configuration").closest(".form-group").hide();
    $("#id_description").closest(".form-group").hide();
    $("#id_client_id").closest(".form-group").hide();
    $("#id_tag").closest(".form-group").hide();


    // Backup specific controls
    $("#id_mysql_conf").closest(".form-group").hide();
    $("#id_compression").closest(".form-group").hide();
    $("#id_optimize").closest(".form-group").hide();
    $("#id_upload_limit").closest(".form-group").hide();
    $("#id_dereference_symlink").closest(".form-group").hide();
    $("#id_max_segment_size").closest(".form-group").hide();
    $("#id_dst_file").closest(".form-group").hide();
    $("#id_mode").closest(".form-group").hide();
    $("#id_sql_server_conf").closest(".form-group").hide();
    $("#id_cinder_vol_id").closest(".form-group").hide();
    $("#id_nova_inst_id").closest(".form-group").hide();
    $("#id_max_level").closest(".form-group").hide();
    $("#id_always_level").closest(".form-group").hide();
    $("#id_restart_always_level").closest(".form-group").hide();
    $("#id_no_incremental").closest(".form-group").hide();
    $("#id_hostname").closest(".form-group").hide();
    $("#id_upload").closest(".form-group").hide();

    // Snapshot specific controls
    $("#id_use_snapshot").closest(".form-group").hide();
    $("#id_lvm_auto_snap").closest(".form-group").hide();
    $("#id_lvm_srcvol").closest(".form-group").hide();
    $("#id_lvm_snapname").closest(".form-group").hide();
    $("#id_lvm_snapsize").closest(".form-group").hide();
    $("#id_lvm_dirmount").closest(".form-group").hide();
    $("#id_lvm_volgroup").closest(".form-group").hide();
    $("#id_vssadmin").closest(".form-group").hide();

    // Restore specific controls
    $("#id_download_limit").closest(".form-group").hide();
    $("#id_restore_abs_path").closest(".form-group").hide();
    $("#id_restore_from_host").closest(".form-group").hide();
    $("#id_restore_from_date").closest(".form-group").hide();

    // Admin specific controls
    $("#id_remove_older_than").closest(".form-group").hide();
    $("#id_remove_from_date").closest(".form-group").hide();
    $("#id_get_object").closest(".form-group").hide();

}

function showAdminOptions() {
    $("#id_remove_older_than").closest(".form-group").show();
    $("#id_remove_from_date").closest(".form-group").show();
    $("#id_get_object").closest(".form-group").show();
}

function showBackupOptions() {
    $("#id_is_windows").closest(".form-group").show();
    $("#id_mode").closest(".form-group").show();
    $("#id_upload").closest(".form-group").show();
    $("#id_container").closest(".form-group").show();
    $("#id_use_snapshot").closest(".form-group").show();
    $("#id_path_to_backup").closest(".form-group").show();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_dereference_symlink").closest(".form-group").show();
    $("#id_os_auth_ver").closest(".form-group").show();
    $("#id_upload_limit").closest(".form-group").show();
    $("#id_max_priority").closest(".form-group").show();
    $("#id_quiet").closest(".form-group").show();
    $("#id_proxy").closest(".form-group").show();
    $("#id_log_file").closest(".form-group").show();
    $("#id_exclude").closest(".form-group").show();
    $("#id_optimize").closest(".form-group").show();
    $("#id_compression").closest(".form-group").show();
    $("#id_encryption_password").closest(".form-group").show();
    $("#id_max_segment_size").closest(".form-group").show();
    $("#id_no_incremental").closest(".form-group").show();
    $("#id_hostname").closest(".form-group").show();

    $("#id_container").closest(".form-group").addClass("required");

}

function showRestoreOptions() {
    $("#id_container").closest(".form-group").show();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_restore_abs_path").closest(".form-group").show();
    $("#id_restore_from_host").closest(".form-group").show();
    $("#id_restore_from_date").closest(".form-group").show();
    $("#id_os_auth_ver").closest(".form-group").show();
    $("#id_download_limit").closest(".form-group").show();
    $("#id_max_priority").closest(".form-group").show();
    $("#id_quiet").closest(".form-group").show();
    $("#id_proxy").closest(".form-group").show();
    $("#id_log_file").closest(".form-group").show();
}

function showLinuxSnapshotOptions() {
    $("#id_lvm_auto_snap").closest(".form-group").show();
    $("#id_lvm_srcvol").closest(".form-group").show();
    $("#id_lvm_snapname").closest(".form-group").show();
    $("#id_lvm_snapsize").closest(".form-group").show();
    $("#id_lvm_dirmount").closest(".form-group").show();
    $("#id_lvm_volgroup").closest(".form-group").show();
}

function hideLinuxSnapshotOptions() {
    $("#id_lvm_srcvol").closest(".form-group").hide();
    $("#id_lvm_snapname").closest(".form-group").hide();
    $("#id_lvm_snapsize").closest(".form-group").hide();
    $("#id_lvm_dirmount").closest(".form-group").hide();
    $("#id_lvm_volgroup").closest(".form-group").hide();
    $("#id_lvm_auto_snap").closest(".form-group").hide();
}

function showWindowsSnapshotOptions() {
    // TODO: windows doesn't need to display this option
    // because is redundant
    $("#id_vssadmin").closest(".form-group").show();
}

function hideWindowsSnapshotOptions() {
    $("#id_vssadmin").closest(".form-group").hide();
}

function is_windows() {
   if ($("#id_is_windows").is(":checked")) {
       return true;
   }
}

function showSnapshotOptions() {
    if (is_windows()) {
        hideLinuxSnapshotOptions();
        showWindowsSnapshotOptions();
    }
    else {
        hideWindowsSnapshotOptions();
        showLinuxSnapshotOptions();
    }
}

function hideSnapshotOptions() {
    hideWindowsSnapshotOptions();
    hideLinuxSnapshotOptions();
}

function showNovaOptions() {
    $("#id_client_id").closest(".form-group").show();
    $("#id_mode").closest(".form-group").show();
    $("#id_proxy").closest(".form-group").show();
    $("#id_nova_inst_id").closest(".form-group").show();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_container").closest(".form-group").show();
    $("#id_nova_inst_id").closest(".form-group").show().addClass("required");
}

function showCinderOptions() {
    $("#id_client_id").closest(".form-group").show();
    $("#id_mode").closest(".form-group").show();
    $("#id_proxy").closest(".form-group").show();
    $("#id_cinder_vol_id").closest(".form-group").show();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_container").closest(".form-group").show();
    $("#id_path_to_backup").closest(".form-group").show();
    $("#id_cinder_vol_id").closest(".form-group").show().addClass("required");
}

function showIncrementalOptions() {
    $("#id_max_level").closest(".form-group").show();
    $("#id_always_level").closest(".form-group").show();
    $("#id_restart_always_level").closest(".form-group").show();
}

function hideIncrementalOptions() {
    $("#id_max_level").closest(".form-group").hide();
    $("#id_always_level").closest(".form-group").hide();
    $("#id_restart_always_level").closest(".form-group").hide();
    $("#id_advanced_configuration").closest(".form-group").show();
}

function showAdvancedConfigurationOptions() {
    hideEverything();
    showBackupOptions();
    $("#id_tag").closest(".form-group").show();
}

function hideAdvancedConfigurationOptions() {
    hideEverything();
    hideIncrementalOptions();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_container").closest(".form-group").show();
    $("#id_action").closest(".form-group").show();
    $("#id_path_to_backup").closest(".form-group").show();
    $("#id_advanced_configuration").closest(".form-group").show();
    $("#id_mode").closest(".form-group").show();
    $("#id_tag").closest(".form-group").hide();
}

function hideRestoreAdvancedConfigurationOptions() {
    hideEverything();
    $("#id_backup_name").closest(".form-group").show();
    $("#id_container").closest(".form-group").show();
    $("#id_action").closest(".form-group").show();
    $("#id_advanced_configuration").closest(".form-group").show();
    $("#id_restore_abs_path").closest(".form-group").show();
    $("#id_restore_from_host").closest(".form-group").show();
    $("#id_restore_from_date").closest(".form-group").show();
}

function showRestoreAdvancedConfigurationOptions() {
    hideEverything();
    showRestoreOptions();
}

hideEverything();

$("#id_action").change(function() {
    // Update the inputs according freezer action

    if ($("#id_action").val() == 'backup') {
        hideEverything();
        showBackupOptions();
        hideAdvancedConfigurationOptions();
        $("#id_description").closest(".form-group").show();
        $("#id_client_id").closest(".form-group").show();
    }
    else if ($("#id_action").val() == 'restore') {
        hideEverything();
        showRestoreOptions();
        hideRestoreAdvancedConfigurationOptions();
        $("#id_description").closest(".form-group").show();
        $("#id_client_id").closest(".form-group").show();
    }
    else if ($("#id_action").val() == 'admin') {
        hideEverything();
        showAdminOptions();
        $("#id_client_id").closest(".form-group").show();
        $("#id_description").closest(".form-group").show();
    }
    else if ($("#id_action").val() == 'info') {
        hideEverything();
    }
    else  {
        hideEverything();
    }
});

$("#id_use_snapshot").click(function() {
    if ($("#id_use_snapshot").is(":checked")) {
        showSnapshotOptions();
    }
    else {
        hideSnapshotOptions();
    }
});

$("#id_is_windows").click(function() {
    if ($("#id_use_snapshot").is(":checked")) {
        showSnapshotOptions();
    }
    else {
        hideSnapshotOptions();
    }
});

$("#id_mode").change(function() {
    if ($("#id_action").val() == 'backup') {
        if ($("#id_mode").val() == 'fs') {
            hideEverything();
            showBackupOptions();
            showSnapshotOptions();
            $("#id_advanced_configuration").closest(".form-group").show();
        }
        else if ($("#id_mode").val() == 'mysql') {
            hideEverything();
            showBackupOptions();
            showSnapshotOptions();
            $("#id_mysql_conf").closest(".form-group").show();
            $("#id_sql_server_conf").closest(".form-group").hide();
            $("#id_advanced_configuration").closest(".form-group").show();
        }
        else if ($("#id_mode").val() == 'mssql') {
            hideEverything();
            showBackupOptions();
            showSnapshotOptions();
            $("#id_sql_server_conf").closest(".form-group").show();
            $("#id_mysql_conf").closest(".form-group").hide();
            $("#id_advanced_configuration").closest(".form-group").show();
        }
        else if ($("#id_mode").val() == 'cinder') {
            hideEverything();
            showCinderOptions();
            $("#id_cinder_vol_id").closest(".form-group").show().addClass("required");
            $("#id_advanced_configuration").closest(".form-group").show();
        }
        else if ($("#id_mode").val() == 'nova') {
            hideEverything();
            showNovaOptions();
            $("#id_nova_inst_id").closest(".form-group").show().addClass("required");
            $("#id_advanced_configuration").closest(".form-group").show();
        }
        else {

        }
    }
});

$("#id_upload").change(function() {
    if ($("#id_upload").is(":checked")) {
        $("#id_container").closest(".form-group").show().addClass("required");
    }
    else {
        $("#id_container").closest(".form-group").hide().removeClass("required");
    }
});

$("#id_no_incremental").click(function() {
    if ($("#id_no_incremental").is(":checked")) {
        hideIncrementalOptions();
    }
    else {
        showIncrementalOptions();
    }
});

$("#id_advanced_configuration").click(function() {
    if ($("#id_action").val() == 'backup') {
        if ($("#id_advanced_configuration").is(":checked")) {
            showAdvancedConfigurationOptions();
            $("#id_advanced_configuration").closest(".form-group").show();
        }
        else {
            hideAdvancedConfigurationOptions();
        }
    }
    else if ($("#id_action").val() == 'restore') {
        if ($("#id_advanced_configuration").is(":checked")) {
            showRestoreAdvancedConfigurationOptions();
            $("#id_advanced_configuration").closest(".form-group").show();
        }
        else {
            hideRestoreAdvancedConfigurationOptions();
        }
    }
});