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

import psycopg2
import re


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
LEFT JOIN pg_catalog.pg_description ON pg_description.objoid = pg_namespace.oid
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
            pg_namespace.nspname = %(schema)s
            AND pg_class.relname = %(table)s
            AND pg_class.relkind IN ('r', 'v')
        LIMIT 1
    ) AND
    pg_constraint.contype = 'f'
;
'''
        self.cursor.execute(SQL, {
            'schema': schema,
            'table': table,
        })

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
            pg_attrdef.adrelid = pg_attribute.attrelid
            AND pg_attrdef.adnum = pg_attribute.attnum
            AND pg_attribute.atthasdef
    ) AS modifiers,
    pg_description.description
FROM pg_catalog.pg_tables
LEFT JOIN pg_catalog.pg_class ON pg_class.relname = pg_tables.tablename
LEFT JOIN pg_catalog.pg_attribute ON pg_attribute.attrelid = pg_class.oid
LEFT JOIN pg_catalog.pg_description ON
    pg_description.objsubid = pg_attribute.attnum
    AND pg_description.objoid = pg_class.oid
WHERE
    pg_tables.schemaname = %(schema)
    AND pg_tables.tablename = %(table)
    AND pg_attribute.attnum > 0
    AND NOT pg_attribute.attisdropped
ORDER BY pg_attribute.attnum
;
'''
        self.cursor.execute(SQL, {
            'schema': schema,
            'table': table,
        })
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
    pg_tables.tablename,
    pg_description.description
FROM pg_catalog.pg_tables
LEFT JOIN pg_catalog.pg_class ON pg_class.relname = pg_tables.tablename
LEFT JOIN pg_catalog.pg_description ON
    pg_class.oid = pg_description.objoid
    AND pg_description.objsubid = 0
WHERE pg_tables.schemaname = %(schema)s
ORDER BY pg_tables.tablename
;
'''
        self.cursor.execute(SQL, {
            'schema': schema,
        })
        return {
            table: description
            for table, description in self.cursor.fetchall()
        }

    def read_schema_and_tables(self):
        SQL = '''
SELECT schemaname, tablename FROM pg_catalog.pg_tables;
'''
        self.cursor.execute(SQL)
