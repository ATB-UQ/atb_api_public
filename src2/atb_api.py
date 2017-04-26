from __future__ import with_statement
from __future__ import absolute_import
from urllib2 import urlopen, Request
from urllib2 import HTTPError, URLError
from urllib import urlencode
import yaml
import json
import pickle
from operator import itemgetter
from copy import deepcopy
import sys
from inspect import stack
from requests import post
from tempfile import TemporaryFile
from os.path import join
from itertools import imap

MISSING_VALUE = Exception(u'Missing value')
INCORRECT_VALUE = Exception(u'Incorrect value')




def deserializer_fct_for(api_format):
    if api_format == u'json':
        deserializer_fct = lambda x: json.loads(x)
    elif api_format == u'yaml':
        deserializer_fct = lambda x: yaml.load(x)
    elif api_format == u'pickle':
        deserializer_fct = lambda x: pickle.loads(x)
    else:
        raise Exception(u'Incorrect API serialization format.')
    return deserializer_fct

def truncate_str_if_necessary(a_str, max_length = 1000):
    if len(a_str) <= max_length:
        return a_str
    else:
        return a_str[:1000] + u'...[truncated]'

def concat_dicts(*args):
    return dict(
        reduce(
            lambda acc, e: acc + e,
            [
                list(a_dict.items())
                for a_dict in args
            ],
            [],
        ),
    )

DEFAULT_DEBUG_STREAM = sys.stderr

class API(object):
    HOST = u'https://atb.uq.edu.au'
    TIMEOUT = 45
    API_FORMAT = u'yaml'
    ENCODING = u'utf-8'

    def write_to_debug_stream(self, a_str):
        self.debug_stream.write(u'API Client Debug: ' + a_str + u'\n')

    def decode_if_necessary(self, x, encoding = u'utf8'):
        if isinstance(x, unicode):
            return x
        elif isinstance(x, str):
            try:
                return x.decode(encoding)
            except UnicodeDecodeError:
                self.write_to_debug_stream(u'Could not decode output with encoding "{0}". Returning raw bytes...'.format(encoding))
                return x
        else:
            raise Exception(u'Invalid input type: {0}'.format(type(x)))

    def encoded(self, something):
        if type(something) == dict:
            return dict((self.encoded(key), self.encoded(value)) for (key, value) in something.items())
        elif type(something) in (unicode, int, str):
            return something.encode(self.ENCODING)
        elif something == None:
            return something
        else:
            raise Exception(
                u'''Can't uncode object of type {0}: {1}'''.format(
                    type(something),
                    something,
                )
            )

    def safe_urlopen(self, url, data = {}, method = u'GET'):
        if isinstance(data, dict):
            data_items = list(data.items())
        elif type(data) in (tuple, list):
            data_items = list(data)
        else:
            raise Exception(u'Unexpected type: {0}'.format(type(data)))

        data_items += [(u'api_token', self.api_token), (u'api_format', self.api_format)]

        try:
            if method == u'GET':
                url = url + u'?' + urlencode(data_items)
                data_items = None
            elif method == u'POST':
                url = url
            else:
                raise Exception(u'Unsupported HTTP method: {0}'.format(method))
            if self.debug:
                self.write_to_debug_stream(u'Querying {url}'.format(url=url))

            if method == u'POST' and any([isinstance(value, str) or u'read' in dir(value) for (key, value) in data_items]):
                def file_for(content):
                    u'''Cast a content object to a file for request.post'''
                    if u'read' in dir(content):
                        return content
                    else:
                        file_handler = TemporaryFile(mode=u'w+b')
                        file_handler.write(
                            content if isinstance(content, str) else unicode(content).encode(),
                        )
                        file_handler.seek(0) # Rewind the files to future .read()
                        return file_handler

                files=dict(
                    [
                        (key, file_for(value))
                        for (key, value) in data_items
                    ]
                )

                request = post(
                    url,
                    files=files,
                )
                response_content = request.text

                if self.debug:
                    print u'INFO: Will send binary data.'
            else:
                response = urlopen(
                    Request(
                        url,
                        data=self.encoded(urlencode(data_items),) if data_items is not None else None,
                    ),
                    timeout=self.timeout,
                )
                if self.api_format == u'pickle':
                    response_content = response.read()
                else:
                    response_content = response.read().decode()
        except HTTPError, e:
            self.write_to_debug_stream(u'Failed opening url: "{0}{1}{2}".\nResponse was:\n"{3}"\n'.format(
                url,
                u'?' if data_items else u'',
                truncate_str_if_necessary(urlencode(data_items) if data_items else u''),
                self.decode_if_necessary(e.read()),
            ))
            raise e
        except URLError, e:
            raise Exception([url, unicode(e)])
        return response_content

    def __init__(self, host = HOST, api_token = None, debug = False, timeout = TIMEOUT, api_format = API_FORMAT, debug_stream = DEFAULT_DEBUG_STREAM):
        # Attributes
        self.host = host
        self.api_token = api_token
        self.api_format = api_format
        self.debug = debug
        self.debug_stream = debug_stream
        self.timeout = timeout
        self.deserializer_fct = deserializer_fct_for(api_format)

        # API namespaces
        self.Molecules = Molecules(self)
        self.RMSD = RMSD(self)
        self.Jobs = Jobs(self)
# 

    def deserialize(self, an_object):
        try:
            return self.deserializer_fct(an_object)
        except:
            print an_object
            raise

    TWO_FRAMES_ABOVE = itemgetter(2)
    FUNCTION_NAME = itemgetter(3)

    def url(self, api_namespace, api_endpoint = None):
        try:
            return join(
                self.host,
                u'api',
                u'current',
                api_namespace,
                (API.FUNCTION_NAME(API.TWO_FRAMES_ABOVE(stack())) if api_endpoint is None else api_endpoint) + u'.py',
            )
        except IndexError, e:
            raise Exception(u'Invalid stack in API.url(): {0}. Error was: {1}'.format(stack(), unicode(e)))

class ATB_Mol(object):
    def __init__(self, api, molecule_dict):
        self.api = api
        self.molid = molecule_dict[u'molid']
        self.n_atoms = molecule_dict[u'atoms']
        self.has_TI = molecule_dict[u'has_TI']
        self.iupac = molecule_dict[u'iupac']
        self.common_name = molecule_dict[u'common_name']
        self.inchi = molecule_dict[u'inchi']
        self.inchi_key = molecule_dict[u'inchi_key']
        self.experimental_solvation_free_energy = molecule_dict[u'experimental_solvation_free_energy']
        self.curation_trust = molecule_dict[u'curation_trust']
        self.pdb_hetId = molecule_dict[u'pdb_hetId']
        self.netcharge = molecule_dict[u'netcharge']
        self.formula = molecule_dict[u'formula']
        self.is_finished = molecule_dict[u'is_finished']
        self.rnme = molecule_dict[u'rnme']
        self.moltype = molecule_dict[u'moltype']
        self.compound_id = molecule_dict[u'compound_id']
# 

    def download_file(self, **kwargs):
        if u'molid' in kwargs: del kwargs[u'molid']
        return self.api.Molecules.download_file(molid=self.molid, **kwargs)

    def generate_mol_data(self, **kwargs):
        if u'molid' in kwargs: del kwargs[u'molid']
        return self.api.Molecules.generate_mol_data(molid=self.molid, **kwargs)

# 

    def job(self, **kwargs):
        return self.api.Molecules.job(molid=self.molid, **kwargs)

    def __repr__(self):
        return yaml.dump(
            dict((
                key, value)
                for (key, value) in self.__dict__.items()
                if key not in [u'api'])
        )

# 

# 


# 

class Jobs(API):
    def __init__(self, api):
        self.api = api

    def url(self, api_endpoint = None):
        return self.api.url(self.__class__.__name__.lower(), api_endpoint=api_endpoint)

# 

    def get(self, **kwargs):
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(), data=kwargs),
        )[u'jobs']

    def new(self, **kwargs):
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(), data=kwargs),
        )[u'molids']

    def accept(self, **kwargs):
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(), data=kwargs),
        )[u'molids']

    def release(self, **kwargs):
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(), data=kwargs),
        )[u'molids']

    def finished(self, molids = [], qm_logs = [], current_qm_levels = [], method = u'POST', **kwargs):
        return self.api.deserialize(
            self.api.safe_urlopen(
                self.url(),
                data=(
                    list(kwargs.items())
                    +
                    [(u'molid', molid) for molid in molids]
                    +
                    [(u'qm_log', qm_log) for qm_log in qm_logs]
                    +
                    [(u'current_qm_level', current_qm_level) for current_qm_level in current_qm_levels]
                ),
                method=method,
            ),
        )[u'accepted_molids']

    def sync(self, method = u'GET', **kwargs):
        return self.api.deserialize(
            self.api.safe_urlopen(self.url(), data=kwargs, method=method),
        )

# 

# 

class RMSD(API):

    def __init__(self, api):
        self.api = api

    def url(self, api_endpoint = None):
        return self.api.url(self.__class__.__name__.lower(), api_endpoint=api_endpoint)

    def align(self, **kwargs):
        assert u'molids' in kwargs or (u'reference_pdb' in kwargs and u'pdb_0' in kwargs), MISSING_VALUE
        if u'molids' in kwargs:
            if type(kwargs[u'molids']) in (list, tuple):
                kwargs[u'molids'] = u','.join(imap(unicode, kwargs[u'molids']))
            else:
                assert u',' in kwargs[u'molids']
        response_content = self.api.safe_urlopen(self.url(), data=kwargs, method=u'POST')
        return self.api.deserialize(response_content)

    def matrix(self, **kwargs):
        assert u'molids' in kwargs or (u'reference_pdb' in kwargs and u'pdb_0' in kwargs), MISSING_VALUE
        if u'molids' in kwargs:
            if type(kwargs[u'molids']) in (list, tuple):
                kwargs[u'molids'] = u','.join(imap(unicode, kwargs[u'molids']))
            else:
                assert u',' in kwargs[u'molids']
        response_content = self.api.safe_urlopen(self.url(), data=kwargs, method=u'POST')
        return self.api.deserialize(response_content)

# 

# 

class Molecules(API):

    def __init__(self, api):
        self.api = api
        self.download_urls = {
            u'pdb_aa': (u'download_file', dict(outputType=u'top', file=u'pdb_allatom_optimised', ffVersion=u"54A7"),),
            u'pdb_allatom_unoptimised': (u'download_file', dict(outputType=u'top', file=u'pdb_allatom_unoptimised', ffVersion=u"54A7"),),
            u'pdb_ua': (u'download_file', dict(outputType=u'top', file=u'pdb_uniatom_optimised', ffVersion=u"54A7"),),
            u'yml': (u'generate_mol_data', dict(),),
            u'mtb_aa': (u'download_file', dict(outputType=u'top', file=u'mtb_allatom', ffVersion=u"54A7"),),
            u'mtb_ua': (u'download_file', dict(outputType=u'top', file=u'mtb_uniatom', ffVersion=u"54A7"),),
            u'itp_aa': (u'download_file', dict(outputType=u'top', file=u'rtp_allatom', ffVersion=u"54A7"),),
            u'itp_ua': (u'download_file', dict(outputType=u'top', file=u'rtp_uniatom', ffVersion=u"54A7"),),
        }

    def url(self, api_endpoint = None):
        return self.api.url(self.__class__.__name__.lower(), api_endpoint=api_endpoint)

    def search(self, **kwargs):
        return_type = kwargs[u'return_type'] if u'return_type' in kwargs else u'molecules'
        response_content = self.api.safe_urlopen(self.url(), data=kwargs, method=u'GET')
        data = self.api.deserialize(response_content)
        if return_type == u'molecules':
            return [ATB_Mol(self.api, m) for m in data[return_type]]
        elif return_type == u'molids':
            return data[return_type]
        else:
            raise Exception(u'Unknow return_type: {0}'.format(return_type))

    def download_file(self, **kwargs):

        def write_to_file_or_return(response_content, deserializer_fct):
            # Either write response to file 'fnme', or return its content
            if u'fnme' in kwargs:
                fnme = unicode(kwargs[u'fnme'])
                with open(fnme, u'w' + (u'b' if isinstance(response_content, str) else u't')) as fh:
                    fh.write(response_content)
                return None
            else:
                return deserializer_fct(response_content)

        if all([key in kwargs for key in (u'atb_format', u'molid')]):
            # Construct donwload.py request based on requested file format
            atb_format = unicode(kwargs[u'atb_format'])
            call_kwargs = dict([(key, value) for (key, value) in list(kwargs.items()) if key not in (u'atb_format',)])
            api_endpoint, extra_parameters = self.download_urls[atb_format]
            url = self.url(api_endpoint)
            response_content = self.api.safe_urlopen(url, data=concat_dicts(extra_parameters, call_kwargs), method=u'GET')
            deserializer_fct = (self.api.deserializer_fct if atb_format == u'yml' else (lambda x: x))
        else:
            # Forward all the keyword arguments to download_file.py
            response_content = self.api.safe_urlopen(self.url(), data=kwargs, method=u'GET')
            deserializer_fct = lambda x: x
        return write_to_file_or_return(response_content, deserializer_fct)

    def duplicated_inchis(self, **kwargs):
        response_content = self.api.safe_urlopen(self.url(), data=kwargs, method=u'GET')
        return self.api.deserialize(response_content)[u'inchi_key']

    def generate_mol_data(self, **kwargs):
        response_content = self.api.safe_urlopen(self.url(), data=kwargs, method=u'GET')
        return self.api.deserialize(response_content)

# 

    def molid(self, molid = None):
        parameters = dict(molid=molid)
        response_content = self.api.safe_urlopen(self.url(), data=parameters, method=u'GET')
        data = self.api.deserialize(response_content)
        return ATB_Mol(self.api, data[u'molecule'])

    def structure_search(self, method = u'POST', **kwargs):
        assert all([ arg in kwargs for arg in (u'structure', u'netcharge', u'structure_format') ])
        response_content = self.api.safe_urlopen(self.url(), data=kwargs, method=method)
        return self.api.deserialize(response_content)

# 

    def submit(self, request=u'POST', **kwargs):
        assert all([arg in kwargs for arg in (u'netcharge', u'public', u'moltype') ]) and len([True for arg in [u'pdb', u'smiles'] if arg in kwargs]) == 1
        response_content = self.api.safe_urlopen(self.url(), data=kwargs, method=request)
        return self.api.deserialize(response_content)

# 

    def job(self, **kwargs):
        return self.api.deserialize(self.api.safe_urlopen(self.url(), data=kwargs, method=u'GET'))[u'job']

def test_api_client():
    api = API(api_token=u'<put your token here>', debug=True, api_format=u'yaml', host=u'https://atb.uq.edu.au', debug_stream=sys.stderr)

    TEST_RMSD = True
    ETHANOL_MOLIDS = [15608, 23009, 26394]

# 

    if TEST_RMSD:
        print api.RMSD.matrix(molids=ETHANOL_MOLIDS)
        print api.RMSD.align(molids=ETHANOL_MOLIDS[0:2])
        print api.RMSD.align(
                reference_pdb=api.Molecules.download_file(atb_format=u'pdb_aa', molid=ETHANOL_MOLIDS[0]),
                pdb_0=api.Molecules.download_file(atb_format=u'pdb_aa', molid=ETHANOL_MOLIDS[1]),
            )

    print api.Molecules.search(any=u'cyclohexane', curation_trust=0)
    print api.Molecules.search(any=u'cyclohexane', curation_trust=u'0,2', return_type=u'molids')
    mols = api.Molecules.search(any=u'cyclohexane', curation_trust=u'0,2')
    print [mol.curation_trust for mol in mols]

    water_molecules = api.Molecules.search(formula=u'H2O')
    print water_molecules
    for mol in water_molecules:
        print mol.iupac, mol.molid
    #print(water_molecules[0].download_file(fnme='test.mtb', atb_format='mtb_aa'))
    print api.Molecules.download_file(atb_format=u'yml', molid=21)
    print api.Molecules.download_file(atb_format=u'mtb_aa', molid=21, refresh_cache=True)

    print mols[0].job(qm_level=2)

    exit()

# 

if __name__ == u'__main__':
    test_api_client()
