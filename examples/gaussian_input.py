from atb_api import API

api = API(api_token='<ATB API TOKEN>', api_format='yaml', debug=True, timeout=60)


def get_gaussian_input(molid):
    # set optional arguments to default values
    cores = 8
    mem = "8000mb"
    gamess_input = api.QM_Calculations.gaussian_input(molid=molid, cores=cores, mem=mem)
    return gamess_input


if __name__ == "__main__":
    print(get_gaussian_input(21))
