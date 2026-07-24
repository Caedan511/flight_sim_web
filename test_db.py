from backend.init_db import init_database
from backend.auth_service import authenticate_user, create_user


def main():
    init_database()

    ok, msg = authenticate_user("admin", "admin123")
    print("Admin login test:", ok, msg)

    ok, msg = create_user("user1", "123456", "normal")
    print("Create user test:", ok, msg)

    ok, msg = authenticate_user("user1", "123456")
    print("Normal user login test:", ok, msg)


if __name__ == "__main__":
    main()
