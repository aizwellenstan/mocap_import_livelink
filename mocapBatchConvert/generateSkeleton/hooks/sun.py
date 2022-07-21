#-*- coding:utf-8 -*-
import pymel.core as pm


def pre_import(target_namespace, template_name):
    print 'pre_import', target_namespace, template_name
    if template_name == 'sun':
        pm.setAttr('%s:Body1.Upper_Body_LeftLeg_FKIK' % target_namespace, 0)
        pm.setAttr('%s:Body1.Upper_Body_RightLeg_FKIK' % target_namespace, 0)


def post_import(target_namespace, mocap_anim_namespace, template_name):
    print 'post_import', target_namespace, mocap_anim_namespace, template_name

