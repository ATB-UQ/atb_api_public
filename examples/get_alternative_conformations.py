from atb_api import API

# Send an email to the ATB administrators to request an API token
api = API(api_token='<ATB API TOKEN>', api_format='yaml', debug=True, timeout=60)

if __name__ == "__main__":
    confs = api.Molecules.conformations(molid=1414797)
    print(confs)
    confs = api.Molecules.conformations(molids="10,21")
    print(confs)
