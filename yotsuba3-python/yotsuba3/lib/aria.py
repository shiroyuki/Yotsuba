from yotsuba3.core import net
from yotsuba import XML

class Feeds(list):
    @staticmethod
    def makeFromRSSFeed(url, type = 'rss'):
        rssFeedData = net.http.get(url)
        rssFeed = XML(rssFeedData)
        rssItems = rssFeed.get("item").list()
        rssFeeds = Feeds()
        for item in rssItems:
            title = item.get('title').data()
            link = item.get('link').data()
            comments = item.get('comments').data()
            publishedData = item.get('pubDate').data()
            categories = []
            for category in item.get('category').list():
                categories.append(category.data())
            rssFeeds.append(RSSFeed(title, link, categories, comments, publishedData))
        return rssFeeds

class RSSFeed(object):
    def __init__(self, title, link, categories = None, comments = None, publishedData = None):
        self.title = title
        self.link = link
        self.categories = categories
        self.comments = comments
        self.publishedData = publishedData
    