from sqlalchemy import func
from ckan.plugins import toolkit as tk
from ckan.model import Session
from ckan.lib.navl.dictization_functions import validate
from ckan.lib.navl.validators import not_empty
from ckan.logic import get_or_bust

from ..model import DataRequest, DataRequestComment, setup as model_setup


# CKAN 2.9/2.10 ortamlarında 'unicode' validator ismi değişebiliyor; güvenli fallback:
try:
    from ckan.lib.navl.validators import unicode as unicode_safe  # type: ignore
except Exception:
    def unicode_safe(value):
        if value is None:
            return u""
        return str(value)


def _ensure_model():
    # Tabloların ve mapper'ların hazır olduğundan emin ol
    model_setup()


def datarequest_create(context, data_dict):
    _ensure_model()
    tk.check_access("datarequest_create", context, data_dict)

    schema = {
        "title": [not_empty, unicode_safe],
        "description": [not_empty, unicode_safe],
    }
    data, errors = validate(data_dict, schema, context)
    if errors:
        raise tk.ValidationError(errors)

    user = context.get("user")
    userobj = tk.get_action("user_show")({"ignore_auth": True}, {"id": user})

    dr = DataRequest()
    dr.title = data["title"]
    dr.description = data["description"]
    dr.status = u"open"
    dr.user_id = userobj["id"]

    Session.add(dr)
    Session.commit()

    return {
        "id": dr.id,
        "title": dr.title,
        "description": dr.description,
        "status": dr.status,
        "user_id": dr.user_id,
        "created_at": dr.created_at.isoformat() if dr.created_at else None,
        "updated_at": dr.updated_at.isoformat() if dr.updated_at else None,
    }


def datarequest_show(context, data_dict):
    _ensure_model()
    tk.check_access("datarequest_show", context, data_dict)

    dr_id = get_or_bust(data_dict, "id")
    dr = Session.query(DataRequest).get(dr_id)  # noqa
    if not dr:
        raise tk.ObjectNotFound("Data request not found")

    comment_count = (
        Session.query(func.count(DataRequestComment.id))
        .filter(DataRequestComment.data_request_id == dr.id)
        .scalar()
    )

    return {
        "id": dr.id,
        "title": dr.title,
        "description": dr.description,
        "status": dr.status,
        "user_id": dr.user_id,
        "created_at": dr.created_at.isoformat() if dr.created_at else None,
        "updated_at": dr.updated_at.isoformat() if dr.updated_at else None,
        "comment_count": int(comment_count or 0),
    }


def datarequest_list(context, data_dict):
    _ensure_model()
    tk.check_access("datarequest_list", context, data_dict)

    status = (data_dict or {}).get("status")
    include_comments = tk.asbool(
        (data_dict or {}).get("include_comments", False))

    q = Session.query(DataRequest)
    if status in ("open", "closed"):
        q = q.filter(DataRequest.status == status)
    q = q.order_by(DataRequest.created_at.desc())

    # Yorum sayıları için toplu sorgu
    counts = dict(
        Session.query(
            DataRequestComment.data_request_id,
            func.count(DataRequestComment.id)
        )
        .group_by(DataRequestComment.data_request_id)
        .all()
    )

    datarequests = q.all()
    dr_ids = [dr.id for dr in datarequests]

    comments_map = {}
    if include_comments and dr_ids:
        comments = (
            Session.query(DataRequestComment)
            .filter(DataRequestComment.data_request_id.in_(dr_ids))
            .order_by(DataRequestComment.created_at.asc())
            .all()
        )
        for c in comments:
            if c.data_request_id not in comments_map:
                comments_map[c.data_request_id] = []
            author = getattr(c, "author", None)
            user_name = getattr(author, "name", None) if author else None
            user_display_name = getattr(
                author, "display_name", None) if author else None
            comments_map[c.data_request_id].append({
                "id": c.id,
                "data_request_id": c.data_request_id,
                "user_id": c.user_id,
                "user_name": user_name,
                "user_display_name": user_display_name,
                "content": c.content,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })

    out = []
    for dr in datarequests:
        item = {
            "id": dr.id,
            "title": dr.title,
            "description": dr.description,
            "status": dr.status,
            "user_id": dr.user_id,
            "created_at": dr.created_at.isoformat() if dr.created_at else None,
            "updated_at": dr.updated_at.isoformat() if dr.updated_at else None,
            "comment_count": int(counts.get(dr.id, 0)),
        }
        if include_comments:
            item["comments"] = comments_map.get(dr.id, [])
        out.append(item)
    return out


def datarequest_comment_create(context, data_dict):
    _ensure_model()
    tk.check_access("datarequest_comment_create", context, data_dict)

    dr_id = get_or_bust(data_dict, "data_request_id")
    content = get_or_bust(data_dict, "content")

    if not content or not str(content).strip():
        raise tk.ValidationError({"content": ["This field is required."]})

    dr = Session.query(DataRequest).get(dr_id)  # noqa
    if not dr:
        raise tk.ObjectNotFound("Data request not found")

    user = context.get("user")
    userobj = tk.get_action("user_show")({"ignore_auth": True}, {"id": user})

    cmt = DataRequestComment()
    cmt.data_request_id = dr.id
    cmt.user_id = userobj["id"]
    cmt.content = str(content).strip()

    Session.add(cmt)
    Session.commit()

    author = getattr(cmt, "author", None)
    user_name = getattr(author, "name", None) if author else None
    user_display_name = getattr(
        author, "display_name", None) if author else None

    return {
        "id": cmt.id,
        "data_request_id": cmt.data_request_id,
        "user_id": cmt.user_id,
        "user_name": user_name,
        "user_display_name": user_display_name,
        "content": cmt.content,
        "created_at": cmt.created_at.isoformat() if cmt.created_at else None,
    }


def datarequest_comment_list(context, data_dict):
    """
    Belirli bir data request'e ait yorumları döner.
    Parametre:
        data_request_id (zorunlu)
    Opsiyonel:
        limit, offset (performans için ileride)
    """
    _ensure_model()
    tk.check_access("datarequest_comment_list", context, data_dict)

    dr_id = get_or_bust(data_dict, "data_request_id")
    dr = Session.query(DataRequest).get(dr_id)  # noqa
    if not dr:
        raise tk.ObjectNotFound("Data request not found")

    comments = (
        Session.query(DataRequestComment)
        .filter(DataRequestComment.data_request_id == dr_id)
        .order_by(DataRequestComment.created_at.asc())
        .all()
    )

    out = []
    for c in comments:
        author = getattr(c, "author", None)
        user_name = getattr(author, "name", None) if author else None
        user_display_name = getattr(
            author, "display_name", None) if author else None
        out.append({
            "id": c.id,
            "data_request_id": c.data_request_id,
            "user_id": c.user_id,
            "user_name": user_name,
            "user_display_name": user_display_name,
            "content": c.content,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return out


def datarequest_status_update(context, data_dict):
    _ensure_model()
    tk.check_access("datarequest_status_update", context, data_dict)

    dr_id = get_or_bust(data_dict, "id")
    new_status = get_or_bust(data_dict, "status")

    if new_status not in ("open", "closed"):
        raise tk.ValidationError({"status": ['Must be "open" or "closed"']})

    dr = Session.query(DataRequest).get(dr_id)  # noqa
    if not dr:
        raise tk.ObjectNotFound("Data request not found")

    dr.status = new_status
    Session.add(dr)
    Session.commit()

    return {"id": dr.id, "status": dr.status}
