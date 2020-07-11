from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.views.generic import UpdateView, ListView
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

from .forms import NewTopicForm, PostForm
from .models import Board, Topic, Post

# def home(request):
#     boards = Board.objects.all()
#     return render(request, 'home.html', {'boards': boards})

class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'home.html'    

## board_topics 1
# def board_topics(request, pk):
#     # board = Board.objects.get(pk=pk)
#     board = get_object_or_404(Board, pk=pk)
#     return render(request, 'topics.html', {'board': board})

# def board_topics(request, pk):
#     board = get_object_or_404(Board, pk=pk)
#     topics = board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
#     return render(request, 'topics.html', {'board': board, 'topics': topics})

# # board_topics 2
# def board_topics(request, pk):
#     board = get_object_or_404(Board, pk=pk)
#     queryset = board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
#     page = request.GET.get('page', 1)

#     paginator = Paginator(queryset, 5)

#     try:
#         topics = paginator.page(page)
#     except PageNotAnInteger:
#         # fallback to the first page
#         topics = paginator.page(1)
#     except EmptyPage:
#         # probably the user tried to add a page number
#         # in the url, so we fallback to the last page
#         topics = paginator.page(paginator.num_pages)

#     return render(request, 'topics.html', {'board': board, 'topics': topics})

# # board_topics 3
class TopicListView(ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    # paginate_by = 20
    # paginate_by = 10
    paginate_by = 3

    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.board = get_object_or_404(Board, pk=self.kwargs.get('pk'))
        queryset = self.board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
        return queryset


# class PostListView(ListView):
#     model = Post
#     context_object_name = 'posts'
#     template_name = 'topic_posts.html'
#     paginate_by = 2

#     def get_context_data(self, **kwargs):
#         self.topic.views += 1
#         self.topic.save()
#         kwargs['topic'] = self.topic
#         return super().get_context_data(**kwargs)

#     def get_queryset(self):
#         self.topic = get_object_or_404(Topic, board__pk=self.kwargs.get('pk'), pk=self.kwargs.get('topic_pk'))
#         queryset = self.topic.posts.order_by('created_at')
#         return queryset

class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_posts.html'
    # paginate_by = 20
    paginate_by = 2

    def get_context_data(self, **kwargs):

        session_key = 'viewed_topic_{}'.format(self.topic.pk)  # <-- here
        if not self.request.session.get(session_key, False):
            self.topic.views += 1
            self.topic.save()
            self.request.session[session_key] = True           # <-- until here

        kwargs['topic'] = self.topic
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic = get_object_or_404(Topic, board__pk=self.kwargs.get('pk'), pk=self.kwargs.get('topic_pk'))
        queryset = self.topic.posts.order_by('created_at')
        return queryset


@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = request.user  # <- here
            topic.save()
            Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=request.user  # <- and here
            )
            # return redirect('board_topics', pk=board.pk)  # TODO: redirect to the created topic page
            return redirect('topic_posts', pk=pk, topic_pk=topic.pk)
    else:
        form = NewTopicForm()
    return render(request, 'new_topic.html', {'board': board, 'form': form})


# def topic_posts(request, pk, topic_pk):
#     topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
#     return render(request, 'topic_posts.html', {'topic': topic})    

def topic_posts(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    topic.views += 1
    topic.save()
    return render(request, 'topic_posts.html', {'topic': topic})

## It does not show reply last_update, to change by the codes below
# @login_required
# def reply_topic(request, pk, topic_pk):
#     topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
#     if request.method == 'POST':
#         form = PostForm(request.POST)
#         if form.is_valid():
#             post = form.save(commit=False)
#             post.topic = topic
#             post.created_by = request.user
#             post.save()
#             return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
#     else:
#         form = PostForm()
#     return render(request, 'reply_topic.html', {'topic': topic, 'form': form})


# ## It will show reply last_update
# def reply_topic(request, pk, topic_pk):
#     topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
#     if request.method == 'POST':
#         form = PostForm(request.POST)
#         if form.is_valid():
#             post = form.save(commit=False)
#             post.topic = topic
#             post.created_by = request.user
#             post.save()

#             topic.last_updated = timezone.now()  # <- here
#             topic.save()                         # <- and here

#             return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
#     else:
#         form = PostForm()
#     return render(request, 'reply_topic.html', {'topic': topic, 'form': form})


@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()

            topic.last_updated = timezone.now()
            topic.save()

            topic_url = reverse('topic_posts', kwargs={'pk': pk, 'topic_pk': topic_pk})
            topic_post_url = '{url}?page={page}#{id}'.format(
                url=topic_url,
                id=post.pk,
                page=topic.get_page_count()
            )

            return redirect(topic_post_url)
    else:
        form = PostForm()
    return render(request, 'reply_topic.html', {'topic': topic, 'form': form})

class PostUpdateView(UpdateView):
    
    model = Post
    fields = ('message', )
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        return redirect('topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)    