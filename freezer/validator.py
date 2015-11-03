def validate(conf):
    if conf.no_incremental and (conf.max_level or conf.always_level):
        raise Exception(
            'no-incremental option is not compatible '
            'with backup level options')

    if conf.action == "restore" and not conf.restore_abs_path and \
            not conf.nova_inst_id and not conf.cinder_vol_id and \
            not conf.cindernative_vol_id:
        raise Exception("Please provide restore_abs_path")

    if conf.restore_abs_path and not conf.action == "restore":
        raise Exception('Restore abs path with {0} action'
                        .format(conf.action))

    if conf.storage == "ssh" and \
            not (conf.ssh_key and conf.ssh_username and conf.ssh_host):
        raise Exception("Please provide ssh_key, "
                        "ssh_username and ssh_host")
