"""Exterior-only motor override (drive revision 4).

Exec after industrial_v2.py. The former internal cutaway remains available only
in archived .blend/.glb assets. New generic motors contain no winding, rotor or
internal bearing construction; equipment-specific layouts remain inferred.
Run refine_drives_v4.py after the current v3 builders to upgrade their compact
servo and process-drive helpers without changing the equipment geometry.
"""
import importlib.util as _drive_importlib
from pathlib import Path as _DrivePath
_drive_spec = _drive_importlib.spec_from_file_location(
    'textile_external_drives_v4', _DrivePath(__file__).with_name('refine_drives_v4.py'))
_drive_v4 = _drive_importlib.module_from_spec(_drive_spec)
_drive_spec.loader.exec_module(_drive_v4)

def motor(parent,loc=(1.3,0,.8),scale=1,detail=False):
    return _drive_v4.create_generic_motor(parent,loc,scale,detail)
