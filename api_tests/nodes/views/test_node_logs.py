from nose.tools import *  # flake8: noqa

import urlparse
from framework.auth.core import Auth

from website.models import NodeLog
from api.base.settings.defaults import API_BASE

from tests.base import ApiTestCase, assert_datetime_equal
from tests.factories import (
    ProjectFactory,
    AuthUserFactory,
    RegistrationFactory,
    RetractedRegistrationFactory
)
import datetime


API_LATEST = 0
API_FIRST = -1
OSF_LATEST = -1
OSF_FIRST = 0


class TestNodeLogList(ApiTestCase):
    def setUp(self):
        super(TestNodeLogList, self).setUp()
        self.user = AuthUserFactory()
        self.contrib = AuthUserFactory()
        self.creator = AuthUserFactory()
        self.user_auth = Auth(self.user)
        self.NodeLogFactory = ProjectFactory()
        self.pointer = ProjectFactory()

        self.private_project = ProjectFactory(is_public=False, creator=self.user)
        self.private_url = '/{}nodes/{}/logs/'.format(API_BASE, self.private_project._id)

        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_url = '/{}nodes/{}/logs/'.format(API_BASE, self.public_project._id)

    def tearDown(self):
        super(TestNodeLogList, self).tearDown()
        NodeLog.remove()

    def test_add_tag(self):
        user_auth = Auth(self.user)
        self.public_project.add_tag("Jeff Spies", auth=user_auth)
        assert_equal("tag_added", self.public_project.logs[OSF_LATEST].action)
        res = self.app.get(self.public_url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_equal(res.json['data'][API_LATEST]['attributes']['action'], 'tag_added')
        assert_equal("Jeff Spies", self.public_project.logs[OSF_LATEST].params['tag'])

    def test_remove_tag(self):
        user_auth = Auth(self.user)
        self.public_project.add_tag("Jeff Spies", auth=user_auth)
        assert_equal("tag_added", self.public_project.logs[OSF_LATEST].action)
        self.public_project.remove_tag("Jeff Spies", auth=self.user_auth)
        assert_equal("tag_removed", self.public_project.logs[OSF_LATEST].action)
        res = self.app.get(self.public_url, auth=self.user)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_equal(res.json['data'][API_LATEST]['attributes']['action'], 'tag_removed')
        assert_equal("Jeff Spies", self.public_project.logs[OSF_LATEST].params['tag'])

    def test_project_created(self):
        res = self.app.get(self.public_url)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_equal(self.public_project.logs[OSF_FIRST].action, "project_created")
        assert_equal(self.public_project.logs[OSF_FIRST].action,res.json['data'][API_LATEST]['attributes']['action'])

    def test_log_create_on_public_project(self):
        res = self.app.get(self.public_url)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_datetime_equal(datetime.datetime.strptime(res.json['data'][API_FIRST]['attributes']['date'], "%Y-%m-%dT%H:%M:%S.%f"),
                              self.public_project.logs[OSF_FIRST].date)
        assert_equal(res.json['data'][API_FIRST]['attributes']['action'], self.public_project.logs[OSF_FIRST].action)

    def test_log_create_on_private_project(self):
        res = self.app.get(self.private_url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_datetime_equal(datetime.datetime.strptime(res.json['data'][API_FIRST]['attributes']['date'], "%Y-%m-%dT%H:%M:%S.%f"),
                              self.private_project.logs[OSF_FIRST].date)
        assert_equal(res.json['data'][API_FIRST]['attributes']['action'], self.private_project.logs[OSF_FIRST].action)

    def test_add_addon(self):
        self.public_project.add_addon('github', auth=self.user_auth)
        assert_equal('addon_added', self.public_project.logs[OSF_LATEST].action)
        res = self.app.get(self.public_url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_equal(res.json['data'][API_LATEST]['attributes']['action'], 'addon_added')

    def test_project_add_remove_contributor(self):
        self.public_project.add_contributor(self.contrib, auth=self.user_auth)
        assert_equal('contributor_added', self.public_project.logs[OSF_LATEST].action)
        self.public_project.remove_contributor(self.contrib, auth=self.user_auth)
        assert_equal('contributor_removed', self.public_project.logs[OSF_LATEST].action)
        res = self.app.get(self.public_url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_equal(res.json['data'][API_LATEST]['attributes']['action'], 'contributor_removed')
        assert_equal(res.json['data'][1]['attributes']['action'], 'contributor_added')

    def test_remove_addon(self):
        self.public_project.add_addon('github', auth=self.user_auth)
        assert_equal('addon_added', self.public_project.logs[OSF_LATEST].action)
        self.public_project.delete_addon('github', auth=self.user_auth)
        assert_equal('addon_removed', self.public_project.logs[OSF_LATEST].action)
        res = self.app.get(self.public_url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_equal(res.json['data'][API_LATEST]['attributes']['action'], 'addon_removed')

    def test_add_pointer(self):
        self.public_project.add_pointer(self.pointer, auth=Auth(self.user), save=True)
        assert_equal('pointer_created', self.public_project.logs[OSF_LATEST].action)
        res = self.app.get(self.public_url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), len(self.public_project.logs))
        assert_equal(res.json['data'][API_LATEST]['attributes']['action'], 'pointer_created')

    def test_cannot_access_retracted_node_logs(self):
        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        registration = RegistrationFactory(creator=self.user, project=self.public_project)
        url = '/{}nodes/{}/logs/'.format(API_BASE, registration._id)
        retraction = RetractedRegistrationFactory(registration=registration, user=self.user)
        res = self.app.get(url, auth=self.user.auth, expect_errors=True)
        assert_equal(res.status_code, 404)


class TestNodeLogFiltering(TestNodeLogList):

    def test_filter_action_not_equal(self):
        self.public_project.add_tag("Jeff Spies", auth=self.user_auth)
        assert_equal("tag_added", self.public_project.logs[OSF_LATEST].action)
        url = '/{}nodes/{}/logs/?filter[action][ne]=tag_added'.format(API_BASE, self.public_project._id)
        res = self.app.get(url, auth=self.user.auth)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['attributes']['action'], 'project_created')

    def test_filter_date_not_equal(self):
        self.public_project.add_pointer(self.pointer, auth=Auth(self.user), save=True)
        assert_equal('pointer_created', self.public_project.logs[OSF_LATEST].action)
        assert_equal(len(self.public_project.logs), 2)
        date_pointer_added = str(self.public_project.logs[1].date).replace(' ', 'T')

        url = '/{}nodes/{}/logs/?filter[date][ne]={}'.format(API_BASE, self.public_project._id, date_pointer_added)
        res = self.app.get(url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['attributes']['action'], 'project_created')


class TestNodeLogContributors(ApiTestCase):

    def setUp(self):
        super(TestNodeLogContributors, self).setUp()
        self.user = AuthUserFactory()
        self.user_two = AuthUserFactory()
        self.node = ProjectFactory(is_public=False)
        self.node.add_contributor(self.user, auth=Auth(self.node.creator), log=True, save=True)
        self.node.add_contributor(self.user_two, auth=Auth(self.node.creator), log=True, save=True)
        self.node.remove_contributors([self.user_two], auth=Auth(self.node.creator), log=True, save=True)
        self.url = '/{}logs/'.format(API_BASE)

    def test_log_returns_associated_contributors_relationship(self):
        log_id = self.node.logs[1]._id
        url = self.url + '{}/'.format(log_id)
        res = self.app.get(url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        json_data = res.json['data']
        associated_contributors_url = json_data['relationships']['contributors']['links']['related']['href']
        assert_equal(urlparse.urlparse(associated_contributors_url).path, url + 'contributors/')

        res = self.app.get(associated_contributors_url, auth=self.user.auth)
        added_contributor_id = res.json['data'][0]['id']
        assert_equal(self.user._id, added_contributor_id)

    def test_log_associated_contributors_link_leads_to_empty_list(self):
        log_id = self.node.logs[0]._id
        url = self.url + '{}/'.format(log_id)
        res = self.app.get(url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        json_data = res.json['data']
        associated_contributors_url = json_data['relationships']['contributors']['links']['related']['href']
        assert_equal(urlparse.urlparse(associated_contributors_url).path, url + 'contributors/')

        res = self.app.get(associated_contributors_url, auth=self.user.auth)
        assert_equal(res.json['data'], [])

    def test_log_removing_contributors_returns_associated_contributors_relationship(self):
        log_id = self.node.logs[3]._id
        url = self.url + '{}/'.format(log_id)
        res = self.app.get(url, auth=self.user.auth)
        assert_equal(res.status_code, 200)
        json_data = res.json['data']
        assert_equal(json_data['attributes']['action'], 'contributor_removed')
        associated_contributors_url = json_data['relationships']['contributors']['links']['related']['href']
        assert_equal(urlparse.urlparse(associated_contributors_url).path, url + 'contributors/')

        res = self.app.get(associated_contributors_url, auth=self.user.auth)
        removed_contributor_id = res.json['data'][0]['id']
        assert_equal(self.user_two._id, removed_contributor_id)

