"""
Script ini digunakan untuk membuat akun administrator secara manual.
Fitur pendaftaran akun tidak disediakan karena sistem inventaris ini
ditujukan hanya untuk penggunaan internal di lingkungan sekolah.
"""

import bcrypt
hash = bcrypt.hashpw(b"loyal", bcrypt.gensalt()).decode()
print(hash)