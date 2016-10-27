# gis_metadata_parser
XML parsers for GIS metadata that are designed to read in, validate, update and output a core set of properties that have been mapped between the most common standards, currently:

* FGDC
* ISO-19139 (and ISO-19115)
* ArcGIS (tested with ArcGIS format 1.0).

[![Build Status](https://travis-ci.org/consbio/gis-metadata-parser.png?branch=master)](https://travis-ci.org/consbio/gis-metadata-parser) [![Coverage Status](https://coveralls.io/repos/github/consbio/gis-metadata-parser/badge.svg?branch=master)](https://coveralls.io/github/consbio/gis-metadata-parser?branch=master)

#Installation#
Install with `pip install gis-metadata-parser`.

#Usage#

Parsers can be instantiated from files, XML strings or URLs. They can be converted from one standard to another as well.
```python
from gis_metadata.arcgis_metadata_parser import ArcGISParser
from gis_metadata.fgdc_metadata_parser import FgdcParser
from gis_metadata.iso_metadata_parser import IsoParser
from gis_metadata.metadata_parser import get_metadata_parser

# From file objects
with open(r'/path/to/metadata.xml') as metadata:
    fgdc_from_file = FgdcParser(metadata)

with open(r'/path/to/metadata.xml') as metadata:
    iso_from_file = IsoParser(metadata)

# Detect standard based on root element, metadata
fgdc_from_string = get_metadata_parser(
    """
    <?xml version='1.0' encoding='UTF-8'?>
    <metadata>
        <idinfo>
        </idinfo>
    </metadata>
    """
)

# Detect ArcGIS standard based on root element and its nodes
iso_from_string = get_metadata_parser(
    """
    <?xml version='1.0' encoding='UTF-8'?>
    <metadata>
        <dataIdInfo/></dataIdInfo>
        <distInfo/></distInfo>
        <dqInfo/></dqInfo>
    </metadata>
    """
)

# Detect ISO standard based on root element, MD_Metadata or MI_Metadata
iso_from_string = get_metadata_parser(
    """
    <?xml version='1.0' encoding='UTF-8'?>
    <MD_Metadata>
        <identificationInfo>
        </identificationInfo>
    </MD_Metadata>
    """
)

# Convert from one standard to another
fgdc_converted = iso_from_file.convert_to(FgdcParser)
iso_converted = fgdc_from_file.convert_to(IsoParser)
arcgis_converted = iso_converted.convert_to(ArcGISParser)
```

Finally, the properties of the parser can be updated, validated, applied and output:
```python
with open(r'/path/to/metadata.xml') as metadata:
    fgdc_from_file = FgdcParser(metadata)

# Example simple properties
fgdc_from_file.title
fgdc_from_file.abstract
fgdc_from_file.place_keywords
fgdc_from_file.thematic_keywords

# :see: gis_metadata.utils.get_supported_props for list of all supported properties

# Complex properties
fgdc_from_file.attributes
fgdc_from_file.bounding_box
fgdc_from_file.contacts
fgdc_from_file.dates
fgdc_from_file.digital_forms
fgdc_from_file.larger_works
fgdc_from_file.process_steps

# :see: gis_metadata.utils.get_complex_definitions for structure of all complex properties

# Update properties
fgdc_from_file.title = 'New Title'
fgdc_from_file.dates = {'type': 'single' 'values': '1/1/2016'}

# Apply updates
fgdc_from_file.validate()                                      # Ensure updated properties are valid
fgdc_from_file.serialize()                                     # Output updated XML as a string
fgdc_from_file.write()                                         # Output updated XML to existing file
fgdc_from_file.write(out_file_or_path='/path/to/updated.xml')  # Output updated XML to new file
```

#Extending and Customizing#

##Tips##

There are a few unwritten (until now) rules about the way the metadata parsers are wired to work:

1. Properties are generally defined by XPATH in each `parser._data_map`
2. Simple parser properties accept only values of `string` and `list`'s of `string`'s
3. XPATH's configured in the data map support references to element attributes: `'path/to/element/@attr'`
4. Complex parser properties are defined by custom parser/updater functions instead of by XPATH
5. Complex parser properties accept values of type `dict` containing simple properties, or a list of said `dict`'s
6. Properties with leading underscores are parsed, but not validated or written out
7. Properties that "shadow" other properties but with a leading underscore serve as backup values
8. For backup properties, additional underscores indicate further backup options, i.e. `title`, `_title`, `__title`

Some examples of existing backup properties are as follows:
```python
# In the ArcGIS parser for distribution contact phone:

_agis_tag_formats = {
     ...
    'dist_phone': 'distInfo/distributor/distorCont/rpCntInfo/cntPhone/voiceNum',
    '_dist_phone': 'distInfo/distributor/distorCont/rpCntInfo/voiceNum',  # If not in cntPhone
    ...
}

# In the FGDC parser for sub-properties in the contacts definition:

_fgdc_definitions = get_complex_definitions()
_fgdc_definitions[CONTACTS].update({
    '_name': '{_name}',
    '_organization': '{_organization}'
})
...
class FgdcParser(MetadataParser):
    ...
    def _init_data_map(self):
        ...
        ct_format = _fgdc_tag_formats[CONTACTS]
        fgdc_data_structures[CONTACTS] = format_xpaths(
            ...
            name=ct_format.format(ct_path='cntperp/cntper'),
            _name=ct_format.format(ct_path='cntorgp/cntper'),  # If not in cntperp
            organization=ct_format.format(ct_path='cntperp/cntorg'),
            _organization=ct_format.format(ct_path='cntorgp/cntorg'),  # If not in cntperp
        )

# Also see the ISO parser for backup sub-properties in the attributes definition:

_iso_definitions = get_complex_definitions()
_iso_definitions[ATTRIBUTES].update({
    '_definition_source': '{_definition_src}',
    '__definition_source': '{__definition_src}',
    '___definition_source': '{___definition_src}'
})

```


##Examples##

Any of the supported parsers can be extended to include more of a standard's supported data. In this example we'll add two new properties to the `IsoParser`:

* `metadata_language`: a simple string field describing the language of the metadata file itself (not the dataset)
* `metadata_contacts`: a complex structure with contact info leveraging and enhancing the existing contact structure

This example will cover:

1. Adding a new simple property
2. Configuring a backup location for a property
3. Referencing an element attribute in an XPATH
4. Adding a new complex property
5. Customizing the complex property to include a new sub-property

Also, this example is specifically covered by unit tests.

```python
from gis_metadata.iso_metadata_parser import IsoParser
from gis_metadata.utils import CONTACTS, format_xpaths, get_complex_definitions, ParserProperty


class CustomIsoParser(IsoParser):

    def _init_data_map(self):
        super(CustomIsoParser, self)._init_data_map()

        # Basic property: text or list (with backup location referencing codeListValue attribute)

        lang_prop = 'metadata_language'
        self._data_map[lang_prop] = 'language/CharacterString'                    # Parse from here if present
        self._data_map['_' + lang_prop] = 'language/LanguageCode/@codeListValue'  # Otherwise, try from here

        # Complex structure (reuse of contacts structure plus phone)

        # Define some basic variables
        ct_prop = 'metadata_contacts'
        ct_xpath = 'contact/CI_ResponsibleParty/{ct_path}'
        ct_defintion = get_complex_definitions()[CONTACTS]
        ct_defintion['phone'] = '{phone}'

        # Reuse CONTACT structure to specify locations per prop (adapted only slightly from parent)
        self._data_structures[ct_prop] = format_xpaths(
            ct_defintion,
            name=ct_xpath.format(ct_path='individualName/CharacterString'),
            organization=ct_xpath.format(ct_path='organisationName/CharacterString'),
            position=ct_xpath.format(ct_path='positionName/CharacterString'),
            phone=ct_xpath.format(
                ct_path='contactInfo/CI_Contact/phone/CI_Telephone/voice/CharacterString'
            ),
            email=ct_xpath.format(
                ct_path='contactInfo/CI_Contact/address/CI_Address/electronicMailAddress/CharacterString'
            )
        )

        # Set the contact root to insert new elements at "contact" level given the defined path:
        #   'contact/CI_ResponsibleParty/...'
        # By default we would get multiple "CI_ResponsibleParty" elements under a single "contact"
        # This way we get multiple "contact" elements, each with its own single "CI_ResponsibleParty"
        self._data_map['_{prop}_root'.format(prop=ct_prop)] = 'contact'

        # Use the built-in support for parsing complex properties (or write your own a parser/updater)
        self._data_map[ct_prop] = ParserProperty(self._parse_complex_list, self._update_complex_list)

        # And finally, let the parent validation logic know about the two new custom properties

        self._metadata_props.add(lang_prop)
        self._metadata_props.add(ct_prop)


with open(r'/path/to/metadata.xml') as metadata:
    iso_from_file = CustomIsoParser(metadata)

iso_from_file.metadata_language
iso_from_file.metadata_contacts
```
