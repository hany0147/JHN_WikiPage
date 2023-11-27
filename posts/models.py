from django.db import models

# Create your models here.

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    related_post = models.ManyToManyField('self', through='RelatedPost', symmetrical=False)


class TotalWord(models.Model):
    word = models.CharField(max_length=256)
    count = models.IntegerField(default=1)


class PostDetail(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    word = models.ForeignKey(TotalWord, on_delete=models.CASCADE)
    frequency = models.IntegerField()
    association = models.FloatField(null=True) # 삭제 요망?


class RelatedPost(models.Model):
    from_post = models.ForeignKey(Post, related_name='from_related_posts', on_delete=models.CASCADE)
    to_post = models.ForeignKey(Post, related_name='to_related_posts',on_delete=models.CASCADE)
    association = models.FloatField() # 빈도합이면 integerfield로 수정할 필요 있음