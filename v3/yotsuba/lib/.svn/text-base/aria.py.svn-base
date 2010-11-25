from yotsuba.core import net
from yotsuba.lib.kotoba import Kotoba

import re
import time

class Feeds(list):
    @staticmethod
    def make_from_rss_feed(url, cacheLocation = None):
        rssFeedData = net.Http.get(url).content()
        return Feeds.make_from_rss_feed_data(rssFeedData)
    
    @staticmethod
    def make_from_rss_feed_data(rssFeedData):
        rssFeed = Kotoba(rssFeedData)
        rssItems = rssFeed.get("item")
        rssFeeds = Feeds()
        for item in rssItems:
            title = item.get('title').data()
            link = item.get('link').data()
            description = item.get('description').data()
            comments = item.get('comments').data()
            publishedDate = item.get('pubDate').data()
            rssFeeds.append(RSSFeed(title, link, description, comments, publishedDate))
        rssFeeds.sort()
        rssFeeds.reverse()
        return rssFeeds

class RSSFeed(object):
    def __init__(self, title, link, description = None, comments = None, publishedDate = None):
        self.title = title
        self.link = link
        self.description = description
        self.comments = comments
        try:
            self.publishedDate = re.sub("[+-].+$", "", publishedDate).strip()
            self.publishedDateTO = time.strptime(self.publishedDate, "%a, %d %b %Y %H:%M:%S")
        except:
            raise Exception("[%s]" % self.description)
    
    def __le__(self, other):
        return self.publishedDateTO <= other.publishedDateTO
    
    def __lt__(self, other):
        return self.publishedDateTO < other.publishedDateTO