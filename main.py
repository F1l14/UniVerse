from new_eclass import EclassConnector

username = input("username: ")
password = input("password: ")
eclass = EclassConnector(username, password, headless=False)
eclass.login()