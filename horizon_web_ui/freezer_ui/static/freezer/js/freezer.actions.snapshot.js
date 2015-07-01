function hideOptions() {
    // Snapshot specific controls
    $("#id_is_windows").closest(".form-group").hide();
    $("#id_lvm_auto_snap").closest(".form-group").hide();
    $("#id_lvm_srcvol").closest(".form-group").hide();
    $("#id_lvm_snapname").closest(".form-group").hide();
    $("#id_lvm_snapsize").closest(".form-group").hide();
    $("#id_lvm_dirmount").closest(".form-group").hide();
    $("#id_lvm_volgroup").closest(".form-group").hide();
    $("#id_vssadmin").closest(".form-group").hide();
}

function is_windows() {
   if ($("#id_is_windows").is(":checked")) {
       return true;
   }
}

function showWindowsSnapshotOptions() {
    $("#id_vssadmin").closest(".form-group").show();
}

function hideWindowsSnapshotOptions() {
    $("#id_vssadmin").closest(".form-group").hide();
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

function hideSnapshotOptions() {
    hideWindowsSnapshotOptions();
    hideLinuxSnapshotOptions();
    $("#id_is_windows").closest(".form-group").hide();
}

function showSnapshotOptions() {
    $("#id_is_windows").closest(".form-group").show();
    if (is_windows()) {
        hideLinuxSnapshotOptions();
        showWindowsSnapshotOptions();
    }
    else {
        hideWindowsSnapshotOptions();
        showLinuxSnapshotOptions();
    }
}

hideOptions();

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