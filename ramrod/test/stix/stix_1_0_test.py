# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import unittest
from StringIO import StringIO

import ramrod
import ramrod.stix
import ramrod.utils as utils

UPDATER = ramrod.stix.STIX_1_0_Updater

class STIX_1_0_Test(unittest.TestCase):
    XML_VERSIONS = \
    """
    <stix:STIX_Package
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:stix="http://stix.mitre.org/stix-1"
        id="example:STIXPackage-33fe3b22-0201-47cf-85d0-97c02164528d"
        version="1.0">
    </stix:STIX_Package>
    """

    @classmethod
    def setUpClass(cls):
        cls._versions = StringIO(cls.XML_VERSIONS)

    def test_get_version(self):
        root = utils.get_etree_root(self._versions)
        version = UPDATER.get_version(root)
        self.assertEqual(version, UPDATER.VERSION)

    def test_update_version(self):
        valid_versions = ramrod.stix.STIX_VERSIONS
        idx = valid_versions.index
        version_to = valid_versions[idx(UPDATER.VERSION)+1:]

        for version in version_to:
            updated = ramrod.update(self._versions, to_=version)
            updated_root = updated.document.getroot()
            updated_version = UPDATER.get_version(updated_root)
            self.assertEqual(version, updated_version)

if __name__ == "__main__":
    unittest.main()