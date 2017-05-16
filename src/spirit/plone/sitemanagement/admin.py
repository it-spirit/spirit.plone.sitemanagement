# -*- coding: utf-8 -*-
"""Plone site management pages."""

# python imports
import pkg_resources
import transaction

# zope imports
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.browser.admin import Overview
from Products.CMFPlone.interfaces import INonInstallable
from Products.GenericSetup import EXTENSION
try:
    from Products.GenericSetup.tool import UNKNOWN
except ImportError:
    UNKNOWN = 'unknown'
try:
    from plone.app.theming.browser.controlpanel import ThemingControlpanel
except ImportError:
    ThemingControlpanel = None
from zope.component import getAllUtilitiesRegisteredFor
from zope.component.hooks import setSite
from zope.component.interfaces import ComponentLookupError


class SiteManagement(Overview):
    """Site Management Page."""

    def sites(self, root=None):
        result = super(SiteManagement, self).sites(root=root)
        return sorted(result, key=lambda x: x.getId())

    def get_theming(self, site):
        """Return the theming configuration for a site."""
        result = {}
        if ThemingControlpanel is None:
            return result

        setSite(site)
        tcp = ThemingControlpanel(site, self.request)
        try:
            tcp.update()
        except ComponentLookupError:
            tcp = None
        else:
            result['current'] = tcp.selectedTheme
            try:
                settings = getattr(
                    tcp, 'theme_settings', getattr(tcp, 'settings')
                )
            except AttributeError:
                settings = None
            result['settings'] = settings
            themes = [
                theme for theme in tcp.themeList()
                if theme.get('name') == tcp.selectedTheme
            ]
            if len(themes) > 0:
                result['data'] = themes[0]
        finally:
            setSite(None)
        return result

    def get_upgrades(self, site):
        filtered = {}
        addons = self.get_addons(site)
        for product_id, addon in addons.items():
            installed = addon['is_installed']
            if not installed:
                continue
            upgrade_info = addon['upgrade_info']
            if not upgrade_info.get('available'):
                continue
            filtered[product_id] = addon
        return filtered

    def get_addons(self, site):  # noqa
        """"""
        addons = {}
        ignore_profiles = []
        ignore_products = []

        utils = getAllUtilitiesRegisteredFor(INonInstallable)
        for util in utils:
            ni_profiles = getattr(util, 'getNonInstallableProfiles', None)
            if ni_profiles is not None:
                ignore_profiles.extend(ni_profiles())
            ni_products = getattr(util, 'getNonInstallableProducts', None)
            if ni_products is not None:
                ignore_products.extend(ni_products())

        portal_setup = getToolByName(site, 'portal_setup')  # noqa
        profiles = portal_setup.listProfileInfo()
        for profile in profiles:
            if profile['type'] != EXTENSION:
                continue

            pid = profile['id']
            if pid in ignore_profiles:
                continue
            pid_parts = pid.split(':')

            product_id = profile['product']
            if product_id in ignore_products:
                continue

            profile_type = pid_parts[-1]

            if product_id not in addons:
                installed = self.is_profile_installed(portal_setup, pid)
                upgrade_info = {}
                if installed:
                    upgrade_info = self.upgrade_info(portal_setup, product_id)
                addons[product_id] = {
                    'id': product_id,
                    'version': self.get_product_version(product_id),
                    'title': product_id,
                    'description': '',
                    'upgrade_profiles': {},
                    'other_profiles': [],
                    'install_profile': None,
                    'install_profile_id': '',
                    'uninstall_profile': None,
                    'uninstall_profile_id': '',
                    'is_installed': installed,
                    'upgrade_info': upgrade_info,
                    'profile_type': profile_type,
                }
                # Add info on install and uninstall profile.
                product = addons[product_id]
                install_profile = self.get_install_profile(
                    portal_setup,
                    product_id,
                )
                if install_profile is not None:
                    product['title'] = install_profile['title']
                    product['description'] = install_profile['description']
                    product['install_profile'] = install_profile
                    product['install_profile_id'] = install_profile['id']
                    product['profile_type'] = 'default'
                uninstall_profile = self.get_uninstall_profile(
                    portal_setup,
                    product_id,
                )
                if uninstall_profile is not None:
                    product['uninstall_profile'] = uninstall_profile
                    product['uninstall_profile_id'] = uninstall_profile['id']
                    # Do not override profile_type.
                    if not product['profile_type']:
                        product['profile_type'] = 'uninstall'
            if profile['id'] in (product['install_profile_id'],
                                 product['uninstall_profile_id']):
                # Everything has been done.
                continue
            elif 'version' in profile:
                product['upgrade_profiles'][profile['version']] = profile
            else:
                product['other_profiles'].append(profile)
        return addons

    def is_profile_installed(self, portal_setup, profile_id):
        return portal_setup.getLastVersionForProfile(profile_id) != UNKNOWN

    def upgrade_info(self, portal_setup, product_id):
        """Return upgrade info for a product."""
        profile = self.get_install_profile(
            portal_setup,
            product_id,
            allow_hidden=True,
        )
        if profile is None:
            # No GS profile, not supported.
            return {}
        profile_id = profile['id']
        profile_version = str(portal_setup.getVersionForProfile(profile_id))
        if profile_version == 'latest':
            profile_version = self.get_latest_upgrade_step(
                portal_setup,
                profile_id,
            )
        if profile_version == UNKNOWN:
            # If a profile doesn't have a metadata.xml use the package version.
            profile_version = self.get_product_version(product_id)
        installed_profile_version = portal_setup.getLastVersionForProfile(
            profile_id)
        # getLastVersionForProfile returns the version as a tuple or unknown.
        if installed_profile_version != UNKNOWN:
            installed_profile_version = str(
                '.'.join(installed_profile_version))
        return dict(
            required=profile_version != installed_profile_version,
            available=len(portal_setup.listUpgrades(profile_id)) > 0,
            hasProfile=True,
            installedVersion=installed_profile_version,
            newVersion=profile_version,
        )

    def get_install_profile(
            self, portal_setup, product_id, allow_hidden=False):
        """Return the default install profile."""
        return self._get_profile(
            portal_setup,
            product_id,
            'default',
            strict=False,
            allow_hidden=allow_hidden,
        )

    def _get_profile(
            self, portal_setup, product_id, name, strict=True,
            allow_hidden=False):
        """Return profile with given name."""
        profiles = self._install_profile_info(portal_setup, product_id)
        if not profiles:
            return
        utils = getAllUtilitiesRegisteredFor(INonInstallable)
        hidden = []
        for util in utils:
            gnip = getattr(util, 'getNonInstallableProfiles', None)
            if gnip is None:
                continue
            hidden.extend(gnip())

        # We have prime candidates that we prefer, and have hidden candidates
        # in case allow_hidden is True.
        prime_candidates = []
        hidden_candidates = []
        for profile in profiles:
            profile_id = profile['id']
            profile_id_parts = profile_id.split(':')
            if len(profile_id_parts) != 2:
                continue
            if allow_hidden and profile_id in hidden:
                if profile_id_parts[1] == name:
                    # This will especially be true for uninstall profiles,
                    # which are usually hidden.
                    return profile
                hidden_candidates.append(profile)
                continue
            if profile_id_parts[1] == name:
                return profile
            prime_candidates.append(profile)
        if strict:
            return
        if prime_candidates:
            # QI used to pick the first profile.
            # Return the first profile after all.
            return prime_candidates[0]
        if allow_hidden and hidden_candidates:
            # Return the first hidden profile.
            return hidden_candidates[0]

    def _install_profile_info(self, portal_setup, product_id):
        """List extension profile infos of a given product."""
        profiles = portal_setup.listProfileInfo()
        # We are only interested in extension profiles for the product.
        profiles = [
            prof for prof in profiles
            if prof['type'] == EXTENSION and (
                prof['product'] == product_id or
                prof['product'] == 'Products.{0}'.format(product_id)
            )
        ]
        return profiles

    def get_latest_upgrade_step(self, portal_setup, profile_id):
        """Get highest ordered upgrade step for profile."""
        profile_version = UNKNOWN
        try:
            available = portal_setup.listUpgrades(profile_id, True)
            if available:  # could return empty sequence
                latest = available[-1]
                profile_version = max(
                    latest['dest'],
                    key=pkg_resources.parse_version
                )
        except Exception:
            pass
        return profile_version

    def get_product_version(self, product_id):
        """Return the version of the product (package)."""
        try:
            dist = pkg_resources.get_distribution(product_id)
            return dist.version
        except pkg_resources.DistributionNotFound:
            return ''

    def get_uninstall_profile(self, portal_setup, product_id):
        """Return the uninstall profile."""
        return self._get_profile(
            portal_setup,
            product_id,
            'uninstall',
            strict=True,
            allow_hidden=True,
        )


class UpgradeProducts(SiteManagement):
    """Upgrade a product... or twenty"""

    def __call__(self):
        addons = self.request.get('addons', None)
        if isinstance(addons, basestring):
            addons = [addons]
        messages = []
        if addons:
            for addon in addons:
                site_id, addon_id = addon.split('__')
                result = self.upgrade_product(site_id, addon_id)
                if not result:
                    messages.append(
                        u'Error upgrading ${0} in {1}'.format(
                            addon_id,
                            site_id,
                        )
                    )
                    # Abort changes for all upgrades.
                    transaction.abort()
                    break
            else:
                messages.append(
                    u'Upgraded products.'
                )
        url = self.context.absolute_url() + '/@@plone-sitemanagement'
        self.request.response.redirect(url)

    def upgrade_product(self, site_id, product_id):
        """Run the upgrade steps for a product."""
        site = self.context.get(site_id, None)
        if not site:
            return False
        setSite(site)
        portal_setup = getToolByName(site, 'portal_setup')  # noqa
        profile = self.get_install_profile(
            portal_setup,
            product_id,
            allow_hidden=True,
        )
        if profile is None:
            setSite(None)
            return False
        try:
            portal_setup.upgradeProfile(profile['id'])
        except AttributeError:
            qi = getToolByName(site, 'portal_quickinstaller')  # noqa
            qi.upgradeProduct(product_id)
        setSite(None)
        return True
