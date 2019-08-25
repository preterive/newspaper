from app import *

db.create_all()
u = User(email='test@test.de',pwd='test',role='god')
db.session.add(u)
db.session.commit()
