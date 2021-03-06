import requests
import time

class APIResponseError(Exception):
    """ Exception raise if the API replies with an HTTP code
    not in the 2xx range. """
    pass

class Session:
    def __init__(self):
        self.__requests_session = requests.Session()
        # self.__requests_session.headers.update({'User-Agent': 'medex'})

    def api_request(self, url, params={}, auth='', http_call='get'):

        def api_exec(url, params={}, auth='', http_call='get'):
            if http_call == 'get':
                response = self.__requests_session.get(url)
            elif http_call == 'post':
                response = self.__requests_session.post(url, data=params, auth=auth)
            return response


        resp = api_exec(url=url, params=params, auth=auth, http_call=http_call)
        while not resp.ok:
            resp = api_exec(url=url, params=params, auth=auth, http_call=http_call)
            time.sleep(0.5)

        return resp

        # if not response.ok:
        #     msg = "API response error: %s".format(response.status_code)
        #     raise APIResponseError(msg)

        # return response
