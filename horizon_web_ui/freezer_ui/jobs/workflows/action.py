# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from django.utils.translation import ugettext_lazy as _
from horizon import workflows
from horizon import exceptions
from horizon import forms
import horizon_web_ui.freezer_ui.api.api as freezer_api


class ActionConfigurationAction(workflows.Action):
    action = forms.ChoiceField(
        help_text=_("Set the action to be taken"),
        required=True)

    mode = forms.ChoiceField(
        help_text=_("Choose what you want to backup"),
        required=False)

    original_name = forms.CharField(
        widget=forms.HiddenInput(),
        required=False)

    action_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=False)

    storage = forms.ChoiceField(
        help_text=_("Set storage backend for a backup"),
        required=True)

    backup_name = forms.CharField(
        label=_("Backup Name"),
        required=False)

    mysql_conf = forms.CharField(
        label=_("MySQL Configuration File"),
        help_text=_("Set the path where the MySQL configuration file "
                    "is on the file system "),
        required=False)

    sql_server_conf = forms.CharField(
        label=_("SQL Server Configuration File"),
        help_text=_("Set the path where the SQL Server configuration file"
                    " is on the file system"),
        required=False)

    path_to_backup = forms.CharField(
        label=_("Source File/Directory"),
        help_text=_("The file or directory you want to back up."),
        required=False)

    container = forms.CharField(
        label=_("Container Name or Path"),
        help_text=_("Swift container for swift backend or "
                    "path for ssh or local backend"),
        required=False)

    restore_abs_path = forms.CharField(
        label=_("Restore Absolute Path"),
        help_text=_("Set the absolute path where you"
                    " want your data restored."),
        required=False)

    restore_from_host = forms.CharField(
        label=_("Restore From Host"),
        help_text=_("Set the hostname used to identify the"
                    " data you want to restore from."
                    " If you want to restore data in the same"
                    " host where the backup was executed just"
                    " type from your shell: '$ hostname' and"
                    " the output is the value that needs to"
                    " be passed to this option. Mandatory"
                    " with Restore"),
        required=False)

    restore_from_date = forms.CharField(
        label=_("Restore From Date"),
        help_text=_("Set the absolute path where you want "
                    "your data restored.Please provide "
                    "datetime in format 'YYYY-MM-DDThh:mm:ss' "
                    "i.e. '1979-10-03T23:23:23'. Make sure the "
                    "'T' is between date and time"),
        required=False)

    cinder_vol_id = forms.CharField(
        label=_("Cinder Volume ID"),
        help_text=_("Id of cinder volume for backup"),
        required=False)

    nova_inst_id = forms.CharField(
        label=_("Nova Volume ID"),
        help_text=_("Id of nova instance for backup"),
        required=False)

    get_object = forms.CharField(
        label=_("Get A Single Object"),
        help_text=_("The Object name you want to download on "
                    "the local file system."),
        required=False)

    dst_file = forms.CharField(
        label=_("Destination File"),
        help_text=_("The file name used to save the object "
                    "on your local disk and upload file in swift."),
        required=False)

    remove_older_than = forms.CharField(
        label=_("Remove Older Than"),
        help_text=_("Checks in the specified container for"
                    " object older than the specified days."
                    "If i.e. 30 is specified, it will remove"
                    " the remote object older than 30 days."
                    " Default False (Disabled) The option "
                    "--remove-older-then is deprecated and "
                    "will be removed soon"),
        required=False)

    remove_from_date = forms.CharField(
        label=_("Remove From Date"),
        help_text=_("Checks the specified container and removes"
                    " objects older than the provided datetime"
                    " in the format YYYY-MM-DDThh:mm:ss "
                    "i.e. 1974-03-25T23:23:23. Make sure the "
                    "'T' is between date and time "),
        required=False)

    ssh_key = forms.CharField(
        label=_("SSH Private Key"),
        help_text=_("Path for ssh private key"),
        required=False)

    ssh_username = forms.CharField(
        label=_("SSH Username"),
        help_text=_("Path for ssh private key"),
        required=False)

    ssh_host = forms.CharField(
        label=_("SSH Host"),
        help_text=_("IP address or dns name of host to connect through ssh"),
        required=False)

    def clean(self):
        cleaned_data = super(ActionConfigurationAction, self).clean()

        if cleaned_data.get('action') == 'backup':
            self._check_container(cleaned_data)
            self._check_backup_name(cleaned_data)
            self._check_path_to_backup(cleaned_data)

        elif cleaned_data.get('action') == 'restore':
            self._check_container(cleaned_data)
            self._check_backup_name(cleaned_data)
            self._check_restore_abs_path(cleaned_data)

        return cleaned_data

    def _check_restore_abs_path(self, cleaned_data):
        if not cleaned_data.get('restore_abs_path'):
            msg = _("You must define a path to restore.")
            self._errors['restore_abs_path'] = self.error_class([msg])

    def _check_container(self, cleaned_data):
        if not cleaned_data.get('container'):
            msg = _("You must define a container.")
            self._errors['container'] = self.error_class([msg])

    def _check_backup_name(self, cleaned_data):
        if not cleaned_data.get('backup_name'):
            msg = _("You must define an backup name.")
            self._errors['backup_name'] = self.error_class([msg])

    def _check_path_to_backup(self, cleaned_data):
        if not cleaned_data.get('path_to_backup'):
            msg = _("You must define a path to backup.")
            self._errors['path_to_backup'] = self.error_class([msg])

    def populate_mode_choices(self, request, context):
        return [
            ('fs', _("File system")),
            ('mongo', _("MongoDB")),
            ('mysql', _("MySQL")),
            ('mssql', _("Microsoft SQL Server")),
            ('cinder', _("Cinder")),
            ('nova', _("Nova")),
        ]

    def populate_action_choices(self, request, context):
        return [
            ('', _("Select an action")),
            ('backup', _("Backup")),
            ('restore', _("Restore")),
            ('admin', _("Admin")),
        ]

    def populate_storage_choices(self, request, context):
        return [
            ('swift', _("Swift")),
            ('local', _("Local Path")),
            ('ssh', _("SSH")),
        ]

    def __init__(self, request, context, *args, **kwargs):
        self.request = request
        self.context = context
        super(ActionConfigurationAction, self).__init__(
            request, context, *args, **kwargs)

    class Meta(object):
        name = _("Action")
        help_text_template = "freezer_ui/jobs" \
                             "/_action.html"


class ActionConfiguration(workflows.Step):
    action_class = ActionConfigurationAction
    contributes = ('action',
                   'mode',
                   'original_name',
                   'backup_name',
                   'mysql_conf',
                   'sql_server_conf',
                   'path_to_backup',
                   'container',
                   'restore_abs_path',
                   'restore_from_host',
                   'restore_from_date',
                   'cinder_vol_id',
                   'nova_inst_id',
                   'get_object',
                   'dst_file',
                   'remove_older_than',
                   'remove_from_date',
                   'original_name',
                   'action_id')


class SnapshotConfigurationAction(workflows.Action):
    use_snapshot = forms.BooleanField(
        label=_("Snapshot"),
        help_text=_("Use a LVM or Shadow Copy snapshot "
                    "to have point in time consistent backups"),
        widget=forms.CheckboxInput(),
        initial=False,
        required=False)

    is_windows = forms.BooleanField(
        label=_("Job For Windows"),
        help_text=_("Is this job going to "
                    "execute on windows?"),
        widget=forms.CheckboxInput(),
        required=False)

    vssadmin = forms.BooleanField(
        label=_("VSSAdmin"),
        help_text=_("Create a backup using a snapshot on windows "
                    "using vssadmin. Options are: "
                    "True and False, default is True"),
        widget=forms.CheckboxInput(),
        initial=True,
        required=False)

    lvm_auto_snap = forms.CharField(
        label=_("LVM Auto Snapshot"),
        help_text=_("Automatically guess the volume group and "
                    "volume name for given PATH."),
        required=False)

    lvm_srcvol = forms.CharField(
        label=_("Set The Volume For Snapshot"),
        help_text=_("Set the lvm volume you want to take a "
                    "snapshot from. Default no volume"),
        required=False)

    lvm_snapname = forms.CharField(
        label=_("Set A Snapshot Name"),
        help_text=_("Set the lvm snapshot name to use. "
                    "If the snapshot name already exists, "
                    "the old one will be used a no new one "
                    "will be created. Default freezer_backup_snap."),
        required=False)

    lvm_snapsize = forms.CharField(
        label=_("Snapshot Size"),
        help_text=_("Set the lvm snapshot size when creating "
                    "a new snapshot. Please add G for Gigabytes "
                    "or M for Megabytes, i.e. 500M or 8G. Default 5G."),
        required=False)

    lvm_dirmount = forms.CharField(
        label=_("Snapshot Directory"),
        help_text=_("Set the directory you want to mount "
                    "the lvm snapshot to. Default not set"),
        required=False)

    lvm_volgroup = forms.CharField(
        label=_("Volume Group"),
        help_text=_("Specify the volume group of your logical volume."
                    "This is important to mount your snapshot volume."
                    "Default not set"),
        required=False)

    class Meta(object):
        name = _("Snapshot")
        help_text_template = "freezer_ui/jobs" \
                             "/_snapshot.html"


class SnapshotConfiguration(workflows.Step):
    action_class = SnapshotConfigurationAction
    contributes = ('use_snapshot',
                   'is_windows',
                   'vssadmin',
                   'lvm_auto_snap',
                   'lvm_srcvol',
                   'lvm_snapname',
                   'lvm_snapsize',
                   'lvm_dirmount',
                   'lvm_volgroup',)


class AdvancedConfigurationAction(workflows.Action):

    log_file = forms.CharField(
        label=_("Log File Path"),
        help_text=_("Set log file. By default logs to "
                    "/var/log/freezer.log If that file "
                    "is not writable, freezer tries to "
                    "log to ~/.freezer/freezer.log"),
        required=False)

    exclude = forms.CharField(
        label=_("Exclude Files"),
        help_text=_("Exclude files, given as a PATTERN.Ex:"
                    " '*.log, *.pyc' will exclude any "
                    "file with name ending with .log. "
                    "Default no exclude"),
        widget=forms.widgets.Textarea(),
        required=False)

    proxy = forms.CharField(
        label=_("Proxy URL"),
        help_text=_("Enforce proxy that alters system "
                    "HTTP_PROXY and HTTPS_PROXY"),
        widget=forms.URLInput(),
        required=False)

    os_auth_ver = forms.ChoiceField(
        label=_("OpenStack Authentication Version"),
        help_text=_("Swift auth version, could be 1, 2 or 3"),
        required=False)

    upload_limit = forms.IntegerField(
        label=_("Upload Limit"),
        help_text=_("Upload bandwidth limit in Bytes per sec."
                    " Can be invoked with dimensions "
                    "(10K, 120M, 10G)."),
        initial=-1,
        min_value=-1,
        required=False)

    download_limit = forms.IntegerField(
        label=_("Download Limit"),
        help_text=_("Download bandwidth limit in Bytes per sec. "
                    "Can be invoked with dimensions"
                    " (10K, 120M, 10G)."),
        initial=-1,
        min_value=-1,
        required=False)

    optimize = forms.ChoiceField(
        choices=[('speed', _("Speed (tar)")),
                 ('bandwidth', _("Bandwidth/Space (rsync)"))],
        help_text="",
        label=_('Optimize For...'),
        required=False)

    compression = forms.ChoiceField(
        choices=[('gzip', _("Minimum Compression (GZip/Zip/Zlib)"))],
        help_text="",
        label=_('Compression Level'),
        required=False)

    max_segment_size = forms.IntegerField(
        label=_("Maximum Segment Size"),
        help_text=_("Set the maximum file chunk size in bytes"
                    " to upload to swift."
                    " Default 67108864 bytes (64MB)"),
        initial=67108864,
        min_value=1,
        required=False)

    hostname = forms.CharField(
        label=_("Hostname"),
        help_text=_("Set hostname to execute actions. If you are "
                    "executing freezer from one host but you want"
                    " to delete objects belonging to another host "
                    "then you can set this option that hostname and "
                    "execute appropriate actions. Default current "
                    "node hostname."),
        required=False)

    encryption_password = forms.CharField(
        label=_("Encryption Key"),
        help_text=_("Set the path where the encryption key"
                    "is on the file system"),
        required=False)

    no_incremental = forms.BooleanField(
        label=_("No Incremental"),
        help_text=_("Disable incremental feature. By default"
                    " freezer build the meta data even for "
                    "level 0 backup. By setting this option "
                    "incremental meta data is not created at all."
                    " Default disabled"),
        widget=forms.CheckboxInput(),
        initial=True,
        required=False)

    max_level = forms.IntegerField(
        label=_("Max Level"),
        initial=0,
        min_value=0,
        help_text=_("Set the backup level used with tar to implement"
                    " incremental backup. If a level 1 is specified "
                    "but no level 0 is already available, a level 0"
                    " will be done and subsequently backs to level 1."
                    " Default 0 (No Incremental)"),
        required=False)

    always_level = forms.IntegerField(
        label=_("Always Level"),
        initial=0,
        min_value=0,
        help_text=_("Set backup maximum level used with tar to"
                    " implement incremental backup. If a level "
                    "3 is specified, the backup will be executed "
                    "from level 0 to level 3 and to that point "
                    "always a backup level 3 will be executed. "
                    "It will not restart from level 0. This option "
                    "has precedence over --max-backup-level. "
                    "Default False (Disabled)"),
        required=False)

    restart_always_level = forms.IntegerField(
        label=_("Restart Always Level"),
        initial=0,
        min_value=0,
        help_text=_("Restart the backup from level 0 after n days. "
                    "Valid only if --always-level option if set. "
                    "If --always-level is used together with "
                    "--remove-older-then, there might be the "
                    "chance where the initial level 0 will be "
                    "removed Default False (Disabled)"),
        required=False)

    insecure = forms.BooleanField(
        label=_("insecure"),
        help_text=_("Allow to access swift servers without"
                    " checking SSL certs."),
        widget=forms.CheckboxInput(),
        required=False)

    dereference_symlink = forms.BooleanField(
        label=_("Follow Symlinks"),
        help_text=_("Follow hard and soft links and archive "
                    "and dump the files they refer to. "
                    "Default False"),
        widget=forms.CheckboxInput(),
        required=False)

    dry_run = forms.BooleanField(
        label=_("Dry Run"),
        help_text=_("Do everything except writing or "
                    "removing objects"),
        widget=forms.CheckboxInput(),
        required=False)

    max_priority = forms.BooleanField(
        label=_("Max Priority"),
        help_text=_("Set the cpu process to the "
                    "highest priority (i.e. -20 "
                    "on Linux) and real-time for "
                    "I/O. The process priority "
                    "will be set only if nice and "
                    "ionice are installed Default "
                    "disabled. Use with caution."),
        widget=forms.CheckboxInput(),
        required=False)

    quiet = forms.BooleanField(
        label=_("Quiet"),
        help_text=_("Suppress error messages"),
        widget=forms.CheckboxInput(),
        required=False)

    def populate_os_auth_ver_choices(self, request, context):
        return [
            ('2', _("v2")),
            ('1', _("v1")),
            ('3', _("v3")),
        ]

    class Meta(object):
        name = _("Advanced")
        help_text_template = "freezer_ui/jobs" \
                             "/_advanced.html"


class AdvancedConfiguration(workflows.Step):
    action_class = AdvancedConfigurationAction
    contributes = ('log_file',
                   'exclude',
                   'proxy',
                   'os_auth_ver',
                   'upload_limit',
                   'download_limit',
                   'optimize',
                   'compression',
                   'max_segment_size',
                   'hostname',
                   'encryption_password',
                   'no_incremental',
                   'max_level',
                   'always_level',
                   'restart_always_level',
                   'insecure',
                   'dereference_symlink',
                   'dry_run',
                   'max_priority',
                   'quiet',)


class RulesConfigurationAction(workflows.Action):
    max_retries = forms.IntegerField(
        label=_("Max Retries"),
        initial=0,
        min_value=0,
        help_text=_("In case of error, set the amount"
                    " of retries for this job"),
        required=False)

    max_retries_interval = forms.IntegerField(
        label=_("Max Retries Interval"),
        initial=0,
        min_value=0,
        help_text=_("Set the interval between intervals "
                    "for retries in seconds"),
        required=False)

    mandatory = forms.BooleanField(
        label=_("Mandatory"),
        help_text=_("Set this job as mandatory"),
        widget=forms.CheckboxInput(),
        required=False)

    class Meta(object):
        name = _("Rules")


class RulesConfiguration(workflows.Step):
    action_class = RulesConfigurationAction
    contributes = ('max_retries',
                   'max_retries_interval',
                   'mandatory')


class ConfigureAction(workflows.Workflow):
    slug = "action"
    name = _("Action Configuration")
    finalize_button_name = _("Save")
    success_message = _('Action file saved correctly.')
    failure_message = _('Unable to save action file.')
    success_url = "horizon:freezer_ui:jobs:index"

    default_steps = (ActionConfiguration,
                     SnapshotConfiguration,
                     RulesConfiguration,
                     AdvancedConfiguration)

    def handle(self, request, context):
        try:
            if context['is_windows']:
                client_os = 'Windows'
            else:
                client_os = 'Linux'

            if context['use_snapshot'] and client_os == 'Windows':
                context['vssadmin'] = True
            else:
                context['vssadmin'] = False

            if context['action_id'] == '':
                return freezer_api.action_create(request, context)
            else:
                return freezer_api.action_update(request, context)
        except Exception:
            exceptions.handle(request)
            return False
