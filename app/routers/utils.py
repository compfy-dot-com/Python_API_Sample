from fastapi import HTTPException

CODE_RESPONSE_LIST = {
    201: {'description': 'Created'},
    204: {'description': 'No content'},
    400: {'description': 'Bad request'},
    409: {'description': 'Duplicate record'}
    }

def http_responses(codes):
    return {code:CODE_RESPONSE_LIST[code] for code in codes}

def http_exception(code, msg=None):
    return  HTTPException(status_code=code, 
                          detail=msg if msg else CODE_RESPONSE_LIST[code]['description'])
