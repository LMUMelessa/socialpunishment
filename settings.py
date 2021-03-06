import os
from os import environ
import dj_database_url
#from boto.mturk import qualification
import otree.settings


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# the environment variable OTREE_PRODUCTION controls whether Django runs in
# DEBUG mode. If OTREE_PRODUCTION==1, then DEBUG=False
if environ.get('OTREE_PRODUCTION') not in {None, '', '0'}:
    DEBUG = False
else:
    DEBUG = True

#if you didnt set environment variable then set debug = False or True here
DEBUG = True

ADMIN_USERNAME = 'admin'

# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
ADMIN_PASSWORD = 'natcoop'

# don't share this with anybody.
SECRET_KEY = '(50kdv-2+)m*=(k_+zw2g93j!%*)2k*o3p07%eo5o6#7lfx%n#'

#note: when you deploy on heroku then this cannot be here
#environ['DATABASE_URL'] = 'postgres://postgres@localhost/django_db'

DATABASES = {
    'default': dj_database_url.config(
        # Rather than hardcoding the DB parameters here,
        # it's recommended to set the DATABASE_URL environment variable.
        # This will allow you to use SQLite locally, and postgres/mysql
        # on the server
        # Examples:
        # export DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/NAME
        # export DATABASE_URL=mysql://USER:PASSWORD@HOST:PORT/NAME

        # fall back to SQLite if the DATABASE_URL env var is missing
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}

# AUTH_LEVEL:
# If you are launching a study and want visitors to only be able to
# play your app if you provided them with a start link, set the
# environment variable OTREE_AUTH_LEVEL to STUDY.
# If you would like to put your site online in public demo mode where
# anybody can play a demo version of your game, set OTREE_AUTH_LEVEL
# to DEMO. This will allow people to play in demo mode, but not access
# the full admin interface.

AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL')
AUTH_LEVEL = 'STUDY'

# setting for integration with AWS Mturk
AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')


# e.g. EUR, CAD, GBP, CHF, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = True
POINTS_DECIMAL_PLACES = 2
REAL_WORLD_CURRENCY_DECIMAL_PLACES = 1


# e.g. en, de, fr, it, ja, zh-hans
# see: https://docs.djangoproject.com/en/1.9/topics/i18n/#term-language-code
LANGUAGE_CODE = 'de' # de for german

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree', 'django_extensions']
EXTENSION_APPS = ['otree_redwood','pg_vote_famfeud']


# SENTRY_DSN = ''

DEMO_PAGE_INTRO_TEXT = """
oTree games
"""

# from here on are qualifications requirements for workers
# see description for requirements on Amazon Mechanical Turk website:
# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html
# and also in docs for boto:
# https://boto.readthedocs.org/en/latest/ref/mturk.html?highlight=mturk#module-boto.mturk.qualification

mturk_hit_settings = {
    'keywords': ['easy', 'bonus', 'choice', 'study'],
    'title': 'Title for your experiment',
    'description': 'Description for your experiment',
    'frame_height': 500,
    'preview_template': 'global/MTurkPreview.html',
    'minutes_allotted_per_assignment': 60,
    'expiration_hours': 7*24,  # 7 days
    # 'grant_qualification_id': 'YOUR_QUALIFICATION_ID_HERE',# to prevent retakes
    # to use qualification requirements, you need to uncomment the 'qualification' import
    # at the top of this file.
    'qualification_requirements': [
        # qualification.LocaleRequirement("EqualTo", "US"),
        # qualification.PercentAssignmentsApprovedRequirement("GreaterThanOrEqualTo", 50),
        # qualification.NumberHitsApprovedRequirement("GreaterThanOrEqualTo", 5),
        # qualification.Requirement('YOUR_QUALIFICATION_ID_HERE', 'DoesNotExist')
    ]
}



ROOM_DEFAULTS = {}

ROOMS = [
    {
        'name': 'awi_lab',
        'display_name': 'AWI Experimentallabor',
        'participant_label_file':'participant_labels.txt'
     
    }]




# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 0.8,
    'participation_fee': 6.00,
    'doc': "",
    'mturk_hit_settings': mturk_hit_settings,
}


SESSION_CONFIGS = [


    #only Treatment App
{
        'name': 'pggonly',
        'display_name': 'Only PGG (only, Note:separate App)',
        'num_demo_participants': 5,
        'app_sequence': ['onlytreatment'],
        'valuation':'on', #on;off
        'treatment': 'onlytreatment' #don't change'
    },

    ## depreciated
    # {
    #     'name': 'only',
    #     'display_name': 'Only PGG (only)',
    #     'num_demo_participants': 5,
    #     'app_sequence': ['pg_vote_famfeud'],
    #     'treatment': 'only',  # only;nosanction;exclude;dislike;punish
    #     'valuation':'off' #always off because in this treatment there is no FF
    # },

{
        'name': 'nosanction',
        'display_name': 'PGG-GG (nosanction)',
        'num_demo_participants': 5,
        'app_sequence': ['pg_vote_famfeud'],
        'valuation':'on', #on;off
        'treatment': 'nosanction',# only;nosanction;exclude;dislike;punish
        'cost_for_vote': 0.0 #leave empty but key is needed
    },

    {
        'name': 'excludec05',
        'display_name': 'PGG-exclude-GG_c05 (exclude)',
        'num_demo_participants': 5,
        'app_sequence': ['pg_vote_famfeud'],
        'valuation': 'on',  # on;off
        'treatment': 'exclude',  # only;nosanction;exclude;dislike;punish
        'cost_for_vote': 0.5 #either 0.5 or 0.2 these two possibilities are hardcoded in Control Questions
    },


    {
        'name': 'excludec02',
        'display_name': 'PGG-exclude-GG_c02 (exclude)',
        'num_demo_participants': 5,
        'app_sequence': ['pg_vote_famfeud'],
        'valuation': 'on',  # on;off
        'treatment': 'exclude',  # only;nosanction;exclude;dislike;punish
        'cost_for_vote': 0.2 #either 0.5 or 0.2 these two possibilities are hardcoded in Control Questions
    },



    {
        'name': 'dislikec05',
        'display_name': 'PGG-dislike-GG_c05 (dislike)',
        'num_demo_participants': 5,
        'app_sequence': ['pg_vote_famfeud'],
        'valuation': 'on',  # on;off
        'treatment': 'dislike', # only;nosanction;exclude;dislike;punish
        'cost_for_vote': 0.5 #either 0.5 or 0.2 these two possibilities are hardcoded in Control Questions
    },

{
        'name': 'punishc05',
        'display_name': 'PGG-punish-GG_c05 (punish)',
        'num_demo_participants': 5,
        'app_sequence': ['pg_vote_famfeud'],
        'valuation': 'on',  # on;off
        'treatment': 'punish', # only;nosanction;exclude;dislike;punish
        'cost_for_vote': 0.5 #either 0.5 or 0.2 these two possibilities are hardcoded in Control Questions
    },

{
        'name': 'pgvoteff4',
        'display_name': 'Family Feud only',
        'num_demo_participants': 5,
        'app_sequence': ['pg_vote_famfeud'],
        'valuation':'on',
        'treatment': 'FF',# only;nosanction;exclude;dislike;punish
        'cost_for_vote': 0.0 #leave empty but key is needed
    },

]

###
# anything you put after the below line will override
# oTree's default settings. Use with caution.
otree.settings.augment_settings(globals())
