from django.conf import settings

class CommonUtils:
    def get_full_url(relative_url):
        return f'{settings.MY_SITE_SCHEME}://{settings.MY_SITE_DOMAIN}{relative_url}'