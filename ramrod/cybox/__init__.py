from lxml import etree
from distutils.version import StrictVersion
from ramrod import (_BaseUpdater, UnknownVersionError, InvalidVersionError,
    UpdateError, UpdateResults)
from ramrod.utils import get_etree_root

TAG_CYBOX_MAJOR  = "cybox_major_version"
TAG_CYBOX_MINOR  = "cybox_minor_version"
TAG_CYBOX_UPDATE = "cybox_update_version"

CYBOX_VERSIONS = ('2.0', '2.0.1', '2.1')


class _CyboxUpdater(_BaseUpdater):
    """Base class for CybOX updating code. Sets default values for
    CybOX-specific xpaths and namespaces.

    """
    DEFAULT_VOCAB_NAMESPACE = 'http://cybox.mitre.org/default_vocabularies-1'
    XPATH_VERSIONED_NODES = "//cybox:Observables"
    XPATH_ROOT_NODES = "//cybox:Observables"
    XPATH_OBJECT_PROPS = "//cybox:Object/cybox:Properties"

    def __init__(self):
        super(_CyboxUpdater, self).__init__()


    @classmethod
    def get_version(cls, observables):
        """Returns the version of the `observables` Observables node.

        This generates a version string from the ``cybox_major``,
        ``cybox_minor`` and ``cybox_update`` attribute values.

        Raises:
            UnknownVersionError: If `observables` does not contain a
                ``cybox_major_version``, ``cybox_minor_version``, or
                 ``cybox_update_version`` attribute..
        """
        cybox_major  = observables.attrib.get(TAG_CYBOX_MAJOR)
        cybox_minor  = observables.attrib.get(TAG_CYBOX_MINOR)
        cybox_update = observables.attrib.get(TAG_CYBOX_UPDATE)

        if not any((cybox_major, cybox_minor, cybox_update)):
            raise UnknownVersionError()

        if cybox_update:
            version = "%s.%s.%s" % (cybox_major, cybox_minor, cybox_update)
        else:
            version = "%s.%s" % (cybox_major, cybox_minor)

        return version


    def _check_version(self, root):
        """Checks the versions of the Observables instances found in the
        `root` document. This overrides the ``_BaseUpdater._check_version()``
        method.

        Note:
            The ``version`` attribute of `root` is compared against the
            ``VERSION`` class-level attribute.

        Args:
            root: The root node for the document.

        Raises:
            UnknownVersionError: If `root` does not contain a ``version``
                attribute.
            InvalidVersionError: If the ``version`` attribute value for `root`
                does not match the value of ``VERSION``.

        """
        roots = self._get_root_nodes(root)
        expected = self.VERSION

        for node in roots:
            found = self.get_version(node)

            if StrictVersion(expected) != StrictVersion(found):
                raise InvalidVersionError(node, expected, found)



from .cybox_2_0 import Cybox_2_0_Updater
from .cybox_2_0_1 import Cybox_2_0_1_Updater

CYBOX_UPDATERS = {
    '2.0': Cybox_2_0_Updater,
    '2.0.1': Cybox_2_0_1_Updater
}

def update(doc, from_=None, to_=None, options=None, force=False):
    """Updates a CybOX document to align with a given version of the CybOX
    Language.

    Args:
        doc: A CybOX document filename, file-like object, etree._Element, or
            etree._ElementTree.
        from_(optional, string): The base version for the update process. If
            ``None``, an attempt will be made to extract the version number
            from `doc`.
        to_(optional, string): The version to update to. If ``None``, the
            latest version of CybOX is assumed.
        force(boolean): Forces the update process. This may result in content
            being removed during the update process and could result in
            schema-invalid content. **Use at your own risk!**

    Returns:
        An instance of ``UpdateResults`` named tuple.

    Raises:
        UpdateError: If any of the following conditions are encountered:
            * The `from_` or `to_` versions are invalid.
            * An untranslatable field is encountered and `force` is ``False``.
            * A non-unique ID is encountered and `force` is ``False``.
        InvalidVersionError: If the source document version and the `from_`
            value do not match and `force` is ``False``.
        UnknownVersionError: If the source document does not contain version
            information and `force` is ``False``.

    """
    root = get_etree_root(doc)

    from_ = from_ or _CyboxUpdater.get_version(root)
    if from_ not in CYBOX_VERSIONS:
        raise UpdateError("The `from_` parameter specified an unknown CybOX "
                          "version: '%s'" % from_)

    to_ = to_ or CYBOX_VERSIONS[-1]  # The latest version if not specified
    if to_ not in CYBOX_VERSIONS:
        raise UpdateError("The `to_` parameter specified an unknown CybOX "
                          "version: '%s'" % to_)

    if StrictVersion(from_) >= StrictVersion(to_):
        raise UpdateError("Cannot upgrade from '%s' to '%s'" % (from_, to_))

    removed, remapped = [], {}
    updated = root

    idx = CYBOX_VERSIONS.index
    for version in CYBOX_VERSIONS[idx(from_):idx(to_)]:
        klass   = CYBOX_UPDATERS[version]
        updater = klass()

        updated = updater.update(updated, options=options, force=force)
        removed.extend(updater.cleaned_fields)
        remapped.update(updater.cleaned_ids)

    updated = etree.ElementTree(updated)

    return UpdateResults(document=updated,
                         removed=removed,
                         remapped_ids=remapped)