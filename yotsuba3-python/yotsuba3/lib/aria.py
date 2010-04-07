from yotsuba3.core import net
from yotsuba import XML, syslog

import re
import time

class Feeds(list):
    @staticmethod
    def makeFromRSSFeed(url, cacheLocation = None):
        rssFeedData = net.http.get(url, cacheLocation = cacheLocation)
        return Feeds.makeFromRSSFeedData(rssFeedData)
    
    @staticmethod
    def makeFromRSSFeedData(rssFeedData):
        rssFeed = XML(rssFeedData)
        rssItems = rssFeed.get("item").list()
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