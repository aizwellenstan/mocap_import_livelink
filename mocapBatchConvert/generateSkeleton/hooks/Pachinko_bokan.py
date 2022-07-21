#-*- coding:utf-8 -*-
import os

import pymel.core as pm


def pre_import(target_namespace, template_name):
    pass


def post_import(target_namespace, mocap_anim_namespace, template_name):
    pass


def get_default_skeleton_path(target_namespace):
    for ref in pm.listReferences():
        if target_namespace != ref.namespace:
            continue
        ref_dir = os.path.dirname(ref.path)
        ref_dir = os.path.abspath(ref_dir)
        pub_dir = os.path.join(ref_dir, 'pub')
        if not os.path.isdir(pub_dir):
            return None
        for file_ in os.listdir(pub_dir):
            return os.path.join(pub_dir, file_)

