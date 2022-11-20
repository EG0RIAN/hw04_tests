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
        cls.templates_url_names_public = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug},
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': cls.author.username},
            ),
        }

        cls.templates_url_names_private = {
            'posts/create_post.html': reverse('posts:create_post')
        }

        cls.templates_url_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug},
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': cls.author.username},
            ),
        }

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
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.post.group.slug]),
            reverse('posts:profile', args=[self.author]),
            reverse('posts:post_detail', args=[self.post.pk]),
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        

    def test_urls_auth_user_private(self):
        """
        Проверка на доступнотсь ссылок авторизованному пользователю и редирект
        недоступных страниц.
        """
        url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.post.group.slug]),
            reverse('posts:profile', args=[self.author]),
            reverse('posts:post_detail', args=[self.post.pk]),
            reverse('posts:create_post'),
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_auth_user_private(self):
        """
        Проверка на доступнотсь ссылок авторизованному пользователю и редирект
        недоступных страниц.
        """
        url_names = [
            reverse('posts:create_post'),
            reverse('posts:post_edit', args=[self.post.pk]),
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, reverse(
                    'users:login')
                    + "?next=" + url
                )

    def test_home_url_exists_for_author(self):
        """проверка доступности страниц только автору."""
        url_names = [
            reverse('posts:post_edit', args=[self.post.pk]),
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                if self.post.author == self.authorized_client:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

                elif self.author == self.authorized_client:
                    self.assertRedirects(response, url)

                else:
                    response = self.guest_client.get(url)
                    self.assertRedirects(
                        response, reverse(
                            'users:login'
                        ) + "?next=" + reverse(
                            'posts:post_edit', args=[self.post.pk])
                    )

    def test_urls_guest_user_public(self):
        """
        Проверка на доступность ссылок гостевому пользователю и редирект
        доступных страниц.
        """
        for template, reverse_name in self.templates_url_names_public.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_authorized_user(self):
        """Проверка ссылок авторизованному пользователю - автору поста."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_use_correct_template(self):
        """Проверка на то что URL-адрес использует подходящий шаблон."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
