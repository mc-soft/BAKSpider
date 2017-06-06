import os
from html.parser import HTMLParser
from urllib import parse
from urllib import request
from urllib.parse import urlsplit
from urllib.parse import urlparse

spidered_links = []

backup_extensions = ["backup", "bck", "old", "save", "bak", "sav", "~",
                     "copy", "old", "orig", "tmp", "txt", "back"]

class WebSpider(HTMLParser):
    """Class to help with our webpage operations."""
    # TODO: Calculate root rather than have it passed.
    # TODO: Remove the recursive functionality, one scan per class instance.
    def __init__(self, url, root):
        HTMLParser.__init__(self)
        self.url = url
        self.root = root
        return

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    self.parse_href(value)
        return

    def parse_href(self, link):
        # TODO: Maybe consolidate these if-statements, will have to calculate performance.
        if "://" in link:  # Check if relative or absolute
            if link.startswith("{0.scheme}://{0.netloc}/".format(urlsplit(self.root))):
                self.parse_url(link)
        else:
            url = parse.urljoin(self.root, link)
            self.parse_url(url)

        return

    def parse_url(self, url):
        parsed_url = urlparse(url)
        clean_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path

        self.spider_url(url, clean_url);
        return

    def spider_url(self, url_to_spider, file_only_url):
        if not self.is_valid_url(file_only_url):
            return

        checked_files = []

        if file_only_url not in checked_files and not file_only_url.endswith('/'):
            # Check for backups here
            print("Checking {0} for backups now::".format(file_only_url))
            #self.check_dirs_for_backups(file_only_url) # TODO: Enable this if directory scanning is enabled.
            checked_files.append(file_only_url)

        if url_to_spider not in spidered_links:
            root = url_to_spider[:url_to_spider.rfind("/") + 1]

            # Begin spidering a new page
            spidered_links.append(url_to_spider)
            WebSpider(url_to_spider, root).scan()
        return

    @staticmethod
    def is_valid_url(url):
        if url.startswith("mailto"):
            return 0

        return 1

    # TODO: Check for certain extensions (exclude PDF etc.)
    # TODO: This is still being called when the --dir option isn't specified
    def check_dirs_for_backups(self, url):
        self.check_url(url)

        filename = os.path.basename(url)
        print("Checking dirs for", filename)

        for dir_name in additional_dirs:
            dir_url = parse.urljoin(dir_name, filename)
            self.check_url(dir_url)

        input("Continue?...")

        return

    # TODO: Move backup_extensions into their own file and allow seperate argument for custom file.
    def check_url(self, url):
        # Check with original extension
        for ext in backup_extensions:
            bak_url = "{0}.{1}".format(url, ext)
            print(bak_url)

            if self.response_code(bak_url) == 200:
                print("[200 - OK] Backup found: {0}".format(bak_url))

        # Check without original extension
        url = url.rsplit('.', 1)[0]
        for ext in backup_extensions:
            bak_url = "{0}.{1}".format(url, ext)
            print(bak_url)

            if self.response_code(bak_url) == 200:
                print("[200 - OK] Backup found: {0}".format(bak_url))

    def scan(self):
        print("---###[ SCANNING {0} ]###---".format(self.url))

        body = request.urlopen(self.url)
        page_enc = body.headers.get_content_charset() or 'UTF-8'

        try:
            for line in body:
                self.feed(line.decode(page_enc))
        except UnicodeDecodeError:
            pass

    def is_accessible(self):
        return self.response_code(self.url) == 200

    # TODO: Check for redirect to 404 page (will return 200)
    # TODO: Allow custom timeout
    @staticmethod
    def response_code(url):
        try:
            return request.urlopen(url).getcode()
        except Exception as e:
            return 404