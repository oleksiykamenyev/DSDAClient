"""DSDA client class

Used to retrieve info from DSDA by parsing the HTML
"""

import io
import operator
import os
import re
import yaml

from dsda_client.helper_functions import helper_functions as hf
from random import randint

__author__ = '4shockblast'


class DSDAClient(object):
    """Client to retrieve information from the DSDA

    Currently supports record retrieval based on guessed compatibilities
    for the wads, can retrieve the last update date, can return various
    stats on players and wads, and can return random wad and player pages
    """
    # Static list of DSDA URLs listing out all the wads, not expected
    # to change anytime soon
    WAD_LIST_URLS = [
        'http://doomedsda.us/wadlist1.html',
        'http://doomedsda.us/wadlist2.html',
        'http://doomedsda.us/wadlist3.html',
        'http://doomedsda.us/wadlist4.html',
        'http://doomedsda.us/wadlist5.html',
        'http://doomedsda.us/wadlist6.html',
        'http://doomedsda.us/wadlist7.html',
        'http://doomedsda.us/wadlist8.html',
        'http://doomedsda.us/wadlist9.html'
    ]
    # DSDA URL listing out all the players, not expected to change
    # anytime soon
    PLAYER_LIST_URL = 'http://doomedsda.us/players.html'
    # DSDA URL containing all of the updates, not expected to change
    # anytime soon
    UPDATES_URL = 'http://doomedsda.us/updates.html'

    # Static list of wads on DSDA that are paginated, not expected
    # to change
    PAGINATED_WADS = [
        'doom2',
        'doom',
        'tnt',
        'plutonia',
        'hr',
        'scythe',
        'mm',
        'av (2nd Release)',
        'mm2',
        'requiem'
    ]
    # Regexes matching executables used by players on DSDA mapped
    # to their respective compatibilities
    EXECUTABLE_REGEXES = {
        # Original Boom port versions
        re.compile(r'^Boom.*$'): 'Boom',

        # Initially a modified doom2.exe, eventually based on MBF with extra
        # features. Currently only recordings by port author for vanilla
        # mapsets.
        re.compile(r'^CDooM.*$'): 'limit-removing',

        # Designed to emulate vanilla Doom as closely as possible, mapped to
        # limit-removing to be safe
        re.compile(r'^Chocolate DooM.*$'): 'limit-removing',

        # Modified Chocolate with extra speedrun-oriented features, only
        # vanilla compatible demos supported
        re.compile(r'^CNDoom.*$'): 'limit-removing',

        # Modified Chocolate with limits removed
        re.compile(r'^Crispy Doom.*$'): 'limit-removing',

        # Vanilla Doom, Doom 2, or Final Doom exes all map to limit-removing
        # to be safe
        re.compile(r'^DooM2? v1.\d+\.?\d*f?$'): 'limit-removing',

        # Doom 95 exes map to limit-removing to be safe
        re.compile(r'^DooM2? v95f?$'): 'limit-removing',

        # Doom 64 port to PC, maps to its own compatibility
        re.compile(r'^Doom64 EX.*$'): 'Doom 64',

        # Advanced source port, features mostly limited to hi-res textures and
        # fancy effects, but still does not correspond easily to any
        # obvious compatibility
        re.compile(r'^Doomsday.*$'): 'Unknown',

        # Earliest source port, mostly equivalent to vanilla
        re.compile(r'^DosDooM.*$'): 'limit-removing',

        # Version of DosDoom designed for TAS, also should be mostly equivalent
        # to vanilla
        re.compile(r'^TasDooM.*$'): 'limit-removing',

        # Advanced source port, impossible to map to anything, as its features
        # are in between PrBoom and (G)ZDoom
        re.compile(r'^Eternity.*$'): 'Unknown',

        # Advanced source port
        re.compile(r'^GZDoom.*$'): 'GZDoom',

        # Initially very similar to DOSDoom, later added many advanced features
        re.compile(r'^Legacy.*$'): 'Unknown',

        # Modified version of (G)ZDoom with some extra features and difficulty
        # settings, maps to GZDoom compatibility I guess
        re.compile(r'^ManDoom.*$'): 'GZDoom',

        # Modified Boom with extra features, maps to MBF compatibility
        re.compile(r'^MBF.*$'): 'MBF',

        # Version of MBF supporting TAS, it doesn't look like any demos are
        # marked with this even though there are MBF TAS demos on DSDA
        re.compile(r'^TASMBF.*$'): 'MBF',

        # Encompasses both the original PrBoom and PrBoom+, if a compatiblity
        # level is specified, then that gives the wad compat mapping, otherwise
        # doesn't map to anything
        re.compile(r'^PRBoom.*$'): 'PrBoom',

        # Modified version of Chocolate with some limits removed
        re.compile(r'^Strawberry DooM.*$'): 'limit-removing',

        # Old multiplayer port of ZDoom, with limited exceptions commonly
        # used for rocket jump maps, so it maps to its own compatibility,
        # some exceptions are that recordings for ZDoom maps and
        # co-op demos that are not too common
        re.compile(r'^ZDaemon.*$'): 'ZDaemon',

        # Advanced source port, maps to GZDoom compatibility as there
        # is no clear distinction that can be made between the
        # two based on the version of (G)ZDoom used
        re.compile(r'^ZDoom.*$'): 'GZDoom'
    }
    # Valid categories to query records for, maps possible query
    # strings to exact category strings used on DSDA
    VALID_CATEGORIES = {
        'uvmax': ['UV Max'],
        'max': ['UV Max'],
        'uvspeed': ['UV Speed', 'Pacifist', 'UV Max'],
        'nmspeed': ['NM Speed', 'NM 100'],
        'nm100': ['NM 100'],
        'nm100s': ['NM 100'],
        'uvfast': ['UV -Fast'],
        'fast': ['UV -Fast'],
        'uvrespawn': ['Respawn'],
        'respawn': ['Respawn'],
        'uvpacifist': ['Pacifist'],
        'pacifist': ['Pacifist'],
        'uvtyson': ['Tyson'],
        'tyson': ['Tyson'],
        'nomo': ['NoMo', 'NoMo 100'],
        'uvnomo': ['NoMo', 'NoMo 100'],
        'nomonsters': ['NoMo', 'NoMo 100'],
        'uvnomonsters': ['NoMo', 'NoMo 100'],
        'nomo100': ['NoMo 100'],
        'uvnomo100': ['NoMo 100'],
        'nomonsters100': ['NoMo 100'],
        'uvnomonsters100': ['NoMo 100']
    }

    # Dictionary mapping exact DSDA category strings to "fixed" category names :^)
    DSDA_CATEGORIES_TO_FIXED_NAMES = {
        'UV Max': 'UV-Max',
        'UV Speed': 'UV-Speed',
        'NM Speed': 'NM-Speed',
        'NM 100': 'NM100',
        'Pacifist': 'UV Pacifist',
        'Tyson': 'UV Tyson',
        'UV -Fast': 'UV -fast',
        'Respawn': 'UV -respawn',
        'NoMo': 'Nomo',
        'NoMo 100': 'Nomo100'
    }

    # Files used to cache various info synced with DSDA
    PLAYER_NAME_TO_URL_FILE_NAME = 'player_name_to_url.txt'
    WAD_NAME_TO_URL_FILE_NAME = 'wad_name_to_url.txt'
    WAD_NAME_TO_COMPAT_FILE_NAME = 'wad_name_to_compat.txt'
    HIGHEST_PLAYER_FILE_NAME = 'highest_player.txt'
    HIGHEST_WAD_FILE_NAME = 'highest_wad.txt'

    def __init__(self):
        """Initialization function

        Creates dictionaries for caching info from DSDA
        """
        self._player_name_to_url_dict = {}
        self._player_lowercase_to_original_dict = {}
        self._url_to_player_name_dict = {}
        self._wad_name_to_url_dict = {}
        self._url_to_wad_name_dict = {}
        self._wad_name_to_compat_dict = {}

    @staticmethod
    def _get_wad_urls_for_paginated_wad(wad_url):
        """Gets all wad URLs fo a paginated wad"""
        # Current URL will always be the first page of a paginated wad
        wad_urls = [wad_url]
        tree = hf.get_web_page_html(wad_url)
        # Gets the second table on a page, which will always exist for
        # paginated wads as the first is the demo table and the second is
        # the navigation table
        tables = tree.xpath('//table')
        rows = tables[1].xpath('.//tr[@class="row1" or @class="row2"]')
        for row in rows:
            for col in row:
                # Sometimes columns in the table will be blank for padding
                if len(col):
                    page_url = col[0].get('href')
                    wad_urls.append('http://doomedsda.us/{}'.format(page_url))
        return wad_urls

    @staticmethod
    def _get_demo_rows_for_wad_url(wad_url):
        """Gets demo rows for a wad URL"""
        tree = hf.get_web_page_html(wad_url)
        # Demos for wads on DSDA are placed in a table, and there are at
        # most two tables on a particular page (demo and page navigation
        # tables), so the first one is needed to parse the demos
        tables = tree.xpath('//table')
        # All demo rows on DSDA have these classes
        rows = tables[0].xpath('.//tr[@class="row1" or @class="row2" or'
                               ' @class="row1top" or @class="row2top"]')
        return rows

    def _get_wad_url(self, wad_name):
        """Finds wad name in wad name to URL dictionary

        If the wad name is not found in the dictionary, the function will
        attempt to sanitize the name in case it has a ".wad" or ".pk3" prefix.

        No substring search is performed because there are probably too many
        wads for that to have much use
        """
        wad_name_sanitized = wad_name.rstrip()
        if wad_name_sanitized in self._wad_name_to_url_dict:
            return self._wad_name_to_url_dict[wad_name_sanitized], wad_name_sanitized
        else:
            wad_name_sanitized = wad_name_sanitized.rsplit('.wad', 1)[0]\
                                                   .rsplit('.pk3', 1)[0]
            if wad_name_sanitized in self._wad_name_to_url_dict:
                return self._wad_name_to_url_dict[wad_name_sanitized], wad_name_sanitized
            else:
                possible_options = []
                for possible_wad in self._wad_name_to_url_dict:
                    if wad_name_sanitized in possible_wad:
                        possible_options.append(possible_wad)
                if possible_options:
                    num_possible_options = len(possible_options)
                    if num_possible_options == 1:
                        wad_name_found = possible_options[0]
                        return self._wad_name_to_url_dict[wad_name_found], wad_name_found
                    else:
                        possible_options.sort()
                        if num_possible_options > 20:
                            return None, 'Found {} matching wads!'.format(num_possible_options)
                        error_string = 'Found {} matching wads! Possible wads:\n'.format(
                            num_possible_options
                        )
                        count = 1
                        for option in possible_options:
                            error_string = '{prev_error}  {count}: {option}\n'.format(
                                prev_error=error_string,
                                count=count,
                                option=option
                            )
                            count += 1
                        return None, error_string.rstrip('\n')
                else:
                    return None, 'Wad name not found!'

    def _get_wad_compat(self, wad_name):
        """Finds wad name in wad name to compat dictionary

        If the wad name is not found in the dictionary, the function will
        attempt to sanitize the name in case it has a ".wad" or ".pk3" prefix.

        No substring search is performed because there are probably too many
        wads for that to have much use
        """
        wad_name_sanitized = wad_name.rstrip()
        if wad_name_sanitized in self._wad_name_to_compat_dict:
            return self._wad_name_to_compat_dict[wad_name_sanitized], ''
        else:
            wad_name_sanitized = wad_name_sanitized.rsplit('.wad', 1)[0]\
                                                   .rsplit('.pk3', 1)[0]
            if wad_name_sanitized in self._wad_name_to_compat_dict:
                return self._wad_name_to_compat_dict[wad_name_sanitized], ''
            else:
                possible_options = []
                for possible_wad in self._wad_name_to_compat_dict:
                    if wad_name_sanitized in possible_wad:
                        possible_options.append(possible_wad)
                if possible_options:
                    num_possible_options = len(possible_options)
                    if num_possible_options == 1:
                        wad_name_found = possible_options[0]
                        return self._wad_name_to_compat_dict[wad_name_found], ''
                    else:
                        possible_options.sort()
                        if num_possible_options > 20:
                            return None, 'Found {} matching wads!'.format(num_possible_options)
                        error_string = 'Found {} matching wads! Possible wads:\n'.format(
                            num_possible_options
                        )
                        count = 1
                        for option in possible_options:
                            error_string = '{prev_error}  {count}: {option}\n'.format(
                                prev_error=error_string,
                                count=count,
                                option=option
                            )
                            count += 1
                        return None, error_string.rstrip('\n')
                else:
                    return None, 'Wad compat not found!'

    def sync_full(self):
        """Sync everything from DSDA to local cache

        Syncs players, wads, and compats. Syncs all compats if the compats
        cache file doesn't exist and just new compats if it exists.
        """
        self.sync_players()
        if not os.path.isfile(self.WAD_NAME_TO_COMPAT_FILE_NAME):
            self.sync_compats_full()
        else:
            if not self._wad_name_to_compat_dict:
                with io.open(self.WAD_NAME_TO_COMPAT_FILE_NAME, encoding='utf8') \
                        as wad_name_to_compat_file:
                    wad_mappings = wad_name_to_compat_file.readlines()

                for wad_map in wad_mappings:
                    wad, compat = wad_map.rsplit('=')
                    self._wad_name_to_compat_dict[wad] = compat.strip()
            self.sync_compats_new()
        self.sync_wads()

    def sync_players(self):
        """Sync players to local cache from DSDA

        Parses player page on DSDA and generates a mapping from each
        player name to the player page URL. This information is then
        saved to a dictionary and to a local file. This also retrieves
        the largest player index in order to determine the last player
        page URL for random player page support.
        """
        open(self.PLAYER_NAME_TO_URL_FILE_NAME, 'w').close()
        open(self.HIGHEST_PLAYER_FILE_NAME, 'w').close()
        highest_url_index = -1
        tree = hf.get_web_page_html(self.PLAYER_LIST_URL)
        rows = tree.xpath('//tr[@class="row1" or @class="row2"]')
        for row in rows[1:]:
            if len(row) > 1:
                # Players with profile pages have the text nested under an
                # extra <a> element
                if len(row[0]):
                    # Some player names use special characters
                    player_name = row[0][0].text.encode('utf-8')
                else:
                    player_name = row[0].text.encode('utf-8')
                url_prefix = row[1][0].get('href')
                player_url = 'http://doomedsda.us/{}'.format(url_prefix)
                self._player_name_to_url_dict[player_name.decode('utf-8').lower()] = player_url
                self._url_to_player_name_dict[player_url.rstrip('\n')] = player_name.decode('utf-8')
                # Ugly way to keep track of the original spelling for player
                # names for error message printing
                self._player_lowercase_to_original_dict[
                    player_name.decode('utf-8').lower()
                ] = player_name.decode('utf-8')
                with io.open(self.PLAYER_NAME_TO_URL_FILE_NAME, 'a', encoding='utf8')\
                        as player_name_to_url_file:
                    player_name_to_url_file.write('{player_name}={player_url}\n'.format(
                        player_name=player_name.decode('utf-8'),
                        player_url=player_url
                    ))

                cur_url_index = int(re.findall(r'\d+', url_prefix)[0])
                if cur_url_index > highest_url_index:
                    highest_url_index = cur_url_index

        with open(self.HIGHEST_PLAYER_FILE_NAME, 'a') as highest_player_file:
            highest_player_file.write('{}\n'.format(highest_url_index))

    def sync_wads(self):
        """Sync wads to local cache from DSDA

        Parses wad pages on DSDA and generates a mapping from each
        wad name to the wad page URL. This information is then
        saved to a dictionary and to a local file. This also retrieves
        the largest wad index in order to determine the last wad
        page URL for random wad page support.
        """
        open(self.WAD_NAME_TO_URL_FILE_NAME, 'w').close()
        open(self.HIGHEST_WAD_FILE_NAME, 'w').close()
        highest_url_index = -1
        for wad_list_url in self.WAD_LIST_URLS:
            tree = hf.get_web_page_html(wad_list_url)
            rows = tree.xpath('//tr[@class="row1" or @class="row2"]')
            for row in rows[1:]:
                if len(row) and len(row[0]):
                    wad_name = row[0][0].text
                    url_prefix = row[0][0].get('href')
                    wad_url = 'http://doomedsda.us/{}'.format(url_prefix)
                    self._wad_name_to_url_dict[wad_name] = wad_url
                    self._url_to_wad_name_dict[wad_url.rstrip('\n')] = wad_name
                    with open(self.WAD_NAME_TO_URL_FILE_NAME, 'a')\
                            as wad_name_to_url_file:
                        wad_name_to_url_file.write('{wad_name}={wad_url}\n'.format(
                            wad_name=wad_name,
                            wad_url=wad_url
                        ))

                    cur_url_index = int(re.findall(r'\d+', url_prefix)[0])
                    if cur_url_index > highest_url_index:
                        highest_url_index = cur_url_index

        with open(self.HIGHEST_WAD_FILE_NAME, 'a') as highest_wad_file:
            highest_wad_file.write('{}\n'.format(highest_url_index))

    def sync_compats_full(self):
        """Sync wad compatibilities to local cache from DSDA

        Performs a full sync for each wad to its compatibility,
        this function takes a long time to run because it needs
        to examine every wad page on DSDA, so be careful. Places
        the wad-to-compat mappings into a dictionary and local file.
        This file is sorted for ease of readability.
        """
        if not self._wad_name_to_url_dict:
            if os.path.isfile(self.WAD_NAME_TO_URL_FILE_NAME):
                with io.open(self.WAD_NAME_TO_URL_FILE_NAME, encoding='utf8')\
                        as wad_name_to_url_file:
                    wad_mappings = wad_name_to_url_file.readlines()

                for wad_map in wad_mappings:
                    wad, url = wad_map.rsplit('=')
                    self._wad_name_to_url_dict[wad] = url
                    self._url_to_wad_name_dict[url] = wad
            else:
                self.sync_wads()

        open(self.WAD_NAME_TO_COMPAT_FILE_NAME, 'w').close()
        for wad_name in self._wad_name_to_url_dict:
            guessed_compat = self._guess_compat_by_wad_name(wad_name)
            self._wad_name_to_compat_dict[wad_name] = guessed_compat[0]
            with open('wad_name_to_compat.txt', 'a') as wad_name_to_compat_file:
                wad_name_to_compat_file.write('{wad_name}={compat}\n'.format(
                    wad_name=wad_name,
                    compat=guessed_compat[0]
                ))

        hf.sort_file(self.WAD_NAME_TO_COMPAT_FILE_NAME)

    def _guess_compat_by_wad_name(self, wad_name):
        """Guesses compat for a wad name

        Top-level function which determines what URLs correspond
        to a particular wad name (may be many in case it is a
        paginated wad), then calls a helper function.
        """
        wad_url = self._wad_name_to_url_dict[wad_name]
        if wad_name in self.PAGINATED_WADS:
            wad_urls = self._get_wad_urls_for_paginated_wad(wad_url)
            return self._guess_compat_by_wad_url_list(wad_urls)
        else:
            return self._guess_compat_by_wad_url_list([wad_url])

    def _guess_compat_by_wad_url_list(self, wad_urls):
        """Guesses compat for a list of wad URLs

        This guess is performed according to the most used source
        port. Each source port is mapped to a particular compatibility,
        and the compatibility mapping for the most used source port
        is used as the guess for the wad.

        In case a source port cannot be mapped to a clear compatibility,
        it is marked as Unknown except in the case of generic PrBoom being
        used. Because many demos on DSDA use PrBoom as a source port
        but do not specify the compatibility used, the count from those
        demos is added to the most used compatibility that is supported
        by PrBoom+. If there are no other compatibilities in the list
        supported by PrBoom+, those entries are converted to Unknown.

        The script will output any ports that were entirely unrecognized.
        This can happen if there is a mistake on any existing source
        port field on DSDA or a new source port is added to DSDA.
        """
        compatibility_counts = {}
        known_unmapped_ports = {}
        unrecognized_ports = {}
        for wad_url in wad_urls:
            rows = self._get_demo_rows_for_wad_url(wad_url)
            for row in rows[1:]:
                if len(row) > 2:
                    port = row[-2].text
                    port_matched = False
                    for port_regex in self.EXECUTABLE_REGEXES:
                        if re.match(port_regex, port):
                            current_compat = self.EXECUTABLE_REGEXES[port_regex]
                            if self.EXECUTABLE_REGEXES[port_regex] != 'PrBoom':
                                if current_compat in compatibility_counts:
                                    compatibility_counts[current_compat] += 1
                                else:
                                    compatibility_counts[current_compat] = 1
                                if current_compat == 'Unknown':
                                    if port in known_unmapped_ports:
                                        known_unmapped_ports[port] += 1
                                    else:
                                        known_unmapped_ports[port] = 1
                            else:
                                port_split = port.split('cl')
                                if len(port_split) > 1:
                                    compatibility_guess = self._guess_prboom_compat(port_split)
                                    if compatibility_guess == 'PrBoom':
                                        if port in known_unmapped_ports:
                                            known_unmapped_ports[port] += 1
                                        else:
                                            known_unmapped_ports[port] = 1

                                    if compatibility_guess in compatibility_counts:
                                        compatibility_counts[compatibility_guess] += 1
                                    else:
                                        compatibility_counts[compatibility_guess] = 1
                                else:
                                    if 'PrBoom' in compatibility_counts:
                                        compatibility_counts['PrBoom'] += 1
                                    else:
                                        compatibility_counts['PrBoom'] = 1
                                    if port in known_unmapped_ports:
                                        known_unmapped_ports[port] += 1
                                    else:
                                        known_unmapped_ports[port] = 1
                            port_matched = True
                    if not port_matched:
                        if port in unrecognized_ports:
                            unrecognized_ports[port] += 1
                        else:
                            unrecognized_ports[port] = 1

        if unrecognized_ports:
            print('Unrecognized ports for WAD URL: {}'.format(wad_urls[0]))
            print(unrecognized_ports)

        if 'PrBoom' in compatibility_counts:
            compats_sorted = sorted(compatibility_counts.items(),
                                    key=operator.itemgetter(1),
                                    reverse=True)
            pushed_down = False
            for compat in compats_sorted:
                # Compatibilities supported by PrBoom
                if (compat[0] == 'limit-removing' or
                        compat[0] == 'Boom' or
                        compat[0] == 'MBF'):
                    compatibility_counts[compat[0]] += compatibility_counts['PrBoom']
                    pushed_down = True
                    break
            if not pushed_down:
                if 'Unknown' in compatibility_counts:
                    compatibility_counts['Unknown'] += compatibility_counts['PrBoom']
                else:
                    compatibility_counts['Unknown'] = compatibility_counts['PrBoom']

            compatibility_counts.pop('PrBoom')

        if compatibility_counts.items():
            max_compat = max(compatibility_counts.items(), key=operator.itemgetter(1))
        else:
            # This will only be executed if a wad has no demos on DSDA
            # presumably that can happen if all demos were removed on
            # request for a particular wad
            print('Error: no compats for wad URL: {}'.format(wad_urls[0]))
            max_compat = ['Unknown']
        return max_compat

    @staticmethod
    def _guess_prboom_compat(port_split):
        """Guesses engine compatibility based on PrBoom+ complevel"""
        # PrBoom entries with complevels use the
        # complevel for guessing the compat
        complevel = int(port_split[1])
        # Lower complevels correspond to
        # limit-removing/vanilla
        if 0 <= complevel <= 6:
            compatibility_guess = 'limit-removing'
        # Boom/LxDoom complevels
        elif 7 <= complevel <= 10:
            compatibility_guess = 'Boom'
        elif complevel == 11:
            compatibility_guess = 'MBF'
        # All higher complevels and -1 correspond
        # to versions of PrBoom/PrBoom+
        else:
            compatibility_guess = 'PrBoom'
        return compatibility_guess

    def sync_compats_new(self):
        """Sync compats only for new wads on DSDA

        Because a full sync takes so much time and guessed compats for
        existing wads are unlikely to shift much (and likely to shift both
        incorrectly and correctly), this only syncs wads for new wads added
        since the last DSDA update.
        """
        # Only resync wads if they were never synced on current machine,
        # otherwise the sync would mess with the highest wad number
        if not os.path.isfile(self.HIGHEST_WAD_FILE_NAME):
            self.sync_wads()

        with open(self.HIGHEST_WAD_FILE_NAME)\
                as highest_wad_file:
            highest_wad_number = highest_wad_file.read().strip()

        # Checks all wad pages from the next wad number after the highest
        next_wad = int(highest_wad_number) + 1
        new_wads_added = False
        while True:
            cur_url = 'http://doomedsda.us/wad{}.html'.format(next_wad)
            tree = hf.get_web_page_html(cur_url)
            # Wad title on DSDA has no class or id, but always is a th
            # element and always uses colspan="5"
            title = tree.xpath('//th[@colspan="5"]')
            wad_name = title[0][0].text_content()
            # If a wad page does not exist on DSDA, the wad name is empty
            if not wad_name:
                break
            new_wads_added = True
            guessed_compat = self._guess_compat_by_wad_url_list([cur_url])
            self._wad_name_to_compat_dict[wad_name] = guessed_compat[0]
            with open('wad_name_to_compat.txt', 'a') as wad_name_to_compat_file:
                wad_name_to_compat_file.write('{wad_name}={compat}\n'.format(
                    wad_name=wad_name,
                    compat=guessed_compat[0]
                ))
            next_wad += 1

        # Re-sort file if new wads were added
        if new_wads_added:
            hf.sort_file(self.WAD_NAME_TO_COMPAT_FILE_NAME)

    def get_last_update_date(self):
        """Gets last update date from DSDA"""
        tree = hf.get_web_page_html(self.UPDATES_URL)
        date_span = tree.xpath('//span[@class="date"]')
        return date_span[0].text

    def get_last_update_info(self):
        """Gets last update info from DSDA

        Retrieves date and demo count info as well as info on new players and
        wads
        """
        if not self._wad_name_to_url_dict:
            if os.path.isfile(self.WAD_NAME_TO_URL_FILE_NAME):
                with io.open(self.WAD_NAME_TO_URL_FILE_NAME, encoding='utf8')\
                        as wad_name_to_url_file:
                    wad_mappings = wad_name_to_url_file.readlines()

                for wad_map in wad_mappings:
                    wad, url = wad_map.rsplit('=')
                    self._wad_name_to_url_dict[wad] = url
                    self._url_to_wad_name_dict[url] = wad
            else:
                self.sync_wads()
        if not self._player_name_to_url_dict:
            if os.path.isfile(self.PLAYER_NAME_TO_URL_FILE_NAME):
                with io.open(self.PLAYER_NAME_TO_URL_FILE_NAME, encoding='utf8')\
                        as player_name_to_url_file:
                    player_mappings = player_name_to_url_file.readlines()

                for player_map in player_mappings:
                    player, url = player_map.rsplit('=')
                    self._player_name_to_url_dict[player.lower()] = url
                    self._url_to_player_name_dict[url.rstrip('\n')] = player
                    # Ugly way to keep track of the original spelling for player
                    # names for error message printing
                    self._player_lowercase_to_original_dict[player.lower()] = player
            else:
                self.sync_players()

        tree = hf.get_web_page_html(self.UPDATES_URL)
        date_span = tree.xpath('//span[@class="date"]')
        demos = tree.xpath('//span[@class="lmp"]')
        demo_count = len(demos)
        new_players = []
        for demo in demos:
            demo_info_text = demo.text_content()
            player_name = demo_info_text.split(' by ')[-1]
            if player_name.lower() not in self._player_name_to_url_dict:
                new_players.append(player_name)

        return_dict = {
            'update_date': date_span[0].text,
            'demo_count': demo_count,
            'new_players': list(set(new_players))
        }
        return return_dict

    def get_player_stats(self, player_name):
        """Gets player stats for given player name

        Top-level function which ensures that the player to URL dictionary
        exists before calling the main function.
        """
        if not player_name:
            return None, 'Please provide a player name!'
        if not self._player_name_to_url_dict:
            if os.path.isfile(self.PLAYER_NAME_TO_URL_FILE_NAME):
                with io.open(self.PLAYER_NAME_TO_URL_FILE_NAME, encoding='utf8')\
                        as player_name_to_url_file:
                    player_mappings = player_name_to_url_file.readlines()

                for player_map in player_mappings:
                    player, url = player_map.rsplit('=')
                    self._player_name_to_url_dict[player.lower()] = url
                    self._url_to_player_name_dict[url.rstrip('\n')] = player
                    # Ugly way to keep track of the original spelling for player
                    # names for error message printing
                    self._player_lowercase_to_original_dict[player.lower()] = player
            else:
                self.sync_players()

        return self._get_player_stats(player_name)

    def _get_player_stats(self, player_name):
        """Gets player stats for given player name, helper function

        Iterates over every run on the player page for the given player name
        and obtains following stats:
          - run count
          - total time
          - average time
          - maximum recorded wad
          - maximum recorded category
          - average runs per wad
          - TAS run count

        Run count and total time follow the DSDA convention of excluding
        FDAs. Calls a helper function to perform a smarter search for the
        player name in the dictionary.
        """
        player_page_tuple = self._get_player_page(player_name)
        if player_page_tuple[0] is None:
            player_name_no_spaces = player_name.replace(' ', '')
            player_page_tuple = self._get_player_page(player_name_no_spaces)
            if player_page_tuple[0] is None:
                return player_page_tuple

        # All demo rows on DSDA have these classes
        rows = player_page_tuple[0].xpath('//tr[@class="row1" or @class="row2" or'
                                          '@class="row1top" or @class="row2top"]')
        run_count = 0
        tas_run_count = 0
        time_list = []
        num_distinct_wads = 0
        wad_to_run_count_dict = {}
        category_to_run_count_dict = {}
        # First row is always the header row for the table, so it is skipped
        for row in rows[1:]:
            if len(row) > 2:
                if len(row) > 3:
                    # On the player page, row1top and row2top are always
                    # as headers for new wads
                    if (row.get('class') == 'row1top'
                            or row.get('class') == 'row2top'):
                        wad_name = row[0][0].text
                        num_distinct_wads += 1
                    category = row[-4].text
                time_text = row[-1].text_content()
                if 'TAS' in time_text:
                    tas_run_count += 1
                # Skip FDAs according to DSDA run count/total time logic
                if category.strip() != 'FDA':
                    run_count += 1

                    time_text = time_text.split()[0]
                    time_list.append(hf.str_to_timedelta(time_text))
                    if category in category_to_run_count_dict:
                        category_to_run_count_dict[category] += 1
                    else:
                        category_to_run_count_dict[category] = 1
                    if wad_name in wad_to_run_count_dict:
                        wad_to_run_count_dict[wad_name] += 1
                    else:
                        wad_to_run_count_dict[wad_name] = 1

        max_category = hf.max_tuple_dict(category_to_run_count_dict, 1)
        max_wad = hf.max_tuple_dict(wad_to_run_count_dict, 1)
        if len(wad_to_run_count_dict):
            average_runs_per_wad = round(sum(wad_to_run_count_dict.values()) /
                                         len(wad_to_run_count_dict))
        else:
            average_runs_per_wad = 0
        total_time = hf.format_timedelta(hf.total_time(time_list))
        average_time = hf.format_timedelta(hf.average_time(time_list))
        longest_time = hf.format_timedelta(hf.longest_time(time_list))
        print(category_to_run_count_dict)

        return_dict = {
            'player_name': player_page_tuple[1],
            'total_run_count': run_count,
            'tas_run_count': tas_run_count,
            'num_distinct_wads': num_distinct_wads,
            'max_category': max_category,
            'max_wad': max_wad,
            'average_runs_per_wad': average_runs_per_wad,
            'total_time': total_time,
            'average_time': average_time,
            'longest_time': longest_time
        }

        return return_dict, ''

    def _get_player_page(self, player_name):
        """Returns web page for given player name

        If the player name is not found in the dictionary, the
        function will check if it is in the manually generated aliases
        dictionary, and will perform a substring search across all
        names and aliases.
        """
        player_name_sanitized = player_name.lower().rstrip()
        if player_name_sanitized in self._player_name_to_url_dict:
            return (hf.get_web_page_html(self._player_name_to_url_dict[player_name_sanitized]),
                    self._player_lowercase_to_original_dict[player_name_sanitized])
        else:
            possible_options = []
            for possible_player in self._player_name_to_url_dict:
                if player_name_sanitized in possible_player:
                    possible_options.append(
                        self._player_lowercase_to_original_dict[possible_player]
                    )

            with open('config/player_aliases_partial.yaml', encoding='utf-8') \
                    as player_aliases_yaml_file:
                player_aliases_dict = yaml.load(player_aliases_yaml_file)

            aliases_used = {}
            for cur_player_name, cur_player_aliases in player_aliases_dict.items():
                for player_alias in cur_player_aliases:
                    # Kind of ugly logic to ensure that if an exact match is
                    # found in the aliases dictionary, it will always return
                    # the exact match for short name cases such as "Cyb".
                    player_alias_lower = player_alias.lower()
                    if player_name_sanitized == player_alias_lower:
                        possible_options = [cur_player_name]
                        break
                    if player_name_sanitized in player_alias_lower:
                        possible_options.append(cur_player_name)
                        aliases_used[cur_player_name] = player_alias
            if possible_options:
                possible_options = list(set(possible_options))
                num_possible_options = len(possible_options)
                if num_possible_options == 1:
                    return hf.get_web_page_html(
                        self._player_name_to_url_dict[possible_options[0].lower().rstrip()]
                    ), possible_options[0]
                else:
                    possible_options.sort()
                    if num_possible_options > 20:
                        return None, 'Found {} matching players!'.format(num_possible_options)
                    error_string = 'Found {} matching players! Possible players:\n'.format(
                        num_possible_options
                    )
                    count = 1
                    for option in possible_options:
                        error_string = '{prev_error}  {count}: {option}\n'.format(
                            prev_error=error_string,
                            count=count,
                            option=option
                        )
                        if option in aliases_used:
                            error_string = '{prev_error} ({alias})\n'.format(
                                prev_error=error_string.rstrip('\n'),
                                alias=aliases_used[option]
                            )
                        count += 1
                    return None, error_string.rstrip('\n')
            else:
                return None, 'No matching player found!'

    def get_wad_stats(self, wad_name):
        """Gets wad stats for given wad name

        Top-level function which ensures that the wad to URL dictionary
        exists before calling the next function
        """
        if not wad_name:
            return None, 'Please provide a wad name!'
        if not self._wad_name_to_url_dict:
            if os.path.isfile(self.WAD_NAME_TO_URL_FILE_NAME):
                with io.open(self.WAD_NAME_TO_URL_FILE_NAME, encoding='utf8')\
                        as wad_name_to_url_file:
                    wad_mappings = wad_name_to_url_file.readlines()

                for wad_map in wad_mappings:
                    wad, url = wad_map.rsplit('=')
                    self._wad_name_to_url_dict[wad] = url
                    self._url_to_wad_name_dict[url.rstrip('\n')] = wad
            else:
                self.sync_wads()

        return self._get_wad_stats(wad_name)

    def _get_wad_stats(self, wad_name):
        """Gets wad stats for given wad name, first helper function

        First helper function that selects set of URLs that correspond to
        a particular wad. Usually, this is just one URL, but for paginated
        wads, it has to figure out what all the pages are.
        """
        wad_url_tuple = self._get_wad_url(wad_name)
        wad_url = wad_url_tuple[0]
        if not wad_url:
            return wad_url_tuple
        if wad_url_tuple[1] in self.PAGINATED_WADS:
            wad_urls = self._get_wad_urls_for_paginated_wad(wad_url)
            return self._get_wad_stats_from_urls(wad_urls, wad_url_tuple[1])
        else:
            return self._get_wad_stats_from_urls([wad_url], wad_url_tuple[1])

    def _get_wad_stats_from_urls(self, wad_urls, wad_name):
        """Gets wad stats for given set of wad URLs, second helper function

        Iterates over every run on the wad page for the given wad name
        and obtains following stats:
          - run count
          - total time
          - average time
          - number of distinct players
          - player with the most runs

        Run count and total time follow the DSDA convention of excluding
        FDAs.
        """
        run_count = 0
        time_list = []
        player_to_run_count_dict = {}
        category = None
        for wad_url in wad_urls:
            rows = self._get_demo_rows_for_wad_url(wad_url)
            # First row is always the header row for the table, so it is skipped
            for row in rows[1:]:
                if len(row) > 2:
                    if len(row) > 3:
                        category = row[-4].text
                    player_name = None
                    time_text = row[-1].text_content()
                    # Skip FDAs according to DSDA run count/total time logic
                    if category and category.strip() != 'FDA':
                        run_count += 1
                        player_name = row[-3].text

                        time_text = time_text.split()[0]
                        time_list.append(hf.str_to_timedelta(time_text))
                    if player_name is not None:
                        if player_name in player_to_run_count_dict:
                            player_to_run_count_dict[player_name] += 1
                        else:
                            player_to_run_count_dict[player_name] = 1

        max_player = hf.max_tuple_dict(player_to_run_count_dict, 1)
        total_time = hf.format_timedelta(hf.total_time(time_list))
        average_time = hf.format_timedelta(hf.average_time(time_list))
        num_distinct_players = len(player_to_run_count_dict)

        return_dict = {
            'wad_name': wad_name,
            'total_run_count': run_count,
            'num_distinct_players': num_distinct_players,
            'max_player': max_player,
            'total_time': total_time,
            'average_time': average_time
        }

        return return_dict, ''

    def get_record(self, wad_name, category, map_number=None):
        """Gets record for given wad name, category, and map number

        Top-level function which ensures that the wad to URL and wad to compat
        dictionaries exist before calling the next function
        """
        if not wad_name or not category:
            return None, 'Please provide a wad name and category!'
        if not self._wad_name_to_url_dict:
            if os.path.isfile(self.WAD_NAME_TO_URL_FILE_NAME):
                with io.open(self.WAD_NAME_TO_URL_FILE_NAME, encoding='utf8')\
                        as wad_name_to_url_file:
                    wad_mappings = wad_name_to_url_file.readlines()

                for wad_map in wad_mappings:
                    wad, url = wad_map.rsplit('=')
                    self._wad_name_to_url_dict[wad] = url
                    self._url_to_wad_name_dict[url.rstrip('\n')] = wad
            else:
                self.sync_wads()
        if not self._wad_name_to_compat_dict:
            if os.path.isfile(self.WAD_NAME_TO_COMPAT_FILE_NAME):
                with io.open(self.WAD_NAME_TO_COMPAT_FILE_NAME, encoding='utf8') \
                        as wad_name_to_compat_file:
                    wad_mappings = wad_name_to_compat_file.readlines()

                for wad_map in wad_mappings:
                    wad, compat = wad_map.rsplit('=')
                    self._wad_name_to_compat_dict[wad] = compat.strip()
            else:
                # If the wad to compat dictionary is not cached, this will not
                # automatically generate the dictionary because it takes too
                # long
                return None, 'Please sync the wad compats first!'

        return self._get_record(wad_name, category, map_number)

    def _get_record(self, wad_name, category, map_number=None):
        """Gets record for given wad/category/map number, first helper function

        This helper function performs some preliminary checks to ensure that
        the record retrieval request is valid and then figures out the wad URL
        that needs to be parsed to obtain the info on the record before calling
        the next helper function.
        """
        # Regex to sanitize category and map number strings, removes all
        # non-alphanumeric characters, does not test for uppercase
        # characters because the strings are converted to lowercase before
        # applying this regex
        alphabet_regex = re.compile(r'[^a-z0-9]')
        short_map_number_regex = re.compile(r'^[0-9][0-9]?s?$')
        short_s_map_number_regex = re.compile(r'^s[0-9]$')
        cat_sanitized = alphabet_regex.sub('', category.lower())
        if map_number:
            map_number_sanitized = alphabet_regex.sub('', map_number.lower())
            if (re.match(short_map_number_regex, map_number_sanitized) or
                    re.match(short_s_map_number_regex, map_number_sanitized)):
                map_number_sanitized = 'map{}'.format(map_number_sanitized.zfill(2))
        else:
            map_number_sanitized = None
        if cat_sanitized in self.VALID_CATEGORIES:
            wad_url_tuple = self._get_wad_url(wad_name)
            wad_compat_tuple = self._get_wad_compat(wad_name)
            wad_url = wad_url_tuple[0]
            if wad_url is None:
                return wad_url_tuple
            wad_compat = wad_compat_tuple[0]
            if wad_compat is None:
                return wad_compat_tuple
            if wad_name in self.PAGINATED_WADS:
                wad_url_to_search = None
                tree = hf.get_web_page_html(wad_url)
                # Gets the second table on a page, which will always exist for
                # paginated wads as the first is the demo table and the second is
                # the navigation table
                tables = tree.xpath('//table')
                rows = tables[1].xpath('.//tr[@class="row1" or @class="row2"]')
                if map_number:
                    map_number_not_secret = map_number_sanitized.rstrip('s')
                    for row in rows:
                        for col in row:
                            # Sometimes columns in the table will be blank for padding
                            if len(col):
                                if map_number_not_secret == col.text_content().lower():
                                    page_url = col[0].get('href')
                                    wad_url_to_search = 'http://doomedsda.us/{}'.format(page_url)
                                    break
                if not wad_url_to_search:
                    wad_url_to_search = wad_url
                return self._search_for_record(wad_url_to_search,
                                               wad_compat,
                                               self.VALID_CATEGORIES[cat_sanitized],
                                               map_number_sanitized)
            else:
                return self._search_for_record(wad_url,
                                               wad_compat,
                                               self.VALID_CATEGORIES[cat_sanitized],
                                               map_number_sanitized)
        else:
            return None, 'Invalid category name!'

    def _search_for_record(self, wad_url, wad_compat, categories, map_number=None):
        """Gets a record based on compat/category/map number on single URL

        This retrieves a record for a wad URL for the correct category or set of
        categories and map number.

        If it is given a a list of one category, it will return the top time
        for that category, otherwise it will return the minimum time across
        all categories given (needed for any category where multiple categories
        satisfy the requirements).

        If the map number is set to None, it will return the time for the first
        map.

        It will only return the top time if it is not co-op, not TAS, and the
        port used matches the guessed compatibility of the wad. For
        simplicity's sake, it will return any run for wads with an unknown
        compat and will always return PrBoom runs even if complevel is not set.
        """
        rows = self._get_demo_rows_for_wad_url(wad_url)
        in_right_map = False
        in_right_category = False
        possible_times = []
        for row in rows[1:]:
            time_tuple = None
            if len(row) > 2:
                if in_right_map:
                    # If the next map has been encountered (a row with at least
                    # five columns), then all possible records have been found.
                    if len(row) > 4:
                        break
                    else:
                        if len(row) > 3:
                            found_category = row[0].text
                            if in_right_category:
                                # If the next category is encountered (a row with
                                # at least four columns), and it's not one of the
                                # categories wanted, set current category to wrong.
                                if found_category not in categories:
                                    in_right_category = False
                                    continue
                                time_tuple = self._valid_check_record(row, wad_compat)
                            else:
                                # Keep checking that the category is the one needed
                                # for all category rows (length greater than 3)
                                if found_category in categories:
                                    in_right_category = True
                                    time_tuple = self._valid_check_record(row, wad_compat)
                else:
                    # Map number rows all have five columns or more
                    if len(row) > 4:
                        found_category = row[1].text
                        if not map_number or row[0].text.lower() == map_number.lower():
                            in_right_map = True
                        if in_right_map and found_category in categories:
                            time_tuple = self._valid_check_record(row, wad_compat)
                            in_right_category = True
                if time_tuple:
                    if found_category == categories[0]:
                        time_tuple.append(None)
                    else:
                        time_tuple.append(self.DSDA_CATEGORIES_TO_FIXED_NAMES[found_category])
                    possible_times.append(time_tuple)

        if not possible_times:
            if map_number:
                error_string = 'No run for given wad, category, and map combination!'
            else:
                error_string = 'No run for given wad and category!'
            return None, error_string
        else:
            return min(possible_times, key=self._time_tuple_to_comparable), ''

    @classmethod
    def _valid_check_record(cls, row, wad_compat):
        """Check if record is valid for given time and wad

        Ensures that the demo is not TAS or co-op and ensures that the port
        matches the compatibility of the wad, or is PrBoom, or the wad
        compatibility is unknown.
        """
        time = row[-1].text_content()
        # Check that time is not TAS and not co-op, and
        # the player element is length zero for co-op runs
        # that are not tagged with 'CO'
        if ('TAS' not in time and
                'CO' not in time and
                not len(row[-3])):
            url_prefix = row[-1][0].get('href')
            demo_url = 'http://doomedsda.us/{}'.format(url_prefix)
            if wad_compat == 'Unknown':
                return time.split()[0], row[-3].text, demo_url
            port = row[-2].text
            for port_regex in cls.EXECUTABLE_REGEXES:
                if re.match(port_regex, port):
                    if (cls.EXECUTABLE_REGEXES[port_regex] == 'PrBoom' or
                            wad_compat == cls.EXECUTABLE_REGEXES[port_regex]):
                        return [time.split()[0], row[-3].text, demo_url]

        return None

    @staticmethod
    def _time_tuple_to_comparable(time_tuple):
        """Make time tuple comparable

        Take the first entry of the time tuple (always the time), remove
        all colons, and convert to int to make it easy to compare tuples
        """
        return int(time_tuple[0].replace(':', ''))

    def random_wad_page(self):
        """Gets random wad page from DSDA"""
        if not self._wad_name_to_url_dict:
            if os.path.isfile(self.WAD_NAME_TO_URL_FILE_NAME):
                with io.open(self.WAD_NAME_TO_URL_FILE_NAME, encoding='utf8')\
                        as wad_name_to_url_file:
                    wad_mappings = wad_name_to_url_file.readlines()

                for wad_map in wad_mappings:
                    wad, url = wad_map.rsplit('=')
                    self._wad_name_to_url_dict[wad] = url
                    self._url_to_wad_name_dict[url.rstrip('\n')] = wad
            else:
                self.sync_wads()

        with open(self.HIGHEST_WAD_FILE_NAME)\
                as highest_wad_file:
            highest_wad_number = highest_wad_file.read().strip()
        random_wad_number = randint(1, int(highest_wad_number))
        random_wad_url = 'http://doomedsda.us/wad{}.html'.format(
            random_wad_number
        )
        return random_wad_url, self._url_to_wad_name_dict[random_wad_url]

    def random_player_page(self):
        """Gets random player page from DSDA"""
        if not self._player_name_to_url_dict:
            if os.path.isfile(self.PLAYER_NAME_TO_URL_FILE_NAME):
                with io.open(self.PLAYER_NAME_TO_URL_FILE_NAME, encoding='utf8')\
                        as player_name_to_url_file:
                    player_mappings = player_name_to_url_file.readlines()

                for player_map in player_mappings:
                    player, url = player_map.rsplit('=')
                    self._player_name_to_url_dict[player.lower()] = url
                    self._url_to_player_name_dict[url.rstrip('\n')] = player
                    # Ugly way to keep track of the original spelling for player
                    # names for error message printing
                    self._player_lowercase_to_original_dict[player.lower()] = player
            else:
                self.sync_players()

        with open(self.HIGHEST_PLAYER_FILE_NAME) \
                as highest_player_file:
            highest_player_number = highest_player_file.read().strip()
        random_player_number = randint(1, int(highest_player_number))
        random_player_url = 'http://doomedsda.us/player{}lmps.html'.format(
            random_player_number
        )
        return (random_player_url,
                self._url_to_player_name_dict[random_player_url])
