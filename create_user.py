import argparse
import bcrypt

def make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--username", required=True)
    p.add_argument("--display", required=True)
    p.add_argument("--role", choices=["admin","staff","member"], required=True)
    p.add_argument("--member-id", default="")
    p.add_argument("--password", default=None, help="Vermezseniz sizden istenir")
    args = p.parse_args()

    if args.password is None:
        import getpass
        args.password = getpass.getpass("Şifre: ")

    h = make_hash(args.password)
    # CSV satırı
    print("username,display_name,role,member_id,password_hash")
    print(f"{args.username},{args.display},{args.role},{args.member_id},{h}")

if __name__ == "__main__":
    main()
