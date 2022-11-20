from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

POST_PER_PAGE = 10

COUNT_RANGE = 13


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тест!',
            author=cls.user,
            group=cls.group,
        )
        cls.index = ('posts:index', None)
        cls.group_page = ('posts:group_list', ['test-slug'])
        cls.profile = ('posts: profile', [cls.user])
        cls.detail = ('posts:post_detail', [cls.post.id])
        cls.create = ('posts: post_create', None)
        cls.edit = ('posts:post_edit', [cls.post.id])


    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def posts_check_all_fields(self, post):
        """Метод, проверяющий поля поста."""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

    def test_posts_pages_use_correct_template(self):
        """Проверка, использует ли адрес URL соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_profile_show_correct_context_posts(self):
        """Шаблоны index, group_list, profile сформированы
        с правильным контекстом."""
        responses = (
        self.index,
        self.group_page,
        self. profile,
        )
        for response in responses:
            with self.subTest(response=response):
                template_address, argument = response
                first_object = self.guest_client.get(reverse(
                    template_address,args=argument
                    )
                ).context['page_obj'][0]
                context = (
                    (first_object.author, self.user),
                    (first_object.text, self.post.text),
                    (first_object.group, self.group),
                )
                for context, reverse_context in context:
                    with self.subTest(context=context):
                        self.assertEqual(context, reverse_context)

    def test_posts_context_group_list_template(self):
        """
        Проверка, сформирован ли шаблон group_list с
        правильным контекстом.
        Появляется ли пост, при создании на странице его группы.
        """
        response = self.authorized_client.get(
            self.group_page
        )
        test_group = response.context['group']
        self.posts_check_all_fields(response.context['page_obj'][0])
        test_post = str(response.context['page_obj'][0])
        self.assertEqual(test_group, self.group)

    def test_posts_context_post_create_template(self):
        """
        Проверка, сформирован ли шаблон post_create с
        правильным контекстом.
        """
        response = self.authorized_client.get(self.create_post)

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_posts_context_post_edit_template(self):
        """
        Проверка, сформирован ли шаблон post_edit с
        правильным контекстом.
        """
        response = self.authorized_client.get(
            self.post_edit
        )

        form_fields = {'text': forms.fields.CharField}

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_context_profile_template(self):
        """
        Проверка, сформирован ли шаблон profile с
        правильным контекстом.
        """
        response = self.authorized_client.get(
            self.profile
        )
        profile = {'author': self.post.author}

        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

        self.posts_check_all_fields(response.context['page_obj'][0])
        test_page = response.context['page_obj'][0]
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_posts_context_post_detail_template(self):
        """
        Проверка, сформирован ли шаблон post_detail с
        правильным контекстом.
        """
        response = self.authorized_client.get(
            self.post_detail
        )

        profile = {'post': self.post}

        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

    def test_posts_not_from_foreign_group(self):
        """
        Проверка, при указании группы поста, попадает
        ли он в другую группу.
        """
        response = self.authorized_client.get(self.index)
        self.posts_check_all_fields(response.context['page_obj'][0])
        post = response.context['page_obj'][0]
        group = post.group
        self.assertEqual(group, self.group)


class PostsPaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(COUNT_RANGE):
            cls.post = Post.objects.create(
                text=f'Тестовый текст поста номер {count}',
                author=cls.user,
            )
        cls.index = ('posts:index', None)
        cls.group_page = ('posts:group_list', ['test-slug'])
        cls.profile = ('posts: profile', [cls.user])

    def test_posts_if_first_page_has_ten_records(self):
        """Проверка, содержит ли первая страница 10 записей."""
        response = self.authorized_client.get(self.index)
        self.assertEqual(len(response.context.get('page_obj').object_list), POST_PER_PAGE)

    def test_posts_if_second_page_has_three_records(self):
        """Проверка, содержит ли вторая страница 3 записи."""
        response = self.authorized_client.get(
            self.index + '?page=2'
        )
        self.assertEqual(len(response.context.get('page_obj').object_list), 3)
