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

from __future__ import print_function
import argparse
import psycopg2
import re
import os
from jinja2 import Environment, FileSystemLoader
from bottle import Bottle


FOREIGN_KEY_PARSE_RE = re.compile(
    '^FOREIGN KEY \("?(.+?)"?\) REFERENCES ' +
    '"?(.+?)"?\."?(.+?)"?\("?(.+?)"?\).*$'
)


class PgStructure(object):
    def __init__(self, args):
        self.conn = psycopg2.connect(
            database=args.database,
            user=args.user,
            password=args.password,
            port=args.port,
            host=args.host
        )
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def get_schema_list(self):
        SQL = '''
SELECT
    pg_catalog.pg_namespace.nspname,
    pg_description.description
FROM pg_catalog.pg_namespace
LEFT JOIN pg_catalog.pg_description ON
    pg_description.objoid = pg_namespace.oid
;
        '''
        self.cursor.execute(SQL)
        return {
            schema: description
            for schema, description in self.cursor.fetchall()
        }

    def get_foreign_key_dict(self, schema, table):
        SQL = '''
SELECT
    pg_constraint.conname,
    pg_catalog.pg_get_constraintdef(pg_constraint.oid, true)
FROM
    pg_catalog.pg_constraint
WHERE
    pg_constraint.conrelid = (
        SELECT pg_class.oid
        FROM pg_catalog.pg_class
        LEFT JOIN pg_catalog.pg_namespace ON
            pg_namespace.oid = pg_class.relnamespace
        WHERE
            pg_namespace.nspname = '{schema}' AND
            pg_class.relname = '{table}' AND
            pg_class.relkind in ('r', 'v') LIMIT 1
    ) AND
    pg_constraint.contype = 'f'
;
        '''.format(schema=schema, table=table)
        self.cursor.execute(SQL)

        result = {}
        for k, v in self.cursor.fetchall():
            m = FOREIGN_KEY_PARSE_RE.search(v)
            result[m.group(1)] = {
                'foreign_key': k,
                'target_schema': m.group(2),
                'target_table': m.group(3),
                'target_column': m.group(4),
            }
        return result

    def get_column_list(self, schema, table):
        SQL = '''
SELECT
    pg_attribute.attname,
    pg_attribute.attnotnull,
    pg_catalog.format_type(pg_attribute.atttypid, pg_attribute.atttypmod),
    (
        SELECT pg_catalog.pg_get_expr(pg_attrdef.adbin, pg_attrdef.adrelid)
        FROM pg_catalog.pg_attrdef
        WHERE
            pg_attrdef.adrelid = pg_attribute.attrelid AND
            pg_attrdef.adnum = pg_attribute.attnum AND
            pg_attribute.atthasdef
    ) AS modifiers,
    pg_description.description
FROM pg_catalog.pg_tables
LEFT JOIN pg_catalog.pg_class ON pg_class.relname = pg_tables.tablename
LEFT JOIN pg_catalog.pg_attribute ON pg_attribute.attrelid = pg_class.oid
LEFT JOIN pg_catalog.pg_description ON
    pg_description.objsubid = pg_attribute.attnum AND
    pg_description.objoid = pg_class.oid
WHERE
    pg_tables.schemaname = '{schema}' AND
    pg_tables.tablename = '{table}' AND
    pg_attribute.attnum > 0 AND
    NOT pg_attribute.attisdropped
ORDER BY pg_attribute.attnum
;
        '''.format(schema=schema, table=table)
        self.cursor.execute(SQL)
        return [{
            'column': column,
            'is_not_null': is_not_null,
            'type': type,
            'modifiers': modifiers,
            'description': description,
        } for
            column,
            is_not_null,
            type,
            modifiers,
            description in self.cursor.fetchall()]

    def get_table_list(self, schema):
        SQL = '''
SELECT
    pg_tables.tablename, pg_description.description
FROM pg_catalog.pg_tables
LEFT JOIN pg_catalog.pg_class ON pg_class.relname = pg_tables.tablename
LEFT JOIN pg_catalog.pg_description ON
    pg_class.oid = pg_description.objoid AND
    pg_description.objsubid = 0
WHERE pg_tables.schemaname = '{}'
ORDER BY pg_tables.tablename
;
        '''.format(schema)
        self.cursor.execute(SQL)
        return {
            table: description
            for table, description in self.cursor.fetchall()
        }

    def read_schema_and_tables(self):
        SQL = '''SELECT schemaname, tablename FROM pg_catalog.pg_tables;'''
        self.cursor.execute(SQL)


class Server(object):
    def __init__(self, args):
        self.args = args
        self.environment = (lambda p: Environment(
            loader=FileSystemLoader('{}/templates'.format(p), encoding='utf8')
        ))(os.path.dirname(os.path.abspath(__file__)))
        self._app = Bottle()
        self._route()

    def _route(self):
        for (path, params) in [
                ('/', {
                    'method': 'GET', 'callback': self.schema_list
                }),
                ('/schema/<schema>', {
                    'method': 'GET', 'callback': self.table_list
                }),
                ('/schema/<schema>/table/<table>', {
                    'method': 'GET', 'callback': self.column_list
                }), ]:
            self._app.route(path, **params)

    def render(self, template, params):
        return self.environment.get_template(template).render(**params)


    def schema_list(self):
        pg_structure = PgStructure(self.args)
        schema_list = pg_structure.get_schema_list().items()
        pg_structure.close()

        return self.render('schema_list.html', {
            'title': 'Schema list',
            'schema_list': schema_list,
        })

    def table_list(self, schema):
        pg_structure = PgStructure(self.args)
        table_list = pg_structure.get_table_list(schema).items()
        pg_structure.close()

        return self.render('table_list.html', {
            'title': 'Table list',
            'schema': schema,
            'table_list': table_list,
        })

    def column_list(self, schema, table):
        pg_structure = PgStructure(self.args)
        foreign_key_dict = pg_structure.get_foreign_key_dict(schema, table)

        column_list = []
        for column in pg_structure.get_column_list(schema, table):
            column['foreign_key'] = self.render(
                'foreign_key_link.html',
                foreign_key_dict[column['column']]
            ) if column['column'] in foreign_key_dict else None

            column_list.append(column)
        pg_structure.close()

        return self.render('column_list.html', {
            'title': 'Column list',
            'schema': schema,
            'table': table,
            'column_list': column_list,
        })

    def start(self):
        self._app.run(host='0.0.0.0', port=8765)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate reStructuredText from PostgreSQL'
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


if __name__ == '__main__':
    Server(parse_args()).start()
