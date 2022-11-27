from rest_framework.pagination import PageNumberPagination

from foodgram.settings import REST_FRAMEWORK  # isort:skip


class PageNumberLimitPagination(PageNumberPagination):
    """
    To customize pagination with 'limil' query param.
    """

    page_size = REST_FRAMEWORK['PAGE_SIZE']
    page_size_query_param = 'limit'
