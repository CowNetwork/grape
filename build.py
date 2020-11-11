import configparser
import lxml.etree as etree
import os
import sys
import argparse


class Config:
    """Holds build information and dependency list."""

    def __init__(self, options, dependencies):
        self.options = options
        self.dependencies = dependencies

    def version(self):
        return self.options["version"]

    def group_id(self):
        return self.options["groupid"]

    def artifact_id(self):
        return self.options["artifactid"]

    def stage(self):
        return self.options["stage"]


class Dependency:
    """Holds information about a dependency to shade into the project."""

    def __init__(self, group_id, artifact_id, version):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

    def __str__(self):
        return f"{self.group_id}/{self.artifact_id}:{self.version}"

    def __iter__(self):
        return iter((self.group_id, self.artifact_id, self.version))


def create_dependency(group_id, artifact_id, version):
    """Creates an XML dependency element and its sub-elements

    Following structure:
        <dependency>
            <groupId>...</groupId>
            <artifactId>...</artifactId>
            <version>...</version>
        </dependency>

    :return: an XML element
    """
    dep_elem = etree.Element("dependency")

    etree.SubElement(dep_elem, "groupId").text = group_id
    etree.SubElement(dep_elem, "artifactId").text = artifact_id
    etree.SubElement(dep_elem, "version").text = version
    etree.SubElement(dep_elem, "scope").text = "compile"
    return dep_elem


def from_grape_file(filename, delimiter):
    """Reads all dependencies from given .grape file.

    :param filename: path and name of the file
    :param delimiter: string delimiting each dependency column
    :return: a config object
    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(filename)

    option_section = "Config"
    dependency_section = "Dependencies"

    options = {}
    for c in config.options(option_section):
        options[c] = config.get(option_section, c)

    dependencies = []
    for d in config.options(dependency_section):
        group_id, artifact_id, version = d.split(delimiter)
        dep = Dependency(group_id, artifact_id, version)

        dependencies.append(dep)
    return Config(options, dependencies)


def namespaced(key, url):
    """Simply returns the key with namespaced prefix"""
    return f"{'{' + url + '}'}{key}"


def set_xml(root: etree.Element, url: str, key: str, value: str):
    """Appends a new xml element or sets the current one to given value"""

    elem = root.find(namespaced(key, url))
    if elem == None:
        etree.SubElement(root, key).text = value
        return
    elem.text = value
    pass


# Commandline usage: ... [-t template] config
parser = argparse.ArgumentParser(description="Build configured dependencies into one project.")
parser.add_argument("config", nargs=1, type=str, help="path to .grape file")
parser.add_argument("-t", "--template", type=str, nargs="?", default="grape-plain", help="path to template folder")
args = parser.parse_args()

config_path = args.config
template_dir = args.template

# print(r"""         __
#     __ {_/
#     \_}\\ _
#        _\(_)_
#       (_)_)(_)_
#      (_)(_)_)(_)
#       (_)(_))_)
#        (_(_(_)
#         (_)_)
#          (_)
# """)

print("loading dependencies from config...")

config = None
try:
    config = from_grape_file(config_path, ";")
except FileNotFoundError:
    print(f"invalid config '{config_path}', has to be a valid .csv file with ';' delimiter")
    sys.exit(1)


# We have to specify a namespace, to be able to access
# elements in the tree
url = "http://maven.apache.org/POM/4.0.0"

# Using a custom parser instance, as whitespaces sometimes
# can corrupt the XML data.
print("parsing target pom.xml...")
root = etree.parse(f"{template_dir}/pom.xml", etree.XMLParser(remove_blank_text=True)).getroot()
for element in root.iter():
    element.tail = None

print("injecting dependencies into xml...")
dep_element = root.find(namespaced("dependencies", url))

for dep in config.dependencies:
    group_id, artifact_id, version = dep
    dep_element.append(create_dependency(group_id, artifact_id, version))

print("setting bundle values...")
set_xml(root, url, "groupId", config.group_id())
set_xml(root, url, "artifactId", config.artifact_id())
set_xml(root, url, "version", config.version())

# ===========================================================================

print("building project...")
with open(f"{template_dir}/pom-build.xml", "wb") as f:
    f.write(etree.tostring(root, pretty_print=True))

if config.stage() == "package":
    os.system(f"cd {template_dir} && mvn clean package -f pom-build.xml")
elif config.stage() == "deploy":
    os.system(f"cd {template_dir} && mvn clean deploy -f pom-build.xml")

print("Done.")
