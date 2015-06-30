class Validator:

    @staticmethod
    def validate(conf):
        if conf.no_incremental and (conf.max_level or conf.always_level):
            raise Exception(
                'no-incremental option is not compatible '
                'with backup level options')

        if conf.restore_abs_path and not conf.action == "restore":
            raise Exception('Restore abs path with {0} action'
                            .format(conf.action))
        options = conf.options
        """:type: freezer.utils.OpenstackOptions"""
        if (conf.storage == 'swift' or conf.backup_media != 'fs') and not (
                options.password and options.user_name and options.auth_url and
                options.tenant_id):
            raise Exception("Please set up in your env:"
                            "OS_USERNAME, OS_TENANT_NAME, OS_AUTH_URL,"
                            "OS_PASSWORD")
