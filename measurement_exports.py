"""Prepare measurement tables without treating rodent diagnostic fits as orbits."""

import pandas as pd


NO_ORBIT_STATUS = 'not_an_orbit'
NO_ORBIT_REASON = 'The fitted sphere does not identify the orbit; no orbital measurements are reported.'

# These describe the specimen or mesh, independently of the fitted sphere.
SPECIMEN_COLUMNS = {
    'filename', 'specimen', 'species', 'group', 'folder', 'path',
    'length_x', 'width_y', 'height_z', 'L',
    'closed', 'n_components', 'genus_largest', 'n_vertices', 'n_faces',
    'status', 'reliable', 'flag_reason',
}


def is_rodent_filename(name):
    return 'peromyscus' in str(name).casefold()


def rodent_mask(frame):
    mask = pd.Series(False, index=frame.index)
    for column in ('filename', 'specimen', 'species', 'group', 'folder', 'path'):
        if column in frame:
            mask |= frame[column].astype('string').str.contains('peromyscus', case=False, na=False)
    return mask


def export_measurements(frame):
    """Return an export copy; retain full diagnostic fits in the caller's data.

    Remeshing settings belong to the remeshing inputs and run logs, rather than
    the measurement table. Peromyscus examples illustrate a failure to identify
    the orbit, so their numerical fitting results must not become orbital data.
    """
    result = frame.drop(columns=['para', 'remeshing_parameter'], errors='ignore').copy()
    rodents = rodent_mask(result)
    if not rodents.any():
        return result

    for column in result.columns.difference(SPECIMEN_COLUMNS):
        if pd.api.types.is_bool_dtype(result[column].dtype):
            result[column] = result[column].astype(object)
        result.loc[rodents, column] = None

    if 'status' in result:
        result.loc[rodents, 'status'] = NO_ORBIT_STATUS
    elif 'reliable' not in result:
        result['status'] = 'numerical_fit'
        result.loc[rodents, 'status'] = NO_ORBIT_STATUS
    if 'reliable' in result:
        result.loc[rodents, 'reliable'] = 'no fit reported'
    if 'flag_reason' in result:
        result.loc[rodents, 'flag_reason'] = NO_ORBIT_REASON
    return result
