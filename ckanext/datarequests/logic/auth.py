from ckan.plugins import toolkit as tk


def datarequest_create(context, data_dict):
    if not context.get('user'):
        return {'success': False, 'msg': 'You must be logged in to create a data request.'}
    return {'success': True}


def datarequest_show(context, data_dict):
    return {'success': True}


def datarequest_list(context, data_dict):
    return {'success': True}


def datarequest_comment_list(context, data_dict):
    # Anonim kullanıcılar dahil herkes yorum listesini görebilsin
    return {'success': True}


def datarequest_comment_create(context, data_dict):
    if not context.get('user'):
        return {'success': False, 'msg': 'You must be logged in to comment.'}
    return {'success': True}


def datarequest_status_update(context, data_dict):
    user = context.get('user')
    if not user:
        return {'success': False, 'msg': 'You must be sysadmin to change status.'}
    user_obj = tk.get_action('user_show')({'ignore_auth': True}, {'id': user})
    if not user_obj.get('sysadmin'):
        return {'success': False, 'msg': 'You must be sysadmin to change status.'}
    return {'success': True}
