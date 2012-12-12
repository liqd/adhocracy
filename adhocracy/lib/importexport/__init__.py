"""
Helper functions for human-readable and interoperable formats for adhocracy's data.
"""

import logging
import email.utils
import time
import zipfile

from .formats import render,read_data
from .transforms import BadgeTransform

import formencode






def _get_user(options, dict):
    user = None
    if options['incl_users'] == True and 'author' in dict:
        user = model.User.find(dict['author'], include_deleted=True)
    if not user:
            user = options['default_user']
    return user


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

        res[str(rc.id)] = c
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
                proposals[str(rp.id)] = p
            i['discussion '] = proposals
        instances[ri.key] = i
    return instances

def _format_time(timestamp):
    return email.utils.formatdate(timestamp)

def _create_instance(name, instance, replacement_strategy):
    assert 'title' in instance

    user = _get_user(options, instance)
    myInstance = model.Instance.find(instance['key'], include_deleted=True)

    if myInstance:
        doUpdate = replacement_strategy == 'update'
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
            myInstance.use_norms = use_norms
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

    model.meta.Session.add(my_instance)
    return myInstance


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

            model.meta.Session.add(myProposal)

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
            model.meta.Session.add(myComment)

            # Add subcomments
            if 'comments' in comment:
                for sub_id, subcomment in comment['comments'].iteritems():
                    _create_comment(sub_id, subcomment, options, topic, reply=myComment)


def _perform_import(f, format, opts):

    data = formats.read_data(f)


    if include_badges:
        if 'badges' in data:
            for badge in data['badges'].values():
                _create_badge(badge, options)

    if include_users == True:
        if 'users' in data:
            for user in data['users'].values():
                _create_user(user)

    if include_instances:
        if 'discussions' in data:
            for name, instance in data['discussions'].iteritems():
                inst = _create_instance(name, instance, options)

                # create proposals
                if options['include_proposals']:
                    if 'discussion ' in instance:
                        for p_name, proposal in instance['discussion '].iteritems():
                            _create_proposal(p_name, proposal, options)


def export_data(opts):
    data = {}
    for transform in _TRANSFORMS:
        if getattr(opts, 'include_' + transform.name.lower()):
            data[transform.name] = transform.export_all()
    return data

def export(opts):
    return render(export_data(ops))


    #     include_users = self.form_result.get('users_enabled')

    #     id_user = None

    #     now = time.time()
    #     data = {
    #         'metadata': {
    #             'type': 'normsetting-export',
    #             'version': 2,
    #             'time': _format_time(now),
    #         }
    #     }

    #     if self.form_result.get('badges'):
    #         data['badges'] = _get_badges()

    #     if include_users:
    #         include_users_personal = self.form_result.get('users_personal')
    #         if include_users_personal:
    #             id_user = lambda u: u.user_name
    #         else:
    #             id_user = lambda u: str(u.id)

    #         data['users'] = _get_userData(id_user,
    #                             include_users_personal=self.form_result.get('users_personal'),
    #                             include_password=self.form_result.get('users_password'),
    #                             include_badges=self.form_result.get('badges'))

    #     if self.form_result.get('instances_enabled'):
    #         data['discussions'] = _get_instanceData(self.form_result, id_user)

    #     timeStr = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(now))
    #     title = config.get('adhocracy.site.name', 'adhocracy') + '-' + timeStr
    #     eFormat = self.form_result.get('format')
    

# TODO move model.meta.Session.commit() calls to the upper layers
# TODO merge with csv user import

