# Copyright (C) 2016 stereodruid(J.G.) Mail: stereodruid@gmail.com
#
#
# This file is part of OSMOSIS
#
# OSMOSIS is free software: you can redistribute it.
# You can modify it for private use only.
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OSMOSIS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from kodi_six.utils import py2_decode
import os
import re
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from .common import Globals
from .create import fillPluginItems
from .fileSys import readMediaList
from .guiTools import selectDialog
from .moduleUtil import getModule
from .stringUtils import getProviderId, getStrmname, parseMediaListURL

globals = Globals()
ADDON_PATH = py2_decode(xbmc.translatePath(globals.addon.getAddonInfo('path')))
MEDIALIST_PATH = py2_decode(xbmc.translatePath(globals.addon.getSetting('MediaList_LOC')))
MediaList_LOC = os.path.join(MEDIALIST_PATH, 'MediaList.xml')
represent = os.path.join(ADDON_PATH, 'resources/media/icon.png')

actor_update_manual = 0
actor_update_periodictime = 1
actor_update_fixtime = 2


def strm_update(selectedItems=None, actor=0):
    if xbmcvfs.exists(MediaList_LOC):
        thelist = sorted(readMediaList())
        if not selectedItems and actor == actor_update_manual:
            selectAction = ['Movies', 'TV-Shows', 'Audio', 'All']
            choice = selectDialog('Update all: Select which Media Types to update', selectAction)
            if choice == -1:
                return
            elif choice == 3:
                cTypeFilter = None
            else:
                cTypeFilter = selectAction[choice]
        else:
            cTypeFilter = None

        items = selectedItems if selectedItems else [{'entry': item} for item in thelist]
        if len(items) > 0:
            dialogeBG = xbmcgui.DialogProgressBG()
            dialogeBG.create('OSMOSIS total update process')

            iUrls = 0
            splittedEntries = []
            for item in items:
                splits = item.get('entry').split('|')
                if cTypeFilter and not re.findall(cTypeFilter, splits[0]):
                    continue
                iUrls += len(splits[2].split('<next>'))
                splittedEntries.append(splits)

            if iUrls == 0:
                dialogeBG.close()
                return

            step = j = 100 / iUrls
            for splittedEntry in splittedEntries:
                cType, name, url = splittedEntry[0], splittedEntry[1], splittedEntry[2]

                urls = url.split('<next>')
                for url in urls:
                    name_orig, plugin_url = parseMediaListURL(url)
                    plugin_id = getProviderId(plugin_url).get('plugin_id')
                    if plugin_id:
                        module = getModule(plugin_id)
                        if module and hasattr(module, 'update'):
                            url = module.update(name, url, 'video', thelist)

                    dialogeBG.update(int(j), 'OSMOSIS total update process' , 'Current Item: {0}; Items left: {1}'.format(getStrmname(name), iUrls))
                    j += step

                    fillPluginItems(url, strm=True, strm_name=name, strm_type=cType, name_orig=name_orig)
                    iUrls -= 1

            dialogeBG.close()
            if actor == actor_update_periodictime:
                xbmc.executebuiltin('Notification({0}, {1}, {2}, {3})'.format(globals.PLUGIN_NAME, 'Next update in: {0}h'.format(globals.addon.getSetting('Automatic_Update_Time')), 5000, represent))
            elif actor == actor_update_fixtime:
                next_run = globals.addon.getSetting('update_time')[:5]
                xbmc.executebuiltin('Notification({0}, {1}, {2}, {3})'.format(globals.PLUGIN_NAME, 'Next update: {0}h'.format(next_run), 5000, represent))