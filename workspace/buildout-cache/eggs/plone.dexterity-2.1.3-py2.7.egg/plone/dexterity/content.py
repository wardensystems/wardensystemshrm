from Acquisition import Explicit, aq_base, aq_parent
from zExceptions import Unauthorized

from copy import deepcopy

from zope.component import queryUtility

from zope.interface import implements
from zope.interface.declarations import Implements
from zope.interface.declarations import implementedBy
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import ObjectSpecificationDescriptor

from zope.security.interfaces import IPermission

from zope.annotation import IAttributeAnnotatable

from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityItem
from plone.dexterity.interfaces import IDexterityContainer

from plone.dexterity.schema import SCHEMA_CACHE

from zope.container.contained import Contained

import AccessControl.Permissions
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager

import Products.CMFCore.permissions
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.PortalFolder import PortalFolderBase
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFPlone.interfaces import IConstrainTypes
from Products.CMFCore.interfaces import ITypeInformation

from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDefault.utils import tuplize
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

from plone.folder.ordered import CMFOrderedBTreeFolderBase
from plone.uuid.interfaces import IAttributeUUID
from plone.uuid.interfaces import IUUID

from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.supermodel.utils import mergedTaggedValueDict

from plone.dexterity.filerepresentation import DAVResourceMixin, DAVCollectionMixin
from plone.dexterity.interfaces import IDexterityFTI

_marker = object()

class FTIAwareSpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the object, plus the schema interface set in the FTI.
    """
    
    def __get__(self, inst, cls=None):
        # We're looking at a class - fall back on default
        if inst is None:
            return getObjectSpecification(cls)
        
        # Find the data we need to know if our cache needs to be invalidated
        direct_spec = getattr(inst, '__provides__', None)
        portal_type = getattr(inst, 'portal_type', None)
        
        spec = direct_spec

        # If the instance doesn't have a __provides__ attribute, get the
        # interfaces implied by the class as a starting point.
        if spec is None:
            spec = implementedBy(cls)

        # If the instance has no portal type, then we're done.
        if portal_type is None:
            return spec

        fti = queryUtility(IDexterityFTI, name=portal_type)
        if fti is None:
            return spec

        schema = SCHEMA_CACHE.get(portal_type)
        subtypes = SCHEMA_CACHE.subtypes(portal_type)

        # Find the cached value. This calculation is expensive and called
        # hundreds of times during each request, so we require a fast cache
        cache = getattr(inst, '_v__providedBy__', None)
        updated = inst._p_mtime, schema, subtypes, direct_spec

        # See if we have a valid cache. Reasons to do this include:
        #
        #  - The schema was modified.
        #  - The subtypes were modified.
        #  - The instance was modified and persisted since the cache was built.
        #  - The instance has a different direct specification.
        if cache is not None:
            cached_mtime, cached_schema, cached_subtypes, \
                cached_direct_spec, cached_spec = cache

            if cache[:-1] == updated:
                return cached_spec

        dynamically_provided = [] if schema is None else [schema]
        dynamically_provided.extend(subtypes)

        # If we have neither a schema, nor a subtype, then we're also done.
        if not dynamically_provided:
            return spec

        dynamically_provided.append(spec)
        spec = Implements(*dynamically_provided)
        inst._v__providedBy__ = updated + (spec, )

        return spec


class AttributeValidator(Explicit):
    """Decide whether attributes should be accessible. This is set as the
    __allow_access_to_unprotected_subobjects__ variable in Dexterity's content
    classes.
    """
    
    def __call__(self, name, value):
        
        # Short circuit for things like views or viewlets
        if name == '':
            return 1
        
        context = aq_parent(self)
        
        schema = self._get_schema(context)
        if schema is None:
            return 1
        
        info = mergedTaggedValueDict(schema, READ_PERMISSIONS_KEY)
        
        if name not in info:
            return 1
        
        permission = queryUtility(IPermission, name=info[name])
        if permission is not None:
            return getSecurityManager().checkPermission(permission.title, context)
        
        return 0
    
    def _get_schema(self, inst):
        portal_type = getattr(inst, 'portal_type', None)
        if portal_type is not None:
            try:
                return SCHEMA_CACHE.get(portal_type)
            except (ValueError, AttributeError,):
                pass
        return None


class PasteBehaviourMixin(object):
    def _verifyObjectPaste(self, obj, validate_src=True):
        # Extend the paste checks from OFS.CopySupport.CopyContainer
        # (permission checks) and
        # Products.CMFCore.PortalFolder.PortalFolderBase (permission checks and
        # allowed content types) to also ask the FTI if construction is
        # allowed.
        super(PasteBehaviourMixin, self)._verifyObjectPaste(obj, validate_src)
        if validate_src:
            portal_type = getattr(aq_base(obj), 'portal_type', None)
            if portal_type:
                fti = queryUtility(ITypeInformation, name=portal_type)
                if fti is not None and not fti.isConstructionAllowed(self):
                    raise ValueError('You can not add the copied content here.')


class DexterityContent(DAVResourceMixin, PortalContent, DefaultDublinCoreImpl, Contained):
    """Base class for Dexterity content
    """
    implements(IDexterityContent, IAttributeAnnotatable, IAttributeUUID)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    # portal_type is set by the add view and/or factory
    portal_type = None

    # description should always be a string
    description = u''
    
    def __getattr__(self, name):
        # optimization: sometimes we're asked for special attributes
        # such as __conform__ that we can disregard (because we
        # wouldn't be in here if the class had such an attribute
        # defined).
        if name.startswith('__'):
            raise AttributeError(name)

        # attribute was not found; try to look it up in the schema and return
        # a default
        schema = SCHEMA_CACHE.get(self.portal_type)
        if schema is not None:
            field = schema.get(name, None)
            if field is not None:
                return deepcopy(field.default)

        # do the same for each subtype
        for schema in SCHEMA_CACHE.subtypes(self.portal_type):
            field = schema.get(name, None)
            if field is not None:
                return deepcopy(field.default)

        raise AttributeError(name)
    
    # Let __name__ and id be identical. Note that id must be ASCII in Zope 2,
    # but __name__ should be unicode. Note that setting the name to something
    # that can't be encoded to ASCII will throw a UnicodeEncodeError
    
    def _get__name__(self):
        return unicode(self.id)
    def _set__name__(self, value):
        if isinstance(value, unicode):
            value = str(value) # may throw, but that's OK - id must be ASCII
        self.id = value
    __name__ = property(_get__name__, _set__name__)

    def UID(self):
        """Returns the item's globally unique id."""
        return IUUID(self)

    def setTitle(self, title):
        if isinstance(title, str):
            title = title.decode('utf-8')
        self.title = title
    
    def Title(self):
        # this is a CMF-style accessor, so should return utf8-encoded
        if isinstance(self.title, unicode):
            return self.title.encode('utf-8')
        return self.title or ''

    def setDescription(self, description):
        if isinstance(description, str):
            description = description.decode('utf-8')
        self.description = description
    
    def Description(self):
        # this is a CMF-style accessor, so should return utf8-encoded
        if isinstance(self.description, unicode):
            return self.description.encode('utf-8')
        return self.description or ''
    
    def setSubject(self, subject):
        subject = tuplize('subject', subject)
        s = []
        for part in subject:
            if isinstance(part, str):
                part = part.decode('utf-8')
            s.append(part)
        self.subject = tuple(s)
    
    def Subject(self):
        # this is a CMF-style accessor, so should return utf8-encoded
        s = []
        if self.subject:
            for part in self.subject:
                if isinstance(part, unicode):
                    part = part.encode('utf-8')
                s.append(part)
        return tuple(s)


class Item(PasteBehaviourMixin, BrowserDefaultMixin, DexterityContent):
    """A non-containerish, CMFish item
    """
    
    implements(IDexterityItem)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    isPrincipiaFolderish = 0
    
    def __init__(self, id=None, **kwargs):
        if id is not None:
            self.id = id

        dublin_kw = {}
        for arg in [ "title", "subject", "description", "contributors",
                     "effective_date", "expiration_date", "format", "language",
                     "rights"]:
            if arg in kwargs:
                dublin_kw[arg] = kwargs.pop(arg)

        DefaultDublinCoreImpl.__init__(self, **dublin_kw)
        for (k,v) in kwargs.items():
            setattr(self, k, v)
    
    # Be explicit about which __getattr__ to use
    __getattr__ = DexterityContent.__getattr__


class Container(PasteBehaviourMixin, DAVCollectionMixin, BrowserDefaultMixin, CMFCatalogAware, CMFOrderedBTreeFolderBase, DexterityContent):
    """Base class for folderish items
    """
    
    implements(IDexterityContainer)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    security = ClassSecurityInfo()
    security.declareProtected(AccessControl.Permissions.copy_or_move, 'manage_copyObjects')
    security.declareProtected(Products.CMFCore.permissions.ModifyPortalContent, 'manage_cutObjects')
    security.declareProtected(Products.CMFCore.permissions.ModifyPortalContent, 'manage_pasteObjects')
    security.declareProtected(Products.CMFCore.permissions.ModifyPortalContent, 'manage_renameObject')    
    security.declareProtected(Products.CMFCore.permissions.ModifyPortalContent, 'manage_renameObjects')
    
    isPrincipiaFolderish = 1
    
    # make sure CMFCatalogAware's manage_options don't take precedence
    manage_options = PortalFolderBase.manage_options

    # Make sure PortalFolder's accessors and mutators don't take precedence
    Title = DexterityContent.Title
    setTitle = DexterityContent.setTitle
    Description = DexterityContent.Description
    setDescription = DexterityContent.setDescription

    def __init__(self, id=None, **kwargs):
        dublin_kw = {}
        for arg in [ "title", "subject", "description", "contributors",
                     "effective_date", "expiration_date", "format", "language",
                     "rights"]:
            if arg in kwargs:
                dublin_kw[arg] = kwargs.pop(arg)

        CMFOrderedBTreeFolderBase.__init__(self, id)
        DefaultDublinCoreImpl.__init__(self, **dublin_kw)

        for (k,v) in kwargs.items():
            setattr(self, k, v)
    
    def __getattr__(self, name):
        try:
            return DexterityContent.__getattr__(self, name)
        except AttributeError:
            pass

        # Be specific about the implementation we use
        return CMFOrderedBTreeFolderBase.__getattr__(self, name)
    
    security.declareProtected(Products.CMFCore.permissions.DeleteObjects, 'manage_delObjects')
    def manage_delObjects(self, ids=None, REQUEST=None):
        """Delete the contained objects with the specified ids.

        If the current user does not have permission to delete one of the
        objects, an Unauthorized exception will be raised.
        """
        if ids is None:
            ids = []
        if isinstance(ids, basestring):
            ids = [ids]
        for id in ids:
            item = self._getOb(id)
            if not getSecurityManager().checkPermission(Products.CMFCore.permissions.DeleteObjects, item):
                raise Unauthorized, (
                    "Do not have permissions to remove this object")
        return super(Container, self).manage_delObjects(ids, REQUEST=REQUEST)

    # override PortalFolder's allowedContentTypes to respect IConstrainTypes
    # adapters
    def allowedContentTypes(self, context=None):
        if not context:
            context = self

        constrains = IConstrainTypes(context, None)
        if not constrains:
            return super(Container, self).allowedContentTypes()

        return constrains.allowedContentTypes()

    # override PortalFolder's invokeFactory to respect IConstrainTypes
    # adapters
    def invokeFactory(self, type_name, id, RESPONSE=None, *args, **kw):
        """Invokes the portal_types tool
        """
        constrains = IConstrainTypes(self, None)

        if constrains and not type_name in [fti.getId() for fti in constrains.allowedContentTypes()]:
            raise ValueError('Subobject type disallowed by IConstrainTypes adapter: %s' % type_name)

        return super(Container, self).invokeFactory(type_name, id, RESPONSE, *args, **kw)


def reindexOnModify(content, event):
    """When an object is modified, re-index it in the catalog
    """
    
    if event.object is not content:
        return
    
    # NOTE: We are not using event.descriptions because the field names may
    # not match index names.
    
    content.reindexObject()
