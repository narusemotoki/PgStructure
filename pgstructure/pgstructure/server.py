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

import os
from jinja2 import Environment, FileSystemLoader
from bottle import Bottle
from pgstructure import PgStructure


PORT = 9876


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
        self._app.run(host='0.0.0.0', port=PORT)
