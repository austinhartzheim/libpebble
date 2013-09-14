import os, sh
import uuid
import string

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
        with open(os.path.join(project_root, "appinfo.json"), "w") as f:
            f.write(FILE_DUMMY_APPINFO.substitute(uuid=str(uuid.uuid4())))

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

FILE_DUMMY_APPINFO = string.Template("""{
  "uuid": "${uuid}",
  "shortName": "Template App",
  "longName": "Pebble Template App",
  "companyName": "Your Company",
  "versionCode": 1,
  "versionLabel": "1.0.0",
  "watchapp": {
    "watchface": false
  },
  "appKeys": {
    "dummy": 0
  },
  "resources": {
    "media": [
      {
        "type": "raw",
        "name": "DUMMY",
        "file": "appinfo.json"
      }
    ]
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

