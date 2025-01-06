from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from model import SessionLocal, Product
from parser import parse_products
from typing import List

app = FastAPI()
# base_url = https://at-store.ru/internet-shop/kupit_apple_iphone/

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

connected_clients: List[WebSocket] = []


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Получено сообщение: {data}")
            await websocket.send_text(f"Получено сообщение: {data}")
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("Клиент отключился")


async def send_notification(message: str):
    for client in connected_clients:
        try:
            await client.send_text(message)
        except:
            pass


@app.get("/parse/")
async def parse(base_url: str, db: Session = Depends(get_db)):
    products = parse_products(base_url)
    for title, price in products:
        db.add(Product(title=title, price=price))
    db.commit()
    await send_notification("Парсинг завершён")
    return {"message": "Parsing finished"}


@app.post("/products/")
async def add_product(product_id: int, title: str, price: str, db: Session = Depends(get_db)):
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    if existing_product:
        raise HTTPException(status_code=400, detail=f"Товар {Product.id} уже существует")

    new_product = Product(id=product_id, title=title, price=price)
    db.add(new_product)
    db.commit()
    await send_notification(
        f"Добавлен товар {title}, стоимостью {price} с ID {product_id}")
    return {"message": "Product added"}


@app.get("/products/")
async def get_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    await send_notification(f"Список товаров получен")
    return products


@app.put("/products/{product_id}")
async def update_product(product_id: int, title: str, price: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    product.title = title
    product.price = price
    db.commit()
    await send_notification(f"Товар {product_id} обновлён")
    return product


@app.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    db.delete(product)
    db.commit()
    await send_notification(f"Товар {product_id} удалён")
    return {"detail": "Product deleted"}
