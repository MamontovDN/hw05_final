import os
import re
from time import sleep
from django.conf import settings as st
from django.core.cache import cache
from django.test import TestCase, Client
from .models import User, Post, Group
from django.urls import reverse


class TestStringMethods(TestCase):
    def setUp(self):
        self.client = Client()
        self.client_not_auth = Client()
        self.client2 = Client()
        self.client_blogger = Client()
        self.user = User.objects.create_user(
            username='test',
            first_name='test',
            last_name='tester',
            email='test@test.com',
            password='test'
        )
        self.user2 = User.objects.create_user(
            username='test1',
            first_name='test1',
            last_name='tester1',
            email='test1@test.com',
            password='test'
        )
        self.blogger = User.objects.create_user(
            username='blogger',
            first_name='Famous',
            last_name='Star',
            email='blogger@mail.com',
            password='test'
        )
        self.client.force_login(self.user)
        self.client2.force_login(self.user2)
        self.client_blogger.force_login(self.blogger)

    def content_valid(self, post):
        # check main page
        cache.clear()
        response = self.client.get(reverse('index'))
        index_post = response.context['page'][0]
        self.assertEqual(post.text,
                         index_post.text,
                         msg='Некорректный текст последнего поста на гл стр')
        self.assertEqual(post.group,
                         index_post.group,
                         msg='Некорректная группа последнего поста на гл стр')
        self.assertEqual(post.author,
                         index_post.author,
                         msg='Некорректный автор последнего поста на гл стр')
        self.assertEqual(post.pub_date,
                         index_post.pub_date,
                         msg='Некорректная дата последнего поста на гл стр')
        # check profile page
        response = self.client.get(
            reverse('profile', args=[self.user.username]))
        profile_post = response.context['page'][0]
        self.assertEqual(post.text,
                         profile_post.text,
                         msg='Некорректный текст последнего '
                             'поста на личной стр')
        self.assertEqual(post.group,
                         profile_post.group,
                         msg='Некорректная группа последнего '
                             'поста на личной стр')
        self.assertEqual(post.author,
                         profile_post.author,
                         msg='Некорректный автор последнего '
                             'поста на личной стр')
        self.assertEqual(post.pub_date,
                         profile_post.pub_date,
                         msg='Некорректная дата последнего '
                             'поста на личной стр')
        # check post page
        response = self.client.get(
            reverse('post', args=[self.user.username, post.id]))
        single_post = response.context['post']
        self.assertEqual(post.text,
                         single_post.text,
                         msg='Некорректный текст последнего '
                             'поста на стр одиночного поста')
        self.assertEqual(post.group,
                         single_post.group,
                         msg='Некорректная группа последнего '
                             'поста на стр одиночного поста')
        self.assertEqual(post.author,
                         single_post.author,
                         msg='Некорректный автор последнего '
                             'поста на стр одиночного поста')
        self.assertEqual(post.pub_date,
                         single_post.pub_date,
                         msg='Некорректная дата последнего '
                             'поста на стр одиночного поста')

    def test_profile(self):
        response = self.client.get(
            reverse('profile', args=[self.user.username]),
            follow=True)
        self.assertEqual(response.status_code,
                         200,
                         msg='после регистрации нет профиля'
                         )

    def test_new_post(self):
        response = self.client.get(
            reverse('new_post'),
            follow=True)
        self.assertEqual(response.status_code,
                         200,
                         msg='Нет доступа к странице создания записи'
                         )
        Group.objects.create(
            title='test1',
            slug='t1',
            description="it's test1 group"
        )
        groups = ['', '1']
        for i in range(2):
            response = self.client.post(reverse('new_post'),
                                        {
                                            'text': f'test_text {i}',
                                            'group': groups[i]
                                        },
                                        follow=True)

            self.assertEqual(response.status_code,
                             200,
                             msg=f'Ошибка создания записи #{i}'
                             )
            self.assertRedirects(
                response,
                reverse('index'),
                msg_prefix='Не перенаправлен на главную страницу'
            )
            post = Post.objects.latest('id')
            self.assertEqual(post.text, f'test_text {i}',
                             msg=f'Некорректное сохранение текста #{i}')
            group = Group.objects.get(pk=int(groups[i])) if groups[i] else None
            self.assertEqual(post.group, group,
                             msg=f'Некорректное сохранение группы #{i}')

    def test_non_auth_new_post(self):
        response = self.client_not_auth.get(
            reverse('new_post'),
            follow=True)
        self.assertRedirects(
            response,
            '%s?next=%s' % (reverse('login'), reverse('new_post')),
            msg_prefix='Неавторизованный полтзователь'
                       ' не перенаправлен на вход'
        )
        response = self.client_not_auth.post(
            reverse('new_post'),
            {
                'text': "non auth user's text",
                'group': ''
            },
            follow=True
        )
        self.assertRedirects(
            response,
            '%s?next=%s' % (reverse('login'), reverse('new_post')),
            msg_prefix='При отправке пост-запроса не '
                       'авторизированный пользователь '
                       'не был перенаправлен на страницу логина'
        )

    def test_text_content(self):
        self.client.post(reverse('new_post'),
                         {
                             'text': 'test_text ABC',
                             'group': ['']
                         },
                         follow=True)
        post = Post.objects.latest('id')
        self.content_valid(post)

    def test_edit_post(self):
        self.client.post(reverse('new_post'),
                         {
                             'text': 'test_text ABCs',
                             'group': ['']
                         },
                         follow=True)
        post = Post.objects.latest('id')
        response = self.client_not_auth.get(
            reverse('post_edit', args=[self.user.username, post.id]),
            follow=True)
        self.assertRedirects(
            response,
            '%s?next=%s' % (reverse('login'),
                            reverse('post_edit',
                                    args=[self.user.username,
                                          post.id])),
            msg_prefix='При попытке редактирования не '
                       'авторизованный пользователь '
                       'не был перенаправлен на страницу авторизации'
        )
        response = self.client2.post(
            reverse('post_edit', args=[self.user.username, post.id]),
            {'text': 'text wrong user', 'group': ''},
            follow=True
        )
        illegal_edit = response.context['post']
        self.assertEqual(post.text,
                         illegal_edit.text,
                         msg='пост отредактирован не автором'
                         )
        self.assertEqual(post.group,
                         illegal_edit.group,
                         msg='пост отредактирован не автором'
                         )
        response = self.client.post(
            reverse('post_edit', args=[self.user.username, post.id]),
            {'text': 'new text after post edit', 'group': ''},
            follow=True
        )
        self.assertRedirects(response,
                             reverse('post',
                                     args=[self.user.username, post.id]),
                             msg_prefix='Не перенаправлен на страницу поста'
                             )
        post = Post.objects.latest('id')
        self.content_valid(post)

    def test_404(self):
        response = self.client.get('/unknown_address/', follow=True)
        self.assertEqual(response.status_code, 404,
                         msg='Сервер не вернул 404 при '
                             'вызове несуществующей ошибки')

    def test_post_img(self):
        cache.clear()
        path_img = os.path.join(st.BASE_DIR, 'media/posts/320.jpg')
        with open(path_img, 'rb') as im:
            response = self.client.post(
                reverse('new_post'),
                {'text': 'test_text', 'image': im},
                follow=True
            )
        # check index
        html = response.content.decode()
        self.assertIsNotNone(re.search(r'img.*src=.*\.jpg', html),
                             msg='Не найдена картинка на гл стр')
        # check profile
        response = self.client.get(
            reverse('profile', args=[self.user.username])
        )
        html = response.content.decode()
        self.assertIsNotNone(re.search(r'img.*src=.*\.jpg', html),
                             msg='Не найдена картинка на личн стр')
        # check post
        post_id = Post.objects.latest('id').id
        response = self.client.get(
            reverse('post', args=[self.user.username, post_id])
        )
        html = response.content.decode()
        self.assertIsNotNone(re.search(r'img.*src=.*\.jpg', html),
                             msg='Не найдена картинка на стр поста')
        # check wrong file extension
        with open(os.path.join(st.BASE_DIR, 'requirements.txt'), 'rb') as im:
            response = self.client.post(
                reverse('new_post'),
                {'text': 'wrong format', 'image': im},
            )
            wrong_format_post_id = Post.objects.latest('id').id
            self.assertEqual(
                post_id,
                wrong_format_post_id,
                msg='Добавлен пост с неверным форматом картинки')

    def test_cache(self):
        self.client.post(reverse('new_post'),
                         {'text': 'test test test'},
                         follow=True)
        response = self.client.post(reverse('new_post'),
                                    {'text': 'test cache'},
                                    follow=True)
        self.assertNotContains(response, 'test cache',
                               msg_prefix='кэширование не работает')

        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'test cache',
                            msg_prefix='записи нет ')

    def test_subscribe(self):
        cache.clear()
        # non-auth follow
        # ===============================================================
        response = self.client_not_auth.get(
            reverse('profile_follow', args=[self.blogger.username]),
            follow=True
        )
        self.assertRedirects(
            response,
            '%s?next=%s' % (reverse('login'),
                            reverse('profile_follow',
                                    args=[self.blogger.username])),
            msg_prefix='при подписки неавторизов. '
                       'польз. нет redirect на login'
        )
        # auth follow
        # ===============================================================
        self.client.get(
            reverse('profile_follow', args=[self.blogger.username]),
            follow=True
        )
        self.assertTrue(
            self.user.follower.filter(author=self.blogger).exists(),
            msg='Нет подписки'
        )
        response = self.client.get(
            reverse('profile', args=[self.blogger.username]),
            follow=True
        )
        self.assertContains(
            response,
            'Отписаться',
            msg_prefix='Кнопка подписки не изменилась'
        )
        # test follow-index
        # ===============================================================
        self.client_blogger.post(
            reverse('new_post'),
            {'text': 'for followers'},
            follow=True
        )
        response = self.client.get(reverse('follow_index'), follow=True)
        self.assertContains(
            response,
            'for followers',
            msg_prefix='Нет текста в ленте подписок'
        )
        response = self.client2.get(reverse('follow_index'), follow=True)
        self.assertNotContains(
            response,
            'for followers',
            msg_prefix='текст в ленте не от автора из подписки'
        )
        # non-auth unfollow
        # ===============================================================
        response = self.client_not_auth.get(
            reverse('profile_unfollow', args=[self.blogger.username]),
            follow=True
        )
        self.assertRedirects(
            response,
            '%s?next=%s' % (reverse('login'),
                            reverse('profile_unfollow',
                                    args=[self.blogger.username])),
            msg_prefix='при отписки неавторизов. '
                       'польз. нет redirect на login'
        )
        # auth unfollow
        # ===============================================================
        self.client.get(
            reverse('profile_unfollow', args=[self.blogger.username]),
            follow=True
        )
        self.assertFalse(
            self.user.follower.filter(author=self.blogger).exists(),
            msg='Нет отписки'
        )
        response = self.client.get(
            reverse('profile', args=[self.blogger.username]),
            follow=True
        )
        self.assertContains(
            response,
            'Подписаться',
            msg_prefix='Кнопка отписки не изменилась'
        )

    def test_comment(self):
        # test non-auth comment
        # ===============================================================
        self.client_blogger.post(
            reverse('new_post'),
            {'text': 'for comments'},
            follow=True
        )
        post_id = Post.objects.latest('id').id
        response = self.client_not_auth.post(
            reverse('add_comment', args=[self.blogger.username, post_id]),
            {'text': 'comment'},
            follow=True
        )
        self.assertRedirects(
            response,
            '%s?next=%s' % (reverse('login'),
                            reverse('add_comment',
                                    args=[self.blogger.username, post_id])
                            ),
            msg_prefix='при комментирования неавторизов. '
                       'польз. нет redirect на login'
        )
        # test auth comment
        # ===============================================================
        self.client.post(
            reverse('add_comment', args=[self.blogger.username, post_id]),
            {'text': 'comment for blogger'},
            follow=True
        )
        response = self.client.get(
            reverse('post', args=[self.blogger.username, post_id]),
            follow=True
        )
        self.assertContains(
            response,
            'comment for blogger',
            msg_prefix='Нет комментария от пользователя'
        )
