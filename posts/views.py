from django.shortcuts import render, redirect
from .models import Post, TotalWord, PostDetail, RelatedPost
from .forms import PostForm
from sklearn.feature_extraction.text import CountVectorizer
from pprint import pprint
from django.db.models import F, Sum

def index(request):
    posts = Post.objects.all().order_by('-created_at')

    context = {
        'posts': posts,
    }

    return render(request, 'posts/index.html', context)

def create_related_posts(post):
    total_posts_count = Post.objects.count()
    threshold = total_posts_count * 0.6
    excluded = TotalWord.objects.filter(count__gt=threshold).values_list('word', flat=True)

    core_words = PostDetail.objects.filter(post=post).exclude(word__in=excluded).values_list('word__word', flat=True)
    if not core_words:
        return False
    
    related_posts = []
    other_posts = Post.objects.exclude(pk=post.pk)
    for other_post in other_posts:
        
        other_words = PostDetail.objects.filter(post=other_post).exclude(word__in=excluded).values_list('word__word', flat=True)
        common_words = set(core_words) & set(other_words)

        if len(common_words) >= 2:
            tmp = 0
            for common_word in common_words:
                post_association = PostDetail.objects.filter(post=post, word__word=common_word).values_list('association', flat=True).first()
                other_post_frequency = PostDetail.objects.filter(post=other_post, word__word=common_word).values_list('frequency', flat=True).first()
                tmp += post_association * other_post_frequency

            related_post = RelatedPost(from_post=post, to_post=other_post, association=tmp)

            related_posts.append(related_post)

    return RelatedPost.objects.bulk_create(related_posts)


def create(request):
    if request.method == 'POST':
        
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save()

            # 단어 저장
            content = [request.POST['content'].lower()]
            vectorizer = CountVectorizer()
            frequency = vectorizer.fit_transform(content)
            words = vectorizer.get_feature_names_out()
            word_cnts = dict(zip(words, frequency.toarray()[0]))
            total = frequency.sum()
            for word, frequency in word_cnts.items():
                total_word, created = TotalWord.objects.get_or_create(word=word)
                if not created:
                    total_word.count += 1
                total_word.save()


                # 40% 미만 단어 전체 중 해당 단어의 빈도 * 100으로 추후 대체하자.
                association = frequency / total * 100
                post_detail = PostDetail(post=post, word=total_word, frequency=frequency, association=association)
                post_detail.save()

            create_related_posts(post)

            return redirect('posts:detail', post.pk)
    else:
        form = PostForm()

    context = {
        'form': form,
    }

    return render(request, 'posts/create.html', context)

def detail(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    related_posts = RelatedPost.objects.filter(from_post=post).order_by('-association')
    context = {
        'post': post,
        'related_posts': related_posts,
    }

    return render(request, 'posts/detail.html', context)