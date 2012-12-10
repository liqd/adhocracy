import logging
import email.utils
import time
try:
    from cStringIO import StringIO
except ImportErro:
    from StringIO import StringIO
import zipfile

import simplejson
import formencode

from pylons import config, request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import validate

from repoze.what.plugins.pylonshq import ActionProtector

from adhocracy import model
from adhocracy.lib.auth.authorization import has_permission
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, render_real_json, ret_success

log = logging.getLogger(__name__)

_INDEX_FN = 'index.json'

class ExportForm(formencode.Schema):
    allow_extra_fields = True

class ImportForm(formencode.Schema):
    allow_extra_fields = True

def _data_genJson(data):
    return simplejson.dumps(data, indent=4)

def _dataToFiles(data, prefix='', forceIndex=False):
    nested = False
    myData = {}
    for k,subData in data.items():
        if isinstance(subData, dict):
            for resel in _dataToFiles(subData, (prefix + '/' if prefix else '') + k):
                nested = True
                yield resel
        else:
            myData[k] = subData

    if myData:
        myFn = prefix + ('/' + _INDEX_FN if nested or forceIndex else '.json')
        jsonData = _data_genJson(myData)
        yield (myFn, jsonData)

def _render_zip(data, filename):
    fakeFile = StringIO()
    zf = zipfile.ZipFile(fakeFile, 'w')
    for fn,jsonData in _dataToFiles(data):
        zf.writestr(fn, jsonData)
    zf.close()

    if filename is not None:
        response.content_disposition = 'attachment; filename="' + filename.replace('"', '_') + '"'
    response.content_type = 'application/zip'
    return fakeFile.getvalue()

def _safe_id(s):
    if '.json' in s:
        s += '_'
    return s

def _zip_Content_To_dict(f, dict, hierarchy):
    if f.compress_size == 0: # Directory entry
        return
    if len(hierarchy) == 1:
        fn = hierarchy[0].split('.')
        dict[fn[0]] = simplejson.load(f)
    # handle special case of 'index.json'
    elif ((len(hierarchy) == 2) and (hierarchy[1] == 'index.json')):
            index = simplejson.load(f)
            fn = hierarchy[0].split('.')
            if fn[0] not in dict:
                dict[fn[0]] = {}
            dict[fn[0]].update(index)
    else:
        try:
            subdict = dict[hierarchy[0]]
        except KeyError:
            subdict = {}
            dict[hierarchy[0]] = subdict

        del hierarchy[0]
        _zip_Content_To_dict(f, subdict, hierarchy)


def _get_badges():
    badges = {}
    raw_badges = model.Badge.all()
    for badge in raw_badges:
        b = {}
        b['title'] = badge.title
        b['color'] = badge.color
        b['description'] = badge.description
        b['display_group'] = badge.display_group
        if badge.group_id:
            g = model.Group.by_id(badge.group_id)
            b['group'] = g.group_name
        else:
            b['group'] = False
        badges[badge.title] = b
    return badges

def _get_user(options, dict):
    user = None
    if options['incl_users'] == True and 'author' in dict:
        user = model.User.find(dict['author'], include_deleted=True)
    if not user:
            user = options['default_user']
    return user


def _get_userData(id_user, include_personal, include_password, include_badges):
    raw_users = model.user.User.all()
    users = {}
    for raw_u in raw_users:
        u = {}
        if include_personal:
            u['user_name'] = raw_u.user_name
            u['display_name'] = raw_u.display_name
            u['gender'] = raw_u.gender
            u['bio'] = raw_u.bio
            u['email'] = raw_u.email
            u['locale'] = raw_u.locale_id
            u['adhocracy_no_instancetext'] = raw_u.no_instancetext
        if include_password:
            u['adhocracy_activation_code'] = raw_u.activation_code
            u['adhocracy_reset_code'] = raw_u.reset_code
            u['adhocracy_password'] = raw_u.password
            u['adhocracy_banned'] = raw_u.banned
        if include_badges:
            u['badges'] = [b.title for b in raw_u.badges]
        users[id_user(raw_u)] = u
    return users

def _get_commentData(all_comments, id_user, parent=None):
    res = {}
    for rc in all_comments:
        if rc.reply != parent:
            continue
        c = {
            'text': rc.latest.text,
            'adhocracy_type': 'comment',
        }
        if id_user is not None:
            c['author'] = id_user(rc.creator)
        children = _get_commentData(all_comments, id_user, rc)
        if children:
            c['comments'] = children

        res[_safe_id(str(rc.id))] = c
    return res

def _get_instanceData(form, id_user):
    instances = {}
    raw_instances = model.instance.Instance.all()
    for ri in raw_instances:
        i = {
            'key': ri.key,
            'title': ri.label,
            'text': ri.description,
            'frozen': ri.frozen,
            'hidden': ri.hidden,
            'knowledge_link': ri.knowledge_link,
            'adhocracy_groupname': ri.groupname,
            'adhocracy_type': 'instance',
            'adhocracy_disable_proposals': ri.disable_proposals,
            'adhocracy_allow_adopt': ri.allow_adopt,
            'adhocracy_allow_delegate': ri.allow_delegate,
            'adhocracy_allow_index': ri.allow_index,
        }
        if ri.locale:
            i['locale'] = ri.locale.__str__()
        if id_user is not None:
            i['author'] = id_user(ri.creator)
        if form.get('proposals_enabled'):
            proposals = {}
            raw_proposals = model.proposal.Proposal.all(instance=ri)
            for rp in raw_proposals:
                p = {
                    'title': rp.title,
                    'text': rp.description.head.text,
                    'instance': rp.instance.key,
                    'adhocracy_type': 'proposal',
                }
                if id_user is not None:
                    p['author'] = id_user(rp.creator)
                if form.get('proposals_comments_enabled'):
                    all_comments = rp.description.comments
                    p['comments'] = _get_commentData(all_comments, id_user)
                proposals[_safe_id(str(rp.id))] = p
            i['discussion '] = proposals
        instances[_safe_id(ri.key)] = i
    return instances

def _format_time(timestamp):
    return email.utils.formatdate(timestamp)

def _create_user(name, user, options):
    assert 'user_name' in user
    assert 'email' in user
    email = user['email'].lower()
    myUser = model.User.find_by_email(email, include_deleted=True)
    if myUser:
        doUpdate = options['replacement_strategy'] == 'update'
    else:
        myUser = model.User.create(user['user_name'], email)
        doUpdate = True

    if doUpdate:
        if 'bio' in user:
            myUser.bio = user['bio']
        if 'display_name' in user:
            myUser.display_name = user['display_name']
        if 'locale' in user:
            myUser.locale = user['locale']
        if 'gender' in user:
            myUser.gender = user['gender']
        if 'user_name' in user:
            myUser.user_name = user['user_name']
        if 'adhocracy_no_instancetext' in user:
            myUser.no_instancetext = user['adhocracy_no_instancetext']
        if 'adhocracy_reset_code' in user:
            myUser.reset_code = user['adhocracy_reset_code']
        if 'adhocracy_password' in user:
            myUser.password_hash = user['adhocracy_password']
        if 'adhocracy_activation_code' in user:
            myUser.activation_code = user['adhocracy_activation_code']
        if 'adhocracy_banned' in user:
            myUser.banned = user['adhocracy_banned']

        model.meta.Session.commit()

def _create_instance(name, instance, options):
    assert 'title' in instance

    user = _get_user(options, instance)
    myInstance = model.Instance.find(instance['key'], include_deleted=True)

    if myInstance:
        doUpdate = options['replacement_strategy'] == 'update'
    else:
        myInstance = model.Instance.create(instance['key'], instance['title'], user, instance['text'])
        doUpdate = True

    if doUpdate:
        if 'label' in instance:
            myInstance.label = instance['title']
        if user:
            myInstance.creator = user
        if 'text' in instance:
            myInstance.description = instance['text']
        if 'adhocracy_groupname' in instance:
            myInstance.groupname = instance['adhocracy_groupname']
        if 'frozen' in instance:
            myInstance.frozen = instance['frozen']
        if 'hidden' in instance:
            myInstance.hidden = instance['hidden']
        if 'use_norms' in instance:
            myInstance.use_norms = instance['use_norms']
        else:
            myInstance.use_norms = False
        if 'knowledge_link' in instance:
            myInstance.knowledge_link = instance['knowledge_link']
        if 'adhocracy_sort_weight' in instance:
            myInstance.sort_weight = instance['adhocracy_sort_weight']
        if 'adhocracy_disable_proposals' in instance:
            myInstance.disable_proposals = instance['adhocracy_disable_proposals']
        if 'locale' in instance:
            myInstance.locale = instance['locale']
        if 'adhocracy_allow_adopt' in instance:
            myInstance.allow_adopt = instance['adhocracy_allow_adopt']
        if 'adhocracy_allow_delegate' in instance:
            myInstance.allow_delegate = instance['adhocracy_allow_delegate']
        if 'adhocracy_allow_index' in instance:
            myInstance.allow_index = instance['adhocracy_allow_index']

    model.meta.Session.commit()

    # create proposals
    if options['incl_proposals']:
        if 'discussion ' in instance:
            for p_name, proposal in instance['discussion '].iteritems():
                _create_proposal(p_name, proposal, options)


def _create_proposal(name, proposal, options):
    if 'adhocracy_type' in proposal:
        if proposal['adhocracy_type'] == 'proposal':
            user = _get_user(options, proposal)

            myProposal = model.Proposal.find_by_title(proposal['title'], include_deleted=True)
            if myProposal:
                if options['replacement_strategy'] == 'update':
                    myProposal.text = proposal['text']

            else:
                myProposal = model.Proposal.create(model.Instance.find(proposal['instance'], include_deleted=True), proposal['title'], user)
                myProposal.milestone = None
                model.meta.Session.flush()
                myDescription = model.Page.create(model.Instance.find(proposal['instance'], include_deleted=True), proposal['title'], proposal['text'], user, function=model.Page.DESCRIPTION)
                myDescription.parents = [myProposal]

                myProposal.description = myDescription

            model.meta.Session.flush()

            # create comments
            if options['incl_comments'] == True:
                if 'comments' in proposal:
                    for id, comment in proposal['comments'].iteritems():
                        _create_comment(id, comment, options, myProposal.description)


def _create_comment(id, comment, options, topic, reply=None):
    if 'adhocracy_type' in comment:
        if comment['adhocracy_type'] == 'comment':
            user = _get_user(options, comment)
            myComment = model.Comment.create(' ', comment['text'], user, topic, reply=reply, wiki=False)
            model.meta.Session.commit()

            # Add subcomments
            if 'comments' in comment:
                for sub_id, subcomment in comment['comments'].iteritems():
                    _create_comment(sub_id, subcomment, options, topic, reply=myComment)

def _create_badge(badge, options):
    myBadge = model.Badge.find(badge['title'])
    if myBadge:
        if options['replacement_strategy'] == 'update':
            myBadge.color = badge['color']
            myBadge.description = badge['description']
            if badge['group']:
                myBadge.group = model.Group.by_id(badge['group'])
            myBadge.display_group = badge['display_group']
    else:
        myBadge = model.Badge.create(badge['title'], badge['color'], badge['description'])
        myBadge.display_group=badge['display_group']
        if badge['group']:
            myBadge.group = model.Group.by_id(badge['group'])

    model.meta.Session.commit()

def _perform_import(f, options):
        # creates a dictionary 'data' with the imported data for json file
        f.seek(0, 0)
        if f.readline()[:1] == "{":
            f.seek(0, 0)
            data = simplejson.load(f)

        # creates a dictionary 'data' with the imported data of zip file
        f.seek(0, 0)
        if f.readline()[:2] == "PK":
            data ={}
            f.seek(0, 0)
            zip = zipfile.ZipFile(f)
            for contained_file in sorted(zip.namelist()):
                hierarchy = contained_file.split('/')
                f = zip.open(contained_file)
                _zip_Content_To_dict(f, data, hierarchy)

        if options['incl_badges'] == True:
            if 'badges' in data:
                for badge in data['badges'].itervalues():
                    _create_badge(badge, options)

        if options['incl_users'] == True:
            if 'users' in data:
                for name, user in data['users'].iteritems():
                    _create_user(name, user, options)

        if options['incl_instances'] == True:
            if 'discussions' in data:
                for name, instance in data['discussions'].iteritems():
                    _create_instance(name, instance, options)

class ImportexportController(BaseController):
    @ActionProtector(has_permission("global.admin"))
    def export_dialog(self):
        return render('importexport/export_dialog.html')

    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("global.admin"))
    @validate(schema=ExportForm(), post_only=True)
    def export_do(self):
        id_user = None

        now = time.time()
        data = {
            'metadata': {
                'type': 'normsetting-export',
                'version': 2,
                'time': _format_time(now),
            }
        }

        if self.form_result.get('badges'):
            data['badges'] = _get_badges()

        if self.form_result.get('users_enabled'):
            include_personal = self.form_result.get('users_personal')
            if include_personal:
                auth_by = config.get('adhocracy.authentication.by', 'user_name')
                id_user = lambda u: _safe_id(getattr(u, auth_by))
            else:
                id_user = lambda u: _safe_id(str(u.id))

            data['users'] = _get_userData(id_user,
                                include_personal=self.form_result.get('users_personal'),
                                include_password=self.form_result.get('users_password'),
                                include_badges=self.form_result.get('badges'))

        if self.form_result.get('instances_enabled'):
            data['discussions'] = _get_instanceData(self.form_result, id_user)

        timeStr = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(now))
        title = config.get('adhocracy.site.name', 'adhocracy') + '-' + timeStr
        eFormat = self.form_result.get('format')
        if eFormat == 'zip':
            return _render_zip(data, filename=title + '.zip')
        elif eFormat == 'json_download':
            return render_real_json(data, filename=title + '.json')
        elif eFormat == 'json':
            return render_real_json(data)
        else:
            raise ValueError('Invalid format')

    @ActionProtector(has_permission("global.admin"))
    def import_dialog(self):
        return render('importexport/import_dialog.html')


    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("global.admin"))
    @validate(schema=ImportForm(), post_only=True)
    def import_do(self):
        obj = request.POST['importfile']
        contenttype = obj.headers.get('content-type')
        f = obj.file
        options = {}
        options['incl_users'] = self.form_result.get('users_enabled') == 'on'
        options['incl_instances'] = self.form_result.get('instances_enabled') == 'on'
        options['incl_proposals'] = self.form_result.get('proposals_enabled') == 'on'
        options['incl_comments'] = self.form_result.get('proposals_comments_enabled') == 'on'
        options['incl_badges'] = self.form_result.get('badges') == 'on'
        options['replacement_strategy'] = self.form_result.get('replacement')
        # define default user to be author of content that has no valid author
        options['default_user'] = model.User.find(u"admin", include_deleted=True)
        assert options['default_user']

        _perform_import(f, options)

        return render('importexport/import_success.html')

