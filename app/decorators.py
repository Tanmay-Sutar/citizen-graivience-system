from functools import wraps
from flask import abort
from flask_login import current_user


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def citizen_only(f):
    return roles_required('citizen')(f)


def officer_only(f):
    return roles_required('officer', 'co_officer', 'main_authority')(f)


def co_officer_only(f):
    return roles_required('co_officer', 'main_authority')(f)


def admin_only(f):
    return roles_required('main_authority')(f)
