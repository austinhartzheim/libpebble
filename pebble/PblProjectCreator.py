import os, sh
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

        project_resources_src = os.path.join(project_root, os.path.join("resources","src"))
        project_src = os.path.join(project_root, "src")

        # Create directories
        os.makedirs(project_root)
        os.makedirs(project_resources_src)
        os.makedirs(project_src)

        # Create main .c file
        self.generate_main_file(os.path.join(project_src, "%s.c" % (project_name)))

        # Add resource file
        with open(os.path.join(project_resources_src, "resource_map.json"), "w") as f:
            f.write(FILE_DUMMY_RESOURCE_MAP)

        # Add wscript file
        with open(os.path.join(project_root, "wscript"), "w") as f:
            f.write(FILE_WSCRIPT)

        # Add .gitignore file
        with open(os.path.join(project_root, ".gitignore"), "w") as f:
            f.write(FILE_GITIGNORE)

        if args.javascript:
            project_js_src = os.path.join(project_src, "js")
            os.makedirs(project_js_src)

            with open(os.path.join(project_js_src, "appinfo.json"), "w") as f:
                f.write(FILE_DUMMY_JAVASCRIPT_APPINFO)

            with open(os.path.join(project_js_src, "pebble-js-app.js"), "w") as f:
                f.write(FILE_DUMMY_JAVASCRIPT_SRC)


    def generate_uuid_as_array(self):
        """
        Returns a freshly generated UUID value in string form formatted as
        a C array for inclusion in a template's "#define MY_UUID {...}"
        macro.
        """
        return ", ".join(["0x%02X" % ord(b) for b in uuid.uuid4().bytes])


    def generate_main_file(self, destination_filepath):
        """
        Generates the main file *and* replaces a dummy UUID
        value in it with a freshly generated value.
        """

        # This is the dummy UUID value in the template file.
        UUID_VALUE_TO_REPLACE="/* GENERATE YOURSELF USING `uuidgen` */ 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF"

        open(destination_filepath, "w").write(FILE_DUMMY_MAIN.replace(UUID_VALUE_TO_REPLACE, self.generate_uuid_as_array(), 1))


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

# When an empty resource map is required this can be used but...
FILE_DEFAULT_RESOURCE_MAP = """
{"friendlyVersion": "VERSION", "versionDefName": "VERSION", "media": []}
"""

# ...for the moment we need to have one with a dummy entry due to
# a bug that causes a hang when there's an empty resource map.
FILE_DUMMY_RESOURCE_MAP = """
{"friendlyVersion": "VERSION",
 "versionDefName": "VERSION",
 "media": [
     {
      "type":"raw",
      "defName":"DUMMY",
      "file":"resource_map.json"
     }
    ]
}
"""

FILE_DUMMY_MAIN = """#include <pebble_os.h>
#include <pebble_app.h>
#include <pebble_fonts.h>


#define MY_UUID { /* GENERATE YOURSELF USING `uuidgen` */ 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF, 0xBE, 0xEF }
PBL_APP_INFO(MY_UUID,
             "Template App", "Your Company",
             1, 0, /* App version */
             DEFAULT_MENU_ICON,
             APP_INFO_STANDARD_APP);

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

FILE_DUMMY_JAVASCRIPT_APPINFO = """{
  "info": {
    "app_id": "com.getpebble.example",
    "app_uuid": "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF",
    "app_name": "Template Javascript App",
    "support_url": "http://www.yourwebsite.com",
    "version_code": 1,
    "version_label": "1.0.0",
    "app_key_type": "manual"
  },
  "app_keys": {
    "dummy": 0
  }
}
"""

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

    if not os.path.isdir('src') or not os.path.exists('resources/src/resource_map.json'):
        raise InvalidProjectException

    if os.path.islink('pebble_app.ld'):
        raise OutdatedProjectException

def requires_project_dir(func):
    def wrapper(self, args):
        check_project_directory()
        func(self, args)
    return wrapper

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
        if not os.path.islink(l):
            raise Exception("Don't know how to convert this project, %s is not a symlink" % l)
        os.unlink(l)

    os.remove('.gitignore')
    os.remove('.hgignore')

    with open("wscript", "w") as f:
        f.write(FILE_WSCRIPT)

    with open(".gitignore", "w") as f:
        f.write(FILE_GITIGNORE)

class PblProjectConverter(PblCommand):
    name = 'convert-project'
    help = """convert an existing Pebble project to the current SDK.

Note: This will only convert the project, you'll still have to update your source to match the new APIs."""

    def run(self, args):
        try:
            check_project_directory()
        except OutdatedProjectException:
            convert_project()
            print "Project successfully converted!"

        print "No conversion required"

