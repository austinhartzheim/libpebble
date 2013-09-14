import json
import os
import re
import sh
import string
import uuid

from PblCommand import PblCommand

class PblProjectCreator(PblCommand):
    name = 'new-project'
    help = 'Create a new Pebble project'

    def configure_subparser(self, parser):
        parser.add_argument("name", help = "Name of the project you want to create")
        parser.add_argument("--javascript", action="store_true", help = "Generate javascript related files")

    def run(self, args):
        print "Creating new project {}".format(args.name)

        # User can give a path to a new project dir
        project_path = args.name
        project_name = os.path.split(project_path)[1]
        project_root = os.path.join(os.getcwd(), project_path)

        project_src = os.path.join(project_root, "src")

        # Create directories
        os.makedirs(project_root)
        os.makedirs(os.path.join(project_root, "resources"))
        os.makedirs(project_src)

        # Create main .c file
        with open(os.path.join(project_src, "%s.c" % (project_name)), "w") as f:
            f.write(FILE_DUMMY_MAIN)

        # Add wscript file
        with open(os.path.join(project_root, "wscript"), "w") as f:
            f.write(FILE_WSCRIPT)

        # Add appinfo.json file
        appinfo_dummy = DICT_DUMMY_APPINFO.copy()
        appinfo_dummy['uuid'] = str(uuid.uuid4())
        with open(os.path.join(project_root, "appinfo.json"), "w") as f:
            f.write(FILE_DUMMY_APPINFO.substitute(**appinfo_dummy))

        # Add .gitignore file
        with open(os.path.join(project_root, ".gitignore"), "w") as f:
            f.write(FILE_GITIGNORE)

        if args.javascript:
            project_js_src = os.path.join(project_src, "js")
            os.makedirs(project_js_src)

            with open(os.path.join(project_js_src, "pebble-js-app.js"), "w") as f:
                f.write(FILE_DUMMY_JAVASCRIPT_SRC)



FILE_GITIGNORE = """
# Ignore build generated files
build
"""

FILE_WSCRIPT = """
#
# This file is the default set of rules to compile a Pebble project.
#
# Feel free to customize this to your needs.
#

top = '.'
out = 'build'

def options(ctx):
  ctx.load('pebble_sdk')

def configure(ctx):
  ctx.load('pebble_sdk')

def build(ctx):
  ctx.load('pebble_sdk')
"""

FILE_DUMMY_MAIN = """#include <pebble_os.h>
#include <pebble_app.h>
#include <pebble_fonts.h>

static Window *window;
static TextLayer *text_layer;

void select_click_handler(ClickRecognizerRef recognizer, void *context) {
  text_layer_set_text(text_layer, "Select");
}

void up_click_handler(ClickRecognizerRef recognizer, void *context) {
  text_layer_set_text(text_layer, "Up");
}

void down_click_handler(ClickRecognizerRef recognizer, void *context) {
  text_layer_set_text(text_layer, "Down");
}

void config_provider(ClickConfig **config, Window *window) {
  config[BUTTON_ID_SELECT]->click.handler = select_click_handler;
  config[BUTTON_ID_UP]->click.handler = up_click_handler;
  config[BUTTON_ID_DOWN]->click.handler = down_click_handler;
}

void handle_init(void) {
  window = window_create();
  window_set_click_config_provider(window, (ClickConfigProvider) config_provider);
  window_stack_push(window, true /* Animated */);

  text_layer = text_layer_create(GRect(/* x: */ 0, /* y: */ 74,
                                       /* width: */ 144, /* height: */ 20));
  layer_add_child(window_get_root_layer(window), text_layer_get_layer(text_layer));

  text_layer_set_text(text_layer, "Press a button");
}

void handle_deinit(void) {
  text_layer_destroy(text_layer);
  window_destroy(window);
}

int main(void) {
  handle_init();

  APP_LOG(APP_LOG_LEVEL_DEBUG, "Done initializing, pushed window: %p", window);

  app_event_loop();
  handle_deinit();
}
"""

DICT_DUMMY_APPINFO = {
    'short_name': 'Template App',
    'long_name': 'Pebble Template App',
    'company_name': 'Your Company',
    'version_code': 1,
    'version_label': '1.0.0',
    'is_watchface': 'false',
    'app_keys': """{
    "dummy": 0
  }""",
    'resources_media': '[]'
}

FILE_DUMMY_APPINFO = string.Template("""{
  "uuid": "${uuid}",
  "shortName": "${short_name}",
  "longName": "${long_name}",
  "companyName": "${company_name}",
  "versionCode": ${version_code},
  "versionLabel": "${version_label}",
  "watchapp": {
    "watchface": ${is_watchface}
  },
  "appKeys": ${app_keys},
  "resources": {
    "media": ${resources_media}
  }
}
""")

FILE_DUMMY_JAVASCRIPT_SRC = """\
Pebble.showSimpleNotificationOnPebble("Hello world!", "Sent from your javascript application.")
"""

class InvalidProjectException(Exception):
    pass

class OutdatedProjectException(Exception):
    pass

def check_project_directory():
    """Check to see if the current directly matches what is created by PblProjectCreator.run.

    Raises an InvalidProjectException or an OutdatedProjectException if everything isn't quite right.
    """

    if not os.path.isdir('src') or not os.path.exists('wscript'):
        raise InvalidProjectException

    if os.path.islink('pebble_app.ld') or os.path.exists('resources/src/resource_map.json'):
        raise OutdatedProjectException

def requires_project_dir(func):
    def wrapper(self, args):
        check_project_directory()
        func(self, args)
    return wrapper

PBL_APP_INFO_PATTERN = ('PBL_APP_INFO(?:_SIMPLE)?\(\s*'
        + '\s*,\s*'.join(['([^,]+)'] * 4)
        + '(?:\s*,\s*' + '\s*,\s*'.join(['([^,]+)'] * 3) + ')'
        + '\s*\)'
        )

PBL_APP_INFO_FIELDS = [
        'uuid',
        'name',
        'company_name',
        'version_major',
        'version_minor',
        'menu_icon',
        'type'
        ]

C_SINGLELINE_COMMENT_PATTERN = '//.*'
C_MULTILINE_COMMENT_PATTERN = '/\*.*\*/'

C_MACRO_USAGE_PATTERN = '^[A-Za-z_]\w*$'
C_DEFINE_PATTERN = '#define\s+{}\s+\(*(.+)\)*\s*'
C_STRING_PATTERN = '^"(.*)"$'

C_UUID_BYTE_PATTERN = '0x([0-9A-Fa-f]{2})'
C_UUID_PATTERN = '^{\s*' + '\s*,\s*'.join([C_UUID_BYTE_PATTERN] * 16) + '\s*}$'

UUID_TEMPLATE = "{}{}{}{}-{}{}-{}{}-{}{}-{}{}{}{}{}{}"

def convert_c_uuid(c_uuid):
    c_uuid = c_uuid.lower()
    if re.match(C_UUID_PATTERN, c_uuid):
        return UUID_TEMPLATE.format(*re.findall(C_UUID_BYTE_PATTERN, c_uuid))
    else:
        return c_uuid

def convert_c_expr_dict(c_code, c_expr_dict):
    for k, v in c_expr_dict.iteritems():
        # Expand C macros
        if re.match(C_MACRO_USAGE_PATTERN, v):
            m = re.search(C_DEFINE_PATTERN.format(v), c_code)
            if m:
                v = m.groups()[0]

        # Format C strings
        m = re.match(C_STRING_PATTERN, v)
        if m:
            v = m.groups()[0].decode('string-escape')

        c_expr_dict[k] = v

    return c_expr_dict

def extract_c_appinfo(c_code, c_path):
    m = re.search(PBL_APP_INFO_PATTERN, c_code)
    if m:
        appinfo_c_def = dict(zip(PBL_APP_INFO_FIELDS, m.groups()))
    else:
        raise Exception("Could not find PBL_APP_INFO in {}".format(c_path))

    appinfo_c_def = convert_c_expr_dict(c_code, appinfo_c_def)

    version_major = int(appinfo_c_def['version_major'])
    version_minor = int(appinfo_c_def['version_minor'])

    appinfo_json_def = {
        'uuid': convert_c_uuid(appinfo_c_def['uuid']),
        'short_name': appinfo_c_def['name'],
        'long_name': appinfo_c_def['name'],
        'company_name': appinfo_c_def['company_name'],
        'version_code': version_major,
        'version_label': '{}.{}.0'.format(version_major, version_minor),
        'is_watchface': 'true' if appinfo_c_def['type'] == 'APP_INFO_WATCH_FACE' else 'false',
        'app_keys': '{}',
        'resources_media': '[]'
    }

    return appinfo_json_def

def read_c_code(c_path):
    with open(c_path, 'r') as f:
        c_code = f.read()

        c_code = re.sub(C_SINGLELINE_COMMENT_PATTERN, '', c_code)
        c_code = re.sub(C_MULTILINE_COMMENT_PATTERN, '', c_code)

        return c_code

def generate_appinfo_from_old_project():
    project_root = os.getcwd()
    project_name = os.path.basename(project_root)
    main_c_path = "src/{}.c".format(project_name)

    c_code = read_c_code(main_c_path)

    appinfo_json_def = extract_c_appinfo(c_code, main_c_path)

    with open(os.path.join(project_root, "appinfo.json"), "w") as f:
        f.write(FILE_DUMMY_APPINFO.substitute(**appinfo_json_def))

def convert_project():
    links_to_remove = [
            'include',
            'lib',
            'pebble_app.ld',
            'tools',
            'waf',
            'wscript'
            ]

    for l in links_to_remove:
        if os.path.islink(l):
            os.unlink(l)

    if os.path.exists('.gitignore'):
        os.remove('.gitignore')

    if os.path.exists('.hgignore'):
        os.remove('.hgignore')

    with open("wscript", "w") as f:
        f.write(FILE_WSCRIPT)

    with open(".gitignore", "w") as f:
        f.write(FILE_GITIGNORE)

    generate_appinfo_from_old_project()

class PblProjectConverter(PblCommand):
    name = 'convert-project'
    help = """convert an existing Pebble project to the current SDK.

Note: This will only convert the project, you'll still have to update your source to match the new APIs."""

    def run(self, args):
        try:
            check_project_directory()
            print "No conversion required"
        except OutdatedProjectException:
            convert_project()
            print "Project successfully converted!"


