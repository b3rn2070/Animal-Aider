import secrets

# Gera uma chave aleatória de 32 caracteres
random_key = secrets.token_hex(16)  # 16 bytes = 32 caracteres hexadecimais
print(f"Chave gerada: {random_key}")