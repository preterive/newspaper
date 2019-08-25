from functools import wraps
from flask import g, redirect

def roles(roles=[]):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is not None:
                if g.user.role in roles:
                    return f(*args, **kwargs)
                else:
                    return redirect('/')

        return decorated_function
    return decorator
