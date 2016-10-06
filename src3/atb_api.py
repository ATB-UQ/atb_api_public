
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
import yaml
import json
import pickle
from copy import deepcopy
from sys import stderr
import inspect
from sys import stderr

MISSING_VALUE = Exception('Missing value')
INCORRECT_VALUE = Exception('Incorrect value')

def stderr_write(a_str):
    stderr.write('API Client Debug: ' + a_str + '\n')

def deserializer(api_format):
    if api_format == 'json':
        deserializer = json.loads
    elif api_format == 'yaml':
        deserializer = yaml.load
    elif api_format == 'pickle':
        deserializer = pickle.loads
    else:
        raise Exception('Incorrect API serialization format.')
    return deserializer

class API(object):

    HOST = 'https://atb.uq.edu.au'
    TIMEOUT = 45
    API_FORMAT = 'yaml'
    ENCODING = 'utf-8'

    def encoded(self, something):
        if type(something) == dict:
            return {self.encoded(key): self.encoded(value) for (key, value) in something.items()}
        elif type(something) in (str, int):
            return something.encode(self.ENCODING)
        elif something == None:
            return something
        else:
            raise Exception(
                '''Can't uncode object of type {0}: {1}'''.format(
                    type(something),
                    something,
                )
            )

    def safe_urlopen(self, url, data={}, method='GET'):
        data['api_token'] = self.api_token
        data['api_format'] = self.api_format
        try:
            if method == 'GET':
                url = url + '?' + urlencode(data)
                data = None
            elif method == 'POST':
                url = url
                data = data
            else:
                raise Exception('Unsupported HTTP method: {0}'.format(method))
            if self.debug:
                print('Querying: {url}'.format(url=url), file=stderr)

            response = urlopen(url, timeout=self.timeout, data=self.encoded(urlencode(data)) if data else None)
        except Exception as e:
            stderr_write("Failed opening url: {0}{1}{2}".format(
                url,
                '?' if data else '',
                urlencode(data) if data else '',
            ))
            if e and 'fp' in e.__dict__: stderr_write( "Response was: {0}".format(e.fp.read()) )
            raise e
        return response

    def __init__(self, host=HOST, api_token=None, debug=False, timeout=TIMEOUT, api_format=API_FORMAT):
        self.host = host
        self.api_token = api_token
        self.api_format = api_format
        self.debug = debug
        self.timeout = timeout
        self.Molecules = Molecules(self)
        self.deserializer = deserializer(api_format)
# 

# 

# 


# 

# 

# 

# 

class RMSD(API):

    def __init__(self, api):
        self.api = api

    def url(self, api_endpoint):
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

    def align(self, **kwargs):
        assert 'molids' in kwargs or ('reference_pdb' in kwargs and 'pdb_0' in kwargs), MISSING_VALUE
        if 'molids' in kwargs:
            if type(kwargs['molids']) in (list, tuple):
                kwargs['molids'] = ','.join(map(str, kwargs['molids']))
            else:
                assert ',' in kwargs['molids']
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='POST')
        return self.api.deserializer(response.read())

    def matrix(self, **kwargs):
        assert 'molids' in kwargs or ('reference_pdb' in kwargs and 'pdb_0' in kwargs), MISSING_VALUE
        if 'molids' in kwargs:
            if type(kwargs['molids']) in (list, tuple):
                kwargs['molids'] = ','.join(map(str, kwargs['molids']))
            else:
                assert ',' in kwargs['molids']
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='POST')
        return self.api.deserializer(response.read())

# 

class Molecules(API):

    def __init__(self, api):
        self.api = api
        self.download_urls = {
            'pdb_aa': ('download_file', dict(outputType='top', file='pdb_allatom_optimised', ffVersion="54A7"),),
            'pdb_allatom_unoptimised': ('download_file', dict(outputType='top', file='pdb_allatom_unoptimised', ffVersion="54A7"),),
            'pdb_ua': ('download_file', dict(outputType='top', file='pdb_uniatom_optimised', ffVersion="54A7"),),
            'yml': ('generate_mol_data', dict(),),
            'mtb_aa': ('download_file', dict(outputType='top', file='mtb_allatom', ffVersion="54A7"),),
            'mtb_ua': ('download_file', dict(outputType='top', file='mtb_uniatom', ffVersion="54A7"),),
            'itp_aa': ('download_file', dict(outputType='top', file='rtp_allatom', ffVersion="54A7"),),
            'itp_ua': ('download_file', dict(outputType='top', file='rtp_uniatom', ffVersion="54A7"),),
        }

    def url(self, api_endpoint):
        return self.api.host + '/api/current/' + self.__class__.__name__.lower() + '/' + api_endpoint + '.py'

    def search(self, **kwargs):
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        data = self.api.deserializer(response.read())
        return [ATB_Mol(self.api, m) for m in data['molecules']]

    def download_file(self, **kwargs):

        def write_to_file_or_return(response, deserializer):
            # Either write response to file 'fnme', or return its content
            if 'fnme' in kwargs:
                fnme = kwargs['fnme']
                with open(fnme, 'w') as fh:
                    fh.write( response.read() )
            else:
                return deserializer(response.read())

        if all([ key in kwargs for key in ('atb_format', 'molid')]):
            # Construct donwload.py request based on requested file format
            atb_format = kwargs['atb_format']
            call_kwargs = dict([(key, value) for (key, value) in list(kwargs.items()) if key not in ('atb_format',)])
            api_endpoint, extra_parameters = self.download_urls[atb_format]
            url = self.url(api_endpoint)
            response = self.api.safe_urlopen(url, data=dict(list(call_kwargs.items()) + list(extra_parameters.items())), method='GET')
            deserializer = (self.api.deserializer if atb_format == 'yml' else lambda x: x)
        else:
            # Forward all the keyword arguments to download_file.py
            response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
            deserializer = lambda x: x
        return write_to_file_or_return(response, deserializer)

    def duplicated_inchis(self, **kwargs):
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        return self.api.deserializer(response.read())['InChIs']

    def generate_mol_data(self, **kwargs):
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs, method='GET')
        return self.api.deserializer(response.read())

# 

    def molid(self, molid=None):
        parameters = dict(molid=molid)
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=parameters, method='GET')
        data = self.api.deserializer(response.read())
        return ATB_Mol(self.api, data['molecule'])

# 

    def submit(self, **kwargs):
        assert all([ arg in kwargs for arg in ('netcharge', 'pdb', 'public', 'moltype') ])
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs)
        return self.api.deserializer(response.read())

    def submit_TI(self, **kwargs):
        assert all([ arg in kwargs for arg in ('fe_method', 'fe_solvent', 'unique_id', 'molid', 'target_uncertainty') ])
        response = self.api.safe_urlopen(self.url(inspect.stack()[0][3]), data=kwargs)
        return response.read()

# 

class ATB_Mol(object):
    def __init__(self, api, molecule_dict):
        self.api = api
        self.molid = molecule_dict['molid']
        self.n_atoms = molecule_dict['atoms']
        self.has_TI = molecule_dict['has_TI']
        self.iupac = molecule_dict['iupac']
        self.common_name = molecule_dict['common_name']
        self.inchi = molecule_dict['InChI']
        self.experimental_solvation_free_energy = molecule_dict['experimental_solvation_free_energy']
        self.curation_trust = molecule_dict['curation_trust']
        self.pdb_hetId = molecule_dict['pdb_hetId']
        self.netcharge = molecule_dict['netcharge']
        self.formula = molecule_dict['formula']
        self.is_finished = molecule_dict['is_finished']
#       

    def download_file(self, **kwargs):
        if 'molid' in kwargs: del kwargs['molid']
        return self.api.Molecules.download_file(molid=self.molid, **kwargs)

    def generate_mol_data(self, **kwargs):
        if 'molid' in kwargs: del kwargs['molid']
        return self.api.Molecules.generate_mol_data(molid=self.molid, **kwargs)

# 

    def __repr__(self):
        self_dict = deepcopy(self.__dict__)
        del self_dict['api']
        return yaml.dump(self_dict)

def test_api_client():
    api = API(api_token='<put your token here>', debug=True, api_format='yaml', host='https://atb.uq.edu.au')

    TEST_RMSD = True
    ETHANOL_MOLIDS = [15608, 23009, 26394]

    if TEST_RMSD:
        print(api.RMSD.matrix(molids=ETHANOL_MOLIDS))
        print(api.RMSD.align(molids=ETHANOL_MOLIDS[0:2]))
        print(
            api.RMSD.align(
                reference_pdb=api.Molecules.download_file(atb_format='pdb_aa', molid=ETHANOL_MOLIDS[0]),
                pdb_0=api.Molecules.download_file(atb_format='pdb_aa', molid=ETHANOL_MOLIDS[1]),
            ),
        )

    print(api.Molecules.search(any='cyclohexane', curation_trust=0))
    print(api.Molecules.search(any='cyclohexane', curation_trust='0,2'))
    mols = api.Molecules.search(any='cyclohexane', curation_trust='0,2')
    print([mol.curation_trust for mol in mols])

    water_molecules = api.Molecules.search(formula='H2O')
    print(water_molecules)
    for mol in water_molecules:
        print(mol.iupac, mol.molid)
    #print(water_molecules[0].download_file(fnme='test.mtb', atb_format='mtb_aa'))
    print(api.Molecules.download_file(atb_format='yml', molid=21))
    print(api.Molecules.download_file(atb_format='mtb_aa', molid=21, refresh_cache=True))

    exit()

# 

if __name__ == '__main__':
    test_api_client()
