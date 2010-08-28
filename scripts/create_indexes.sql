
CREATE INDEX idx_catgraph_child ON category_graph (child_id);
CREATE INDEX idx_catgraph_parent ON category_graph (parent_id);

CREATE INDEX idx_cmt_creator_id ON comment (creator_id);
CREATE INDEX idx_cmt_reply_id ON comment (reply_id);
CREATE INDEX idx_cmt_poll_id ON comment (poll_id);
CREATE INDEX idx_cmt_topic_id ON comment (topic_id);
CREATE INDEX idx_cmt_variant ON comment (variant);

CREATE INDEX idx_cmtd_id ON comment (id,delete_time);
CREATE INDEX idx_cmtd_reply_id ON comment (reply_id,delete_time);
CREATE INDEX idx_cmtd_poll_id ON comment (poll_id,delete_time);
CREATE INDEX idx_cmtd_topic_id ON comment (topic_id,delete_time);
CREATE INDEX idx_cmtd_variant ON comment (variant,delete_time);

CREATE INDEX idx_rev_comment_id ON revision (comment_id);

CREATE INDEX idx_dgb_creator_id ON delegateable (creator_id);
CREATE INDEX idx_dgb_instance_id ON delegateable (instance_id);
CREATE INDEX idx_dgb_type ON delegateable (type);
CREATE INDEX idx_dgb_type_id ON delegateable (id,type);

CREATE INDEX idx_dgbd_creator_id ON delegateable (creator_id,delete_time);
CREATE INDEX idx_dgbd_instance_id ON delegateable (instance_id,delete_time);
CREATE INDEX idx_dgbd_type ON delegateable (type,delete_time);
CREATE INDEX idx_dgbd_type_id ON delegateable (id,type,delete_time);

CREATE INDEX idx_del_principal_id ON delegation (principal_id);
CREATE INDEX idx_del_agent_id ON delegation (agent_id);
CREATE INDEX idx_del_scope_id ON delegation (scope_id);
CREATE INDEX idx_del_scope_principal_id ON delegation (scope_id,principal_id);
CREATE INDEX idx_deld_principal_id ON delegation (principal_id,revoke_time);
CREATE INDEX idx_deld_agent_id ON delegation (agent_id,revoke_time);
CREATE INDEX idx_deld_scope_id ON delegation (scope_id,revoke_time);
CREATE INDEX idx_deld_scope_principal_id ON delegation (scope_id,principal_id,revoke_time);

CREATE INDEX idx_evt_user_id ON event (user_id);
CREATE INDEX idx_evt_instance_id ON event (instance_id);
CREATE INDEX idx_evt_topic_topic_id ON event_topic (topic_id);
CREATE INDEX idx_evt_topic_event_topic_id ON event_topic (event_id, topic_id);

CREATE INDEX idx_group_code ON `group` (`code`);
CREATE INDEX idx_group_perm_group_id ON group_permission (group_id);
CREATE INDEX idx_group_perm_perm_id ON group_permission (permission_id);
CREATE INDEX idx_group_perm_perm_group_id ON group_permission (permission_id,group_id);

CREATE INDEX idx_instance_key ON instance (`key`);
CREATE INDEX idx_instanced_key ON instance (`key`,delete_time);
CREATE INDEX idx_mem_user_id ON membership (user_id);
CREATE INDEX idx_mem_instance_id ON membership (instance_id);
CREATE INDEX idx_mem_group_id ON membership (instance_id);

CREATE INDEX idx_selection_prop_id ON selection (proposal_id);
CREATE INDEX idx_selection_page_id ON selection (page_id);
CREATE INDEX idx_selection_key ON selection (proposal_id);
CREATE INDEX idx_selectiond_prop_id ON selection (proposal_id,delete_time);
CREATE INDEX idx_selectiond_page_id ON selection (page_id,delete_time);
CREATE INDEX idx_selectiond_key ON selection (proposal_id,delete_time);

CREATE INDEX idx_poll_subject ON poll (subject);
CREATE INDEX idx_tally_poll_id ON tally (poll_id);

CREATE INDEX idx_text_page_id ON `text` (page_id);
