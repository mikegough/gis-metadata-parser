import six
import unittest

from os.path import os

from parserutils.collections import wrap_value
from parserutils.elements import element_exists, element_to_dict, element_to_string
from parserutils.elements import clear_element, get_element_text, get_elements, get_remote_element
from parserutils.elements import insert_element, remove_element, remove_element_attributes, set_element_attributes

from gis_metadata.arcgis_metadata_parser import ArcGISParser, ARCGIS_NODES, ARCGIS_ROOTS
from gis_metadata.fgdc_metadata_parser import FgdcParser, FGDC_ROOT
from gis_metadata.iso_metadata_parser import IsoParser, ISO_ROOTS, _iso_tag_formats
from gis_metadata.metadata_parser import MetadataParser, get_metadata_parser, get_parsed_content

from gis_metadata.exceptions import ConfigurationError, InvalidContent, NoContent, ValidationError
from gis_metadata.utils import format_xpaths, get_complex_definitions, get_default_for_complex, get_supported_props
from gis_metadata.utils import DATE_TYPE, DATE_VALUES
from gis_metadata.utils import DATE_TYPE_SINGLE, DATE_TYPE_RANGE, DATE_TYPE_MISSING, DATE_TYPE_MULTIPLE
from gis_metadata.utils import ATTRIBUTES, CONTACTS, DIGITAL_FORMS, PROCESS_STEPS
from gis_metadata.utils import BOUNDING_BOX, DATES, LARGER_WORKS, RASTER_INFO
from gis_metadata.utils import KEYWORDS_PLACE, KEYWORDS_THEME
from gis_metadata.utils import ParserProperty


iteritems = getattr(six, 'iteritems')
StringIO = getattr(six, 'StringIO')


TEST_TEMPLATE_VALUES = {
    'dist_contact_org': 'ORG',
    'dist_contact_person': 'PERSON',
    'dist_address_type': 'PHYSICAL ADDRESS',
    'dist_address': 'ADDRESS LOCATION',
    'dist_city': 'CITY',
    'dist_state': 'STATE',
    'dist_postal': '12345',
    'dist_country': 'USA',
    'dist_phone': '123-456-7890',
    'dist_email': 'EMAIL@DOMAIN.COM',
}

TEST_METADATA_VALUES = {
    'abstract': 'Test Abstract',
    'attribute_accuracy': 'Test Attribute Accuracy',
    'attributes': [{
        'definition': 'Attributes Definition 1',
        'label': 'Attributes Label 1',
        'aliases': 'Attributes Alias 1',
        'definition_source': 'Attributes Definition Source 1'
    }, {
        'definition': 'Attributes Definition 2',
        'label': 'Attributes Label 2',
        'aliases': 'Attributes Alias 2',
        'definition_source': 'Attributes Definition Source 2'
    }, {
        'definition': 'Attributes Definition 3',
        'label': 'Attributes Label 3',
        'aliases': 'Attributes Alias 3',
        'definition_source': 'Attributes Definition Source 3'
    }],
    'bounding_box': {
        'east': '179.99999999998656',
        'north': '87.81211601444309',
        'west': '-179.99999999998656',
        'south': '-86.78249642712764'
    },
    'contacts': [{
        'name': 'Contact Name 1', 'email': 'Contact Email 1',
        'position': 'Contact Position 1', 'organization': 'Contact Organization 1'
    }, {
        'name': 'Contact Name 2', 'email': 'Contact Email 2',
        'position': 'Contact Position 2', 'organization': 'Contact Organization 2'
    }],
    'dataset_completeness': 'Test Dataset Completeness',
    'data_credits': 'Test Data Credits',
    'dates': {'type': 'multiple', 'values': ['Multiple Date 1', 'Multiple Date 2', 'Multiple Date 3']},
    'digital_forms': [{
        'access_desc': 'Digital Form Access Description 1',
        'version': 'Digital Form Version 1',
        'specification': 'Digital Form Specification 1',
        'access_instrs': 'Digital Form Access Instructions 1',
        'name': 'Digital Form Name 1',
        'network_resource': 'Digital Form Resource 1',
        'content': 'Digital Form Content 1',
        'decompression': 'Digital Form Decompression 1'
    }, {
        'access_desc': 'Digital Form Access Description 2',
        'version': 'Digital Form Version 2',
        'specification': 'Digital Form Specification 2',
        'access_instrs': 'Digital Form Access Instructions 2',
        'name': 'Digital Form Name 2',
        'network_resource': 'Digital Form Resource 2',
        'content': 'Digital Form Content 2',
        'decompression': 'Digital Form Decompression 2'
    }],
    'dist_address': 'Test Distribution Address',
    'dist_address_type': 'Test Distribution Address Type',
    'dist_city': 'Test Distribution City',
    'dist_contact_org': 'Test Distribution Org',
    'dist_contact_person': 'Test Distribution Person',
    'dist_country': 'US',
    'dist_email': 'Test Distribution Email',
    'dist_liability': 'Test Distribution Liability',
    'dist_phone': 'Test Distribution Phone',
    'dist_postal': '12345',
    'dist_state': 'OR',
    'larger_works': {
        'publish_place': 'Larger Works Place',
        'publish_info': 'Larger Works Info',
        'other_citation': 'Larger Works Other Citation',
        'online_linkage': 'http://test.largerworks.online.linkage.com',
        'publish_date': 'Larger Works Date',
        'title': 'Larger Works Title',
        'edition': 'Larger Works Edition',
        'origin': ['Larger Works Originator']
    },
    'raster_info': {
        'dimensions': 'Test # Dimensions',
        'row_count': 'Test Row Count',
        'column_count': 'Test Column Count',
        'vertical_count': 'Test Vertical Count',
        'x_resolution': 'Test X Resolution',
        'y_resolution': 'Test Y Resolution',
    },
    'online_linkages': 'http://test.onlinelinkages.org',
    'originators': 'Test Originators',
    'other_citation_info': 'Test Other Citation Info',
    'place_keywords': ['Oregon', 'Washington'],
    'process_steps': [{
        'sources': ['Process Step Sources 1.1', 'Process Step Sources 1.2'],
        'description': 'Process Step Description 1',
        'date': 'Process Step Date 1'
    }, {
        'sources': [],
        'description': 'Process Step Description 2',
        'date': ''
    }, {
        'sources': [], 'description': '', 'date': 'Process Step Date 3'
    }, {
        'sources': ['Process Step Sources 4.1', 'Process Step Sources 4.2'],
        'description': 'Process Step Description 4',
        'date': ''
    }],
    'processing_fees': 'Test Processing Fees',
    'processing_instrs': 'Test Processing Instructions',
    'purpose': 'Test Purpose',
    'publish_date': 'Test Publish Date',
    'resource_desc': 'Test Resource Description',
    'supplementary_info': 'Test Supplementary Info',
    'tech_prerequisites': 'Test Technical Prerequisites',
    'thematic_keywords': ['Ecoregion', 'Risk', 'Threat', 'Habitat'],
    'title': 'Test Title',
    'use_constraints': 'Test Use Constraints'
}


class MetadataParserTestCase(unittest.TestCase):

    valid_complex_values = ('one', ['before', 'after'], ['first', 'next', 'last'])

    def setUp(self):
        sep = os.path.sep
        dir_name = os.path.dirname(os.path.abspath(__file__))

        self.data_dir = sep.join((dir_name, 'data'))
        self.arcgis_file = sep.join((self.data_dir, 'arcgis_metadata.xml'))
        self.fgdc_file = sep.join((self.data_dir, 'fgdc_metadata.xml'))
        self.iso_file = sep.join((self.data_dir, 'iso_metadata.xml'))

        # Initialize metadata files

        self.arcgis_metadata = open(self.arcgis_file)
        self.fgdc_metadata = open(self.fgdc_file)
        self.iso_metadata = open(self.iso_file)

        self.metadata_files = (self.arcgis_metadata, self.fgdc_metadata, self.iso_metadata)

        # Define test file paths

        self.test_arcgis_file_path = '/'.join((self.data_dir, 'test_arcgis.xml'))
        self.test_fgdc_file_path = '/'.join((self.data_dir, 'test_fgdc.xml'))
        self.test_iso_file_path = '/'.join((self.data_dir, 'test_iso.xml'))

        self.test_file_paths = (self.test_arcgis_file_path, self.test_fgdc_file_path, self.test_iso_file_path)

    def assert_equal_for(self, parser_type, prop, value, target):

        self.assertEqual(
            value, target,
            'Parser property "{0}.{1}" does not equal target:{2}'.format(
                parser_type, prop, '\n\tparsed: "{0}" ({1})\n\texpected: "{2}" ({3})'.format(
                    value, type(value).__name__, target, type(target).__name__
                )
            )
        )

    def assert_reparsed_complex_for(self, parser, prop, value, target):

        setattr(parser, prop, value)

        parser_type = type(parser)
        parser_name = parser_type.__name__
        reparsed = getattr(parser_type(parser.serialize()), prop)

        if prop in get_complex_definitions():
            target = get_default_for_complex(prop, target)

        if isinstance(reparsed, dict):
            # Reparsed is a dict: compare each value with corresponding in target
            for key, val in iteritems(reparsed):
                self.assert_equal_for(
                    parser_name, '{0}.{1}'.format(prop, key), val, target.get(key, u'')
                )

        elif len(reparsed) <= 1:
            # Reparsed is empty or a single-item list: do a single value comparison
            self.assert_equal_for(parser_name, prop, reparsed, target)

        else:
            # Reparsed is a multiple-item list: compare each value with corresponding in target
            for idx, value in enumerate(reparsed):
                if not isinstance(value, dict):
                    self.assert_equal_for(parser_name, '{0}[{1}]'.format(prop, idx), value, target[idx])
                else:
                    for key, val in iteritems(value):
                        self.assert_equal_for(
                            parser_name, '{0}.{1}'.format(prop, key), val, target[idx].get(key, u'')
                        )

    def assert_reparsed_simple_for(self, parser, props, value=None, target=None):

        use_props = isinstance(props, dict)

        for prop in props:
            if use_props:
                value = props[prop]
            setattr(parser, prop, value)

        parser_type = type(parser)
        parser_name = parser_type.__name__
        reparsed = parser_type(parser.serialize())

        for prop in props:
            if use_props:
                target = props[prop]
            self.assert_equal_for(parser_name, prop, getattr(reparsed, prop), target)

    def assert_parser_conversion(self, content_parser, target_parser, comparison_type=''):
        converted = content_parser.convert_to(target_parser)

        self.assert_valid_parser(content_parser)
        self.assert_valid_parser(target_parser)

        self.assertFalse(
            converted is target_parser,
            '{0} conversion is returning the original {0} instance'.format(type(converted).__name__)
        )

        for prop in get_supported_props():
            self.assertEqual(
                getattr(content_parser, prop), getattr(converted, prop),
                '{0} {1}conversion does not equal original {2} content for {3}'.format(
                    type(converted).__name__, comparison_type, type(content_parser).__name__, prop
                )
            )

    def assert_parsers_are_equal(self, parser_tgt, parser_val):
        parser_type = type(parser_tgt).__name__

        self.assert_valid_parser(parser_tgt)
        self.assert_valid_parser(parser_val)

        for prop in get_supported_props():
            self.assert_equal_for(parser_type, prop, getattr(parser_val, prop), getattr(parser_tgt, prop))

    def assert_parser_after_write(self, parser_type, in_file, out_file_path, use_template=False):

        parser = parser_type(in_file, out_file_path)

        complex_defs = get_complex_definitions()

        # Update each value and read the file in again
        for prop in get_supported_props():

            if prop in (ATTRIBUTES, CONTACTS, DIGITAL_FORMS, PROCESS_STEPS):
                value = [
                    {}.fromkeys(complex_defs[prop], 'test'),
                    {}.fromkeys(complex_defs[prop], prop)
                ]
            elif prop in (BOUNDING_BOX, LARGER_WORKS, RASTER_INFO):
                value = {}.fromkeys(complex_defs[prop], 'test ' + prop)
            elif prop == DATES:
                value = {DATE_TYPE: DATE_TYPE_RANGE, DATE_VALUES: ['test', prop]}
            elif prop in (KEYWORDS_PLACE, KEYWORDS_THEME):
                value = ['test', prop]
            else:
                value = 'test ' + prop

            if prop in get_complex_definitions():
                value = get_default_for_complex(prop, value)

            setattr(parser, prop, value)

        parser.write(use_template=use_template)

        with open(out_file_path) as out_file:
            self.assert_parsers_are_equal(parser, parser_type(out_file))

    def assert_valid_parser(self, parser):

        parser_type = type(parser.validate()).__name__

        self.assertIsNotNone(parser._xml_root, '{0} root not set'.format(parser_type))

        self.assertIsNotNone(parser._xml_tree)
        self.assertEqual(parser._xml_tree.getroot().tag, parser._xml_root)

    def assert_validates_for(self, parser, prop, invalid):

        valid = getattr(parser, prop)
        setattr(parser, prop, invalid)

        try:
            parser.validate()
        except Exception as e:
            # Not using self.assertRaises to customize the failure message
            self.assertEqual(type(e), ValidationError, (
                'Property "{0}.{1}" does not raise ParserError for value: "{2}" ({3})'.format(
                    type(parser).__name__, prop, invalid, type(invalid).__name__
                )
            ))
        finally:
            setattr(parser, prop, valid)  # Reset value for next test

    def tearDown(self):

        for metadata_file in self.metadata_files:
            metadata_file.close()

        for test_file_path in self.test_file_paths:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)


class MetadataParserTemplateTests(MetadataParserTestCase):

    def assert_template_after_write(self, parser_type, out_file_path):

        parser = parser_type(out_file_or_path=out_file_path)

        # Reverse each value and read the file in again
        for prop, val in iteritems(TEST_TEMPLATE_VALUES):
            setattr(parser, prop, val[::-1])

        parser.write()

        with open(out_file_path) as out_file:
            self.assert_parsers_are_equal(parser, parser_type(out_file))

    def assert_valid_template(self, parser, root):

        parser_type = type(parser.validate()).__name__

        self.assertIsNotNone(parser._xml_root, '{0} root not set'.format(parser_type))
        self.assertEqual(parser._xml_root, root)
        self.assertIsNotNone(parser._xml_tree)
        self.assertEqual(parser._xml_tree.getroot().tag, parser._xml_root)

        for prop, val in iteritems(TEST_TEMPLATE_VALUES):
            parsed_val = getattr(parser, prop)
            self.assertEqual(parsed_val, val, (
                '{0} property {1}, "{2}", does not equal "{3}"'.format(parser_type, prop, parsed_val, val)
            ))

    def test_arcgis_template_values(self):
        arcgis_template = ArcGISParser(**TEST_TEMPLATE_VALUES)

        self.assert_valid_template(arcgis_template, root='metadata')
        self.assert_reparsed_simple_for(arcgis_template, TEST_TEMPLATE_VALUES)

    def test_fgdc_template_values(self):
        fgdc_template = FgdcParser(**TEST_TEMPLATE_VALUES)

        self.assert_valid_template(fgdc_template, root='metadata')
        self.assert_reparsed_simple_for(fgdc_template, TEST_TEMPLATE_VALUES)

    def test_iso_template_values(self):
        iso_template = IsoParser(**TEST_TEMPLATE_VALUES)

        self.assert_valid_template(iso_template, root='MD_Metadata')
        self.assert_reparsed_simple_for(iso_template, TEST_TEMPLATE_VALUES)

    def test_template_conversion(self):
        arcgis_template = ArcGISParser()
        fgdc_template = FgdcParser()
        iso_template = IsoParser()

        self.assert_parser_conversion(arcgis_template, fgdc_template, 'template')
        self.assert_parser_conversion(arcgis_template, iso_template, 'template')

        self.assert_parser_conversion(fgdc_template, iso_template, 'template')
        self.assert_parser_conversion(fgdc_template, arcgis_template, 'template')

        self.assert_parser_conversion(iso_template, fgdc_template, 'template')
        self.assert_parser_conversion(iso_template, arcgis_template, 'template')

    def test_template_conversion_bad_roots(self):

        bad_root_format = 'Bad root test failed for {0} with {1}'

        for bad_root in (None, u'', StringIO(u''), {}, '<?xml version="1.0" encoding="UTF-8"?>\n'):
            with self.assertRaises(NoContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
                get_parsed_content(bad_root)
            with self.assertRaises(NoContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
                get_metadata_parser(bad_root)

            if bad_root is not None:
                with self.assertRaises(NoContent, msg=bad_root_format.format('ArcGISParser', bad_root)):
                    ArcGISParser(bad_root)
                with self.assertRaises(NoContent, msg=bad_root_format.format('FgdcParser', bad_root)):
                    FgdcParser(bad_root)
                with self.assertRaises(NoContent, msg=bad_root_format.format('IsoParser', bad_root)):
                    IsoParser(bad_root)

        for bad_root in (u'NOT XML', u'<badRoot/>', u'<badRoot>invalid</badRoot>'):
            with self.assertRaises(InvalidContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
                get_parsed_content(bad_root)
            with self.assertRaises(InvalidContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
                get_metadata_parser(bad_root)
            with self.assertRaises(InvalidContent, msg=bad_root_format.format('ArcGISParser', bad_root)):
                ArcGISParser(bad_root)
            with self.assertRaises(InvalidContent, msg=bad_root_format.format('FgdcParser', bad_root)):
                FgdcParser(bad_root)
            with self.assertRaises(InvalidContent, msg=bad_root_format.format('IsoParser', bad_root)):
                IsoParser(bad_root)

        with self.assertRaises(InvalidContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
            IsoParser(FGDC_ROOT.join(('<', '></', '>')))

        for iso_root in ISO_ROOTS:
            with self.assertRaises(InvalidContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
                ArcGISParser(iso_root.join(('<', '></', '>')))
            with self.assertRaises(InvalidContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
                FgdcParser(iso_root.join(('<', '></', '>')))

        for arcgis_root in ARCGIS_ROOTS:

            with self.assertRaises(InvalidContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
                IsoParser(arcgis_root.join(('<', '></', '>')))

            if arcgis_root != FGDC_ROOT:
                with self.assertRaises(InvalidContent, msg=bad_root_format.format('get_parsed_content', bad_root)):
                    FgdcParser(arcgis_root.join(('<', '></', '>')))

    def test_template_conversion_from_dict(self):

        for arcgis_root in ARCGIS_ROOTS:
            for arcgis_node in ARCGIS_NODES:

                data = {'name': arcgis_root, 'children': [{'name': arcgis_node}]}
                self.assert_parser_conversion(
                    FgdcParser(), get_metadata_parser(data), 'dict-based template'
                )
                self.assert_parser_conversion(
                    IsoParser(), get_metadata_parser(data), 'dict-based template'
                )

        self.assert_parser_conversion(
            ArcGISParser(), get_metadata_parser({'name': FGDC_ROOT}), 'dict-based template'
        )
        self.assert_parser_conversion(
            IsoParser(), get_metadata_parser({'name': FGDC_ROOT}), 'dict-based template'
        )

        for iso_root in ISO_ROOTS:
            self.assert_parser_conversion(
                ArcGISParser(), get_metadata_parser({'name': iso_root}), 'dict-based template'
            )
            self.assert_parser_conversion(
                FgdcParser(), get_metadata_parser({'name': iso_root}), 'dict-based template'
            )

    def test_template_conversion_from_str(self):

        for arcgis_root in ARCGIS_ROOTS:
            for arcgis_node in ARCGIS_NODES:

                data = arcgis_node.join(('<', '></', '>'))
                data = arcgis_root.join(('<', '>{0}</', '>')).format(data)

                self.assert_parser_conversion(
                    FgdcParser(), get_metadata_parser(data), 'dict-based template'
                )
                self.assert_parser_conversion(
                    IsoParser(), get_metadata_parser(data), 'dict-based template'
                )

        self.assert_parser_conversion(
            ArcGISParser(), get_metadata_parser(FGDC_ROOT.join(('<', '></', '>'))), 'str-based template'
        )
        self.assert_parser_conversion(
            IsoParser(), get_metadata_parser(FGDC_ROOT.join(('<', '></', '>'))), 'str-based template'
        )

        for iso_root in ISO_ROOTS:
            self.assert_parser_conversion(
                ArcGISParser(), get_metadata_parser(iso_root.join(('<', '></', '>'))), 'str-based template'
            )
            self.assert_parser_conversion(
                FgdcParser(), get_metadata_parser(iso_root.join(('<', '></', '>'))), 'str-based template'
            )

    def test_template_conversion_from_type(self):

        self.assert_parser_conversion(
            ArcGISParser(), get_metadata_parser(FgdcParser), 'type-based template'
        )
        self.assert_parser_conversion(
            ArcGISParser(), get_metadata_parser(IsoParser), 'type-based template'
        )

        self.assert_parser_conversion(
            IsoParser(), get_metadata_parser(ArcGISParser), 'type-based template'
        )
        self.assert_parser_conversion(
            IsoParser(), get_metadata_parser(FgdcParser), 'type-based template'
        )

        self.assert_parser_conversion(
            FgdcParser(), get_metadata_parser(ArcGISParser), 'type-based template'
        )
        self.assert_parser_conversion(
            FgdcParser(), get_metadata_parser(IsoParser), 'type-based template'
        )

    def test_write_template(self):

        self.assert_template_after_write(ArcGISParser, self.test_arcgis_file_path)
        self.assert_template_after_write(FgdcParser, self.test_fgdc_file_path)
        self.assert_template_after_write(IsoParser, self.test_iso_file_path)


class MetadataParserTests(MetadataParserTestCase):

    def test_custom_parser(self):
        """ Covers support for custom parsers """

        target_values = {
            'metadata_contacts': [{
                'name': 'Custom Contact Name', 'email': 'Custom Contact Email', 'phone': 'Custom Contact Phone',
                'position': 'Custom Contact Position', 'organization': 'Custom Contact Organization'
            }],
            'metadata_language': 'eng'
        }

        custom_parser = CustomIsoParser(self.iso_metadata)
        for prop in target_values:
            self.assertEqual(getattr(custom_parser, prop), target_values[prop], 'Custom parser values were not parsed')

        complex_val = {
            'name': 'Changed Contact Name', 'email': 'Changed Contact Email', 'phone': 'Changed Contact Phone',
            'position': 'Changed Contact Position', 'organization': 'Changed Contact Organization'
        }
        self.assert_reparsed_complex_for(custom_parser, 'metadata_contacts', complex_val, [complex_val])
        self.assert_reparsed_simple_for(custom_parser, ['metadata_language'], 'es', 'es')

        # Test conversion with custom props
        converted_parser = custom_parser.convert_to(CustomIsoParser)

        self.assert_parsers_are_equal(custom_parser, converted_parser)
        self.assertEqual(converted_parser.metadata_contacts, custom_parser.metadata_contacts)
        self.assertEqual(converted_parser.metadata_language, custom_parser.metadata_language)

        # Test conversion that must ignore custom props
        agis_parser = custom_parser.convert_to(ArcGISParser)
        fgdc_parser = custom_parser.convert_to(FgdcParser)
        self.assert_parsers_are_equal(agis_parser, fgdc_parser)

        # Test invalid custom complex structure value

        metadata_contacts = custom_parser.metadata_contacts
        custom_parser.metadata_contacts = u'None'

        with self.assertRaises(ValidationError):
            custom_parser.validate()

        custom_parser.metadata_contacts = metadata_contacts

        # Test invalid custom simple value

        metadata_language = custom_parser.metadata_language
        custom_parser.metadata_language = {}

        with self.assertRaises(ValidationError):
            custom_parser.validate()

        custom_parser.metadata_language = metadata_language

    def test_generic_parser(self):
        """ Covers code that enforces certain behaviors for custom parsers """

        parser = MetadataParser()
        prop_get = '{0}'.format
        prop_set = '{xpaths}'.format

        with self.assertRaises(ConfigurationError):
            # Un-callable property parser (no xpath)
            ParserProperty(None, None)

        with self.assertRaises(ConfigurationError):
            # Un-callable property parser (no xpath)
            ParserProperty(None, prop_set)

        with self.assertRaises(ConfigurationError):
            # Un-callable property updater
            ParserProperty(prop_get, None)

        parser_prop = ParserProperty(None, prop_set, 'path')
        with self.assertRaises(ConfigurationError):
            # Un-callable property parser with xpath
            parser_prop.get_prop('prop')

        parser_prop = ParserProperty(prop_get, prop_set, 'path')
        self.assertEqual(parser_prop.get_prop('prop'), 'prop')
        self.assertEqual(parser_prop.set_prop(), 'path')
        self.assertEqual(parser_prop.set_prop(xpaths='diff'), 'path')

        data_map_1 = parser._data_map
        parser._init_data_map()
        data_map_2 = parser._data_map

        self.assertIs(data_map_1, data_map_2, 'Data map was reinitialized after instantiation')

        with self.assertRaises(IOError):
            parser.write()

    def test_specific_parsers(self):
        """ Ensures code enforces certain behaviors for existing parsers """

        for parser_type in (ArcGISParser, FgdcParser, IsoParser):
            parser = parser_type()

            data_map_1 = parser._data_map
            parser._init_data_map()
            data_map_2 = parser._data_map

            self.assertIs(data_map_1, data_map_2, 'Data map was reinitialized after instantiation')

            with self.assertRaises(IOError):
                parser.write()

            with self.assertRaises(ValidationError):
                parser._data_map.clear()
                parser.validate()

    def test_arcgis_parser(self):
        """ Tests behavior unique to the FGDC parser """

        # Test dates structure defaults

        # Remove multiple dates to ensure range is queried
        arcgis_element = get_remote_element(self.arcgis_file)
        remove_element(arcgis_element, 'dataIdInfo/dataExt/tempEle/TempExtent/exTemp/TM_Instant', True)

        # Assert that the backup dates are read in successfully
        arcgis_parser = ArcGISParser(element_to_string(arcgis_element))
        self.assertEqual(arcgis_parser.dates, {'type': 'range', 'values': ['Date Range Start', 'Date Range End']})

        # Remove one of the date range values and assert that only the end date is read in as a single
        remove_element(arcgis_element, 'dataIdInfo/dataExt/tempEle/TempExtent/exTemp/TM_Period/tmBegin', True)
        arcgis_parser = ArcGISParser(element_to_string(arcgis_element))
        self.assertEqual(arcgis_parser.dates, {'type': 'single', 'values': ['Date Range End']})

        # Remove the last of the date range values and assert that no dates are read in
        remove_element(arcgis_element, 'dataIdInfo/dataExt/tempEle/TempExtent/exTemp/TM_Period', True)
        arcgis_parser = ArcGISParser(element_to_string(arcgis_element))
        self.assertEqual(arcgis_parser.dates, {})

        # Insert a single date value and assert that only it is read in

        single_path = 'dataIdInfo/dataExt/tempEle/TempExtent/exTemp/TM_Instant/tmPosition'
        single_text = 'Single Date'
        insert_element(arcgis_element, 0, single_path, single_text)

        arcgis_parser = ArcGISParser(element_to_string(arcgis_element))
        self.assertEqual(arcgis_parser.dates, {'type': 'single', 'values': [single_text]})

    def test_fgdc_parser(self):
        """ Tests behavior unique to the FGDC parser """

        # Test dates structure defaults

        # Remove multiple dates to ensure range is queried
        fgdc_element = get_remote_element(self.fgdc_file)
        remove_element(fgdc_element, 'idinfo/timeperd/timeinfo/mdattim', True)

        # Assert that the backup dates are read in successfully
        fgdc_parser = FgdcParser(element_to_string(fgdc_element))
        self.assertEqual(fgdc_parser.dates, {'type': 'range', 'values': ['Date Range Start', 'Date Range End']})

        # Test contact data structure defaults

        contacts_def = get_complex_definitions()[CONTACTS]

        # Remove the contact organization completely
        fgdc_element = get_remote_element(self.fgdc_file)
        for contact_element in get_elements(fgdc_element, 'idinfo/ptcontac'):
            if element_exists(contact_element, 'cntinfo/cntorgp'):
                clear_element(contact_element)

        # Assert that the contact organization has been read in
        fgdc_parser = FgdcParser(element_to_string(fgdc_element))
        for key in contacts_def:
            for contact in fgdc_parser.contacts:
                self.assertIsNotNone(contact[key], 'Failed to read contact.{0}'.format(key))

        # Remove the contact person completely
        fgdc_element = get_remote_element(self.fgdc_file)
        for contact_element in get_elements(fgdc_element, 'idinfo/ptcontac'):
            if element_exists(contact_element, 'cntinfo/cntperp'):
                clear_element(contact_element)

        # Assert that the contact organization has been read in
        fgdc_parser = FgdcParser(element_to_string(fgdc_element))
        for key in contacts_def:
            for contact in fgdc_parser.contacts:
                self.assertIsNotNone(contact[key], 'Failed to read updated contact.{0}'.format(key))

    def test_iso_parser(self):
        """ Tests behavior unique to the ISO parser """

        # Remove the attribute details href attribute
        iso_element = get_remote_element(self.iso_file)
        for citation_element in get_elements(iso_element, _iso_tag_formats['_attr_citation']):
            removed = remove_element_attributes(citation_element, 'href')

        # Assert that the href attribute was removed and a different one was read in
        iso_parser = IsoParser(element_to_string(iso_element))
        attribute_href = iso_parser._attr_details_file_url

        self.assertIsNotNone(removed, 'ISO file URL was not removed')
        self.assertIsNotNone(attribute_href, 'ISO href attribute was not read in')
        self.assertNotEqual(attribute_href, removed, 'ISO href attribute is the same as the one removed')

        # Remove the attribute details linkage attribute
        iso_element = get_remote_element(self.iso_file)
        for linkage_element in get_elements(iso_element, _iso_tag_formats['_attr_contact_url']):
            removed = get_element_text(linkage_element)
            clear_element(linkage_element)

        # Assert that the linkage URL was removed and a different one was read in
        iso_parser = IsoParser(element_to_string(iso_element))
        linkage_url = iso_parser._attr_details_file_url

        self.assertIsNotNone(removed, 'ISO linkage URL was not removed')
        self.assertIsNotNone(linkage_url, 'ISO linkage URL was not read in')
        self.assertNotEqual(linkage_url, removed, 'ISO file URL is the same as the one removed')

        # Change the href attribute so that it is invalid
        for citation_element in get_elements(iso_element, _iso_tag_formats['_attr_citation']):
            removed = set_element_attributes(citation_element, href='neither url nor file')

        # Assert that the href attribute was removed and a different one was read in
        iso_parser = IsoParser(element_to_string(iso_element))
        attributes = iso_parser.attributes
        self.assertIsNone(iso_parser._attr_details_file_url, 'Invalid URL stored with parser')
        self.assertEqual(
            attributes, TEST_METADATA_VALUES[ATTRIBUTES], 'Invalid parsed attributes: {0}'.format(attributes)
        )

    def test_parser_values(self):
        """ Tests that parsers are populated with the expected values """

        arcgis_element = get_remote_element(self.arcgis_file)
        arcgis_parser = ArcGISParser(element_to_string(arcgis_element))
        arcgis_new = ArcGISParser(**TEST_METADATA_VALUES)

        # Test that the two ArcGIS parsers have the same data given the same input file
        self.assert_parsers_are_equal(arcgis_parser, arcgis_new)

        fgdc_element = get_remote_element(self.fgdc_file)
        fgdc_parser = FgdcParser(element_to_string(fgdc_element))
        fgdc_new = FgdcParser(**TEST_METADATA_VALUES)

        # Test that the two FGDC parsers have the same data given the same input file
        self.assert_parsers_are_equal(fgdc_parser, fgdc_new)

        iso_element = get_remote_element(self.iso_file)
        remove_element(iso_element, _iso_tag_formats['_attr_citation'], True)
        iso_parser = IsoParser(element_to_string(iso_element))
        iso_new = IsoParser(**TEST_METADATA_VALUES)

        # Test that the two ISO parsers have the same data given the same input file
        self.assert_parsers_are_equal(iso_parser, iso_new)

        # Test that all distinct parsers have the same data given equivalent input files

        self.assert_parsers_are_equal(arcgis_parser, fgdc_parser)
        self.assert_parsers_are_equal(fgdc_parser, iso_parser)
        self.assert_parsers_are_equal(iso_parser, arcgis_parser)

        # Test that each parser's values correspond to the target values
        for parser in (arcgis_parser, fgdc_parser, iso_parser):
            parser_type = type(parser)

            for prop, target in TEST_METADATA_VALUES.items():
                self.assert_equal_for(parser_type, prop, getattr(parser, prop), target)

    def test_parser_conversion(self):
        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        self.assert_parser_conversion(arcgis_parser, fgdc_parser, 'file')
        self.assert_parser_conversion(arcgis_parser, iso_parser, 'file')

        self.assert_parser_conversion(fgdc_parser, arcgis_parser, 'file')
        self.assert_parser_conversion(fgdc_parser, iso_parser, 'file')

        self.assert_parser_conversion(iso_parser, arcgis_parser, 'file')
        self.assert_parser_conversion(iso_parser, fgdc_parser, 'file')

    def test_conversion_from_dict(self):
        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        self.assert_parser_conversion(
            arcgis_parser, get_metadata_parser(element_to_dict(fgdc_parser._xml_tree, recurse=True)), 'dict-based'
        )
        self.assert_parser_conversion(
            arcgis_parser, get_metadata_parser(element_to_dict(iso_parser._xml_tree, recurse=True)), 'dict-based'
        )

        self.assert_parser_conversion(
            fgdc_parser, get_metadata_parser(element_to_dict(arcgis_parser._xml_tree, recurse=True)), 'dict-based'
        )
        self.assert_parser_conversion(
            fgdc_parser, get_metadata_parser(element_to_dict(iso_parser._xml_tree, recurse=True)), 'dict-based'
        )

        self.assert_parser_conversion(
            iso_parser, get_metadata_parser(element_to_dict(arcgis_parser._xml_tree, recurse=True)), 'dict-based'
        )
        self.assert_parser_conversion(
            iso_parser, get_metadata_parser(element_to_dict(fgdc_parser._xml_tree, recurse=True)), 'dict-based'
        )

    def test_conversion_from_str(self):
        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        self.assert_parser_conversion(
            arcgis_parser, get_metadata_parser(fgdc_parser.serialize()), 'str-based'
        )
        self.assert_parser_conversion(
            arcgis_parser, get_metadata_parser(iso_parser.serialize()), 'str-based'
        )

        self.assert_parser_conversion(
            fgdc_parser, get_metadata_parser(arcgis_parser.serialize()), 'str-based'
        )
        self.assert_parser_conversion(
            fgdc_parser, get_metadata_parser(iso_parser.serialize()), 'str-based'
        )

        self.assert_parser_conversion(
            iso_parser, get_metadata_parser(arcgis_parser.serialize()), 'str-based'
        )
        self.assert_parser_conversion(
            iso_parser, get_metadata_parser(fgdc_parser.serialize()), 'str-based'
        )

    def test_reparse_complex_lists(self):
        complex_defs = get_complex_definitions()
        complex_lists = (ATTRIBUTES, CONTACTS, DIGITAL_FORMS)

        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        for parser in (arcgis_parser, fgdc_parser, iso_parser):

            # Test reparsed empty complex lists
            for prop in complex_lists:
                for empty in (None, [], [{}], [{}.fromkeys(complex_defs[prop], u'')]):
                    self.assert_reparsed_complex_for(parser, prop, empty, [])

            # Test reparsed valid complex lists (strings and lists for each property in each struct)
            for prop in complex_lists:
                complex_list = []

                for val in self.valid_complex_values:

                    # Test with single unwrapped value
                    next_complex = {}.fromkeys(complex_defs[prop], val)
                    self.assert_reparsed_complex_for(parser, prop, next_complex, wrap_value(next_complex))

                    # Test with accumulated list of values
                    complex_list.append({}.fromkeys(complex_defs[prop], val))
                    self.assert_reparsed_complex_for(parser, prop, complex_list, wrap_value(complex_list))

    def test_reparse_complex_structs(self):
        complex_defs = get_complex_definitions()
        complex_structs = (BOUNDING_BOX, LARGER_WORKS, RASTER_INFO)

        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        for parser in (arcgis_parser, fgdc_parser, iso_parser):

            # Test reparsed empty complex structures
            for prop in complex_structs:
                for empty in (None, {}, {}.fromkeys(complex_defs[prop], u'')):
                    self.assert_reparsed_complex_for(parser, prop, empty, {})

            # Test reparsed valid complex structures
            for prop in complex_structs:
                for val in self.valid_complex_values:
                    complex_struct = {}.fromkeys(complex_defs[prop], val)
                    self.assert_reparsed_complex_for(parser, prop, complex_struct, complex_struct)

    def test_reparse_dates(self):
        valid_values = (
            (DATE_TYPE_SINGLE, ['one']),
            (DATE_TYPE_RANGE, ['before', 'after']),
            (DATE_TYPE_MULTIPLE, ['first', 'next', 'last'])
        )

        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        for parser in (arcgis_parser, fgdc_parser, iso_parser):

            # Test reparsed empty dates
            for empty in (None, {}, {DATE_TYPE: u'', DATE_VALUES: []}):
                self.assert_reparsed_complex_for(parser, DATES, empty, {})

            # Test reparsed valid dates
            for val in valid_values:
                complex_struct = {DATE_TYPE: val[0], DATE_VALUES: val[1]}
                self.assert_reparsed_complex_for(
                    parser, DATES, complex_struct, complex_struct
                )

    def test_reparse_keywords(self):

        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        for parser in (arcgis_parser, fgdc_parser, iso_parser):

            # Test reparsed empty keywords
            for keywords in ('', u'', []):
                self.assert_reparsed_complex_for(parser, KEYWORDS_PLACE, keywords, [])
                self.assert_reparsed_complex_for(parser, KEYWORDS_THEME, keywords, [])

            # Test reparsed valid keywords
            for keywords in ('keyword', ['keyword', 'list']):
                self.assert_reparsed_complex_for(parser, KEYWORDS_PLACE, keywords, wrap_value(keywords))
                self.assert_reparsed_complex_for(parser, KEYWORDS_THEME, keywords, wrap_value(keywords))

    def test_reparse_process_steps(self):
        proc_step_def = get_complex_definitions()[PROCESS_STEPS]

        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        for parser in (arcgis_parser, fgdc_parser, iso_parser):

            # Test reparsed empty process steps
            for empty in (None, [], [{}], [{}.fromkeys(proc_step_def, u'')]):
                self.assert_reparsed_complex_for(parser, PROCESS_STEPS, empty, [])

            complex_list = []

            # Test reparsed valid process steps
            for val in self.valid_complex_values:
                complex_struct = {}.fromkeys(proc_step_def, val)

                # Process steps must have a single string value for all but sources
                complex_struct.update({
                    k: ', '.join(wrap_value(v)) for k, v in iteritems(complex_struct) if k != 'sources'
                })

                complex_list.append(complex_struct)

                self.assert_reparsed_complex_for(parser, PROCESS_STEPS, complex_list, complex_list)

    def test_reparse_simple_values(self):

        complex_props = set(get_complex_definitions().keys())
        required_props = set(get_supported_props())

        simple_props = required_props.difference(complex_props)
        simple_props = simple_props.difference({KEYWORDS_PLACE, KEYWORDS_THEME})

        simple_empty_vals = ('', u'', [])
        simple_valid_vals = (u'value', [u'item', u'list'])

        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        for parser in (arcgis_parser, fgdc_parser, iso_parser):

            # Test reparsed empty values
            for val in simple_empty_vals:
                self.assert_reparsed_simple_for(parser, simple_props, val, u'')

            # Test reparsed valid values
            for val in simple_valid_vals:
                self.assert_reparsed_simple_for(parser, simple_props, val, val)

    def test_validate_complex_lists(self):
        complex_props = (ATTRIBUTES, CONTACTS, DIGITAL_FORMS, PROCESS_STEPS)

        invalid_values = ('', u'', {'x': 'xxx'}, [{'x': 'xxx'}], set(), tuple())

        for parser in (ArcGISParser().validate(), FgdcParser().validate(), IsoParser().validate()):
            for prop in complex_props:
                for invalid in invalid_values:
                    self.assert_validates_for(parser, prop, invalid)

    def test_validate_complex_structs(self):
        complex_props = (BOUNDING_BOX, DATES, LARGER_WORKS, RASTER_INFO)

        invalid_values = ('', u'', {'x': 'xxx'}, list(), set(), tuple())

        for parser in (ArcGISParser().validate(), FgdcParser().validate(), IsoParser().validate()):
            for prop in complex_props:
                for invalid in invalid_values:
                    self.assert_validates_for(parser, prop, invalid)

    def test_validate_dates(self):
        invalid_values = (
            (DATE_TYPE_MISSING, ['present']),
            (DATE_TYPE_MULTIPLE, ['single']),
            (DATE_TYPE_MULTIPLE, ['first', 'last']),
            (DATE_TYPE_RANGE, []),
            (DATE_TYPE_RANGE, ['just one']),
            (DATE_TYPE_SINGLE, []),
            (DATE_TYPE_SINGLE, ['one', 'two']),
            ('unknown', ['unknown'])
        )

        arcgis_parser = ArcGISParser(self.arcgis_metadata)
        fgdc_parser = FgdcParser(self.fgdc_metadata)
        iso_parser = IsoParser(self.iso_metadata)

        for parser in (arcgis_parser, fgdc_parser, iso_parser):
            for val in invalid_values:
                self.assert_validates_for(parser, DATES, {DATE_TYPE: val[0], DATE_VALUES: val[1]})

    def test_validate_simple_values(self):
        complex_props = set(get_complex_definitions().keys())
        simple_props = set(get_supported_props()).difference(complex_props)

        invalid_values = (None, [None], dict(), [dict()], set(), [set()], tuple(), [tuple()])

        for parser in (ArcGISParser().validate(), FgdcParser().validate(), IsoParser().validate()):
            for prop in simple_props:
                for invalid in invalid_values:
                    self.assert_validates_for(parser, prop, invalid)

    def test_write_values(self):

        self.assert_parser_after_write(ArcGISParser, self.arcgis_metadata, self.test_arcgis_file_path)
        self.assert_parser_after_write(FgdcParser, self.fgdc_metadata, self.test_fgdc_file_path)
        self.assert_parser_after_write(IsoParser, self.iso_metadata, self.test_iso_file_path)

    def test_write_values_to_template(self):

        self.assert_parser_after_write(ArcGISParser, self.arcgis_metadata, self.test_arcgis_file_path, True)
        self.assert_parser_after_write(FgdcParser, self.fgdc_metadata, self.test_fgdc_file_path, True)
        self.assert_parser_after_write(IsoParser, self.iso_metadata, self.test_iso_file_path, True)


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

        # Set the root and add getter/setter (parser/updater) to the data map
        self._data_map['_{prop}_root'.format(prop=ct_prop)] = 'contact'
        self._data_map[ct_prop] = ParserProperty(self._parse_complex_list, self._update_complex_list)

        # And finally, let the parent validation logic know about the two new custom properties

        self._metadata_props.add(lang_prop)
        self._metadata_props.add(ct_prop)
