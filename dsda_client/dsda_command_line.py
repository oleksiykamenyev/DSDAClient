"""DSDA command line client

Uses an underlying class to retrieve info from DSDA by parsing the HTML, these
commands can be used via command line
"""

import shlex
import sys

from dsda_client.dsda_client_class import DSDAClient

__author__ = '4shockblast'


def main():
    """Main function"""
    print('DSDA command line client v0.3.2.')
    print('Type help for usage info.')
    exited = False
    dsda_client = DSDAClient()
    help_text = """Available commands to DSDA:
      - sync
          Sync player URL, wad URL, and wad compatibility guesses to a local cache.
      - get_record <wad_name> <category> (<map_number>)
          Get record for given wad name, category, and map number if provided.

          If map number is not provided, the client will only search through the
          first map on the wad page.

          Map number format must be "e#m#" or "map##" or "d#ep#" or "d#all".
          If the format is ##, it will be assumed to be for map##.

          Wad and category names with spaces must be put in quotes,
          e.g. "2 (1994)".
      - playerstats <player_name>
          Get player stats for player with player_name.
      - wadstats <wad_name>
          Get wad stats for wad with <wad_name>
      - random_player_page
          Returns random player page URL.
      - random_wad_page
          Returns random wad page URL.
      - last_dsda_update
          Returns last DSDA update date.
      - exit
          Exits the application.
      - help
          You're reading it."""
    while not exited:
        try:
            user_query = input('> ')
        except EOFError:
            sys.exit()
        except KeyboardInterrupt:
            print('Please type "exit" or "e" to exit the application.')
        if user_query.lower() == 'exit' or user_query.lower() == 'e':
            sys.exit()
        elif user_query.lower() == 'help' or user_query.lower() == 'h':
            print(help_text)
        elif user_query.lower() == 'sync' or user_query.lower() == 's':
            print('Starting sync. Do not interrupt the application!')
            dsda_client.sync_full()
            print('Sync completed!')
        elif (user_query.lower().startswith('get_record') or
              user_query.lower().startswith('gr ') or
              user_query.lower().startswith('g ')):
            # Split into maximum of four strings, then pad up to four with Nones
            # in case there are fewer
            user_query_split = shlex.split(user_query)[:4]
            user_query_split += [None] * (4 - len(user_query_split))
            if len(user_query_split) > 2:
                _, user_wad_name, user_category, user_map_number = user_query_split
                record_tuple = dsda_client.get_record(user_wad_name, user_category, user_map_number)
                record_info = record_tuple[0]
                if record_info is not None:
                    print('Time: {time}\nPlayer: {player}\nDemo link: {demo}'.format(
                        time=record_info[0],
                        player=record_info[1],
                        demo=record_info[2]
                    ))
                else:
                    print(record_tuple[1])
            else:
                print('Not enough options for get_record command!')
        elif (user_query.lower().startswith('playerstats') or
              user_query.lower().startswith('ps ') or
              user_query.lower().startswith('p ')):
            user_query_split = user_query.split(None, 1)
            if len(user_query_split) > 1:
                player_stats_tuple = dsda_client.get_player_stats(user_query_split[1])
                player_stats = player_stats_tuple[0]
                if player_stats:
                    if not player_stats['max_wad'][1]:
                        player_stats['max_wad'] = None, 'no'
                    if not player_stats['max_category'][1]:
                        player_stats['max_category'] = None, 'no'
                    print('Player name: {}'.format(player_stats['player_name']))
                    print('Total demo count: {}'.format(player_stats['total_run_count']))
                    print('Total demo time: {}'.format(player_stats['total_time']))
                    print('Longest demo: {}'.format(player_stats['longest_time']))
                    print('Average demo time: {}'.format(player_stats['average_time']))
                    print('Total TAS demo count: {}'.format(player_stats['tas_run_count']))
                    print('Average demos recorded per wad: {}'.format(
                        player_stats['average_runs_per_wad']
                    ))
                    print('Number of distinct wads recorded for: {}'.format(
                        player_stats['num_distinct_wads']
                    ))
                    print('Maximum recorded wad: {}, {} demos'.format(
                        player_stats['max_wad'][0],
                        player_stats['max_wad'][1]
                    ))
                    print('Maximum recorded category: {}, {} demos'.format(
                        player_stats['max_category'][0],
                        player_stats['max_category'][1]
                    ))
                else:
                    print(player_stats_tuple[1])
            else:
                print('Not enough options for playerstats command!')
        elif (user_query.lower().startswith('wadstats') or
              user_query.lower().startswith('ws ') or
              user_query.lower().startswith('w ')):
            user_query_split = user_query.split(None, 1)
            if len(user_query_split) > 1:
                wad_stats_tuple = dsda_client.get_wad_stats(user_query_split[1])
                wad_stats = wad_stats_tuple[0]
                if wad_stats:
                    if not wad_stats['max_player'][1]:
                        wad_stats['max_player'] = None, 'no'
                    print('Wad name: {}'.format(wad_stats['wad_name']))
                    print('Total demo count: {}'.format(wad_stats['total_run_count']))
                    print('Total demo time: {}'.format(wad_stats['total_time']))
                    print('Average demo time: {}'.format(wad_stats['average_time']))
                    print('Number of players: {}'.format(wad_stats['num_distinct_players']))
                    print('Player with most demos: {}, {} demos'.format(
                        wad_stats['max_player'][0],
                        wad_stats['max_player'][1]
                    ))
                else:
                    print(wad_stats_tuple[1])
            else:
                print('Not enough options for wadstats command!')
        elif (user_query.lower() == 'random_player_page' or
              user_query.lower() == 'rpp' or
              user_query.lower() == 'rp'):
            random_player_page_tuple = dsda_client.random_player_page()
            print('{player_name}: {player_url}'.format(
                player_name=random_player_page_tuple[1],
                player_url=random_player_page_tuple[0]
            ))
        elif (user_query.lower() == 'random_wad_page' or
              user_query.lower() == 'rwp' or
              user_query.lower() == 'rw'):
            random_wad_page_tuple = dsda_client.random_wad_page()
            print('{wad_name}: {wad_url}'.format(
                wad_name=random_wad_page_tuple[1],
                wad_url=random_wad_page_tuple[0]
            ))
        elif (user_query.lower() == 'last_dsda_update' or
              user_query.lower() == 'ldu' or
              user_query.lower() == 'l'):
            print(dsda_client.get_last_update_date())
        else:
            print('Unrecognized command: {}'.format(user_query))

if (__name__ == '__main__' or
        __name__ == 'dsda_command_line__main__'):
    main()
