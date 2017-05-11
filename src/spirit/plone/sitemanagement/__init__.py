# -*- coding: utf-8 -*-
"""Control your Plone sites from one management screen."""

# python imports
import logging

# zope imports
from zope.i18nmessageid import MessageFactory

# local imports
from spirit.plone.sitemanagement import config

logger = logging.getLogger(config.PROJECT_NAME)
_ = MessageFactory(config.PROJECT_NAME)
