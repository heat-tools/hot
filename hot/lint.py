import requests

RULES = [
    "TemplateLintRequiredSections",
    "TemplateLintOutputChecks",
    "TemplateLintParameterLabelCheck",
    "TemplateLintParameterDescriptionCheck",
    "TemplateLintParameterConstraintCheck",
    "TemplateLintParameterGroupLabelCheck",
    "MetadataRequiredSections",
    "MetadataReachImagesDefined",
    "MetadataReachImagesAvailable"
]


class TemplateLintRule(object):
    """Base class for template lint rules"""
    def __init__(self, template, metadata):
        self.template = template
        self.metadata = metadata
        self.custom_message = None
        self.name = "Unnamed Rule"
        self.description = "No rule description"
        self.set_name()

    def set_name(self):
        """Placeholder for derived class"""
        pass

    def passes_check(self):
        """Placeholder for derived class"""

    def __repr__(self):
        return "TemplateLintRule(name=%s, description=%s)" % (
            self.name, self.description)

    def message(self, message):
        """Set a custom message"""
        self.custom_message = "%s: %s. %s" % (self.name, self.description,
                                              message)

    def check(self):
        """Prints a rule message if the check fails"""
        if not self.passes_check():
            if self.custom_message:
                print(self.custom_message)
            else:
                print("%s: %s" % (self.name, self.description))


class TemplateLintRequiredSections(TemplateLintRule):
    """Require sections of a template"""
    def set_name(self):
        self.name = "LINT-001"
        self.description = "`heat_template_version`, `description`, "\
                           "`parameter_groups`, `parameters`, `resources`, "\
                           "and `outputs` sections are required."

    def passes_check(self):
        required_sections = ['heat_template_version', 'description',
                             'parameter_groups', 'parameters', 'resources',
                             'outputs']
        for section in required_sections:
            if section not in self.template:
                return False
        return True


class TemplateLintOutputChecks(TemplateLintRule):
    """Verify how all outputs are setup"""
    def set_name(self):
        self.name = "LINT-002"
        self.description = "All outputs should have a `description` and "\
                           "`value` defined ."

    def passes_check(self):
        required_keys = ['description', 'value']
        outputs = self.template['outputs']
        for output, values in outputs.items():
            for key in required_keys:
                if key not in values:
                    return False
        return True


class TemplateLintParameterLabelCheck(TemplateLintRule):
    """Verify that all parameters have a label"""
    def set_name(self):
        self.name = "LINT-003"
        self.description = "All parameters should have a defined `label`."

    def passes_check(self):
        parameters = self.template['parameters']
        for parameter, values in parameters.items():
            if 'label' not in values:
                return False
        return True


class TemplateLintParameterDescriptionCheck(TemplateLintRule):
    """Verify that all parameters have a description"""
    def set_name(self):
        self.name = "LINT-004"
        self.description = "All parameters should have a defined "\
                           "`description`."

    def passes_check(self):
        parameters = self.template['parameters']
        for parameter, values in parameters.items():
            if 'description' not in values:
                return False
        return True


class TemplateLintParameterConstraintCheck(TemplateLintRule):
    """Verify that all parameters have a constraint"""
    def set_name(self):
        self.name = "LINT-005"
        self.description = "All parameters should have defined "\
                           "`constraints`."

    def passes_check(self):
        parameters = self.template['parameters']
        for parameter, values in parameters.items():
            if 'constraints' not in values:
                return False
        return True


class TemplateLintParameterGroupLabelCheck(TemplateLintRule):
    """Verify that all parameter groups have a label"""
    def set_name(self):
        self.name = "LINT-006"
        self.description = "All parameters groups should have a `label`."

    def passes_check(self):
        parameter_groups = self.template['parameter_groups']
        for group in parameter_groups:
            if 'label' not in group:
                return False
        return True


class MetadataRequiredSections(TemplateLintRule):
    """Verify all required metadata sections are present"""
    def set_name(self):
        self.name = "LINT-007"
        self.description = "`schema-version`, `application-family`, "\
                           "`application-name`, `application-version`, "\
                           "`flavor`, `flavor-weight`, `reach-info`, "\
                           "`abstract`, and `instructions` sections are "\
                           "required in the metadata."

    def passes_check(self):
        required_sections = ['schema-version', 'application-family',
                             'application-name', 'application-version',
                             'flavor', 'flavor-weight', 'reach-info',
                             'abstract', 'instructions']
        for section in required_sections:
            if section not in self.metadata:
                return False
        return True


class MetadataReachImagesDefined(TemplateLintRule):
    """Verify that all reach images exist"""
    def set_name(self):
        self.name = "LINT-008"
        self.description = "`tattoo` and `icon-20x20` images should be "\
                           "defined."

    def passes_check(self):
        images = ['tattoo', 'icon-20x20']
        for image in images:
            if image not in self.metadata['reach-info']:
                return False
        return True


class MetadataReachImagesAvailable(TemplateLintRule):
    """Verify that all reach images defined are available"""
    def set_name(self):
        self.name = "LINT-009"
        self.description = "`tattoo` and `icon-20x20` images should be "\
                           "accessible."

    def passes_check(self):
        images = ['tattoo', 'icon-20x20']
        for image in images:
            if image in self.metadata['reach-info']:
                img = requests.get(self.metadata['reach-info'][image])
                if not img.ok:
                    return False
        return True
