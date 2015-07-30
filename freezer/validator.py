class Validator:

    @staticmethod
    def validate_env(options):
        """:type options: freezer.utils.OpenstackOptions"""
        if not (options.password and options.user_name and options.auth_url and
                options.tenant_name):
            raise Exception("Please set up in your env:"
                            "OS_USERNAME, OS_TENANT_NAME, OS_AUTH_URL,"
                            "OS_PASSWORD")

    @staticmethod
    def validate(conf):
        if conf.no_incremental and (conf.max_level or conf.always_level):
            raise Exception(
                'no-incremental option is not compatible '
                'with backup level options')

        if conf.action == "restore" and not conf.restore_abs_path:
            raise Exception("Please provide restore_abs_path")

        if conf.restore_abs_path and not conf.action == "restore":
            raise Exception('Restore abs path with {0} action'
                            .format(conf.action))
