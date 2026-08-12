from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Tüm DRF hatalarını tutarlı bir `{"detail": ..., "errors": ...}` gövdesiyle döndürür."""
    response = exception_handler(exc, context)

    if response is None:
        return response

    data = response.data
    if isinstance(data, dict) and 'detail' in data and len(data) == 1:
        response.data = {'detail': data['detail']}
    else:
        detail = data.get('detail') if isinstance(data, dict) else None
        response.data = {
            'detail': detail or 'Doğrulama hatası oluştu.',
            'errors': data,
        }

    return response
