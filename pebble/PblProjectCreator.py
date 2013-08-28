import os, sh
import uuid

from PblCommand import PblCommand

class PblProjectCreator(PblCommand):
    name = 'new-project'
    help = 'Create a new Pebble project'

    def configure_subparser(self, parser):
        parser.add_argument("name", help = "Name of the project you want to create")

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
        open(os.path.join(project_resources_src, "resource_map.json"), "w").write(FILE_DUMMY_RESOURCE_MAP)

        # Add wscript file
        open(os.path.join(project_root, "wscript"), "w").write(FILE_WSCRIPT)

        # Add .gitignore file
        open(os.path.join(project_root, ".gitignore"), "w").write(FILE_GITIGNORE)

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
  window_stack_push(window, true /* Animated */);

  window_set_click_config_provider(window, (ClickConfigProvider) config_provider);

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
  app_event_loop();
  handle_deinit();
}
"""
