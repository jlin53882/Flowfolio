class PortfolioItem:
    def __init__(self, title, category, media_link="", description="", year=None):
        self.title = title
        self.category = category
        self.media_link = media_link
        self.description = description
        self.year = year

    def to_dict(self):
        return {
            "title": self.title,
            "category": self.category,
            "media_link": self.media_link,
            "description": self.description,
            "year": self.year
        }