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
        Проверка на доступнотсь ссылок гостевому пользователю и редирект
        недоступных страниц.
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
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_auth_user_private(self):
        """
        Проверка на доступнотсь ссылок авторизованному пользователю и редирект
        недоступных страниц.
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
        Проверка на доступнотсь ссылок авторизованному пользователю и редирект
        недоступных страниц.
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

    def test_home_url_exists_for_author(self):
        """проверка доступности страниц только автору."""
        url_names = [
            self.edit,
        ]

        for url in url_names:
            with self.subTest(url=url):
                template_address, argument = url
                response = self.authorized_client.get(reverse(
                    template_address, args=argument
                ))

                if self.post.author == self.authorized_client:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

                elif self.author == self.authorized_client:
                    self.assertRedirects(response, url)

                else:
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
