from django.conf import settings
from django.core.paginator import Paginator


def create_pages(request, object_list):
    paginator = Paginator(object_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
