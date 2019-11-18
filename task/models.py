from django.db import models


class Task(models.Model):

    CHOICES = [
        ('run_parser', 'Run Parser And Get All Data'),
        ('get_fresh_links', 'Get Only Fresh Links From SiteMap'),
        ('get_news', 'Get News Only'),
        ('get_columns', 'Get Columns Only'),
        ('get_articles', 'Get Articles Only'),
        ('count_images', 'Show Count Images'),
        ('count__total_news', 'Show Number Of News In DB'),
        ('count__articles', 'Show Number Of Articles in DB'),
        ('count__columns', 'Show Number Of Columns in DB'),
        ('count__categories', 'How Many Categories In DB'),
        ('count__author', 'How Many Authors'),
    ]

    task = models.CharField(max_length=255, choices=CHOICES)
    status = models.CharField(max_length=255, null=True, blank=True)
    arg = models.CharField(max_length=255, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.task
