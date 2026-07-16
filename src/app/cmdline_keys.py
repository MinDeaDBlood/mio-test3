from __future__ import annotations

PROGRAM_DESCRIPTION = "app_cmdline_program_description"
SUBCOMMANDS_TITLE = "app_cmdline_subcommands_title"
SUBCOMMANDS_DESCRIPTION = "app_cmdline_subcommands_description"
UNPACK_COMMAND_HELP = "app_cmdline_unpack_command_help"
SET_COMMAND_HELP = "app_cmdline_set_command_help"
GET_COMMAND_HELP = "app_cmdline_get_command_help"
HELP_COMMAND_HELP = "app_cmdline_help_command_help"
LPMAKE_COMMAND_HELP = "app_cmdline_lpmake_command_help"
INPUT_PATH_MISSING_LOG_FORMAT = "app_cmdline_input_path_missing_log_format"
SET_TOO_MANY_ARGUMENTS_MESSAGE = "app_cmdline_set_too_many_arguments_message"
SET_CONFIG_LOG_FORMAT = "app_cmdline_set_config_log_format"
GET_TOO_MANY_ARGUMENTS_MESSAGE = "app_cmdline_get_too_many_arguments_message"
STDOUT_ORIGIN_MISSING_LOG_MESSAGE = "app_cmdline_stdout_origin_missing_log_message"
LPMAKE_WORK_DIRECTORY_HELP = "app_cmdline_lpmake_work_directory_help"
LPMAKE_SPARSE_HELP = "app_cmdline_lpmake_sparse_help"
LPMAKE_GROUP_NAME_HELP = "app_cmdline_lpmake_group_name_help"
LPMAKE_SIZE_HELP = "app_cmdline_lpmake_size_help"
LPMAKE_PARTITION_LIST_HELP = "app_cmdline_lpmake_partition_list_help"
LPMAKE_DELETE_SOURCE_HELP = "app_cmdline_lpmake_delete_source_help"
LPMAKE_PARTITION_TYPE_HELP = "app_cmdline_lpmake_partition_type_help"
LPMAKE_ATTRIBUTE_HELP = "app_cmdline_lpmake_attribute_help"
LPMAKE_PATH_MISSING_MESSAGE = "app_cmdline_lpmake_path_missing_message"

ALL_KEYS = (
    PROGRAM_DESCRIPTION,
    SUBCOMMANDS_TITLE,
    SUBCOMMANDS_DESCRIPTION,
    UNPACK_COMMAND_HELP,
    SET_COMMAND_HELP,
    GET_COMMAND_HELP,
    HELP_COMMAND_HELP,
    LPMAKE_COMMAND_HELP,
    INPUT_PATH_MISSING_LOG_FORMAT,
    SET_TOO_MANY_ARGUMENTS_MESSAGE,
    SET_CONFIG_LOG_FORMAT,
    GET_TOO_MANY_ARGUMENTS_MESSAGE,
    STDOUT_ORIGIN_MISSING_LOG_MESSAGE,
    LPMAKE_WORK_DIRECTORY_HELP,
    LPMAKE_SPARSE_HELP,
    LPMAKE_GROUP_NAME_HELP,
    LPMAKE_SIZE_HELP,
    LPMAKE_PARTITION_LIST_HELP,
    LPMAKE_DELETE_SOURCE_HELP,
    LPMAKE_PARTITION_TYPE_HELP,
    LPMAKE_ATTRIBUTE_HELP,
    LPMAKE_PATH_MISSING_MESSAGE,
)

__all__ = [name for name in globals() if name.isupper()]
