"""
Terminator plugin to open a file using a chosen editor.

Author: michele.silva@gmail.com
License: GPLv2
"""
import inspect, os, shlex, subprocess
from terminatorlib import plugin
from terminatorlib import config

AVAILABLE = ['EditorPlugin']
DEFAULT_COMMAND = '{filepath}'
DEFAULT_EDITOR = 'kate'
DEFAULT_REGEX = '[^ \\t\\n\\r\\f\\v:]+?\.(ini|conf|me|txt|xml|json)[ \\n:]([0-9]+)*'
REPLACE = {'\\t':'\t', '\\n':'\n', '\\r':'\r', '\\f':'\f', '\\v':'\v'}


class EditorPlugin(plugin.URLHandler):
    """ Process URLs returned by commands. """
    capabilities = ['url_handler']
    handler_name = 'editorurl'
    nameopen = 'Open File'
    namecopy = 'Copy Open Command'
    match = None

    def __init__(self):
        self.plugin_name = self.__class__.__name__
        self.current_path = None
        self.config = config.Config()
        self.check_config()
        self.match = self.config.plugin_get(self.plugin_name, 'match')
        for key,val in REPLACE.iteritems():
            self.match = self.match.replace(key, val)

    def check_config(self):
        updated = False
        config = self.config.plugin_get_config(self.plugin_name)
        if not config:
            config = {}
            updated = True
        if 'command' not in config:
            config['command'] = DEFAULT_COMMAND
            updated = True
        if 'editor' not in config:
            config['editor'] = DEFAULT_EDITOR
            updated = True            
        if 'match' not in config:
            config['match'] = DEFAULT_REGEX
            updated = True
        if updated:
            self.config.plugin_set_config(self.plugin_name, config)
            self.config.save()

    def get_cwd(self):
        """ Return current working directory. """
        # HACK: Because the current working directory is not available to plugins,
        # we need to use the inspect module to climb up the stack to the Terminal
        # object and call get_cwd() from there.
        for frameinfo in inspect.stack():
            frameobj = frameinfo[0].f_locals.get('self')
            if frameobj and frameobj.__class__.__name__ == 'Terminal':
                return frameobj.get_cwd()
        return None

    def open_url(self):
        """ Return True if we should open the file. """
        # HACK: Because the plugin doesn't tell us we should open or copy
        # the command, we need to climb the stack to see how we got here.
        return inspect.stack()[3][3] == 'open_url'

    def callback(self, strmatch):
        strmatch = strmatch.strip(':').strip()
        filepath = os.path.join(self.get_cwd(), strmatch.split(':')[0])
        #BUG si ls -l /etc/ suis encore dans home :( filepath pas bon !!
        
        lineno = strmatch.split(':')[1] if ':' in strmatch else '1'
        # Generate the openurl string
        command = self.config.plugin_get(self.plugin_name, 'editor') +' '+ self.config.plugin_get(self.plugin_name, 'command')
        command = command.replace('{filepath}', filepath)
        command = command.replace('{line}', lineno)
        if filepath.find("/home/")<0:
            command = 'kdesu ' + command
        # Check we are opening the file
        if self.open_url():
            if os.path.exists(filepath):
                subprocess.call(shlex.split(command))
            return '--version'
        return command
