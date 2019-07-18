_ = lambda x: x

APP_DOMAIN = 'helian'

HELIAN_MAJOR_VERSION = 3
HELIAN_MINOR_VERSION = 0
HELIAN_VERSION_STR = 'v{major}.{minor}'.format(major=HELIAN_MAJOR_VERSION,
                                               minor=HELIAN_MINOR_VERSION)
HELIAN_NAME = _('Helianthus')
HELIAN_PRODUCT_NAME = '{name} {version}'
HELIAN_PRESENCE = _('Type {prefix}help for a list of commands.')

EMOJI_STAR = '\u2605'
EMOJI_UP = '\u2B06'
EMOJI_DOWN = '\u2B07'
EMOJI_LEFT = '\u2B05'
EMOJI_RIGHT = '\u27A1'

CORE_MISSING_PERMISSION_STR = _('You do not have the requisite permissions to run this command.')
CORE_COMMAND_NOT_FOUND_STR = _('Please enter a valid command.')
CORE_MISSING_REQUIRED_ARGUMENT_STR = _('You are missing a required argument `{parameter}`')
CORE_BAD_ARGUMENT_STR = _('Please enter an argument with a correct type.')

DB_TDOLL_ALIAS_STR = '%{alias}%'
DB_TDOLL_TIME_QUERY = 'SELECT * FROM doll_info WHERE time=?'
DB_TDOLL_NAME_QUERY = 'SELECT * FROM doll_info WHERE alias LIKE ?'
DB_TDOLL_RANDOM_QUERY = 'SELECT * FROM doll_info\nORDER BY RANDOM()\nLIMIT 1'
DB_EQUIPMENT_TIME_QUERY = 'SELECT * FROM equip_info WHERE time=?'

TIME_FORMAT_ERROR_STR = _('Please enter a time in a correct format (%H:%M or %H%M)')

INFO_NAME_LBL = _('Name')
INFO_TYPE_LBL = _('Type')
INFO_PRODUCTION_TIME_LBL = _('Production Time')
INFO_RARITY_LBL = _('Rarity')
INFO_ID_LBL = _('ID')
INFO_BUFF_LBL = _('Tile Coverage')
INFO_BUFF_STR = '{tiles}\n{description}'
INFO_SKILL_LBL = _('Skill')
INFO_SKILLS_LBL = _('Skills')
INFO_ARTIST_LBL = _('Artist')
INFO_CV_LBL = _('CV')
INFO_SKILL_STR = '**{name}**\n{description}'
INFO_STATS_LBL = _('Stats')

STATS_DEVELOPER_LBL = _('Developer')
STATS_DEVELOPER_ID_LBL = _('Developer ID')
STATS_BOT_ID_LBL = _('Helian\'s ID')
STATS_MEMORY_USAGE_LBL = _('Memory Usage')
STATS_MEMORY_USAGE_STR = _('{memory:.2f} MB')
STATS_PRESENCE_LBL = _('Presence')
STATS_PRESENCE_STR = _('Servers: {n_servers}\nText Channels: {n_text}\nVoice Channels: {n_voice}')
STATS_LANGUAGE_LBL = _('Server Language')
STATS_INVITE_LBL = _('Invite')
STATS_INVITE_URL_STR = 'https://discordapp.com/oauth2/authorize?client_id={id}&scope=bot&permissions=66186303'

CMD_HELP_HELP_STR = _('Have Helian get you some help.')
CMD_HELP_COMMAND_NOT_FOUND_STR = _('That command does not exist.')
CMD_HELP_COMMAND_STR = _('```\nUSAGE\n-----\n{usage}\n\nHELP\n----\n{help}\n\nPARAMETERS\n----------\n{params}```')

PAGINATOR_PAGE_COUNTER_STR = _('Page {current} of {max}')
PAGINATOR_SUBPAGE_COUNTER_STR = _('Subpage {current} of {max}')
PAGINATOR_FOOTER_STR = '{page} {sub_page}'

CMD_RELOAD_HELP_STR = _('Have Helian reload her databases.')
CMD_RELOAD_BEGIN_STR = _('Beginning reload...')
CMD_RELOAD_EXTENSION_RELOAD_STR = _('Reloaded extension {extension}.')
CMD_RELOAD_SETTINGS_DUMP_STR = _('Dumped server settings.')
CMD_RELOAD_COMPLETE_STR = _('Reload complete. Elapsed time: {time:.2f} seconds.')

CMD_SETLANG_HELP_STR = _('Have Helian set your server\'s global language.')
CMD_SETLANG_UNKNOWN_LANGUAGE_STR = _('You have entered an unsupported or unknown language. Only following locales are '
                                     'supported: {locales}')
CMD_SETLANG_SUCCESS_STR = _('This server\'s language has been set to: {language}.')

CMD_SETCHLANG_HELP_STR = _('Have Helian set a channel\'s language.')
CMD_SETCHLANG_UNKNOWN_LANGUAGE_STR = CMD_SETLANG_UNKNOWN_LANGUAGE_STR
CMD_SETCHLANG_SUCCESS_STR = _('This channel\'s language has been set to: {language}')

CMD_DELCHLANG_HELP_STR = _('Have Helian unset a channel\'s language.')
CMD_DELCHLANG_LANG_UNASSIGNED_STR = _('This channel does not have an assigned language.')
CMD_DELCHLANG_SUCCESS_STR = _('This channel\'s language has been successfully deleted.')

CMD_IDW_HELP_STR = _('Have Helian IDW someone.')
CMD_IDW_MENTION_NOT_IN_VOICE_STR = _('Please mention a member currently in voice.')

CMD_CHOOSE_HELP_STR = _('Have Helian choose something for you.')
CMD_CHOOSE_EMPTY_INPUT_STR = _('Please supply a whitespace-separated list.')

CMD_AVATAR_HELP_STR = _('Have Helian retrieve a user\'s avatar.')

CMD_SAY_HELP_STR = _('Have Helian say something.')

CMD_RANDOM_HELP_STR = _('Have Helian select a random T-Doll for you.')

CMD_DINFO_HELP_STR = _('Have Helian lookup T-Doll information by name.')
CMD_DINFO_DOLL_NOT_FOUND_STR = _('There are no T-Dolls under this alias.')

CMD_EXP_HELP_STR = _('Have Helian calculate the number of combat reports required for leveling T-Dolls.\n\n'
                     'Pass in "yes" or "no" or any amalgamation or abbreviation of those two for the "oath" parameter.')
CMD_EXP_INVALID_START_LEVEL_STR = _('Please enter a valid starting level between 1 and 120.')
CMD_EXP_INVALID_TARGET_LEVEL_STR = _('Please enter a valid target level between 1 and 120.')
CMD_EXP_TARGET_LESS_THAN_START_STR = _('Please enter a target level greater than {level}.')
CMD_EXP_REPORT_UNNCESSARY_STR = _('You do not need any combat reports.')
CMD_EXP_INVALID_EXP_STR = _('Please enter a valid amount of EXP.')
CMD_EXP_OUTPUT_STR = _('At **level {start}@({exp} EXP)**, to reach **level {target}** you will need **{reports}** '
                       'combat reports to cover {exp_difference} EXP.')

CMD_EQUIP_HELP_STR = _('Have Helian retrieve equipment with the given production time.\n\n'
                       'Enter a time in either the %H:%M or %H%M format, where %H is an optionally 0-padded two-digit '
                       'hour and %M is an optionally 0-padded two-digit minute.\n\n'
                       'Examples: 12:34, 1:2 (01:02), 12:3 (12:03), 12 (00:12), 123 (01:23)')
CMD_EQUIP_EQUIP_NOT_FOUND_STR = _('There are no pieces of equipment with the '
                                  'selected production time.')

CMD_DOLL_HELP_STR = _('Have Helian retrieve T-Dolls with the given production time.\n\n'
                      'Enter a time in either the %H:%M or %H%M format, where %H is an optionally 0-padded two-digit '
                      'hour and %M is an optionally 0-padded two digit minute.\n\n'
                      'Examples: 12:34, 1:2 (01:02), 12:3 (12:03), 12 (00:12), 123 (01:23)')
CMD_DOLL_DOLL_NOT_FOUND_STR = _('There are no T-Dolls with the selected '
                                'production time.')

CMD_STATS_HELP_STR = _('Get Helian\'s performance statistics.')


def setup(*args) -> None:
    del args
    print(f'Loaded {__file__}')
