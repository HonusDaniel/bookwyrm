""" testing activitystreams """
from unittest.mock import patch
from django.test import TestCase
from bookwyrm import activitystreams, models


@patch("bookwyrm.models.activitypub_mixin.broadcast_task.delay")
@patch("bookwyrm.activitystreams.ActivityStream.add_status")
class Activitystreams(TestCase):
    """ using redis to build activity streams """

    def setUp(self):
        """ use a test csv """
        self.local_user = models.User.objects.create_user(
            "mouse", "mouse@mouse.mouse", "password", local=True, localname="mouse"
        )
        self.another_user = models.User.objects.create_user(
            "nutria", "nutria@nutria.nutria", "password", local=True, localname="nutria"
        )
        with patch("bookwyrm.models.user.set_remote_server.delay"):
            self.remote_user = models.User.objects.create_user(
                "rat",
                "rat@rat.com",
                "ratword",
                local=False,
                remote_id="https://example.com/users/rat",
                inbox="https://example.com/users/rat/inbox",
                outbox="https://example.com/users/rat/outbox",
            )
        self.book = models.Edition.objects.create(title="test book")

        class TestStream(activitystreams.ActivityStream):
            """ test stream, don't have to do anything here  """

            key = "test"

        self.test_stream = TestStream()

    def test_activitystream_class_ids(self, *_):
        """ the abstract base class for stream objects """
        self.assertEqual(
            self.test_stream.stream_id(self.local_user),
            "{}-test".format(self.local_user.id),
        )
        self.assertEqual(
            self.test_stream.unread_id(self.local_user),
            "{}-test-unread".format(self.local_user.id),
        )

    def test_abstractstream_stream_users(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.remote_user, content="hi", privacy="public"
        )
        users = self.test_stream.stream_users(status)
        # remote users don't have feeds
        self.assertFalse(self.remote_user in users)
        self.assertTrue(self.local_user in users)
        self.assertTrue(self.another_user in users)

    def test_abstractstream_stream_users_direct(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.remote_user,
            content="hi",
            privacy="direct",
        )
        status.mention_users.add(self.local_user)
        users = self.test_stream.stream_users(status)
        self.assertEqual(users, [])

        status = models.Comment.objects.create(
            user=self.remote_user,
            content="hi",
            privacy="direct",
            book=self.book,
        )
        status.mention_users.add(self.local_user)
        users = self.test_stream.stream_users(status)
        self.assertTrue(self.local_user in users)
        self.assertFalse(self.another_user in users)
        self.assertFalse(self.remote_user in users)

    def test_abstractstream_stream_users_followers_remote_user(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.remote_user,
            content="hi",
            privacy="followers",
        )
        users = self.test_stream.stream_users(status)
        self.assertFalse(users.exists())

    def test_abstractstream_stream_users_followers_self(self, *_):
        """ get a list of users that should see a status """
        status = models.Comment.objects.create(
            user=self.local_user,
            content="hi",
            privacy="direct",
            book=self.book,
        )
        users = self.test_stream.stream_users(status)
        self.assertTrue(self.local_user in users)
        self.assertFalse(self.another_user in users)
        self.assertFalse(self.remote_user in users)

    def test_abstractstream_stream_users_followers_with_mention(self, *_):
        """ get a list of users that should see a status """
        status = models.Comment.objects.create(
            user=self.remote_user,
            content="hi",
            privacy="direct",
            book=self.book,
        )
        status.mention_users.add(self.local_user)

        users = self.test_stream.stream_users(status)
        self.assertTrue(self.local_user in users)
        self.assertFalse(self.another_user in users)
        self.assertFalse(self.remote_user in users)

    def test_abstractstream_stream_users_followers_with_relationship(self, *_):
        """ get a list of users that should see a status """
        self.remote_user.followers.add(self.local_user)
        status = models.Comment.objects.create(
            user=self.remote_user,
            content="hi",
            privacy="direct",
            book=self.book,
        )
        users = self.test_stream.stream_users(status)
        self.assertFalse(self.local_user in users)
        self.assertFalse(self.another_user in users)
        self.assertFalse(self.remote_user in users)

    def test_homestream_stream_users(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.remote_user, content="hi", privacy="public"
        )
        users = activitystreams.HomeStream().stream_users(status)
        self.assertFalse(users.exists())

    def test_homestream_stream_users_with_mentions(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.remote_user, content="hi", privacy="public"
        )
        status.mention_users.add(self.local_user)
        users = activitystreams.HomeStream().stream_users(status)
        self.assertFalse(self.local_user in users)
        self.assertFalse(self.another_user in users)

    def test_homestream_stream_users_with_relationship(self, *_):
        """ get a list of users that should see a status """
        self.remote_user.followers.add(self.local_user)
        status = models.Status.objects.create(
            user=self.remote_user, content="hi", privacy="public"
        )
        users = activitystreams.HomeStream().stream_users(status)
        self.assertTrue(self.local_user in users)
        self.assertFalse(self.another_user in users)

    def test_localstream_stream_users_remote_status(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.remote_user, content="hi", privacy="public"
        )
        users = activitystreams.LocalStream().stream_users(status)
        self.assertEqual(users, [])

    def test_localstream_stream_users_local_status(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.local_user, content="hi", privacy="public"
        )
        users = activitystreams.LocalStream().stream_users(status)
        self.assertTrue(self.local_user in users)
        self.assertTrue(self.another_user in users)

    def test_localstream_stream_users_unlisted(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.local_user, content="hi", privacy="unlisted"
        )
        users = activitystreams.LocalStream().stream_users(status)
        self.assertEqual(users, [])

    def test_federatedstream_stream_users(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.remote_user, content="hi", privacy="public"
        )
        users = activitystreams.FederatedStream().stream_users(status)
        self.assertTrue(self.local_user in users)
        self.assertTrue(self.another_user in users)

    def test_federatedstream_stream_users_unlisted(self, *_):
        """ get a list of users that should see a status """
        status = models.Status.objects.create(
            user=self.remote_user, content="hi", privacy="unlisted"
        )
        users = activitystreams.FederatedStream().stream_users(status)
        self.assertEqual(users, [])
