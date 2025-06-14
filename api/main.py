from codecs import encode, decode
from cryptography.fernet import Fernet, InvalidToken
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sqlite3

app = FastAPI()

@app.get("/")
def root_getter():
    return "Access /buscaHash/<hash>"

@app.get("/buscaHash/{hash}")
def get_by_hash(hash: str):
    try:
        with open("key", "r") as keyFile:
            password = encode(keyFile.read().strip())
        cipher_suite = Fernet(password)
        decoded_hash = decode(cipher_suite.decrypt(hash.encode()))
    except (InvalidToken, ValueError, Exception):
        return JSONResponse(content={"erro": "QRCode inválido"})

    conn = sqlite3.connect("controle.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM convidados WHERE Convite = ?", (decoded_hash,))
    row = cursor.fetchone()

    if not row:
        return JSONResponse(content={"erro": "Convite não encontrado"})

    if row["Check in"] == int(1):
        return JSONResponse(content={"erro": "O Convite ja fez check in no evento"})

    if row["Convite"] != decoded_hash:
        return JSONResponse(content={"erro": "QRCode inválido"})

    response = {
        key: (None if row[key] is None else row[key])
        for key in row.keys()
    }

    conn.close()
    return JSONResponse(content=response)

@app.get("/checkIn/{convite}")
def check_in(convite: str):
    conn = sqlite3.connect("controle.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE convidados SET `Check in` = '1' WHERE Convite = ?", (convite,))
    conn.commit()
    conn.close()

    return JSONResponse(content={"status": 1})

@app.get("/convites")
def get_convites():
    conn = sqlite3.connect("controle.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM convidados WHERE `Check in` = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return JSONResponse(content={"total_convites": count})
    