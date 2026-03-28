from auth import hash_password

if __name__ == "__main__":
    password = input("Mot de passe à hasher : ").strip()
    print(hash_password(password))
