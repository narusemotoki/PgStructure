#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PgStructure
Copyright (C) 2014 Motoki Naruse <motoki@naru.se>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import argparse
from server import Server


def parse_args():
    parser = argparse.ArgumentParser(
        description='You can check the database structure of PostgreSQL.'
    )
    for k, v in {
        ('--database', '--dbname', ): {
            'type': str,
            'required': True,
            'help': 'Name of your PostgreSQL',
        },
        ('--user', ): {
            'type': str,
            'help': 'User of your PostgreSQL',
        },
        ('--password', '--passwd', '--pass', ): {
            'type': str,
            'help': 'Password of user',
        },
        ('--host', '--hostname', ): {
            'type': str,
            'help': 'Hostname of your PostgreSQL',
        },
        ('--port', ): {
            'type': int,
            'default': 5432,
            'help': 'Port number of your PostgreSQL',
        },
    }.items():
        parser.add_argument(*k, **v)

    return parser.parse_args()


def main():
    Server(parse_args()).start()


if __name__ == '__main__':
    main()
