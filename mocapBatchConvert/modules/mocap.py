import os
import sys
import pymel.core as pm
sys.path.append("I:/script/bin/td/maya/scripts/mocapConvert/mocapBatchConvert/modules")
import convert
reload(convert)
print(convert)
from convert import read_yaml, import_animation

def MocapImport(project_name, template_name, skeleton_path, mocap_path, remove_anim_reference=True):
    """Import mocap animation.
    """
    print("mocap import")
    if not pm.ls(sl=1):
        raise Exception('Please select Root of character first')
    target = pm.ls(sl=1)[0]
    target_namespace = target.namespace()[:-1]

    asset_name = target_namespace.split('_')[0]

    if not os.path.isfile(skeleton_path):
        raise Exception(
            'Mocap skeleton path: %s does not exist !!!' % skeleton_path)

    if not os.path.isfile(mocap_path):
        raise Exception(
            'Mocap animation path: %s does not exist !!!' % mocap_path)

    template_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'yaml'))
    # get mapping path
    mapping_path = os.path.join(
        template_root, project_name, '%s.yaml' % template_name)
    mapping_rules = read_yaml(mapping_path)

    # import_animation
    mocap_namespace = import_animation(
        target,
        skeleton_path,
        mocap_path,
        project_name,
        template_name,
        mapping_rules)

    # remove anim reference
    if remove_anim_reference:
        for ref in pm.listReferences():
            if ref.namespace == mocap_namespace.split(':')[0]:
                ref.remove()