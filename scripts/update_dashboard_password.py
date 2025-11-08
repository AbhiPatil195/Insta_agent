#!/usr/bin/env python3
"""
Generate htpasswd entries for Nginx basic authentication.
Requires: pip install passlib
"""
import sys
import secrets
import string
from pathlib import Path


def generate_password(length=16):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_htpasswd_entry(username, password):
    """Create bcrypt htpasswd entry (more secure than apr1)."""
    try:
        from passlib.hash import bcrypt
        hashed = bcrypt.using(rounds=12).hash(password)
        return f"{username}:{hashed}"
    except ImportError:
        print("ERROR: passlib not installed. Install with: pip install passlib", file=sys.stderr)
        print("Falling back to apache htpasswd utility if available...", file=sys.stderr)
        return None


def main():
    print("=" * 70)
    print("Dashboard Password Generator for Insta Agent")
    print("=" * 70)
    
    # Get username
    username = input("\nEnter username (default: admin): ").strip()
    if not username:
        username = "admin"
    
    # Get or generate password
    use_random = input("Generate random password? (Y/n): ").strip().lower()
    if use_random in ("", "y", "yes"):
        password = generate_password()
        print(f"\n✓ Generated password: {password}")
        print("  SAVE THIS PASSWORD - it won't be shown again!")
    else:
        password = input("Enter password: ").strip()
        if len(password) < 8:
            print("ERROR: Password must be at least 8 characters", file=sys.stderr)
            sys.exit(1)
    
    # Create htpasswd entry
    entry = create_htpasswd_entry(username, password)
    
    if entry:
        # Update .htpasswd file
        htpasswd_path = Path(__file__).parent.parent / "nginx" / ".htpasswd"
        htpasswd_path.parent.mkdir(exist_ok=True)
        
        with open(htpasswd_path, "w") as f:
            f.write(entry + "\n")
        
        print(f"\n✓ Updated {htpasswd_path}")
        print(f"\nCredentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print("\nRestart nginx to apply changes:")
        print("  docker compose restart nginx")
        
    else:
        print("\nManual alternative using htpasswd command:")
        print(f"  htpasswd -Bc nginx/.htpasswd {username}")
        print("  (You'll be prompted for the password)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
