"""Self-contained regression tests. Run: python -m unittest discover -s tests -v"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from compare_openapi import compare, read_document, resolve


def api(path='/items', method='get', *, params=None, body=None, response=None):
    return {'openapi': '3.1.0','info': {'title':'test','version':'1'},'paths':{path:{method:{'parameters':params or [],'responses':response if response is not None else {'200':{'description':'ok'}}, **({'requestBody':body} if body else {})}}}}


def codes(a,b):
    return {x['code'] for x in compare(a,b)}


class Tests(unittest.TestCase):
    def test_operation_removed(self):
        self.assertIn('operation-removed',codes(api(),api('/other')))

    def test_required_query(self):
        new=api(params=[{'name':'token','in':'query','required':True,'schema':{'type':'string'}}])
        self.assertIn('required-parameter-added',codes(api(),new))

    def test_optional_query_nonbreaking(self):
        new=api(params=[{'name':'page','in':'query','required':False,'schema':{'type':'integer'}}])
        self.assertFalse(compare(api(),new))

    def test_request_required_property(self):
        body=lambda req: {'required':True,'content':{'application/json':{'schema':{'type':'object','properties':{'id':{'type':'string'}},'required':req}}}}
        self.assertIn('new-required-request-property',codes(api(method='post',body=body([])),api(method='post',body=body(['id']))))

    def test_narrowed_enum(self):
        p=lambda vals: [{'name':'mode','in':'query','schema':{'type':'string','enum':vals}}]
        self.assertIn('request-enum-narrowed',codes(api(params=p(['a','b'])),api(params=p(['a']))))

    def test_success_status_removed(self):
        self.assertIn('response-status-removed',codes(api(response={'201':{'description':'created'}}),api(response={'200':{'description':'ok'}})))

    def test_response_required_property_removed(self):
        def response(props):
            return {'200':{'description':'ok','content':{'application/json':{'schema':{'type':'object','properties':props,'required':['id']}}}}}
        self.assertIn('response-property-removed',codes(api(response=response({'id':{'type':'string'}})),api(response=response({}))))

    def test_reference_pointer(self):
        doc={'components':{'schemas':{'Thing/One':{'type':'string'}}}}
        self.assertEqual(resolve(doc,{'$ref':'#/components/schemas/Thing~1One'})['type'],'string')

    def test_external_ref_is_unresolved(self):
        item={'$ref':'https://invalid.example/schema.json'}
        self.assertEqual(resolve({},item),item)

    def test_cli_exit_status_and_json(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            (d/'old.json').write_text(json.dumps(api()))
            (d/'new.json').write_text(json.dumps(api('/new')))
            cmd=[sys.executable,str(ROOT/'scripts'/'compare_openapi.py'),'--old',str(d/'old.json'),'--new',str(d/'new.json'),'--format','json']
            p=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(p.returncode,2,p.stderr)
            self.assertEqual(json.loads(p.stdout)['summary']['breaking'],1)

    def test_invalid_input_errors(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'bad.json';file.write_text('{')
            with self.assertRaises(Exception):read_document(file)


if __name__=='__main__':
    unittest.main()
