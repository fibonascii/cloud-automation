import os
from jinja2 import Environment, FileSystemLoader


class TemplateHandler:

    def __init__(self, project_path, environment_name, data):
        self.data = data
        self.project_path = project_path
        self.environment_name = environment_name
        self.environment_path = os.path.join(self.project_path, 'config/{}'.format(self.environment_name))
        self.config_template_path = os.path.join(self.project_path, 'config_templates')
        self.j2_env = Environment(loader=FileSystemLoader(self.config_template_path), trim_blocks=True)

    def get_templates(self):
        """ Return a list of all templates"""

        template_list = []
        # Check there are files in the directory before iterating
        if os.listdir(self.config_template_path):
            for root, dirs, files in os.walk(self.config_template_path):
                for filename in files:
                    if '.j2' in filename:
                        template_list.append(filename)

        return template_list

    def render(self, template_name):
        """ Render a Template from Input Data"""
        template = self.j2_env.get_template(template_name)
        rendered = template.render(self.data)

        return rendered

    def generate_config_from_template(self, template_list):
        """ Iterate through list of Templates and Generate YAML Config files from Templates"""
        config_file_list = []
        for template in template_list:
            rendered = self.render(template)
            with open(os.path.join(self.environment_path, template.strip('.j2')), 'w') as config_file:
                config_file.write(rendered)
                config_file_list.append(config_file)

        return config_file_list

    def generate_templates(self):
        """Call other class methods to get a list of the templates and the generate the config
        files from the templates"""

        templates = self.get_templates()
        config_files = self.generate_config_from_template(templates)

        return config_files