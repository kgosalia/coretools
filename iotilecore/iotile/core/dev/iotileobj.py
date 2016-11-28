# This file is copyright Arch Systems, Inc.  
# Except as otherwise provided in the relevant LICENSE file, all rights are reserved.

from iotile.core.utilities.kvstore import KeyValueStore
from iotile.core.exceptions import *
import json
import os.path

class IOTile:
    """
    IOTile

    A python representation of an IOTile module allowing you to inspect the products 
    that its build produces and include it as a dependency in another build process. 
    """

    def __init__(self, folder):
        self.folder = folder
        self.filter_prods = False

        self._load_settings()


    def _load_settings(self):
        modfile = os.path.join(self.folder, 'module_settings.json')

        try:
            with open(modfile, "r") as f:
                settings = json.load(f)
        except IOError:
            raise EnvironmentError("Could not load module_settings.json file, make sure this directory is an IOTile component", path=self.folder)

        if 'module_name' in settings:
            modname = settings['module_name']
        if 'modules' not in settings or len(settings['modules']) == 0:
            raise DataError("No modules defined in module_settings.json file")
        elif len(settings['modules']) > 1:
            raise DataError("Mulitple modules defined in module_settings.json file", modules=settings['modules'].keys())
        else:
            #TODO: Remove this other option once all tiles have been converted to have their own name listed out
            modname = settings['modules'].keys()[0]
        
        if modname not in settings['modules']:
            raise DataError("Module name does not correspond with an entry in the modules directory", name=modname, modules=settings['modules'].keys())
        
        modsettings = settings['modules'][modname]

        self.settings = modsettings

        #Name is converted to all lowercase to canonicalize it
        prepend = ''
        if 'domain' in modsettings:
            prepend = modsettings['domain'].lower() + '/'

        key = prepend + modname.lower()

        #Copy over some key properties that we want easy access to
        self.name = key
        self.unique_id = key.replace('/', '_')
        self.short_name = modname

        self.full_name = "Undefined"
        if "full_name" in self.settings:
            self.full_name = self.settings['full_name']

        #FIXME: make sure this is a list
        self.authors = []
        if "authors" in self.settings:
            self.authors = self.settings['authors']

        #FIXME: Convert this to a SemanticVersion object
        self.version = "0.0.0"
        if "version" in self.settings:
            self.version = self.settings['version']

        #Load all of the build products that can be created by this IOTile
        self.products = modsettings.get('products', {})

        #If this is a release IOTile component, check for release information
        if 'release' in settings and settings['release'] is True:
            self.release = True

            if 'release_date' not in settings:
                raise DataError("Release mode IOTile component did not include a release date")

            import dateutil.parser
            self.release_date = dateutil.parser.parse(settings['release_date'])
            self.output_folder = self.folder
        else:
            self.release = False
            self.output_folder = os.path.join(self.folder, 'build', 'output')

            #If this tile is a development tile and it has been built at least one, add in a release date
            #from the last time it was built
            if os.path.exists(os.path.join(self.output_folder, 'module_settings.json')):
                release_settings = os.path.join(self.output_folder, 'module_settings.json')

                with open(release_settings, 'rb') as f:
                    release_dict = json.load(f)

                import dateutil.parser
                self.release_date = dateutil.parser.parse(release_dict['release_date'])
            else:
                self.release_date = None

        self.dependencies = []
        if 'depends' in self.settings:
            for dep, prods in self.settings['depends'].iteritems():
                name, sep, version = dep.partition(',')
                unique_id = name.lower().replace('/', '_')

                if version is '':
                    version = "^0.0.0"

                depdict = {
                    'name': name,
                    'unique_id': unique_id,
                    'required_version': version,
                    'products': prods
                }

                self.dependencies.append(depdict)

    def include_directories(self):
        """
        Return a list of all include directories that this IOTile could provide other tiles
        """

        #Only return include directories if we're returning everything or we were asked for it 
        if self.filter_prods and 'include_directories' not in self.desired_prods:
            return []

        if 'include_directories' in self.products:
            if self.release:
                joined_dirs = [os.path.join(self.output_folder, 'include', *x) for x in self.products['include_directories']]
            else:
                joined_dirs = [os.path.join(self.output_folder, *x) for x in self.products['include_directories']]
            return joined_dirs

        return []

    def libraries(self):
        """
        Return a list of all libraries produced by this IOTile that could be provided to other tiles
        """

        libs = [x[0] for x in self.products.iteritems() if x[1] == 'library']

        if self.filter_prods:
            libs = [x for x in libs if x in self.desired_prods]

        badlibs = filter(lambda x: not x.startswith('lib'), libs)
        if len(badlibs) > 0:
            raise DataError("A library product was listed in a module's products without the name starting with lib", bad_libraries=badlibs)

        #Remove the prepended lib from each library name
        return [x[3:] for x in libs]

    def type_packages(self):
        """
        Return a list of the python type packages that are provided by this tile
        """

        libs = [x[0] for x in self.products.iteritems() if x[1] == 'type_package']

        if self.filter_prods:
            libs = [x for x in libs if x in self.desired_prods]

        libs = [os.path.join(self.folder, x) for x in libs]

        return libs

    def linker_scripts(self):
        """
        Return a list of the linker scripts that are provided by this tile
        """

        ldscripts = [x[0] for x in self.products.iteritems() if x[1] == 'linker_script']

        if self.filter_prods:
            ldscripts = [x for x in ldscripts if x in self.desired_prods]

        # Now append the whole path so that the above comparison works based on the name of the product only
        ldscripts = [os.path.join(self.output_folder, 'linker', x) for x in ldscripts]
        return ldscripts

    def proxy_modules(self):
        """
        Return a list of the python proxy modules that are provided by this tile
        """

        libs = [x[0] for x in self.products.iteritems() if x[1] == 'proxy_module']

        if self.filter_prods:
            libs = [x for x in libs if x in self.desired_prods]

        libs = [os.path.join(self.folder, x) for x in libs]
        return libs

    def proxy_plugins(self):
        """
        Return a list of the python proxy plugins that are provided by this tile
        """

        libs = [x[0] for x in self.products.iteritems() if x[1] == 'proxy_plugin']

        if self.filter_prods:
            libs = [x for x in libs if x in self.desired_prods]

        libs = [os.path.join(self.folder, x) for x in libs]
        return libs

    def firmware_images(self):
        """
        Return a list of the python proxy plugins that are provided by this tile
        """

        libs = [x[0] for x in self.products.iteritems() if x[1] == 'firmware_image']

        if self.filter_prods:
            libs = [x for x in libs if x in self.desired_prods]

        libs = [os.path.join(self.output_folder, x) for x in libs]
        return libs

    def tilebus_definitions(self):
        """
        Return a list of all tilebus definitions that this IOTile could provide other tiles
        """

        #Only return include directories if we're returning everything or we were asked for it 
        if self.filter_prods and 'tilebus_definitions' not in self.desired_prods:
            return []

        if 'tilebus_definitions' in self.products:
            if self.release:
                #For released tiles, all of the tilebus definitions are copies to the same directory
                joined_dirs = [os.path.join(self.output_folder, 'tilebus', os.path.basename(os.path.join(*x))) for x in self.products['tilebus_definitions']]
            else:
                joined_dirs = [os.path.join(self.folder, 'firmware', 'src', *x) for x in self.products['tilebus_definitions']]
            return joined_dirs

        return []

    def library_directories(self):
        libs = self.libraries()

        if len(libs) > 0:
            return [os.path.join(self.output_folder)]

        return []

    def filter_products(self, desired_prods):
        """
        When asked for a product that this iotile produces, filter only those on this list
        """

        self.filter_prods = True
        self.desired_prods = set(desired_prods)

    def path(self):
        return self.folder