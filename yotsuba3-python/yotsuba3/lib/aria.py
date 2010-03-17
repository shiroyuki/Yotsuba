from yotsuba3.core import net
from yotsuba import XML

import re
import time

class Feeds(list):
    @staticmethod
    def makeFromRSSFeed(url, type = 'rss', cacheLocation = None):
        rssFeedData = net.http.get(url, cacheLocation = cacheLocation)
        rssFeed = XML(rssFeedData)
        rssItems = rssFeed.get("item").list()
        rssFeeds = Feeds()
        for item in rssItems:
            title = item.get('title').data()
            link = item.get('link').data()
            comments = item.get('comments').data()
            publishedDate = item.get('pubDate').data()
            categories = []
            for category in item.get('category').list():
                categories.append(category.data())
            rssFeeds.append(RSSFeed(title, link, categories, comments, publishedDate))
        rssFeeds.sort()
        rssFeeds.reverse()
        return rssFeeds

class RSSFeed(object):
    def __init__(self, title, link, categories = None, comments = None, publishedDate = None):
        self.title = title
        self.link = link
        self.categories = categories
        self.comments = comments
        self.publishedDate = re.sub("\+0000", "GMT", publishedDate)
        self.publishedDateTO = time.strptime(publishedDate, "%a, %d %b %Y %H:%M:%S +0000")
    
    def __le__(self, other):
        return self.publishedDateTO <= other.publishedDateTO
    
    def __lt__(self, other):
        return self.publishedDateTO < other.publishedDateTO