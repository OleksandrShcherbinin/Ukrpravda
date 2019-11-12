from django.db import models


class NewsTag(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    slug = models.CharField(max_length=100, null=True, blank=True)

    objects = models.Manager()

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    slug = models.CharField(max_length=100, null=True, blank=True)

    objects = models.Manager()

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    news_text = models.TextField()
    image = models.ImageField(upload_to='images', null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    news_date = models.DateTimeField(null=True, blank=True)
    news_source = models.URLField(null=True, blank=True)
    parsing_date = models.DateTimeField(auto_created=True, null=True, blank=True)
    source_reviews = models.IntegerField()
    news_tag = models.ManyToManyField(NewsTag)

    objects = models.Manager()

    def __str__(self):
        return self.title


class Columns(models.Model):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    column_text = models.TextField()
    image = models.ImageField(upload_to='images', null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    column_date = models.DateTimeField(null=True, blank=True)
    column_source = models.URLField(null=True, blank=True)
    parsing_date = models.DateTimeField(auto_created=True, null=True, blank=True)
    source_reviews = models.IntegerField()
    moderated = models.BooleanField(default=False)
    news_tag = models.ManyToManyField(NewsTag)
    author_tag = models.ManyToManyField(Author)

    objects = models.Manager()

    def __str__(self):
        return self.title


class Article(models.Model):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    article_text = models.TextField()
    image = models.ImageField(upload_to='images', null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    article_date = models.DateTimeField(null=True, blank=True)
    article_source = models.URLField(null=True, blank=True)
    parsing_date = models.DateTimeField(auto_created=True, null=True, blank=True)
    source_reviews = models.IntegerField()
    moderated = models.BooleanField(default=False)
    news_tag = models.ManyToManyField(NewsTag)
    author_tag = models.ManyToManyField(Author)

    objects = models.Manager()

    def __str__(self):
        return self.title


class Reviews(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField()
    comment = models.TextField()
    published = models.DateTimeField(auto_now_add=True)
    moderated = models.BooleanField(default=False)

    news = models.ForeignKey(News, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ArticleReviews(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField()
    comment = models.TextField()
    published = models.DateTimeField(auto_now_add=True)
    moderated = models.BooleanField(default=False)

    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ColumnReviews(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField()
    comment = models.TextField()
    published = models.DateTimeField(auto_now_add=True)
    moderated = models.BooleanField(default=False)

    column = models.ForeignKey(Columns, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
