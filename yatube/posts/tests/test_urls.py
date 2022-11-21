from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsUrlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название для теста',
            slug='slug',
            description='Описание для теста',
        )
        cls.author = User.objects.create_user(
            username='Пользователь для теста'
        )
        cls.no_author = User.objects.create_user(
            username='Не зареганный юзер'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост для теста',
            group=cls.group,
        )

        cls.index = ('posts:index', None)
        cls.group_page = ('posts:group_list', [cls.post.group.slug])
        cls.profile = ('posts:profile', [cls.author])
        cls.detail = ('posts:post_detail', [cls.post.id])
        cls.create = ('posts:create_post', None)
        cls.edit = ('posts:post_edit', [cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.no_author_client = Client()
        self.no_author_client.force_login(self.no_author)

    def test_urls_guest_user_private(self):
        """
        Проверка на доступнотсь ссылок гостевому пользователю
        """
        url_names = [
            self.index,
            self.group_page,
            self.profile,
            self.detail,
        ]

        for url in url_names:
            with self.subTest(url=url):
                template_address, argument = url
                response = self.guest_client.get(reverse(
                    template_address, args=argument
                ))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Проверка несуществующих страниц"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_auth_user_private(self):
        """
        Проверка на доступнотсь ссылок авторизованному пользователю
        """
        url_names = [
            self.index,
            self.group_page,
            self.profile,
            self.detail,
            self.create,
        ]

        for url in url_names:
            with self.subTest(url=url):
                template_address, argument = url
                response = self.no_author_client.get(reverse(
                    template_address, args=argument
                ))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_auth_user_private(self):
        """
        Проверка на доступнотсь ссылок авторизованному пользователю
        """
        url_names = [
            self.create,
            self.edit,
        ]

        for url in url_names:
            with self.subTest(url=url):
                template_address, argument = url
                response = self.guest_client.get(reverse(
                    template_address, args=argument
                ))
                self.assertRedirects(response, reverse(
                    'users:login')
                    + "?next=" + reverse(
                        template_address, args=argument)
                )

    def test_post_edit_url(self):
        """проверка доступности страниц только автору."""

        template_address, argument = self.edit
        response = self.authorized_client.get(reverse(
            template_address, args=argument
        ))

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_redirect(self):
        template_address, argument = self.edit
        response = self.no_author_client.get(reverse(
            template_address, args=argument
        ))
        self.assertRedirects(response, (reverse(
            'posts:post_detail', args=[self.post.id]
        )))

    def test_post_edit_redirect_login(self):
        template_address, argument = self.edit
        response = self.guest_client.get(reverse(
            template_address, args=argument
        ))
        self.assertRedirects(
            response, reverse(
                'users:login'
            ) + "?next=" + reverse(
                template_address, args=argument)
        )

    def test_urls_use_correct_template(self):
        templates_url_names_public = [
            (
                'posts/index.html',
                self.index
            ),
            (
                'posts/group_list.html',
                self.group_page
            ),
            (
                'posts/profile.html',
                self.profile
            ),
            (
                'posts/post_detail.html',
                self.detail
            ),
            (
                'posts/create_post.html',
                self.create
            ),
            (
                'posts/create_post.html',
                self.edit
            )
        ]
        """Проверка на то что URL-адрес использует подходящий шаблон."""
        for template, reverse_name in templates_url_names_public:
            with self.subTest():
                template_address, argument = reverse_name
                response = self.authorized_client.get(reverse(
                    template_address, args=argument
                ))
                self.assertTemplateUsed(response, template)
